# SPDX-License-Identifier: MIT
"""Independent serialized-output tests for the collar's removable print stock.

Run through run_locked.py. These validate CAD exports, not slicer behavior or a
physical print. Production/coupon STL includes stock; assembled STEP excludes it.
"""
import contextlib
import io
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch

import cadquery as cq
import manifold3d as m3
import numpy as np

import build_d2 as B
import checks as CK
import d2_common as dc
import layout as L
import make_coupons as MC


def stl_manifold(path):
    """Read the exported binary STL, independently of the BRep mesh checker."""
    data = Path(path).read_bytes()
    n = struct.unpack_from('<I', data, 80)[0]
    if len(data) != 84 + n * 50:
        raise AssertionError('Expected an exact binary STL triangle payload')
    dtype = np.dtype([('normal', '<f4', (3,)), ('v', '<f4', (3, 3)), ('attr', '<u2')])
    vertices = np.frombuffer(data, dtype=dtype, offset=84)['v'].reshape(-1, 3)
    _, indices, inverse = np.unique(np.round(vertices / 1e-5).astype(np.int64), axis=0,
                                    return_index=True, return_inverse=True)
    mesh = m3.Mesh(vert_properties=np.ascontiguousarray(vertices[indices], np.float32),
                   tri_verts=np.ascontiguousarray(inverse.reshape(-1, 3), np.uint32))
    result = m3.Manifold(mesh)
    if result.is_empty():
        raise AssertionError('Serialized STL is not a nonempty manifold')
    return result


def symmetric_mesh_volume(a, b):
    return abs((a - b).volume()) + abs((b - a).volume())


class PrintStockExportTests(unittest.TestCase):
    def test_real_production_step_and_coupon_exports(self):
        for lens in ('kowa_lm6hc', 'fujinon_hf6xa'):
            with self.subTest(lens=lens), tempfile.TemporaryDirectory(prefix='d2-print-export-') as td, \
                    patch.object(L, 'LENS', lens), patch.object(B, 'OUT', td):
                rows, _ = B.build_printed(only='lens_collar')
                row = rows['lens_collar']
                self.assertFalse(row['stub'])
                finished, stock = row['shape'], row['print_shape']
                self.assertGreater(stock.Volume(), finished.Volume())

                bed, meshes = [], []
                manifest = B.export_part('lens_collar', row, bed, [], meshes)
                self.assertEqual(bed[0]['status'], 'pass')
                self.assertEqual(meshes[0]['status'], 'pass')
                self.assertEqual(manifest['print_preparation']['membrane_count'], 3)
                self.assertEqual(manifest['print_preparation']['membrane_thickness_mm'], 0.2)
                self.assertIn('STEP', manifest['print_preparation']['assembled_geometry'])
                self.assertIn('3.4 mm', manifest['print_preparation']['postprocess'])
                self.assertAlmostEqual(manifest['finished_volume_mm3'], finished.Volume(), places=3)

                production = stl_manifold(Path(td) / manifest['stl'])
                expected_stock = CK.manifold_of_tol(dc.to_print_pose(stock, '+X'), 0.03, 0.2)
                self.assertEqual(len(production.decompose()), 1)
                self.assertLess(symmetric_mesh_volume(production, expected_stock), 0.05)

                # Exporter must choose row.shape, not the printable stock. Exact
                # Boolean comparison after STEP round-trip catches filled holes.
                B.export_step(rows)
                imported = cq.importers.importStep(str(Path(td) / 'step/parts/lens_collar.step')).val()
                self.assertLess(imported.cut(finished).Volume() + finished.cut(imported).Volume(), 0.002)
                self.assertGreater(stock.Volume() - imported.Volume(), 5.0)

                # Isolate this coupon from unrelated, slow whole-body cuts while
                # exercising the real collar coupon preparation and STL writer.
                def collar_only(pid, box):
                    return finished.copy() if pid == 'lens_collar' else None

                with patch.object(MC, '_cut', side_effect=collar_only), contextlib.redirect_stdout(io.StringIO()):
                    coupon = next(x for x in MC.coupons() if x[0] == 'collar_part')
                self.assertIn('Clear the three anchor holes to 3.4 mm', coupon[5])
                self.assertLess(coupon[1].cut(stock).Volume() + stock.cut(coupon[1]).Volume(), 0.002)
                coupon_dir = Path(td) / 'coupon-only'
                with patch.object(MC, 'coupons', return_value=iter([coupon])), \
                        patch.object(sys, 'argv', ['make_coupons.py', '--out', str(coupon_dir)]), \
                        contextlib.redirect_stdout(io.StringIO()):
                    MC.main()
                coupon_mesh = stl_manifold(coupon_dir / 'stl/coupons/collar_part.stl')
                self.assertLess(symmetric_mesh_volume(production, coupon_mesh), 0.05)


if __name__ == '__main__':
    unittest.main(verbosity=2)
