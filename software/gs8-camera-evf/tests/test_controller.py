# SPDX-License-Identifier: MIT
# Copyright (c) 2026 GS8 contributors
"""Screenless recording state-machine tests with fault-injected virtual devices.

These tests establish software behavior, not Pi timing, GPIO, audio, or sensor
performance. All capture paths are fresh TemporaryDirectory instances.
"""

from contextlib import contextmanager
from dataclasses import replace
import errno
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest import mock
import wave

from gs8_camera_evf.backends import SIMULATION_SENSOR, SimulationBackend
from gs8_camera_evf.controller import Controller, State
from gs8_camera_evf.controls import ControlSelection
from gs8_camera_evf.models import Artifact, AudioInfo, Frame, TakeSettings
from gs8_camera_evf.storage import ClipStore
from gs8_camera_evf.writer import InlineClipWriter


BASE = ControlSelection(18, 180, 1.0, "5600", "raw", "film", False)
ALTERNATE = ControlSelection(24, 90, 4.0, "3200", "encoded", "pxl", False)
MS = 1_000_000


class ScriptedBackend:
    """Independent stop-request and drain-ack controls, plus injected failures."""

    simulated = True

    def __init__(self):
        self.starts = []
        self.stops = []
        self.polls = []
        self.frames = []
        self.returned_artifacts = []
        self.drain_ack = False
        self.preflight_error = None
        self.start_error = None
        self.poll_error = None
        self.stop_error = None
        self.drain_error = None
        self.artifact_error = None
        self.delivered = 0
        self.source_count = 0
        self.closed = False

    def preflight(self, settings):
        if self.preflight_error:
            raise self.preflight_error
        return dict(SIMULATION_SENSOR)

    def start(self, settings, now_ns):
        self.starts.append((settings, now_ns))
        self.delivered = self.source_count = 0
        self.closed = False
        if self.start_error:
            raise self.start_error

    def poll(self, now_ns):
        self.polls.append(now_ns)
        if self.poll_error:
            raise self.poll_error
        ready, self.frames = self.frames, []
        self.delivered += len(ready)
        if ready:
            self.source_count = ready[-1].index + 1
        return ready

    def request_stop(self, now_ns):
        self.stops.append(now_ns)
        if self.stop_error:
            raise self.stop_error

    def drained(self, now_ns):
        if self.drain_error:
            raise self.drain_error
        return self.drain_ack

    def artifacts(self):
        if self.artifact_error:
            raise self.artifact_error
        return self.returned_artifacts

    def final_summary(self):
        return {'expected_frame_count': self.delivered, 'source_frame_count': self.source_count,
                'stop_requested_ns': self.stops[-1], 'evidence': 'backend_counters'}

    def close(self):
        self.closed = True


@contextmanager
def camera(backend=None, **options):
    with TemporaryDirectory(prefix="gs8-controller-test-") as directory:
        store = ClipStore(Path(directory), reserve_bytes=0)
        backend = backend if backend is not None else ScriptedBackend()
        options.setdefault('writer_factory', InlineClipWriter)
        controller = Controller(store, backend, **options)
        try:
            yield controller, backend, store
        finally:
            if store.active is not None:
                store.active.abandon()
            store.close()


def tick(controller, milliseconds, pressed, selection=BASE, shutdown=False):
    return controller.step(milliseconds * MS, selection, trigger_pressed=pressed,
                           shutdown_requested=shutdown)


def start_take(controller, selection=BASE):
    tick(controller, 0, False, selection)
    tick(controller, 20, False, selection)
    tick(controller, 40, True, selection)
    return tick(controller, 60, True, selection)


def first_frame(controller, backend, selection=BASE):
    backend.frames.append(Frame(0, 100 * MS, b"synthetic first frame"))
    return tick(controller, 100, True, selection)


def request_release(controller, selection=BASE):
    tick(controller, 120, False, selection)
    return tick(controller, 140, False, selection)


def saved_manifest(controller):
    return json.loads((controller.last_clip / "manifest.json").read_text(encoding="utf-8"))


class TriggerAndSelectionTests(unittest.TestCase):
    def test_trigger_held_at_startup_requires_release_then_new_press(self):
        with camera() as (controller, backend, store):
            for when in (0, 20, 100):
                tick(controller, when, True)
            self.assertEqual(backend.starts, [])
            self.assertIsNone(store.active)
            tick(controller, 120, False)
            tick(controller, 140, False)
            tick(controller, 160, True)
            self.assertEqual(tick(controller, 180, True), State.STARTING)
            self.assertEqual(len(backend.starts), 1)

    def test_press_bounce_requires_entire_new_stable_interval(self):
        with camera() as (controller, backend, _):
            tick(controller, 0, False)
            tick(controller, 20, False)
            for when, pressed in ((40, True), (50, False), (55, True), (74, True)):
                tick(controller, when, pressed)
                self.assertEqual(backend.starts, [])
            self.assertEqual(tick(controller, 75, True), State.STARTING)

    def test_release_bounce_does_not_prematurely_stop_take(self):
        with camera() as (controller, backend, _):
            start_take(controller)
            first_frame(controller, backend)
            for when, pressed in ((120, False), (130, True), (140, False), (159, False)):
                tick(controller, when, pressed)
                self.assertEqual(backend.stops, [])
                self.assertEqual(controller.state, State.RECORDING)
            self.assertEqual(tick(controller, 160, False), State.STOPPING)
            self.assertEqual(len(backend.stops), 1)

    def test_rec_is_steady_only_after_a_frame_is_accepted(self):
        with camera() as (controller, backend, _):
            self.assertEqual(start_take(controller), State.STARTING)
            self.assertEqual(controller.indicators()["rec"], "slow_blink")
            tick(controller, 80, True)
            self.assertEqual(controller.state, State.STARTING)
            self.assertEqual(first_frame(controller, backend), State.RECORDING)
            self.assertEqual(controller.indicators()["rec"], "steady")
            names = [event["event"] for event in controller.events]
            self.assertEqual(names.count("first_frame_accepted"), 1)

    def test_dials_are_frozen_through_invalid_samples_and_apply_next_take(self):
        with camera() as (controller, backend, _):
            start_take(controller)
            first_frame(controller, backend, ALTERNATE)
            tick(controller, 110, True, None)
            self.assertEqual(controller.settings.fps, 18)
            self.assertEqual(controller.settings.capture_format, "raw")
            request_release(controller, ALTERNATE)
            backend.drain_ack = True
            tick(controller, 160, False, ALTERNATE)
            committed = saved_manifest(controller)
            self.assertEqual(committed["settings"]["fps"], 18)
            self.assertEqual(committed["settings"]["capture_format"], "raw")
            tick(controller, 180, False, ALTERNATE)
            tick(controller, 200, True, ALTERNATE)
            tick(controller, 220, True, ALTERNATE)
            self.assertEqual(len(backend.starts), 2)
            self.assertEqual(backend.starts[1][0].fps, 24)
            self.assertEqual(backend.starts[1][0].capture_format, "encoded")

    def test_press_during_invalid_selector_is_not_queued_for_later(self):
        with camera() as (controller, backend, _):
            tick(controller, 0, False)
            tick(controller, 20, False)
            tick(controller, 40, True, None)
            self.assertEqual(tick(controller, 60, True, None), State.CHECK)
            tick(controller, 80, True)
            tick(controller, 100, True)
            self.assertEqual(backend.starts, [])
            tick(controller, 120, False)
            tick(controller, 140, False)
            tick(controller, 160, True)
            tick(controller, 180, True)
            self.assertEqual(len(backend.starts), 1)

    def test_repress_while_closing_cannot_start_next_clip_until_new_release(self):
        with camera() as (controller, backend, _):
            start_take(controller)
            first_frame(controller, backend)
            request_release(controller)
            tick(controller, 150, True)
            tick(controller, 170, True)
            backend.drain_ack = True
            tick(controller, 180, True)
            tick(controller, 220, True)
            self.assertEqual(len(backend.starts), 1)
            tick(controller, 240, False)
            tick(controller, 260, False)
            tick(controller, 280, True)
            tick(controller, 300, True)
            self.assertEqual(len(backend.starts), 2)


class DrainAndShutdownTests(unittest.TestCase):
    def test_stop_request_waits_for_final_queued_frame_and_explicit_drain(self):
        with camera() as (controller, backend, store):
            start_take(controller)
            first_frame(controller, backend)
            self.assertEqual(request_release(controller), State.STOPPING)
            self.assertEqual(controller.indicators()["rec"], "fast_blink")
            self.assertIsNotNone(store.active)
            backend.frames.append(Frame(1, 130 * MS, b"queued before stop"))
            tick(controller, 160, False)
            self.assertEqual(controller.state, State.STOPPING)
            self.assertEqual(len(store.active.manifest["frames"]), 2)
            self.assertEqual(len(backend.stops), 1)
            backend.drain_ack = True
            tick(controller, 180, False)
            self.assertIsNone(store.active)
            self.assertEqual(saved_manifest(controller)["status"], "complete")
            self.assertEqual(len(saved_manifest(controller)["frames"]), 2)

    def test_unsolicited_drain_ack_does_not_close_running_take(self):
        with camera() as (controller, backend, store):
            start_take(controller)
            backend.drain_ack = True
            first_frame(controller, backend)
            self.assertEqual(controller.state, State.RECORDING)
            self.assertIsNotNone(store.active)

    def test_non_boolean_drain_response_is_not_accepted_as_shutdown_ack(self):
        with camera() as (controller, backend, store):
            start_take(controller)
            first_frame(controller, backend)
            backend.drain_ack = "not drained"
            tick(controller, 120, True, shutdown=True)
            self.assertFalse(controller.safe_to_request_poweroff)
            self.assertEqual(controller.state, State.FAULT)
            self.assertIsNotNone(store.active)

    def test_shutdown_latches_until_drain_and_durable_close(self):
        with camera() as (controller, backend, store):
            start_take(controller)
            first_frame(controller, backend)
            self.assertEqual(tick(controller, 120, True, shutdown=True), State.STOPPING)
            self.assertFalse(controller.safe_to_request_poweroff)
            tick(controller, 160, True, shutdown=False)
            self.assertIsNotNone(store.active)
            self.assertFalse(controller.safe_to_request_poweroff)
            backend.drain_ack = True
            self.assertEqual(tick(controller, 180, True), State.SHUTDOWN)
            self.assertTrue(controller.safe_to_request_poweroff)
            self.assertEqual(saved_manifest(controller)["status"], "complete")
            tick(controller, 200, False)
            tick(controller, 220, False)
            tick(controller, 240, True)
            tick(controller, 260, True)
            self.assertEqual(len(backend.starts), 1)
            with self.assertRaises(RuntimeError):
                controller.recover()

    def test_idle_shutdown_never_starts_backend_or_creates_clip(self):
        with camera() as (controller, backend, store):
            self.assertEqual(tick(controller, 0, True, shutdown=True), State.SHUTDOWN)
            self.assertTrue(controller.safe_to_request_poweroff)
            self.assertEqual(backend.starts, [])
            self.assertEqual(list(store.root.glob("*/manifest.json")), [])

    def test_drain_timeout_retains_ownership_and_blocks_poweroff_until_real_ack(self):
        with camera(drain_timeout_ms=100) as (controller, backend, store):
            start_take(controller)
            first_frame(controller, backend)
            tick(controller, 120, True, shutdown=True)
            tick(controller, 219, True)
            self.assertEqual(controller.state, State.STOPPING)
            tick(controller, 220, True)
            self.assertEqual(controller.state, State.FAULT)
            self.assertIn("drain", controller.failure)
            self.assertIsNotNone(store.active)
            self.assertFalse(controller.safe_to_request_poweroff)
            with self.assertRaises(RuntimeError):
                controller.recover()
            backend.drain_ack = True
            tick(controller, 240, True)
            self.assertTrue(controller.safe_to_request_poweroff)
            self.assertEqual(saved_manifest(controller)["status"], "failed")


class FaultAndRecoveryTests(unittest.TestCase):
    def test_preflight_failure_creates_no_clip_and_requires_explicit_recovery(self):
        with camera() as (controller, backend, store):
            backend.preflight_error = RuntimeError("sensor unavailable")
            self.assertEqual(start_take(controller), State.FAULT)
            self.assertEqual(backend.starts, [])
            self.assertIsNone(store.active)
            self.assertEqual(list(store.root.glob("*/manifest.json")), [])
            with self.assertRaises(RuntimeError):
                controller.recover()
            tick(controller, 80, False)
            tick(controller, 100, False)
            self.assertEqual(controller.state, State.FAULT)
            backend.preflight_error = None
            controller.recover()
            self.assertEqual(controller.state, State.CHECK)
            tick(controller, 120, False)
            tick(controller, 140, True)
            tick(controller, 160, True)
            self.assertEqual(controller.state, State.STARTING)

    def test_partial_start_failure_must_stop_and_drain_before_recovery(self):
        with camera() as (controller, backend, store):
            backend.start_error = RuntimeError("device acquired, then start failed")
            self.assertEqual(start_take(controller), State.FAULT)
            self.assertEqual(len(backend.stops), 1)
            self.assertIsNotNone(store.active)
            with self.assertRaises(RuntimeError):
                controller.recover()
            backend.drain_ack = True
            tick(controller, 80, False)
            tick(controller, 100, False)
            self.assertEqual(saved_manifest(controller)["status"], "failed")
            self.assertIsNone(store.active)
            controller.recover()
            self.assertEqual(controller.state, State.CHECK)

    def test_poll_failure_does_not_implicitly_acknowledge_drain(self):
        with camera() as (controller, backend, store):
            start_take(controller)
            first_frame(controller, backend)
            backend.poll_error = OSError("sensor disconnected")
            tick(controller, 120, True)
            self.assertEqual(controller.state, State.FAULT)
            self.assertEqual(len(backend.stops), 1)
            self.assertIsNotNone(store.active)
            backend.poll_error = None
            backend.drain_ack = True
            tick(controller, 140, False)
            tick(controller, 160, False)
            self.assertEqual(saved_manifest(controller)["status"], "failed")
            controller.recover()

    def test_failed_stop_is_retried_and_not_treated_as_drained(self):
        with camera() as (controller, backend, store):
            start_take(controller)
            first_frame(controller, backend)
            backend.stop_error = OSError("stop ioctl failed")
            backend.drain_ack = True
            request_release(controller)
            self.assertEqual(controller.state, State.FAULT)
            self.assertIsNotNone(store.active)
            self.assertFalse(controller.safe_to_request_poweroff)
            backend.stop_error = None
            tick(controller, 160, False)
            self.assertGreaterEqual(len(backend.stops), 2)
            self.assertEqual(saved_manifest(controller)["status"], "failed")

    def test_drain_query_failure_keeps_faulted_take_owned(self):
        with camera() as (controller, backend, store):
            start_take(controller)
            first_frame(controller, backend)
            backend.drain_error = OSError("queue status unavailable")
            request_release(controller)
            self.assertEqual(controller.state, State.FAULT)
            self.assertIsNotNone(store.active)
            backend.drain_error = None
            backend.drain_ack = True
            tick(controller, 160, False)
            self.assertEqual(saved_manifest(controller)["status"], "failed")

    def test_first_frame_timeout_faults_and_requests_stop(self):
        with camera(frame_timeout_ms=100) as (controller, backend, store):
            start_take(controller)
            tick(controller, 159, True)
            self.assertEqual(controller.state, State.STARTING)
            tick(controller, 160, True)
            self.assertEqual(controller.state, State.FAULT)
            self.assertIn("no capture frames", controller.failure)
            self.assertEqual(len(backend.stops), 1)
            self.assertIsNotNone(store.active)
            backend.drain_ack = True
            tick(controller, 180, True)
            self.assertEqual(saved_manifest(controller)["status"], "failed")

    def test_backend_sequence_gap_is_preserved_without_silently_shortening_take(self):
        with camera() as (controller, backend, _):
            start_take(controller)
            backend.frames = [Frame(0, 90 * MS, b"first"), Frame(2, 100 * MS, b"gap")]
            tick(controller, 100, True)
            self.assertEqual(controller.state, State.RECORDING)
            request_release(controller)
            backend.drain_ack = True
            tick(controller, 160, False)
            saved = saved_manifest(controller)
            self.assertEqual(saved["status"], "complete")
            self.assertEqual([frame["index"] for frame in saved["frames"]], [0, 1])
            self.assertEqual([frame["source_sequence"] for frame in saved["frames"]], [0, 2])
            self.assertEqual(saved['dropped_frames'], [{'first_sequence': 1, 'count': 1,
                                                       'reason': 'unreported_source_sequence_gap'}])

    def test_storage_full_faults_and_stops_without_claiming_recorded_frames(self):
        with camera() as (controller, backend, store):
            start_take(controller)
            backend.frames = [Frame(0, 100 * MS, b"first")]
            with mock.patch.object(store, "free_bytes", return_value=0):
                tick(controller, 100, True)
            self.assertEqual(controller.state, State.FAULT)
            self.assertIn("storage reserve", controller.failure)
            self.assertEqual(controller.indicators()["rec"], "off")
            backend.drain_ack = True
            tick(controller, 120, True)
            self.assertEqual(saved_manifest(controller)["status"], "failed")
            self.assertEqual(saved_manifest(controller)["frames"], [])

    def test_failed_final_commit_blocks_recovery_and_poweroff_permission(self):
        with camera() as (controller, backend, store):
            start_take(controller)
            first_frame(controller, backend)
            request_release(controller)
            backend.drain_ack = True
            with mock.patch("gs8_camera_evf.storage.os.replace", side_effect=OSError(errno.EIO, "manifest publish failed")):
                tick(controller, 160, False)
            self.assertEqual(controller.state, State.FAULT)
            self.assertIsNone(store.active)
            self.assertIsNone(controller.last_clip)
            with self.assertRaisesRegex(RuntimeError, "commit"):
                controller.recover()
            tick(controller, 180, False, shutdown=True)
            self.assertFalse(controller.safe_to_request_poweroff)
            self.assertNotEqual(store.incomplete_clips(), [])

    def test_requested_audio_requires_a_completed_audio_artifact(self):
        selection = replace(BASE, audio=True)
        with camera() as (controller, backend, store):
            start_take(controller, selection)
            first_frame(controller, backend, selection)
            request_release(controller, selection)
            backend.drain_ack = True
            tick(controller, 160, False, selection)
            self.assertEqual(controller.state, State.FAULT)
            self.assertIn("audio artifact", controller.failure)
            self.assertNotEqual(store.incomplete_clips(), [])

    def test_audio_artifact_is_packaged_only_after_drain(self):
        selection = replace(BASE, audio=True)
        with camera() as (controller, backend, store):
            audio = io.BytesIO()
            with wave.open(audio, "wb") as wav:
                wav.setnchannels(1)
                wav.setsampwidth(2)
                wav.setframerate(48_000)
                wav.writeframes(b"\0\0" * 2666)
            backend.returned_artifacts = [Artifact(
                "audio.synthetic.wav", audio.getvalue(), "simulated_audio",
                AudioInfo(48_000, 1, 2666, 100 * MS),
            )]
            start_take(controller, selection)
            first_frame(controller, backend, selection)
            request_release(controller, selection)
            self.assertFalse((store.active.path / "audio.synthetic.wav").exists())
            backend.drain_ack = True
            tick(controller, 160, False, selection)
            self.assertEqual(saved_manifest(controller)["status"], "complete")
            self.assertEqual(saved_manifest(controller)["artifacts"][0]["kind"], "simulated_audio")
            self.assertEqual(saved_manifest(controller)["audio"]["sample_frames"], 2666)
            self.assertEqual(saved_manifest(controller)["audio"]["sensor_timestamp_ns"], 100 * MS)

    def test_artifact_collection_failure_never_becomes_complete(self):
        with camera() as (controller, backend, store):
            start_take(controller)
            first_frame(controller, backend)
            request_release(controller)
            backend.artifact_error = OSError("audio worker finalization failed")
            backend.drain_ack = True
            tick(controller, 160, False)
            self.assertEqual(controller.state, State.FAULT)
            self.assertFalse(controller.safe_to_request_poweroff)
            self.assertNotEqual(store.incomplete_clips(), [])

    def test_header_only_audio_does_not_complete_a_take_that_requested_audio(self):
        selection = replace(BASE, audio=True)
        with camera() as (controller, backend, _):
            empty_audio = io.BytesIO()
            with wave.open(empty_audio, "wb") as wav:
                wav.setnchannels(1)
                wav.setsampwidth(2)
                wav.setframerate(48_000)
                wav.writeframes(b"")
            backend.returned_artifacts = [Artifact(
                "empty.sim.wav", empty_audio.getvalue(), "simulated_audio",
                AudioInfo(48_000, 1, 0, 100 * MS),
            )]
            start_take(controller, selection)
            first_frame(controller, backend, selection)
            request_release(controller, selection)
            backend.drain_ack = True
            tick(controller, 160, False, selection)
            self.assertEqual(controller.state, State.FAULT)
            self.assertEqual(saved_manifest(controller)["status"], "failed")

    def test_invalid_clock_and_input_types_are_rejected_without_advancing_clock(self):
        with camera() as (controller, _, _):
            tick(controller, 20, False)
            for timestamp in (19 * MS, -1, True, 1.5):
                with self.assertRaises(ValueError):
                    controller.step(timestamp, BASE, trigger_pressed=False)
            with self.assertRaises(ValueError):
                controller.step(20 * MS, BASE, trigger_pressed=0)
            with self.assertRaises(ValueError):
                controller.step(20 * MS, BASE, trigger_pressed=False, shutdown_requested=1)
            tick(controller, 20, False)

    def test_uncommissioned_custom_wb_rejected_before_hardware_take_creation(self):
        backend = ScriptedBackend()
        backend.simulated = False
        with camera(backend) as (controller, _, store):
            start_take(controller, replace(BASE, wb="custom"))
            self.assertEqual(controller.state, State.CHECK)
            self.assertIsNone(controller.failure)
            self.assertIn("calibrated", controller.inhibit_reason)
            self.assertEqual(backend.starts, [])
            self.assertIsNone(store.active)


class SettingsAndSimulationTests(unittest.TestCase):
    def test_shutter_angle_is_converted_to_exposure_at_each_frame_rate(self):
        expected = {
            18: {90: 13889, 144: 22222, 180: 27778, 216: 33333},
            24: {90: 10417, 144: 16667, 180: 20833, 216: 25000},
        }
        for fps, angles in expected.items():
            for angle, exposure_us in angles.items():
                settings = TakeSettings.from_selection(replace(BASE, fps=fps, shutter_angle=angle))
                self.assertEqual(settings.exposure_us, exposure_us)

    def test_calibrated_wb_is_copied_and_invalid_gain_values_are_rejected(self):
        gains = [1.8, 1.4]
        settings = TakeSettings.from_selection(replace(BASE, wb="custom"), gains)
        gains[0] = 9
        self.assertEqual(settings.wb_gains, (1.8, 1.4))
        for bad in ((0, 1), (1, float("nan")), (1, float("inf")), (True, 1), (1,), (1, 2, 3)):
            with self.assertRaises(ValueError):
                TakeSettings.from_selection(BASE, bad)

    def test_simulated_frames_respect_18_and_24_fps_boundaries_and_drain(self):
        for fps in (18, 24):
            backend = SimulationBackend(drain_delay_ns=100 * MS)
            settings = TakeSettings.from_selection(replace(BASE, fps=fps))
            backend.preflight(settings)
            backend.start(settings, 0)
            first_due = (1_000_000_000 + fps - 1) // fps
            self.assertEqual(backend.poll(first_due - 1), [])
            first = backend.poll(first_due)
            self.assertEqual(len(first), 1)
            self.assertEqual(first[0].index, 0)
            self.assertEqual(first[0].sensor_timestamp_ns, first_due)
            backend.request_stop(1_000_000_000)
            remainder = backend.poll(1_000_000_000)
            self.assertEqual(len(remainder) + len(first), fps)
            self.assertFalse(backend.drained(1_099_999_999))
            self.assertTrue(backend.drained(1_100_000_000))
            self.assertEqual(backend.poll(2_000_000_000), [])
            self.assertTrue(all(json.loads(frame.payload)["simulation_only"] for frame in first + remainder))


if __name__ == "__main__":
    unittest.main()

