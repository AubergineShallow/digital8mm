# D2 recorder integration

2026-10-06, cloud-copy implementation. **Host-tested, not deployed or hardware-qualified.**
The current physical architecture is [D2 HANDOFF section 0](../../cad/gs8-d2-v1/HANDOFF.md) and
[D2 WIRING section 8](../../electronics/gs8-d2-v1/WIRING.md). This package's old `run` command and
`power.py` still serve the historical EVF/GNB **3S** commissioning path. D2 uses the separate modules below;
never connect its X1203 **1S** gauge to the old INA260 policy.

## What is implemented

- D2 input decoding, 10 ms contact qualification, toggle recording and release-to-arm safety.
- Physical 18/24 selection; immutable settings during a take and explicit pending selections.
- Fresh Picamera/preview sessions when idle controls change. The old session must close before a new one opens.
  Settings are no longer incorrectly sent into the existing backend's session-long control lock.
- 1S voltage/SOC qualification, stale/missing/read-error handling, a provisional 3.3 V stop, and a 2 s power hold.
- The existing bounded RAW/DNG pipeline, asynchronous disk writer, drain acknowledgement, journal/hash/commit
  receipt and failed/incomplete-take semantics. The application uses four writer slots.
- A status model for the EVF, independent shutdown-screen hook and ordered close/sync/unmount/poweroff contract.
- [Host-only EVF presentation](D2-PRESENTATION.md): deterministic status pixels, full-sensor viewport geometry
  and labelled preview scenarios. Production compositing/display retention remain unimplemented.
- Optional lazy Linux input/gauge adapters, strict configuration, a real application loop and an explicit
  integrator entrypoint. No hardware library is required for host tests or demonstrations.
- Separate, content-hash-verified bench reports and fresh runtime health. Missing readiness inhibits new takes
  and drains an active take without an OS shutdown request.
- Matching EVF/post applied-metadata bounds and canonical IMX296 identity, with independent planner regressions.

**Not implemented/qualified:** a production EVF status renderer that retains the shutdown screen independently
of Picamera's DRM lifetime; a verified removable-media mount/unmount adapter; the deployment-specific health
reader; a default live application adapter; systemd installation/boot sequencing; measured GPIO/encoder
behavior; real DNG decode/image quality; power, heat, storage throughput or eyepiece latency. This is an
integrable commissioning foundation, not a turn-key camera image. No electrical gate is closed by this work.

## Try it on a host

From `software/gs8-camera-evf`, using Python 3.10 or newer:

```sh
PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests -v
python -m gs8_camera_evf d2-demo --output /tmp/d2-two-takes
python -m gs8_camera_evf d2-demo --output /tmp/d2-low-cell --scenario low-battery
python -m gs8_camera_evf d2-demo --output /tmp/d2-lost-inputs --scenario lost-inputs
python -m gs8_camera_evf inspect --output /tmp/d2-two-takes
```

Use fresh output folders to keep a demo's take count unambiguous. The default demonstration records two
synthetic descriptor takes; the 18/24 switch and gain change during the first take and apply to the second.
The other scenarios exercise drained low-cell/input-loss stops. All use a virtual input clock, test WB values,
real bounded asynchronous storage, and explicitly simulated `.simframe` descriptors. They generate
`d2-demo-summary.json` plus ordinary committed take folders. **They contain no camera footage and no performance
measurement. No GPIO, I2C, display, unmount or poweroff action runs.**

The old `simulate`, `inspect` and `run` commands remain available. `run` remains a scheduled, hold-trigger,
3S/INA260-capable historical bench path; it is not a D2 launch shortcut.

## Controls and interaction

| Physical input | Software behavior | Remaining qualification |
|---|---|---|
| GPIO26 run, active low | One press toggles recording; release alone does not stop. Both contact states settle for 10 ms. | G-W9 bounce/polarity and worst-case sampling under load. |
| GPIO13 FPS | High = 18, low = 24. Changing it during capture only changes the pending selection. | G-W9 wiring and knob orientation. A disconnected pulled-up lead can resemble 18 FPS. |
| Seesaw 0x37 encoder | Clockwise raises gain through 1/2/4/8x; saturates at either end. No wrap to minimum. | This one-stop-per-detent mapping is a conservative proposed interaction; direction/counts require G-W9. |
| Seesaw pin 24 push | Debounced reset to 1x gain; applies after the take. | Uncommissioned until production knob/panel travel is measured at MP-ENC/G-W9. |
| Pi `pwr_button` KEY_POWER | Release after startup, then continuous 2 s hold requests a drained shutdown. Short presses do nothing. | G-W8, including the PMIC's forced-off interval. No software can cancel a hardware forced-off hold. |

No FPS menu, dedicated LEDs, microphones or speakers are added. RAW DNG capture and clean preview are silent.
The default source rates are 54 -> 18 and 48 -> 24, with a fixed 90-degree shutter and explicitly calibrated
WB gains. Changing iris/focus remains mechanical. Exposure/gain adjustments are intentionally applied **between**
takes, with active and selected values separately visible in status. There is no claim of live exposure ramping.

A run press held at boot, during warmup, while saving, or while a setting is changing never queues a later take.
An explicit new press after readiness and release is required. After an unusually slow idle camera setup,
input and battery qualification restart; unseen button/encoder movement is not replayed. A sampling gap during
an active take still causes a drained stop. A warmup that does not settle within ten seconds fails explicitly.

The starting r5 snapshot had only 0.2 mm knob-to-panel rest gap and 0.25 mm bushing clearance, with push travel
unmeasured. Later CAD refinements do not substitute for an assembled full-travel test: the push must actuate
without knob/panel/bushing contact, then return reliably. No essential menu or shutdown function depends on push.

## Application interfaces

`D2Runtime(store, backend_factory, now_ns=..., wb_gains=..., simulation_only=...)` is the deterministic recorder
owner. Feed `step()` `D2InputSample`, `D2BatterySample`, and, for a physical runtime, `D2HealthSample` from the
same monotonic clock domain. Acquisitions must be stamped when reading begins, not when a blocked read returns.
Repeated cached values do not advance button/battery qualification. Error fields latch a drained stop.

- `d2_controls.py`: contact/encoder/power semantics. A fresh control sample is at most 100 ms old.
- `d2_power.py`: `D2BatteryPolicy`, `D2Shutdown` and `ShutdownActions`. Battery maximum age is 500 ms; startup
  requires one second of fresh readings above the threshold. Voltage <= 3300 mV stops immediately by default.
  A 3S voltage, malformed sample or lost gauge is an error; SOC never substitutes for cell voltage.
- `d2_readiness.py`: `load_commissioning()` and runtime readiness validation.
- `d2_io.py`: `LatestReader`, `X1203GaugeReader`, `open_linux_inputs()`.
- `d2_runtime.py`: per-take control freezing, session replacement, status and `picamera_backend_factory()`.
- `d2_presentation.py`: pure `present_status`, `present_shutdown` and straight-alpha RGBA rasterization;
  [its compositor contract](D2-PRESENTATION.md) must be integrated before use on the real EVF.
- `d2_app.py`: `D2Config`, `D2Adapters`, `run_application()` and CLI entrypoints.

`D2Adapters` supplies separate readers (`read()` / `close()`), a backend factory, `show_status(status)`,
`hold_shutdown_screen()`, an optional runtime health reader and optional `ShutdownActions`. Readers transfer
ownership to the application immediately, including validation/open failures. An adapter factory must clean
its own partially acquired devices if it raises before returning. `LatestReader` owns one bounded latest slot
and performs device cleanup in its worker; a blocked read never blocks capture. Its pending cleanup is reported,
not falsely marked complete. Pending or failed reader cleanup blocks opt-in poweroff; it is not retried
blindly. No read-only peripheral worker owns footage.

The backend factory creates a fresh backend for each new settings session. Returning a different simulation
flag or a conflicting sensor descriptor fails. The optional Pi factory uses the tested `PicameraEvfBackend`
interface and uniform D2 cadence. Tests also drive that adapter through fake-camera reconfiguration, not only
`SimulationBackend`. The recorder's optional fault observer lets D2 retain its shutdown screen before fault
cleanup closes preview. Existing users without an observer retain the original behavior.

`show_status` must return promptly; it must not perform slow I/O, create an unbounded event queue, or retain
camera buffers. The application stops ordinary status painting once shutdown is latched, preserving the
shutdown-screen owner. `D2Status` includes phase, active/selected FPS and gain, pending-settings flag, measured
battery telemetry, warning/reason, failure, latest clip, readiness reasons and explicit simulation/hardware labels.
`ready` is a software state, `stopped` is a capture state, and `poweroff_requested` is only an OS request.
None means that the PMIC is off or it is safe to remove a battery. Every returned status retains
`hardware_qualified: false`; physical acceptance is an external evidence process.

## Explicit configuration and launch boundary

`examples/d2.config.example.json` deliberately has no WB calibration and references an absent commissioning
record. It must fail until populated with the actual build's measured values. `examples/d2.commissioning.example.json`
is deliberately `not_run`; changing labels without doing the gate procedures does not create evidence.

An installed, reviewed integrator module can expose `build(config) -> D2Adapters`, then launch:

```sh
python -m gs8_camera_evf d2-run --config /path/to/d2.config.json --adapter your_d2_adapter:build
```

The module name is an explicit trusted-code selection, not arbitrary code embedded in a JSON config.
Unknown config keys reject. Relative paths resolve against the config file's directory. Physical configuration
requires a commissioning manifest; the manifest is verified before importing an adapter that may open devices.
A programmatic physical runtime likewise remains unready without qualification and runtime health.

The application defaults to `shutdown_mode: "drain_only"`. A power key/low-cell/input failure safely ends capture
and returns, but does **not** halt the Pi. This mode alone does not satisfy G-W8 or authorize battery removal.
Only an explicit `"poweroff"` configuration plus all commissioned shutdown adapters requests normal OS poweroff.
Simulation configuration rejects poweroff mode. The application never installs packages/services, changes
EEPROM/config.txt/logind, creates output GPIOs, or invokes a shell command of its own.

## Bench evidence versus live readiness

One-time commissioning evidence is a JSON manifest with:

- `schema_version: 1`, `evidence_type: "measured_hardware"`, an actual `build_id`, named `reviewed_by`, and a
  timezone-qualified `recorded_at` date. Identify the camera, pack, storage device, cooling, OS/source revision,
  measured WB and test conditions in the reports. Requalify material changes.
- Reviewed `pass` reports for G-W10, G-W11 and G-W12, each referenced by a relative local path and SHA-256.
  Missing/changed/outside-folder reports reject. Hashes establish traceability and detect changed files;
  they are **not a digital signature or proof that a reported measurement is true**.
- Actual bench measurements meeting the existing necessary limits: maximum 100 ms workload power <= 22.9 W;
  header rail minimum >= 4850 mV and 1 s mean >= 4950 mV; SoC < 80 C; boost <= 70 C; XT30/pad joints <= 60 C;
  warm, part-filled sustained storage rate >= 100 MB/s. Do not substitute ratings, estimates or short burst speed.

These selected bounds do not replace the full gate procedures. Reports must cover the specified closed-body
thermal conditions, load states, battery range, repeated startups, no resets/throttling, frame counts and readable
shutdown take before their reviewed status is pass. The 27 W planning peak versus 25.5 W supply problem remains
open until G-W12 is actually measured. No software readiness flag resolves that deficit.

Runtime `D2HealthSample` contains only observable SoC temperature, throttle bits (including sticky flags),
detected USB resets, verified mounted/writable-media state and free bytes. It must be <= 1 s old. The integrator
must bind these observations to the actual qualified storage device/mount; do not use a writable underlying
root-filesystem directory after a USB mount disappears. Free space must exceed the configured reserve.
The X1203 reader is not asked to produce watts, header-rail waveforms or connector temperatures it cannot measure.

Missing/stale/failed runtime readiness inhibits new takes; loss during recording drains the take and leaves
an explicit `unready`/`degraded` status. Restored readiness never replays a held press. This alone does not request
OS shutdown. Battery-telemetry loss and a real low-cell reading use the separately latched drained battery stop.
The 3.3 V value remains provisional: G-W5/G-W12 can require raising it in 0.05 V steps. The equality case at 3.3 V
stops, so reconcile the start-at-3.3 V planning test with the measured threshold before commissioning.

## Shutdown and cleanup

The order is:

1. `hold_shutdown_screen()` establishes display ownership independent of the capture backend.
2. Stop capture, drain accepted frames, finish/verify the writer commit, and close the backend.
3. Close the clip store; synchronize the explicitly verified media.
4. Unmount that media successfully; request normal OS poweroff.
5. Hardware/OS retains the shutdown image until halt, then EVF dark is measured at G-W8.

Steps 3/4 are explicit callbacks. The application supplies `store.close` itself and never guesses a mount,
executes an unmount command, asserts OS_HALTED or forces a power cut. A callback exception blocks every later
stage. There is no blind retry of an uncertain unmount/poweroff. A capture/commit timeout does not authorize halt.
Reader/capture cleanup must finish without errors before the OS request. During exceptional cleanup a queued writer is joined before
a backend can remove its `FilePayload` staging files. Interrupted takes remain visibly failed/incomplete.

The existing Picamera backend closes DRM on shutdown. A live renderer must therefore transfer/retain the
shutdown image outside that backend. Merely printing JSON or supplying a no-op callback does not satisfy this
requirement. No default live renderer or automatic shutdown service is shipped here, and no display persistence,
USB unmount or actual OS halt was tested.

## Linux adapters and source grounding

Optional imports occur only when an operator explicitly opens a device:

- `open_linux_inputs(chip_path=..., power_device_path=...)` requires libgpiod v2, evdev, Blinka and Adafruit seesaw.
  It checks RP1 chip label and GPIO line names, and checks `pwr_button`/KEY_POWER identity. GPIO paths are supplied,
  never assumed from a kernel's chip number. It reads GPIO26/13 as electrical levels with input pull-ups.
- The seesaw firmware product identifier must be 4991 (the same firmware family as assembled 5880), at address
  0x37 after A0 bridging. Push pin is 24. Default encoder sign is -1 per Adafruit's assembled-encoder guidance;
  G-W9 verifies the actual assembled orientation. No NeoPixel object or LED output is created.
- `X1203GaugeReader.open(bus_number=1)` uses smbus2 read-word operations at 0x36 registers 0x02/0x04. Bytes swap
  into VCELL * 1.25/16 mV and SOC / 256 percent. No charging configuration, gauge reset or GPIO6/16 write occurs.

Primary API/register references reviewed for this implementation:
[Geekworm X1203 hardware](https://wiki.geekworm.com/X1203_Hardware),
[Geekworm X120x software](https://wiki.geekworm.com/X120X_Software),
[Suptronics gauge example](https://github.com/suptronics/x120x/blob/main/qtx120x.py),
[Adafruit encoder guide](https://learn.adafruit.com/adafruit-i2c-qt-rotary-encoder?view=all),
[libgpiod Python request API](https://libgpiod.readthedocs.io/en/v2.3/python_line_request.html),
[python-evdev API](https://python-evdev.readthedocs.io/en/latest/apidoc.html).
Pin the actual Pi package/kernel versions after commissioning; current online documentation is not a hardware test.

## EVF/post correction and remaining output boundaries

The EVF now rejects applied exposure outside max(100 us, 0.5%) and gain/WB outside max(0.01, 1%), matching the
independent post planner. Warmup uses the same checks. Exact case/whitespace-normalized IMX296 names become
`imx296`, with `model_reported` retaining the device string; unrelated suffixed/prefixed names reject.
Tests commit supported synthetic physical-schema takes and pass them through the independent planner, and reject
invalid metadata before handoff. Fixtures use explicitly invalid/test-only DNG bytes and are removed afterward.
Actual sensor quantization must still be measured; tighter validation can correctly keep an unsupported setting unready.

D2 uses only uniform default rates. The historical EVF API retains uneven source-rate options, now explicitly
marked unsupported by the current post planner. Real timestamps are never rewritten to conceal that boundary.
Post remains `planned_not_rendered`: it does not decode DNG, run the film engine, encode or mux footage.
The inherited engine's numerical model checks do not establish a finished Super 8 sequence pipeline or IMX296
spectral calibration. Its existing licensing/provenance and calibration limits remain unchanged.
