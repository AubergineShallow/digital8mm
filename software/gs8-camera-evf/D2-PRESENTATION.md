# D2 EVF status presentation

2026-10-06. **Pure host implementation and rendered previews. Not deployed, optically tested, or hardware-qualified.**

The renderer fills a verified software gap: `D2Status` existed, but the D2 branch had no status pixels.
It does not implement a production display adapter. The existing recorder, controls, capture backend,
GPIO/gauge adapters, readiness policy and shutdown coordinator are unchanged by this module.

## Authority and limits

- [D2 HANDOFF](../../cad/gs8-d2-v1/HANDOFF.md) preserves the physical 18/24 switch and the no-LED design.
- [D2 WIRING section 8](../../electronics/gs8-d2-v1/WIRING.md) specifies a **1024×768** HDMI mode and EVF shutdown status.
- [EVF-A selection](../../electronics/gs8-evf-v1/EVF-SELECTION.md) identifies the selected Hicenda HMX039-V1
  full-RGB 1024×768 panel. Its physical timing, optics, image retention and electrical gates remain open.
- [`EvfPolicy`](gs8_camera_evf/evf.py) requires the full IMX296 **1456:1088 = 91:68** aspect ratio, with
  a default main stream of **728×544**. The 1920×1080 external fallback is not this renderer's target.
- [`D2Status`](gs8_camera_evf/d2_runtime.py) and [D2-INTEGRATION](D2-INTEGRATION.md) define the state and safety meanings.
  No elapsed timer, remaining recording time, current clip identifier, freshness timestamp, measured frame rate,
  shutter/WB values, media-unmount completion or verified OS-halt signal is invented.

There is no FPS menu or new input mapping. Neither essential navigation nor shutdown relies on the encoder push.
The proposed gain-reset behavior and physical push travel remain subject to MP-ENC/G-W9. No audio or dedicated
LED output is added. `REC` is ordinary on-screen text.

## Compact layout

The entire canvas is **1024×768**. Coordinates below are half-open panel-pixel rectangles.

| Region | Coordinates | Content |
|---|---|---|
| Header | x 0–1024, y 0–48 | Phase and measured 1S telemetry; qualification and short action/warning |
| Full-sensor preview | **x 57–967, y 48–728** | **910×680**, exactly 91:68; no status pixels inside |
| Side letterboxes | x 0–57 and 967–1024, y 48–728 | Opaque black |
| Footer | x 0–1024, y 728–768 | Active FPS/gain; `NEXT` FPS/gain only while a change is pending |

The preview uses **78.7% of panel pixels** and **88.5% of panel height**. It shows the complete field of view;
physical image size is reduced, not cropped. Both the 728×544 preview and 1456×1088 full-resolution source use
the same rectangle. The first layout study's 64/88-pixel rails would have left only 819×612 (63.7% of pixels).
The compact 48/40-pixel rails increase the displayed image area by **23.5%** without covering sensor edges.
No permanent crosshair, frame guide, toolbar, menu, clip path or decorative border is painted on the scene.

Routine phase, battery and settings glyphs are 21 pixels high. Secondary qualification/action glyphs are 14
pixels high. Attention-page headings are 28 pixels high and issue labels are 21 pixels high. An original built-in
5×7 raster alphabet guarantees those extents without platform font substitution, font downloads or extra packages.
This is a deterministic host layout choice, **not a measured minimum readable size in the eyepiece**.

Text labels carry meaning independently of color. `REC`, `SAVING`, `LOW CELL`, `INPUT LOST`, `NOT READY` and
`FAULT` remain distinct in grayscale. White, amber and red text have tested numeric contrast against black;
those calculations are not optical contrast, brightness or OLED aging measurements. There is no blinking/animation
that could make an important state disappear between glances.

## What each state means

| Runtime state/condition | Presentation |
|---|---|
| `checking` | `CHECKING`, release/wait cue; unavailable telemetry is explicitly unknown |
| `ready` | `READY`, `PRESS RUN TO RECORD`; a software state only |
| `starting` | `STARTING`, never a premature `REC` claim |
| `recording` | `REC`, active settings, `PRESS RUN TO STOP` |
| `saving` | `SAVING`, active/pending settings, `KEEP POWER CONNECTED` |
| `applying_settings` | `APPLYING`; settings apply between takes |
| Warning above the configured stop threshold | `LOW CELL` remains visible with the full live-view window |
| Low-cell shutdown | Opaque `SHUTTING DOWN` page with `LOW CELL`, even if the warning flag was never set |
| Input failure | `INPUT LOST` and `FAULT`, with shutdown state when reported |
| Gauge read/stale/missing/implausible/gap/clock failure | `BATTERY DATA LOST`; cached numeric gauge values are suppressed |
| Readiness failure | Opaque attention page with every affected fixed category, no scrolling or cycling |
| `shutting_down` | `SHUTTING DOWN`, `KEEP POWER CONNECTED`, `OS HALT IS NOT CONFIRMED` |
| `stopped` / `fault_stopped` | `CAPTURE STOPPED` / `FAULT STOPPED`; still no halt or battery-removal permission |
| Unknown/malformed status | Explicit unknown/invalid state, opaque attention page |

A selection made during recording is labeled `NEXT`, while `ACTIVE` stays attached to the frozen take settings.
While a take is active, the physical FPS contact's 10 ms qualification can temporarily make **both** selected
values `None`. If active settings remain valid and `settings_pending` is explicitly true, the preview remains
visible and the footer reads `NEXT -- FPS  GAIN --` until qualification resolves. It does not show a false
readiness/release instruction or replace the active take values. This narrow exception applies only to
`starting`, `recording` and `saving`; partial/malformed selections, invalid active values, missing pending flags,
real input faults, battery failures and readiness loss still require attention. There is no invented settling
timer: the runtime remains responsible for freshness/fault policy.

The renderer never applies a selection or interprets a button. `ACTIVE` describes the runtime's settings field;
only the phase label declares actual recording. The last-clip path is intentionally absent because it is not a
reliable identifier for the current in-flight take.

Missing values render as `--`, never as zero, full battery or readiness. Known zero SOC remains zero. Voltage is
shown to the reported millivolt rather than rounding across the provisional stop threshold. The renderer does
not impose its own stop voltage, battery hysteresis or SOC policy. D2's actual policy remains in `d2_power.py`.
`D2Status` has no acquisition timestamp; freshness is enforced by the runtime, not reconstructed by this renderer.

Known readiness reasons are grouped as media, storage, USB, heat, throttle, health data and bench checks.
Unknown reasons become `OTHER CHECK`; raw strings stay in `diagnostics`. Up to 16 possible fixed issue categories
fit simultaneously on a dedicated page. Long exceptions, Unicode, paths and control characters never become
arbitrarily sized on-screen text. There is no hidden scrolling area or `+N` omission of critical categories.

Every view retains either `SIMULATION / UNQUALIFIED` or `HARDWARE UNQUALIFIED`. Even an unexpected true
`hardware_qualified` field does not remove that label: it adds `HARDWARE CLAIM UNVERIFIED`, inhibits a contradictory
`READY` title and opens an attention page. This renderer cannot close a physical gate.

## Pure API

`gs8_camera_evf.d2_presentation` has no mandatory dependencies beyond Python's standard library. Importing it does
not import `d2_runtime`, Picamera, GPIO, I2C, Pillow or NumPy, and does not open a device or create a worker.

```python
from gs8_camera_evf.d2_presentation import present_status, present_shutdown, rasterize

presentation = present_status(status, source_size=(728, 544))
assert presentation.canvas_size == (1024, 768)
rgba = rasterize(presentation)
# rgba is immutable, tightly packed RGBA8888: 1024 * 768 * 4 bytes.
# Straight alpha, top-left origin, stride 4096 bytes, no premultiplication.
# presentation.preview_rect says where the whole source must be placed.

# Can be prepared before a no-argument hold_shutdown_screen callback is needed.
shutdown_pixels = rasterize(present_shutdown(simulation_only=True))
```

`D2Presentation` is immutable and exposes labels with exact bounds, a preview rectangle (or `None` for opaque
attention pages), fixed notice codes and diagnostic strings. `validate_layout()` rejects clipping, overlapping
labels, missing required status/attention labels, unsupported glyphs, unsupported canvas sizes and any status label
over the full-sensor viewport.
`rasterize()` returns alpha zero for **every** preview pixel and alpha 255 everywhere else. Attention/shutdown
pages are completely opaque. The function neither reads nor retains camera buffers.

## Required future adapter contract: not a drop-in overlay

**Do not simply call Picamera's overlay method with these pixels over the current backend.**
The existing `PicameraEvfBackend._start_preview()` still places preview at `(0,0,1024,768)`. These reserved rails
would cover its sensor edges. A future commissioned compositor/preview-placement adapter must explicitly consume
the presentation's rectangle and place the **entire** source at `(57,48,910,680)`, with the overlay registered to
the full output canvas. This change is not implemented or qualified here.

The adapter must:

1. Verify the actual native 1024×768 progressive mode, source aspect, orientation and no overscan. Map all four
   full-sensor corners into the returned window without crop/stretch. Confirm its alpha/channel/stride contract.
2. Keep ISP/DMA preview ownership bounded. Do not put this Python rasterizer or a Pillow RGB image copy on every
   camera frame. `show_status(status)` must return promptly: prepare/coalesce presentation changes outside the
   capture callback, use at most one pending newest status and cache unchanged render content. Millivolt updates
   are not permission to block the capture/input loop. Measure the chosen update cadence on the Pi.
3. Feed pixels to the actual display owner using its measured/commissioned interface. Propagate display failures
   through the existing application fault contract; do not silently leave an old `READY` or `REC` image after
   source/scanout failure. A black or failed display is not an OS-halt acknowledgement.
4. Establish **independent retained shutdown-screen ownership before capture teardown**, through the explicit
   `hold_shutdown_screen()` hook. Pre-rendering `present_shutdown()` is only preparation. That function does not
   acquire DRM, make an atomic commit, transfer ownership, keep an image alive or request OS shutdown.
5. Preserve the generic `SHUTTING DOWN` image while the existing coordinator drains capture, closes/syncs/unmounts
   media and, only when authorized/configured, requests poweroff. The current application stops ordinary
   `show_status()` painting once shutdown is latched. Its final stopped status is **not automatically delivered**
   to the ordinary status painter. The richer terminal-state examples here are pure renderer test coverage, not
   a claim that the existing live application already shows them.
6. If cleanup/unmount/poweroff fails or is pending, retain the warning. Do not display a success/checkmark, clear
   the screen to simulate halt, authorize battery removal or retry uncertain system actions merely for UI flow.
   A future independently owned failure view must be explicitly integrated with the coordinator's real outcome.

No production adapter, DRM ownership transfer, shutdown persistence, display watchdog, poweroff command, service
installation, gauge configuration, telemetry-rate change or hardware action is included. The no-argument generic
shutdown page deliberately avoids stale settings/battery values because the callback can run before a new status
snapshot exists. `capture_safely_drained` and `poweroff_requested` do not prove OS halt or physical power-off.

## Reproduce the host evidence

From `software/gs8-camera-evf`:

```sh
PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests -p test_d2_presentation.py -v
PYTHONDONTWRITEBYTECODE=1 python examples/render_d2_presentation.py --output /tmp/d2-evf-previews
```

The renderer and tests require no third-party packages. The optional preview-generation script uses Pillow only
to create the synthetic target, captioned review sheets and PNG/HTML files. It has no network dependency.
It generates 15 scenarios, an explicitly labeled contact sheet, a local gallery, native 1024×768 composited frames,
RGBA overlays and a SHA-256 manifest with the exact input statuses. Every review image has an external host-only
caption; native panel pixels remain separately available. The target's four corner labels make framing visible.
**The scenery is generated test artwork, not camera footage. The gallery is local, not published.**

The test suite covers all phases, 576 phase/FPS/gain combinations, every pixel's transparency classification,
exact aspect ratio, glyph geometry, clipping/overlap rejection, up to 16 simultaneous notices, long/unknown/error
strings, missing/stale/malformed telemetry, persistent qualification labels and conservative shutdown semantics.
A real `D2Runtime`/`SimulationBackend`/`ClipStore` sequence checks record, pending control changes, saving, settings
application and drained stop without changing their behavior. The first single tick of an FPS-switch change
during actual simulated recording and saving is explicitly checked before the contact settles. A real injected
input-reader failure in each of those settling states must still hide preview and show `INPUT LOST` through
drained fault-stop; 48 active-phase/FPS/gain/warning combinations and malformed/fault negatives guard the distinction. A `python -S` subprocess proves rendering imports
and runs without installed site packages or hardware modules.

## Still requires the assembled camera

- Eyepiece legibility at the intended eye position, glasses, diopter extremes and bright/dark surroundings;
  enlarge/rework text only with a correspondingly verified framing/layout change.
- All sensor edges, native timing, orientation, scaling, color/alpha behavior and display disconnect/reconnect.
- Fresh-image cadence, dropped frames, status-update load and optical latency with recording/storage stress.
- Readiness/fault recognition and button-release recovery using the actual controls at G-W9.
- Boot-to-first-status behavior, late/failing shutdown stages and independent image retention through backend close.
- G-W4/G-W8 electrical proof of EVF dark after actual halt and the existing service procedure. A pure image does
  not establish any of those facts or replace the prescribed bench process.

Host evidence narrows software/layout risk. **Hardware qualification remains false.**
