# SPDX-License-Identifier: MIT
"""Fake buses and threads only; never opens Linux devices."""
from enum import Enum
from threading import Event
from types import SimpleNamespace
import time
import unittest

from gs8_camera_evf.d2_io import X1203GaugeReader, LinuxD2Inputs, LatestReader


class Value(Enum):
    INACTIVE = 0
    ACTIVE = 1


class IoTests(unittest.TestCase):
    def test_x1203_correct_endianness_units_registers_and_acquisition_time(self):
        calls = []
        def read(address, register):
            calls.append((address, register))
            return {2: 0x00c3, 4: 0x804b}[register]  # 3900 mV, 75.5 %
        reader = X1203GaugeReader(SimpleNamespace(read_word_data=read, close=lambda: calls.append('close')),
                                  clock_ns=lambda: 42)
        sample = reader.read()
        self.assertEqual((sample.acquired_ns, sample.millivolts, sample.percent), (42, 3900, 75.5))
        self.assertEqual(calls, [(0x36, 2), (0x36, 4)])
        reader.close()
        self.assertEqual(calls[-1], 'close')

    def test_gauge_errors_and_invalid_words_are_not_converted_to_zero(self):
        def failed(*args):
            raise OSError('unplugged')
        for read, error in ((failed, OSError), (lambda *args: -1, ValueError), (lambda *args: True, ValueError)):
            with self.subTest(read=read), self.assertRaises(error):
                X1203GaugeReader(SimpleNamespace(read_word_data=read)).read()

    def test_gpio_mapping_encoder_sign_and_power_level(self):
        calls = []
        def get_values(offsets):
            calls.append(offsets)
            return [Value.INACTIVE, Value.ACTIVE]
        reader = LinuxD2Inputs(SimpleNamespace(get_values=get_values), Value,
                                SimpleNamespace(position=-2), SimpleNamespace(value=True),
                                SimpleNamespace(name='pwr_button', active_keys=lambda: [116]), 116,
                                cleanup=lambda: calls.append('close'), clock_ns=lambda: 99)
        sample = reader.read()
        self.assertEqual((sample.run_high, sample.fps_high, sample.encoder_position, sample.power_pressed),
                         (False, True, 2, True))
        self.assertEqual(sample.acquired_ns, 99)
        self.assertEqual(calls, [[26, 13]])
        reader.close()
        self.assertEqual(calls[-1], 'close')

    def test_wrong_power_device_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'pwr_button'):
            LinuxD2Inputs(None, None, None, None, SimpleNamespace(name='keyboard'), 116, cleanup=lambda: None)

    def test_encoder_sign_wrap_stays_signed_32bit(self):
        reader = LinuxD2Inputs(SimpleNamespace(get_values=lambda _: [Value.ACTIVE] * 2), Value,
                                SimpleNamespace(position=-(2**31)), SimpleNamespace(value=True),
                                SimpleNamespace(name='pwr_button', active_keys=lambda: []), 116,
                                cleanup=lambda: None)
        self.assertEqual(reader.read().encoder_position, -(2**31))

    def test_blocked_reader_never_blocks_poll_or_closes_device_while_reading(self):
        entered, unblock, closed = Event(), Event(), Event()
        class Reader:
            def read(self):
                entered.set()
                if not unblock.wait(3):
                    raise TimeoutError('test deadlock')
                return 'actual sample'
            def close(self):
                closed.set()
        worker = LatestReader(Reader(), interval_seconds=.01)
        try:
            self.assertTrue(entered.wait(1))
            before = time.monotonic()
            self.assertEqual(worker.poll(), (None, None))
            self.assertLess(time.monotonic() - before, .1)
            self.assertFalse(worker.close())
            self.assertFalse(closed.is_set())
        finally:
            unblock.set()
            self.assertTrue(closed.wait(1))
            self.assertTrue(worker.close())

    def test_reader_error_is_latched_and_cleanup_runs(self):
        done = Event()
        class Reader:
            def read(self):
                raise OSError('test bus error')
            def close(self):
                done.set()
        worker = LatestReader(Reader(), interval_seconds=.01)
        self.assertTrue(done.wait(1))
        self.assertIn('test bus error', worker.poll()[1])
        self.assertTrue(worker.close())

    def test_invalid_encoder_sign_rejects_before_hardware_imports(self):
        from gs8_camera_evf.d2_io import open_linux_inputs
        with self.assertRaisesRegex(ValueError, 'encoder_sign'):
            open_linux_inputs(chip_path='/not/a/device', power_device_path='/not/a/device', encoder_sign=0)

    def test_worker_device_close_failure_is_reported_by_close_without_retry(self):
        done = Event()
        calls = []
        class Reader:
            def read(self):
                raise OSError('injected read failure')
            def close(self):
                calls.append('close')
                done.set()
                raise OSError('injected device cleanup failure')
        worker = LatestReader(Reader(), interval_seconds=.01)
        self.assertTrue(done.wait(1))
        with self.assertRaisesRegex(RuntimeError, 'device cleanup failure'):
            worker.close()
        self.assertIn('read failure', worker.poll()[1])
        self.assertEqual(calls, ['close'])
