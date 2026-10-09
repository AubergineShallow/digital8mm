# DESIGN-C5-B: encoder back-stop plate (BX-5), panel shafts (BX-13), shaft cut (BX-14)

Status: design spec, r7 blocker round, 2026-10-08 (22:45-23:55 MPST). Cluster C5, designer B (geometry angle).
Nothing in the repo was changed except this file. Probes (not in the repo): session scratchpad `r7/C5B/`
(`env.py` keep-out/COTS map, `space.py` + `pan.py` printed-part map, `calc.py` clearances and hook release,
`loads2.py` stop loads, `sweep.py` panel_on sweep and s_e driver bits, `drv8.py` step-8 drivers vs knobs). Geometry: `layout.py` imported; part STEP files `out/step/parts/*.step`
(16:05 build). Nothing has been printed, bought or measured. Every encoder dimension is the `ENCODER` /
`cots.encoder` estimate until MP-ENC is filled.

## 1. Problem, re-checked against the current code

| item | BLOCKERS says | current code (re-checked) | verdict |
|---|---|---|---|
| hook reach | 3 teeth, 0.4 mm | `ENCODER['cradle_hooks']['tooth']` 0.40 = reach over the PCB. Printed tooth is `printed_panel.CRADLE['tooth']` 0.65 = reach + SLIDE 0.25. Hooks: top w 8 at z 70.05, sides w 5 at z 45..50 | correct |
| press direction | -Y, away from the panel | encoder body y 25.7..32.2 sits on the panel inner face (SPLIT 32.2). The PCB back face (y 24.1) rests on the teeth with play 0.1. A knob press pushes the shaft, body and PCB to -Y, onto the teeth only | correct |
| nothing behind | HDMI run is a keep-out, no hook under the PCB | PCB bottom edge z 44.2, `ko_hdmi_run` top z 44.0: 0.2 mm. Behind the board (y < 18.8, x -86..-40, z 42..76): 0 mm3 of tub, hood, pi_keeper or lens_collar, and no keep-out or COTS box (probe `space.py`, `env.py`) | correct; the space behind the board is empty |
| shafts proud (BX-13) | 7-9 mm | encoder shaft to y 44.0 = 9.0 above the panel face (y 35.0); 18/24 shaft cut to y 42.0 = 7.0 | correct |
| cut length (BX-14) | 7.0 above the panel face | 42.0 - 35.0 = 7.0. From the switch body face (seats on the panel inner face, y 32.2) it is 9.8 mm | correct; 9.8 from the shoulder is the useful number |

How weak the cradle is. The load splits by moments about the shaft axis (z 57.0): the top hook (z 69.8) takes 0.426 F
and each side hook (z 47.5) 0.287 F. The lateral force that opens a tooth by its 0.40 reach is
W = 3 E I d / L^3 with L = 9.85 (the `encoder_cradle` record), t 1.6. For E = 1.6-2.2 GPa (ASA, FDM) W = 5.5-7.5 N
(top) and 3.4-4.7 N (each side). Release force P = W (tan a + mu)/(1 - mu tan a), mu 0.3:

| effective return angle a of the 0.65 FDM tooth (sagged overhang) | knob press that opens the first hook |
|---|---|
| 45 deg | 22-31 N (a side hook goes first) |
| 60 deg | 51-69 N |
| 75 deg or more | self-locking (no release) |

The print sags a 0.65 mm overhang by an unknown amount, so the return face sits somewhere in this band. A 30-50 N
press-fit knob is inside the release band. BX-5 is a real MAJOR. The same path carries every in-use push and any
knock on the knob. G-MP-ENC already forbids "cradle flex as substitute travel".

An integral feature cannot fix this alone. The D shaft must pass a 7.5 hole in the 2.8 mm wall. The board can
therefore only arrive along +Y for its last 18 mm. Anything on the panel that catches the back face must flex out
of the way (a snap, which can flex out again) or be fitted afterwards. So the positive stop is a second part.

## 2. Chosen fix and why

**A printed back-stop plate `enc_stop`, fitted on the bench at step 2 with 2 PT screws into 2 new panel posts.
Four rigid pads bear on the four PCB back-face corners.** The knob press is reacted pad -> plate -> screws ->
posts -> panel, in bearing and tension. No flexing member is in the load path. The 3 snap hooks stay: they hold the
board while the plate goes on. Their play grows 0.10 -> 0.30 so that they can never be loaded before the pads.
The pads are fitted to the board with a paper test at step 2 (gap <= 0.10).

Both knobs move to step 2 on the bench. They are pressed with the panel face up on a block under the plate, so the
press goes straight into the block. A 0.2 mm paper shim sets the knob gap. BX-13 then reduces to "do not rest the
body on the knobs" and is handled by sequence. BX-14: cut the shaft before the switch is fitted, with a printed
cut gauge (9.8 mm from the body face).

Alternatives considered:
- Locking the existing hooks (blocks outside the beams). This leaves only 0.25-0.40 of tooth engaged after FDM
  tolerance. The left lock block would also sit in C2's `ko_qt_tail` / `ko_qt_plug`. Rejected.
- A slide-in carrier with card-guide grooves on the PCB x-edges. The grooves sweep the full edge band, so they fail
  if the real QT sockets sit at the board edge (unknown). Rejected; the corner pads need only 4 x 4 mm corners.
- A nut on the encoder bushing, or a set-screw knob. Both depend on unknowns (is the 5880 bushing threaded; a knob
  insert). They are good backups (angle A / judge), not this angle.
- Compliant or crush-rib pads for zero gap. FDM crush ribs keep crushing under 25 N per pad. A plastic flexure with
  sustained preload creeps (>= 0.7 % strain at any useful size). Rejected for the fit-to-board paper test.

## 3. Implementation

### 3.1 layout.py

`ENCODER['cradle_hooks']['play']` 0.10 -> **0.30**. The hooks become assembly retainers: they must stay clear of
the board while the pads carry it. `printed_panel._cradle` must read the play from the layout
(`E['cradle_hooks']['play']`), not from `printed_panel.CRADLE['play']`. Delete that key so there is one source.

New entry (after `ENCODER`):

```python
# r7 C5 (BX-5): positive -Y back-stop for the encoder. A plate on 2 panel posts, 2 PT screws, 4 corner pads on the
# PCB back face. The knob press and every in-use push go pad -> plate -> screws -> posts -> panel; the hooks only
# hold the board until the plate is on (play 0.30 >= fit gap 0.10 + plate deflection + 0.10, check encoder_restraint).
ENC_STOP = dict(
    part='enc_stop',
    plate=B(-84.4, -39.0, 12.6, 18.6, 44.5, 71.0), plate_t=6.0, cbore=dict(d=7.0, depth=1.0),   # PT cbore_d
    cutout=B(-84.4, -75.0, 12.6, 18.6, 44.5, 62.5),          # QT tail / plug side (C2 ko_qt_tail, ko_qt_plug)
    pads={'TL': B(-74.9, -70.9, 18.6, 24.05, 65.4, 69.4), 'TR': B(-55.1, -51.1, 18.6, 24.05, 65.4, 69.4),
          'BL': B(-74.9, -70.9, 18.6, 24.05, 44.6, 48.6), 'BR': B(-55.1, -51.1, 18.6, 24.05, 44.6, 48.6)},
    pad_gap_cad=0.05,          # pad face to ENCODER pcb y0 24.1; re-set from MP-ENC (body + PCB stack, CAD 8.1)
    fit_gap_max=0.10,          # step 2 paper test (80 g/m2 copier paper, about 0.1 mm, must not slide in)
    hook_margin_min=0.10,      # cradle play - fit_gap_max - far-pad deflection at press_design_N
    posts={'post_eA': dict(c=(-80.4, 67.0), d=8.0, y=(18.6, SPLIT)),     # PT boss_od 8.0
           'post_eB': dict(c=(-43.0, 48.5), d=8.0, y=(18.6, SPLIT))},
    screws=('s_e1', 's_e2'), press_design_N=100.0, press_install_N=50.0,
    note='BX-5 r7; pads on the 4 PCB corners (G-ENC-1 corner zones); plate fitted at step 2, bench')
```

`SCREWS` gets two rows (PT 3.0 x 12, the existing `PT` spec):

```python
dict(id='s_e1', kind='PT', joins=['enc_stop'], into='panel post_eA', head_part='enc_stop', axis=(0, 1, 0),
     head_point=(-80.4, 13.6, 67.0), tip=(-80.4, 25.6, 67.0), engage=7.0, step=2,
     cbore={'part': 'enc_stop', 'd': 7.0, 'y': (12.6, 13.6)}),
dict(id='s_e2', kind='PT', joins=['enc_stop'], into='panel post_eB', head_part='enc_stop', axis=(0, 1, 0),
     head_point=(-43.0, 13.6, 48.5), tip=(-43.0, 25.6, 48.5), engage=7.0, step=2,
     cbore={'part': 'enc_stop', 'd': 7.0, 'y': (12.6, 13.6)}),
```

Engagement is 7.0 = `PT['engage_min']` (12 minus the 5.0 of plate under the head; the plate is 6.0 with a 1.0
counterbore d 7.0). The pilot goes 8.0 into the post (tip reserve 1.0); the post is 13.6 long. The heads (dia 6.0
x 2.4) seat at y 13.6 and stand 1.4 proud of the plate back face (y 11.2..12.6). Nothing else is there (probe
`space.py`). The bit passes the d 7.0 counterbore with 0.25 radial, the same as the existing counterbores.

Other layout entries:
- `PARTS['enc_stop']`: module `printed_small`, ASA black, `face_down='-Y'` (back face on the bed, pads up),
  100 % infill (load-bearing), mass about 7 g. Also `PART_RATIONALE`, `OWNERS`, `LOAD_BEARING_PARTS` (+enc_stop).
- `FEATURE_GATES['enc_stop'] = _ASA_PROFILE + ('G-MP-ENC', 'G-ENC-1', 'G-ENC-2')`. Add `G-ENC-2` to the gate text
  table: "plate on: paper test <= 0.10 at all 4 pads; a 50 N and a 100 N knob press move the board by nothing
  visible; detents and push still work".
- `PRINT_PREREQS['enc_stop']`: MP-ENC recorded (the pad length comes from the measured stack).
- `MATES`: add `('enc_stop', 'encoder', 'contact')` and `('panel', 'enc_stop', 'screw')`. Keep
  `('knob_exp', 'encoder', 'press')`.
- `CRITICAL_JOINTS` / joint `J12_encoder_cradle`: parts `['panel', 'enc_stop']`, note "encoder: 3 snap retainers +
  back-stop plate (4 pads, 2 PT)". `CRITICAL_FEATURES`: `enc_stop pads` (4.0 x 4.0, structural, class `stop`),
  `enc_stop plate` (t 6.0), `panel post_eA/eB` (boss OD 8.0 >= `boss_od_min` 7.0, class `boss`).
- `KEEPOUTS`: if C2 is adopted, its `ko_qt_tail`, `ko_qt_plug` and `ko_qt_stow` apply as written there. This
  design clears them by: plate 1.5 (z) / 3.3 (x) to `ko_qt_tail`; plate 0.4 (y) to `ko_qt_plug`; post_eA 1.0 (z)
  to `ko_qt_stow` and 2.0 to `ko_qt_plug`. If C2 is not adopted, add C2's `ko_qt_plug` and `ko_qt_tail` anyway, so
  the plug side stays protected.
- `STEPS`: step 2 `bench` += `enc_stop, s_e1, s_e2, knob_exp, knob_fps`; text in s5 below. Step 8 `adds` +=
  `enc_stop, s_e1, s_e2, knob_exp, knob_fps` (they arrive with the panel). Step 9: remove the knobs from the text
  and from adds.
- `INSERTIONS['panel_on'].moving` = `['panel', 'encoder', 'switch_1824', 'enc_stop', 's_e1', 's_e2', 'knob_exp',
  'knob_fps']`. The path is unchanged.
- `PRESS_REACTIONS = {'knob_exp': 'encoder_restraint', 'knob_fps': 'nut'}` (data for the new `press_paths` check).
- `SWITCH_1824['cut_from_shoulder'] = 9.8` (new key, BX-14). `ENGRAVE` and `KNOBS` are unchanged.
  New tool row: "cut gauge (printed, coupon sheet)".

### 3.2 printed_panel.py

- `_cradle(L)`: take the play from `L.ENCODER['cradle_hooks']['play']`. The beam gets 0.20 longer to the tooth
  (L 9.85 -> 10.05; strain 0.0099 -> 0.0095, x SNAP_KT 0.0143, limit 0.02).
- New `_stop_posts(L)`: for each post in `L.ENC_STOP['posts']`, a cylinder d 8.0 from `SPLIT + EPS` to y 18.6
  along -Y. Each gets two 45 deg root gussets (3.0) on sides away from the PCB: post_eA -X and +Z; post_eB +X and +Z.
  Never -Z on post_eB: a gusset there would enter `ko_hdmi_run` (y 20..32, z <= 44.0). Add them to `adds` in `build_part`.
- `_cuts(L)`: add a branch `elif key in L.ENC_STOP['posts']` (screw along +Y into the post from its free end).
  It works like the `PANEL_POSTS` branch: `top = (tip x, post y0, tip z)`, `depth = tip y - post y0 +
  PT['tip_reserve']`.
- The posts print vertically (panel `face_down +Y`), so they have no overhang. Clearances (probe `calc.py`, with
  the hooks deflected 0.4 outward while snapping):
  - post_eA: 0.75 to the PCB, 9.4 to the top hook, 2.0 to the plug zone.
  - post_eB: 3.35 to the PCB, 1.0 to the deflected right hook, 0.5 above `ko_hdmi_run` (z 44.5 vs 44.0), 5.1
    above `ko_fpc_run`.
  - Both are 5 mm or more from the panel's post_f and keeper finger (x >= -39.3).

### 3.3 printed_small.py: new part `enc_stop`

- `_IDS` += `'enc_stop'`. `PRINT['enc_stop']`: face_down -Y, supports none (back face on the bed; plate and pads
  rise), ASA black, 100 %. Notes: "The pad tops are the datum; do not iron them. Sand or tape-shim them at step 2
  (paper test)."
- Geometry from `ENC_STOP`: the plate box minus `cutout`, with the 4 pad boxes fused on. Two clearance holes d 3.4
  (`PT['clear_d']`) on the screw axes, each with a d 7.0 x 1.0 counterbore on the back face. A 0.4 chamfer
  on the pad top edges, so no sharp edge bears on the PCB.
- Mass: plate about 6.2 cm3 + pads 0.35 cm3 = about 7.0 g. The posts and 2 screws add about 2.7 g, so about
  +9.7 g in all.

### 3.4 Knobs and bore fit

`FDM['KNOB_BORE_OFFSET']` and `KNOBS` stay. The plate (or the block at step 2) keeps the press away from the
hooks, so the fit no longer has to be gentle. G-KNOB-1 gets two sentences:
- "The chosen ladder rung seats by thumb (design case 50 N; the plate is checked at 100 N) and does not pull off
  by hand."
- "Press until the knob rests on a 0.2 mm shim (two layers of copier paper) on the panel face."

The shim makes gP = 0.20 repeatable and puts the end-of-stroke force into the panel. KNOB_BORE_OFFSET needs no
change; the coupon still sets it.

### 3.5 BX-14 cut gauge (make_coupons.py)

A printed sleeve on the coupon sheet:

| feature | value | why |
|---|---|---|
| height | **9.8** | shaft end y 42.0 minus body face y 32.2 |
| lower bore | dia 9.8, 6.0 deep | bushing dia 9.5 + 0.3 |
| upper bore | dia 6.7 | shaft 6.35 + 0.35 |
| OD | 13.0 | clears the anti-rotation tab (r 7.9) by 1.4 |

The CAD stack has no washer between the switch body and the panel inner face. If one is fitted, add its thickness:
print the gauge at `SWITCH_1824['cut_from_shoulder'] + t_inner`. Procedure in s5 (step 2).

### 3.6 BOM and harness

- electronics/gs8-d2-v1/bom.csv (via make_bom.py): PT 3.0 x 12 quantity +2 (13 screws in all). Printed parts:
  + `enc_stop` (ASA, about 7 g) and + the cut gauge (coupon sheet, a tool). Consumables: a copier-paper strip and,
  optionally, 0.06 mm polyimide tape for shims.
- harness-schedule.csv: no row changes. The QT plug stays on the -X socket. The +X socket also stays usable:
  post_eB's top (z 52.5) is 1.5 below the socket (z 54..60).

### 3.7 Loads (probe `loads2.py`; E 1.8 GPa; pads 4 x 4 with 0.4 chamfers = 10.24 mm2 each)

| case | worst pad | pad bearing | per screw | far-pad plate deflection (t 6.0) | hook margin (play 0.30 - fit 0.10 - deflection) |
|---|---|---|---|---|---|
| knob press-on, 50 N centred | 12.5 N | 1.2 MPa | 25 N | 0.017 mm | 0.18 |
| design, 100 N centred | 25 N | 2.4 MPa | 50 N | 0.033 mm | 0.17 |
| abuse, 100 N on the knob rim (r 14, toward a far pad) | 73 N | 7.2 MPa | <= 75 N | 0.098 mm | 0.10 |

In the rim case the opposite pad would go into tension (-24 N). It does not, because the body edge tips onto the
panel inner face and takes that share. Post tension at 75 N is 1.65 MPa (net area 45.4 mm2, across the layers).
Post bending at 0.3 N m is 6.0 MPa. ASA bearing and across-layer strength are well above both. No measured
strength is claimed; G-ENC-2 confirms on the print. The hooks carry nothing in any case, because the board meets
the pads first. The load from the shaft to the PCB corners goes through the encoder's own solder joints, as it
does today through the hooks.

## 4. New and extended computed checks

| check (category) | what it computes | pass criterion |
|---|---|---|
| `encoder_restraint` (new; same engine as `check_evf_restraint`) | `ENCODER_RESTRAINT = dict(part='encoder', arrest=['panel', 'enc_stop'], dirs=[(0, -1, 0)], limit_mm=0.15, max_travel_mm=3.0, first='enc_stop', zones=pcb / qt sockets / back parts from cots.encoder)`. It moves the encoder proxy along -Y (`_first_contact`) and classes the contact by board zone | first contact on `enc_stop` at <= 0.15 (CAD 0.05). The next arrester (panel hook teeth, CAD 0.30) is at >= first + `fit_gap_max` + far-pad deflection at `press_design_N` + 0.10. 100 % of the contact is on the `pcb` zone and 0 % on `qt sockets` / `back parts` (>= 10 % flags) |
| `press_paths` (new) | Every `MATES` row of kind `press` must have a `PRESS_REACTIONS` entry. `encoder_restraint` must pass for knob_exp; the nut path is declared for knob_fps. It reports pad bearing, screw load, post tension and far-pad deflection at `press_design_N` (centred and rim cases) | entry present and pass; worst pad <= 10 MPa; per screw <= 80 N; post tension <= 3 MPa; the deflection keeps the hook margin >= 0.10; the screw-to-screw line passes within 2.0 of the shaft axis (now 1.25) |
| `insertion_closure` (new, generic) | For each `INSERTIONS` path: the parts screwed, contact-mated or pressed onto a moving part at an earlier step (`MATES` + `STEPS` adds/bench), and the leads mated outside the body before it (`CABLE_ENDS`) | each is in `moving`, or in a new `path['tethered']` list with a reason. This catches enc_stop or a knob left out of `panel_on`. It also catches the BX-1 class (a plug mated outside the body but not swept) for C1 |
| `snap` (extended) | `encoder_cradle` record with play 0.30 | L 10.05, nominal 0.0095, x SNAP_KT 0.0143 <= 0.02 |
| `driver` / `service_driver` (extended) | s_e1 and s_e2 at step 2 against the step-2 bench set (panel, encoder, switch_1824, enc_stop); service with the panel off. If `screw_audit_set` does not yet handle bench steps (`in_body=False`), add it: present = union of `bench` of the steps <= n for that sub-assembly | 13/13 and 13/13. Probe: the bit envelopes (6.5 x 40 along -Y from the heads) hold 0 mm3 of every part STEP |
| `keepouts` | enc_stop and the 2 posts against all `KEEPOUTS` (incl. C2's `ko_qt_*` if adopted) | 0 overlap; margins `ko_hdmi_run` 0.5, `ko_qt_tail` 1.5, `ko_qt_plug` 0.4, `ko_qt_stow` 1.0 |
| `sweeps` | `panel_on` with the new moving set | 0 mm3. Probe `sweep.py`: the plate/post footprint swept +70 in Y holds 0 mm3 of tub, hood, pi_keeper, lens_collar, base_grip and cap |
| `print_overhang`, `thin_wall`, `critical_features`, `mass` | enc_stop face_down -Y; posts vertical in the panel | 0 new unsupported faces; plate 6.0, pads 4.0, boss OD 8.0; mass +9.7 g reported |

Planted-fault regressions go in a new file `test_r7_c5_regressions.py`. It follows `test_r3_regressions.py`:
copy the layout module, mutate it, run only the named check.
1. Delete `PARTS['enc_stop']` and its MATES -> `encoder_restraint` FAILS (first arrester = panel teeth at 0.30 > 0.15).
2. Move pad TL to z 52.0..56.0 -> `encoder_restraint` FLAGS / FAILS (contact on `qt sockets`).
3. Set `ENCODER['cradle_hooks']['play'] = 0.10` -> `encoder_restraint` FAILS (hook margin < 0.10).
4. Set the post_eB centre to z 47.9 (bottom z 43.9) -> `keepouts` FAILS (`ko_hdmi_run`).
5. Remove `enc_stop` from `INSERTIONS['panel_on'].moving` -> `insertion_closure` FAILS. Remove `knob_exp` -> FAILS.
6. Move post_eB to (-43.0, 62.0) -> `press_paths` FAILS (the screw line misses the shaft axis by more than 2 mm).
7. Delete `PRESS_REACTIONS['knob_exp']` -> `press_paths` FAILS.
8. Move s_e2 `head_point` y 13.6 -> 20.0 (engagement 1.0) -> the existing PT engagement check FAILS.

## 5. Document changes

**ASSEMBLY.md (via make_tables.py / STEPS):**
- Step 2, new text:
  - "Paint-fill the engraving.
  - Cut the 18/24 shaft first, with the switch off the panel. Clamp the long end of the shaft in the vise in soft
    jaws, the switch hanging free. Slide the printed cut gauge over the bushing onto the body face. Saw flush with
    the gauge top, deburr, and check 9.8 +-0.3 mm from the body face.
  - Fit the switch (tab in its slot) and its nut, finger-tight + 1/8 turn. Snap the encoder into its cradle.
  - Lay the stop plate on its 2 posts. It must sit on both posts, and a copier-paper strip must not slide under
    any of its 4 pads. If it rocks, sand the high pad. If paper enters, add polyimide tape to that pad.
  - Drive s_e1 and s_e2 straight down, PH1, 0.35-0.5 N m.
  - Turn the panel face up on a block about 25 x 25 mm under the plate centre (clear of the 2 screw heads,
    which are 20 mm or more from the shaft). Press each knob on (D flats lined up, knob_fps index on the
    flat) until it rests on two layers of copier paper laid on the panel face. Pull the paper out."
- Step 8: the panel arrives with its knobs and the plate. Replace "hold it beside the body" with C2's wording if
  C2 is adopted. Add: "Drive s_r1/s_r2 with the body standing on its base, driver level. Or lay the body on its
  panel side on a folded towel at least 20 mm thick. Never rest it on the bare knobs on a hard bench."
- Step 9: "Fit the eyecup over the barrel. Fit the sleeve to the stick, push the stick in from the rear."
- s3 checks:
  - step 2 record: "plate paper test pass at TL/TR/BL/BR; knob gaps 0.2 (paper)".
  - step 8: "knobs turn freely and do not touch the panel".
- s7 service item 4: "Panel off: the knobs, the stop plate and the encoder stay on the panel. To replace the
  encoder: pull knob_exp off while your fingers push on the plate, remove s_e1/s_e2, lift the plate, unsnap the
  board. Refit with the paper test."
- Between steps 6 and 8 (BX-13, eyepiece): "Keep the body level or nose-down until the panel is on. The EVF cap
  holds the eyepiece."
- Tools: + cut gauge (printed, coupon sheet), + copier paper, optional polyimide tape 0.06.

**MEASURED-PARTS.md:**
- MP-ENC "Measure" row: add "body front face to PCB back face (CAD 8.1 = body 6.5 + PCB 1.6); this sets the
  `ENC_STOP` pad length. Back-face parts in the 4 corner zones (pads 4 x 4, 0.4 from the top/bottom edges and 0.75
  from the side edges)".
- G-ENC-1 pass: add "no back part within 0.3 of a pad footprint".
- New gate G-ENC-2 (text in s3.1).
- If it fails: move the pads along the edges in `ENC_STOP['pads']` (parametric), or shrink them to 3 x 3. Reprint
  enc_stop only.
- MP-SW: "record any washer between the switch body and the panel; the cut gauge is printed at 9.8 + t".

**WIRING.md / harness:** no change. Add a note under the QT row: "-X socket; the stop plate leaves the plug side
open (cut-out x < -75.0 below z 62.5)."

**BOM.md:** PT 3.0 x 12 x 13; + enc_stop; + cut gauge (tool); consumables.

**guide (guide_steps.py):**
- ISSUES: remove the BX-5 interim ("twist the knob on lightly; never push hard"), the BX-13 shaft note and the
  BX-14 note.
- TIPS: step 2 "paper test under each pad" and "knob onto two layers of paper"; step 8 "body upright for
  s_r1/s_r2, or a thick towel".
- Add one picture for step 2: the plate, two screws and the paper strip.

## 6. Interactions and risks

| area | effect | handling |
|---|---|---|
| C2 (BX-2 QT lead) | Its `ko_qt_tail` / `ko_qt_plug` / `ko_qt_stow` sit on the -X side, low. Its plug is mated with the panel 60 mm out on `panel_on` | The plate cut-out (x < -75.0 below z 62.5) and post_eA (z >= 63.0) clear all three (s3.1 margins). A pinch from behind still reaches the plug; the plug enters along +X under the plate edge. If the QT is ever plugged at step 2 on the bench, the plate does not block it either |
| C1 (BX-1 HDMI) | none in geometry | `insertion_closure` is generic and would also have caught BX-1. Hand it to C1 so that only one copy is written |
| EVF restraint, j7_float, lens_support, collar | none (encoder at x -63, EVF at x -140, camera at x > -20) | unchanged |
| driver audit | +2 screws at a bench step; knobs and plate present from step 8 | `screw_audit_set` may need bench support (s4). Probe `drv8.py`: the bit and handle envelopes of s_b1, s_b2, s_r1, s_r2 and s_c4 hold 0 mm3 of knob_exp and knob_fps (assembly-pose STEPs). The plate lies away from every step-8 driver axis (s_b1/s_b2 bits below z 10, s_r1 at x -31.5 z 85.5, s_r2 at x -143.5) |
| keepouts / cable_routes | plate and posts stay out of every box | `ko_hdmi_run` margin 0.5 is the tightest (post_eB). Do not move post_eB lower |
| sweeps | `panel_on` moving set grows (plate, screws, knobs) | probe: 0 mm3 |
| snap strains | encoder_cradle beam 0.20 longer | strain falls (0.0143 with kt) |
| thin walls / critical features / print_overhang | new part (plate 6.0, pads 4.0); 2 bosses | all far above MIN_WALL 1.2; no overhang in either print pose |
| mass | +9.7 g | report it; no limit is near |
| push operation (G-MP-ENC, G-W9) | board play at rest = pad gap <= 0.10, the same as the old 0.10 hook play | no new substitute travel. A hard push now ends on the pads (or on the knob landing on the panel), never on the hooks |
| knob gap gP | the paper shim sets 0.20 | fixed by procedure. The push-stroke question in MP-ENC stays open (not in scope) |

Weaknesses of this angle (honest):
- It adds a part, 2 screws and about 10 minutes at step 2. The fix needs that second part; no single-part
  version can be positive (s1).
- Zero gap depends on a fit step (paper test, sand or tape). If the fit is skipped and a pad gap > 0.30 is left,
  the hooks take the press first, as today. The plate then still catches the board within the gap, so the encoder
  can no longer drop inside the closed body.
- The pads assume the 4 back-face corners are free of parts. That is true of the proxy, unknown for the real
  board, and gated by G-ENC-1. The pads are parametric if it fails.
- The plate hides the encoder back. The QT side stays open, but reading the back silkscreen needs the plate off.

## 7. Acceptance criteria

Computed after the change (full release rebuild, receipt r7):
- all 28 existing categories pass, plus `encoder_restraint`, `press_paths` and `insertion_closure`;
- `encoder_restraint`: first contact enc_stop 0.05 mm; panel teeth 0.30; margin >= 0.10 at the rim case; 100 %
  pcb zone;
- `press_paths` at 100 N: worst pad <= 7.5 MPa (rim) and 2.5 MPa (centred); per screw <= 75 N; post <= 1.7 MPa;
  far-pad deflection <= 0.10 mm; screw line 1.25 mm from the shaft axis (<= 2.0);
- `snap` encoder_cradle <= 0.0145 with kt; `driver` 13/13; `service_driver` 13/13; `keepouts` all pass with
  the s3.1 margins; `sweeps` `panel_on` 0 mm3; `print_overhang` 0 new unsupported faces;
- the test files `test_r7_c5_regressions.py` (8 planted faults) and the existing tests all pass.

Physical gates (first print, before the panel goes on the body): G-MP-ENC and G-ENC-1 (pads on free corners,
stack measured), then G-ENC-2: paper test pass at 4 pads; a 50 N thumb press and a 100 N press on the knob (body
on a kitchen scale, read the press) show no board motion and no whitening at the post roots; detents and 10
push cycles still pass (G-MP-ENC). G-MP-SW: the cut gives 9.8 +-0.3 from the body face; the knob face sits 0.2
off the panel.

## 8. User decisions

None required. This spec decides: the extra printed plate, 2 extra PT 3.0 x 12 screws from the existing PT line,
the fit step with copier paper, and moving both knobs to step 2.

Optional: if the 5880 arrives with a threaded bushing and a panel nut, the user may also fit that nut as a
second, independent stop. That needs the knob_exp recess deepened (a knob reprint) and is not required here.

## 9. Effort and receipt sources

| work | hours |
|---|---|
| layout.py (ENC_STOP, SCREWS, PARTS, MATES, STEPS, INSERTIONS, gates, critical rows, play) | 1.0 |
| printed_panel.py (posts, pilots, play source) and printed_small.py (enc_stop) | 1.25 |
| checks.py (`encoder_restraint` on the EVF engine, `press_paths`, `insertion_closure`, bench driver set) + build_d2.py registration | 2.0 |
| test_r7_c5_regressions.py (8 cases) + fixing existing tests that count parts or screws (11 -> 13) | 1.0 |
| make_coupons.py (cut gauge), make_tables.py / ASSEMBLY.md / MEASURED-PARTS.md / BOM / guide_steps.py | 1.25 |
| full release rebuild through run_locked.py + review of the receipt | 1.0 (mostly machine time) |
| **total** | **about 7.5 h** |

Receipt sources touched: layout.py, printed_panel.py, printed_small.py, checks.py, build_d2.py, make_tables.py and
make_coupons.py. layout.py alone forces a full release rebuild (all printed parts, STEP/STL, tables, guide
renders). Doc-only files: ASSEMBLY.md (generated tables), MEASURED-PARTS.md, BOM.md (make_bom.py), guide_steps.py.
