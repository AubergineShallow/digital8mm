# SPDX-License-Identifier: MIT
"""Independent camera-to-PC manifest contract checks, all synthetic."""
from contextlib import redirect_stdout, redirect_stderr
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from gs8_camera_evf.cli import main

sequence = None
configured = os.environ.get('GS8_SEQUENCE_MODULE')
candidates = ([Path(configured)] if configured else
              [parent / 'post/gs8-sequence/gs8_sequence.py' for parent in Path(__file__).resolve().parents])
for candidate in candidates:
    if candidate.is_file():
        spec = importlib.util.spec_from_file_location('gs8_sequence', candidate)
        sequence = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(sequence)
        break
if configured and sequence is None:
    raise RuntimeError('GS8_SEQUENCE_MODULE must point to the independent planner module')


@unittest.skipIf(sequence is None, 'optional planner unavailable; set GS8_SEQUENCE_MODULE for cross-package checks')
class HandoffTests(unittest.TestCase):
    def simulate(self, output, fps, capture_format='raw'):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            result = main(['simulate', '--output', str(output), '--fps', str(fps),
                           '--frames', str(fps * 2), '--format', capture_format,
                           '--audio', '--reserve-mib', '0'])
        self.assertEqual(result, 0)
        report = json.loads(buffer.getvalue())
        self.assertTrue(report['simulation_only'])
        self.assertTrue(report['safe_to_request_poweroff'])
        return Path(report['clip']) / 'manifest.json'

    def test_camera_raw_audio_passes_independent_pc_validator_at_both_rates(self):
        with TemporaryDirectory(prefix='gs8-handoff-') as folder:
            for fps in (18, 24):
                with self.subTest(fps=fps):
                    path = self.simulate(Path(folder) / str(fps), fps)
                    clip = sequence.validate_clip(path, allow_simulated=True)
                    plan = sequence.build_plan(clip)
                    self.assertEqual(len(plan['frames']), fps * 2)
                    self.assertEqual(plan['state'], 'planned_not_rendered')
                    self.assertEqual(plan['audio']['sample_frames'], 96_000)
                    self.assertEqual(plan['audio_timeline']['offset_ns'], 0)
                    self.assertTrue(all(f['filename'].endswith('.simframe') for f in plan['frames']))

    def test_simulation_is_refused_without_explicit_pc_opt_in(self):
        with TemporaryDirectory(prefix='gs8-handoff-') as folder:
            path = self.simulate(folder, 18)
            with self.assertRaises(sequence.ClipError):
                sequence.validate_clip(path)

    def test_simulated_encoded_is_one_descriptor_file_with_full_container_hash(self):
        with TemporaryDirectory(prefix='gs8-handoff-') as folder:
            path = self.simulate(folder, 24, 'encoded')
            manifest = json.loads(path.read_text())
            self.assertEqual(len(set(f['filename'] for f in manifest['frames'])), 1)
            payload = (path.parent / manifest['frames'][0]['filename']).read_bytes()
            self.assertEqual(len(payload.splitlines()), 48)
            container = next(a for a in manifest['artifacts'] if a['kind'] == 'simulated_encoded')
            self.assertEqual(container['sha256'], hashlib.sha256(payload).hexdigest())
            self.assertEqual(manifest['frames'][0]['sha256'], hashlib.sha256(payload.splitlines(keepends=True)[0]).hexdigest())
            with self.assertRaises(sequence.ClipError):
                sequence.validate_clip(path, allow_simulated=True)

    def test_tampering_camera_output_fails_pc_handoff(self):
        with TemporaryDirectory(prefix='gs8-handoff-') as folder:
            path = self.simulate(folder, 24)
            manifest = json.loads(path.read_text())
            frame = path.parent / manifest['frames'][0]['filename']
            content = frame.read_bytes()
            frame.write_bytes(b'X' + content[1:])
            with self.assertRaises(sequence.ClipError):
                sequence.validate_clip(path, allow_simulated=True)

    def test_real_run_never_falls_back_to_simulation(self):
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as stopped:
            main(['run'])
        self.assertEqual(stopped.exception.code, 2)


if __name__ == '__main__':
    unittest.main()

