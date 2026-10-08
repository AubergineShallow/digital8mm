# SPDX-License-Identifier: MIT
"""Application/CLI tests use fake sources, clocks and temporary descriptor files."""
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import io
import json
import time
import unittest

from gs8_camera_evf.backends import SimulationBackend
from gs8_camera_evf.cli import main
from gs8_camera_evf.d2_app import D2Config, D2Adapters, run_application, run_demo
from gs8_camera_evf.d2_controls import D2InputSample
from gs8_camera_evf.d2_power import D2BatterySample


class AppTests(unittest.TestCase):
    def test_config_rejects_unsafe_or_ambiguous_values_before_opening_hardware(self):
        with TemporaryDirectory() as tmp:
            for change in ({'simulation_only': False}, {'shutdown_mode': 'poweroff'}, {'reserve_mib': -1},
                           {'wb_gains': None}, {'poll_interval_ms': 0}, {'stop_millivolts': 3200},
                           {'drain_timeout_seconds': float('nan')}, {'simulation_only': 1}):
                with self.subTest(change=change), self.assertRaises(ValueError):
                    D2Config(**{'output': Path(tmp), 'wb_gains': (1.5, 1.25), 'simulation_only': True, **change})

    def test_json_paths_resolve_relative_to_config_and_unknown_keys_reject(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / 'config.json'
            value = {'schema_version': 1, 'output': 'takes', 'wb_gains': [1.5, 1.25], 'simulation_only': True}
            path.write_text(json.dumps(value))
            # Compare canonical paths: on Windows the temp dir may be an 8.3 short name (PRE-IN~1) that resolve() expands.
            self.assertEqual(D2Config.load(path).output, Path(tmp).resolve() / 'takes')
            value['gpio_output'] = 25
            path.write_text(json.dumps(value))
            with self.assertRaises(ValueError):
                D2Config.load(path)

    def test_application_drain_only_holds_screen_closes_sources_and_never_powers_off(self):
        with TemporaryDirectory() as tmp:
            events, phases = [], []
            class Clock:
                now = 0
                def read(self):
                    return self.now
                def sleep(self, seconds):
                    self.now += 10_000_000
                    time.sleep(.001)  # schedule the real bounded disk writer
            clock = Clock()
            class Inputs:
                def read(self):
                    ms = clock.now // 1_000_000
                    return D2InputSample(clock.now, not (1200 <= ms < 1240), False, 0, True, ms >= 2000)
                def close(self):
                    events.append('inputs_closed')
            class Battery:
                def read(self):
                    return D2BatterySample(clock.now, 3900, 80)
                def close(self):
                    events.append('battery_closed')
            class Monitor:
                def __init__(self, reader, **kwargs):
                    self.reader = reader
                def poll(self):
                    return self.reader.read(), None
                def close(self):
                    self.reader.close()
                    return True
            adapters = D2Adapters(Inputs(), Battery(), lambda settings: SimulationBackend(),
                                  lambda status: phases.append(status.phase), lambda: events.append('shutdown_screen'))
            config = D2Config(Path(tmp), (1.5, 1.25), simulation_only=True, reserve_mib=0)
            result = run_application(config, adapters, clock_ns=clock.read, sleep=clock.sleep,
                                     manage_signals=False, reader_factory=Monitor)
            self.assertTrue(result['capture_safely_drained'])
            self.assertFalse(result['os_poweroff_requested'])
            self.assertFalse(result['os_halt_verified'])
            self.assertIn('recording', phases)
            self.assertEqual(events.count('shutdown_screen'), 1)
            self.assertIn('inputs_closed', events)
            self.assertIn('battery_closed', events)
            manifest = json.loads(next(Path(tmp).glob('*/manifest.json')).read_text())
            self.assertTrue(manifest['simulated'])
            self.assertEqual(manifest['status'], 'complete')

    def test_demo_scenarios_are_durable_descriptors_and_no_os_actions(self):
        for scenario, count in (('two-takes', 2), ('low-battery', 1), ('lost-inputs', 1)):
            with self.subTest(scenario=scenario), TemporaryDirectory() as tmp, redirect_stdout(io.StringIO()):
                self.assertEqual(run_demo(SimpleNamespace(output=Path(tmp), scenario=scenario)), 0)
                result = json.loads((Path(tmp) / 'd2-demo-summary.json').read_text())
                self.assertTrue(result['simulation_only'])
                self.assertFalse(result['contains_camera_footage'])
                self.assertFalse(result['hardware_qualified'])
                self.assertFalse(result['os_poweroff_requested'])
                self.assertEqual(len(result['clips']), count)
                for clip in result['clips']:
                    manifest = json.loads((Path(clip) / 'manifest.json').read_text())
                    self.assertEqual(manifest['status'], 'complete')
                    self.assertTrue(manifest['simulated'])
                    self.assertFalse(manifest['settings']['audio'])

    def test_cli_keeps_old_commands_and_exposes_explicit_d2_commands(self):
        output = io.StringIO()
        with redirect_stdout(output), self.assertRaises(SystemExit) as result:
            main(['--help'])
        self.assertEqual(result.exception.code, 0)
        for command in ('simulate', 'inspect', 'run', 'd2-demo', 'd2-run'):
            self.assertIn(command, output.getvalue())
        with TemporaryDirectory() as tmp, redirect_stdout(io.StringIO()):
            self.assertEqual(main(['d2-demo', '--output', tmp]), 0)

    def test_malformed_adapter_has_clean_error(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / 'config.json'
            path.write_text(json.dumps({'schema_version': 1, 'output': 'takes', 'wb_gains': [1.5, 1.25],
                                        'simulation_only': True}))
            with redirect_stderr(io.StringIO()):
                self.assertEqual(main(['d2-run', '--config', str(path), '--adapter', 'bad/input']), 1)

    def test_validation_failure_closes_all_supplied_readers(self):
        calls = []
        class Reader:
            def __init__(self, name):
                self.name = name
            def read(self):
                return None
            def close(self):
                calls.append(self.name)
        adapters = D2Adapters(Reader('input'), Reader('battery'), lambda settings: None, lambda status: None,
                              lambda: None, Reader('health'))
        with self.assertRaises(ValueError):
            run_application(None, adapters, manage_signals=False)
        self.assertEqual(sorted(calls), ['battery', 'health', 'input'])

    def test_partial_worker_acquisition_and_failing_close_do_not_leak_other_readers(self):
        calls = []
        class Reader:
            def __init__(self, name):
                self.name = name
            def read(self):
                return None
            def close(self):
                calls.append(self.name)
                if self.name == 'input':
                    raise OSError('injected close failure')
        class Monitor:
            def __init__(self, reader, **kwargs):
                if reader.name == 'battery':
                    raise OSError('injected worker creation failure')
                self.reader = reader
            def close(self):
                self.reader.close()
        with TemporaryDirectory() as tmp:
            adapters = D2Adapters(Reader('input'), Reader('battery'), lambda settings: None, lambda status: None,
                                  lambda: None, Reader('health'))
            config = D2Config(Path(tmp), (1.5, 1.25), simulation_only=True)
            with self.assertRaisesRegex(RuntimeError, 'cleanup'):
                run_application(config, adapters, manage_signals=False, reader_factory=Monitor)
        self.assertEqual(sorted(calls), ['battery', 'health', 'input'])

    def test_config_rejects_post_incompatible_white_balance(self):
        with TemporaryDirectory() as tmp:
            for gains in ((33, 1.25), (.001, 1.25)):
                with self.subTest(gains=gains), self.assertRaisesRegex(ValueError, '0.01..32'):
                    D2Config(Path(tmp), gains, simulation_only=True)
            self.assertEqual(D2Config(Path(tmp), [1.5, 1.25], simulation_only=True).wb_gains, (1.5, 1.25))

    def test_demo_refuses_to_mix_existing_takes_with_synthetic_evidence(self):
        with TemporaryDirectory() as tmp:
            prior = Path(tmp) / 'existing-real-take'
            prior.mkdir()
            with self.assertRaisesRegex(ValueError, 'new or empty'):
                run_demo(SimpleNamespace(output=Path(tmp), scenario='two-takes'))
            self.assertTrue(prior.is_dir())
            self.assertFalse((Path(tmp) / 'd2-demo-summary.json').exists())
