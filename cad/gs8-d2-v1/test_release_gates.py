# SPDX-License-Identifier: MIT
"""Fail-closed regression checks for sampled thin-spot classification."""
import unittest
import build_d2 as B


class ClassificationGateTests(unittest.TestCase):
    def test_failed_or_ambiguous_candidate_returns_nonzero_exit(self):
        self.assertEqual(B.release_exit_code(True), 0)
        for value in (False, None, 'pass', 1):
            with self.subTest(value=value):
                self.assertEqual(B.release_exit_code(value), 1)

    def summary(self, spots):
        return B.summarize('critical_features', [B.unclassified_thin_spot_gate(spots)], info_neutral=True)

    def test_empty_explicit_list_passes_classification_only(self):
        result = self.summary([])
        self.assertEqual(result['status'], 'pass')
        self.assertEqual(result['passed'], 1)

    def test_real_unclassified_point_blocks_required_category(self):
        result = self.summary([dict(part='panel', at=[-66.52, 24.0, 69.95], t_min=1.049)])
        self.assertEqual(result['status'], 'fail')
        self.assertEqual(result['failed'], 1)
        self.assertFalse(all(s['status'] == 'pass' for s in [result]))

    def test_informational_label_cannot_waive_unclassified_geometry(self):
        self.assertEqual(self.summary([dict(status='info', part='panel')])['status'], 'fail')

    def test_missing_or_malformed_reports_fail_closed(self):
        for report in (None, {}, '', False, 0):
            with self.subTest(report=report):
                self.assertEqual(self.summary(report)['status'], 'fail')


if __name__ == '__main__':
    unittest.main(verbosity=2)
