# SPDX-License-Identifier: MIT
"""Host regressions for STEP/VTK output routing; no part geometry or display needed."""
import hashlib
import os
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_d2 as B


class OutputRoutingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='d2-output-routing-')
        self.addCleanup(self.temp.cleanup)
        self.out = Path(self.temp.name)
        self.epoch = time.time() - 1
        for target, value in [('OUT', str(self.out)), ('T0', self.epoch)]:
            patcher = patch.object(B, target, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        for target in ('log', 'lap'):
            patcher = patch.object(B, target)
            patcher.start()
            self.addCleanup(patcher.stop)

    def make_step(self, rows):
        parts = self.out / 'step' / 'parts'
        parts.mkdir(parents=True, exist_ok=True)
        assembly = self.out / 'step' / 'gs8-d2-assembly.step'
        assembly.write_bytes(b'fresh assembly')
        (parts / 'lens_collar.step').write_bytes(b'fresh cleared collar')
        return str(assembly)

    def test_fast_retains_historical_no_step_no_views(self):
        with patch.object(B, 'export_step') as step, patch.object(B, 'render_all') as render:
            self.assertEqual(B.export_presentation_outputs({}, fast=True), {})
            step.assert_not_called()
            render.assert_not_called()

    def test_skip_renders_keeps_fresh_step_and_omits_old_views(self):
        old = self.out / 'renders' / 'hero.png'
        old.parent.mkdir()
        old.write_bytes(b'old unrelated image')
        with patch.object(B, 'export_step', side_effect=self.make_step) as step, \
                patch.object(B, 'render_all') as render:
            files = B.export_presentation_outputs({}, skip_renders=True)
            step.assert_called_once_with({})
            render.assert_not_called()
        self.assertEqual(set(files), {'step/gs8-d2-assembly.step', 'step/parts/lens_collar.step'})
        self.assertEqual(files['step/gs8-d2-assembly.step'], hashlib.sha256(b'fresh assembly').hexdigest())
        self.assertEqual(old.read_bytes(), b'old unrelated image')

    def test_stale_per_part_step_is_not_adopted(self):
        old = self.out / 'step' / 'parts' / 'old.step'
        old.parent.mkdir(parents=True)
        old.write_bytes(b'old geometry')
        os.utime(old, (self.epoch - 100, self.epoch - 100))
        with patch.object(B, 'export_step', side_effect=self.make_step):
            files = B.export_presentation_outputs({}, skip_renders=True)
        self.assertNotIn('step/parts/old.step', files)

    def test_default_still_exports_step_and_vtk_views(self):
        with patch.object(B, 'export_step', side_effect=self.make_step), \
                patch.object(B, 'render_all', return_value={'renders/hero.png': 'fresh-view-hash'}) as render:
            files = B.export_presentation_outputs({})
            render.assert_called_once_with({})
        self.assertIn('step/gs8-d2-assembly.step', files)
        self.assertEqual(files['renders/hero.png'], 'fresh-view-hash')

    def test_cli_skip_renders_does_not_imply_fast_or_weaken_checks(self):
        with patch.object(B, 'run_full', return_value=0) as run:
            self.assertEqual(B.main(['--skip-renders', '--sweep-step', '1.0']), 0)
        args = run.call_args.args[0]
        self.assertTrue(args.skip_renders)
        self.assertFalse(args.fast)
        self.assertFalse(args.no_thin)
        self.assertFalse(args.no_sweeps)
        self.assertEqual(args.sweep_step, 1.0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
