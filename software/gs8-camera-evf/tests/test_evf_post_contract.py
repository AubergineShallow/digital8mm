# SPDX-License-Identifier: MIT
"""Synthetic physical-backend metadata handoff, never camera/image evidence.

The optional integration checks deliberately exercise the non-simulated schema
branch using temporary TIFF-magic-only bytes. Those bytes are NOT valid DNGs.
They are removed with the temporary directory; no fixture is capture evidence.
"""
from dataclasses import replace
import importlib.util
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import time
import unittest

from gs8_camera_evf.evf import EvfPolicy, PicameraEvfBackend
from gs8_camera_evf.storage import ClipStore
from test_evf import FakeCamera, await_condition, preview, settings


sequence = None
configured = os.environ.get('GS8_SEQUENCE_MODULE')
candidates = ([Path(configured)] if configured else
              [parent / 'post/gs8-sequence/gs8_sequence.py' for parent in Path(__file__).resolve().parents])
for candidate in candidates:
    if candidate.is_file():
        spec = importlib.util.spec_from_file_location('gs8_sequence_evf_contract', candidate)
        sequence = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(sequence)
        break
if configured and sequence is None:
    raise RuntimeError('GS8_SEQUENCE_MODULE must point to the independent planner module')


class SignatureOnlyFakeCamera(FakeCamera):
    def save_dng(self, pixels, metadata, raw_config, output):
        # Reach the planner's metadata checks, never pretend to decode pixels.
        output.write(b'II*\x00SYNTHETIC-TEST-ONLY-NOT-A-VALID-DNG:' + pixels)


class MetadataContractTests(unittest.TestCase):
    def open_backend(self, fps=24, source=None, model='imx296', *, warm=True):
        camera = SignatureOnlyFakeCamera()
        camera.camera_properties['Model'] = model
        backend = PicameraEvfBackend(EvfPolicy(fps, source), camera_factory=lambda: camera,
                                    preview_factory=preview)
        self.addCleanup(backend.close)
        descriptor = backend.preflight(settings(fps))
        if warm:
            for _ in range(backend.policy.source_fps):
                camera.frame()
            self.assertTrue(backend.warmed_up)
        return backend, camera, descriptor

    def test_exact_model_is_canonicalized_and_reported_identity_retained(self):
        for model in ('imx296', 'IMX296', ' imx296 '):
            with self.subTest(model=model):
                backend, _, descriptor = self.open_backend(model=model)
                self.assertEqual(descriptor['model'], 'imx296')
                self.assertEqual(descriptor['model_reported'], model)
                backend.close()

    def test_similar_sensor_names_are_not_silently_reidentified(self):
        for model in ('imx296_mono', 'not-imx296', 'imx296x', 'imx477'):
            with self.subTest(model=model), self.assertRaisesRegex(ValueError, 'expected colour IMX296'):
                self.open_backend(model=model)

    def test_previous_loose_exposure_gain_and_wb_allowances_fault_before_handoff(self):
        for metadata in ({'ExposureTime': round(settings().exposure_us * 1.02)},
                         {'AnalogueGain': 1.03}, {'ColourGains': (1.545, 1.2875)}):
            with self.subTest(metadata=metadata):
                backend, camera, _ = self.open_backend()
                backend.start(settings(), time.monotonic_ns())
                camera.frame(metadata=metadata)
                with self.assertRaisesRegex(RuntimeError, 'locked take'):
                    backend.poll(0)
                self.assertEqual(backend._expected, 0)
                backend.close()

    def test_stricter_applied_metadata_must_also_settle_before_start(self):
        backend, camera, _ = self.open_backend(warm=False)
        for _ in range(backend.policy.source_fps):
            camera.frame(metadata={'AnalogueGain': 1.03})
        self.assertFalse(backend.warmed_up)
        with self.assertRaisesRegex(RuntimeError, 'settled sensor metadata'):
            backend.start(settings(), time.monotonic_ns())
        for _ in range(backend.policy.source_fps):
            camera.frame()
        self.assertTrue(backend.warmed_up)

    def test_planner_incompatible_numeric_types_and_colour_ranges_fault(self):
        for metadata in ({'ExposureTime': True}, {'AnalogueGain': True}, {'FrameDuration': True},
                         {'ColourGains': (True, 1.25)}, {'ColourGains': (33.0, 1.25)},
                         {'ColourGains': (0.005, 1.25)}):
            with self.subTest(metadata=metadata):
                backend, camera, _ = self.open_backend()
                backend.start(settings(), time.monotonic_ns())
                camera.frame(metadata=metadata)
                with self.assertRaisesRegex(RuntimeError, 'invalid per-frame sensor metadata'):
                    backend.poll(0)
                backend.close()

    def test_requested_wb_gains_must_fit_the_independent_planner_range(self):
        for gains in ((0.005, 1.25), (33.0, 1.25)):
            with self.subTest(gains=gains), self.assertRaisesRegex(ValueError, 'PC planner range'):
                EvfPolicy(24).validate_settings(replace(settings(), wb_gains=gains))

    def test_sampling_description_exposes_current_planner_boundary(self):
        for fps in (18, 24):
            self.assertEqual(EvfPolicy(fps).describe()['post_planner_sampling'],
                             'uniform_candidate_requires_measured_cadence_validation')
        for fps, source in ((18, 48), (18, 60), (24, 54), (24, 60)):
            with self.subTest(fps=fps, source=source):
                policy = EvfPolicy(fps, source)
                self.assertEqual(policy.describe()['post_planner_sampling'], 'unsupported_uneven_cadence')
                self.assertIn('current PC planner rejects', policy.describe()['post_planner_sampling_note'])
                self.assertEqual(sum(policy.selects(i) for i in range(source)), fps)


@unittest.skipIf(sequence is None, 'optional planner unavailable; set GS8_SEQUENCE_MODULE for cross-package checks')
class SyntheticPostHandoffTests(unittest.TestCase):
    def capture(self, root, fps, source=None, metadata=None, model='imx296'):
        camera = SignatureOnlyFakeCamera()
        camera.camera_properties['Model'] = model
        backend = PicameraEvfBackend(EvfPolicy(fps, source), camera_factory=lambda: camera,
                                    preview_factory=preview)
        try:
            take_settings = settings(fps)
            descriptor = backend.preflight(take_settings)
            descriptor['synthetic_test_only'] = True
            for _ in range(backend.policy.source_fps):
                camera.frame()
            backend.start(take_settings, time.monotonic_ns())
            frames = []
            for _ in range(backend.policy.source_fps):
                camera.frame(metadata=metadata or {})
                await_condition(lambda: backend._processing == 0)
                frames.extend(backend.poll(0))
            backend.request_stop(time.monotonic_ns())
            with ClipStore(root, reserve_bytes=0) as store:
                transaction = store.begin(take_settings.to_dict(), False, descriptor)
                for frame in frames:
                    transaction.add_frame(frame.index, frame.sensor_timestamp_ns, frame.payload,
                                          source_sequence=frame.index, applied_metadata=frame.applied_metadata)
                transaction.finish(summary=backend.final_summary())
                return transaction.path / 'manifest.json'
        finally:
            backend.close()

    def test_uniform_defaults_and_canonical_model_reach_non_rendered_plan(self):
        with TemporaryDirectory(prefix='SYNTHETIC-ONLY-evf-post-') as temporary:
            for fps in (18, 24):
                with self.subTest(fps=fps):
                    path = self.capture(Path(temporary) / str(fps), fps, model='IMX296')
                    clip = sequence.validate_clip(path)
                    self.assertTrue(clip['sensor']['synthetic_test_only'])
                    self.assertEqual(clip['sensor']['model'], 'imx296')
                    self.assertEqual(clip['sensor']['model_reported'], 'IMX296')
                    self.assertEqual(len(clip['frames']), fps)
                    self.assertEqual(clip['capture_summary']['source_frame_count'], fps)
                    plan = sequence.build_plan(clip)
                    self.assertEqual(plan['state'], 'planned_not_rendered')
                    self.assertTrue(any('DNG tags' in text for text in plan['limitations']))

    def test_permitted_quantization_survives_independent_post_validation(self):
        with TemporaryDirectory(prefix='SYNTHETIC-ONLY-evf-post-') as temporary:
            for fps in (18, 24):
                metadata = {'ExposureTime': settings(fps).exposure_us + 99,
                            'AnalogueGain': 1.009, 'ColourGains': (1.514, 1.262)}
                with self.subTest(fps=fps):
                    path = self.capture(Path(temporary) / str(fps), fps, metadata=metadata)
                    clip = sequence.validate_clip(path)
                    self.assertEqual(clip['frames'][0]['applied_metadata']['exposure_us'], metadata['ExposureTime'])

    def test_uneven_ratios_keep_true_timestamps_and_fail_current_planner(self):
        with TemporaryDirectory(prefix='SYNTHETIC-ONLY-evf-post-') as temporary:
            for fps, source in ((18, 48), (18, 60), (24, 54), (24, 60)):
                with self.subTest(fps=fps, source=source):
                    path = self.capture(Path(temporary) / f'{fps}-{source}', fps, source)
                    with self.assertRaisesRegex(sequence.ClipError, 'timestamp drift/drop'):
                        sequence.validate_clip(path)


if __name__ == '__main__':
    unittest.main()
