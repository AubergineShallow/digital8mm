# GS8 EVF software fork

## D2 cloud-copy integration (2026-10-06)

For D2's physical 18/24 switch, toggle-run input and **1S X1203** power policy,
start with [D2-INTEGRATION.md](D2-INTEGRATION.md). The new `d2-demo` command runs
labelled synthetic controls/descriptor takes on a host; `d2-run` is an explicit
integrator adapter/config entrypoint with no default live deployment. D2 host
logic is tested; physical GPIO, display retention, media handling and power/heat
qualification remain open. The historical `run` path and **3S** battery text
below are preserved and must not be used as D2 wiring/configuration.

[D2-PRESENTATION.md](D2-PRESENTATION.md) adds pure host-rendered EVF status pixels
and a labelled preview gallery. Its full-sensor viewport requires a future
compositor adapter; it is not a drop-in overlay or verified shutdown display.

## Historical release-v1 / GNB 3S commissioning path

The remaining commands and battery configuration describe the preserved
**3S / hold-trigger** path, not D2's **1S / toggle-run** path. For the D2 cloud
copy, use [D2-INTEGRATION](D2-INTEGRATION.md) and the project-level
[CLOUD-START-HERE](../../CLOUD-START-HERE.md).

Historical branch battery: **GNB11003S60AHV 3S LiHV**, charged outside the camera.
`power.py` supplies the common pack-voltage stop policy and
`step_with_battery` recorder adapter. It inhibits new takes before voltage
qualification and uses the existing durable-drain contract before OS poweroff.
It does not replace independent per-cell protection or a kernel halt interface.
See [power design](../../electronics/gs8-gnb3s-v1/README.md).


This independent package preserves `software/gs8-camera` and adds a real,
lazy-loaded Picamera2 adapter for the colour IMX296 and an HDMI colour EVF.
Host tests pass; no Pi, sensor, DNG output, display, or optical latency has been
tested on physical hardware here. Treat this as a commissioning build.

The ISP feeds a 728 × 544 XRGB8888 preview directly to DRM/KMS. That is exactly
half the 1456 × 1088 sensor in each dimension. DRM preserves the whole sensor
aspect ratio within the HDMI canvas; no electronic finder parallax is added.
The default HDMI canvas is 1024 × 768, the native input of the selected EVF-A (and of
EVF-A2 and EVF-B; see [EVF-SELECTION.md](../../electronics/gs8-evf-v1/EVF-SELECTION.md)).
`--display-size 1920 1080` applies only to the external Kinefinity EAGLE fallback. The active CRTC must match the
requested dimensions at progressive 59–61 Hz, or startup fails. The display
controller can still scale/crop internally: verify a grid and colour bars in
the actual eyepiece, using its native input resolution wherever supported.

## Capture and exposure policy

| Recording | Default sensor/ISP rate | Recorded source frames | 90° exposure |
|---|---:|---|---:|
| 24 FPS | 48 FPS requested | every second frame | 10,417 µs |
| 18 FPS | 54 FPS requested | every third frame | 13,889 µs |

These are new sensor exposures, not repeated recording frames. A 60 Hz display
repeats some of the 48/54 source images. The integer ratios preserve uniform
recorded sampling; the sensor clock and microsecond frame-duration quantisation
still cause small rate error, so actual timestamps and measured rate are saved.

`--source-fps 60` lowers the source period for either recording rate, but 24 FPS
then alternates 2/3 sensor periods (33.3/50 ms), and 18 FPS uses 3/4 periods
(50/66.7 ms). This uneven capture cadence is explicit in the manifest. No
interpolation, duplicates or fabricated sensor timestamps hide the difference.

High source FPS cannot coexist with long per-frame cinema exposures on this
single sensor: 180° at 18 FPS is 27,778 µs, and at 24 FPS it is 20,833 µs.
Both are rejected by the default high-rate modes with a provisional 200 µs
sensor timing margin. **The hardware CLI explicitly defaults to 90°.** It
never silently shortens a selected shutter angle. Actual exposure, gain, WB,
frame duration, and source timestamp are checked and recorded for each take.

## Latency and storage ownership

Preview uses upstream Picamera2's newest completed request, DMA buffer scanout,
`queue=False`, four camera buffers, and noise reduction off. There is no video
encoder, network transport, compositor, or Python preview pixel copy.
`queue=False` disables cached still capture; upstream newest-request rendering
is what prevents a FIFO of old preview frames.

The callback only checks metadata and hands off a reference. A worker retains
**at most one** camera request, copies selected RAW pixels, and releases that
request before a separate worker creates an uncompressed DNG. Copied RAW is
bounded to two queued frames, DNG output to four, and the CLI disk writer to
four. Disk or conversion overload explicitly fails the take rather than
retaining the entire sensor pool. Accepted data drains before durable close;
the inherited journal, hashes, commit receipt and storage reservation remain.

Recording sample indices and original sensor frame sequences are separate.
Intentionally unrecorded preview exposures are counted separately from losses.
Any sensor sequence gap or failure to sustain the requested cadence fails the
take. `record_pts_ns` is an explicitly nominal postproduction timeline;
`sensor_timestamp_ns` remains libcamera's measured CLOCK_BOOTTIME timestamp.

Continuous preview survives normal take completion through `release_take()`.
Subsequent takes use the same sensor controls; changing controls requires a new
backend session. Idle preview errors inhibit recording. Shutdown and faults
fully close the preview/camera; no software code asserts the OS_HALTED line.

## Run on a Raspberry Pi 5

Use Raspberry Pi OS with its matched apt versions of `python3-picamera2`,
libcamera, KMS bindings and NumPy. Run on the local text console with KMS access,
the EVF as the only connected display, and no desktop display server owning DRM.
`kmsprint` reports the active HDMI timing. Before starting, apply the EVF-A HDMI
settings in [EVF-SELECTION.md](../../electronics/gs8-evf-v1/EVF-SELECTION.md) section 4
(also [release WIRING.md](../../electronics/gs8-release-v1/WIRING.md) section 8):
`max_framebuffers=2` and `disable_fw_kms_setup=1` in `config.txt`, and
`video=HDMI-A-1:1024x768@60D vc4.force_hotplug=1` in `cmdline.txt`. Section 4 also
gives the custom-EDID fallback, and receipt gate G2 accepts the mode. The software never
sets an HDMI timing. It refuses to start unless the active mode matches
`--display-size` at progressive 59–61 Hz. Pin and record the installed package
versions after commissioning; upstream API inspection alone is not a version
qualification.

From this package directory:

```sh
python3 -m venv --system-site-packages .venv
. .venv/bin/activate
python -m pip install -e .
kmsprint
# Set these to measured white-balance calibration values for the scene:
export GS8_WB_RED=1.5 GS8_WB_BLUE=1.25  # examples only; replace before commissioning
gs8-camera-evf run --output /media/gs8/takes --fps 24 --shutter-angle 90 \
  --wb-gains "$GS8_WB_RED" "$GS8_WB_BLUE" --seconds 10 --takes 3 --pause-seconds 2 \
  --display-size 1024 768
# External Kinefinity EAGLE fallback only (1920x1080); EVF-A uses --display-size 1024 768:
gs8-camera-evf run --output /media/gs8/takes --fps 18 --shutter-angle 90 \
  --wb-gains "$GS8_WB_RED" "$GS8_WB_BLUE" --preview-only --seconds 60 \
  --display-size 1920 1080
gs8-camera-evf inspect --output /media/gs8/takes
```

SIGINT/SIGTERM request a drained stop. A take may remain failed/incomplete if
hardware or storage refuses to drain. The CLI creates scheduled bench takes;
physical selector/trigger GPIO, audio/I2S, film/pixel looks, automatic service
startup and shutdown wiring still require integration/commissioning. Hardware
capture rejects audio, encoded recording and unimplemented looks. The separate
`simulate` command produces labelled descriptors, never camera footage.

The optional `--battery-hwmon PATH` enables an INA260 low-battery drained stop
through the Linux hwmon driver. It needs a kernel `ina2xx` hwmon device named `ina260`,
which the release `config.txt` does not create yet (open item in
[release WIRING.md](../../electronics/gs8-release-v1/WIRING.md) section 10).
Add `--battery-poweroff` to request OS poweroff
after a battery-triggered stop only when recorder/preview/store cleanup succeeds.
Startup requires one second of valid readings at ≥11.1 V; ≤10.5 V for one second,
≤10.2 V immediately, or faulty/stale telemetry latches stop. Thresholds remain
provisional. Normal command completion ends monitoring without halting the Pi.
This is commissioning software, not an independent battery protector or a
completed physical cutoff. See the [GNB 3S power design](../../electronics/gs8-gnb3s-v1/README.md)
for setup boundaries, warnings, waveform qualification and remaining gates.

Uncompressed 16-bit containers for RAW10 are about 3.17 MB/frame before DNG
overhead: about 76 MB/s at 24 FPS or 57 MB/s at 18 FPS. Use storage with measured
sustained write/fsync margin. DNG conversion and Linux scheduling can compete
with preview despite bounded ownership: benchmark on the actual Pi under heat,
power and disk stress. Optical source-to-eyepiece measurements, not callback
timing, must establish a latency claim. See the fork's root EVF design and
latency acceptance procedure.

## Host verification

```sh
python -m unittest discover -s tests -v
python -m gs8_camera_evf simulate --output /tmp/gs8-evf-smoke --fps 24 --frames 48
```

Tests include source cadence, colour-mode validation, exposure conflicts,
HDMI geometry, retained-buffer limits, blocked conversion, queue saturation,
source loss, applied metadata, close retry, idle fault handling, two complete
takes with continuous preview, and final shutdown. Fake DNG bytes are labelled
test data; these tests do not validate a real DNG decoder or display latency.

## Primary sources inspected 2026-09-20

- [Raspberry Pi Global Shutter Camera specifications](https://www.raspberrypi.com/products/raspberry-pi-global-shutter-camera/): colour IMX296, RAW10, up to 1456 × 1088 at60 Hz.
- [Picamera2 camera configuration and event loop source](https://github.com/raspberrypi/picamera2/blob/main/picamera2/picamera2.py): stream controls, queue semantics and newest-request preview selection.
- [Picamera2 request and DNG helper source](https://github.com/raspberrypi/picamera2/blob/main/picamera2/request.py): reference ownership, owning RAW copies, `Helpers.save_dng()`.
- [Picamera2 DRM preview source](https://github.com/raspberrypi/picamera2/blob/main/picamera2/previews/drm_preview.py): DMA scanout, aspect fit, retained display request and atomic commit.
- [libcamera control definitions](https://docs.libcamera.org/master/internal-api/namespacelibcamera_1_1controls.html): applied sensor controls and timestamp clock.
- [KMS Python bindings](https://github.com/tomba/kmsxx/blob/master/py/pykms/pykmsbase.cpp): CRTC active mode and video timing readback.
