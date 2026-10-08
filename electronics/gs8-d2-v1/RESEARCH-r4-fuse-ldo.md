# D2 r4 research: battery-pigtail fuse and EVF-feed LDO (2026-10-05)

Read-only desk research for `electronics/gs8-d2-v1` (WIRING s4.7, s4.8, gates G-W5/G-W6/G-W7/G-W13; BOM D2-13/14/16R/C/P/26;
layout keep-outs). Nothing was bought or measured. Datasheet facts carry their URL (section 3). [unconfirmed] = not
found in a primary source; [est] = my estimate; [graph] = read off a datasheet curve. Littelfuse and Torex sites refuse
automated fetches (HTTP 403), so their datasheets were read from verbatim third-party copies (revision codes given).

## 1. Task 1: inline fuse in the 18 AWG pigtail

### 1.1 Sizing rule
- Continuous current to carry: **8.6 A** (X1203 25.5 W at 3.3 V, WIRING s4.7). Ambient around the fuse 25-40 C, up to
  about 55-60 C inside the closed body [est].
- Littelfuse 251 datasheet, temperature re-rating note: "Re-rating depicted in this curve is in addition to the standard
  derating of 25% for continuous operation." So I_rated x 0.75 x K(T) >= 8.6 A. K(T) [graph, 251 curve]: about 100 % at
  25 C, 98.5 % at 40 C, 96.5 % at 60 C (the line runs from about 110 % at -60 C to about 91 % at 120 C).
- Minimum rating: 8.6 / (0.75 x 0.985) = **11.6 A at 40 C**; 11.9 A at 60 C. 10 A fails (7.4 A allowed); 12 A passes by
  only 1-3 %; **15 A passes with 2.3-2.6 A in hand**.

### 1.2 Candidates (all axial, solderable inline, currently listed)
| | **A. Littelfuse 0251015.MXL** (PICO II 251, 15 A) | B. OptiFuse FXG-15A (15 A) | C. Littelfuse 0251012.MXL (12 A) |
|---|---|---|---|
| Speed class | very fast-acting | fast-acting | very fast-acting |
| Voltage / interrupting | 32 V AC/DC; **300 A @ 32 VDC**, 50 A @ 32 VAC | 72 VAC (30 A @ 72 VAC); **300 A @ 32 VDC** (15-20 A row) | 32 V; 300 A @ 32 VDC |
| Body | **3.18 mm max dia x 7.11 mm** (drawing, 5-15 A marking); leads 0.81 mm, 27.78 mm each side (T1); DigiKey lists 3.18 x 7.10 | 2.7 +-0.3 dia x 7.3 +-1.0 mm; leads 0.8 mm (>= 8 A) | 3.18 max x 7.11 mm; leads 0.81 mm |
| Cold resistance | 4.46 mohm; nominal drop 0.071 V at 15 A | not published [unconfirmed] | 5.9 mohm; 0.0878 V at 12 A |
| Drop / loss at 8.6 A | **0.038-0.041 V, 0.33-0.35 W** (cold R to the rated-current value) | about the same [unconfirmed: no R in datasheet] | 0.051 V, 0.44 W |
| Melting I2t (nominal) | **68.8 A2s** | 68.28 A2s ("reference") | 45.2 A2s |
| Opening time | 100 %: 4 h min; 200 % (30 A): 10 s max | 100 %: 4 h min; 200 %: 20 s max | 200 %: 10 s max |
| Derating guidance | 25 % standard + re-rating curve (above) | curve "D: effect on current rating", about 100 % at 25 C, 98 % at 40 C [graph]; no 25 % statement in the sheet (industry rule applied) | same as A; **allowed 8.87 A at 40 C, 8.69 A at 60 C: 1-3 % margin** |
| Allowed continuous at 40 C | 11.1 A (8.6 A = 78 %) | 11.0 A [est, same rule] | 8.87 A (8.6 A = 97 %) |
| Operating temp | -55..125 C | -55..125 C | -55..125 C |
| Hand soldering | 350 +-5 C, 5 s max; withstands 60 s above 200 C | not stated [unconfirmed] | as A |
| Distributor | DigiKey **F2352-ND**, 8,035 in stock, USD 1.45 (1) / 1.105 (10), Active; RS 542-1216P | DigiKey keyword search shows FXG-15A at USD 1.16 (DigiKey PN, stock not captured) [unconfirmed]; Jameco 2708495 (page refused fetch) | DigiKey **F2351-ND**, 1,107 in stock, USD 1.63, Active, 17 wk factory lead |
| Datasheet | Littelfuse 251 (rev. VL 09/26/24) [D1] | OptiFuse FXG Rev H 10/2018 [D2] | [D1] |

Element14 SG did not answer within the fetch timeout; no SG listing confirmed [unconfirmed].

### 1.3 Plug-in inrush against the fuse (estimate; the X1203 input capacitance is not published)
Charging a capacitor C from V through loop resistance R dissipates C V^2/2 in R, so the current integral is
**I2t = C V^2 / (2 R)**. V = 4.2 V (full pack). R = 2 cells in parallel + BMS FETs + 60 mm pack lead + XT30 + 180 mm
pigtail + fuse + capacitor ESR >= about 25 mohm [est]. C = X1203 battery-side capacitance, unknown: 100-1000 uF bracket
[unconfirmed; Geekworm publishes no schematic].
- 100 uF: 0.035 A2s; 470 uF: 0.17 A2s; 1000 uF: **0.35 A2s** (peak <= 4.2 / 0.025 = 170 A for tens of us, lower in
  practice because of lead inductance). Then the X1203 soft-starts its boost into the Pi: about 8 A for 10 ms = 0.64 A2s [est].
- Against 68.8 A2s (A/B): <= 1 %. A pulse-cycle derating of 22 % of melting I2t for 100,000 pulses (29 % for 10,000) is
  attributed to Littelfuse's fuse-holder/pulse guidance in a search summary only [unconfirmed, secondary]; even 10 %
  (6.9 A2s) leaves a factor of about 10. C (12 A, 45.2 A2s) also passes. **Inrush is not a selection constraint.**

### 1.4 Fault interruption (estimate)
Prospective current for a pigtail short: 4.2 V / (about 20-35 mohm) = **120-200 A** [est: cell IR class figures, BMS
FETs, leads]; below the 300 A @ 32 VDC interrupting rating of A and B, at a far lower voltage than rated. Adiabatic melt
time at 150 A about 68.8 / 150^2 = 3 ms [est]. A pack BMS short-circuit trip (typically sub-ms) acts first; the fuse is
the second layer for a BMS that fails or does not see the fault (e.g. a 20-40 A resistive fault below its trip). The fuse
protects only the pigtail and the X1203 input; the 60 mm pack lead and the XT30 still rely on the BMS alone.

### 1.5 Fit (box arithmetic; layout.py keep-outs; not a CAD run)
Fused splice [est]: body 7.11 + 2 x (1.5 mm lead stub + 5 mm lap joint on the 18 AWG conductor) = **about 20 mm rigid**;
adhesive-lined 3:1 sleeve (recovered wall about 0.9 mm [est]) over the body gives **OD about 5.0 mm**, about 28 mm long
with 4 mm grip on the insulation each end. The black 18 AWG conductor (OD about 2.2 mm [est]) runs beside it.

| Space | Box | Cross-section check | Length check | Verdict |
|---|---|---|---|---|
| `ko_pig_drop` (vertical) | x -43..-36, y -12..-5, z -12.3..2.7 = **7 x 7 x 15** | 5.0 + 2.2 mm side by side = 7.2 mm > 7.0 square side; **diagonal fit only** (centres 2.5/2.5 and 5.9/5.9: 4.81 mm apart >= 3.6 needed), 0 mm spare | 20 mm rigid > 15 mm: 5 mm overhangs into `ko_xt30` where the pigtail must turn into the XT30 female; fits only with 3.5 mm laps (15.1 mm rigid) | **marginal**; also leaves the drop-to-XT30 length of pigtail unfused |
| `ko_xt30` with the XT30 pair | x -65..-37, y -10..10, z -36.5..-12.5 = **28 x 20 x 24**; `xt30_pair` box x -63..-37, y -5.1..5.1, z -20..-14.8 (26 x 10.2 x 5.2) | free: 16.5 mm under the pair over the full 28 x 20; 4.9 mm strips beside it (y -10..-5.1 / 5.1..10) | 28 mm > 20 mm rigid (lying along x under the pair) | **fits with margin**; the sleeve rides in the slack that moves when the pack and junction are pushed up at step 10 (`pack_in`, 80 mm travel): hand-fit check |
| Floor hole `FLOOR_HOLES['pigtail']` | 11 x 9 | 5.0 mm sleeve passes (the XT30 already has to) | n/a | pass |

### 1.6 Recommendation (fuse)
**Littelfuse 0251015.MXL (15 A, 32 V, very fast-acting, PICO II), sleeved within about 25 mm of the XT30 female, lying
in `ko_xt30` under or beside the XT30 pair.** Reasons: (1) the only option with a published cold resistance and an
explicit maker derating rule, and 8.6 A is 78 % of its derated 40 C allowance; (2) 300 A DC interrupting rating above
the estimated 120-200 A fault; (3) inrush <= 1 % of its I2t; (4) 3.18 x 7.11 mm body, 7 lb lead pull, in stock (8,035)
at USD 1.45; (5) near the XT30 it fuses the whole pigtail, and `ko_xt30` has room that the 7 x 7 drop lacks. The 12 A
part (C) is rejected (1-3 % margin, more loss). FXG-15A (B) is a second source with the same I2t, but no published
resistance. Not a PTC: a polymer PTC holding 8.6 A at 40-60 C is a large part and adds resistance [not pursued].

Knock-on effects (for the main session to decide): **G-W5** drop budget pack-to-pads at 8.6 A becomes about
0.095 + 0.040 = **0.135 V against the 0.15 V limit (15 mV left)** [est]. The fuse also dissipates 0.33-0.35 W inside its
sleeve, so add a thermocouple on the fuse sleeve in G-W5 (a)/(b); I would suggest <= 70 C (the adhesive liner softens
above that) [proposal]. +2 solder joints, +1 BOM line (fuse, order 2), + adhesive heat-shrink about 4.8 mm 3:1. The X1203
cut-off arrives about 0.04 V earlier at peak load.

### 1.7 Alternative: BMS-only protection; text a pack BMS must meet (proposed requirement R-PACK-BMS)
1. Continuous discharge >= 10 A (as D2-13), with no trip at 8.6 A continuous at 25-60 C.
2. Discharge over-current protection: trip threshold **12-25 A**, delay **5-50 ms**, stated as numbers.
3. Short-circuit protection: threshold **<= 100 A**, response **<= 1 ms**, but no trip on the X1203 plug-in surge
   (estimated up to about 170 A peak for under 0.1 ms, 1.3). Many protection ICs trip on capacitive inrush, so G-W1 adds
   **10 plug-ins of the X1203 stack at a full pack with no trip** [proposal].
4. Recovery behaviour (load removal or charger) stated; UVP 2.5-3.0 V (as G-W1); OVP 4.25-4.30 V.
5. Evidence: the pack builder's written spec or the protection IC + MOSFET + sense-resistor part numbers, not a listing
   headline ("15 A BMS").
6. **Single fault**: the BMS is one layer. If its MOSFETs fail shorted (a common failure mode for power MOSFETs
   [general knowledge, unconfirmed here]) about 120-200 A is available into 18 AWG. So BMS-only is acceptable only if
   the pack also contains a second element (a fuse or fusible link in the pack, or a second-level protector), else the
   pigtail fuse of 1.6 is fitted.

## 2. Task 2: R-EVF-REG device (4.55 V class LDO, 0.30 A)

Requirement used (WIRING s4.8): VIN 4.715-5.355 V; band **4.39-4.71 V** (initial + line + load 0-0.30 A + temperature,
TJ to 110 C); dropout **<= 0.30 V max at 0.30 A, hot**; current limit >= 0.5 A, no fold-back below 0.30 A, soft start;
operating VIN >= 5.5 V; installed thermal resistance <= 150 C/W; reverse current reported; carrier <= 16 x 7.5 x 4.5 mm.
Dissipation for row 7 at the asked point: **P = (5.36 - 4.55) x 0.30 = 0.243 W**.

### 2.1 Candidates
| | **A. TI TLV75801P** (adjustable, 500 mA) | B. Torex **XC6220B45BPR-G** (fixed 4.55 V, 1 A) | C. Torex XC6210B45APR-G (fixed 4.55 V, 700 mA) | D. TI TPS73601 (adjustable, NMOS, 400 mA) |
|---|---|---|---|---|
| Orderable 4.5x V | adjustable only: TLV75801PDBVJ / DBVT (SOT-23-5), TLV75801PDRVR (WSON-6 2 x 2) | yes: code (4) = "B" means x.x5 V; type B is the standard type (A/C/D semi-custom) | yes: (4) = "A" means x.x5 V | adjustable: TPS73601DBVR (SOT-23-5), DCQR (SOT-223-6), DRBR; fixed list stops at 4.3 V (TPS73643) |
| VIN (operating / abs max) | 1.5-6.0 / 6.5 V | 1.6-6.0 / 6.5 V | 1.5-6.0 / 6.5 V | 1.7-5.5 / 6.0 V ("must never operate at a dc voltage greater than 5.5V") |
| Output accuracy | VFB 0.55 V: +-0.7 % at 25 C, **+-1 % TJ -40..85 C, +-1.5 % TJ -40..125 C** (resistors excluded) | HS mode (30 mA, VIN = 5.55 V, 25 C): **4.5045-4.5955 V (+-1 %)**; PS mode (0.1 mA): 4.459-4.641 V (+-2 %) | 4.459-4.641 V (+-2 %, 25 C, 30 mA, VIN 5.55 V) | +-1 % over VIN, IOUT 10-400 mA and TJ -40..125 C (VIN >= VOUT + 0.5 V), resistors excluded; VFB 1.198-1.210 V at 25 C |
| Line / load regulation | line 7.5 mV max (VOUT+0.5 <= VIN <= 6 V); load 0.030 V/A **typ only** | line 0.20 %/V max (VIN >= VOUT+0.5); **load 45 mV max, 10-300 mA** | line 0.20 %/V max, specified only for 5.5 <= VIN <= 6.0 V at VOUT >= 4.5 V; load 60 mV max, **1-100 mA only** | in the +-1 % figure |
| Temperature coefficient | inside the accuracy spec | +-100 ppm/C **typ only** (5.0 V curve: -0.46 % at 85 C [graph]) | +-100 ppm/C typ only | inside the accuracy spec |
| Dropout (max) | **130 mV at 500 mA, TJ -40..125 C** (3.3-5.5 V outputs) | **85 mV at 300 mA** (25 C; typ 53); 5.0 V curve about 60-70 mV at 300 mA, 25-85 C [graph] | max given only at 30 mA (23 mV) and 100 mA (75 mV); at 300 mA **typ** about 0.15 V (25 C), 0.17 V (85 C) [graph, 5.0 V part]; **no max at 0.3 A** | 200 mV at 400 mA over temperature (typ 75) |
| Current limit / short | 530 min, 720 typ; brick-wall above 0.4 x VOUT, then fold-back to 350 mA typ at 0 V | 1005 mA min; fold-back to 180 mA typ at short; inrush limited to 700 mA max for about 1 ms at start | 700 min, 800 typ; fold-back to **50 mA** at short [curve stays above a 15 ohm load line, graph] | 400 min (legacy silicon) / 500 (new), 450 mA short; fold-back below 0.5 V |
| Soft start / protection | built-in monotonic soft start, tSTR 500 us; TSD 170 C; UVLO | inrush prevention; TSD 150 C | none listed beyond fold-back | startup 600 us typ; TSD 160 C |
| Reverse current | **no blocking**; body diode; "external protection must be used" if reverse current is expected (Schottky OUT->IN shown); abs max VOUT <= VIN + 0.3 V; 95 ohm active pull-down when disabled / in UVLO | **no blocking** (block diagram: parasitic diode VOUT->VIN); type B adds a 460 ohm CL discharge switch, active only while VIN is present and CE is low | **no blocking** (parasitic diode) | blocks (10 uA max, **fixed versions only**) **only if EN is driven low before VIN is removed**; with EN tied to IN "reverse current flow" can occur; for TPS73601 reverse current can flow when VFB > VIN + 1.0 V |
| Capacitors | CIN >= 1 uF; COUT 1-220 uF (>= 0.47 uF after derating), X5R/X7R | for 3.55-5.00 V: **CIN 10 uF + CL >= 10 uF** (or CIN 22 / CL 6.8, or CIN 4.7 / CL 47); low bias-dependence | CIN 1 uF, CL >= 1 uF | none required; 0.1-1 uF input suggested |
| Package | SOT-23-5 2.9 x 2.8; WSON-6 2 x 2 (pad) | SOT-89-5 (4.5 x 2.5 body) | SOT-89-5 | SOT-23-5; SOT-223-6 6.5 x 7.06 (too wide for a 7.5 carrier with pads) |
| RthJA (maker's board) | DBV **176.9**, DRV **80.3 C/W** (JEDEC 2s2p) | **76.9 C/W** (40 x 40 mm FR-4, 50 % Cu both faces, Tj max 125 C) | 76.9 C/W (1300 mW, 40 x 40 board) | DBV 185 / DCQ 76 (new silicon); legacy 222 / 119 |
| Rise at 0.243 W | DBV 43 C (small carrier 200-250 C/W [est]: 49-61 C); DRV 20 C (carrier 120-150 [est]: 29-36 C) | 19 C (carrier 120-150 [est]: 29-36 C) | as B | DBV 45 C; DCQ 18 C |
| Stock / price | DigiKey: **DBVJ 5,567 at USD 0.33; DBVT 2,357 at 1.06; DRVR 54,465 at 0.35**; DBVR 0 (expected 17 Nov 2026); TI store out of stock | DigiKey: Active, **0 in stock**, USD 0.53 (reel price, MOQ not shown); Avnet: 112-week factory lead on B45BMR/B45BER [search summary]; not found on LCSC | DigiKey: Active, **0 in stock, MOQ 6,000**, USD 0.42 | DigiKey TPS73601DBVR USD 2.51 (stock not captured) |
| Datasheet | [D3] SBVS351D, Oct 2023 | [D4] ETR0341-013 | [D5] ETR0317_007 | [D6] SBVS038X, May 2025 |

**Rejected:** Nisshinbo RP111 (500 mA): VIN 1.4-5.25 V ("When Input Voltage is 5.5V, the total operational time must be
within 500hrs") and outputs 0.7-3.6 V, so it fails row 5 [D7]; the RP115 family is in the same 5.25 V class [search
summary, unconfirmed]. Microchip MCP1826: standard fixed outputs 0.8/1.2/1.8/2.5/3.0/3.3/5.0 V, no 4.5x [search summary];
its ADJ version was not analysed. Diodes AP7361C: fixed options seen 1.0-3.3 V, adjustable 0.8-5.0 V, 360 mV typ at 1 A
[search summary]; not analysed. AP2112 and MIC5219: not checked. **Clones:** "XC6220" parts from AOSSEMI (+-2.5 %,
500 mA abs max, different datasheet) and TDSEMIC are sold under Torex-style numbers; buy Torex only from an authorised
distributor.

### 2.2 Output band against 4.39-4.71 V (row 2)
- **A. TLV75801P, R1 = 11.5 kohm, R2 = 1.58 kohm (E96, 0.1 %)**: VOUT = 0.55 x (1 + 11.5/1.58) = **4.553 V**. Divider
  current 0.35 mA. Terms: +-1.5 % (TJ to 125 C) = +-68 mV; resistor ratio +-0.2 % x 7.28/8.28 = +-8 mV; IFB 0.1 uA max
  x 11.5 k = 1.2 mV; line 7.5 mV; load 0.03 V/A x 0.3 A = 9 mV (typ). **Band 4.459-4.638 V: 69 mV above 4.39, 72 mV
  below 4.71.** TI's limit R1 + R2 <= VOUT / (100 x IFB) = 4.55 Mohm is met. Same ratio at 10x values (115 k / 15.8 k)
  adds up to 11.5 mV of IFB error; prefer the low values.
- **B. XC6220B45BPR-G**: HS 4.5045-4.5955 - load 45 mV - line 0.2 %/V x 0.84 V x 4.55 = 7.6 mV - temperature +-100 ppm/C
  x 85 K = +-39 mV (typ) gives low **4.413 V** (23 mV margin); high, PS mode at no load 4.641 + 7.6 + 39 mV = **4.688 V**
  (22 mV margin). Inside, but the temperature term is typical only. [to confirm hot at G-W13 (a)]
- **C. XC6210B45APR-G**: 4.459 - >= 60 mV load (not specified beyond 100 mA) - 39 - 8 mV gives **<= 4.352 V: fails row 2 on
  paper**, and row 3 has no maximum. Its line regulation is not specified below 5.5 V input. Superseded by B.
- **D. TPS73601, R1 = 45.3 k, R2 = 16.2 k** gives 4.571 V nominal (E96 cannot land nearer 4.55 V at a sensible R1||R2);
  +-1 % +-0.15 % +-13.6 mV IFB (0.3 uA max) gives 4.505-4.637 V. Passes, but rows 4/5/8 are weak (below).

Low-input check (row 3, VIN 4.715 V at 0.30 A): A regulates if VIN >= 4.553 + 0.130 (max at 500 mA) = 4.683 V, so **it
stays in regulation with 32 mV to spare**. B needs 4.55 + 0.085 (25 C max) = 4.635 V, or about 4.67 V hot [est x1.35],
so it is in regulation. D may enter dropout: VOUT >= 4.715 - 0.200 = 4.515 V, which is still in band. Accuracy terms
for A, B and D are specified only for VIN >= VOUT + 0.5 V = 5.05 V; below that, use G-W13 (a)/(b).

### 2.3 Rows 4, 5, 7, 8 per candidate
- Row 4 (>= 0.5 A, no fold-back below 0.30 A): A yes (530 min; fold-back floor 350 mA typ, only below 1.82 V);
  B yes (1005 min; 180 mA floor, 700 mA start-up cap); C fold-back to 50 mA (resistive 0.3 A start relies on a typical
  curve); D 400 mA min on legacy silicon (fails ">= 0.5 A" strictly) and TI warns "Current limit foldback can prevent
  device start-up under some conditions".
- Row 5 (VIN >= 5.5 V): A, B, C 6.0 V; D exactly 5.5 V with a 6.0 V absolute maximum (little room for USB transients).
- Row 7 (<= 150 C/W installed): B and C in SOT-89-5 on a copper carrier [est 120-150]; A only in WSON-6 (DRV) or on a
  copper-rich carrier. With DBV on a small carrier [est 200-250 C/W] the rise is 49-61 C, so TJ is 104-116 C at 55 C
  air: below the 125 C limit but over the row-7 bound. G-W13 (f) decides.
- Row 8 (reverse): no candidate blocks in this circuit (EN/CE tied to VIN, VBUS removed without warning). Body-diode
  backfeed into the Pi VBUS can come only from the EVF board's capacitance (small) or the HDMI pin-19 path (G-W7 <= 50 mA).
  G-W13 (e) (VIN open, 4.90 V via 10 ohm) should read about IQ + divider, well under 1 mA [est], because the open VIN node
  charges and stops conduction. **G-W7 (c) re-run with the regulator fitted is the deciding test.** For A, add to G-W13
  (e) a check that the 95 ohm UVLO pull-down does not sink from EXT+ while VBUS decays [unconfirmed whether it can turn on
  with VIN about 0 V]. D blocks only if EN is driven low before VBUS drops (e.g. from a GPIO): not D2's wiring.

### 2.4 Pre-assembled carrier
None found. Two searches (Pololu/Adafruit/SparkFun/AliExpress terms; TLV758/TPS73601/XC6220 module terms) returned only
AMS1117-3.3 modules (wrong voltage, about 1 V class dropout [search summary]) and a 5 V NCP3334 board (20 x 40 mm). The
carrier stays a hand-assembled or ordered small PCB (D2-16P); with A it also carries the two divider resistors.

### 2.5 Recommendation (LDO)
**TI TLV75801P: TLV75801PDBVJ (SOT-23-5, cut tape, in stock) for a hand-soldered carrier, or TLV75801PDRVR (WSON-6) if
the carrier is reflowed. R1 = 11.5 kohm, R2 = 1.58 kohm, 0.1 % 0603; CIN 2.2-4.7 uF and COUT 4.7 uF X7R 0805 16 V (TI
minimum 1 uF in, 0.47 uF derated out, 220 uF out max); EN tied to IN. VOUT 4.553 V nominal.**
Reasons: the only candidate whose datasheet maxima/minima over TJ -40..125 C cover rows 2-5 with margin (band
4.459-4.638 V; dropout 130 mV max at 500 mA, so regulation holds down to 4.683 V input; current limit >= 530 mA;
VIN 6.0 V); soft start; and it is buyable now in single quantities. Costs against the fixed-part plan: **+2 resistors
(+1 BOM line, +4 SMD joints)**; row 7 needs the WSON package or a copper-rich carrier; no reverse blocking (row 8; as for
every candidate).
**Fixed-voltage alternative: Torex XC6220B45BPR-G (SOT-89-5)**, if it can be obtained: it meets rows 1-7 on paper
(temperature term typical only), uses fewer parts, and has better thermals. But it is not stocked: 0 at DigiKey, a
112-week factory lead on sister codes, likely reel MOQ. It needs CIN 10 uF + CL 10 uF low-bias-loss ceramics
(1206 25 V class [est]), not the 0805 assumed in D2-16C. **Do not use XC6210** (no 0.3 A dropout maximum, fails row 2
on paper, MOQ 6,000). BOM D2-16R/C/P text and G-W13 apply unchanged apart from the device; G-W13 (a) should add the
0 A point to catch the divider and PS-mode behaviour.

## 3. Sources (read 2026-10-05)
- [D1] Littelfuse 251 Series PICO II datasheet, revised VL 09/26/24, read from verbatim copy
  https://mrsdprojects.ri.cmu.edu/2025teamb/wp-content/uploads/sites/84/2025/05/Littelfuse-Fuse-251-253-Datasheet.pdf ;
  official link (403 to fetch) https://www.littelfuse.com/assetdocs/fuse-251-datasheet?assetguid=f47a0bb7-8ede-4679-9646-7114c3787688
- DigiKey 0251015.MXL F2352-ND https://www.digikey.com/en/products/detail/littelfuse-inc/0251015-MXL/776752 ;
  0251012.MXL F2351-ND https://www.digikey.com/en/products/result?keywords=0251012.MXL ; RS 542-1216P
  https://uk.rs-online.com/web/p/non-resettable-fuses/5421216P
- [D2] OptiFuse FXG datasheet Rev H 10/2018 https://www.optifuse.com/optifuse_ecommerce_tools/datasheets/FXG.pdf ;
  DigiKey search https://www.digikey.com/en/products/result?keywords=FXG-15A ; Jameco
  https://www.jameco.com/z/FXG-15A-OptiFuse-Circuit-Protection-Fuse-Thru-Hole-2-7x7-3mm-Fast-72V-15A_2708495.html
- Pulse derating (secondary, search summary only): Littelfuse fuseholder re-rating document
  https://WWW.littelfuse.com/technical-resources/~/media/Files/Littelfuse/Technical%20Resources/Documents/Reference%20Documents/fuseholder_rerating.pdf
- [D3] TI TLV758P SBVS351D (Oct 2023) https://www.ti.com/lit/ds/symlink/tlv758p.pdf ; DigiKey
  https://www.digikey.com/en/products/result?keywords=TLV75801P ; TI store
  https://www.ti.com/product/TLV758P/part-details/TLV75801PDBVR
- [D4] Torex XC6220 ETR0341-013, read from copy https://robu-prod-media.s3.ap-south-1.amazonaws.com/uploads/2024/01/66.pdf ;
  official https://product.torexsemi.com/system/files/series/xc6220.pdf (403); DigiKey
  https://www.digikey.com/en/products/result?keywords=XC6220B45 ; Avnet
  https://www.avnet.com/americas/product/torex/xc6220b45bmr-g/evolve-51196536/ ; clone sheet (AOSSEMI Ver 1.0G)
  https://www.ickey.cn/static-pf/datasheet/44/02/0794/4402079405d6418a19d28d3b90d5f5dd.pdf
- [D5] Torex XC6210 ETR0317_007, read from copy https://cdn.eicom.ru/media/PDF/608471.pdf ; official (DigiKey link, 403)
  https://product.torexsemi.com/system/files/series/xc6210.pdf ; DigiKey https://www.digikey.com/en/products/result?keywords=XC6210B45
- [D6] TI TPS736 SBVS038X (May 2025) https://www.ti.com/lit/ds/symlink/tps736.pdf ; DigiKey
  https://www.digikey.com/en/products/result?keywords=TPS73601DBVR
- [D7] Nisshinbo RP111x EA-241-190523 https://www.nisshinbo-microdevices.co.jp/en/pdf/datasheet/rp111-ea.pdf
- MCP1826 options (search summary) https://www.mouser.in/microchip-mcp1826-mcp1826s-regulators/ ; AP7361C (search
  summary) https://www.lcsc.com/product-detail/C5564289.html ; X1203 page (no schematic) https://geekworm.com/products/X1203
