# GS8 D2 release v1: wiring guide (`electronics/gs8-d2-v1`)

Written 2026-10-04 by the docs owner of the D2 release layer. Geometry, cable ids, lengths and keep-outs come from
`cad/gs8-d2-v1/layout.py` (`CABLES`, `KEEPOUTS`, `COTS`, `STEPS`); the cable table in section 5 is generated from it by
`cad/gs8-d2-v1/make_tables.py`. Component facts come from `concepts/nizo-evf-2026-10-03/research/PALETTE.md` and
`electronics/gs8-evf-v1/EVF-SELECTION.md`. **Nothing here is bought, built or measured.** Every electrical number is a
datasheet, listing or planning figure, and every bench gate in section 9 is open.

**Status (r4, 2026-10-05 evening; r3 text kept).** r4 added the W-10 pigtail fuse, the pack protection requirement
R-PACK-BMS, concrete regulator candidates for option C (s4.8), a defined off-rail G-W13 (e), and the CAD `cable_routes`
check (route continuity, end reach and length; bend radius still a bench item). Done on this machine: CAD geometry and computed checks (`cad/gs8-d2-v1`), these documents,
the generated BOM, the planning calculations of section 4 and a box-arithmetic placement check (s4.8). **Not done:**
procurement (nothing ordered or received), printing or slicing, any measurement, any soldering or harness build, any
power-up, and every bench gate of section 9 (G-W1 to G-W13, EVF-G1 to EVF-G9). No electrical performance, fit or
service life is claimed from CAD or from these calculations.

D2 is much simpler than the release v1 harness: there is no PROTO1 board, no buck converter, no fuse block, no
MCP23017 and no INA260. Power comes from a Geekworm X1203 UPS board under the Pi (pogo pins onto the header tails),
fed from a 1S2P 18650 pack in the grip over one XT30 junction. The four controls use 3 GPIO pins, I2C and the Pi's own
power button.

## 1. Files

| File | What |
|---|---|
| `WIRING.md` | this guide |
| `make_bom.py` | writes `BOM.md` and `bom.csv` from `layout.py` + `outputs/bom-release-2026-09-25/prices.json` |
| `BOM.md`, `bom.csv` | purchased lines, printed parts, fasteners, consumables, tools (generated) |
| `../../cad/gs8-d2-v1/make_tables.py` | refreshes the generated blocks in this file (header, cables, plug order), PRINT-GUIDE.md, ASSEMBLY.md and DESIGN.md, and writes the 3 files below |
| `harness-schedule.csv` | every cable: class, both ends, length, plug steps, keep-out chain, routing note (generated) |
| `pi5-header.csv` | the Pi 5 J8 pins D2 uses (generated) |
| `wiring-d2.svg` | block diagram of the harness (generated) |

## 2. Block diagram

```
 1S2P 18650 pack (BMS)            GRIP                                   BODY
 [cell][cell]--BMS--pack lead 18 AWG--XT30 M | XT30 F--[15 A fuse]--pigtail 18 AWG 180 mm--+
                                                                               | solder, 2 joints
                                                         Geekworm X1203 battery pads (XH socket left empty)
                                                         X1203 boost 5.1 V 5 A  (fuel gauge I2C 0x36)
                                                               | pogo pins onto the header tails (5 V, GND, SDA/SCL, ...)
   Pi 5 power button <-- printed plunger                 Raspberry Pi 5 (EEPROM PSU_MAX_CURRENT=5000)
                                                               |-- CAM/DISP 1 --FPC 22-15 200 mm--> GS camera
                                                               |-- HDMI0 --micro-HDMI 200 mm (90 deg)--> EVF board --flex--> HMX039 OLED
                                                               |-- USB 2 upper --USB-A 5 V lead + 1N5817--> EVF board EXT+
                                                               |      (r3 candidate C: a 4.55 V LDO in place of the diode, s4.8)
                                                               |-- USB 3 lower <== SanDisk SDCZ880 stick (rear scoop)
                                                               |-- FAN <-- Active Cooler lead
                                                               |-- pins 1/3/5/6 <--QT 150 mm-- Adafruit 5880 encoder (0x37)
                                                               |-- pins 33/34 <--Dupont-- 18/24 rotary
                                                               '-- pins 37/39 <--pre-wired lead-- run button (grip)
```

## 3. Decisions made in this layer

| # | Decision | Why |
|---|---|---|
| W-1 | The pigtail is **soldered to the X1203 battery pads**; the board's XH2.54 battery socket stays empty. | An XH2.54 contact is a ~3 A class part. Near cut-off the pack delivers about 8.5 A (section 4). The pad position on the board is open (layout `COTS['x1203']` "pads: position open (Q2)"). |
| W-2 | **18 AWG silicone** for the pigtail and the pack lead; **XT30U** at the grip junction. | 8.5 A planning peak; XT30 is a 15 A continuous class connector. The voltage drop is in section 4. |
| W-3 | **A 1N5817 Schottky in series with the + conductor of the EVF 5 V lead.** | The EVF board needs 4.25-4.90 V at its terminals (EVF-SELECTION s5, vendor range 3.5-5.0 V). A Pi USB port sits at about 5.0-5.1 V. 0.35-0.45 V of diode drop at 0.3 A gives about 4.6-4.7 V. The diode also blocks backfeed from the board into the Pi's USB rail. Confirmed only by bench gate G-W6. **r3:** a diode has no guaranteed minimum drop, so this feed cannot be shown to stay <= 4.90 V on paper and G-W6 is expected to fail; the recommended candidate (s4.8, option C, user decision) replaces the diode by a 4.55 V LDO. |
| W-4 | **The EVF lead has a JST PH 2-pin wire-to-wire junction at the board end.** | The board slides into its slot at step 6 after the lead is plugged into the Pi at step 4. A Rev I board gets a 2-wire PH pigtail soldered to its traced EXT+/GND pads (EVF-SELECTION s5). Never mate it live. |
| W-5 | **The run button is active low on GPIO26** with the internal pull-up; **18/24 is GPIO13**, low = 24 fps, high (open) = 18 fps. | 0 parts; a lead that falls off reads as 18 fps, the safe default. |
| W-6 | **The power button is the Pi 5's own button**, pressed by the printed plunger. logind ignores it; a daemon shuts down only after a **2 s hold**. | A brush of the left hand cannot stop a take (concept E-F2). |
| W-7 | **The pack is charged out of the body** on a 1S Li-ion charger with an XT30 lead. | The X1203's own USB-C input is inside the closed body under the Pi. In-body charging is not provided in D2. |
| W-8 | **No added I2C pull-ups, no level shifting.** | The Pi 5 has 1.8 k pull-ups on GPIO2/3 and the 5880 runs from 3V3 (pin 1). The X1203 gauge shares the bus through the pogo pins; its bus level and any on-board pull-ups are checked at G-W2. |
| W-9 | **Operating restrictions R-P1 to R-P8 (r2)**: 2 USB loads only, no overclock, `arm_freq=1800` if G-W12 allows, radios off, nothing on Ethernet/HDMI1/PCIe, default fan curve, no extra header loads, software low-cell shutdown. | They are intended to reduce the 5.1 V load. With them the load is **estimated** at 17.7-22.1 W (r2 fixer: S3 board 11-12.5 W [est] + HDMI +5 V 0.26 W), within 0.8-5.2 W of the G-W12 P1 limit (22.9 W). **r3: that estimate is not a demonstrated supply margin**: nothing is measured, the restrictions are not shown to hold the load anywhere, and the 27 W planning peak stays above the X1203's 25.5 W and is not served (section 4.1-4.4). G-W12 stays open until measured. |
| W-10 | **r4: a 15 A inline fuse (Littelfuse 0251015.MXL, PICO II, very fast) in the + conductor of the pigtail, within about 25 mm of the XT30 female**, sleeved in adhesive 3:1 heat-shrink and lying along X under the XT30 pair (in `ko_xt30`; modelled in the `xt30_pair` proxy, so the pack-insertion sweep and the interference checks see it). | Before r4 the only protection between 2 high-drain cells and the 18 AWG pigtail was the pack BMS, which was not even specified; a BMS whose MOSFETs fail shorted leaves about 120-200 A [est] into the pigtail. The fuse is a second, independent layer for the pigtail and the X1203 input (not for the 60 mm pack lead and the XT30, which stay on the BMS). Sizing (251 datasheet rev VL: 25 % standard derating plus the temperature curve): 15 A x 0.75 x 0.985 = 11.1 A allowed at 40 C, so 8.6 A is 78 %; the 12 A part keeps only 1-3 % and is rejected. Cold 4.46 mohm: about 0.04 V and 0.33-0.35 W at 8.6 A. Melting I2t 68.8 A2s against an estimated <= 0.35 A2s plug-in surge (X1203 input capacitance unpublished; 100-1000 uF bracket). Interrupting 300 A at 32 VDC against an estimated 120-200 A fault. +1 part, +2 solder joints; confirmed only by G-W5 (drop, temperature) and G-W1 (plug-in). |

## 4. Power path

| Segment | Part | Rating / planning figure | Source |
|---|---|---|---|
| Cells | 2 x 18650 in parallel (1S2P), high-drain class (>= 10 A continuous per cell, e.g. Molicel P28A or Samsung 35E class) | 4.2 V full, 3.6 V nominal, 3.0 V cut-off; 2 x 3.5 Ah x 3.6 V = 25.2 Wh (35E class) | PALETTE s5a |
| BMS | in the pack | must pass >= 10 A continuous; UVP 2.5-3.0 V | estimate |
| Pack lead | 18 AWG silicone, 60 mm, XT30U male | | layout `CABLES['pack_lead']` |
| Junction | XT30U pair in the grip (male on the pack, female on the pigtail) | 15 A continuous class | listing class |
| Fuse (r4, W-10) | Littelfuse 0251015.MXL in the pigtail + conductor, about 20-25 mm from the XT30 female | 15 A very fast; 11.1 A allowed at 40 C after derating; 4.46 mohm cold; I2t 68.8 A2s; 300 A at 32 VDC | 251 datasheet rev VL 09/26/24 |
| Pigtail | 18 AWG silicone, 180 mm, XT30U female, soldered to the X1203 battery pads | | layout `CABLES['pigtail']` |
| UPS | Geekworm X1203: 1S input, boost to 5.1 V, 5 A max out | 5.1 V +-5 %, 5 A | PALETTE s5a (listing) |
| Pi feed | pogo pins onto the 5 V / GND header tails | no USB-PD; hence `PSU_MAX_CURRENT=5000` | PALETTE s5 |
| USB budget | stick (USB 3, lower port) + EVF lead (USB 2, upper port) | 1.6 A total with a 5 A supply declared | Pi 5 whitepaper RP-009856 via PALETTE |

### 4.1 Planning peak against the X1203 ceiling (audit finding 4, r2)

**Planning load** (PALETTE s0/s5, not measured): 18 W record, **27 W peak** on the 5.1 V side. The X1203 is rated
5.1 V x 5 A = **25.5 W**. 27 W is 5.29 A at 5.1 V: **1.5 W (6 %) above the rating.** If the camera really drew 27 W,
the X1203 would not serve it: it would current-limit and the rail would sag (Pi undervoltage, USB resets, a brownout).
Calling the output "capped" does not make a 27 W demand pass. The 27 W figure stays as the inherited planning peak (the
30.5 W EVF-branch allowance of `electronics/gs8-gnb3s-v1/power-budget.json`, minus the dropped microphone, expander,
INA260 and latch). It is an allowance, not an itemised load.

**The 27 W planning peak stays in force against the 25.5 W ceiling.** The estimated envelope of 4.2-4.4 below, with the
operating restrictions of 4.3, is a planning estimate of what D2 may draw; **it is not a demonstrated supply margin**
(r3, audit 2026-10-05 finding 4) and it does not replace the 27 W figure. Gate G-W12 (section 9) stays open until it is
measured on the real stack and loads. If G-W12 fails, the power arrangement of 4.5 (another design, not a verified
drop-in) replaces the X1203.

### 4.2 Workload states and estimated loads at 5.1 V

Sources: [pub] = published third-party bench figures for a bare Pi 5, read 2026-10-05 (r2) from search summaries,
not re-measured: Jeff Geerling 2024, "New 2GB Pi 5 has 33 % smaller die"
(https://www.jeffgeerling.com/blog/2024/new-2gb-pi-5-has-33-smaller-die-30-idle-power-savings/): idle 3.2-3.3 W and
`stress-ng` all cores 9.8 W (4/8 GB); raspberry.tips 2026 "Raspberry Pi Power Consumption"
(https://raspberry.tips/en/faq/raspberry-pi-power-consumption-update-2026-all-models-compared): Active Cooler fan
about 0.5 W, "CPU + USB SSD + 4K video" about 16 W. These are other people's
units, not this one. [rec] = repo record. [spec] = interface specification. [est] = my estimate, with its basis.

| Load | S0 idle | S1 live view | S2 record | S3 write burst | S4 startup | Basis |
|---|---|---|---|---|---|---|
| Pi 5 board (SoC, RAM, RP1, PMIC) | 3.3 | 4.5 | 6.0 | 12.5 | 7.0 | idle [pub]; S1, S2, S4 [est]: ISP + KMS for S1, 47.5-76 MB/s RAW copy + filesystem for S2, all cores during boot for S4. **S3 (r2 fixer): `stress-ng` all cores alone is 9.8 W [pub]; S3 adds the ISP/KMS/RAW pipeline on top, +1.2-2.7 W [est: the S1/S2 board figures minus idle], so 11.0-12.5 W; 12.5 is used.** (r2 R4 had 8.0, below the published CPU-only figure.) The raspberry.tips "CPU + USB SSD + 4K video" 16 W total implies a board near 11-13 W, consistent |
| HDMI +5 V (pin 19 to the EVF board) | 0.26 | 0.26 | 0.26 | 0.26 | 0.26 | the G-W7 limit, 50 mA x 5.1 V [rec: EVF-SELECTION G5 expects <= about 30 mA]; r2 fixer: was in no table |
| GS camera (IMX296, from the Pi 3V3) | 0.05 | 0.4 | 0.4 | 0.4 | 0.2 | [est] small sensor module, not published |
| Active Cooler fan | 0.2 | 0.3 | 0.5 | 0.5 | 0.5 | full speed about 0.5 W [pub]; the curve sets the rest [est] |
| EVF board + panel (USB 2 port, through the 1N5817) | 0.8 | 1.3 | 1.3 | 1.55 | 1.55 | <= 0.30 A at the board (EVF-G4 [rec]) = 1.55 W at 5.1 V; menu/live split [est] |
| SDCZ880 stick (USB 3 port) | 0.3 | 0.3 | 2.5 | 4.6 | 2.5 | 4.6 W = the USB 3 device maximum of 900 mA [spec]; idle and sustained write [est] |
| Encoder, X1203 gauge (header 3V3) | 0.1 | 0.1 | 0.1 | 0.1 | 0.1 | [est] seesaw MCU about 20 mA |
| **Total (W)** | **5.0** | **7.2** | **11.1** | **19.9** | **12.1** | sum (r2 fixer; R4 had 4.8 / 6.9 / 10.8 / 15.2 / 11.9) |
| **Current at 5.1 V (A)** | 0.98 | 1.41 | 2.17 | 3.90 | 2.37 | P / 5.1 |

State definitions (G-W12 uses the same ones):
- **S0 idle**: booted to the camera service, EVF on a static menu, sensor not streaming, stick mounted, no writes.
- **S1 live view**: sensor streaming 1456 x 1088 at 24 fps to the EVF (1024 x 768), no writes.
- **S2 record**: S1 + RAW 24 fps written to the stick (10-bit packed 47.5 MB/s; also the 16-bit container 76 MB/s),
  encoder polled, fan on its curve, steady temperature (10 min).
- **S3 write burst**: S2 on a stick filled to >= 50 % and written past its cache, plus 60 s of `stress-ng --cpu 4`
  (the runaway-software case) and the fan forced to full speed.
- **S4 startup**: from pack connection to recording-ready: X1203 start, boot, stick enumeration, camera probe, EVF
  hotplug. The first 30 s.

The S2 estimate (11.1 W) is below the 18 W planning record figure. PALETTE s5 already expected 10-15 W. The runtimes
and cell currents below keep the 18 W planning figure until G-W12 measures S2.

### 4.3 Operating restrictions (part of the D2 configuration, section 8)

| # | Restriction | Expected effect |
|---|---|---|
| R-P1 | **USB budget**: exactly 2 USB loads: the stick (lower USB 3) and the EVF lead (upper USB 2). The other 2 ports stay empty (they are inside the closed body). `PSU_MAX_CURRENT=5000` gives the Pi's 1.6 A total USB limit. Never add `usb_max_current_enable` tricks or a USB hub | USB side <= 1.6 A x 5.1 V = **8.2 W, the Pi's own USB current limit** (Pi 5 whitepaper RP-009856 via PALETTE s5; its trip behaviour is not measured here); <= 6.15 W by the 2 device maxima (stick 4.6 + EVF 1.55) |
| R-P2 | **No overclock**: no `over_voltage`, no `arm_freq` above 2400, no `force_turbo`; default `ondemand` governor | keeps the board inside the published 9.8 W all-core class |
| R-P3 | **CPU cap `arm_freq=1800`** (25 % below the 2.4 GHz default), kept only if G-W12 shows 0 dropped frames in S2 and S3 at 24 fps | CPU part of the board maximum about 9.8 -> 7.5 W [est: dynamic CPU power scales with f x V^2; idle unchanged], so the S3 board 12.5 -> 10.2 W [est]. **Recommended (r2 fixer)**: without it the estimated worst case (22.1 W, 4.4) is only 0.8 W under the G-W12 P1 limit; with it 3.1 W. Kept only if G-W12 shows 0 dropped frames |
| R-P4 | **Radios off in the camera image**: `dtoverlay=disable-wifi`, `dtoverlay=disable-bt`. Footage leaves on the stick. A bench/maintenance image may enable Wi-Fi, never while recording | removes a 0.3-1 W [est] transmit load that the table does not carry |
| R-P5 | **Nothing on Ethernet, HDMI1 or PCIe**; `dtparam=pciex1` stays off; no M.2 HAT (it also clashes with the cooler) | removes 1-2 W [pub, NVMe class] of possible additions |
| R-P6 | **Fan curve: firmware default, not capped** | 0 W change. Its 0.5 W maximum is already in the table; a capped fan would trade power for throttling (G-W11) |
| R-P7 | **No other loads on header 5 V** (pins 2/4 are the feed); 3V3 carries only the encoder | keeps the header load at the table's 0.1 W |
| R-P8 | **Software low-cell shutdown** at 3.3 V under load (gauge 0x36; G-W5 sets the value) | limits the battery current at end of discharge (4.7) |

### 4.4 Estimated envelope against the ceiling (r2 fixer: an estimate, not a bound)

| Case | Pi board | Camera | Fan | USB (stick + EVF) | Header 3V3 | HDMI +5 V | Total | vs 25.5 W | to P1 (22.9 W) |
|---|---|---|---|---|---|---|---|---|---|
| Expected burst (S3 estimate, no CPU cap, USB at the 2 device maxima) | 12.5 | 0.4 | 0.5 | 6.15 | 0.1 | 0.26 | 19.9 W (3.90 A) | 78 % | 3.0 W |
| R-P1..R-P8 with the CPU cap, USB at the 2 device maxima | 10.2 | 0.5 | 0.5 | 6.15 | 0.1 | 0.26 | 17.7 W (3.47 A) | 69 % | 5.2 W |
| CPU cap, USB at the Pi's hardware limit (1.6 A) | 10.2 | 0.5 | 0.5 | 8.2 | 0.1 | 0.26 | 19.8 W (3.88 A) | 78 % | 3.1 W |
| **No** CPU cap, USB at the hardware limit | 11.0-12.5 | 0.5 | 0.5 | 8.2 | 0.1 | 0.26 | **20.6-22.1 W (4.03-4.33 A)** | 81-87 % | **0.8-2.3 W** |
| Planning peak (kept) | | | | | | | **27 W (5.29 A)** | **106 %: not served** | |

On these estimates (none measured; **not a demonstrated margin**) the envelope would sit below the X1203 rating
(25.5 W), but **not by much**: without the CPU cap and
with the USB side at its hardware limit, the estimated worst case is 0.8-2.3 W under the G-W12 P1 limit (22.9 W, 100 ms
peak). r2 R4's "at least 6.4 W (25 %) in hand" used an S3 board figure (8.0 W) below the published CPU-only maximum and
had no HDMI +5 V row; it is withdrawn. The envelope rests on figures that are not D2 measurements: the published
9.8 W CPU figure, an estimated pipeline increment and the Pi's own USB current limit. G-W12 measures the real
envelope. The X1203 may also derate at a low cell voltage (a boost draws its
highest input current there); G-W12 therefore runs every state at 3.30 V input.

### 4.5 Fallback arrangement with headroom (option b; not applied)

Use it only if G-W12 fails P1 or P2 (load or rail) at any input voltage, or P4 (X1203 temperature) at the measured load.

| Candidate | Rating | D2 geometry and parts impact | Verdict |
|---|---|---|---|
| Geekworm X1206 V2.0 (PALETTE 5a) | 5.1 V 6 A (30.6 W) | 108 x 85 board with 4 x 21700: wider than the tub (inner width 65), so a new body | rejected for D2 |
| Waveshare UPS HAT (E) (PALETTE 5a) | 5 V 6 A | 4 x 21700 in series do not fit the grip bay (38 x 20 x 72, 2 x 18650) | rejected for D2 |
| **2S1P pack of the same 2 cells + 5 V >= 7 A buck on the header feed, replacing the X1203** | >= 35 W | **Pack**: same cells and the same bay envelope (`COTS['pack']` box unchanged), 2S BMS + balance lead, a 2S charger. **Buck**: module class <= 40 x 40 x 10 [est] in the X1203 slot (z 6.0-16.0 under the Pi); the release-v1 DROK 090483 (60 x 52 x 20, 8 A) does not fit that slot and would lift the Pi stack about 10 mm into the FPC/HDMI routes (z 30-44). **Lost**: the X1203 fuel gauge (add a 1-cell-class I2C monitor, +1 board), its start/stop logic. **Added**: an inline fuse, + about 4 solder joints; `COTS['x1203']`, `X1203_KIT`, `PI['x1203_z']` and the pigtail route are re-derived. **r2 fixer:** the `pi_keeper` fingers bear 0.1 over the X1203 top edge, so with the X1203 removed they hold nothing: the keeper fingers, the s_k1/s_k2 bosses and the Pi standoff support (what then carries the Pi standoffs on the floor bosses) are re-derived too (keeper reprint; G-KEEP-1 re-run) | named fallback |

### 4.6 Recommendation (option c)

Keep the X1203 and adopt R-P1 to R-P8 now (configuration only; no parts, no geometry). Keep the 27 W planning peak in
this document (it exceeds the 25.5 W rating; the 17.7-22.1 W estimate does not show that the X1203 suffices), and keep the 18 AWG / XT30 path sized for the full 25.5 W (8.6 A at 3.3 V). G-W12 must pass before
any powered full-build claim. If it fails, the 2S1P + buck arrangement of 4.5 is the next design, with the geometry
work listed there.

### 4.7 Battery current

**Battery current** = P_out / (V_cell x efficiency). With efficiency 0.90 (estimate):

| State | P_out | V_cell | Battery current |
|---|---|---|---|
| S2 record, estimate | 11.1 W | 3.3 V | 3.7 A |
| Record, full pack (planning) | 18 W | 3.9 V | 5.1 A |
| Record, near cut-off (planning) | 18 W | 3.3 V | 6.1 A |
| Envelope without the CPU cap, near cut-off (estimate) | 22.1 W | 3.3 V | 7.4 A (3.7 A per cell) |
| X1203 limit, near cut-off (path sizing) | 25.5 W | 3.3 V | **8.6 A** (about 4.3 A per cell) |

**Drop in the 18 AWG path at 8.6 A** (21 mohm/m copper, 2 x 0.24 m of conductor = 10 mohm; XT30 pair about 1 mohm
estimate; 4 solder joints negligible): about 0.095 V and 0.8 W; **r4: plus the fuse, 4.46 mohm cold, about 0.04 V and
0.33-0.35 W: about 0.135 V in total, 15 mV inside the G-W5 limit of 0.15 V [est]**. This pushes the X1203 toward its
own undervoltage cut-off about 0.14 V early under peak load. Bench gate G-W5 measures it.

**Pack protection requirement R-PACK-BMS (r4; the pack order must state it in numbers, not a listing headline):**
(1) continuous discharge >= 10 A, no trip at 8.6 A continuous at 25-60 C; (2) discharge over-current trip 12-25 A
with a 5-50 ms delay; (3) short-circuit trip <= 100 A within <= 1 ms, yet no trip on the X1203 plug-in surge (about
170 A peak for under 0.1 ms [est]); (4) UVP 2.5-3.0 V, OVP 4.25-4.30 V, recovery behaviour stated; (5) evidence = the
pack builder's written spec or the protection IC, MOSFET and sense-resistor part numbers. The BMS is one layer; the
W-10 fuse is the second for the pigtail. G-W1 checks (1)-(5) on receipt.

**Runtime** (PALETTE s5a): 25.2 Wh x 0.85 conversion x 0.90 usable = 19.3 Wh, about 64 min at 18 W (55 min at 21 W;
about 104 min at the 11.1 W S2 estimate, unmeasured).

### 4.8 EVF feed regulator: resolved requirement (r3; a candidate, not selected, not bought, not verified)

**Why.** The accepted window at the EVF board's EXT+/GND terminals is **4.25-4.90 V** (EVF-SELECTION s5, gates EVF-G4
and EVF-G4b; W-3; G-W6). The diode feed of W-3 has no guaranteed minimum drop (EVF-SELECTION s5: neither the diode nor
the board guarantees one), so in dim, black or no-signal states the terminals can sit near the 5.355 V source maximum;
G-W6 passes only with a total drop >= 0.505 V. r2 carried a generic "5 V regulator module" as the G-W6 fail path.
**That wording is withdrawn (r3):** a 5.0 V regulator in regulation delivers 5.0 V +- its tolerance (4.90-5.10 V at
+-2 %), at or above the 4.90 V maximum, and the common AMS1117-class "5 V module" needs about 1 V of headroom
[class figure, to confirm] that a 4.7-5.36 V input does not have.

**Input at the regulator** (planning worst cases at 0.30 A, the EVF-G4 maximum):

| Term | Min case (V) | Max case (V) | Basis |
|---|---|---|---|
| X1203 output, header pin 2 | 4.845 | 5.355 | listing 5.1 V +-5 %; G-W12 P2 holds the minimum including S4 start-up transients |
| Pi 5 V rail to the upper USB 2 VBUS (power switch, traces) | -0.10 | 0 | [est, to confirm; G-W6 logs pin 2 and VBUS] |
| USB-A contacts + about 60 mm of 26 AWG pair to the regulator (about 0.08 ohm loop) | -0.03 | 0 | [est] |
| **At the regulator input** | **4.715** | **5.355** | sum |
| Regulator output to the board terminals (about 30 mm pair + PH junction, about 0.05 ohm loop) | -0.015 | 0 | [est] |

**Requirement R-EVF-REG** (load 0-0.30 A, junction up to 110 C):

| # | Item | Requirement | Margin / reason |
|---|---|---|---|
| 1 | Setpoint | **4.55 V nominal** (the EVF-G4 middle test point) | window centre 4.575 V |
| 2 | Total output band in regulation: initial + line (4.715-5.355 V) + load (0-0.30 A) + temperature | inside **4.39-4.71 V** (+-3.5 %: a planning split of +-2 % setting accuracy and <= 1.5 % for line, load and temperature [to confirm per device]) | at the terminals 4.375-4.71 V: **0.125 V above 4.25, 0.19 V below 4.90** |
| 3 | Dropout at 0.30 A, hot | **<= 0.30 V** (maximum, not typical) | headroom at minimum input is only 4.715 - 4.55 = 0.165 V, so the part may run in dropout; then the terminals see 4.715 - 0.30 - 0.015 = **4.40 V**, 0.15 V above 4.25 |
| 4 | Start-up | current limit >= 0.5 A with no fold-back below 0.30 A; soft start; stable with the board's unknown input capacitance at the end of about 30 mm of lead; minimum input during S4 as row "at the regulator input" | the panel inrush is not published; G-W13 (c), G-W6 boot state |
| 5 | Input rating | operating Vin >= 5.5 V | 5.355 V source maximum plus USB transients |
| 6 | Dissipation | (5.355 - 4.39) x 0.30 = **0.29 W maximum**; about 0.17 W at 5.1 V in, 4.55 V out | |
| 7 | Temperature | installed thermal resistance <= 150 C/W (SOT-89 / SOT-223 class on a small carrier with copper; **not** a bare SOT-23 dead-bugged in heat-shrink, about 300 C/W [est]) -> rise <= 44 C; with 55 C internal air near the right-rear corner [est; G-W11 measures] the junction stays <= 99 C, about 26 C under a 125 C class limit | thermocouple in G-W13 (f) and G-W11 |
| 8 | Backfeed | the regulator **replaces** the 1N5817 (diode deleted: see the comparison). A sustained reverse current into the Pi USB VBUS could come only from HDMI pin 19 through the board: G-W7 (EVF-G5) bounds that and is re-run at the 4.55 V feed (a lower EXT+ makes an on-board pin-19 path more attractive). The board's capacitance discharging at power-down flows back through a PMOS LDO's body diode unless the device blocks reverse current [to confirm per device] | G-W13 (e), G-W7 (c) |
| 9 | Ripple and transients | <= **50 mV p-p** at the terminals (20 MHz bandwidth) in every G-W6 state; every instantaneous value, ripple and load steps included, inside 4.30-4.85 V | project criterion: the vendor publishes none |
| 10 | Envelope and place | carrier + sleeve <= **16 x 7.5 x 4.5 mm** [est], inline in the vertical run `ko_5v_up` (x -131..-125, y -32..-24, z 27.2..70), at z 40..56 | box check below |

**The diode cannot stay in front of the regulator:** at minimum input the terminals would see 4.715 - 0.45 (1N5817
Vf maximum as used in EVF-SELECTION s5) - 0.30 (dropout) - 0.015 = **3.95 V < 4.25 V: fail.** A diode after the regulator re-introduces the unguaranteed
0.1-0.45 V Vf spread that the regulator is there to remove: rejected.

**Placement (computed, box arithmetic only; not a CAD run).** `cad/gs8-d2-v1/out/_trial-r3-elec/reg_envelope.py`
(output `reg_envelope.json`, run against layout.py sha256 3569785b...; layout.py has since changed only by the r3
checks registry block, `ko_5v_up` (-131..-125, -32..-24, 27.2..70) and the COTS boxes are unchanged, and the r3
release `checks.json` ko_5v_up keep-out rows pass): the estimated 16 x 7.5 x 4.5 [est] envelope at x -130.25..-125.75,
y -31.75..-24.25, z 40..56 lies inside `ko_5v_up`, overlaps no other keep-out and no `COTS` box, and has no COTS box
within 10 mm (at z 30..46 the stick box is 8.3 mm away). The r2 build's `checks.json` keep-out rows give 0.0 mm3 of
tub, hood and panel inside `ko_5v_up` (computed pass); the insertion sweeps see that keep-out (not re-run in r3).
Second choice: `ko_5v_end` (6.5 x 25.5 x 6, shared with the PH junction). Not `ko_usb_evf` (USB-A plug and bend).

**Comparison**

| Option | Parts in the EVF lead | Bench solder joints in the lead | 4.90 V bound met | Gates |
|---|---|---|---|---|
| A. Diode feed (r2 baseline, W-3) | 1 (1N5817) | 3 (diode splice 2, PH plug 1) | not by design; only if G-W6 shows >= 0.505 V drop (not expected) | G-W6 |
| B. Regulator as the G-W6 fail branch | A first; on the expected fail the diode is **replaced** by C (it cannot be added after the diode: headroom above) | 3, then the lead is rebuilt as C | after the rebuild | G-W6 twice, G-W13 |
| **C. Regulator as the primary feed, diode deleted (recommended candidate)** | r4: with the TLV75801P primary candidate 6 on one carrier (LDO, 2 divider resistors, input MLCC, output MLCC, carrier PCB), net **+5** against A; with the fixed XC6220B45 alternative 4, net +3. No pre-assembled 4.5 V board was found | about 18 with the TLV75801P (carrier: LDO 5 + 2 resistors x 2 + 2 MLCC x 2 = 13 SMD; lead: + in, + out, GND in, GND out, PH 1 = 5), net **+15**; about 14 with the XC6220 (net +11) | a device requirement (row 2), **not yet shown**: no device is selected; a selected part's datasheet must meet it, then G-W13 and G-W6 show it on the bench (r4, audit 2026-10-05-r3) | G-W13, G-W6 (regulated run), G-W7 re-run |
| D. Another source | header 5 V tap: the same 4.845-5.355 V, loses the USB port's current limit (a fuse, +1 part) and crowds pin 4 next to the pogo feed; a buck-boost from the 3.0-4.2 V pack: a second converter in the closed body | | | rejected |

**Recommendation (a candidate; the user decides):** C. It is the only option whose 4.90 V upper bound becomes a stated
device requirement (R-EVF-REG row 2) that a selected part can be shown to meet, on its datasheet and then at G-W13,
instead of being hoped for at G-W6 (r4: until a device is selected and G-W13 passes, the bound is a requirement, not a
result); B ends in C anyway on the expected G-W6 fail, after a second lead build and a
second bench run. Cost: +5 parts and about +15 joints in the EVF lead with the TLV75801P (+3 / +11 with the fixed XC6220), no geometry change (its estimated
16 x 7.5 x 4.5 envelope lies inside `ko_5v_up` by box arithmetic; carrier not measured).
**Candidate devices (r4, desk research 2026-10-05 from the datasheets; nothing bought or measured):**

| | **Primary: TI TLV75801P** (adjustable, 500 mA) | Fixed alternative: Torex XC6220B45BPR-G (4.55 V, 1 A) |
|---|---|---|
| Order code | TLV75801PDBVJ (SOT-23-5, hand-solderable; DigiKey 5,567 in stock, USD 0.33) or TLV75801PDRVR (WSON-6 2 x 2, reflow; 54,465 in stock) | XC6220B45BPR-G (SOT-89-5); DigiKey 0 in stock, sister codes show a 112-week factory lead; buy Torex only from an authorised distributor (clones are sold under XC6220 numbers) |
| Setpoint | R1 = 11.5 kohm, R2 = 1.58 kohm, 0.1 % 0603: 0.55 x (1 + 11.5 / 1.58) = **4.553 V** | 4.55 V fixed |
| Row 2 band (datasheet limits) | VFB +-1.5 % over TJ -40..125 C, resistors +-8 mV, IFB 1.2 mV, line 7.5 mV, load 9 mV (typ): **4.459-4.638 V**, about 70 mV inside 4.39-4.71 V both sides | +-1 % initial, load 45 mV max, line 7.6 mV, temperature +-100 ppm/C **typical only**: 4.413-4.688 V, about 22 mV inside |
| Row 3 dropout | 130 mV max at 500 mA over temperature: in regulation down to 4.683 V input (row 3 needs 4.715 V: 32 mV spare) | 85 mV max at 300 mA (25 C); about 4.67 V input needed hot [est] |
| Rows 4, 5 | current limit >= 530 mA, built-in soft start; VIN 1.5-6.0 V | limit >= 1005 mA, inrush prevention; VIN 1.6-6.0 V |
| Row 7 thermal at 0.243 W | SOT-23-5 176.9 C/W (TI board): **over the 150 C/W row** unless the carrier carries generous copper; WSON-6 80.3 C/W meets it. G-W13 (f) decides | SOT-89-5 76.9 C/W (Torex board); 120-150 C/W on a small copper carrier [est] |
| Row 8 reverse current | **no blocking** (body diode; VOUT <= VIN + 0.3 V abs max); a 95 ohm active pull-down when disabled / in UVLO: G-W13 (e) must check it does not sink EXT+ while VBUS decays | **no blocking** (parasitic diode) |
| Capacitors | CIN 2.2-4.7 uF, COUT 4.7 uF X7R 0805 16 V (TI: CIN >= 1 uF, COUT 0.47-220 uF effective) | CIN 10 uF + CL 10 uF low bias-loss ceramics (1206 25 V class [est]), not the 0805 values first assumed |
| Parts / joints on the carrier | LDO + 2 resistors + 2 MLCC + carrier: **+5 parts, about +15 joints net** against A | LDO + 2 MLCC + carrier: +3 parts, about +11 joints net |

**Rejected:** Torex XC6210B45APR-G (no dropout maximum at 0.3 A, its load term fails row 2 on paper, MOQ 6,000); TI
TPS73601 (VIN only 5.5 V with a 6.0 V absolute maximum, 400 mA minimum limit on legacy silicon); Nisshinbo RP111
(VIN 5.25 V class). **No pre-assembled 4.5 V regulator board was found**; the carrier stays a small custom PCB (D2-16P).
**No candidate blocks reverse current with its enable tied to VIN, so the G-W7 (c) re-run with the regulator fitted
remains the deciding backfeed test.** Recommendation inside option C: the TLV75801P, the only candidate whose datasheet
maxima cover rows 2-5 with margin and that can be bought in single quantities now; take the WSON-6 if the carrier is
reflowed, else the SOT-23-5 on a copper-rich carrier and let G-W13 (f) confirm the temperature. Option C itself stays a
user decision (BOM lines at quantity 0). **Nothing here is selected, bought, built or measured; the gate is G-W13
(section 9), then G-W6 on the regulated lead.** Research record: the r4 notes in `cad/gs8-d2-v1/NOTES.md`.

## 5. Pi 5 header (J8) and I2C

<!-- BEGIN:header -->
| Pin | Signal | Connected to | Cable | Bias / logic |
|---|---|---|---|---|
| 1 | 3V3 | encoder V+ (QT red) | `qt` | 3.3 V supply |
| 2, 4 | 5V | X1203 pogo pins (feed in) | none (pogo) | 5.1 V from the X1203 |
| 3 | GPIO2 / SDA1 | encoder SDA (QT blue); X1203 gauge (pogo) | `qt` | Pi 1.8 k pull-up |
| 5 | GPIO3 / SCL1 | encoder SCL (QT yellow); X1203 gauge (pogo) | `qt` | Pi 1.8 k pull-up |
| 6 | GND | encoder GND (QT black) | `qt` |  |
| 33 | GPIO13 | 18/24 switch, common lug | `fps_lead` | input, pull-up; low = 24 fps, high = 18 fps |
| 34 | GND | 18/24 switch, position-2 lug | `fps_lead` |  |
| 37 | GPIO26 | run button | `run_lead` | input, pull-up; low = pressed (run toggles on press) |
| 39 | GND | run button | `run_lead` |  |
| (pogo) | X1203 status lines | X1203 | none | **reserved**: Geekworm documents GPIO lines for power-loss detect and charge control on the X120x family (GPIO6 / GPIO16 on the X1200 wiki, recalled, not re-read). Do not use GPIO6 or GPIO16 until G-W2 confirms them |
<!-- END:header -->

All other header pins are free. The QT, run and 18/24 sockets plug onto the top of the header; the X1203 pogo pins
touch the solder tails from below, so both share pins 1-6 without conflict.

**I2C bus 1 (100 kHz):**

| Address | Device | How set |
|---|---|---|
| 0x36 | X1203 fuel gauge (X120x family; part not re-read) | fixed (listing; G-W2 confirms) |
| 0x37 | Adafruit 5880 encoder (seesaw) | **A0 bridged** with 1 solder blob at step 1 (default 0x36 clashes with the gauge) |

Pi 5 CSI: the GS camera is on **CAM/DISP 1** (layout `COTS['pi5']` `cam1`, x -60..-50 on the port edge). Pi 5 HDMI0
(nearest the USB-C) is `HDMI-A-1`.

## 6. Cables (every cable, both ends)

Generated from `layout.CABLES` and `layout.KEEPOUTS` by `cad/gs8-d2-v1/make_tables.py`; the part-number class and the
routing note per cable are kept in that script (`CABLE_INFO`). Keep-out boxes are in the assembly frame (X forward,
Y left, Z up, x 0 at the front-plate face). The plug steps are the `STEPS` numbers in ASSEMBLY.md.

<!-- BEGIN:cables -->
| id | Cable (class) | From | To | Length (mm) | Plugged at step | Route (keep-out chain) | Routing note |
|---|---|---|---|---|---|---|---|
| `fpc` | Raspberry Pi camera cable "Standard-Mini" 22-to-15 pin, 200 mm (official) | Pi 5 CAM/DISP 1 (port edge) | GS camera (lower rear) | 200 | 4, 7 | `ko_fpc_up` x -60..-50 / y 24..32 / z 20.2..36.5; `ko_fpc_run` x -50..-42.6 / y 17.2..32 / z 30..39.4; `ko_fpc_link` x -43.6..-41.5 / y 17.2..19.5 / z 36.6..39.4; `ko_fpc_loop` x -42.5..-29.7 / y 2..19.5 / z 36.6..56; `ko_fpc_cam` x -32.1..-24 / y -8..8 / z 39.4..47 | up from CAM/DISP 1 beside the HDMI plug, forward over the cooler at z 30-39, S-fold of 9 layers over the fin end (bend r >= 1), down the camera rear face to its 15-pin connector |
| `hdmi` | micro-HDMI D-D, 200 mm (+10/-0), shielded thin coax OD 3.0; Pi end 90 deg up plug (<= 8.5 mm off the board, Q2), board end right-angle with the cable leaving -Y (EVF-SELECTION A3) | Pi 5 HDMI0 | EVF board lower edge | 200 | 4, 6 | `ko_hdmi_pi` x -36.6..-27 / y 24..32 / z 17..41; `ko_hdmi_link` x -37.8..-35.6 / y 24..32 / z 39.6..41; `ko_hdmi_run` x -113..-36.8 / y 20..32 / z 39.6..44; `ko_panel_link` x -114.5..-112 / y 17..21.5 / z 39.6..46; `ko_hdmi_coil` x -139..-113.5 / y -12..18 / z 37.3..60; `ko_hdmi_evf` x -144.8..-136.8 / y 4..17 / z 52..63.8 | up from HDMI0, back along the panel side under the dials (z 39.6-44), slack coil over the stick guide (ko_hdmi_coil, x -139..-113.5), down to the board lower edge through the slot gap y 4-17 |
| `usb_5v` | USB-A male to 2-wire lead (24-26 AWG, 200 mm class) + 1N5817 in the + conductor + JST PH 2-pin wire-to-wire junction at the board end | Pi 5 upper USB 2 port | EVF board 5 V | 200 | 4, 6 | `ko_usb_evf` x -125..-94 / y -32..-16.5 / z 27.2..37; `ko_5v_up` x -131..-125 / y -32..-24 / z 27.2..70; `ko_5v_end` x -136.5..-130 / y -24..1.5 / z 64..70 | from the upper USB 2 port up the right-rear corner (y < -24) to z 64-70, across to the board 5 V pigtail; diode and splice under adhesive heat-shrink |
| `oled_flex` | Hicenda kit flex FM04112-MF1-A, 50 mm (with the panel) | HMX039 | EVF board ZIF | 50 | 6 | direct | from the OLED cell (open +Y) straight back to the board ZIF; mated outside the body, then the OLED and the board go in together as a tethered pair (step 6); no fold beyond the kit form |
| `qt` | Adafruit 4397 STEMMA QT (JST SH 4) to female sockets, 150 mm | encoder | GPIO 1/3/5/6 | 150 | 4, 8 | `ko_qt_lead` x -21..-11 / y -31.7..-25.8 / z 28.8..40; `ko_lead_wall` x -64..-11 / y -32.3..-26 / z 36.6..44; `ko_lead_link` x -75..-63 / y -32.3..-26 / z 36.6..44; `ko_lead_cross` x -84..-74 / y -32.3..20 / z 36.6..44 | header end plugged at step 4 on pins 1/3/5/6 (ko_qt_lead), up the right wall (ko_lead_wall, z 36.6-44), across behind the blower inlet (ko_lead_cross, x -84..-74) to the encoder lower edge; the JST-SH end plugs into the encoder at step 8 |
| `run_lead` | pre-wired momentary button lead with female sockets (Squid Button class) | run button | GPIO26 + GND (pins 37/39) | 250 | 3, 4 | `ko_run_drop` x -34..-28 / y 1.5..9 / z -14.2..2.7; `ko_run_floor` x -34..-22 / y 1.5..31 / z 2.7..5.8; `ko_run_rise` x -26..-22 / y 24.1..31 / z 2.7..37; `ko_run_link` x -26..-22 / y 23..25.5 / z 35.5..38.5; `ko_run_cross` x -27..-21 / y -32.3..24.1 / z 36.6..39.8; `ko_lead_wall` x -64..-11 / y -32.3..-26 / z 36.6..44; `ko_run_leads` x -63..-50 / y -31.7..-25.8 / z 28.8..40 | up from the grip cradle through the base opening and the floor run-lead hole, along the floor channel under the X1203, up the port-side rise (ko_run_rise), over the cooler shroud under the camera (ko_run_cross, x -27..-21, z 36.6-39.8), along the right wall (ko_lead_wall) down to pins 37/39 (plugged at step 4) |
| `fps_lead` | 2-way Dupont F to JST PH 2-pin lead, 200 mm (header side) + 50 mm JST PH pigtail soldered to the switch lugs (2 joints); the PH pair is the step-8 inline junction | 18/24 switch | GPIO13 + GND (pins 33/34) | 200 | 1, 4, 8 | `ko_run_leads` x -63..-50 / y -31.7..-25.8 / z 28.8..40; `ko_lead_wall` x -64..-11 / y -32.3..-26 / z 36.6..44; `ko_lead_link` x -75..-63 / y -32.3..-26 / z 36.6..44; `ko_lead_cross` x -84..-74 / y -32.3..20 / z 36.6..44; `ko_hdmi_run` x -113..-36.8 / y 20..32 / z 39.6..44; `ko_panel_link` x -114.5..-112 / y 17..21.5 / z 39.6..46; `ko_fps_up` x -128..-113 / y 14..19 / z 44..57 | header end plugged at step 4 on pins 33/34, up the right wall (ko_lead_wall), across behind the blower inlet (ko_lead_cross), back along the panel-side channel (ko_hdmi_run), up to the switch lugs (ko_fps_up); PH junction mated at step 8 |
| `pigtail` | 18 AWG silicone pair, 180 mm, XT30U female; soldered to the X1203 battery pads (2 joints); r4: inline 15 A fuse (Littelfuse 0251015.MXL) in the + conductor within about 25 mm of the XT30 female (2 joints) | X1203 battery pads | XT30 junction in the grip | 180 | 1, 4 | `ko_pig_wrap` x -40.5..-35.5 / y 23.7..26.5 / z 2.7..10; `ko_pig_under` x -40.5..-35.5 / y -5..23.7 / z 2.7..5.8; `ko_pig_in` x -43..-19 / y -14..-5 / z 2.7..5.8; `ko_pig_drop` x -43..-36 / y -12..-5 / z -12.3..2.7; `ko_pig_link` x -43..-37 / y -10..-5 / z -13.5..-11.3; `ko_xt30` x -65..-37 / y -10..10 / z -36.5..-12.5 | from the X1203 pads round the port edge (ko_pig_wrap; pad position Q2), under the board (ko_pig_under, ko_pig_in), down the pigtail hole into the grip to the junction; the sleeved fuse (about 20 x dia 5) lies along X under the XT30 pair (ko_xt30) |
| `fan` | Active Cooler fan lead (native, JST-SH 4) | Active Cooler | Pi 5 FAN header | 60 | 1 | direct |  |
| `pack_lead` | 18 AWG silicone pair, 60 mm, XT30U male (part of the pack) | 1S2P BMS | XT30 male | 60 | 10 | `ko_xt30` x -65..-37 / y -10..10 / z -36.5..-12.5 | from the pack BMS to the junction above the pack at the grip mouth |
<!-- END:cables -->

## 7. Plug order (each connector is mated once, at the step listed)

Generated from `PLUG_ORDER` in `cad/gs8-d2-v1/make_tables.py` (the same rows appear per step in ASSEMBLY.md).

<!-- BEGIN:plugs -->
| Step | Connector | Action | Caution |
|---|---|---|---|
| 1 (bench) | pigtail fuse (r4) | splice the 15 A fuse (Littelfuse 0251015.MXL) into the red conductor about 20-25 mm from the XT30 female: trim each fuse lead to 6.5 mm (a 1.5 mm stub at the body + a 5 mm lap joint on the stripped conductor), adhesive 3:1 heat-shrink over the whole splice (about 28 mm) | hand-solder at 350 C for 5 s max per lead (datasheet); never re-solder the XT30 female with the fuse fitted; meter the red path end to end (< 0.1 ohm) |
| 1 (bench) | pigtail -> X1203 battery pads | solder red to +, black to -; adhesive heat-shrink over both joints; strain-relief tie to a standoff | **pack never connected** at the bench; meter + to - for no short before anything else |
| 1 (bench) | Active Cooler lead -> Pi FAN | plug the JST-SH 4 | route it as the cooler ships |
| 1 (bench) | encoder A0 | 1 solder blob on the A0 jumper | address 0x37 |
| 1 (bench) | 18/24 switch pigtail | solder the 50 mm JST PH 2-pin pigtail to the common and position-2 lugs; heat-shrink |  |
| 1 (bench) | microSD | flash it (gate G-W3), then take it out of the Pi | the card must be out for steps 3-4 (it hits the front wall on the stack path) |
| 1 (bench) | EVF 5 V lead | solder the 1N5817 into the + conductor (band toward the board), the PH plug on the free end; adhesive heat-shrink | polarity: meter USB-A VBUS -> PH pin 1 through the diode (forward), GND -> pin 2 |
| 1 (bench) | EVF board pigtail (Rev I) | solder the PH 2-pin pigtail to the traced EXT+ / GND pads; heat-shrink strain relief | photograph both board sides first (EVF gate G1) |
| 3 | run lead | after the base slide, fish its socket end up through the floor run-lead hole (x -34..-28, y 1.5..9) with tweezers | not before the slide: the base opening and the hole only overlap at the final pose |
| 4 | run lead | lay it in its floor channel before the stack goes down (`ko_run_floor`) |  |
| 4 | pigtail | feed the XT30 end down through the pigtail hole (x -45..-34, y -13..-4) into the grip | before the stack goes down |
| 4 | micro-HDMI -> Pi HDMI0 | 90 deg plug, cable leaves upward | the EVF end stays loose |
| 4 | FPC -> Pi CAM/DISP 1 | contacts as printed on the cable; latch closed | camera end loose |
| 4 | EVF 5 V lead -> Pi upper USB 2 port | USB-A | PH end loose |
| 4 | QT lead -> pins 1/3/5/6 | red 1, blue 3, yellow 5, black 6; top open, header in sight | count from pin 1: an off-by-one plug puts 5 V (pin 2/4) on the 3V3 wire |
| 4 | 18/24 lead -> pins 33/34 | GPIO13 on 33, GND on 34; PH end parked out of the left side |  |
| 4 | run lead -> pins 37/39 | GPIO26 on 37, GND on 39 | route over the cooler shroud (`ko_run_cross`) |
| 5 | microSD -> Pi slot | push home through the front slot (hood plate + tub wall) with tweezers, contacts up | after the hood is on |
| 6 | flex -> EVF board ZIF | outside the body, contacts per the kit | ESD: grounded mat |
| 6 | micro-HDMI -> EVF board | outside the body; right-angle plug, cable leaves -Y | **only after gate G-W7 passed** |
| 6 | EVF 5 V lead PH -> board pigtail PH | outside the body, then the OLED + board pair slides in | **never mate live** (pack unplugged) |
| 7 | FPC -> GS camera | 15-pin end, latch closed | fold the slack into `ko_fpc_loop` |
| 8 | QT lead -> encoder JST-SH | panel held beside the body | header end went on at step 4 |
| 8 | 18/24 PH junction | mate the 2-pin PH pair | header end went on at step 4 |
| 9 | USB stick -> Pi lower USB 3 port | from the rear scoop, sleeve fitted |  |
| 10 | pack XT30 -> pigtail XT30 | at the grip mouth; push the junction and pack up | **this powers the camera**: the X1203 may start the Pi |
<!-- END:plugs -->

## 8. Raspberry Pi configuration

Use Raspberry Pi OS **Lite** (64-bit) on the microSD card: a desktop session would handle the power key itself.

`/boot/firmware/config.txt`:

```
[all]
dtparam=i2c_arm=on
dtparam=i2c_arm_baudrate=100000
camera_auto_detect=1                 # GS camera (IMX296) on CAM/DISP 1
max_framebuffers=2                   # EVF (EVF-SELECTION s4)
disable_fw_kms_setup=1               # firmware must not pass its own EDID-derived video= line
# operating restrictions (section 4.3); the camera image only
arm_freq=1800                        # R-P3: keep only if G-W12 shows 0 dropped frames in S2/S3
dtoverlay=disable-wifi               # R-P4
dtoverlay=disable-bt                 # R-P4
# R-P2: no over_voltage / force_turbo / arm_freq > 2400. R-P5: no dtparam=pciex1
# no LED indicators (user decision 2026-10-05): both Pi 5 onboard LEDs off once the firmware reads this file
# WHOLE BLOCK [to confirm on the bench, G-W3]: parameter names from community guides, not the official page; trigger
# and polarity both unconfirmed. Fallback if a LED stays lit: the other polarity, or trigger=default-on with activelow=off
dtparam=pwr_led_trigger=none
dtparam=pwr_led_activelow=off        # [to confirm on the bench, G-W3]: if the LED lights instead, use =on
dtparam=act_led_trigger=none
dtparam=act_led_activelow=off        # [to confirm on the bench, G-W3]: same polarity check
```

**No LED indicators (user decision 2026-10-05).** The camera's I/O is the exposure dial (encoder, with its push
switch), the 18/24 dial, the power plunger (on/off), the run (record) button and the EVF. The plunger is black ASA
and is no longer a light pipe. The four `dtparam` lines above switch the Pi 5 onboard LEDs off (syntax as the
Raspberry Pi config.txt LED parameters; the active-low polarity on the Pi 5 is [to confirm on the bench] at G-W3). The
bootloader may still blink the LED before it reads config.txt; behind the black plunger only the 0.3 mm clearance
round the stem could show it, so it is not an indicator (record at G-W8 what is visible). LEDs on the X1203 and
the EVF board, if any, sit inside the closed body and are not indicators: no action, unless G-W8 finds one visible
through a vent (then record it there). The 5880 encoder board's NeoPixel, if the board has one, stays off: the
software never writes it [to confirm at G-W9].

Append to the single line of `/boot/firmware/cmdline.txt` (EVF-SELECTION s4; HDMI0 = HDMI-A-1, 1024x768 60 Hz DMT):

```
video=HDMI-A-1:1024x768@60D vc4.force_hotplug=1
```

Bootloader EEPROM (`sudo rpi-eeprom-config --edit`):

```
PSU_MAX_CURRENT=5000                 # no USB-PD on the pogo feed: declare a 5 A supply (USB budget 1.6 A)
POWER_OFF_ON_HALT=1                  # after halt the PMIC switches the board off (lowest standby drain)
                                     # if the Pi 5 bootloader also wants WAKE_ON_GPIO=0 for this, set it (check the rpi-eeprom notes; G-W8)
                                     # BOOT_ORDER: leave the default (microSD first); the stick is media, not boot
```

**Power key.** `/etc/systemd/logind.conf.d/gs8-powerkey.conf`:

```
[Login]
HandlePowerKey=ignore
HandlePowerKeyLongPress=ignore
```

Then a small daemon (`gs8-powerkey.service`, Restart=always) reads the `pwr_button` input device (python-evdev) and runs
`systemctl poweroff` only when KEY_POWER has been held down for **2.0 s** without release. A shorter press does
nothing. While halted (POWER_OFF_ON_HALT=1), a press of the button powers the Pi on again (G-W8 confirms this on the
X1203 feed). The 2 s threshold must stay well below the PMIC's forced-off hold; G-W8 measures both.

**Inputs** (libgpiod v2, `gpiochip0` on the Pi 5 RP1, line offsets = BCM numbers):
- GPIO26 run: input, bias pull-up, debounce 10 ms, falling edge = toggle record.
- GPIO13 18/24: input, bias pull-up; read on boot and on both edges; low = 24 fps, high = 18 fps.
- Encoder 0x37: seesaw (adafruit-circuitpython-seesaw, `IncrementalEncoder`); the 5880's push switch (seesaw pin 24,
  pull-up) is free for an "exposure reset" function.
- X1203 gauge 0x36: read the cell voltage and state of charge for the EVF overlay; shut down cleanly at a software
  cell threshold under load (planning value 3.3 V; G-W5 sets it).

**Status on the EVF (no LEDs; software requirement, r3 led-removal).** Power-on is shown by the EVF boot screen.
On every shutdown (2 s plunger hold, low-cell threshold or a software poweroff) the camera software shows a
"shutting down" screen and keeps it until recording has stopped, the stick has been synced and unmounted and the
system halts. After halt the EVF goes dark. The EVF is fed from Pi USB 2 (upper) and from HDMI0; with
`POWER_OFF_ON_HALT=1` the Pi switches its outputs off at halt, so EVF dark is expected to be a direct sign that the
Pi is off. This follows from the configuration only and must be confirmed on the bench (G-W4 and G-W8 pass
criteria). The procedures (ASSEMBLY s7 P1, battery removal) wait 5 s after the EVF goes dark.

## 9. Bench gates (all open; none can be closed from documents)

| Gate | When | Procedure | Acceptance |
|---|---|---|---|
| G-W1 Pack receipt | before printing the grip | meter the XT30 polarity and the pack voltage; confirm the BMS and its rating label; check the pack against the bay (`COTS['pack']` box 38 x 20 x 72); r4: check the builder's BMS data against R-PACK-BMS (s4.7) and, once the fused pigtail and the X1203 stack exist, plug the full pack into the stack 10 times | + on the marked contact, 3.5-3.9 V, BMS >= 10 A; R-PACK-BMS (1)-(5) stated in numbers; r4: 10 of 10 plug-ins with no BMS trip and the fuse intact (red path end to end < 0.1 ohm afterwards) |
| G-W2 X1203 identity | on receipt | photograph both sides; locate the battery pads (Q2); read the GPIO / I2C notes on the vendor wiki; record the standoff length (10.9 assumed) | pad position and reserved GPIO lines recorded here |
| G-W3 Pi on the bench PSU | before any internal power | official 27 W PSU: flash the OS, set the EEPROM, install section 8; camera, stick, fan; `i2cdetect -y 1` shows 0x37 (and 0x36 once the X1203 is stacked); look at the Pi 5 LED after the kernel has started | all present; the onboard LED dark after boot, neither red nor green lit (else try the other `*_activelow` polarity, or trigger=default-on with activelow=off, section 8) |
| G-W4 X1203 feed | stack on the bench, pack replaced by a current-limited supply at 3.7 V | boot; `vcgencmd get_throttled` = 0x0; 5 V at header pin 2 by meter under CPU + camera + stick load; then `sudo poweroff` and meter the USB 2 (upper, EVF feed) 5 V and record the time from the end of the shutdown screen | 0x0, >= 4.95 V; USB 2 5 V < 0.5 V within 5 s of halt (expected from POWER_OFF_ON_HALT=1, unconfirmed) |
| G-W5 8.6 A path | stack on the bench with the real pack, pigtail and XT30 | (a) 10 min at camera full load (stress + recording + EVF, about 4-7 A by 4.7); (b) **10 min at 8.6 A** (the 4.7 sizing current) drawn by an electronic load on the pigtail end before it is soldered to the X1203 (or across the pads with the X1203 disabled), pack >= 3.7 V; thermocouples on the pads, the XT30, the pigtail and (r4) the fuse sleeve in both; record the pack voltage at the X1203 cut-off | joints and XT30 < 60 C in (a) and (b); r4: fuse sleeve <= 70 C (the adhesive liner softens above it); drop pack-to-pads at 8.6 A <= 0.15 V, fuse included (estimate 0.135 V: only 15 mV in hand; if it fails, shorten the pigtail or move to 16 AWG before relaxing the limit); cut-off recorded for the software threshold |
| G-W6 EVF rail (diode upper bound) | after EVF-G1 and EVF-G4 (board alone at 4.25 / 4.55 / 4.90 V), on the G-W4 bench stack (X1203 fed from the bench supply), **before the EVF carrier freeze and before the print set** (r2 fixer: it no longer waits for G-W12) | the real lead (USB port + 1N5817): voltage at the board terminals in 5 states (HDMI unplugged, boot, full black, full white, 10 min live), with the X1203 output (header pin 2) logged at the same moment | 4.25-4.90 V in every state (the G4b window), **and** worst case = highest reading + (source max - X1203 output at that reading) + 0.05 V hot-diode allowance <= 4.90 V, lowest reading - (X1203 output - 4.845 V) >= 4.25 V. Source max = 5.355 V (X1203 listing 5.1 V +5 %) for this run. A unit-specific value (highest X1203 output recorded in G-W12 + 0.05 V, unit photographed) may replace it only in a re-run after G-W12. No typical diode drop is accepted on paper. **Expect a fail**: with 5.355 V the gate passes only if the total drop is >= 0.505 V; a 1N5817 at 0.1-0.3 A plus the lead gives about 0.30-0.45 V [est]. **Fail (diode lead), r3:** the diode is **replaced** (not supplemented) by the regulated feed of s4.8 (option C: 4.55 V LDO, R-EVF-REG; r4: +5 parts and about +15 joints net with the TLV75801P, +3 / +11 with the fixed XC6220B45; BOM candidate lines D2-16R/D/C/P); run G-W13, then this gate on the regulated lead. **Regulated-lead run (option C):** the same 5 states and logging, plus a scope (20 MHz bandwidth) at the board terminals; pass = every reading inside **4.35-4.80 V** (0.10 V inside the window), ripple <= 50 mV p-p in every state, every instantaneous value inside 4.30-4.85 V, and lowest reading - (X1203 output at that reading - 4.845 V) >= 4.25 V. The upper bound needs no source correction because G-W13 (a) shows the output at a 5.36 V input. G-W7 is re-run with the regulated feed |
| **G-W13 EVF feed regulator (r3, option C)** | on receipt of the regulator carrier, before the regulated lead is built and before G-W6 (regulated run) | bench supply into VIN; electronic load at the end of the real output lead length (about 30 mm + PH pair); thermocouple on the regulator case; scope 20 MHz bandwidth at the load end. (a) Vin 4.715 / 5.10 / 5.36 V x load 0 / 0.05 / 0.15 / 0.30 A, cold and after (f); (b) at 0.30 A lower Vin until Vout falls 2 % below its 5.10 V-input value, record Vin - Vout; (c) Vin stepped 0 -> 4.85 V (about 1 ms rise) into 0.30 A resistive + 100 uF at the load end [stand-in for the unknown board capacitance], 5 times; (d) load step 0.05 <-> 0.30 A, and steady 0.30 A with the X1203 bench stack's USB port as the source; (e) **back-feed against a defined off rail (r4, audit 2026-10-05-r3; replaces "VIN open", which only charges a floating node)**: VIN on the real lead's USB-A plug in the G-W4 bench stack (Pi 5 + X1203 on the bench supply), with a 100 ohm stand-in load from that VBUS to GND; VOUT held through 10 ohm at 4.90 V, or at VIN + the selected device's rated maximum VOUT - VIN if that is lower (never beyond the device's ratings); log the reverse current into VOUT and the VBUS voltage with the stack running, through `sudo shutdown -h now`, the X1203 output off and for 60 s after, 3 times; (f) 10 min at 5.36 V and 0.30 A in its sleeve in still air | (a) Vout 4.39-4.71 V at every point (R-EVF-REG row 2), in regulation or in dropout; (b) dropout <= 0.30 V hot; (c) monotonic rise, no overshoot above 4.80 V, >= 4.39 V within 5 ms, 5 of 5; (d) ripple <= 50 mV p-p steady, every instantaneous value in 4.30-4.85 V, settled within 100 us, no sustained oscillation; (e) reverse current into VOUT <= 1 mA at every logged point, and with the stack off the VBUS rise caused by the held VOUT <= 0.10 V; no rating of the device exceeded (if the device has no reverse-current blocking, record it and G-W7 (c) with the regulator fitted decides); (f) case rise <= 44 C over ambient; in G-W11 (closed body, 30 C ambient) the case stays <= 90 C. Any fail: a different device against R-EVF-REG; never a wider window |
| G-W7 HDMI pin 19 | before the HDMI meets the Pi | EVF-SELECTION G5 (a)-(c) | board draws <= 50 mA from HDMI +5 V; no backfeed |
| G-W8 Power key | OS installed | short press: nothing; 2 s hold: clean poweroff; press while halted: boots; record the PMIC forced-off hold time. No LEDs (2026-10-05): the EVF shows the boot screen at power-on and the shutdown screen until halt, then goes dark; record the seconds from shutdown screen to EVF dark and whether any light shows at the plunger or a vent, also in the halted standby state (a glow there is a light leak, not an indicator) | as stated; EVF dark within 5 s of halt, the shutdown screen visible until the halt |
| G-W9 Controls | panel fitted | `gpiomon` on GPIO26 / GPIO13; encoder counts both ways; push switch | run low when pressed; 18 high, 24 low |
| G-W10 USB budget | recording | stick sustained >= 100 MB/s past cache on a part-filled stick, warm; EVF on; no USB resets in `dmesg` | no resets; throttled 0x0 |
| G-W11 Thermal | closed body | 10 min record at 30 C ambient; with EVF-feed option C also a thermocouple on the regulator case at `ko_5v_up` and the EVF terminal voltage logged; r6 (audit 2026-10-06 B-8): a second thermocouple taped to the lens collar's LR foot where it meets the tub front wall | `vcgencmd measure_temp` < 80 C, no throttling; X1203 boost < 70 C (thermocouple); option C: regulator case <= 90 C and EVF terminals inside 4.35-4.80 V at the end of the 10 min; collar foot: record the peak. Above 50 C, reprint the collar in PC and repeat G-COL-1 on PC coupons (PRINT-GUIDE s1) |
| **G-W12 Workload power (audit finding 4, r2)** | after G-W3, G-W4, G-W5 and G-W7 and after the print set (B and C need the closed body); **G-W6 is not a prerequisite** (it runs earlier, before the carrier freeze); before any powered full-build claim | **A. Load** (independent of the X1203): Pi on the official 27 W PSU through an inline USB-C power meter logging >= 10 samples/s; every load connected (camera, stick filled >= 50 %, EVF on its real lead, fan, encoder); run S0-S4 of section 4.2 (S2 and S3 10 min each; S4 5 times). **B. X1203 feed**: the stack on the X1203, the pack replaced by a bench supply feeding **through an XT30 male lead into the real pigtail** (current limit 10 A, remote sense at the X1203 pads, 4.20, 3.70 and 3.30 V at the pads) so the XT30 pair and the pad joints carry the load; repeat S0-S4 at each; closed body, thermocouples on the X1203 boost IC and inductor, the XT30 pair, both pad joints; scope on header pin 2 to pin 6 (20 MHz bandwidth limit, falling-edge trigger at 4.90 V). **C. Real pack**: full charge to the software cut-off in S2 | **P1 load**: highest 100 ms power in A <= 22.9 W (0.9 x 25.5 W) in every state; the S2 mean is reported against the 18 W planning figure (a higher mean re-issues 4.7 and the runtime). **P2 rail**: header pin 2 never below 4.85 V (the X1203 -5 % bound, 4.845 V) on the scope in any state, including S4 and S3 triggers; 1 s average >= 4.95 V. **P3 no resets / throttling**: `vcgencmd get_throttled` = 0x0 after every state (sticky bits included); no "Undervoltage", "usb ... reset" or "disconnect" line in `dmesg`; the `journalctl --list-boots` count unchanged; 0 dropped frames (continuous sequence numbers) in S2 and S3. **P4 temperatures** (10 min S3, ambient recorded, corrected to 30 C): X1203 boost IC and inductor <= 70 C; XT30 pair and pad joints <= 60 C; SoC < 80 C. **P5 battery range**: P2-P4 hold at 4.20, 3.70 and 3.30 V in B; in C the software shutdown fires before the X1203 cut-off in 3 of 3 runs and the open take closes readable. **P6 startup**: 5 of 5 cold starts at 3.30 V reach recording-ready with P2 and P3 held, the stick enumerated at 5000M, the camera detected and an EVF image. **P7 burst**: S3 at 3.30 V holds P1-P3. Any fail at P1, P2 or P4: option 4.5. R-P3 (CPU cap) stays only if P3's frame count passes with it. **Other fails (r2 fixer):** P3 with throttling, undervoltage or reset bits = a P2 fail (option 4.5); P3 with dropped frames only: drop R-P3 if it was on, else fix the writer (queue depth, sync policy) and re-run A and B. P5 (software shutdown after the X1203 cut-off): raise the R-P8 threshold in 0.05 V steps and re-run C; if no threshold leaves a usable runtime, option 4.5. P6: if the scope shows a P2 dip in S4, option 4.5; if only enumeration or camera detection fails, fix the boot sequence (software) and re-run 5 of 5 |

## 10. Open items

- **Q2 (concept):** X1203 pad position, stack height (`X1203_KIT` standoff 10.9 assumed), boost heat at 5 A in the
  closed tub, its USB-C position (unused in D2), and whether it starts the Pi when the pack is plugged in.
- **Pack:** variant NOT chosen: a procurement decision for the user (MEASURED-PARTS MP-PACK); a 1S2P high-drain pack
  with BMS and an XT30 male lead may need a custom build (+2 joints if the XT30 is not fitted). Out-of-body charging needs a 1S Li-ion charger with an XT30 lead (BOM tools).
- **EVF board revision:** Rev I assumed (pads); a Rev II board takes a 6-pin header lead (EVF-SELECTION s5).
- **FPC length:** a 100-150 mm 22-to-15 cable would remove the S-fold (concept Q4); 200 mm is the stocked length.
  Quantified as option (b) in `cad/gs8-d2-v1/OPTIONS.md` (presented, not applied).
- **Interface records (r2; count r3):** every part whose real dimensions drive CAD has a measurement record, gate and
  pass criterion in `cad/gs8-d2-v1/MEASURED-PARTS.md`: **10 records**, one `MP-*` id each (MP-PACK, MP-X1203 with its
  Active Cooler line, MP-CAM, MP-HDMI, MP-RUN, MP-EVF, MP-ENC, MP-SW, MP-STICK, MP-FPC); none measured yet. The EVF bench assembly (MP-EVF) comes before the carrier freeze.
- **Power (r2):** the 27 W planning peak exceeds the X1203's 25.5 W. Section 4 estimates the envelope with
  R-P1..R-P8 at 17.7-22.1 W (r2 fixer; R4's 15-19 W used an S3 board figure below the published CPU-only figure);
  the worst case is only 0.8-2.3 W under the G-W12 P1 limit without the CPU cap. **r3: an estimate, not a
  demonstrated supply margin; the 27 W planning peak stays above the 25.5 W rating.** G-W12 stays open until measured.
  Fallback: 4.5 (another design, not a verified drop-in).
- **EVF feed (r3, replaces the r2 "G-W6 likely outcome" item):** the diode feed passes G-W6 only with a >= 0.505 V
  total drop at the 5.355 V source maximum, which no datasheet guarantees. The r2 contingency "5 V regulator module" is
  withdrawn (a 5.0 V output breaks the 4.90 V maximum). Resolved requirement R-EVF-REG, comparison and recommendation
  in s4.8: **option C, a 4.55 V LDO as the primary feed with the diode deleted** (r4: primary candidate TI TLV75801P set to 4.553 V,
  fixed alternative Torex XC6220B45BPR-G; XC6210 rejected); gates G-W13 then G-W6 (regulated run) and a G-W7 re-run.
  User decision; BOM candidate lines D2-16R/D/C/P at quantity 0 until it is taken.
- **Pigtail fuse (r4, W-10):** Littelfuse 0251015.MXL in the pigtail + conductor near the XT30 female; fit is computed
  (in the `xt30_pair` proxy, seen by the pack-insertion sweep) but the hand-fit of the sleeve in the junction slack, the
  drop (0.135 V estimate against 0.15 V) and the sleeve temperature are G-W5 items; the plug-in surge is G-W1.
- **Fan lead:** the Active Cooler's own lead is in `layout.CABLES` (`fan`, 60 mm estimate, plugged at step 1, no keep-out: it stays on the cooler).
- **Header leads (FIXER A-F1, 2026-10-04):** the QT, 18/24 and run leads go on the Pi header at step 4 with the top open; step 8 only makes the panel-side joints (QT JST-SH at the encoder, 18/24 JST PH inline junction). Their bodies have keep-outs (`ko_lead_wall`, `ko_lead_cross`, `ko_run_cross`, `ko_fps_up`) that the hood, EVF, camera and panel sweeps see. Lead lengths are path estimates from the keep-out chain (QT about 130 mm in a 150 mm lead; 18/24 about 190 mm in 200 + 50 mm): confirm on the mock-up.
