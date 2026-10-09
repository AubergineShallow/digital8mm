# SPEC-C3: pigtail tie point and XT30 reach, leads under the stack, run-lead threading (BX-3, BX-11, BX-16)

**r7 fix-up correction (VERIFY-C3, 2026-10-09).** (1) `lead_access` pigtail_drop: the WIRING s4 / G-W5 drop estimate
caps d_board at 25 mm (L_cut 225 mm, 0.150 V); step 1 and G-W2 carry a stop branch (pads farther from W: do not cut);
pigtail_range names the drop-limited pad samples. (2) pigtail_store exits: the S4 pose of the XT30 pair had 2.0 mm (0.15 mm to
the base_grip cradle with shapes) beyond its +X end and 5.5 mm beyond its -X end, against >= 7.2 mm (2 x OD + OD) plus
the unknown rigid exit. Re-posed (fix-up 04:30-04:40): `COTS['xt30_pair']` x -60.25..-34.25, y -7.8..7.6, z
-36.4..-30.0, flat on the pack top under the run button, female (pigtail) end -X, fuse sleeve beside it on +Y
(`PIGTAIL_FUSE` beside=True, x -58.25..-38.25, y 5.1, z -33.2); exits 8.0 mm each end to the base_grip / bay wall
(rigid-exit allowance 0.8 mm at OD 2.4, gate G-MP-PACK); fill 0.149, U-turn margin 0.8; MATE_POSES xt30 W at the -X
female end, disp z -95.0 (W 15 mm below the mouth). A pose that fails the exits is marked status 'info' + gate, never a
plain pass. (3) Step 10
rests the camera on its right side (REST_POSES right_down_10) with the pack held in the palm; the xt30 'hang' spot is
where the palm holds the pack.

Status: design spec, r7 blocker fixes, 2026-10-08 23:00-23:55 MPST; adversarial review and correction 2026-10-08
23:10-00:35 MPST (changes listed in "Review notes" at the end; review probes in session scratchpad `r7/C3rev/`).
Nothing in the repo was changed except this file.
Probes: session scratchpad `r7/C3/` (`nums.py`, `occ.py`, `hole.py`, `rider.py`, `cr.py`, `proto.py`), run against the current `layout.py` and the
r6 part STEPs in `out/step/parts/` (16:05 build). Every dimension of a purchased part below is an estimate or the
existing layout proxy. Nothing was bought, printed or measured.

## 1. Problem, re-checked against the current code

| item | BLOCKERS value | re-check (probe) | verdict |
|---|---|---|---|
| Route wrap top (-38, 25.1, 10) to the pigtail-hole top (box-centre polyline: ko_pig_wrap, ko_pig_under, ko_pig_in, ko_pig_drop) | 38.7 mm | 38.7 | right |
| Hole top (z 2.7) straight down to the grip mouth (`GRIP['bay']` z0 -110) | 112.7 mm | 112.7 | right |
| Wire past the mouth, taut, 180 mm, pads at the wrap | 28.6 mm | 28.6 | right, but optimistic |
| Same with the `cable_routes` service allowance (max(10, 10 % L) = 18 mm) | not given | **10.6 mm** | NEW: the current 180 mm fails a 15 mm criterion even with no tie and the most favourable pads |
| Nearest kit standoffs to the wrap point (-38, 23.7) | 28.7 / 29.7 mm | 28.7 / 29.7 | right; a tie there and back costs about 57.4 mm, so the wire end sits about 28.8 mm (taut) inside the bay |
| `cable_routes` pigtail row (final pose only) | slack 75.7 | est 86.3, allowance 18, slack 75.7 | right; no row checks the step-10 mating pose |
| Pad position | open (Q2) | `COTS['x1203']` "position open (Q2)"; WIRING W-1, G-W2 | open |
| (review) U at the port edge vs the keeper | not given | `PI_KEEPER['bar']` and kf4 end at x -41.0 and sit 0.1 above the X1203 (z 7.7), 0.65 over the edge; r6 `ko_pig_wrap` x0 -40.5 | NEW: 0.5 mm of hand-forming tolerance. A pair laid 0.5 mm too far -X lies under the keeper, which is then screwed down on a battery lead |
| (review) base run-lead passage | not given | `printed_grip.py:202-205` cuts the base passage from `FLOOR_HOLES['run_lead']` x/y | NEW: lengthening the floor hole would also cut the base unless decoupled (3.3) |
| (review) pack lead | not given | `CABLES['pack_lead']` 60 mm, via `ko_xt30` | NEW: it shares the store with the pigtail; it was not counted |

Credible pad range (nothing known, so the whole board): any point of the X1203 PCB (x -91..-6, y -32.3..23.7), either
face. Extra on-board path to the wrap entry W = (-38, 23.7) (top face, Manhattan, routing round parts): 0 to
**109.0 mm** (far corner -91, -32.3). At the cots.py XH-header estimate (-85, -19.3): 90.0 mm. Underside pads run straight
under the board to the hole: at most 83.7 mm, which is at most 45.0 mm more than the modelled 38.7. So the top-face
far corner is the worst case.

Stored length at the final pose (taut final path: pads at W, 38.7 to the hole top, then 25.0 to the +X end centre of the
`xt30_pair` box (-37, 0, -20.65)): 180 mm leaves **116.3 mm** of pigtail folded above the pack today. Nothing checks
that it fits. `ko_xt30` is 28 x 20 x 24 = 13,440 mm3; minus the `xt30_pair` box (3,103 mm3) leaves 10,337 mm3.

Under the stack (BX-11): floor top z 2.5, X1203 underside z 6.0, so 3.5 mm free; the lane boxes are z 2.7..5.8.
`ko_pig_under` is 5.0 wide (x -40.5..-35.5). Tub and keeper probe: the lane and `ko_pig_wrap` hold 0 mm3 of printed
material. Today the guide lays both leads on the floor and lowers the stack onto them blind. The pigtail is joined to
the stack at the pads, so about 40 mm of it has to fold into the wrap as the stack comes down the last 40 mm. Extra
length (and section 2 adds some) bunches in a 3.5 mm space that nobody can see. A pinched battery lead under a board
that is then screwed down by its keeper is a short-circuit hazard. The pigtail is fused, but only at the XT30 end.

Run lead (BX-16): probe of `base_grip.step` shows that at y 1.5..9 the base is open only over the run-lead passage x
-34..-28 (= `ko_run_drop`); there is base material at x -38.5..-34 and -28..-25.5 (z -10..0). At the `base_on` start
pose (base -10 in x) the floor hole x -34..-28 sits over base-frame x -24..-18, 4 mm clear of that passage. So the lead
cannot be threaded before the tub goes down, and it is fished blind through the 6 x 7.5 mm hole afterwards (BX-16
right).

## 2. Chosen fix and why

**BX-3, tie point: a moulded strain relief at the pads; no tie anywhere else.** At step 1, after soldering and
heat-shrinking, a neutral-cure silicone RTV bead bonds the first 8-10 mm of the pair to the X1203 next to the pads. The
anchor is at the route's start, so its detour is 0 mm for any pad position. It travels with the stack, so it also
protects the joints at step 4 and in service. Silicone RTV bonds to the silicone insulation; hot-melt does not hold on
silicone. A neutral (alkoxy or oxime) cure is needed because an acetoxy cure gives off acetic acid that attacks copper.
The "tie to a standoff" is deleted. Order at the bench (review): solder and heat-shrink, lead the pair to W, form the U
and tape the leg (BX-11 below), THEN apply the bead, because with the pads at or near W the first 8-10 mm of the pair is
the U itself, and a cured bead cannot be bent. Top-face pads sit under the Pi 5 once stacked, so the bead goes on before
the Pi. Stack only after the bead is tack-free, and pull on the pigtail only after the full cure the tube states. The
U round the board edge also acts as a capstan in series with the bead (not credited: friction unknown).

**Bend classes (review).** The U at the port edge is a static bend, formed once on the board edge (centreline r 2.0,
inner r 0.8 = half the 1.6 mm board, set by the 4.0 mm between the leg centres above and below the board) and taped.
It is not flexed again. The store fold above the pack flexes at every pack change, so it keeps the 2 x OD inner radius.
`PIGTAIL['bend']` records both. Physical check: G-W2 forms the U on the real board with the real wire (3.1 Step 1).

**Wrap point moved 0.5 mm +X (review).** W goes from x -38.0 to **x -37.5**, and the lane `ko_pig_wrap` /
`ko_pig_under` from x -40.5..-35.5 to **x -40.0..-35.0**. Above z 7.7 the U must stay clear of the keeper (bar and kf4
end at x -41.0). Below z 5.8 it must stay clear of the run lanes (`ko_run_floor` / `ko_run_drop` start at x -34.0).
With r6's -40.5, a hand-formed pair 0.5 mm too far -X would lie under a keeper that is then screwed down: a pinched
battery lead. At x -40.0..-35.0 the tolerance is +-1.0 each way at OD 2.4 (+-1.5 at OD 1.9). Probe (`C3rev/rev3.py`):
tub 0 and keeper 0 at the final pose; pi_in rider sweep against the tub 0; keeper_in sweep 0; keeper inside the lane
grown 1.0 in x: 0.000 mm3 (r6 lane: 0.295). New row `pigtail_wrap_clear` (3.2).

**BX-3, length: cut to length from the measured pad position.** Base length `L0 = 200 mm` with the pads at W; cut
length `L_cut = 200 + d_board`, rounded up to 5 mm. `d_board` is the string length on the board from the pad joint to W,
measured at G-W2. Over the credible range L_cut is 200-310 mm. The wire is bulk stock (D2-26, 1 m per colour), so this
costs nothing. The stored length stays constant (136.1 mm plus up to 4.9 mm of rounding, with W at x -37.5) for any
pad position. L_cut is the finished length from the pad joint to the XT30 rear, the same for both conductors. The W-10
fuse splice in + (20-25 mm from the XT30) is part of it, not added to it.

**BX-11: a sequence change, no new geometry.** At the bench (step 1) the under-board leg of the pigtail is pre-formed
round the port edge at W and taped flat to the X1203 underside along the lane, with 2 strips of Kapton. It then comes
down with the stack as part of it, and nothing has to fold blind. The run lead (in the tub since step 3) is taped to
the floor in `ko_run_floor` before the stack comes. A computed lane-fit row and a sweep "rider" (sections 3.2 and 4) cover it.

**BX-16: geometry plus a sequence change.** Lengthen the floor run-lead hole in -X from x -34 to **x -41.5**
(13.5 x 7.5). At the `base_on` start pose it then overlaps the base passage by 3.5 mm, so the lead can be threaded up
through the floor before the tub is lowered and stays in that window while the tub drops and slides. No fishing.
Review: `printed_grip.py` `_base_cuts` builds the base run-lead passage from `FLOOR_HOLES['run_lead']`. Left as it is,
the longer hole would also cut about 590 mm3 out of the base plate (x -41.5..-34, z -10.5..0.5) for no gain: the window
is 3.5 either way, because it is set by the base passage's +X edge at -38. So the base passage is decoupled. It is cut
from `ko_run_drop`, through a new layout helper `base_run_passage()` that printed_grip and the check both use. The base
geometry then stays exactly r6, and at the final pose the extension sits over solid base (probe: base_grip
180 + 222.5 mm3 under x -41.5..-34, y 1.5..9, z -8..0).

Alternatives considered:
- Printed tie slot beside `ko_pig_wrap`: there is no room for one (occupancy probe). The kf4 keeper finger is at
  x -48..-42, z 7.7..9.8; the keeper bar ends at x -41; the lip gusset starts at y 26.8 (z 2.5) and rises at 45 deg;
  `ko_run_floor` starts at x -34. A tab hanging from the keeper would hit the lip (z <= 7.9) on the -Y `keeper_in` slide.
  A tunnel through the 5.4 x 5.4 gusset leaves walls under MIN_WALL 1.2. Rejected.
- One fixed length for the whole pad range: L >= (151.6 + 109.5 + 15)/0.9 = 306.8, so 310 mm. With the pads at W that
  stores 246 mm (net fill 0.22 of `ko_xt30`, above the 0.20 limit in section 4). Rejected for cut-to-length.
- Floor grooves or guide ribs under the X1203 (BX-11): a groove leaves a 1.5 mm floor and gains only 1 mm; ribs would
  meet unknown underside parts of the X1203. Taping the leg to the stack removes the cause instead. Rejected.
- Widening `BASE_OPENING` +X (BX-16): it runs into the tongue_f base pocket (x -22.25..-3.75). Rejected.

## 3. Exact implementation

### 3.1 layout.py (receipt source: full release rebuild)

New dict after `PIGTAIL_FUSE` (section J13):

```python
# r7 C3 (BX-3): pigtail length rule, tie point and mating pose. Pads: Q2, recorded at G-W2.
PIGTAIL = dict(
    base_len=200.0,                 # L0: cut length with the pads at W (d_board = 0)
    wrap_entry=(-37.5, 23.7),       # W: X1203 port edge, top face (ko_pig_wrap centre x; review: was -38.0)
    pad=dict(face='top', xy=(-37.5, 23.7), status='assumed (Q2); G-W2 records the real position'),
    pad_range=dict(x=PI['x'], y=PI['y'], faces=('top', 'bottom')),   # credible range: anywhere on the X1203
    od_range=(1.9, 2.4),            # 18 AWG silicone, per conductor [est, listing class]; MP-PACK measures
    tie=dict(kind='moulded', what='neutral-cure silicone RTV bead over the pads + first 8-10 mm of the pair',
             at='pad'),             # 'pad' or an (x, y, z) point; checks compute the detour (0 here)
    face_out_min=15.0,              # XT30 face out of the grip mouth at the step-10 mating pose
    housing_credit=0.0,             # XT30U female body length NOT credited (not measured)
    cut_round=5.0,                  # L_cut rounded UP to 5 mm
    store=dict(zone='ko_xt30', fill_max=0.20, bend_r_od=2.0,    # fold above the pack, flexed per pack change [est]
               shared=('pack_lead',)),   # review: other cables whose slack also lives in the zone (counted in full)
    bend=dict(formed_r_min=0.8,     # review: static U on the board edge (inner r = half the 1.6 PCB), formed once
              flex_r_od=2.0),       #   flexed fold: inner r >= 2 x OD (= store bend_r_od)
    form_tol=1.0,                   # review: hand-forming tolerance of the lane in x (keeper / other lanes clearance)
)

def base_run_passage():             # review: ONE source for the base run-lead passage (printed_grip + lead_access)
    b = KEEPOUTS['ko_run_drop']
    return dict(x=b['x'], y=b['y'])
```

Changed entries:

| entry | now | r7 |
|---|---|---|
| `CABLES['pigtail']` | length 180, name "XT30 pigtail 18 AWG 180 mm" | length **200**, name "XT30 pigtail 18 AWG, cut length 200 mm + d_board (PIGTAIL, G-W2)"; add `od=2.4`, `cores=2`, `lanes=['ko_pig_under']` |
| `CABLES['run_lead']` | no od | add `od=1.6`, `cores=2` (per core, est, MP-RUN), `lanes=['ko_run_floor']` |
| `COTS['xt30_pair']` | name "... + 180 mm 18 AWG pigtail ...", mass 11.6 | name "... + fused 18 AWG pigtail (cut length L_cut, PIGTAIL) ..."; mass **12.0** (+2 x 20 mm at about 10 g/m, est) |
| `KEEPOUTS['ko_pig_wrap']` | B(-40.5, -35.5, 23.7, 26.5, 2.7, 10.0) | **B(-40.0, -35.0, 23.7, 26.9, 2.7, 10.0)**. x: forming tolerance (section 2). y1 26.9: the U round the board edge with the leg taped under the board has a centreline r of 2.0 about (y 23.7, z 6.8), so its outer edge is at 23.7 + 2.0 + 1.2 = 26.9 (OD 2.4). Probe: tub 0 mm3. The box clears the lip gusset by only 0.1 at z 2.7 (gusset from y 27.0), but the real U's outer edge is at y 25.5 at z 4.16 and 26.35 at z 5.0, against a gusset at 28.3 / 29.3 |
| `KEEPOUTS['ko_pig_under']` | B(-40.5, -35.5, -5.0, 23.7, 2.7, 5.8) | **B(-40.0, -35.0, -5.0, 23.7, 2.7, 5.8)** (review; tub 0 mm3; 1.0 to `ko_run_floor` / `ko_run_drop`; still overlaps `ko_pig_in` and `ko_pig_drop`, so the route chain is unchanged) |
| `FLOOR_HOLES['run_lead']` | B(-34.0, -28.0, 1.5, 9.0, 0, T) | **B(-41.5, -28.0, 1.5, 9.0, 0, T)** (13.5 x 7.5). Probe: the extension x -41.5..-34 is plain floor (84.4 mm3 at x -38.5..-34, nothing above it); web to the pigtail hole y -4..1.5 = 5.5; tongues at x -22..-14 and -83..-75 clear; at the final pose the extension sits over base material (closed from below) |
| `INSERTIONS['pi_in']` | no riders | add `riders=['ko_pig_wrap', 'ko_pig_under']` (the taped leg comes down with the stack) |
| `printed_grip.py` `_base_cuts` (review) | rect 2 = `FH['run_lead']` x/y | rect 2 = `L.base_run_passage()` x/y (= `ko_run_drop`, x -34..-28, y 1.5..9: the r6 numbers, so the base solid is unchanged) |
| new constant | | `RUN_WINDOW_MIN = 3.2` (2 x run-lead core od, est) next to `FLOOR_HOLES` |

`STEPS` text (new wording; this is the source of the ASSEMBLY.md step table):

- **Step 1** replace "Solder the 180 mm XT30 pigtail to the X1203 battery pads (2 joints)" with (review: reordered so
  the U is formed before the bead, and the bead goes on before the Pi covers top-face pads): "Make the pigtail to
  L_cut = 200 mm + the G-W2 pads-to-W length (round up to 5 mm; 200 mm if the pads are at W). L_cut is the finished
  length from the pad joint to the XT30 rear, with the fuse splice included. Solder it to the X1203 battery pads
  (2 joints) and heat-shrink them. On the bare X1203, lead the pair on the top face to W (a pen mark on the port edge
  31.5 mm from the button-end edge), coming straight in from inside the board, not along the edge. Put one strip of
  Kapton over the board edge at W, fold the pair round the edge, and tape the leg flat under the board with 2 strips
  of Kapton, straight in from W for about 32 mm, to above the pigtail hole. Keep the pair within 1 mm of the mark. The
  rest hangs free. (Pads on the underside: run the pair straight under the board to that point and tape it, with no
  U.) Strain relief: a neutral-cure silicone RTV bead over both joints and the first 8-10 mm of the pair, bonded to
  the board (not acetoxy; keep it off the pogo pads and connectors). Stack only when the bead is tack-free, and do
  not pull on the pigtail before the full cure the tube states." Delete "tie the pigtail to a standoff (strain
  relief)". After G-W2 the designer sets `PIGTAIL['pad']` and `CABLES['pigtail']['length']` to the measured position
  and to the L_cut that `pigtail_range` reports.
- **Step 3** replace "Lower the tub onto the base with the base 10 mm back ... Only now fish the run lead up through
  the floor hole ... (the base opening and the hole overlap only at the final pose)." with: "Hold the tub over the base
  with the base 10 mm back. Push the run-lead sockets (separate 1-pin housings) up through the base passage and the
  rear (-X) end of the floor run-lead hole into the tub. Lower the tub, tongues through the windows, keeping the lead
  lightly pulled up so that it stays in the rear end of the hole. Slide the base 10 mm forward (unlocked until step 8);
  the lead moves to the front end of the hole by itself. Lay the run lead in its floor lane and tape it flat with
  Kapton; let the socket end hang out over the open +Y side."
- **Step 4** replace "Lay the run lead in its floor channel. Feed the XT30 pigtail round the port edge and down through
  the pigtail hole." with: "Check that the run lead is still taped flat in its lane, with its socket end held out over
  the open +Y side. Feed the XT30 end (long side front to back) down through the pigtail hole; the taped leg comes
  down with the stack. Hold the stack's port edge away from the U (more than 10 mm from the W mark)." The rest of
  step 4 stays.
- **Step 10** replace "Plug the pack XT30 into the pigtail at the grip mouth" with: "Draw the pigtail XT30 out of the
  grip mouth until its face is at least 15 mm out (estimate: about 28 mm or more). If it does not reach, stop:
  never mate it inside the bay. Plug the pack XT30 into it, holding both housings. Push the junction and the folded
  pigtail up into the bay ahead of the pack, then push the pack up; nothing may hang in the gaps beside the pack"
  (rest unchanged).

### 3.2 checks.py (receipt source)

New category **`lead_access`** (category count 28 -> 29), function `check_lead_access(L)`, wired in `build_d2.py` next
to `cable_routes`. Factor the box-centre polyline out of `check_cable_routes` into `_route_points(L, via)` so that
both checks use one length model. Rows:

1. **`pigtail_xt30_mouth`** (kind `reach`). With W_top = (Wx, Wy + 1.4, ko_pig_wrap z1), the r6 probe start point:
   `path_in` = W_top through the via overlaps to the hole top (centre of `FLOOR_HOLES['pigtail']`, z = ko_pig_drop
   z1) = **38.9** with W at x -37.5 (38.7 with r6's -38). `drop` = 2.7 - `GRIP['bay']` z0 = 112.7. `d_board(pad)`:
   top face |x - Wx| + |y - Wy|; underside Manhattan(pad, hole centre) - path_in (min 0). `detour` = 2 x the distance
   from the tie point to the route polyline (pad, W_top, overlaps ..., hole top); `at='pad'` gives 0. `face_out = L -
   allowance(L) - d_board - path_in - drop - detour + housing_credit`, with allowance(L) = max(ROUTE_ALLOWANCE[0],
   ROUTE_ALLOWANCE[1] x L), the `cable_routes` constant, imported and not re-typed. Pass: face_out >= `face_out_min`.
   Also reported: `required_len_mm`, the smallest 5 mm step that passes, plus `allowance_mm` and `housing_credit_mm`.
   Now: L 200, face_out **28.4**, required 190 (185 gives 14.9). The taut value with no allowance is 48.4; it is
   reported but never used to pass.
2. **`pigtail_range`** (kind `reach`): apply the cut rule L_cut = ceil5(L0 + d_board) at the 4 PCB corners on both
   faces, at the cots.py XH estimate and at the assumed pad. Pass: min face_out >= 15. Now: worst **17.4** at
   (-91, -32.3) top before rounding (17.9 at L_cut 310). L_cut max 310 <= the D2-26 stock (1000 mm per colour).
3. **`pigtail_store`** (kind `store`). stored = L_cut - d_board - path_in - d_fin, where d_fin = hole top to the
   `xt30_pair` box +X end centre = 25.0. This is conservative: the 20-25 mm of + conductor round the fuse lies inside
   the pair box and is counted again here. Now: 136.1 to **140.6** over the sampled range (the 5 mm rounding bounds it
   at 141.0). Then: (a) net fill = (stored_max + the full length of every `store['shared']` cable, i.e. pack_lead 60)
   x cores x pi/4 x od_max^2 / (V(ko_xt30) - V(xt30_pair box)) <= 0.20. Now (1,272 + 543) / 10,337 = **0.176**
   (pigtail alone 0.123). (b) U-turn: in the free section below the pair (ko_xt30 z0 to the xt30_pair z0,
   28 (x) x 20 (y) x 10 (z)), the fold runs along x and turns across the 20 mm y width. With the pair lying flat in
   the bend plane (conservative), the turn needs 2 x bend_r_od x od + 2 x cores x od = 19.2 <= 20: margin **0.8** at
   OD 2.4 (4.8 at 1.9). (c) ko_xt30 is inside `GRIP['bay']`; the `COTS['pack']` top (-36.8) is at or below the
   ko_xt30 z0 (-36.5); `CAP['box']` does not overlap ko_xt30. (d) Reported as info, not pass/fail: the gaps between
   the pack and the bay walls (y 2.5 / 2.5, -X 4.0, +X 1.0) against OD 2.4. A loop can enter the y and -X gaps, which
   is why step 10 feeds the fold up first and G-MP-PACK looks for it.
4. **`lane_<cable>_<box>`** (kind `lane`), for each cable with `lanes`: box width >= cores x od, box height >= od + 0.5,
   box height <= X1203 z0 - floor top (3.5). Now: pigtail in ko_pig_under 5.0 >= 4.8 and 3.1 >= 2.9; run lead in
   ko_run_floor 12.0 >= 3.2 and 3.1 >= 2.1. Plus **`lane_separation`** (review): every lane box is at least
   `PIGTAIL['form_tol']` (1.0) from every lane or route box of another cable laid at the same or an earlier step.
   Now ko_pig_under to ko_run_floor 1.0 and to ko_run_drop 1.0. The `sweeps` keep-out logic cannot see this pair:
   at pi_in, the run lead's end pi5 is moving, so its lanes are not active obstacles.
5. **`run_lead_window`** (kind `thread`): along the `base_on` waypoints and segments with z offset 0, sampled every
   0.5 mm, the base passage (`layout.base_run_passage()`, the footprint printed_grip cuts) moved by the base offset
   must overlap `FLOOR_HOLES['run_lead']` by >= RUN_WINDOW_MIN in x and >= cores x od in y. Now: min x overlap
   **3.5** (offset -10), y 7.5. With the r6 x0 of -34: **-4.0** (fail).
6. **`pigtail_wrap_clear`** (kind `clear`, review): the wrap and under-board lane boxes grown by `form_tol` (1.0) in x
   hold <= 0.01 mm3 of the pi_keeper. That is tested at the final pose and along `keeper_in`, with the keeper solid
   when build `rows` are given; in the fast test (no shapes) the stand-in is `PI_KEEPER['bar']` plus the kf3/kf4
   finger boxes. Now 0.000 (probe `C3rev/rev3.py`). With r6's x -40.5..-35.5: 0.295 mm3 (fail). Volume tolerance
   0.01, not the 0.5 mm3 of the sweeps, because a 0.5 mm sliver of keeper is under 0.5 mm3.

`check_sweeps` (the `sweeps` category, extended): an insertion may list `riders`, keep-out boxes that move with the
moving set. Each rider is swept with it against the obstacles and is dropped from that insertion's keep-out obstacle
list. The row lists `riders`. `pi_in` with the 2 riders: the probe gives **0.000 mm3** of tub over all 5 segments
(r6 x and the review x -40.0..-35.0, both with ko_pig_wrap y1 26.9). This is the general fix for "a lead fixed to a
moving part must be in its sweep". Review addition: once its insertion is done, a rider is an obstacle at its final
pose for every LATER insertion of the same step. Today `active_ko` takes only cables whose end was in the body at
step - 1, so `keeper_in` (step 4) does not see the pigtail keep-outs at all. Now `keeper_in` sees ko_pig_wrap and
ko_pig_under: 0.000 mm3 (probe). Later steps already see them through `active_ko`.

**C2 interface (review: names and no-weakening corrected).** C2 (SPEC-C2 s3.1/3.2) defines `MATE_POSES`, `mate_reach`
(slack = length_min - fixed - tail - MATE_MARGIN 10) and `cable_stow` (STOW_FILL 0.25). If C2 lands:
- Add the C3-owned entry `dict(id='xt30', cable='pigtail', step=10, insertion='pack_in', disp=(0, 0, -110.2),
  end='xt30_pair', W=(-37.0, 0.0, -14.8), axis=(0, 0, -1), anchor='ko_pig_drop', hand='pinch_xt30',
  out_of=('-z', GRIP['bay']['z'][0], 15.0), length_min=CABLES pigtail length - d_board(PIGTAIL['pad']))`. Here W is
  the XT30 wire entry (pair box top, +X end) at the final pose. disp puts it at z -125, 15 mm out of the mouth, with
  no housing credit. The anchor is the last box that fixes the route, because the tie is at the route start (0
  detour). `pack_in` path becomes `[(0, 0, -110.2), (0, 0, -80.0), (0, 0, 0)]` so that disp lies on it (C2's rule).
  The new segment is a straight extension of the same vertical line through the open mouth (cap off). The pack and
  pair boxes stay inside the bay footprint (x -64.5..-26.5 and -63..-37 within -68.5..-25.5; y +-10 and +-5.1 within
  +-12.5), so the `pack_in` sweep is expected to stay 0 mm3 (the rebuild confirms).
- Keep `lead_access` rows 1-2 as they are. Moving them into `mate_reach` would replace C3's allowance (max(10, 10 %),
  20 at 200 mm) with C2's flat 10 and would drop the pad-range sweep, and the rules say no check may be weakened. Both
  rows must pass: the C2 row adds the hand envelope and the tail path, C3 the allowance and the pad range. Expected C2
  slack at 200 mm with the pads at W: about 22 (C2's own generic figure is 2.2 at 180 mm).
- Do not give the pigtail a `stow` key. `pigtail_store` (fill 0.20, pack lead counted, U-turn, pack/cap) is the
  stricter and more specific row, and a second `cable_stow` row at 0.25 would only duplicate it.
Without C2 the rows stand alone as above.

### 3.3 printed_tub.py / printed_grip.py

There is no new code. The floor-hole loop (`for b in L.FLOOR_HOLES.values()`, line 143) cuts the longer hole from the
layout. Review: `printed_grip.py` is NOT untouched. `_base_cuts` (lines 202-205) also reads `FLOOR_HOLES['run_lead']`,
so its rect 2 changes to `L.base_run_passage()` (3.1 table). That keeps the base solid identical to r6. Without that
edit the base plate loses x -41.5..-34 over z -10.5..0.5, the extension opens into the bay, and the base print checks
change. `airflow/voxelize.py:411` also reads FLOOR_HOLES. The airflow study is paused and is not a release check, so
there is no edit, but its next run sees the longer hole. In print (face_down -Y) the hole's +Y edge is a 13.5 mm anchored bridge (the pigtail hole already bridges
11 mm), well inside `FDM['MAX_BRIDGE']` 30, so `print_overhang` should pass with no supports. If it does flag the
edge, give it a 45 deg gable (a diamond top, apex +Y). Do not add supports.

### 3.4 make_tables.py / electronics (regenerated or edited docs)

- `make_tables.py` line 67 (the pigtail routing note): "from the X1203 pads (RTV strain relief at the pads) on the
  board top to W (port edge, x -38), round the edge (ko_pig_wrap), taped flat under the board (ko_pig_under) to the
  pigtail hole, down into the grip (ko_pig_drop, ko_pig_link) and folded above the pack in ko_xt30 (about 136-141 mm
  stored); cut length 200 mm + the pads-to-W length from G-W2 (PIGTAIL)". Change "x -38" in that note to "x -37.5".
  Also `make_tables.py` line 312, the wiring-diagram edge label `'pigtail 18 AWG 180'`, becomes `'pigtail 18 AWG
  L_cut'` (review: this was missed). `harness-schedule.csv` and the WIRING cables block are then regenerated from
  `CABLES`.
- `make_bom.py` D2-26: note "pigtail cut length 200-310 mm per colour (PIGTAIL; G-W2) + spare". D2-50: description
  "Small cable ties 2.5 mm (lead bundles)" (drop "pigtail strain relief at a standoff"). New consumable row
  **D2-46R**: "Neutral-cure (alkoxy or oxime) silicone RTV, electronics grade, non-corrosive, small tube (pigtail
  strain relief at the X1203 pads)", 1 tube, class, any, planning USD 6.0 (estimate, not a quote), note "not acetoxy".
  D2-48 note: "+ Kapton for the pigtail leg under the X1203 and the run-lead lane".

## 4. Computed checks and planted-fault regressions

New file `test_r7_lead_access.py` (pure Python, layout import only, no CAD: runs in seconds; run through
`run_locked.py` like the rest). Each case passes a modified copy of the layout (`copy.deepcopy` of the dicts on a
`SimpleNamespace(**vars(L))`, as in test_mechanical_refinements.py) to `checks.check_lead_access` or to the sweep
helper and asserts the CORRECTED behaviour:

| case | plant | expect |
|---|---|---|
| r6 length caught | `CABLES['pigtail']['length'] = 180` | `pigtail_xt30_mouth` fail, face_out 10.4 (< 15), required_len 190 |
| standoff tie caught (BX-3 recurrence) | `PIGTAIL['tie']['at'] = (-9.5, 20.2, 12.0)` | fail; detour 57.0 mm (point-to-polyline), face_out -28.6 |
| pads moved, length not updated | `PIGTAIL['pad'] = dict(face='top', xy=(-91.0, -32.3))`, length 200 | fail (face_out -81.1); with length 310: pass (17.9) |
| cut rule broken | `PIGTAIL['base_len'] = 180` | `pigtail_range` fail (worst face_out < 15) |
| no hidden credit | default layout | the row reports `housing_credit_mm` 0 and `allowance_mm` 20; a planted credit of 16 must show in the row (the case asserts that the field is printed, so a credit can never be hidden) |
| coil too big | `PIGTAIL['od_range'] = (1.9, 3.5)` | `pigtail_store` fail on fill or on the U-turn |
| storage squeezed | `KEEPOUTS['ko_xt30']` y to (-8, 8) | `pigtail_store` U-turn fail (16 < 19.2) |
| pack fouls the store | `COTS['pack']` box z1 -30 | `pigtail_store` (c) fail |
| lane too narrow | `CABLES['pigtail']['od'] = 2.6` | `lane_pigtail_ko_pig_under` fail (5.2 > 5.0) |
| run hole back to r6 | `FLOOR_HOLES['run_lead']` x0 -34.0 | `run_lead_window` fail (-4.0) |
| rider swept | `INSERTIONS['pi_in']` riders with ko_pig_wrap y1 30.0, swept against a synthetic gusset solid: a triangular prism along x (x -45..-30) through (y 26.8, z 2.5), (y 32.2, z 2.5), (y 32.2, z 7.9), the tub's 45 deg lip gusset | sweep hit > 0.5 mm3; with y1 26.9: no hit (0.1 clear at z 2.7) |
| rider declared, missing keep-out | riders `['ko_nope']` | the sweeps row fails with "rider not in KEEPOUTS" |
| (review) pack lead forgotten | `PIGTAIL['store']['shared'] = ()` vs default | default fill 0.176; without the pack lead 0.123. The case asserts that the row's `shared_mm` field is 60, so the pack lead is counted |
| (review) store over-full with the pack lead | `CABLES['pack_lead']['length'] = 150` | `pigtail_store` fill fail ((1,272 + 1,357) / 10,337 = 0.254 > 0.20) |
| (review) lane drifts into the run lane | `KEEPOUTS['ko_pig_under']['x'] = (-39.5, -34.5)` | `lane_separation` fail (0.5 < 1.0) |
| (review) wrap back under the keeper | `KEEPOUTS['ko_pig_wrap']['x'] = (-40.5, -35.5)` | `pigtail_wrap_clear` fail with the `PI_KEEPER['bar']` stand-in (about 0.3 mm3 > 0.01) |
| (review) base passage re-coupled | real layout and source | asserts `base_run_passage()` == `ko_run_drop` x/y, `printed_grip.py` `_base_cuts` calls `base_run_passage(` and no longer reads `FH['run_lead']`, so the base cannot silently follow the longer floor hole |
| (review) riders as later obstacles | synthetic keeper box B(-48, -38.0, 23.05, 31.9, 7.7, 15.6) as the `keeper_in` mover (path `PI_KEEPER['path']`), with the pi_in riders at the default x | the `keeper_in` row hits ko_pig_wrap (about 14.7 mm3 > 0.5); with x1 -41.0 it passes (touch, 0) |

The rider and keeper cases use small synthetic solids, not the exported STEPs, so the test stays fast and is
independent of the build (the r3 regression style). Case count: 12 + 6 = 18.

## 5. Document changes

- **ASSEMBLY.md**: the step table is generated from `STEPS` (3.1). Step 1 "Harness" row: replace "strain-relief tie
  to a standoff" with "RTV strain relief at the pads (neutral cure); leg taped under the X1203 to the hole point".
  Step 3 s3 check: "The run lead runs up through the -X end of the floor hole, not over the base top; the base slides
  without catching it." Step 4 s3 check (add): "Before the keeper: the pigtail leg is still taped flat under the
  X1203 and the U at the port edge is inside the gap to the lip gusset; the run lead is taped in its lane." Step 10 /
  s5 **Fit**: "Draw the pigtail XT30 out until its face is at least 15 mm out of the grip mouth (estimate: about
  28 mm or more). If it does not reach, stop and do not mate inside the bay; re-check the cut length (G-W2). Feed the
  folded pigtail up ahead of the pack; look up the mouth before the cap: no loop beside the pack." s7 **P3**: add
  "the pigtail is long enough for the junction to come at least 15 mm (estimate about 28 mm) out of the mouth". Step 4
  s3 check (add): "the U lies at the W mark, not under the keeper finger kf4 or the bar (x -41 and beyond)". s7 item
  for the stack (stack
  out): "the taped leg and the RTV stay on the X1203; lift the stack straight up with the pigtail following through
  the hole (XT30 long side front to back)".
- **WIRING.md**: s2 diagram "pigtail 18 AWG 180 mm" -> "pigtail 18 AWG, cut length 200 mm + pads-to-W (G-W2)". W-1:
  add "Strain relief: a neutral-cure silicone RTV bead at the pads (BX-3). No tie to a standoff." The s3 parts row
  "Pigtail": "18 AWG silicone, 200 mm + d_board (200-310 mm), XT30U female ...". s6 cables block: regenerated. s7
  harness table: row "1 (bench) pigtail -> X1203 battery pads": "cut to L_cut (PIGTAIL); solder red to +, black
  to -; adhesive heat-shrink; on the bare X1203 lead the pair to the W mark, Kapton over the edge, form the U and
  tape the leg flat under the board to the hole point; then the RTV bead over the joints and 8-10 mm of the pair
  (before the Pi covers top-face pads); stack when tack-free, full cure before step 4". Row "4 pigtail": "feed the XT30 end down
  through the pigtail hole (long side front to back); the taped leg comes down with the stack". Row "10": add "face
  >= 15 mm out of the mouth, never mated inside the bay". G-W2 row: add "measure d_board = the pads-to-W string length
  (W: port edge, 31.5 mm from the button-end edge) and enter the pad face and position in `PIGTAIL['pad']`; cut the
  pigtail to the length `pigtail_range` reports; form the U on the board edge at W with a 30 mm offcut of the real
  wire pair and check that it stays within 3.2 mm of the edge (y 26.9) and within the 5.0 mm lane width". Open-items
  list: Q2 note "pad position now changes only the cut length (PIGTAIL), unless the pads are on the underside inside
  the run lane footprint (x -34..-22, y 1.5..31), which needs a new lane; the route and the keep-outs stay".
- **BOM.md**: regenerated by make_bom.py (D2-26, D2-46R, D2-48, D2-50 as in 3.4).
- **MEASURED-PARTS.md**: MP-X1203 "Measure" add "the pads-to-W string length on the board (`PIGTAIL['pad']`, d_board);
  a free solder-mask area of about 10 x 5 mm next to the pads for the RTV bead; the underside parts under the lane
  x -40.0..-35.0, y -5..23.7 (the taped leg); for underside pads, the joint + bead height (must stay <= 3.1, the lane
  height) and whether the pads lie inside the run lane footprint x -34..-22, y 1.5..31 (then a new pigtail lane is
  needed: 2.4 + 1.6 stacked > the 3.5 gap)". "If it fails": replace "Pads elsewhere: re-route the pigtail keep-outs"
  with "Pads elsewhere: enter them in `PIGTAIL['pad']` and cut to the reported L_cut; re-route only if they are on
  the underside under the lane". MP-PACK "Measure" add "pigtail wire OD (18 AWG silicone, design range 1.9-2.4:
  `PIGTAIL['od_range']`), the pack lead length and OD (design 60 mm, `CABLES['pack_lead']`, counted in the store)
  and the XT30U female body length (not credited)". G-MP-PACK pass add "with the pigtail folded above it (about
  140 mm) plus the pack lead, the pack goes home and the cap shuts 10 times without pinching either lead, and no loop
  lies in the gaps beside the pack (look up the mouth before the cap)". MP-RUN
  "Measure" add "lead core OD (design 1.6, `CABLES['run_lead']['od']`)".
- **guide/guide_steps.py**: delete `ISSUES['1g']` and `ISSUES['10a']` (BX-3) once the fix lands. Replace TIPS
  `'3b'` BX-16 with "Thread the run-lead sockets up through the floor hole before you lower the tub; keep the lead
  in the rear (-X) end of the hole while the tub drops and slides." Replace TIPS `'4a'` BX-11 with "The pigtail leg
  is already taped under the X1203 (page 1): just feed the XT30 down the hole as the stack comes down. Check that the
  run lead is still taped flat in its lane." Line 197 text: "Feed the XT30 end of the pigtail down through the pigtail
  hole into the grip (long side front to back); the leg under the board comes down with the stack." Page 1g: add
  the cut-length, RTV and tape actions; page 10a: add the "15 mm out, else stop" line. Regenerate the guide and mark
  BX-3, BX-11 and BX-16 "fixed in r7" in BLOCKERS-2026-10-08.md (a status column only; the ids stay).
- **HANDOFF.md** top: one paragraph naming C3, the new `lead_access` category and the step 1/3/4/10 changes.
- Guide and WIRING s7, one more line: "the top leg reaches W from inside the board (y < 23), not along the port edge,
  so that the keeper fingers kf3 / kf4 (port edge x -80 / -45, tips 0.65 over the edge, 0.1 above the board) never
  sit on it."

## 6. Interactions and risks

| area | effect | status |
|---|---|---|
| `keepouts` | ko_pig_wrap B(-40.0, -35.0, 23.7, 26.9, 2.7, 10.0) and ko_pig_under x -40.0..-35.0: tub 0, keeper 0 mm3 (review probe). The keeper (bar and kf4 tip) ends at x -41.0, or -42.2 during `keeper_in`: 1.0 clear; panel at y >= 32.2. The x1203_kit COTS envelope (x -70.4..-6.6, z 4.25..21.85) overlaps ko_pig_under as it did in r6; it is an envelope of the 4 corner standoffs, which are far from the lane | holds |
| `sweeps` | `pi_in` gains 2 riders: 0.000 mm3 (probe). `keeper_in` gains the riders as obstacles: 0.000 (probe). `base_on`: no change (base solid unchanged by 3.3). `pack_in`: no change, or the C2 waypoint (3.2) | holds |
| `stack_retention` / keeper fingers | the U at x -40.0..-35.0 is 1.0 from the keeper bar end (x -41.0) and 2.0 from kf4's body (x -48..-42); `pigtail_wrap_clear` computes it; the top-leg rule above keeps the leg out from under kf3/kf4 | holds; G-PI-1 adds "no lead under a finger" |
| base_grip (review) | `_base_cuts` reads `base_run_passage()` (= ko_run_drop) instead of FLOOR_HOLES: same numbers as r6, so the base solid is unchanged | holds; the receipt shows an unchanged base hash, or the reviewer explains it |
| `thin_wall` / `critical_features` | the floor web between the run-lead and pigtail holes stays 5.5 (y -4..1.5); there are no bosses or tongues near x -41.5..-34 | expect pass; the rebuild confirms |
| `print_overhang` | 13.5 mm floor-hole bridge, under MAX_BRIDGE 30 | expect pass |
| `cable_routes` | pigtail 200 with the review lane (x -40.0..-35.0, y1 26.9), computed with `check_cable_routes` on a patched layout (`C3rev/cr2.py`): est 86.6, allowance 20, slack 93.4 | pass |
| `mass_com` | +0.4 g on `xt30_pair`; the RTV and Kapton are below 1 g | negligible |
| driver audit, `service_driver`, `j7_float`, `lens_*`, `evf_restraint` | no screws, camera or EVF geometry touched | unaffected |
| `layout_self_check` | the tongue-vs-`FLOOR_HOLES` test (layout.py:2156) still passes (tongues at x -22..-14 and -83..-75) | holds |
| C1 (BX-1) | [Plan edit P3-4] C1 changes no printed part (rail cut rejected); only C3 changes the tub | none |
| C2 (generic mating-pose reach) | the xt30 `MATE_POSES` entry is given in 3.2; rows 1-2 stay in `lead_access` (no weakening); no `stow` key on the pigtail | no conflict |
| category count | C1 (`mate_paths`), C2 (`mate_reach`, `cable_stow`), C3 (`lead_access`) and C6 (`plunger_capture`) each add categories, so the r7 total is 28 + all that land, not 29. `test_build_outputs.py` and HANDOFF must take the count from the build summary, not hard-code it | coordinate at integration |
| BX-2 / BX-10 clusters (QT lead, header sockets) | they change other `CABLES` rows; `lane` rows read `od` / `cores` only where present | no conflict |

Risks:
- The U-turn store margin is 0.8 mm at the upper OD estimate. It is an estimate check: G-MP-PACK closes it on the real
  pack and pigtail. 18 AWG stays (W-2). If the gate fails, the fallback is to store part of the fold in the y side
  strips beside the pair (4.9 wide each) and to re-check the bend with the measured OD. Decide that at G-MP-PACK, not
  now.
- The RTV bond needs about 10 x 5 mm of clean solder mask next to the pads (G-W2 photo). If there is none, put the
  bead on the board edge at W (still on the route, detour 0).
- The taped leg sits under unknown underside parts of the X1203. Kapton insulates, but a tall underside part in the
  lane would push the leg down onto the floor (3.5 mm total gap). MP-X1203 now asks for the underside parts in the
  lane.
- Threading before the slide depends on the lead's core OD (est 1.6) against the 3.5 mm window. MP-RUN measures it.
- (review) The U at the port edge is a tight static fold (inner r 0.8 for OD 2.4), inherited from r6, whose lane
  (y1 26.5) was tighter still. Silicone insulation and fine-strand copper take a formed static fold, but the PCB edge
  can cut the insulation, hence the Kapton strip over the edge at W. G-W2 forms it on the real board (5).
- (review) Hand-forming tolerance: +-1.0 mm about the W mark (31.5 mm from the button-end edge). A U formed more than
  1 mm toward -X lies under the keeper. The step-4 check looks for it before the keeper goes in.
- (review) The store fill (0.176 with the pack lead) and the 0.20 limit are design estimates; 0.20 is stricter than
  C2's STOW_FILL 0.25. G-MP-PACK is the real test.
- The silicone RTV needs time to cure before the pigtail is handled (thin bead: follow the tube; typically about
  24 h for full strength). It costs calendar time, not a step: steps 2-3 (panel, base) can run meanwhile.

## 7. Acceptance criteria

Computed, after the full rebuild (`run_locked.py -- build_d2.py`), with 0 fail in every category:

| check | value that must hold |
|---|---|
| `lead_access` `pigtail_xt30_mouth` | face_out >= 15.0 (expected 28.4 at L 200, path_in 38.9, allowance 20, housing credit 0, detour 0); required_len 190 |
| `lead_access` `pigtail_range` | min face_out >= 15.0 over the 10 sampled pads (expected 17.4 before rounding, 17.9 at L_cut 310); L_cut max <= 1000 |
| `lead_access` `pigtail_store` | fill <= 0.20 (expected 0.176 with the 60 mm pack lead; 0.123 pigtail alone); U-turn need 19.2 <= 20.0; pack top -36.8 <= ko_xt30 z0 -36.5; cap does not overlap ko_xt30; side gaps reported |
| `lead_access` lane rows | pigtail 5.0 >= 4.8 and 3.1 >= 2.9; run lead 12.0 >= 3.2 and 3.1 >= 2.1; both lane heights <= 3.5; `lane_separation` 1.0 >= 1.0 |
| `lead_access` `run_lead_window` | min x overlap >= 3.2 (expected 3.5), passage from `base_run_passage()`; y overlap 7.5 >= 3.2 |
| `lead_access` `pigtail_wrap_clear` | keeper in the lane boxes grown 1.0 in x: <= 0.01 mm3 at the final pose and along keeper_in (expected 0.000) |
| `sweeps` `pi_in` / `keeper_in` | pass with riders [ko_pig_wrap, ko_pig_under] (expected 0 mm3), and the riders are obstacles in `keeper_in` (expected 0 mm3) |
| `cable_routes` pigtail | pass (est 86.6, slack 93.4) |
| `keepouts`, `thin_wall`, `critical_features`, `print_overhang`, `layout_self_check` | pass, with the longer run-lead hole, the lane at x -40.0..-35.0 and ko_pig_wrap y1 26.9 |
| base_grip | geometry unchanged from r6 (passage decoupled, 3.3) |
| every other r6 category | unchanged pass (no check weakened; the category count rises by 1 for C3; see section 6 for the total) |
| `test_r7_lead_access.py` | all 18 planted-fault cases give the stated result |

Physical gates (later):
- **G-W2** (X1203 receipt): pads located; d_board measured with a string; `PIGTAIL['pad']` entered;
  `pigtail_range` / `pigtail_xt30_mouth` re-run; L_cut taken from the row. There is a free area for the RTV bead and
  no underside part in the lane. The U formed with a wire offcut on the real board edge stays within 3.2 mm of the
  edge and within the 5.0 mm lane.
- **G-MP-PACK** (pack receipt, real pigtail): the stored fold (about 140 mm) plus the pack lead goes above the pack
  10 times without pinching, the cap shuts each time, and no loop lies beside the pack; the pigtail, pack lead and
  XT30U body dimensions are recorded.
- **First assembly**: at step 10 the XT30 face comes at least 15 mm out of the mouth (estimate about 28 mm or more); at step 3
  the run lead threads before the slide and is not caught; at step 4 the taped leg is still flat under the stack
  (look in at the port edge before the keeper goes in).

## 8. User decisions

None needed. The new purchase is a consumable (a small tube of neutral-cure silicone RTV, planning USD 6, BOM D2-46R),
and the pigtail wire is already on the BOM as bulk stock (D2-26, 1 m per colour; nothing has been bought yet). The pack and run-button variants stay
the user's open procurement choices, as before.

## 9. Effort and receipt sources

| work | hours |
|---|---|
| layout.py (PIGTAIL, `base_run_passage()`, CABLES od/cores/lanes, ko_pig_wrap / ko_pig_under, FLOOR_HOLES, riders, STEPS text) | 0.8 |
| printed_grip.py `_base_cuts` rect 2 -> `base_run_passage()` (review) | 0.1 |
| checks.py (`_route_points` refactor, `check_lead_access` rows 1-6 incl. lane separation and wrap clearance, riders in `check_sweeps` incl. later same-step obstacles) + build_d2.py wiring | 2.3 |
| test_r7_lead_access.py (18 cases) | 1.2 |
| make_tables.py notes (lines 67 and 312), make_bom.py rows, regenerate tables / BOM / harness CSV | 0.5 |
| ASSEMBLY / WIRING / MEASURED-PARTS / guide_steps.py text, guide regeneration, HANDOFF | 1.2 |
| tub rebuild + full release build + review of the receipt (shared with C1) | 1.0 |
| **total** | **about 7.1** |

Receipt sources touched: `layout.py`, `checks.py`, `build_d2.py`, `printed_grip.py` (one line; the base solid stays
r6) (full release rebuild: every part and every check re-runs); `printed_tub.py` itself is not edited, but the tub
geometry changes through `FLOOR_HOLES`, so the tub STEP / STL, the tub print checks and the release hash set change.
`make_tables.py` and `electronics/gs8-d2-v1/make_bom.py`
regenerate ASSEMBLY.md, DESIGN.md, WIRING.md, harness-schedule.csv, bom.csv and BOM.md.
`test_r7_lead_access.py` is a new test file. Prototype of the row arithmetic (layout import only): session scratchpad
`r7/C3/proto.py` (designer, W -38) and `r7/C3rev/proto2.py` (review, W -37.5, lane x -40..-35: the numbers in this
spec); rider sweep probe `r7/C3/rider.py`; review CAD probes `r7/C3rev/rev1.py` and `rev3.py`, run through
`run_locked.py`.

## Review notes (adversarial review, 2026-10-08 23:10-00:35 MPST)

Verified by my own probes (layout import plus cadquery against the r6 part STEPs, through `run_locked.py`):
- Route 38.7 + 112.7 mm, r6 taut reach 28.6, 180 mm with allowance 10.6, standoff detour about 57-58, cut-rule range
  and stored length: all reproduced (`proto.py` re-run). The fix does remove BX-3's problem: the tie detour is 0, and
  the 15 mm reach is computed over the whole board.
- Floor-hole extension x -41.5..-38.5 (the designer probed only -38.5..-34): plain floor (56.25 mm3), nothing above it
  to z 12, nothing below z 0; base solid under it at the final pose. Window 3.5 at base_on start (r6 -4.0).
- ko_pig_wrap y1 26.9: tub 0. The box is 0.1 clear of the gusset at z 2.7, but the real U clears it by about 3 mm.
- pi_in riders: tub 0 (r6 and review x). keeper_in against ko_pig_wrap: 0. cable_routes pigtail at 200: pass.

Changed (errors and gaps found):
1. **Base coupling (major, missed):** `printed_grip.py:202-205` cuts the base run-lead passage from
   `FLOOR_HOLES['run_lead']`, so the spec's change would also have cut the base (about 590 mm3), opened the extension
   into the bay, and voided "closed from below". Decoupled through `base_run_passage()` (= ko_run_drop). printed_grip.py
   is added to the files, and a test pins it.
2. **Keeper tolerance (major, missed):** the r6/spec lane x0 -40.5 is 0.5 from the keeper bar/kf4 end (x -41.0, 0.1
   above the board). A hand-formed pair 0.5 mm off would be screwed down under the keeper: a pinched battery lead. W
   and the lane are moved +0.5 to x -37.5 / -40.0..-35.0 (+-1.0 tolerance; 1.0 to the run lanes), checked by the new
   rows `pigtail_wrap_clear` (0.01 mm3 tolerance, because a 0.5 mm sliver is under the sweeps' 0.5 mm3) and
   `lane_separation`, with a W pen mark in the guide. All numbers are recomputed: path_in 38.9, face_out 28.4,
   required_len 190 (was 185), range worst 17.4 / 17.9, stored 136.1-140.6, cable_routes est 86.6 / slack 93.4.
3. **Pack lead omitted from the store:** the 60 mm pack lead also lives in ko_xt30. Fill 0.122 -> **0.176**
   (still <= 0.20); `store['shared']`; 2 regression cases.
4. **keeper_in blind spot:** `active_ko` ignores same-step cables, so riders are now obstacles for later same-step
   insertions.
5. **Bend-radius inconsistency:** the port-edge U (inner r 0.8) contradicted the store's 2 x OD rule without
   comment. Bend classes defined (static formed vs flexed); Kapton over the board edge; G-W2 forms the U on the real
   board.
6. **Step-1 order:** the bead was applied before the U was formed, but with pads at W the bead would lock the U
   section. Reordered: U and tape, then bead (before the Pi covers top pads), then tack-free, then stack.
7. **C2 alignment:** the real names are `MATE_POSES` / `mate_reach` / `cable_stow`. The concrete xt30 entry is given
   (disp -110.2, pack_in waypoint). Rows 1-2 now stay in lead_access, because moving them to C2's flat 10 mm margin
   would weaken them. No `stow` key.
8. Smaller items: U-turn text ("larger side (20)" -> the 20 mm y width); the step-10 "designed about 29" is the
   allowance-reduced value, so the wording is now "about 28 mm or more" (taut 48.4); the fuse splice sits within
   L_cut; underside-pad limits (bead height <= 3.1, run-lane footprint); `make_tables.py:312` label; side-gap info and
   the step-10 "fold up first" wording; the rider test wedge made explicit (a box would also hit at 26.9); the
   category count is not "29" with C1/C2/C6 also adding categories; section 8 said the wire was "already bought"
   (nothing is); 6 test cases added (18); effort 6.4 -> 7.1 h.

Not changed / accepted: the RTV-at-pads tie (sound: 0 detour, travels with the stack; neutral cure is correct), the
cut-to-length rule, the BX-11 taped-leg sequence, the BX-16 slot length (x -41.5) and RUN_WINDOW_MIN 3.2, D2-46R. No
user decision is needed.

## Plan edits (integration, 2026-10-09 00:00-01:00 MPST; PLAN.md wins where it and this spec differ)

Plan edits: P3-1 C2 lands before C3 (PLAN.md order), so the `xt30` MATE_POSES row is REQUIRED, not "if C2 lands".
It carries `plug='p_pig_xt30'` and `reach='pigtail'`: mate_reach takes its slack from the same helper as
`pigtail_xt30_mouth` (`_pigtail_face_out(L, pad)` - face_out_min), so there is one pigtail length model and one
number. lead_access keeps `pigtail_xt30_mouth` (required_len, credit and allowance fields) and `pigtail_range`;
mate_reach adds pose-on-path, hand (`pinch_xt30`), tail path and out_of. out_of is ('-z', GRIP['bay']['z'][0],
15.0) (the 3.2 text had 'z' without a sign). The `pack_in` path [(0, 0, -110.2), (0, 0, -80.0), (0, 0, 0)] lands.
Plan edits: P3-2 The reason given in 3.2 for keeping rows 1-2 ("C2's flat 10 mm margin") is stale: SPEC-C2's final
margin is max(10, ROUTE_ALLOWANCE[0], ROUTE_ALLOWANCE[1] x length), identical to allowance(L). Both use the shared
helper `reach_margin(L, length)`; `ROUTE_ALLOWANCE` stays imported, not re-typed.
Plan edits: P3-3 `riders` are implemented in the single carried-box routine (SPEC-C1 P1-3) as kind 'rider': hard
against every solid and every active keep-out; after their insertion they are final-pose obstacles for later
insertions of the same step (this also applies to C1's carried plugs). PLUGS `p_pig_pads` has no box (C1 P1-2), so
ko_pig_wrap is swept once, as a rider.
Plan edits: P3-4 Section 6 row "C1 (BX-1 tub rail cut)" and the risk "Build together with C1 (BX-1 rail cut)" are
void: SPEC-C1 rejected the rail cut and changes no printed part. C3 alone changes the tub (FLOOR_HOLES); the tub
STL hash change is expected, the base_grip hash must stay identical.
Plan edits: P3-5 STEPS step 4 is a sentence-level merge with SPEC-C2 (header sentence); step 10 with SPEC-C4
(level-window sentence). Merged texts: PLAN.md s4. Guide TIPS['3b'] is shared with SPEC-C6 (drop the BX-12 strap
line): one merged tip. ASSEMBLY s3 row 3 ("Run lead fished up ... after the slide") becomes "Run lead threaded up
through the floor hole before the tub was lowered, taped flat in its lane, not pinched". All BOM edits go into
make_bom.py `LINES`. `lead_access` registers with `info_neutral=True` (side-gap info rows).
