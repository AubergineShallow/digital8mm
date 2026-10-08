# SPDX-License-Identifier: MIT
"""Audit regressions, including blocked disk-worker and commit fault injection."""
from contextlib import redirect_stdout
from dataclasses import replace
import hashlib
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Event
import time
import unittest
from unittest import mock

from gs8_camera_evf.cli import main
from gs8_camera_evf.controller import Controller, State
from gs8_camera_evf.models import DroppedFrames, FilePayload, Frame
from gs8_camera_evf.storage import ClipStore, StorageError, incomplete_clips
from gs8_camera_evf.writer import AsyncClipWriter
from test_controller import BASE, MS, ScriptedBackend, camera, first_frame, request_release, saved_manifest, start_take, tick
from test_storage import SETTINGS, disposable_store, manifest


class AuditStorageTests(unittest.TestCase):
    def test_failed_directory_sync_after_replace_remains_in_incomplete_inventory(self):
        with disposable_store() as store:
            tx = store.begin(SETTINGS, True)
            tx.add_frame(0, 1, b'frame')
            with mock.patch('gs8_camera_evf.storage.sync_directory', side_effect=OSError('directory flush failed')):
                with self.assertRaises(OSError):
                    tx.finish()
            self.assertEqual(manifest(tx)['status'], 'complete')
            self.assertFalse((tx.path / 'commit.json').exists())
            self.assertEqual(incomplete_clips(store.root), [{'clip_id': tx.path.name, 'status': 'uncertain_commit'}])

    def test_receipt_failure_does_not_leave_a_successful_commit_receipt(self):
        with disposable_store() as store:
            tx = store.begin(SETTINGS, True)
            tx.add_frame(0, 1, b'frame')
            with mock.patch('gs8_camera_evf.storage.sync_directory', side_effect=[None, OSError('receipt flush failed')]):
                with self.assertRaises(OSError):
                    tx.finish()
            self.assertEqual(incomplete_clips(store.root)[0]['status'], 'uncertain_commit')

    def test_readonly_inspect_works_during_exclusive_recording_without_changes(self):
        with disposable_store() as store:
            tx = store.begin(SETTINGS, True)
            before = {p: p.read_bytes() for p in store.root.rglob('*') if p.is_file() and p.name != '.gs8-owner.lock'}
            lock_stat = (store.root / '.gs8-owner.lock').stat()
            output = io.StringIO()
            with redirect_stdout(output):
                self.assertEqual(main(['inspect', '--output', str(store.root)]), 0)
            self.assertEqual(json.loads(output.getvalue())['incomplete_clips'][0]['clip_id'], tx.path.name)
            self.assertEqual(before, {p: p.read_bytes() for p in store.root.rglob('*') if p.is_file() and p.name != '.gs8-owner.lock'})
            self.assertEqual(lock_stat, (store.root / '.gs8-owner.lock').stat())

    def test_context_cleanup_preserves_original_exception_and_releases_owner(self):
        with TemporaryDirectory() as folder:
            with self.assertRaisesRegex(ValueError, 'original failure'):
                with ClipStore(folder, reserve_bytes=0) as store:
                    tx = store.begin(SETTINGS, True)
                    raise ValueError('original failure')
            self.assertTrue(tx.closed)
            self.assertTrue(tx._journal.closed)
            with ClipStore(folder, reserve_bytes=0) as reopened:
                self.assertEqual(reopened.incomplete_clips()[0]['status'], 'recording')

    def test_frame_namespace_reserved_for_future_frames_case_insensitively(self):
        with disposable_store() as store:
            for filename in ('00000001.dng', '123456789.SIMFRAME', 'commit.json'):
                tx = store.begin(SETTINGS, True)
                with self.assertRaises(StorageError):
                    tx.add_artifact(filename, b'not a frame', 'attachment')
                tx.abandon()

    def test_file_handoff_and_mutable_buffers_preserve_exact_content(self):
        with disposable_store() as store:
            sensor = {'model': 'test_sensor', 'width': 800, 'height': 600, 'bit_depth': 12,
                      'mode': 'crop-test', 'crop': [20, 40, 800, 600], 'timestamp_clock': 'sensor_boot'}
            source = store.root / 'closed-source.dng'
            content = b'II*\x00' + bytes(range(256)) * 9000
            source.write_bytes(content)
            tx = store.begin(SETTINGS, False, sensor=sensor)
            metadata = {'exposure_us': 20000, 'analogue_gain': 1.125, 'colour_gains': [1.8, 1.4]}
            tx.accept_message(Frame(0, 100, FilePayload(source), metadata))
            tx.add_frame(1, 200, memoryview(bytearray(b'memory view')), applied_metadata=metadata)
            tx.finish()
            self.assertEqual(manifest(tx)['sensor'], sensor)
            self.assertEqual(manifest(tx)['frames'][0]['applied_metadata'], metadata)
            self.assertEqual(manifest(tx)['frames'][0]['sha256'], hashlib.sha256(content).hexdigest())
            self.assertEqual((tx.path / '00000000.dng').read_bytes(), content)
            self.assertTrue(source.exists(), 'backend owns staging cleanup after close')

    def test_explicit_tail_drops_and_backend_counts_are_not_lost(self):
        with disposable_store() as store:
            tx = store.begin(SETTINGS, True)
            tx.accept_message(Frame(0, 100, b'first'))
            tx.accept_message(DroppedFrames(1, 2, 'sensor_queue_overrun'))
            tx.finish(summary={'expected_frame_count': 1, 'source_frame_count': 3, 'stop_requested_ns': 200})
            self.assertEqual(manifest(tx)['status'], 'complete')
            self.assertEqual(manifest(tx)['dropped_frames'][0]['count'], 2)
            journal = (tx.path / 'frames.jsonl').read_text().splitlines()
            self.assertEqual(json.loads(journal[-1])['dropped_frames']['first_sequence'], 1)

    def test_missing_final_delivery_fails_producer_counter_check(self):
        with disposable_store() as store:
            tx = store.begin(SETTINGS, True)
            tx.accept_message(Frame(0, 100, b'first'))
            tx.finish(summary={'expected_frame_count': 2, 'source_frame_count': 2, 'stop_requested_ns': 200})
            self.assertEqual(manifest(tx)['status'], 'failed')
            self.assertIn('counters disagree', manifest(tx)['failure'])

    def test_directory_sync_covers_journal_creation_and_each_new_file(self):
        with disposable_store() as store:
            with mock.patch('gs8_camera_evf.storage.sync_directory') as flush:
                tx = store.begin(SETTINGS, True)
                self.assertGreaterEqual(sum(c.args == (tx.path,) for c in flush.call_args_list), 2)
                flush.reset_mock()
                tx.add_frame(0, 100, b'frame')
                tx.add_artifact('notes.bin', b'notes', 'notes')
                self.assertEqual(flush.call_args_list, [mock.call(tx.path), mock.call(tx.path)])

    def test_encoded_journal_has_durable_byte_ranges_before_finish(self):
        with disposable_store() as store:
            tx = store.begin(dict(SETTINGS, capture_format='encoded'), True)
            parts = (b'{"frame":0}\n', b'{"frame":1}\n')
            for i, part in enumerate(parts):
                tx.add_frame(i, i + 1, part)
                self.assertEqual((tx.path / 'take.simclip.jsonl').read_bytes(), b''.join(parts[:i + 1]))
            entries = [json.loads(line) for line in (tx.path / 'frames.jsonl').read_text().splitlines()]
            self.assertEqual(entries[1]['byte_offset'], len(parts[0]))
            self.assertEqual(entries[1]['sha256'], hashlib.sha256(parts[1]).hexdigest())


class AuditControllerTests(unittest.TestCase):
    def test_missing_or_weakened_backend_summary_never_completes_take(self):
        valid = {'expected_frame_count': 1, 'source_frame_count': 1,
                 'stop_requested_ns': 140 * MS, 'evidence': 'backend_counters'}
        invalid = [None, {}, {key: value for key, value in valid.items() if key != 'evidence'},
                   dict(valid, evidence='writer_observed_only'),
                   {key: value for key, value in valid.items() if key != 'source_frame_count'},
                   dict(valid, expected_frame_count=True), dict(valid, source_frame_count=-1),
                   dict(valid, source_frame_count=0), dict(valid, stop_requested_ns=None),
                   dict(valid, stop_requested_ns=True), dict(valid, stop_requested_ns=-1),
                   dict(valid, stop_requested_ns=139 * MS), dict(valid, stop_requested_ns=161 * MS)]
        for summary in invalid:
            with self.subTest(summary=summary), camera() as (controller, backend, _):
                start_take(controller)
                first_frame(controller, backend)
                # The producer independently knows one final image was lost.
                # Omitting its evidence must never substitute journal counts.
                backend.source_count = 2
                backend.final_summary = lambda: summary
                request_release(controller)
                backend.drain_ack = True
                tick(controller, 160, False)
                self.assertEqual(saved_manifest(controller)['status'], 'failed')
                self.assertEqual(controller.state, State.FAULT)
                self.assertIsNotNone(controller.failure)
                self.assertTrue(backend.closed)

    def test_zero_frame_cancel_still_requires_backend_counter_evidence(self):
        with camera() as (controller, backend, _):
            start_take(controller)
            backend.final_summary = lambda: None
            request_release(controller)
            backend.drain_ack = True
            tick(controller, 160, False)
            self.assertEqual(saved_manifest(controller)['status'], 'failed')
            self.assertEqual(controller.state, State.FAULT)
            self.assertIn('backend_counters', controller.failure)

    def test_cancel_before_first_frame_is_benign_and_next_press_records(self):
        with camera() as (controller, backend, _):
            start_take(controller, replace(BASE, audio=True))
            request_release(controller)
            backend.drain_ack = True
            tick(controller, 160, False)
            self.assertIsNone(controller.failure)
            self.assertEqual(saved_manifest(controller)['status'], 'cancelled')
            self.assertTrue(backend.closed)
            tick(controller, 180, False)
            tick(controller, 200, True)
            tick(controller, 220, True)
            self.assertEqual(len(backend.starts), 2)

    def test_uncalibrated_custom_wb_inhibits_and_dial_change_recovers(self):
        backend = ScriptedBackend()
        backend.simulated = False
        with camera(backend) as (controller, _, store):
            start_take(controller, replace(BASE, wb='custom'))
            self.assertEqual(controller.state, State.CHECK)
            self.assertIsNone(controller.failure)
            self.assertIsNone(store.active)
            tick(controller, 80, False)
            tick(controller, 100, False)
            tick(controller, 120, True)
            tick(controller, 140, True)
            self.assertEqual(controller.state, State.STARTING)

    def test_malformed_selection_during_take_cannot_starve_poll(self):
        with camera() as (controller, backend, _):
            start_take(controller)
            backend.frames = [Frame(0, 100 * MS, b'first')]
            tick(controller, 100, True, selection='invalid non-None selection')
            self.assertIn(100 * MS, backend.polls)
            self.assertEqual(controller.state, State.RECORDING)
            self.assertIsNone(controller.failure)
            self.assertEqual(controller.settings.fps, 18)

    def test_invalid_calibration_rejected_and_mutable_calibration_copied_at_construction(self):
        with disposable_store() as store:
            for gains in (1, '12', (0, 1), (1, float('nan')), (True, 1), (1,)):
                with self.assertRaises(ValueError):
                    Controller(store, ScriptedBackend(), wb_gains=gains)
            gains = [1.8, 1.4]
            controller = Controller(store, ScriptedBackend(), wb_gains=gains)
            gains[0] = 50
            self.assertEqual(controller.wb_gains, (1.8, 1.4))

    def test_begin_failure_still_stops_drains_and_closes_backend(self):
        with camera() as (controller, backend, store):
            with mock.patch.object(store, 'begin', side_effect=StorageError('reserve reached')):
                start_take(controller)
            self.assertEqual(len(backend.stops), 1)
            self.assertFalse(backend.closed)
            backend.drain_ack = True
            tick(controller, 80, False)
            self.assertTrue(backend.closed)
            self.assertIsNone(store.active)

    def test_writer_startup_failure_releases_handles_only_after_backend_drain(self):
        factory = mock.Mock(side_effect=RuntimeError('worker unavailable'))
        with camera(writer_factory=factory) as (controller, backend, store):
            start_take(controller)
            self.assertEqual(len(backend.stops), 1)
            self.assertIsNotNone(store.active)
            backend.drain_ack = True
            tick(controller, 80, False)
            self.assertTrue(backend.closed)
            self.assertIsNone(store.active)
            self.assertEqual(store.incomplete_clips()[0]['status'], 'recording')

    def test_close_error_withholds_poweroff_and_is_retried(self):
        with camera() as (controller, backend, _):
            start_take(controller)
            first_frame(controller, backend)
            backend.drain_ack = True
            with mock.patch.object(backend, 'close', side_effect=OSError('device still closing')):
                tick(controller, 120, True, shutdown=True)
                self.assertFalse(controller.safe_to_request_poweroff)
            tick(controller, 140, True)
            self.assertTrue(controller.safe_to_request_poweroff)

    def test_blocked_writer_does_not_block_trigger_sampling_or_claim_shutdown(self):
        release = Event()
        entered = Event()
        with camera(writer_factory=AsyncClipWriter) as (controller, backend, store):
            start_take(controller)
            original = store.active._write_payload

            def blocked(*args):
                entered.set()
                if not release.wait(5):
                    raise TimeoutError('test did not release writer')
                return original(*args)

            try:
                with mock.patch.object(store.active, '_write_payload', side_effect=blocked):
                    before = time.monotonic()
                    first_frame(controller, backend)
                    self.assertLess(time.monotonic() - before, 0.2)
                    self.assertTrue(entered.wait(2))
                    before = time.monotonic()
                    request_release(controller)
                    backend.drain_ack = True
                    tick(controller, 160, False, shutdown=True)
                    self.assertLess(time.monotonic() - before, 0.2)
                    self.assertEqual(controller.state, State.STOPPING)
                    self.assertFalse(controller.safe_to_request_poweroff)
                    self.assertFalse(backend.closed)
                    release.set()
                    controller._finish_future.result(timeout=5)
                    tick(controller, 180, False)
                    self.assertTrue(controller.safe_to_request_poweroff)
                    self.assertTrue(backend.closed)
            finally:
                release.set()
                if controller._writer:
                    controller._writer.wait_idle()
                    if controller._finish_future:
                        controller._finish_future.result(timeout=5)
                        tick(controller, 200, False)

    def test_bounded_queue_overload_faults_without_waiting_or_silently_dropping(self):
        release, entered = Event(), Event()
        with camera(writer_factory=lambda tx: AsyncClipWriter(tx, capacity=1)) as (controller, backend, store):
            start_take(controller)
            original = store.active._write_payload

            def blocked(*args):
                entered.set()
                release.wait(5)
                return original(*args)

            try:
                with mock.patch.object(store.active, '_write_payload', side_effect=blocked):
                    first_frame(controller, backend)
                    self.assertTrue(entered.wait(2))
                    backend.frames = [Frame(1, 110 * MS, b'over capacity')]
                    before = time.monotonic()
                    tick(controller, 110, True)
                    self.assertLess(time.monotonic() - before, 0.2)
                    self.assertEqual(controller.state, State.FAULT)
                    self.assertIn('queue is full', controller.failure)
                    backend.drain_ack = True
                    tick(controller, 120, False)
                    release.set()
                    controller._finish_future.result(timeout=5)
                    tick(controller, 140, False)
                    self.assertEqual(saved_manifest(controller)['status'], 'failed')
            finally:
                release.set()
                if controller._writer:
                    controller._writer.wait_idle()
                    if controller._finish_future:
                        controller._finish_future.result(timeout=5)
                        tick(controller, 160, False)


if __name__ == '__main__':
    unittest.main()

