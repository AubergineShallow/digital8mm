# SPDX-License-Identifier: MIT
"""Synthetic bench-report fixtures test validation only, never hardware evidence."""
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
import hashlib
import json
import unittest

from gs8_camera_evf.d2_readiness import (D2HealthSample, D2Commissioning, bench_limit_failures,
                                       evaluate_readiness, load_commissioning)

MEASUREMENTS = {'power_100ms_w': 22.9, 'header_min_mv': 4850, 'header_mean_mv': 4950,
                'soc_temperature_c': 79.9, 'boost_temperature_c': 70, 'xt30_temperature_c': 60,
                'pad_temperature_c': 60, 'sustained_write_mb_s': 100}
TEST_QUALIFICATION = D2Commissioning('synthetic-test-only', True, True)


def write_test_manifest(directory):
    root = Path(directory)
    report = root / 'NOT-HARDWARE-test-report.txt'
    report.write_text('SYNTHETIC TEST ONLY. NO MEASUREMENT. Not usable commissioning evidence.\n')
    entry = {'status': 'pass', 'report': report.name, 'sha256': hashlib.sha256(report.read_bytes()).hexdigest()}
    # The schema marker is a test input, not a statement about the fixture.
    manifest = {'schema_version': 1, 'evidence_type': 'measured_hardware', 'build_id': 'synthetic-test-only',
                'reviewed_by': 'test-fixture', 'recorded_at': '2026-10-06T00:00:00+00:00',
                'gates': {gate: entry.copy() for gate in ('G-W10', 'G-W11', 'G-W12')},
                'measurements': MEASUREMENTS.copy()}
    path = root / 'commissioning-test-only.json'
    path.write_text(json.dumps(manifest))
    return path, manifest, report


class ReadinessTests(unittest.TestCase):
    def health(self, **changes):
        return replace(D2HealthSample(0, 50, 0, 0, True, 10_000), **changes)

    def test_bench_and_live_evidence_are_distinct_and_both_required(self):
        self.assertFalse(evaluate_readiness(0, self.health(), reserve_bytes=1000).ready)
        self.assertFalse(evaluate_readiness(0, None, reserve_bytes=1000, commissioning=TEST_QUALIFICATION).ready)
        result = evaluate_readiness(0, self.health(), reserve_bytes=1000, commissioning=TEST_QUALIFICATION)
        self.assertTrue(result.ready)
        self.assertEqual(result.state, 'reported_limits_pass')

    def test_existing_gw12_boundaries_are_enforced(self):
        self.assertEqual(bench_limit_failures(MEASUREMENTS), ())
        for key, value in (('power_100ms_w', 22.91), ('header_min_mv', 4849), ('header_mean_mv', 4949),
                           ('soc_temperature_c', 80), ('boost_temperature_c', 70.1),
                           ('xt30_temperature_c', 60.1), ('pad_temperature_c', 60.1),
                           ('sustained_write_mb_s', 99.9)):
            with self.subTest(key=key):
                self.assertTrue(bench_limit_failures({**MEASUREMENTS, key: value}))
        self.assertTrue(bench_limit_failures({}))
        self.assertTrue(bench_limit_failures({**MEASUREMENTS, 'power_100ms_w': float('nan')}))

    def test_missing_stale_or_faulty_runtime_observations_inhibit(self):
        for changes in ({'throttled_bits': 1 << 16}, {'usb_resets': 1}, {'soc_temperature_c': 80},
                        {'media_writable': False}, {'media_writable': 1}, {'free_bytes': 1000},
                        {'soc_temperature_c': None}, {'throttled_bits': False}, {'acquired_ns': 1}):
            with self.subTest(changes=changes):
                self.assertFalse(evaluate_readiness(0, self.health(**changes), reserve_bytes=1000,
                                                    commissioning=TEST_QUALIFICATION).ready)
        self.assertFalse(evaluate_readiness(1_000_000_001, self.health(), reserve_bytes=1000,
                                            commissioning=TEST_QUALIFICATION).ready)

    def test_report_hashes_are_verified_and_bad_measurements_do_not_pass(self):
        with TemporaryDirectory() as tmp:
            path, value, report = write_test_manifest(tmp)
            self.assertTrue(load_commissioning(path).limits_passed)
            value['measurements']['power_100ms_w'] = 27
            path.write_text(json.dumps(value))
            qualification = load_commissioning(path)
            self.assertFalse(qualification.limits_passed)
            self.assertTrue(qualification.artifacts_verified)
            report.write_text('changed test report')
            with self.assertRaisesRegex(ValueError, 'hash'):
                load_commissioning(path)

    def test_unreviewed_simulated_reports_and_traversal_rejected(self):
        with TemporaryDirectory() as tmp:
            path, original, _ = write_test_manifest(tmp)
            for change in ({'evidence_type': 'simulation'}, {'schema_version': True}, {'reviewed_by': ''},
                           {'recorded_at': '2026-10-06'}, {'gates': {}},
                           {'gates': {'G-W10': {'status': 'pass', 'report': '../elsewhere', 'sha256': '0' * 64}}}):
                with self.subTest(change=change):
                    path.write_text(json.dumps({**original, **change}))
                    with self.assertRaises(ValueError):
                        load_commissioning(path)

    def test_inconsistent_bench_minimum_and_mean_are_rejected(self):
        self.assertIn('bench_header_min_exceeds_mean', bench_limit_failures({**MEASUREMENTS, 'header_min_mv': 6000}))
