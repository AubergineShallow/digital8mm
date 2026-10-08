# SPDX-License-Identifier: MIT
# Copyright (c) 2026 GS8 contributors
"""Storage failure and process-ownership tests, using only disposable folders."""

from contextlib import contextmanager
import errno
import hashlib
import json
import os
from pathlib import Path
import queue
import subprocess
import sys
from tempfile import TemporaryDirectory
import threading
import unittest
from unittest import mock

from gs8_camera_evf.storage import ClipStore, StorageError


SETTINGS = {
    "fps": 18,
    "shutter_angle": 180,
    "analogue_gain": 1.0,
    "wb": "5600",
    "capture_format": "raw",
    "look": "clean",
    "audio": False,
}


@contextmanager
def disposable_store():
    with TemporaryDirectory(prefix="gs8-storage-test-") as directory:
        store = ClipStore(Path(directory), reserve_bytes=0)
        try:
            yield store
        finally:
            if store.active is not None:
                store.active.abandon()
            store.close()


def manifest(transaction):
    return json.loads((transaction.path / "manifest.json").read_text(encoding="utf-8"))


def finish_after_io_failure(transaction):
    """Either reject finalization or publish failed; neither may claim complete."""
    try:
        transaction.finish()
    except StorageError:
        pass


class StorageTransactionTests(unittest.TestCase):
    def test_raw_commit_contains_exact_bytes_hashes_and_journal(self):
        with disposable_store() as store:
            tx = store.begin(dict(SETTINGS), simulated=True)
            self.assertEqual(manifest(tx)["status"], "recording")
            payloads = (b"frame-zero\n", b"frame-one\n")
            for index, payload in enumerate(payloads):
                tx.add_frame(index, 1_000_000 + index * 55_555_556, payload)
            tx.add_artifact("audio-test.bin", b"synthetic-audio", "simulated_audio")
            path = tx.finish()
            committed = manifest(tx)
            self.assertEqual(path, tx.path)
            self.assertEqual(committed["status"], "complete")
            self.assertTrue(committed["simulated"])
            self.assertIsNone(store.active)
            self.assertTrue(tx.closed)
            for entry, payload in zip(committed["frames"], payloads):
                self.assertEqual((tx.path / entry["filename"]).read_bytes(), payload)
                self.assertEqual(entry["size_bytes"], len(payload))
                self.assertEqual(entry["sha256"], hashlib.sha256(payload).hexdigest())
            journal = [json.loads(line) for line in (tx.path / "frames.jsonl").read_text().splitlines()]
            self.assertEqual(journal, committed["frames"])
            self.assertEqual(store.incomplete_clips(), [])

    def test_encoded_commit_flushes_single_container_and_hash(self):
        with disposable_store() as store:
            tx = store.begin(dict(SETTINGS, capture_format="encoded"), simulated=True)
            parts = (b'{"frame":0}\n', b'{"frame":1}\n')
            tx.add_frame(0, 0, parts[0])
            tx.add_frame(1, 55_555_556, parts[1])
            tx.finish()
            data = b"".join(parts)
            committed = manifest(tx)
            container = committed["artifacts"][0]
            self.assertEqual(container["kind"], "simulated_encoded")
            self.assertEqual((tx.path / container["filename"]).read_bytes(), data)
            self.assertEqual(container["size_bytes"], len(data))
            self.assertEqual(container["sha256"], hashlib.sha256(data).hexdigest())
            self.assertFalse(list(tx.path.glob("*.simframe")))
            self.assertTrue(tx._encoded.closed)
            self.assertTrue(tx._journal.closed)

    def test_zero_frames_never_publish_complete(self):
        with disposable_store() as store:
            for mode in ("raw", "encoded"):
                tx = store.begin(dict(SETTINGS, capture_format=mode), simulated=True)
                tx.finish()
                self.assertEqual(manifest(tx)["status"], "failed")
                self.assertIn("no frames", manifest(tx)["failure"])

    def test_explicit_capture_failure_is_retained(self):
        with disposable_store() as store:
            tx = store.begin(dict(SETTINGS), simulated=True)
            tx.add_frame(0, 1, b"one")
            tx.finish(failure="camera disconnected")
            self.assertEqual(manifest(tx)["status"], "failed")
            self.assertEqual(manifest(tx)["failure"], "camera disconnected")
            self.assertEqual(store.incomplete_clips(), [{"clip_id": tx.path.name, "status": "failed"}])

    def test_frame_sequence_and_timestamp_corruption_is_rejected(self):
        with disposable_store() as store:
            for bad_index in (-1, 1, True, 0.0):
                tx = store.begin(dict(SETTINGS), simulated=True)
                with self.assertRaises(StorageError):
                    tx.add_frame(bad_index, 10, b"one")
                self.assertEqual(tx.manifest["frames"], [])
                tx.abandon()
            for bad_timestamp in (-1, 9, 10, True, 11.0):
                tx = store.begin(dict(SETTINGS), simulated=True)
                tx.add_frame(0, 10, b"one")
                with self.assertRaises(StorageError):
                    tx.add_frame(1, bad_timestamp, b"two")
                self.assertEqual(len(tx.manifest["frames"]), 1)
                self.assertEqual(len(list(tx.path.glob("*.simframe"))), 1)
                tx.abandon()
            tx = store.begin(dict(SETTINGS), simulated=True)
            tx.add_frame(0, 10, b"one")
            with self.assertRaises(StorageError):
                tx.add_frame(0, 11, b"duplicate")
            self.assertEqual(len(tx.manifest["frames"]), 1)
            self.assertEqual(len(list(tx.path.glob("*.simframe"))), 1)

    def test_payload_validation_has_no_filesystem_side_effect(self):
        with disposable_store() as store:
            for payload in (b"", "text", None):
                tx = store.begin(dict(SETTINGS), simulated=True)
                before = set(tx.path.iterdir())
                with self.assertRaises(StorageError):
                    tx.add_frame(0, 1, payload)
                self.assertEqual(set(tx.path.iterdir()), before)
                tx.abandon()

    def test_exclusive_frame_and_artifact_creation_never_overwrites(self):
        with disposable_store() as store:
            tx = store.begin(dict(SETTINGS), simulated=True)
            frame = tx.path / "00000000.simframe"
            frame.write_bytes(b"existing evidence")
            with self.assertRaises(OSError):
                tx.add_frame(0, 1, b"replacement")
            self.assertEqual(frame.read_bytes(), b"existing evidence")
            tx.abandon()
            tx = store.begin(dict(SETTINGS), simulated=True)
            artifact = tx.path / "notes.bin"
            artifact.write_bytes(b"original")
            with self.assertRaises(OSError):
                tx.add_artifact("notes.bin", b"replacement", "test")
            self.assertEqual(artifact.read_bytes(), b"original")

    def test_artifact_path_escape_and_manifest_overwrite_are_rejected(self):
        with disposable_store() as store:
            for name in ("../escaped.bin", "child/escaped.bin", "manifest.json", "frames.jsonl", ".", "..", "take.simclip.jsonl", "NUL", "audio.bin:stream", "trailing."):
                tx = store.begin(dict(SETTINGS), simulated=True)
                before = (tx.path / "manifest.json").read_bytes()
                with self.assertRaises(StorageError):
                    tx.add_artifact(name, b"bad", "test")
                self.assertEqual((tx.path / "manifest.json").read_bytes(), before)
                tx.abandon()
            self.assertFalse((store.root / "escaped.bin").exists())

    def test_disk_space_precheck_rejects_frame_without_starting_write(self):
        with disposable_store() as store:
            tx = store.begin(dict(SETTINGS), simulated=True)
            before = set(tx.path.iterdir())
            with mock.patch.object(store, "free_bytes", return_value=2):
                with self.assertRaises(StorageError):
                    tx.add_frame(0, 1, b"three")
            self.assertEqual(set(tx.path.iterdir()), before)
            self.assertEqual(tx.manifest["frames"], [])

    def test_disk_full_after_prior_frame_cannot_be_finalized_complete(self):
        with disposable_store() as store:
            tx = store.begin(dict(SETTINGS), simulated=True)
            tx.add_frame(0, 1, b"one")
            with mock.patch("gs8_camera_evf.storage.os.fsync", side_effect=OSError(errno.ENOSPC, "disk full")):
                with self.assertRaises(OSError):
                    tx.add_frame(1, 2, b"partly durable second frame")
            finish_after_io_failure(tx)
            self.assertNotEqual(manifest(tx)["status"], "complete")

    def test_journal_failure_after_frame_file_cannot_be_finalized_complete(self):
        with disposable_store() as store:
            tx = store.begin(dict(SETTINGS), simulated=True)
            tx.add_frame(0, 1, b"one")
            journal = mock.Mock(wraps=tx._journal)
            journal.write.side_effect = OSError(errno.EIO, "journal write failed")
            with mock.patch.object(tx, "_journal", journal):
                with self.assertRaises(OSError):
                    tx.add_frame(1, 2, b"unindexed frame")
            finish_after_io_failure(tx)
            self.assertNotEqual(manifest(tx)["status"], "complete")

    def test_artifact_failure_cannot_be_finalized_complete(self):
        with disposable_store() as store:
            tx = store.begin(dict(SETTINGS), simulated=True)
            tx.add_frame(0, 1, b"one")
            with mock.patch("gs8_camera_evf.storage.os.fsync", side_effect=OSError(errno.EIO, "audio write failed")):
                with self.assertRaises(OSError):
                    tx.add_artifact("audio-test.bin", b"partial audio", "simulated_audio")
            finish_after_io_failure(tx)
            self.assertNotEqual(manifest(tx)["status"], "complete")

    def test_failed_manifest_replace_leaves_recording_status_and_no_temporary_file(self):
        with disposable_store() as store:
            tx = store.begin(dict(SETTINGS), simulated=True)
            tx.add_frame(0, 1, b"one")
            with mock.patch("gs8_camera_evf.storage.os.replace", side_effect=OSError(errno.EIO, "rename failed")):
                with self.assertRaises(OSError):
                    tx.finish()
            self.assertEqual(manifest(tx)["status"], "recording")
            self.assertFalse(list(tx.path.glob("*.tmp")))
            self.assertNotEqual(store.incomplete_clips(), [])

    def test_encoded_finalize_failure_does_not_publish_complete(self):
        with disposable_store() as store:
            tx = store.begin(dict(SETTINGS, capture_format="encoded"), simulated=True)
            tx.add_frame(0, 1, b'{"frame":0}\n')
            with mock.patch("gs8_camera_evf.storage.os.fsync", side_effect=OSError(errno.EIO, "container flush failed")):
                with self.assertRaises(OSError):
                    tx.finish()
            self.assertEqual(manifest(tx)["status"], "recording")

    def test_initialization_failure_closes_every_handle_it_opened(self):
        with disposable_store() as store:
            opened = []
            real_open = Path.open

            def capture_open(path, *args, **kwargs):
                stream = real_open(path, *args, **kwargs)
                if path.name in ("frames.jsonl", "take.simclip.jsonl"):
                    opened.append(stream)
                return stream

            try:
                with mock.patch.object(Path, "open", new=capture_open):
                    with self.assertRaises(StorageError):
                        store.begin(dict(SETTINGS, capture_format="encoded"), simulated=False)
                self.assertIsNone(store.active)
                self.assertTrue(all(stream.closed for stream in opened), "constructor leaked a capture handle")
            finally:
                for stream in opened:
                    stream.close()

    def test_abandon_releases_other_handles_when_container_close_raises(self):
        with disposable_store() as store:
            tx = store.begin(dict(SETTINGS, capture_format="encoded"), simulated=True)
            tx.add_frame(0, 1, b'{"frame":0}\n')
            encoded = tx._encoded
            proxy = mock.Mock(wraps=encoded)
            proxy.closed = False

            def failing_close():
                encoded.close()
                raise OSError(errno.EIO, "close reported a late flush error")

            proxy.close.side_effect = failing_close
            with mock.patch.object(tx, "_encoded", proxy):
                try:
                    tx.abandon()
                except (OSError, StorageError):
                    pass
            self.assertTrue(tx._journal.closed, "journal leaked after container close failed")
            self.assertTrue(tx.closed)
            self.assertIsNone(store.active)
            self.assertNotEqual(manifest(tx)["status"], "complete")

    def test_abandon_old_closed_transaction_does_not_clear_current_owner(self):
        with disposable_store() as store:
            old = store.begin(dict(SETTINGS), simulated=True)
            old.add_frame(0, 1, b"one")
            old.finish()
            current = store.begin(dict(SETTINGS), simulated=True)
            try:
                old.abandon()
                self.assertIs(store.active, current)
                with self.assertRaises(StorageError):
                    store.begin(dict(SETTINGS), simulated=True)
            finally:
                current.abandon()

    def test_constructor_io_failure_closes_previously_opened_journal(self):
        with disposable_store() as store:
            opened = []
            real_open = Path.open

            def capture_open(path, *args, **kwargs):
                if path.name == "take.simclip.jsonl":
                    raise OSError(errno.ENOSPC, "cannot create encoded container")
                stream = real_open(path, *args, **kwargs)
                if path.name == "frames.jsonl":
                    opened.append(stream)
                return stream

            try:
                with mock.patch.object(Path, "open", new=capture_open):
                    with self.assertRaises(OSError):
                        store.begin(dict(SETTINGS, capture_format="encoded"), simulated=True)
                self.assertIsNone(store.active)
                self.assertTrue(opened)
                self.assertTrue(all(stream.closed for stream in opened))
            finally:
                for stream in opened:
                    stream.close()

    def test_retry_after_commit_error_can_only_publish_failed(self):
        with disposable_store() as store:
            for mode in ("raw", "encoded"):
                tx = store.begin(dict(SETTINGS, capture_format=mode), simulated=True)
                tx.add_frame(0, 1, b'{"frame":0}\n')
                with mock.patch("gs8_camera_evf.storage.os.replace", side_effect=OSError(errno.EIO, "rename failed")):
                    with self.assertRaises(OSError):
                        tx.finish()
                tx.finish()
                self.assertEqual(manifest(tx)["status"], "failed")
                self.assertIn("rename failed", manifest(tx)["failure"])

    def test_rejected_write_poison_inhibits_subsequent_writes_and_complete_status(self):
        with disposable_store() as store:
            tx = store.begin(dict(SETTINGS), simulated=True)
            tx.add_frame(0, 1, b"one")
            with self.assertRaises(StorageError):
                tx.add_frame(2, 2, b"gap")
            with self.assertRaises(StorageError):
                tx.add_frame(1, 2, b"retry")
            with self.assertRaises(StorageError):
                tx.add_artifact("audio.bin", b"audio", "test")
            tx.finish()
            self.assertEqual(manifest(tx)["status"], "failed")

    def test_empty_failure_reason_cannot_turn_empty_take_into_complete(self):
        with disposable_store() as store:
            tx = store.begin(dict(SETTINGS), simulated=True)
            with self.assertRaises(StorageError):
                tx.finish(failure="")
            self.assertNotEqual(manifest(tx)["status"], "complete")

    def test_inventory_tolerates_missing_invalid_and_non_object_json(self):
        with disposable_store() as store:
            specimens = {"missing": None, "bad-json": "{", "array": "[]", "null": "null", "scalar": "42"}
            for name, contents in specimens.items():
                directory = store.root / name
                directory.mkdir()
                if contents is not None:
                    (directory / "manifest.json").write_text(contents, encoding="utf-8")
            before = {p: p.read_bytes() for p in store.root.rglob("manifest.json")}
            found = store.incomplete_clips()
            self.assertEqual({item["clip_id"] for item in found}, set(specimens))
            self.assertTrue(all(item["status"] == "missing_or_invalid_manifest" for item in found))
            self.assertEqual({p: p.read_bytes() for p in store.root.rglob("manifest.json")}, before)

    def test_only_one_clip_active_and_closed_objects_reject_writes(self):
        with disposable_store() as store:
            tx = store.begin(dict(SETTINGS), simulated=True)
            with self.assertRaises(StorageError):
                store.begin(dict(SETTINGS), simulated=True)
            with self.assertRaises(StorageError):
                store.close()
            tx.add_frame(0, 1, b"one")
            tx.finish()
            with self.assertRaises(StorageError):
                tx.add_frame(1, 2, b"two")
            with self.assertRaises(StorageError):
                tx.finish()
            with self.assertRaises(StorageError):
                tx.add_artifact("late.bin", b"late", "test")
            store.close()
            with self.assertRaises(StorageError):
                store.begin(dict(SETTINGS), simulated=True)


class StorageOwnershipTests(unittest.TestCase):
    def test_second_owner_is_rejected_and_close_releases_same_lock_file(self):
        with TemporaryDirectory(prefix="gs8-lock-test-") as directory:
            root = Path(directory)
            first = ClipStore(root, reserve_bytes=0)
            lock_inode = (root / ".gs8-owner.lock").stat().st_ino
            try:
                with self.assertRaises(StorageError):
                    ClipStore(root, reserve_bytes=0)
            finally:
                first.close()
            with ClipStore(root, reserve_bytes=0):
                self.assertEqual((root / ".gs8-owner.lock").stat().st_ino, lock_inode)

    def test_process_crash_releases_os_owner_without_deleting_lock_file(self):
        with TemporaryDirectory(prefix="gs8-crash-test-") as directory:
            source_root = str(Path(__file__).resolve().parents[1])
            environment = dict(os.environ)
            environment["PYTHONPATH"] = source_root + os.pathsep + environment.get("PYTHONPATH", "")
            program = (
                "from pathlib import Path\n"
                "from gs8_camera_evf.storage import ClipStore\n"
                "import os, sys\n"
                "owner = ClipStore(Path(sys.argv[1]), reserve_bytes=0)\n"
                "print('locked', flush=True)\n"
                "sys.stdin.readline()\n"
                "os._exit(23)\n"
            )
            process = subprocess.Popen(
                [sys.executable, "-c", program, directory],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, env=environment,
            )
            try:
                # Bound child startup observation, including unexpected imports/hangs.
                startup = queue.Queue()
                reader = threading.Thread(target=lambda: startup.put(process.stdout.readline()), daemon=True)
                reader.start()
                self.assertEqual(startup.get(timeout=10).strip(), "locked")
                with self.assertRaises(StorageError):
                    ClipStore(Path(directory), reserve_bytes=0)
                output, errors = process.communicate("crash\n", timeout=10)
                self.assertEqual(process.returncode, 23, errors + output)
                self.assertTrue((Path(directory) / ".gs8-owner.lock").exists())
                with ClipStore(Path(directory), reserve_bytes=0) as reopened:
                    self.assertIsNone(reopened.active)
            finally:
                if process.poll() is None:
                    process.kill()
                    process.wait(timeout=10)
                for pipe in (process.stdin, process.stdout, process.stderr):
                    if pipe is not None:
                        pipe.close()


if __name__ == "__main__":
    unittest.main()

