# SPDX-License-Identifier: MIT
"""GS8 D2 release v1: bill of materials generator (plain Python, no CadQuery).

    python electronics/gs8-d2-v1/make_bom.py        # writes BOM.md and bom.csv next to this file

Sources:
- cad/gs8-d2-v1/layout.py (COTS, CABLES, PT, PARTS) and make_tables.printed_rows() (printed volume and mass: the build's
  print manifest when present, else the layout estimate);
- outputs/bom-release-2026-09-25/prices.json: a line is priced from it only where the part (or its exact class) is
  the same; the price and its basis are carried with the id, date and confidence;
- every other price is an ESTIMATE (a planning figure in USD written in LINES below, not a quote, not looked up), or
  blank (unpriced). Nothing was bought; no cart was used.
SGD conversion follows the prices.json legend: included / as_displayed as is; excluded x (1 + GST);
usd_list and estimates USD x fx x (1 + GST).
"""
import csv
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
CAD = os.path.join(ROOT, 'cad', 'gs8-d2-v1')
sys.path.insert(0, CAD)
import layout as L  # noqa: E402
import make_tables as MT  # noqa: E402

PRICES = os.path.join(ROOT, 'outputs', 'bom-release-2026-09-25', 'prices.json')

# r2 (R4): counts that other owners change are read from the layout, never typed here.
# PT screws: every layout.SCREWS entry is a PT 3.0 x 12 PH1 unless it says otherwise (R1's keeper screws included).
# r5: by SCREWS 'kind' (layout.pt_screw_ids()); the lens-collar M3 rows are counted apart (M3_* below)
_PT = L.pt_screw_ids() if hasattr(L, 'pt_screw_ids') else [
    s['id'] for s in L.SCREWS if str(s.get('type', s.get('spec', 'PT'))).upper().startswith('PT')]
PT_USED = len(_PT)
PT_SPARE = 4
PT_IDS = ', '.join(_PT)
# r5 (J7-R lens collar, FASTENER-POLICY I): kind M3 rows -> inserts (tub L 4.0 / collar lug L 5.7), screws by length,
# ISO 7089 washers; spares are planning figures (an insert set crooked is drilled out, not re-used)
_M3 = [s for s in L.SCREWS if s.get('kind') == 'M3']
M3_IDS = ', '.join(s['id'] for s in _M3)
M3_INS_TUB = sum(1 for s in _M3 if (s.get('insert') or {}).get('part') == 'tub')
M3_INS_LUG = sum(1 for s in _M3 if (s.get('insert') or {}).get('part') == 'lens_collar')
M3_BY_LEN = {n: sum(1 for s in _M3 if s['length'] == n) for n in sorted({s['length'] for s in _M3})}
M3_WASHERS = sum(1 for s in _M3 if s.get('washer'))
M3_SPARE = dict(ins=2, screw=1, washer=2)
# bench solder joints (WIRING s7, ASSEMBLY step 1); OPTIONS (a) would remove '18/24 switch lugs'
# r3: the X1203 kit fasteners are counted from layout.X1203_KIT, separately from the PT body screws
import re  # noqa: E402
KIT_SCREWS = int(re.match(r'\s*(\d+)\s*x', L.X1203_KIT['screws']).group(1))
KIT_STANDOFFS = int(re.match(r'\s*(\d+)\s*x', L.X1203_KIT['standoff']).group(1))
# r3 option C (WIRING s4.8): the regulated EVF feed replaces the diode splice (2 joints) by a carrier with the LDO
# (5 SMD joints) and 2 MLCC (4) plus 4 wire joints; a user decision, so it is a delta here, not in SOLDER_JOINTS.
# r4: with the primary candidate TLV75801P (adjustable) the carrier also holds 2 divider resistors (+4 SMD joints)
REG_C_JOINTS_DELTA = (5 + 2 * 2 + 2 * 2 + 4) - 2
SOLDER_JOINTS = {'pigtail to X1203 pads': 2, 'pigtail fuse splice (r4, W-10)': 2,
                 'EVF 5 V lead (diode splice + PH plug)': 3, 'encoder A0 blob': 1, '18/24 switch lugs': 2,
                 'EVF board pigtail (Rev I)': 2}

# section, line id, item, qty, unit, SKU or class, supplier, prices.json id, estimate USD (unit), COTS/cable id, note
S_EL, S_CB, S_FA, S_CO, S_TO = ('A. Electronics, optics, power', 'B. Cables and leads', 'C. Fasteners',
                                'E. Consumables', 'F. Tools and accessories (not in the camera)')
LINES = [
    (S_EL, 'D2-01', 'Raspberry Pi 5, 8 GB (4 GB is enough; the 8 GB line is the priced one)', 1, 'ea', 'SC1432 (8 GB, prices.json); layout pn SC1111/SC1112', 'Cytron SG', 'CMP-01', None, 'pi5', ''),
    (S_EL, 'D2-02', 'Raspberry Pi Active Cooler', 1, 'ea', 'SC1148', 'MakerSupplies SG', 'CMP-02', None, 'cooler', 'fan lead plugs into the Pi FAN header'),
    (S_EL, 'D2-03', 'Geekworm X1203 UPS board (pogo pins, 1S input, 5.1 V 5 A) with its M2.5 standoff kit', 1, 'ea', 'X1203', 'Geekworm', None, 30.0, 'x1203', 'kit: %d standoffs + %d M2.5 screws (layout X1203_KIT; not PT body screws); bench gate G-W2' % (KIT_STANDOFFS, KIT_SCREWS)),
    (S_EL, 'D2-04', 'microSD card, A2 class, 32-64 GB (OS only, front slot)', 1, 'ea', 'A2 class', 'any', None, 10.0, 'microsd', 'boot medium; out of the Pi for steps 3-4, pushed home at step 5'),
    (S_EL, 'D2-05', 'Raspberry Pi Global Shutter Camera (IMX296) with its C-CS adapter', 1, 'ea', 'SC0926', 'Cytron SG', 'CMP-04', None, 'gs_camera', 'the 5 mm C-CS adapter ships with it (c_cs_adapter); r5: so do the tripod block and its 2 screws, removed at bench B0 and bagged (not in the body)'),
    (S_EL, 'D2-06', 'C-mount lens: Kowa LM6HC 6 mm f/1.8 1 in (default, 215 g)', 1, 'ea', 'LM6HC', 'Kowa distributor', None, None, 'lens', 'LENS decision pending (user review); alternative D2-06b'),
    (S_EL, 'D2-06b', 'Alternative lens: Fujinon HF6XA-5M 6 mm (100 g); order instead of D2-06', 0, 'ea', 'HF6XA-5M', 'Fujifilm distributor', None, None, None, 'balance: CoM moves about 10 mm rearward (concept table)'),
    (S_EL, 'D2-07', 'EVF-A display kit: Hicenda HMX039 0.39 in 1024x768 micro-OLED + HDMI board (option "Display+HDMI Board+Prism")', 1, 'kit', 'Hicenda Tindie kit', 'Hicenda (Tindie)', 'EVF-01', None, 'hmx039', 'covers hmx039, evf_board and oled_flex'),
    (S_EL, 'D2-08', 'EVF-A eyepiece: Display Components 0PE039-16X glass eyepiece', 1, 'ea', '0PE039-16X', 'Display Components (Tindie)', 'EVF-02', None, 'eyepiece', ''),
    (S_EL, 'D2-09', 'SanDisk Extreme PRO USB 3.2 solid state flash drive, 256 GB', 1, 'ea', 'SDCZ880-256G', 'any', None, 40.0, 'usb_stick', 'gate G-W10 (100 MB/s sustained, warm)'),
    (S_EL, 'D2-10', 'Adafruit 5880 I2C STEMMA QT rotary encoder (encoder pre-soldered)', 1, 'ea', 'Adafruit 5880', 'Adafruit / DigiKey', None, 8.0, 'encoder', 'bridge A0 -> 0x37'),
    (S_EL, 'D2-11', '18/24 selector: mini rotary switch with adjustable stop, 6.35 mm shaft, nut + washer', 1, 'ea', 'Lorlin CK1049 class', 'any', None, 6.0, 'switch_1824', 'set the stop to 2 positions; dims are estimates (G-HDMI note)'),
    (S_EL, 'D2-12', 'Run button: pre-wired momentary, red cap, female-socket leads', 1, 'ea', 'Squid Button (non-latching) class', 'The Pi Hut', None, 4.0, 'run_button', 'lead about 250 mm'),
    (S_EL, 'D2-13', '1S2P 18650 pack: 2 high-drain cells (>= 10 A class), BMS >= 10 A, 18 AWG lead, XT30U male, pull ribbon', 1, 'ea', '1S2P custom (Molicel P28A / Samsung 35E class)', 'pack builder', None, 30.0, 'pack', 'gate G-W1; the order states R-PACK-BMS (WIRING s4.7) in numbers; +2 joints if the XT30 is not fitted'),
    (S_EL, 'D2-14', 'XT30U connector pair (female for the pigtail; male if the pack lacks one)', 2, 'pair', 'Amass XT30U', 'any', None, 1.0, 'xt30_pair', '1 spare pair'),
    (S_EL, 'D2-14F', 'Inline fuse 15 A, very fast, axial PICO II, 32 V (pigtail + conductor near the XT30 female; W-10, r4)', 2, 'ea', 'Littelfuse 0251015.MXL (DigiKey F2352-ND)', 'DigiKey', None, 1.45, None, '1 spare; USD 1.45 is the DigiKey listing seen 2026-10-05 (8,035 in stock), not a quote; gates G-W1, G-W5'),
    (S_EL, 'D2-15', 'Hand strap, 12 mm webbing with buckle', 1, 'ea', 'class', 'any', None, 8.0, 'strap', 'through the 2 base and 2 heel slots'),
    (S_EL, 'D2-16', 'Schottky diode 1N5817 (EVF 5 V lead, W-3; baseline feed)', 2, 'ea', 'MCC 1N5817-TP', 'DigiKey SG', 'PRT-05', None, None, '1 spare; deleted under option C (WIRING s4.8)'),
    (S_EL, 'D2-16R', 'Candidate (option C, WIRING s4.8; qty 0 until the user adopts it or G-W6 fails): LDO, adjustable 500 mA, set to 4.553 V by D2-16D (R-EVF-REG band 4.459-4.638 V from datasheet limits)', 0, 'ea', 'TI TLV75801PDBVJ (SOT-23-5) or TLV75801PDRVR (WSON-6, reflow)', 'DigiKey', None, 0.33, None, 'replaces D2-16; order 2 (1 spare); r4 desk research, listing USD 0.33 seen 2026-10-05; fixed alternative Torex XC6220B45BPR-G (0 stock, long lead); NOT XC6210 and NOT a generic 5 V regulator; gate G-W13'),
    (S_EL, 'D2-16D', 'Candidate (option C): divider resistors for D2-16R, R1 11.5 kohm + R2 1.58 kohm, 0.1 %, 0603', 0, 'ea', 'thin film 0.1 % class', 'any', None, 0.3, None, 'order 4 (1 set spare); not needed with the fixed XC6220B45'),
    (S_EL, 'D2-16C', 'Candidate (option C): MLCC CIN 2.2-4.7 uF + COUT 4.7 uF, X7R, 16 V, 0805 (TLV75801P; the XC6220 would need 10 uF + 10 uF, 1206 25 V)', 0, 'ea', 'class', 'any', None, 0.1, None, 'order 4 (2 spare)'),
    (S_EL, 'D2-16P', 'Candidate (option C): small SOT-89 carrier PCB with copper (est. 16 x 7.5 x 4.5 sleeved envelope inside ko_5v_up by box arithmetic; carrier not measured)', 0, 'ea', 'SOT-23-5 / WSON-6 carrier with copper pour (custom; no 4.5 V module found)', 'any', None, 1.0, None, 'order 2 (1 spare); copper-rich (row 7: SOT-23-5 is 177 C/W on the TI board); thin-wall sleeve, no adhesive heat-shrink over the LDO'),
    (S_CB, 'D2-20', 'Pi 5 camera cable Standard-Mini 22-to-15 pin, 200 mm', 1, 'ea', 'official 200 mm', 'MakerSupplies SG', 'HAR-07', None, 'fpc', 'priced from the 300 mm SC1129 listing (same family); order 200 mm'),
    (S_CB, 'D2-21', 'micro-HDMI D-D 200 mm (+10/-0), OD 3.0, Pi end 90 deg up, board end right-angle (-Y exit)', 1, 'ea', 'EVF-SELECTION A3 class', 'any', 'HAR-08', 12.0, 'hdmi', 'gates G-HDMI (plug <= 8.5 mm), G-W7'),
    (S_CB, 'D2-22', 'USB-A male to 2-wire lead, 24-26 AWG, about 200 mm', 1, 'ea', 'class', 'any', None, 3.0, 'usb_5v', '+ D2-16 diode + D2-23 junction'),
    (S_CB, 'D2-23', 'JST PH 2-pin wire-to-wire pigtail pair, pre-crimped 24-26 AWG', 2, 'pair', 'PHR-2 class', 'any', 'HAR-04', 1.0, None, 'EVF 5 V junction (W-4); 1 spare'),
    (S_CB, 'D2-24', 'Adafruit 4397 STEMMA QT to female sockets, 150 mm', 1, 'ea', 'Adafruit 4397', 'Adafruit / DigiKey', None, 1.0, 'qt', ''),
    (S_CB, 'D2-25', '2-way Dupont female to JST PH 2-pin lead, 200 mm (header side of the 18/24 lead)', 1, 'ea', 'class', 'any', None, 1.5, 'fps_lead', 'concept tally 200 mm; plugged on pins 33/34 at step 4'),
    (S_CB, 'D2-27', 'JST PH 2-pin wire-to-wire pigtail pair, 50 mm (18/24 inline junction, switch side soldered)', 1, 'pair', 'PHR-2 class', 'any', 'HAR-04', 1.0, None, 'the step-8 joint of the 18/24 lead (FIXER A-F1)'),
    (S_CB, 'D2-26', 'Silicone wire 18 AWG, red + black, 1 m each', 1, 'set', 'class', 'any', 'HAR-W18', 4.0, 'pigtail', 'pigtail 180 mm + spare'),
    (S_FA, 'D2-30', 'PT 3.0 x 12 thread-forming screw for plastics, pan head, PH1 (EJOT PT K30x12 WN 1411 / Delta PT 30x12 class)', PT_USED + PT_SPARE, 'ea', 'WN 1411 class', 'any', None, 0.15, 'pt_screws', '%d used (%s) + %d spare; count from layout.SCREWS (FASTENER-POLICY A)' % (PT_USED, PT_IDS, PT_SPARE)),
    (S_FA, 'D2-31', '1/4-20 UNC hex nut, steel (tripod socket)', 1, 'ea', 'ISO 4032 class', 'any', None, 0.3, 'tripod_nut', 'pressed into the base pocket'),
    (S_FA, 'D2-32', 'Insert fallback: M3 x 5.7 brass heat-set insert (pack)', 1, 'pack', 'CNC Kitchen M3 standard', 'Printed Solid (US)', 'INS-M3', None, None, 'only for a stripped boss (FASTENER-POLICY E)'),
    (S_FA, 'D2-33', 'Insert fallback: M3 x 10 pan head A2, ISO 7045 cross recess PH1 (no hex: straight-driver rule)', PT_USED, 'ea', 'ISO 7045 class', 'any', None, 0.1, None, 'with D2-32 only; 1 per PT boss'),
    # r5 (J7-R, FASTENER-POLICY I): lens-collar hardware (layout COTS m3_hw; counts from the kind M3 SCREWS rows)
    (S_FA, 'D2-35', 'M3 heat-set insert, brass, short (L 4.0, OD 4.6 class), lens-collar anchors in the tub bosses', M3_INS_TUB + M3_SPARE['ins'], 'ea', 'heat-set insert class (procure; G-COL-1)', 'any', None, 0.2, 'm3_hw', '%d used (tub TL / TR / LL, set at the bench before step 3) + %d spare' % (M3_INS_TUB, M3_SPARE['ins'])),
    (S_FA, 'D2-36', 'M3 heat-set insert, brass, L 5.7 (OD 4.6 class), lens-collar pinch lug', M3_INS_LUG, 'ea', 'CNC Kitchen M3 standard class', 'any', None, 0.2, None, '%d used (s_c4, pressed into the lower lug from below); spare: the D2-32 pack' % M3_INS_LUG),
    (S_FA, 'D2-37', 'M3 x 10 pan head A2, ISO 7045 cross recess PH1 (lens-collar anchors)', M3_BY_LEN.get(10.0, 0) + M3_SPARE['screw'], 'ea', 'ISO 7045 class', 'any', None, 0.1, None, '%d used (s_c1..s_c3, %.2f N m provisional cap) + %d spare; separate from the D2-33 fallback screws' % (M3_BY_LEN.get(10.0, 0), L.M3['torque_Nm']['s_c1'], M3_SPARE['screw'])),
    (S_FA, 'D2-38', 'M3 x 16 pan head A2, ISO 7045 cross recess PH1 (lens-collar pinch)', M3_BY_LEN.get(16.0, 0) + M3_SPARE['screw'], 'ea', 'ISO 7045 class', 'any', None, 0.1, None, '%d used (s_c4, 0.2 N m, the last operation on the lens) + %d spare' % (M3_BY_LEN.get(16.0, 0), M3_SPARE['screw'])),
    (S_FA, 'D2-39', 'M3 washer, ISO 7089 A2 (3.2 x 7.0 x 0.5)', M3_WASHERS + M3_SPARE['washer'], 'ea', 'ISO 7089 class', 'any', None, 0.05, None, '%d used (one under each lens-collar screw: %s) + %d spare' % (M3_WASHERS, M3_IDS, M3_SPARE['washer'])),
    (S_FA, 'D2-34', 'Contingency: M2.5 x 5 pan head A2, ISO 7045 cross recess PH1', 0, 'ea', 'ISO 7045 class', 'any', None, 0.1, None, 'order 8 only if the X1203 kit screws are hex-socket (FASTENER-POLICY F, G-W2)'),
    (S_CO, 'D2-40', 'ASA filament 1.75 mm, 1 kg, satin silver (tub, panel, sleeve)', 1, 'spool', 'Polymaker ASA class', 'MakerSupplies SG', 'CON-01', None, None, 'price of the black spool line'),
    (S_CO, 'D2-41', 'ASA filament 1.75 mm, 1 kg, black (hood, base + grip, cap, knobs, pi_keeper, plunger)', 1, 'spool', 'Polymaker ASA class', 'MakerSupplies SG', 'CON-01', None, None, ''),
    (S_CO, 'D2-43', 'TPU 95A filament, black (eyecup)', 1, 'spool', 'class', 'any', 'CON-02', 25.0, None, 'about 5 g needed'),
    (S_CO, 'D2-44', 'Paint pen / enamel for the engraving fill: black (silver panel, concept tally) + white (plunger symbol)', 2, 'ea', 'class', 'any', 'CON-10', 4.0, None, 'confirm the panel fill colour with the concept'),
    (S_CO, 'D2-45', 'Closed-cell foam sheet 1.0 mm (OLED pad 16 x 14)', 1, 'sheet', 'class', 'any', 'CON-20', 3.0, 'foam_pad', ''),
    (S_CO, 'D2-46', 'Adhesive-lined heat-shrink 3:1 (pigtail, diode splice, r4 fuse splice: about 4.8 mm, 30 mm per fuse) + thin-wall 2:1 (switch lugs)', 1, 'set', 'class', 'any', 'HAR-HSA', 4.0, None, ''),
    (S_CO, 'D2-47', 'Solder, flux, wick', 1, 'set', 'class', 'any', 'CON-15', 6.0, None, ''),
    (S_CO, 'D2-48', 'Pull ribbon 10 mm (if the pack has none) + Kapton tape', 1, 'set', 'class', 'any', 'CON-16', 2.0, None, ''),
    (S_CO, 'D2-49', 'Isopropyl alcohol + glue stick (bed release)', 1, 'set', 'class', 'any', 'CON-11', 4.0, None, ''),
    (S_CO, 'D2-50', 'Small cable ties 2.5 mm (pigtail strain relief at a standoff, lead bundles)', 1, 'pack', 'class', 'any', None, 2.0, None, 'step 1'),
    (S_TO, 'D2-60', 'PH1 screwdriver, straight, shank dia <= 6.5, blade >= 40 mm (hand)', 1, 'ea', 'TLS-14 class', 'any', 'TLS-14', 6.0, None, 'straight-driver rule'),
    (S_TO, 'D2-61', '1/2 in (12.7 mm) socket or spanner for the switch nut', 1, 'ea', 'class', 'any', None, 5.0, None, 'ASSEMBLY s1.1 tool 6; OPTIONS (a) removes it'),
    (S_TO, 'D2-62', 'Fine tweezers (OLED, flex, microSD)', 1, 'ea', 'class', 'any', None, 4.0, None, ''),
    (S_TO, 'D2-63', 'Temperature-controlled soldering iron', 1, 'ea', 'class', 'any', 'TLS-07', None, None, '%d joints at the bench (WIRING s7); +2 if the pack lacks an XT30; +%d under option C' % (sum(SOLDER_JOINTS.values()), REG_C_JOINTS_DELTA)),
    (S_TO, 'D2-64', 'Digital multimeter + thermocouple', 1, 'ea', 'class', 'any', 'TLS-05', None, None, 'gates G-W1 to G-W13'),
    (S_TO, 'D2-65', 'Adjustable bench DC supply with current limit (>= 10 A for G-W5 and G-W12, else 3 A)', 1, 'ea', 'class', 'any', 'TLS-03', None, None, ''),
    (S_TO, 'D2-66', 'Official Raspberry Pi 27 W USB-C PSU (bring-up)', 1, 'ea', 'SC1149', 'MakerSupplies SG', 'TLS-01', None, None, 'gate G-W3'),
    (S_TO, 'D2-67', '1S Li-ion balance charger (SkyRC B6neo class) + XT60-to-XT30 lead + USB-C PD supply', 1, 'set', 'SkyRC B6neo', 'Makerfire (US)', 'CHG-01', None, None, 'out-of-body charging (W-7); adapter and PD supply unpriced (CHG-02/03)'),
    (S_TO, 'D2-68', 'Wire stripper / flush cutter, heat gun', 1, 'set', 'class', 'any', 'TLS-12', None, None, ''),
    (S_TO, 'D2-69', 'Junior hacksaw + small flat file (cut the 18/24 switch shaft to y 42.0)', 1, 'set', 'class', 'any', None, 6.0, None, 'step 2; ASSEMBLY s1.1 tool 7; OPTIONS (a) removes it'),
    (S_TO, 'D2-70', 'ESD mat + wrist strap', 1, 'set', 'class', 'any', None, 12.0, None, 'steps 1, 4, 6, 7'),
    (S_TO, 'D2-71', '2 x dia 1.5 steel pins, ISO 8734 1.5 x 16 dowel class (hood release hold-open; r2 fixer: replaces the 3 mm release blade)', 2, 'ea', 'class', 'any', None, 0.5, None, 'ASSEMBLY s1.1 tool 9; s7 item 9 (or the shanks of 2 x 1.5 mm drills)'),
    (S_TO, 'D2-72', 'Digital calipers, 0.01 mm', 1, 'ea', 'class', 'any', None, 15.0, None, 'MEASURED-PARTS records (r2)'),
    (S_TO, 'D2-73', 'Oscilloscope >= 20 MHz + inline USB-C power meter (logging)', 1, 'set', 'class', 'any', None, None, None, 'gate G-W12 (workload power, WIRING s9); unpriced'),
    (S_TO, 'D2-74', 'M3 heat-set tip in the tip system of the D2-63 iron (900M class for a YIHUA 928D or Hakko 936-type station, the T12 or TS100 range for those irons) + insert fallback set (pin vise or hand drill, 3.2 + 4.0 mm drills)', 1, 'set', 'class', 'any', None, 12.0, None, 'r5: the tip is needed in every build (the 4 lens-collar inserts, ASSEMBLY B1, FASTENER-POLICY I); the drills only for a stripped boss (FASTENER-POLICY E). r6 (audit B-12): buy the tip for the chosen iron; tips do not cross between systems'),
    (S_TO, 'D2-75', 'DC electronic load >= 10 A / 30 W, constant-current mode (r3 fix-baseline)', 1, 'ea', 'class', 'any', None, None, None, 'gates G-W5 (b) (8.6 A on the pigtail end) and G-W13 (option C); unpriced'),
    (S_TO, 'D2-76', 'G-W13 (c) bench stand-ins: 100 uF electrolytic + power resistor for a 0.30 A load at 4.5 V (about 15 ohm, >= 3 W) (r3 fix-baseline)', 1, 'set', 'class', 'any', None, None, None, 'only with EVF-feed option C; bench consumables; unpriced'),
    (S_TO, 'D2-77', 'Adjustable torque screwdriver 0.1-0.6 N m, straight, PH1 bit: shank dia <= 6.5 over >= 40 mm, handle dia <= 30 (the DRIVER audit envelope)', 1, 'ea', 'class', 'any', None, None, None, 'r6 (audit 2026-10-06 B-6 / X5): sets s_c1..s_c3 0.15 N m, s_c4 0.2 N m and the PT screws 0.35-0.5 N m; a firm hand on a plain PH1 gives 0.4-0.6 N m, 2-3x the M3 values; also used for G-PT-1 and G-COL-1; unpriced'),
]


# layout ids that are bought inside another line (kit contents) -> that line
INCLUDED_IN = {'x1203_kit': 'D2-03', 'c_cs_adapter': 'D2-05', 'evf_board': 'D2-07', 'oled_flex': 'D2-07',
               'pack_lead': 'D2-13', 'run_lead': 'D2-12', 'fan': 'D2-02',
               'tripod_block': 'D2-05'}   # r5: the GS tripod block + 2 screws (removed at B0; layout CAM tripod_block)


def coverage(rows):
    """Every layout COTS id and cable id -> the BOM line(s) that buy it. Returns (table rows, uncovered ids)."""
    by_ref = {}
    for r in rows:
        if r['ref']:
            by_ref.setdefault(r['ref'], []).append(r['line'])
    ids = [('COTS', k) for k in L.COTS] + [('cable', c['id']) for c in L.CABLES]
    out, missing = [], []
    for kind, k in ids:
        lines = by_ref.get(k) or ([INCLUDED_IN[k] + ' (included)'] if k in INCLUDED_IN else [])
        if not lines:
            missing.append(k)
        out.append('| %s | `%s` | %s |' % (kind, k, ', '.join(lines) or '**not covered**'))
    return out, missing


def load_prices():
    with open(PRICES, encoding='utf-8') as f:
        return json.load(f)


def resolve(pid, est_usd, P):
    """-> (unit SGD incl. GST allowance or None, basis text, prices.json id used or '')."""
    fx, gst = P['fx']['rate'], P['gst_allowance']
    it = P['items'].get(pid) if pid else None
    if it and it.get('price') is not None:
        p, gb = it['price'], it.get('gst_basis')
        sgd = p * fx * (1 + gst) if gb == 'usd_list' else p * (1 + gst) if gb == 'excluded' else p
        return sgd, 'prices.json %s (%s, %s, %s)' % (pid, it.get('date'), it.get('confidence'), gb), pid
    if est_usd is not None:
        tag = ' (prices.json %s has no price)' % pid if it else ''
        return est_usd * fx * (1 + gst), 'estimate: USD %s planning figure, not a quote%s' % (est_usd, tag), ''
    return None, 'unpriced' + (' (prices.json %s has no price)' % pid if it else ''), ''


def build():
    P = load_prices()
    rows = []
    for sec, lid, item, qty, unit, sku, sup, pid, est, ref, note in LINES:
        unit_sgd, basis, used = resolve(pid, est, P)
        rows.append(dict(section=sec, line=lid, item=item, qty=qty, unit=unit, sku_or_class=sku, supplier=sup,
                         ref=ref or '', unit_sgd=unit_sgd, line_sgd=None if unit_sgd is None else unit_sgd * qty,
                         basis=basis, prices_id=used, note=note))
    printed = MT.printed_rows()
    return P, rows, printed


def money(v):
    return '' if v is None else '%.2f' % v


# ------------------------------------------------------------------ H. second-hand alternatives (Carousell SG snapshot)
# Source: SECONDHAND-CAROUSELL-2026-10-05.md (52 browser searches on 2026-10-05 about 23:00 SGT; listing pages
# checked for the picks). Listings change daily, so re-check before use. New references are the BOM line price where
# one exists, otherwise the research agents' new-retail estimate (marked est). All SGD.
# Landed-cost model (planning assumptions, stated in the generated section):
SH_DATE = '2026-10-05'
SH_TRIP = 4.0        # public-transport round trip per meet-up or collection [est]
SH_FEE = 0.03        # Carousell Buyer Protection / payment fee allowance on the price [est; confirm at checkout]
SH_HOURS = 1.5       # per seller: travel + an on-the-spot check [est]
SH_DUTY_NOTE = ('Singapore charges no customs duty on these goods; duty applies only to liquor, tobacco, motor '
                'vehicles and petroleum. The 9 % import GST is already inside every new price in this BOM, including '
                'low-value overseas orders, which carry GST since 2023/2024. Local second-hand sales between '
                'individuals carry no GST.')
# (id, BOM lines, item, listing id, used price, new reference, new-ref basis, new delivery share, risk share,
#  recommend, note)
SECONDHAND = [
    ('H1', 'D2-01 + D2-66', 'Raspberry Pi 5 8 GB kit with a Cytron 27 W 5.1 V 5 A PSU (+ micro-HDMI cable; its '
     '3rd-party heatsink is not used)', '1465023314', 220.0, 279.18 + 28.00, 'BOM D2-01 + D2-66', 0.0, 0.05, 'yes',
     'the seller says it was tested on 30 Sep 2026; check that it boots, shows 8 GB and gives no 5 A-supply warning'),
    ('H2', 'D2-02', 'Raspberry Pi Active Cooler, unopened', '1447325605', 10.0, 15.00, 'BOM D2-02', 0.0, 0.05, 'no',
     'only if collected on the same trip as another pick; confirm that it is the official SC1148'),
    ('H3', 'D2-67', 'SkyRC B6neo charger (new stock from a shop; offer price S$45)', '1331349488', 45.0, 53.00,
     'BOM D2-67', 0.0, 0.02, 'no', 'the exact model, but the net saving is about nil after the trip'),
    ('H4', 'D2-64', 'Fluke 17B+ multimeter (well used, tested) + a generic K-type probe if missing (S$15)',
     '1465242951', 175.0 + 15.0, 279.0, 'est. new 17B+ (agents)', 5.0, 0.05, 'yes',
     'ask whether the 80BK-A probe is included'),
    ('H5', 'D2-73 (scope)', 'Siglent SDS1202X-E 200 MHz 2-channel oscilloscope, probes included', '1464903923', 350.0,
     529.0, 'est. new (agents)', 10.0, 0.08, 'yes', 'run the self-calibration and check for a clean probe-comp '
     'square wave on both channels'),
    ('H6', 'D2-63', 'YIHUA 928D soldering iron with 5 spare tips', '1465859700', 25.0, 56.0, 'est. new (agents)', 5.0,
     0.10, 'yes', 'premium alternative: the Hakko FX-951 at S$200 against about S$393 new (listing 1441107252)'),
    ('H7', 'D2-68 (heat gun)', 'Black & Decker HG 991 heat gun', '1465184811', 19.0, 30.0, 'est. new', 5.0, 0.10,
     'marginal', 'saves little after the trip; worth it only alongside another pick'),
    ('H8', 'D2-65', 'Tenma 72-2925 0-30 V 0-10 A linear bench supply', '1406062545', 250.0, 110.0,
     'est. new 30 V 10 A switch-mode supply (agents)', 5.0, 0.08, 'no',
     'dearer than a new switch-mode 10 A supply; only worth it if you want a linear supply (about S$300+ new)'),
]
SH_OPTIONAL = [
    ('H9', 'printer (not in the BOM)', 'Bambu Lab P1S, like new, no AMS', '1452157022', 520.0, 682.0,
     'est. new (agents)', 0.0, 0.08, 'optional',
     'only if you have no enclosed printer; check the print hours and have the seller unbind it from their account'),
    ('H10', 'test lens (not in the BOM)', 'Official Raspberry Pi 6 mm CS lens (bring-up only; not a D2 lens option)',
     '1367268824', 25.0, 37.38, 'est. new (agents)', 0.0, 0.05, 'optional', 'CS mount, about 53 g'),
]


def sh_rows(items):
    out = []
    for (hid, lines, item, lid, used, new, basis, dnew, risk, rec, note) in items:
        new_landed = new + dnew
        cost = used + SH_TRIP + used * SH_FEE + used * risk
        net = new_landed - cost
        out.append(dict(id=hid, lines=lines, item=item, url='https://www.carousell.sg/p/%s/' % lid, used=used,
                        new=new, basis=basis, new_landed=new_landed, trip=SH_TRIP, fee=used * SH_FEE,
                        risk=used * risk, cost=cost, gross=new - used, net=net, hours=SH_HOURS,
                        per_hour=net / SH_HOURS, rec=rec, note=note))
    return out


def sh_section():
    main, opt = sh_rows(SECONDHAND), sh_rows(SH_OPTIONAL)
    with open(os.path.join(HERE, 'secondhand.csv'), 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f, lineterminator='\n')
        w.writerow(['id', 'bom_lines', 'item', 'listing', 'used_sgd', 'new_ref_sgd', 'new_ref_basis',
                    'new_landed_sgd', 'trip_sgd', 'fee_sgd', 'risk_allowance_sgd', 'used_landed_sgd',
                    'gross_saving_sgd', 'net_saving_sgd', 'hours', 'net_per_hour_sgd', 'recommend', 'note'])
        for r in main + opt:
            w.writerow([r['id'], r['lines'], r['item'], r['url'], money(r['used']), money(r['new']), r['basis'],
                        money(r['new_landed']), money(r['trip']), money(r['fee']), money(r['risk']),
                        money(r['cost']), money(r['gross']), money(r['net']), r['hours'], money(r['per_hour']),
                        r['rec'], r['note']])
    hdr = ['| Alt | Replaces | Item (Carousell listing) | Used | New ref (basis) | New landed | Used landed | '
           'Gross saving | **Net saving** | Net per hour of your time | Take it? |',
           '|---|---|---|---|---|---|---|---|---|---|---|']

    def tab(rows):
        return ['| %s | %s | [%s](%s) | %s | %s (%s) | %s | %s | %s | **%s** | %s | %s: %s |' % (
            r['id'], r['lines'], r['item'], r['url'], money(r['used']), money(r['new']), r['basis'],
            money(r['new_landed']), money(r['cost']), money(r['gross']), money(r['net']), money(r['per_hour']),
            r['rec'], r['note']) for r in rows]

    def S(rs, k):
        return sum(r[k] for r in rs)

    def line(name, rs):
        return '| %s | %s | %s | %s | **%s** | %.1f h | %s |' % (
            name, money(S(rs, 'new_landed')), money(S(rs, 'cost')), money(S(rs, 'gross')), money(S(rs, 'net')),
            S(rs, 'hours'), money(S(rs, 'net') / max(S(rs, 'hours'), 1e-9)))
    take = [r for r in main if r['rec'] == 'yes']
    cam = [r for r in take if r['id'] == 'H1']
    tools = [r for r in take if r['id'] != 'H1']
    out = ['## H. Second-hand alternatives to buying new (Carousell SG snapshot %s)' % SH_DATE, '',
           'These are alternatives only: the lines above remain the plan of record. Source and per-listing checks: '
           '[SECONDHAND-CAROUSELL-2026-10-05.md](SECONDHAND-CAROUSELL-2026-10-05.md); machine-readable: '
           '`secondhand.csv` (generated). Listings change daily, so re-check each one before travelling.', '',
           '**Cost model (planning assumptions, not quotes).**',
           '- New landed = the BOM unit price (GST included) plus a delivery share: S$0 for parts that ride on the '
           'main electronics order (needed anyway for the camera parts), S$5-10 for a tool bought on its own.',
           '- Used landed = the listing price + S$%.0f round-trip public transport per seller + a %d %% Carousell '
           'Buyer Protection / payment fee allowance + a risk allowance (the expected loss, 2-10 %% of the price by '
           'item). Used gear has no warranty, and private sales are final unless paid with Buyer Protection.'
           % (SH_TRIP, round(SH_FEE * 100)),
           '- Duties: ' + SH_DUTY_NOTE,
           '- Your time: about %.1f h per seller (travel + an on-the-spot check). It is shown as net saving per hour '
           'so you can compare it with what your time is worth; it is not subtracted from the net saving.'
           % SH_HOURS, ''] + hdr + tab(main) + ['', '**Optional extras (not BOM lines):**', ''] + hdr + tab(opt) + [
           '', '**Expected savings (recommended picks only: %s):**' % ', '.join(r['id'] for r in take), '',
           '| Scope | New landed | Used landed | Gross saving | Net saving | Your time | Net per hour |',
           '|---|---|---|---|---|---|---|',
           line('Camera parts (H1)', cam),
           line('Tools (%s)' % ', '.join(r['id'] for r in tools), tools),
           line('**All recommended**', take), '',
           '**Non-tangibles (not priced above):**',
           '- *Warranty and returns*: new parts carry the maker or retailer warranty (typically 1 year; Fluke meters '
           'longer); used ones carry none. Pay through Carousell with Buyer Protection where it is offered, and '
           'test before paying when meeting in person.',
           '- *Counterfeits*: Hakko tips, SanDisk flash, 18650 cells and SkyRC chargers are commonly faked. The picks '
           'above avoid those categories, or need a label or serial check (see the "Take it?" column).',
           '- *Availability*: a listing can sell before you reach it. The cooler (H2), charger (H3) and heat gun (H7) '
           'are only worth it as add-ons to a trip you make anyway.',
           '- *Schedule*: second-hand avoids retailer stock waits (one Pi 5 seller notes that local retailers are '
           'out of stock), but adds coordination time.',
           '- *Not available used at all* (buy new): the Global Shutter camera, X1203, EVF kit and eyepiece, 6 mm '
           'C-mount lens, encoder, 18/24 switch, cells or pack, XT30, fuse, recording stick, microSD, cables and a '
           '10 A electronic load.', '']
    return out, S(take, 'net')


def write(P, rows, printed):
    with open(os.path.join(HERE, 'bom.csv'), 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f, lineterminator='\n')
        w.writerow(['section', 'line', 'item', 'qty', 'unit', 'sku_or_class', 'supplier', 'layout_id', 'unit_sgd',
                    'line_sgd', 'price_basis', 'prices_json_id', 'note'])
        for r in rows:
            w.writerow([r['section'], r['line'], r['item'], r['qty'], r['unit'], r['sku_or_class'], r['supplier'],
                        r['ref'], money(r['unit_sgd']), money(r['line_sgd']), r['basis'], r['prices_id'], r['note']])
        for n, p in enumerate(printed, 1):
            w.writerow(['D. Printed parts', 'P-%02d' % n, p['id'], 1, 'part', '%s, %s' % (p['material'], p['colour']),
                        'printed', p['id'], '', '', 'material in section E', '',
                        'mass at 100 %% %.1f g; as printed %.1f g; filament %.1f g; %s; face down %s' % (
                            p['solid_g'], p['mass_g'], p['filament_g'], p['basis'], p['face_down'])])

    def tot(sel, kind):
        return sum(r['line_sgd'] for r in rows if sel(r) and r['line_sgd'] is not None and r['basis'].startswith(kind))

    def cnt(sel, kind):
        return sum(1 for r in rows if sel(r) and r['qty'] and r['basis'].startswith(kind))

    camera = lambda r: r['section'] != S_TO  # noqa: E731
    tools = lambda r: r['section'] == S_TO  # noqa: E731
    out = ['# GS8 D2 release v1: bill of materials (`electronics/gs8-d2-v1`)', '',
           'Generated by `make_bom.py` from `cad/gs8-d2-v1/layout.py` and `%s`. **Do not edit by hand**: change '
           '`LINES` in the script (or the layout, or prices.json) and re-run `python electronics/gs8-d2-v1/make_bom.py`.'
           % os.path.relpath(PRICES, ROOT).replace('\\', '/'), '',
           '**Status:** planning only. Nothing was bought, no cart was used, no supplier was contacted. Currency **SGD**, '
           'including a %d %% GST allowance; shipping excluded. Lines priced from prices.json carry its id, date and '
           'confidence (see its legend; USD list prices x %.4f x 1.09). Every other figure is marked **estimate**: a '
           'USD planning figure written in the script, not looked up and not a quote. "unpriced" lines have no figure.'
           % (round(P['gst_allowance'] * 100), P['fx']['rate']), '',
           '**Done on this machine vs not done (r3).** Done: this generated list, the CAD and its computed checks, the '
           'planning calculations (WIRING s4). Not done: procurement, printing or slicing, measurement, soldering, '
           'power-up and every bench gate (WIRING s9, MEASURED-PARTS). Candidate lines (quantity 0) are not adopted.', '',
           '## Totals (SGD)', '', '| Scope | From prices.json | Estimates | Lines unpriced |', '|---|---|---|---|',
           '| Camera build (sections A-C, E) | %.2f | %.2f | %d |' % (tot(camera, 'prices'), tot(camera, 'estimate'),
                                                                     cnt(camera, 'unpriced')),
           '| Tools and accessories (F) | %.2f | %.2f | %d |' % (tot(tools, 'prices'), tot(tools, 'estimate'),
                                                                 cnt(tools, 'unpriced')), '',
           'The lens (D2-06) is unpriced on purpose: the user reviews the lens choice later. Kowa LM6HC and Fujinon '
           'HF6XA-5M are both C-mount; `layout.LENS` selects the CAD proxy.', '',
           '## Build counts (r2)', '',
           'Read from `layout.py` at generation time (solder joints from `SOLDER_JOINTS` in this script). Optional '
           'reductions are quantified in `cad/gs8-d2-v1/OPTIONS.md`; the full toolset is ASSEMBLY s1.1. The authoritative '
           'count block for the whole release is `cad/gs8-d2-v1/DESIGN.md` s1.1 (`counts`, generated by make_tables.py).', '',
           '| Count | Value |', '|---|---|',
           '| Printed parts | %d (%s) |' % (len(printed), ', '.join(p['id'] for p in printed)),
           '| PT 3.0 x 12 PH1 screws used | %d (%s) |' % (PT_USED, PT_IDS),
           '| Harnesses (`layout.CABLES`) | %d |' % len(L.CABLES),
           '| Keep-outs (`layout.KEEPOUTS`) | %d |' % len(L.KEEPOUTS),
           '| Solder joints | %d (%s); +2 if the pack lacks an XT30 |' % (
               sum(SOLDER_JOINTS.values()), ', '.join('%s %d' % kv for kv in SOLDER_JOINTS.items())),
           '| X1203 kit fasteners (with D2-03; not PT body screws) | %d x M2.5 screws + %d standoffs (`layout.X1203_KIT`) |'
           % (KIT_SCREWS, KIT_STANDOFFS),
           '| Candidate: regulated EVF feed (option C, WIRING s4.8; user decision) | a 4.55 V LDO on a carrier with 2 MLCC '
           'replaces the 1N5817: net +3 parts, +%d solder joints; gates G-W13, G-W6 (regulated run), G-W7 re-run. '
           'The r2 "5 V regulator module" contingency is withdrawn (a 5.0 V output breaks the 4.90 V maximum) |'
           % REG_C_JOINTS_DELTA, '']
    for sec in (S_EL, S_CB, S_FA, S_CO, S_TO):
        out += ['## %s' % sec, '', '| Line | Item | Qty | SKU or class | Supplier | Layout id | Unit (SGD) | Line (SGD) | '
                'Price basis | Note |', '|---|---|---|---|---|---|---|---|---|---|']
        for r in rows:
            if r['section'] == sec:
                out.append('| %s | %s | %s %s | %s | %s | %s | %s | %s | %s | %s |' % (
                    r['line'], r['item'], r['qty'], r['unit'], r['sku_or_class'], r['supplier'],
                    '`%s`' % r['ref'] if r['ref'] else '', money(r['unit_sgd']), money(r['line_sgd']), r['basis'],
                    r['note']))
        out.append('')
        if sec == S_FA:
            out += ['Not separately bought: the X1203 kit (%d M2.5 F-F standoffs, %d M2.5 x 5 screws, with D2-03; '
                    'counted apart from the %d PT body screws), the ' % (KIT_STANDOFFS, KIT_SCREWS, PT_USED) +
                    '18/24 switch nut and washer (with D2-11), the C-CS adapter (with D2-05) and the OLED flex '
                    '(with D2-07).', '']
            out += ['## D. Printed parts (%d parts, %s)' % (len(printed), printed[0]['basis'] if printed else ''), '',
                    '| # | Part | Material, colour | Face down | Volume (cm3) | Mass at 100 % (g) | Mass as printed (g) | '
                    'Filament [est] (g) | Basis |', '|---|---|---|---|---|---|---|---|---|']
            for n, p in enumerate(printed, 1):
                out.append('| P-%02d | `%s` | %s, %s | %s | %.1f | %.1f | %.1f | %.1f | %s |' % (
                    n, p['id'], p['material'], p['colour'], p['face_down'], p['volume_mm3'] / 1000, p['solid_g'],
                    p['mass_g'], p['filament_g'], p['basis']))
            by = {}
            for p in printed:
                k = '%s, %s' % (p['material'].split(' (')[0], p['colour'])
                by[k] = by.get(k, 0.0) + p['filament_g']
            out += ['', 'Filament by material and colour (estimate, before purges and failed prints): ' +
                    '; '.join('%s %.1f g' % kv for kv in sorted(by.items())) + '.', '',
                    '"Mass as printed" = volume x density x the layout infill factor (%s). Replace the layout estimates '
                    'by re-running this script after `build_d2.py` has written its print manifest.' %
                    ', '.join('%s %s' % kv for kv in L.INFILL_FACTOR.items()), '']
    sh, _ = sh_section()
    out += sh
    cov, missing = coverage(rows)
    out += ['## G. Coverage: every layout COTS and cable id', '',
            'Each id in `layout.COTS` and `layout.CABLES` and the BOM line that buys it. Uncovered ids: %s.' % (
                ', '.join(missing) or 'none'), '', '| Kind | Layout id | BOM line |', '|---|---|---|'] + cov + ['']
    with open(os.path.join(HERE, 'BOM.md'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(out))
    return tot(camera, 'prices'), tot(camera, 'estimate'), cnt(camera, 'unpriced')


if __name__ == '__main__':
    P, rows, printed = build()
    a, b, c = write(P, rows, printed)
    print('coverage: %d uncovered %s' % (len(coverage(rows)[1]), coverage(rows)[1]))
    print('BOM: %d purchased lines, %d printed parts; camera SGD %.2f from prices.json + %.2f estimate; %d unpriced'
          % (len(rows), len(printed), a, b, c))
