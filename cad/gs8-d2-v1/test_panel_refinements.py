# SPDX-License-Identifier: MIT
"""Exact encoder-tooth root and portable engraving-font regressions; run via run_locked.py."""
import copy
import math
import unittest
from unittest.mock import patch

import cadquery as cq
import layout as L
import d2_common as dc
import printed_panel as PP
import checks as CK


class PanelRefinements(unittest.TestCase):
    def test_all_three_tooth_roots_exceed_loaded_floor(self):
        hooks = PP._cradle(L)
        probes = [f for f in L.CRITICAL_FEATURES if f['id'].startswith('panel_encoder_hook_tooth_')]
        self.assertEqual(len(probes), 3)
        for h, f in zip(hooks, probes):
            for off in (-1.0, 0.0, 1.0):
                ax = f['span'][2]
                p = tuple(a + off * b for a, b in zip(f['origin'], ax))
                t, _, _, error = CK.chord(h, p, f['direction'])
                self.assertIsNone(error, f['id'])
                self.assertAlmostEqual(t, 1.62, places=5)
                self.assertGreaterEqual(t, L.FDM['MIN_WALL_LOADED'])
        joint = next(j for j in L.CRITICAL_JOINTS if j['id'] == 'J12_encoder_cradle')
        self.assertTrue(all(f['id'] in joint['required'] for f in probes))

    def test_old_short_land_fails_root_floor(self):
        enc = copy.deepcopy(L.ENCODER)
        enc['cradle_hooks']['land'] = 0.4
        with patch.object(L, 'ENCODER', enc):
            hooks = PP._cradle(L)
        probes = [f for f in L.CRITICAL_FEATURES if f['id'].startswith('panel_encoder_hook_tooth_')]
        for h, f in zip(hooks, probes):
            t, _, _, error = CK.chord(h, f['origin'], f['direction'])
            self.assertIsNone(error)
            self.assertAlmostEqual(t, 1.02, places=5)
            self.assertLess(t, L.FDM['MIN_WALL_LOADED'])

    def test_retention_faces_and_beams_stay_fixed(self):
        current = PP._cradle(L)
        enc = copy.deepcopy(L.ENCODER)
        enc['cradle_hooks']['land'] = 0.4
        with patch.object(L, 'ENCODER', enc):
            old = PP._cradle(L)
        for a, b in zip(old, current):
            self.assertLess(a.cut(b).Volume(), 0.001)  # adds tip/land material only
            oldbb, newbb = a.BoundingBox(), b.BoundingBox()
            self.assertAlmostEqual(oldbb.ymin - newbb.ymin, 0.6, places=5)
            self.assertAlmostEqual(oldbb.ymax, newbb.ymax)
            self.assertAlmostEqual(oldbb.zmin, newbb.zmin)
            self.assertAlmostEqual(oldbb.zmax, newbb.zmax)
            # Ahead of the fixed catch y = 24.0, the entire beam/gusset is byte-independent geometry.
            fixed = cq.Solid.makeBox(300, 100, 150, cq.Vector(-200, 24.0001, 0))
            self.assertLess(a.intersect(fixed).cut(b).Volume() + b.intersect(fixed).cut(a).Volume(), 0.001)
        self.assertLess(L.snap_strains()['encoder_cradle']['with_kt'], L.snap_strains()['encoder_cradle']['limit'])

    def test_font_identity_and_explicit_route(self):
        f = dc.engraving_font()
        self.assertEqual(f['family'], 'DejaVu Sans')
        self.assertEqual(f['kind'], 'bold')
        self.assertEqual(f['sha256'], L.ENGRAVE['font_sha256'])
        # No text drawing here: inspect the actual call boundary, so OS fallback cannot silently return.
        with patch.object(cq.Workplane, 'text', autospec=True, side_effect=RuntimeError('captured')) as text:
            with self.assertRaisesRegex(RuntimeError, 'captured'):
                dc.engrave([dict(kind='text', at=(-63, 36.5), text='test', h=3.0)])
            self.assertEqual(text.call_args.kwargs['fontPath'], f['path'])

    def test_missing_modified_or_conflicting_font_fails(self):
        for update in ({'font_file': 'fonts/missing.ttf'}, {'font_sha256': '0' * 64}):
            spec = dict(L.ENGRAVE, **update)
            with patch.object(L, 'ENGRAVE', spec), self.assertRaises(ValueError):
                dc.engraving_font()
        with self.assertRaises(ValueError):
            dc.engrave([], font='Arial')


if __name__ == '__main__':
    unittest.main(verbosity=2)
