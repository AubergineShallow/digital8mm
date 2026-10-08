# SPDX-License-Identifier: MIT
"""Regression checks for ordinary incomplete/corrupt release packaging."""
import json
import copy
from pathlib import Path
import tempfile
import unittest
import audit_cloud_release as A


class AuditCoverageTests(unittest.TestCase):
    def valid_common(self):
        return dict(revision='test', all_ok=True,
                    producer=dict(script='test_common.py', generated_at=1, source_hashes={'source.py': 'hash'}),
                    results=[dict(helper=name, ok=True, n=1, volume_mm3=1) for name in A.EXPECTED_COMMON_HELPERS])

    def test_failed_common_test_cannot_be_carried_as_pass(self):
        result = self.valid_common()
        result['all_ok'] = False
        result['results'][0]['ok'] = False
        failures = []
        A.validate_common_result(result, 'test', {'source.py': 'hash'}, failures)
        self.assertTrue(failures)

    def test_common_test_requires_complete_results_and_producer_hashes(self):
        for mutation in ('missing result', 'stale producer'):
            result = self.valid_common()
            if mutation == 'missing result':
                result['results'].pop()
            else:
                result['producer']['source_hashes'] = {'source.py': 'old'}
            failures = []
            A.validate_common_result(result, 'test', {'source.py': 'hash'}, failures)
            self.assertTrue(failures, mutation)

    def test_valid_common_producer_and_results_pass(self):
        failures = []
        A.validate_common_result(self.valid_common(), 'test', {'source.py': 'hash'}, failures)
        self.assertEqual(failures, [])

    def test_invalid_stale_or_unbound_coupon_manifest_fails(self):
        good = dict(revision='test',
                    producer=dict(script='make_coupons.py', generated_at=1, source_hashes={'source.py': 'hash'}),
                    coupons=[dict(valid=True, volume_mm3=1, stl='coupon.stl', stl_sha256='mesh-hash')])
        for mutation in ('invalid', 'revision', 'mesh', 'producer'):
            result = copy.deepcopy(good)
            if mutation == 'invalid': result['coupons'][0]['valid'] = False
            if mutation == 'revision': result['revision'] = 'old'
            if mutation == 'mesh': result['coupons'][0]['stl_sha256'] = 'old'
            if mutation == 'producer': result['producer']['source_hashes'] = {}
            failures = []
            A.validate_coupon_manifest(result, 'test', {'source.py': 'hash'}, {'coupon.stl': 'mesh-hash'},
                                       'make_coupons.py', failures)
            self.assertTrue(failures, mutation)

    def test_empty_sources_and_gate_docs_fail_exact_coverage(self):
        for expected in (A.EXPECTED_SOURCES, A.EXPECTED_GATE_DOCS):
            failures = []
            A.exact_coverage({}, expected, 'required manifest', failures)
            self.assertTrue(failures)

    def test_incomplete_source_manifest_fails(self):
        failures = []
        A.exact_coverage(A.EXPECTED_SOURCES - {'checks.py'}, A.EXPECTED_SOURCES, 'sources', failures)
        self.assertIn('checks.py', failures[0])

    def test_missing_font_asset_fails_cloud_source_coverage(self):
        failures = []
        A.exact_coverage(A.EXPECTED_SOURCES, A.EXPECTED_SOURCES | A.FONT_SOURCES, 'sources', failures)
        self.assertIn('DejaVuSans-Bold.ttf', failures[0])

    def test_empty_and_incomplete_locks_fail(self):
        for text in ('', 'cadquery==2.6.1\n'):
            failures = []
            A.validated_pins(text, failures)
            self.assertTrue(failures)

    def test_changed_dependency_version_fails(self):
        pins = dict(A.EXPECTED_PINS, manifold3d='0.0.0')
        failures = []
        A.validated_pins('\n'.join('%s==%s' % row for row in pins.items()), failures)
        self.assertTrue(failures)

    def test_complete_pins_pass(self):
        failures = []
        result = A.validated_pins('\n'.join('%s==%s' % row for row in A.EXPECTED_PINS.items()), failures)
        self.assertEqual(len(result), 43)
        self.assertEqual(failures, [])

    def test_duplicate_dependency_pin_rejected(self):
        with self.assertRaises(ValueError):
            A.parse_pins('cadquery==2.6.1\ncadquery==2.6.1\n')

    def test_duplicate_cannot_replace_missing_production_part(self):
        rows = [{'id': part} for part in sorted(A.EXPECTED_PARTS)]
        rows[-1] = dict(rows[0])
        failures = []
        A.validate_print_parts(rows, failures)
        self.assertTrue(any('coverage missing' in failure for failure in failures))
        self.assertTrue(any('Duplicate' in failure for failure in failures))

    def test_missing_evidence_state_fails(self):
        failures = []
        A.exact_coverage({'cad_checks': {}}, set(A.EXPECTED_STATES) | {'cad_checks'}, 'states', failures)
        self.assertTrue(failures)

    def test_duplicate_json_keys_and_missing_essential_keys_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / 'receipt.json'
            for text in ('{"sources":{},"sources":{}}', '{}', '{"value":NaN}'):
                p.write_text(text)
                with self.subTest(text=text), self.assertRaises(ValueError):
                    A.load_json(p, A.RECEIPT_KEYS)

    def test_missing_receipt_returns_failure(self):
        with tempfile.TemporaryDirectory() as td:
            result = A.audit(Path(td), Path(td), require_step=True, final_release=True)
        self.assertEqual(result['status'], 'fail')
        self.assertTrue(result['failures'])

    def test_empty_receipt_returns_failure(self):
        with tempfile.TemporaryDirectory() as td:
            (Path(td) / 'build-receipt.json').write_text(json.dumps({}))
            result = A.audit(Path(td), Path(td), require_step=True, final_release=True)
        self.assertEqual(result['status'], 'fail')
        self.assertTrue(result['failures'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
