# SPDX-License-Identifier: MIT
"""Project-local execution-lock tests; no geometry or system configuration changes."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
import run_locked as R


@unittest.skipIf(os.name == 'nt', 'POSIX kernel-lock tests')
class PosixLockTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='d2-lock-test-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        patcher = patch.object(R, 'LOCK', str(self.root / '.cad.lock'))
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(R.release_lock)

    def test_stable_inode_and_released_metadata(self):
        self.assertTrue(R.try_lock(['first'], 0))
        inode = os.stat(R.LOCK).st_ino
        R.release_lock()
        self.assertEqual(json.loads(Path(R.LOCK).read_text())['state'], 'released')
        self.assertTrue(R.try_lock(['second'], 0))
        self.assertEqual(os.stat(R.LOCK).st_ino, inode)

    def test_live_lock_never_uses_namespace_pid_or_age(self):
        self.assertTrue(R.try_lock(['holder'], 0))
        before = Path(R.LOCK).read_bytes()
        with patch.object(R, 'pid_alive', side_effect=AssertionError('PID check forbidden on POSIX')):
            self.assertFalse(R.try_lock(['contender'], -999))
        self.assertEqual(Path(R.LOCK).read_bytes(), before)

    def test_child_keeps_lock_after_wrapper_is_terminated(self):
        runner = self.root / 'run_locked.py'
        runner.write_text(Path(R.__file__).read_text())
        probe = self.root / 'probe.py'
        started, finished = self.root / 'started', self.root / 'finished'
        probe.write_text('from pathlib import Path\nimport time\n'
                         'Path(%r).write_text("started")\ntime.sleep(2)\nPath(%r).write_text("finished")\n'
                         % (str(started), str(finished)))
        parent = subprocess.Popen([sys.executable, str(runner), '--min-free-mb', '0', '--', str(probe)],
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.addCleanup(lambda: parent.kill() if parent.poll() is None else None)
        deadline = time.monotonic() + 10
        while not started.exists() and time.monotonic() < deadline:
            time.sleep(0.02)
        self.assertTrue(started.exists())
        parent.terminate()
        parent.wait(timeout=5)
        self.assertFalse(R.try_lock(['too-early'], 0), 'Child must retain its inherited lock')
        while not finished.exists() and time.monotonic() < deadline:
            time.sleep(0.02)
        self.assertTrue(finished.exists())
        while not R.try_lock(['after-child'], 0) and time.monotonic() < deadline:
            time.sleep(0.02)
        self.assertIsNotNone(R._POSIX_LOCK_FD)

    def test_foreign_process_times_out_without_running_command(self):
        self.assertTrue(R.try_lock(['holder'], 0))
        runner = self.root / 'run_locked.py'
        runner.write_text(Path(R.__file__).read_text())
        marker = self.root / 'should-not-exist'
        result = subprocess.run([sys.executable, str(runner), '--max-wait-min', '0.002', '--',
                                 '-c', 'from pathlib import Path;Path(%r).touch()' % str(marker)],
                                capture_output=True, text=True, timeout=5)
        self.assertEqual(result.returncode, 75, result.stdout + result.stderr)
        self.assertFalse(marker.exists())
        self.assertNotIn('broke stale lock', result.stdout)


class WindowsCompatibilityTests(unittest.TestCase):
    def test_windows_metadata_creation_and_cleanup_path_retained(self):
        with tempfile.TemporaryDirectory() as td:
            lock = str(Path(td) / '.cad.lock')
            with patch.object(R, 'LOCK', lock), patch.object(R.os, 'name', 'nt'):
                self.assertTrue(R.try_lock(['example.py'], 5400))
                with open(lock, encoding='utf-8') as stream:
                    self.assertEqual(json.load(stream)['cmd'], ['example.py'])
                R.release_lock()
                self.assertFalse(os.path.exists(lock))


if __name__ == '__main__':
    unittest.main(verbosity=2)
