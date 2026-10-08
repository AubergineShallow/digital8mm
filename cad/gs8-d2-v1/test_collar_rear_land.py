# SPDX-License-Identifier: MIT
"""Rear-entry geometry regressions. Run through the serialized run_locked.py owner."""
import copy
import math
import unittest
from unittest.mock import patch

import layout as L
import printed_collar as PC
import checks as CK
import cots


class CollarRearLand(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.current = {n: PC.build_part(L, 'lens_collar', n).val() for n in L.LENSES}
        cls.old = {}
        original = L.collar_spec
        def old_profile(name=None):
            n = name or L.LENS
            original_cs = original(n)
            if original_cs is None:
                return None
            cs = dict(original_cs)
            drop = min(L.COLLAR['cone_drop'], cs['seat_r'] - cs['rear_step_r'] - 0.3)
            cs.update(cone_x0=round(cs['seat_x']-drop,4), cone_r0=round(cs['seat_r']-drop,4))
            # Deliberately lie in metadata: the measured check must find the actual material fault.
            return cs
        with patch.object(L, 'collar_spec', old_profile):
            cls.old = {n: PC.build_part(L, 'lens_collar', n).val() for n in L.LENSES}

    def test_actual_land_measured_for_both_production_lenses(self):
        rows = CK.check_lens_support(L, collars=self.current)
        for n in L.LENSES:
            cases = [r for r in rows if r.get('lens') == n and r['item'] in ('rear_entry_plan','rear_entry_measured')]
            self.assertEqual(len(cases), 2)
            self.assertTrue(all(r['status']=='pass' for r in cases), cases)
            measured = next(r for r in cases if r['item']=='rear_entry_measured')
            self.assertAlmostEqual(measured['measured_min_mm'], 1.63, places=3)
            self.assertEqual(measured['required_mm'], 1.6)

    def test_old_feather_fails_despite_claimed_new_profile(self):
        rows = CK.check_lens_support(L, collars=self.old)
        for n in L.LENSES:
            case = next(r for r in rows if r.get('lens') == n and r['item']=='rear_entry_measured')
            self.assertEqual(case['status'], 'fail')
            self.assertLess(case['measured_min_mm'], 0.6)

    def test_seat_contact_bore_and_outer_envelope_do_not_move(self):
        for n, sh in self.current.items():
            old, cs = self.old[n], L.collar_spec(n)
            self.assertLess(sh.cut(old).Volume(), 0.001)  # material removal at inner free edge only
            self.assertGreater(old.cut(sh).Volume(), 100)
            self.assertLess(old.cut(sh).Volume(), 150)
            a,b=old.BoundingBox(),sh.BoundingBox()
            for k in ('xmin','xmax','ymin','ymax','zmin','zmax'):
                self.assertAlmostEqual(getattr(a,k),getattr(b,k),places=5)
            lens,_=cots.lens_proxy(L,n)
            self.assertLess(sh.intersect(lens).Volume(),0.001)
            self.assertLess(sh.distance(lens),0.001)
            self.assertAlmostEqual(cs['seat_x'],L.C_FLANGE_X+L.LENSES[n]['support']['x0'])
            self.assertAlmostEqual(cs['cone_x0']-cs['rear_x'],1.6)

    def test_declared_minimum_cannot_be_lowered_below_loaded_floor(self):
        lower=dict(L.COLLAR,rear_bore_land_min=0.1)
        with patch.object(L,'COLLAR',lower):
            for n in L.LENSES:
                self.assertEqual(L.collar_spec(n)['rear_bore_land_min'],1.6)
                self.assertGreaterEqual(L.collar_spec(n)['rear_bore_land_mm'],1.6)

    def test_data_only_candidate_cannot_export_an_infeasible_collar(self):
        n='computar_h6z0812'
        self.assertFalse(L.collar_spec(n)['rear_entry_feasible'])
        with self.assertRaisesRegex(ValueError,'different rear-entry design'):
            PC.build_part(L,'lens_collar',n)
        rows=CK.check_lens_support(L)
        r=next(r for r in rows if r.get('lens')==n and r['item']=='rear_entry_plan')
        self.assertEqual(r['status'],'info')
        self.assertIn('no printable collar is approved',r['warn'])

    def test_promoting_infeasible_candidate_to_production_fails(self):
        n='computar_h6z0812'
        production=dict(L.LENSES,**{n:L.LENSES_DATA_ONLY[n]})
        with patch.object(L,'LENSES',production):
            rows=CK.check_lens_support(L)
            r=next(r for r in rows if r.get('lens')==n and r['item']=='rear_entry_plan')
            self.assertEqual(r['status'],'fail')
            with self.assertRaisesRegex(ValueError,'different rear-entry design'):
                PC.build_part(L,'lens_collar',n)


if __name__ == '__main__':
    unittest.main(verbosity=2)
