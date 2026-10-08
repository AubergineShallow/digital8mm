# SPDX-License-Identifier: MIT
"""Run one heavy CAD command at a time, and only when enough RAM is free.

The GS8 working tree is shared with other sessions and agents that run CAD builds, so every D2 CAD
process (build, part test, render, audit) goes through this wrapper (copied from cad/gs8-stills-v1):

    .venv-cad/Scripts/python.exe cad/gs8-d2-v1/run_locked.py [--min-free-mb 700] -- <script.py> [args...]

The script runs with the same interpreter as this wrapper. The wrapper:
- on POSIX, holds a kernel flock on a persistent .cad.lock inode; PID metadata is diagnostic only.
  The child inherits the descriptor, so a terminated wrapper cannot unlock a still-running build;
- on Windows, retains the original process-lock implementation;
- waits until free physical RAM is at least --min-free-mb (default 700);
- runs the command with PYTHONDONTWRITEBYTECODE=1 and returns its exit code.
Waiting is bounded by --max-wait-min, after which it exits 75 without running anything.
"""
import argparse
import ctypes
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
LOCK = os.path.join(HERE, ".cad.lock")
_POSIX_LOCK_FD = None


def free_ram_mb():
    if os.name == "nt":
        class MEMORYSTATUSEX(ctypes.Structure):
            _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                        ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                        ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                        ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                        ("sullAvailExtendedVirtual", ctypes.c_ulonglong)]
        st = MEMORYSTATUSEX()
        st.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(st))
        return st.ullAvailPhys / 2**20
    with open("/proc/meminfo") as f:
        for line in f:
            if line.startswith("MemAvailable:"):
                return int(line.split()[1]) / 1024
    return float("inf")


def pid_alive(pid):
    if os.name == "nt":
        h = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
        if not h:
            return False
        code = ctypes.c_ulong()
        ctypes.windll.kernel32.GetExitCodeProcess(h, ctypes.byref(code))
        ctypes.windll.kernel32.CloseHandle(h)
        return code.value == 259  # STILL_ACTIVE
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _try_windows_lock(cmd, stale_s):
    try:
        fd = os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        try:
            with open(LOCK, encoding="utf-8") as f:
                info = json.load(f)
            age = time.time() - info.get("t", 0)
            if age > stale_s or not pid_alive(int(info.get("pid", -1))):
                os.remove(LOCK)
                print(f"[run_locked] broke stale lock {info}", flush=True)
        except (OSError, ValueError):
            pass
        return False
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump({"pid": os.getpid(), "t": time.time(), "cmd": cmd}, f)
    return True


def try_lock(cmd, stale_s):
    """Never infer another POSIX executor's liveness from its namespace-local PID."""
    global _POSIX_LOCK_FD
    if os.name == 'nt':
        return _try_windows_lock(cmd, stale_s)
    import fcntl
    fd = os.open(LOCK, os.O_CREAT | os.O_RDWR, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        os.close(fd)
        return False
    except BaseException:
        os.close(fd)
        raise  # unsupported/denied locking fails closed, never falls back to PID guesses
    try:
        payload = json.dumps(dict(pid=os.getpid(), t=time.time(), cmd=cmd,
                                  locking='posix-flock', state='running')).encode('utf-8')
        os.ftruncate(fd, 0)
        os.write(fd, payload)
        os.fsync(fd)
    except BaseException:
        os.close(fd)
        raise
    _POSIX_LOCK_FD = fd
    return True


def release_lock():
    global _POSIX_LOCK_FD
    if os.name == 'nt':
        try:
            os.remove(LOCK)
        except OSError:
            pass
        return
    fd, _POSIX_LOCK_FD = _POSIX_LOCK_FD, None
    if fd is None:
        return
    try:
        os.lseek(fd, 0, os.SEEK_SET)
        os.ftruncate(fd, 0)
        os.write(fd, json.dumps(dict(locking='posix-flock', state='released',
                                     released_at=time.time())).encode('utf-8'))
        os.fsync(fd)
    finally:
        # Do not unlink or explicitly LOCK_UN: a surviving child inherits this open
        # file description and must keep the lock until its last descriptor closes.
        os.close(fd)


def run_child(cmd, env):
    kwargs = dict(env=env)
    if os.name != 'nt':
        kwargs['pass_fds'] = (_POSIX_LOCK_FD,)
    child = subprocess.Popen([sys.executable, *cmd], **kwargs)
    try:
        return child.wait()
    except BaseException:
        if child.poll() is None:
            child.terminate()
            try:
                child.wait(timeout=10)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait()
        raise


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-free-mb", type=int, default=700)
    ap.add_argument("--stale-min", type=float, default=90)
    ap.add_argument("--max-wait-min", type=float, default=60)
    ap.add_argument("cmd", nargs=argparse.REMAINDER)
    a = ap.parse_args()
    cmd = a.cmd[1:] if a.cmd[:1] == ["--"] else a.cmd
    if not cmd:
        ap.error("no command given")
    deadline = time.time() + a.max_wait_min * 60
    announced = False
    while True:
        if announced and time.time() >= deadline:
            print("[run_locked] gave up waiting for the lock", flush=True)
            return 75
        if try_lock(cmd, a.stale_min * 60):
            break
        if time.time() >= deadline:
            print("[run_locked] gave up waiting for the lock", flush=True)
            return 75
        if not announced:
            print("[run_locked] waiting for another D2 CAD process ...", flush=True)
            announced = True
        time.sleep(min(5, max(0.01, deadline - time.time())))
    try:
        while free_ram_mb() < a.min_free_mb:
            if time.time() > deadline:
                print(f"[run_locked] free RAM stayed below {a.min_free_mb} MB; not running", flush=True)
                return 75
            print(f"[run_locked] free RAM {free_ram_mb():.0f} MB < {a.min_free_mb} MB, waiting", flush=True)
            time.sleep(20)
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
        print(f"[run_locked] running (free RAM {free_ram_mb():.0f} MB): {' '.join(cmd)}", flush=True)
        return run_child(cmd, env)
    finally:
        release_lock()


if __name__ == "__main__":
    sys.exit(main())
