# SPDX-License-Identifier: MIT
"""Optional, lazy D2 Linux readers and bounded latest-sample transport.

No charger, NeoPixel, LED, GPIO output, cutoff or system-power command exists
here. Opening controls configures input pull-ups. Hardware remains untested.
See D2-INTEGRATION.md for the primary API/register sources and bench gates.
"""
from contextlib import ExitStack
from threading import Event, Lock, Thread
import math
import time

from .d2_controls import D2InputSample, RUN_GPIO, FPS_GPIO, ENCODER_ADDRESS, ENCODER_PUSH_PIN
from .d2_power import D2BatterySample


class LatestReader:
    """One read-only worker/slot; a blocked peripheral cannot block recording.

    Samples timestamp acquisition start in the reader, not delivery here.
    Errors latch. close() never closes a device beneath an in-flight call; the
    worker owns device cleanup. False means cleanup is still pending, not done.
    """
    def __init__(self, reader, *, interval_seconds, name='d2-input'):
        if (type(interval_seconds) not in (int, float) or not math.isfinite(interval_seconds)
                or not 0 < interval_seconds <= 1):
            raise ValueError('reader interval must be finite and in (0, 1] seconds')
        self.reader = reader
        self.interval = interval_seconds
        self._sample = self._error = self._close_error = None
        self._lock, self._stop = Lock(), Event()
        self._thread = Thread(target=self._run, name=name, daemon=True)
        self._thread.start()

    def _run(self):
        try:
            while not self._stop.is_set():
                sample = self.reader.read()
                with self._lock:
                    self._sample = sample
                self._stop.wait(self.interval)
        except Exception as error:
            with self._lock:
                self._error = f'{type(error).__name__}: {error}'
        finally:
            try:
                self.reader.close()
            except Exception as error:
                with self._lock:
                    self._close_error = f'close: {type(error).__name__}: {error}'
                    self._error = self._error or self._close_error

    def poll(self):
        with self._lock:
            return self._sample, self._error

    def close(self):
        self._stop.set()
        self._thread.join(timeout=.2)
        finished = not self._thread.is_alive()
        with self._lock:
            close_error = self._close_error
        if finished and close_error is not None:
            raise RuntimeError(close_error)
        return finished


class X1203GaugeReader:
    """Read only 0x36 VCELL/SOC via an injected SMBus word reader.

    Supplier uses byte-swapped register 0x02 * 1.25/16 mV and 0x04 /256 %.
    Never use the older package's INA260/3S thresholds with this reader.
    """
    address = 0x36

    def __init__(self, bus, *, clock_ns=time.monotonic_ns):
        self.bus, self.clock = bus, clock_ns

    @staticmethod
    def _swap(value):
        if type(value) is not int or not 0 <= value <= 0xffff:
            raise ValueError('gauge returned an invalid SMBus word')
        return (value & 0xff) << 8 | value >> 8

    def read(self):
        started = self.clock()
        voltage = self._swap(self.bus.read_word_data(self.address, 0x02))
        capacity = self._swap(self.bus.read_word_data(self.address, 0x04))
        return D2BatterySample(started, round(voltage * 5 / 64), capacity / 256)

    def close(self):
        self.bus.close()

    @classmethod
    def open(cls, *, bus_number=1):
        if type(bus_number) is not int or bus_number < 0:
            raise ValueError('I2C bus number must be a nonnegative integer')
        from smbus2 import SMBus
        return cls(SMBus(bus_number))


class LinuxD2Inputs:
    """Transport adapter. Position is normalized so clockwise raises gain.

    Inputs are sequential reads, not an atomic physical snapshot. D2Controls
    qualifies contact stability. active_keys() reads actual KEY_POWER state;
    keyboard repeats cannot extend a released press. No event-device grabbing.
    """
    def __init__(self, lines, value_enum, encoder, push, power_device, power_key_code,
                 *, cleanup, encoder_sign=-1, clock_ns=time.monotonic_ns):
        if type(encoder_sign) is not int or encoder_sign not in (-1, 1):
            raise ValueError('encoder_sign must be -1 or 1; verify clockwise at G-W9')
        if power_device.name != 'pwr_button':
            raise ValueError('D2 power input must be the verified pwr_button device')
        self.lines, self.value_enum, self.encoder = lines, value_enum, encoder
        self.push, self.power, self.power_key = push, power_device, power_key_code
        self.cleanup, self.sign, self.clock = cleanup, encoder_sign, clock_ns

    def _high(self, value):
        if value == self.value_enum.ACTIVE:
            return True  # active_low=False in the GPIO request: logical active is electrically high
        if value == self.value_enum.INACTIVE:
            return False
        raise ValueError('GPIO returned an invalid electrical level')

    def read(self):
        started = self.clock()
        levels = self.lines.get_values([RUN_GPIO, FPS_GPIO])
        if len(levels) != 2:
            raise ValueError('D2 GPIO read did not return both controls')
        raw_position = self.encoder.position
        if type(raw_position) is not int or not -(2**31) <= raw_position < 2**31:
            raise ValueError('seesaw position is not signed 32-bit')
        position = (self.sign * raw_position + 2**31) % 2**32 - 2**31
        push_high = self.push.value
        if type(push_high) is not bool:
            raise ValueError('seesaw push value must be boolean')
        return D2InputSample(started, self._high(levels[0]), self._high(levels[1]), position,
                             push_high, self.power_key in self.power.active_keys())

    def close(self):
        self.cleanup()


def open_linux_inputs(*, chip_path, power_device_path, encoder_sign=-1):
    """Explicit hardware opt-in; rejects a wrong RP1 chip or input-device name.

    Uses libgpiod v2, evdev, Blinka and Adafruit seesaw, already installed by a
    commissioning operator. It does not install packages or configure the OS.
    D2 uses address 0x37 after A0 bridging, avoiding the gauge at 0x36.
    """
    if type(encoder_sign) is not int or encoder_sign not in (-1, 1):
        raise ValueError('encoder_sign must be -1 or 1; verify clockwise at G-W9')
    import gpiod
    from gpiod.line import Direction, Bias, Value
    from evdev import InputDevice, ecodes
    import board
    from adafruit_seesaw import digitalio, rotaryio, seesaw

    with ExitStack() as cleanup:
        chip = cleanup.enter_context(gpiod.Chip(str(chip_path)))
        if chip.get_info().label != 'pinctrl-rp1':
            raise ValueError('selected GPIO chip is not pinctrl-rp1; verify the Pi 5 header mapping')
        for offset in (RUN_GPIO, FPS_GPIO):
            if chip.get_line_info(offset).name != f'GPIO{offset}':
                raise ValueError(f'RP1 line {offset} is not named GPIO{offset}; verify mapping before use')
        lines = chip.request_lines(consumer='gs8-d2-inputs', config={
            (RUN_GPIO, FPS_GPIO): gpiod.LineSettings(direction=Direction.INPUT, bias=Bias.PULL_UP, active_low=False)})
        cleanup.callback(lines.release)
        power = InputDevice(str(power_device_path))
        cleanup.callback(power.close)
        if power.name != 'pwr_button' or ecodes.KEY_POWER not in power.capabilities().get(ecodes.EV_KEY, []):
            raise ValueError('selected input device is not the Pi pwr_button with KEY_POWER')
        i2c = board.I2C()
        cleanup.callback(i2c.deinit)
        device = seesaw.Seesaw(i2c, addr=ENCODER_ADDRESS)
        if (device.get_version() >> 16) & 0xffff != 4991:
            raise ValueError('seesaw at 0x37 is not the expected 4991/5880 encoder firmware')
        device.pin_mode(ENCODER_PUSH_PIN, device.INPUT_PULLUP)
        encoder = rotaryio.IncrementalEncoder(device)
        push = digitalio.DigitalIO(device, ENCODER_PUSH_PIN)
        reader = LinuxD2Inputs(lines, Value, encoder, push, power, ecodes.KEY_POWER,
                                cleanup=lambda: None, encoder_sign=encoder_sign)
        reader.cleanup = cleanup.pop_all().close
        return reader
