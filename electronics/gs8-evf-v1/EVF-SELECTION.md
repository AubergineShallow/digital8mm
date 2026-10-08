# GS8 EVF selection (final, 25 September 2026)

This file records the EVF selection for the GS8 EVF branch. It replaces the provisional
"Hicenda integrated kit with 15X optics" selection in [RESEARCH.md](RESEARCH.md) and the
earlier [selection.json](selection.json) revision. The selection is a **design and purchase
direction, not a hardware qualification**. No EVF part has been bought, connected or measured.
Every electrical fact that no vendor publishes is closed by the receipt gates G1-G9 below, plus the in-circuit rail gate G4b (added 27 September 2026).

The CAD for this selection is in the release layer: [cad/gs8-release-v1/DESIGN.md](../../cad/gs8-release-v1/DESIGN.md)
(`evf_module.py`). The wiring is in [electronics/gs8-release-v1/WIRING.md](../gs8-release-v1/WIRING.md).
Machine-readable record: [selection.json](selection.json).

Axes are GS8 assembly coordinates: X front to rear (eye at +X), Y left to right, Z up, in mm.

## 1. Decision

| Role | Selection | Status |
|---|---|---|
| **Primary, EVF-A** | Hicenda HMX039-V1 0.39 in 1024x768 full-RGB micro-OLED (flex FM04112-MF1-A) and its HDMI driver board, bought as the Hicenda Tindie kit, option "Display+HDMI Board+Prism". The panel is removed from the kit's resin prism and fitted in a printed GS8 carrier behind a Display Components **0PE039-16X** M29x0.75 glass eyepiece. | Selected. The optics CAD uses published drawings. The electronics depend on gates G1-G8. |
| Second-source electronics, EVF-A2 | Display Components Sony **ECX334C** 0.39 in 1024x768 panel and DC **37.5 x 15 mm** HDMI board, in the same M29 cell. | Order only if the Hicenda electronics fail G2-G5. The tray adapter is not modelled yet. |
| Backup, EVF-B | The same Hicenda/YX HMX039-V1 HDMI kit, unmodified, with its stock resin prism. | Measure-first. No vendor drawing exists, so no carrier is released for it. |
| External fallback | Kinefinity EAGLE HDMI. | External mount only; unchanged from the earlier record. |

**Why EVF-A.** The 0PE039-16X is the only compact eyepiece found with a complete published
mechanical interface: barrel dia. 38.5, M29x0.75 male spigot 4.5 long, flange datum F, display
plane at F - 6.0, f = 16 mm, eye relief 28.1 mm, diopter -6/+4 D. The HMX039 panel outline is
published on two vendor drawings (FM04136-MF1-A and FM04112-MF1-B; 15.6 x 13.6 x 1.93 mm). Other
internal candidates either have no dimensions (the integrated kit, the resin block) or no HDMI
board that fits the hood (SeeYA SY040).

**What is still unknown for every candidate:** which HDMI board revision ships, whether its
power input is isolated from HDMI +5 V, and its EDID and 60 Hz behaviour. Gates G1-G6 close these.

### Corrections carried into this record

1. **Panel placement.** The eyepiece drawing puts the display plane at the flange face - 6.0 mm,
   1.5 mm beyond the spigot end. An earlier placement was 3 mm (about 11.7 D) wrong.
2. **HDMI +5 V is Type D pin 19.** On micro-HDMI (Type D), pin 18 is DDC SDA; pin 18 is +5 V only
   on Type A. Isolating "pin 18" on this cable would cut EDID.
3. **The Hicenda integrated-kit table is a panel/FPCA table only**, not an assembly table
   (RESEARCH.md earlier called it a "published mechanical table").
4. **Flex length.** The 50.4 +-1 mm and 60.4 +-1 mm figures belong to two flex variants:
   FM04112-MF1-A (50.4, the one photographed on kits) and FM04136-MF1-A (60.4, drawings only).
   Gate G8 identifies the shipped one.

## 2. What to order (not ordered)

List prices were re-checked on 25 September 2026. Shipping to the owner's country was not checked.

| # | Supplier | Item | Qty | Unit |
|---|---|---|---|---|
| A1 | Hicenda (Tindie store `hicenda`) - [listing](https://www.tindie.com/products/hicenda/039-inch-oled-microdisplay-resolution-1024x768/) | 0.39 in OLED 1024x768 with HDMI driver + prism, option "Display+HDMI Board+Prism". **Not** the CVBS listing. | 2 (min. 1) | $139.50 |
| A2 | Display Components (Tindie store `oled-modules`) - [listing](https://www.tindie.com/products/oled-modules/optics-for-microdisplays/) | 0PE039-16X, 0.39 in, 16X, M29x0.75 | 1 | $79.00 |
| A3 | Any | Micro-HDMI Type D male to Type D male, shielded thin coax, HDMI 1.4 high speed, **200 mm (+10 / -0)**, jacket **OD 3.0 +-0.1 mm**. Pi end: 90 deg plug. EVF board end: **right-angle plug with the cable leaving its -Y side face** (a rear exit cannot pass the hood-floor opening). Revised 2026-10-01 (decision D5; CAD records `evf_hdmi_cable_length_budget`: seated 189.5 mm, hood-loop stow 26.5 mm, a 250-300 mm cable does not stow; `evf_hdmi_board_plug_passes_hood_floor_opening`). Supersedes the earlier 250-300 mm / OD <= 3.6 mm line. | 1 | ~$15-30 (estimate) |
| A4 | Any distributor | Bourns MF-R050 radial PTC (0.50 A hold, 1.00 A trip) or Littelfuse 60R050XU | 2 | < $1 |
| A5 | Any | onsemi 1N5817 Schottky (an alternative must also have Vf max <= 0.45 V at 1 A; 1N5819 at 0.60 V does not) | 2 | < $1 |
| A6 | Any | JST PH 2-pin pre-crimped leads, 24-26 AWG, PHR-2 / B2B-PH-K; for a Rev II board, a matching 6-pin lead identified on receipt | 1 set | few $ |

The second A1 kit stays intact as the EVF-B backup, bench reference and spare panel/board.
Totals before cable, small parts and shipping: $358.00 recommended (2 x A1 + A2), $218.50 minimum.

Equivalent electronics SKUs if Tindie is out of stock (same HMX039-V1 family): Hicenda Shopify
HMX039V1V1-HDMI ($189); YX Microdisplay HMX039-V1-V1 "EVF Module+HDMI Board" ($189). Always
choose the **HDMI** variant; the CVBS variant is listed at the same price.

**Ask the seller before paying:** (1) HDMI version with a full-RGB 1024x768 panel, not CVBS,
"Tricolor" AV or 800x600; (2) which board ships (Rev I: ITE IT6801FN, about 28.5 x 27 mm; Rev II:
26 x 26 mm with a 6-pin header RX/TX/BRT-/BRT+/GND/EXT +3.5-5 V) and its receiver IC; (3) whether
the board has a separate power input and whether HDMI +5 V (Type D pin 19) is isolated from it, so
that the board draws <= 50 mA from HDMI +5 V when externally powered; (4) supply range and full-white
current; (5) whether it accepts 1024x768@60 VESA DMT without a frame buffer; (6) flex part number and
whether the panel is clipped or bonded into the prism holder; (7) the included cable and the board
connector type.

## 3. Receipt gates (bench, before printing the final carrier)

Record photos, board revision, measurements and the EDID dump with the unit serial.

| Gate | Test | Pass criterion |
|---|---|---|
| G1 Identity | Photograph both board sides, receiver IC, flex marking, connectors | HDMI kit, 61-pin panel, FM041xx flex; board revision recorded |
| G2 HDMI / timing | Pi 5 with the settings in section 4; `edid-decode`, `kmsprint` or `modetest -M vc4 -c` | Stable image at 1024x768, 65.000 MHz, 60.00 Hz DMT; no frame drop in 10 min; full-RGB colour bars; correct black level |
| G3 Latency | Optical latency experiment in [EVF-DESIGN.md](../../EVF-DESIGN.md) with `tools/analyze_evf_latency.py` | Board adds < 1 frame (< 16.7 ms) over a directly connected HDMI monitor |
| G4 Power range | Board alone on a bench supply at 4.25, 4.55 and 4.90 V into its external supply input | Works at all three; steady current at full white <= 0.30 A and <= 1.5 W |
| G4b In-circuit rail envelope | Final PROTO1 (real MF-R050 + 1N5817) and H-EVF harness, DROK set as close to 5.14 V as it adjusts; EXT+ at the board in five states: HDMI unplugged, Pi booting before KMS, full black, full white, 10 min live preview. Record in `electronics/gs8-release-v1/bench-evf-rail.json` | `validate.py` computes worst case = highest reading + (5.14 V - setpoint) + 0.05 V hot-diode allowance <= 4.90 V, and lowest reading - (setpoint - 5.04 V) >= 4.25 V. Fail: replace the PTC + Schottky with a regulated feed |
| G5 HDMI +5 V isolation | (a) unpowered resistance/diode test, receptacle pin 19 to EXT+; (b) Pi on, EVF branch on, HDMI connected; (c) Pi 5 V rail off, EVF branch on, HDMI connected | (b) branch current >= 0.9 x the G4 current, so HDMI +5 V supplies <= ~30 mA; (c) < 0.3 V at Pi header pin 2/4 (no backfeed) |
| G6 Inrush | Scope J5 (EVF power) and the Pi 5 V input at camera power-on | Pi rail dip <= 100 mV; no PTC trip; `vcgencmd get_throttled` = 0x0 |
| G7 Panel release (kit 1 only) | Does the panel (or panel + metal holder) unclip from the resin prism? | Clipped: use the carrier. Bonded: stop; use a bare-panel source or EVF-B |
| G8 Flex | Measure panel edge to stiffener end to finger end; ROM side | FM04112: 50.4 +-1, stiffener 8 +-0.5. FM04136 (60.4) needs a longer-flex carrier variant |
| G9 Thermal (final) | Closed hood, recording, full brightness, 35 C ambient | Panel <= 55 C |

**If G5 fails**, in order: obtain a board revision with an isolated external input; or, with the
owner's explicit approval and photos, remove the single series part between receptacle pin 19 and
the board 5 V net (a deviation from the no-modification rule for bought assemblies); or switch to
EVF-A2 and repeat G1-G6. Do not raise the EVF feed above 5.0 V and do not run the board from HDMI +5 V.

## 4. Pi 5 HDMI settings (Raspberry Pi OS Bookworm/Trixie, KMS)

Legacy `hdmi_group`, `hdmi_mode`, `hdmi_cvt` and `hdmi_force_hotplug` are ignored under KMS.
HDMI0 (the port nearest USB-C) is `HDMI-A-1`.

`/boot/firmware/config.txt` (HDMI lines only):

```ini
dtoverlay=vc4-kms-v3d
max_framebuffers=2
disable_fw_kms_setup=1
```

`/boot/firmware/cmdline.txt` (append to the existing single line):

```text
video=HDMI-A-1:1024x768@60D vc4.force_hotplug=1
```

- `D` forces the connector on without HPD/EDID. Do not add `M` (that selects CVT, 63.5 MHz, not DMT).
- `vc4.force_hotplug` is optional; confirm it exists with `modinfo vc4 | grep force_hotplug`.
- If the panel is mounted inverted, append `,rotate=180` (the HVS cannot rotate 90 deg).
- Target timing, VESA DMT: `Modeline "1024x768_60" 65.000 1024 1048 1184 1344 768 771 777 806 -hsync -vsync`.
  The kit has no scaler (Rev I; Rev II to be confirmed), so the input must be the native size.
- If G2 fails on EDID: install a custom EDID with only this timing at
  `/lib/firmware/edid/gs8-evf-1024x768.bin` and add `drm.edid_firmware=HDMI-A-1:edid/gs8-evf-1024x768.bin`.
- Preview: Pi OS Lite without a compositor; Picamera2 `Preview.DRM` or rpicam-apps DRM preview,
  fullscreen 1024x768; scale 1456x1088 to 1024x765 (3-line letterbox) or crop 1450x1088. Keep
  60 Hz scan-out with repeated frames at the 54/48 fps acquisition rates.

## 5. Power branch (H-EVF)

| Quantity | Value |
|---|---|
| Source | DROK 5.10 V output, own conductor pair at the distribution terminal (not from the Pi harness) |
| Protection and drop | F_EVF Bourns MF-R050 PTC, then D_EVF 1N5817, both on PROTO1 (the single permitted passives board, decision D8) |
| Connector | J5 JST PH 2-pin: pin 1 EVF_5V_BRD, pin 2 GND. Never mate live. |
| Board-terminal voltage | Required 4.25-4.90 V, inside the vendor's 3.5-5.0 V. Minimum from datasheet maxima: 4.342 V (5.06 V - 20 mV transient - 0.30 A x (MF-R050 R1max 0.77 ohm + wiring) - 1N5817 Vf max 0.45 V). **Upper bound not demonstrated:** neither the diode (maximum Vf only) nor the board (G4 caps only the maximum current) guarantees a minimum drop, so on paper EXT+ can reach the 5.14 V source maximum in dim, black or no-signal states. `validate.py` fails the EVF rail until gate G4b is recorded. (The 2026-09-25 figure of 4.283-4.81 V assumed a 100 mA minimum current and a 0.28 V minimum Vf that no datasheet or gate supports; review 2026-09-27.) |
| Acceptance current | <= 0.30 A steady, <= 1.5 W (G4). Replaces the W2-era 0.6 A / 0.62 A figures. |
| Inrush | Unknown; accepted by G6 |
| HDMI +5 V (Type D pin 19) | <= 50 mA drawn by the board when externally powered; no backfeed (G5) |
| Board end | Rev II: 6-pin header lead, GND and EXT+ only, other pins insulated. Rev I: two wires soldered to the traced EXT+/GND pads with a printed strain relief. |

Known limitation: a PTC takes about 0.1-1 s to trip on a hard short, so a dead short in the EVF
could brown out the Pi before it opens. The repo's TPS2553DBVR-1 limiter circuit
([circuit.json](circuit.json)) remains a documented alternative that would need an assembled board.

Wiring detail (harnesses H-EVF, H-HDMI, H-EVF-FPC and routes `route_EVF_power`,
`route_EVF_power_board`) is in [WIRING.md](../gs8-release-v1/WIRING.md).

## 6. How the CAD implements it (release layer)

`cad/gs8-release-v1/evf_module.py` retires the old supplier-unknown reservations and adds a fixed
hood interface plus one per-kit carrier: flange datum F = X181 on axis Y22/Z128.5, an M29 split
U-cradle with a screwed clamp cap (the eyepiece is clamped, never held by a printed thread), a
panel cell with no printed ledge, a sliding controller tray with a ZIF fence at X155.6 that
takes the Rev I and Rev II boards, a 30 mm rear port, an ocular ring, a TPU eyecup and a sun cap.
The glass-side focus stop is the eyepiece spigot end (F - 4.5, a vendor datum). A 2.0 mm shim-swap
set (0.25/0.25/0.5/1.0 mm frames) is always fitted: frames in front of the glass set the focus, and
the rest sit behind the panel, so the pad preload stays constant. Front 0 / 1.0 (nominal) / 2.0 mm
puts the emitter at F - 5.0 / F - 6.0 (vendor MBF) / F - 7.0, which is +/-1.0 mm (about +/-3.9 D)
about nominal. If the rear lens stands proud of the spigot end, the minimum front shim is that
protrusion plus 0.1 mm. Checks in that build are CAD checks only. Known open items from it: flex
slack 1.81 mm nominal and 0.81 mm worst case, and nose clearance 0.79-4.69 mm against a 5 mm
target, so a face-fit mock-up is required. The EVF-A2 tray adapter and the EVF-B carrier are
not modelled.

## 7. Rejected candidates

| Candidate | Reason |
|---|---|
| Hicenda integrated kit HTHMX039-V1-039E-1 (former primary) | All assembly dimensions are photo estimates; no FOV, eye relief or diopter figure; undocumented board with hidden main IC and firmware flash (a frame buffer is possible); radial micro-HDMI plug does not fit the 41 mm hood; most expensive |
| SeeYA/TDO SY040WDG01 0.4 in 1440x1080 | Only HDMI board offered is 65 x 64 x 11.8 mm, which cannot enter the hood; non-standard mode |
| GZOT XGA039 kit | No eyepiece or board dimensions; store paused (B2B only) |
| Sony ECX337A 0.5 in kits | Only optics found are dia. 42 mm, wider than the 41 mm hood interior |
| DisplayModule DMGXO0039XGNA + USB-C board | Board size unknown, no optics, $298 before optics |
| OLiGHTEK SXGA060 | 5:4 panel, enquiry-only, datasheets unavailable, eyepiece pairing unconfirmed |
| 0.4 in FLCoS 1280x960 kits | Field-sequential colour breaks up on pans; inherent frame store; 150:1 contrast |
| V780H-EVF | External, unknown maker, 16:9, draws about 500 mA from HDMI +5 V |
| Kopin CyberEVF | 854x480 colour LCD, MIPI/ASIC, OEM only |
| AliExpress 1005004141499765 "0.39 Optics Tricolor", PVS31 and all CVBS/AV kits | "Tricolor" is an AV palette option; CVBS is 50/60 Hz interlaced analog |
| MicroOLED MDP03C + OEVF109B | Eye relief 16.5 mm; STEP behind a partner login; no HDMI kit |
| BOE 0.39 in 1920x1080 | 16:9; a 4:3 image uses about 6.6 x 5.0 mm; no EVF optic offered |
| Wisecoco, eMagin, Raystar/Winstar, Lakeside, Sony ECX335 0.7 in kits | No individually buyable HDMI + compact optic set, or optics too large |
| Repurposed camera EVFs; SPI/DSI LCD + loupe | Proprietary protocols; visible pixels |
| Kinefinity EAGLE HDMI | Not internal (105 x 54 x 59 mm, 348 g); kept as the external fallback |

Not chosen but noted: Display Components 0PE-15X (same M29 cell, eye relief 39.7 mm, would improve
nose clearance; spigot drawing not checked) and the Display Components bare 0.39 in 1024x768 panel
(a possible source if G7 fails).

## 8. Residual risks

1. Board revision and power path (G1, G5): common to every Hicenda/YX/Youritech 0.39 in HDMI kit.
2. Panel release from the prism (G7): with two kits it cannot block both EVF-A and EVF-B.
3. Timing (G2/G3): receiver-only boards need the exact native mode; the Rev II receiver is unknown.
4. Eye-relief reference surface (+-2 mm) and nose clearance: face-fit mock-up; fallback is a
   5 mm hood extension or the 0PE-15X.
5. 1.25 mm radial clearance around the rotating diopter knurl.
6. Supply chain: Tindie stock, shipping and lead times are not verified.
7. Thermal (G9) unmeasured.

## Sources

- Display Components 0PE039-16X specification sheet and dimensioned drawing (Tindie listing above).
- Hicenda HMX039 panel drawing FM04136-MF1-A ([research/hicenda-panel-drawing.jpg](research/hicenda-panel-drawing.jpg)) and Youritech FM04112-MF1-B drawing; Hicenda 61-pin pinout and 26 x 26 board wiring image.
- Hicenda HMX039V1V1-HDMI and [YX HMX039-V1-V1](https://www.yxmicrodisplay.com/products/0-39-micro-oled-electronic-viewfinder-module) product pages and photos ([research/yx-hmx039-hdmi-kit-photo.png](research/yx-hmx039-hdmi-kit-photo.png)).
- Display Components ECX334C and 37.5 x 15 HDMI board listings (Tindie); Sony ECX334C drawing.
- Raspberry Pi documentation: KMS `video=` mode syntax and legacy config.txt options.
- HDMI Type D pinout (pin 18 DDC SDA, pin 19 +5 V).
- [Bourns MF-R datasheet](https://www.bourns.com/docs/product-datasheets/mf-r.pdf): MF-R050 Rmin 0.41 ohm, R1max 0.77 ohm at 23 C. [onsemi 1N5817 datasheet](https://www.onsemi.com/download/data-sheet/pdf/1n5817-d.pdf): Vf max 0.32 V at 0.1 A and 0.45 V at 1 A; no minimum Vf is specified.
- Internal review notes, 25 September 2026 (EVF market survey, verification and decision reports; not in the repository).
