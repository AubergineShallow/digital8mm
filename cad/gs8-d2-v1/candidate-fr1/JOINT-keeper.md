# FR1 joint: Pi keeper, 2 -> 1 PT screw (keyed seat at the arm end + s_k2)

EXPLORATORY candidate (cad/gs8-d2-v1/candidate-fr1, toggle `D2_FR=keeper`). The r2 release in cad/gs8-d2-v1/ is
unchanged. Every number below is computed from CAD on this machine; nothing was printed, sliced, bought, measured
or powered. "pass" means a computed check result only.

**Verdict: recommend** (computed checks pass; physical gate G-KEEP-1r still to run). It removes one screw and one
floor boss and adds no part, no loose piece, no tool and no flexing catch. The assembler makes one extra short push
(3 mm toward the right wall) at the end of the same slide-in path. See "Trade-off".

## 1. Proposal

r2 holds the keeper with two PT 3.0 x 12 PH1 screws: s_k1 at the corner of the arm (-99.5, 16) and s_k2 in the middle
of the port bar (-64, 28.25). FR1 makes these changes:

- **s_k1 and its tub floor boss are deleted.** The keeper's s_k1 counterbore is also gone.
- **Tongue (keeper).** The USB-edge arm continues past finger kf1 at its -Y end as a full-depth tongue:
  x -105..-97 (8.0 wide), y -29.75..-23 (6.75 long), z 9.8..15.6 (5.8 deep, the arm depth). The tip has 0.6 x 45 deg
  lead-in chamfers top and bottom. The top one is the bed-face chamfer.
- **Keyed seat (tub).** A solid block grows from the right wall and floor in the empty corner behind the USB end of the
  stack: B(-106.85, -95.15, -32.55, -27.0, 2.45, 18.75). A pocket is cut into it from the +Y side:
  B(-105.15, -96.85, -29.9, -26.9, 9.65, 15.75). The pocket gives:
  - a 3.0 ledge over the tongue (z 15.75..18.75), bridged between the two side walls and the back wall;
  - a lower jaw (floor to z 9.65) that the tongue rests on;
  - two 1.7 side walls that key the keeper in x;
  - a 5.1 back (right wall plus block).
  The fits are LOCATE 0.15 on every side (x, z and the tip). The engagement under the ledge is 2.75.
- **s_k2 stays** as the one accessible positive lock: the same boss, spot face, screw axis and step as r2.
- The seat side walls and back are 0.15 off the tongue, while the finger faces are 0.25 off the board edges. The seat
  therefore stops the keeper before any finger face can touch the X1203. The fingers still carry no positioning load,
  and the 4 floor bosses still locate the stack.

Print: the tub prints with its right wall down (+Y up). Every seat face is then either vertical or parallel to the
bed, with no overhang. The pocket roof (the ledge underside) is a vertical wall in print. The keeper still prints top
face down with no supports.

## 2. Alternatives compared

| Option | Result |
|---|---|
| **A. Tongue at the arm end into a right-wall seat, -Y 3 final stroke, keep s_k2 (chosen)** | Computed checks pass. Longest lever to a restraint line drops from 36.8 to 18.4 mm (see section 5). |
| B. Tongue at the bar front end (x -41) into a tub post, engaged by the +X stroke, keep s_k1 | Rejected. The J4 lock boss sits 0.8 behind the arm's -1.2 offset, so the +X stroke cannot grow beyond about 1.75: engagement 1.0-1.5 at LOCATE. The post would sit in the 4 mm gap between ko_pig_wrap (XT30 pigtail bend) and ko_hdmi_pi. |
| C. Keep s_k1, delete s_k2, no key | Rejected. The port bar becomes a 55 mm cantilever (7.95 x 5.8 ASA): about 0.21 mm/N at kf4 (estimate, E 2 GPa), so a 10 N knock means about 2 mm of lift. |
| D. Long captured dovetail along the 60 mm -Y slide | Rejected. It is a long sliding fit past the X1203 edge under the stick rail, with more friction and tolerance stack, and the slide has to be at the final height. That is more complicated, not less. |
| E. Panel rib holds the bar down | Rejected. Pi retention would then depend on panel service (panel off = keeper end free), and it would couple to the panel joint, which another role owns. |
| F. Snap latch | Rejected. r1's floor hooks were deleted for lack of release access. A catch would add a release motion or a tool. |

## 3. Assembly and reverse-service motion (step 4, hood and panel off; tool: straight PH1 for s_k2)

Insertion `keeper_in` (displacements from the final pose):

1. (-1.2, +63, +0.5) -> (-1.2, +3, +0.5): the same slide in from the open left side as r2.
2. Down 0.5 at (-1.2, +3). All 4 fingers are clear of the board: the port tips are 2.35 off the edge and the USB tips
   0.55 off. The tongue tip is 0.25 short of the seat mouth.
3. +X 1.2: the USB fingers go over the X1203 edge, under the Pi.
4. -Y 3.0: the port fingers go over the X1203 edge and the tongue goes home in the seat.
5. Drive s_k2 straight down, 0.35-0.5 N m, stopping at head contact.

Removal `keeper_out`: s_k2 out, then the exact reverse (+Y 3, -X 1.2, lift 0.5, +Y 60). Nothing flexes and there is
no latch.

`pi_out` follows unchanged: lift 5, -X 2.8, up 35, +Y 2.1, up 40. The seat is clear of that path (see section 4).

## 4. Nearby clearances (computed; probe = test_fr_keeper.py, out/_keeper-probe/test_fr_keeper-keeper.json)

- **Seat volume before FR1** (D2_FR=none): only 82.9 mm3 of existing tub, from the floor/wall corner material, and no
  keep-out. **After FR1**: no keep-out overlaps the seat. Gaps from the seat volume:
  - X1203: 4.15
  - Pi 5: 1.77 (the USB connector overhang at z >= 20.1; the seat top is 18.75)
  - kit: 24.8
  - cooler: 22.6
- **Keeper vs keep-outs**: overlap 0. The nearby keep-outs are ko_usb_evf (z >= 27.2 above the seat), ko_pig_wrap,
  ko_pig_under, ko_run_floor, ko_hdmi_pi and ko_fpc_up.
- **Tongue in seat**: minimum gap 0.15, overlap 0.
- **Keeper parts**: X1203 gap 0.1 (finger underside, as r2), kit 1.25, Pi 2.9, cooler 9.2; overlap 0 with each.
- **Sweeps (1 mm step)**: pi_in pass, keeper_in pass.
- **Removals**: keeper_out pass, pi_out pass.
- **Driver**: s_k2 pass (bit 1.23 to the keeper, handle 38.5 to the tub).
- **Boss audit**: s_k2 pass.
- **J4 lock boss** (-111, -20): the seat starts at y <= -27, clear of it and of its chin.
- **Stack retention**: the fingers and the hood post are unchanged, so check_stack_retention keeps the same points.
  - Sensitivity, computed with the check's own LP: if the full 0.15 seat play were added to kf1/kf2, the worst boss
    lift would rise from 0.131 to 0.24, against 1.9 allowed.
  - Restraint geometry: the longest lever from a finger to the line between the two keeper restraints is 18.4 mm (kf4
    to the s_k2-seat line). In r2 it is 36.8 mm (kf1 to the s_k1-s_k2 line).

## 5. Part and fastener changes (before -> after)

- PT 3.0 x 12 PH1 body screws: 7 -> 6 with this joint alone (s_k1 deleted). With the panel joint as well, the FR1
  count comes from fr1_counts.py.
- UPS kit screws and standoffs: unchanged (8 x M2.5 x 5 + 4 standoffs).
- Printed parts: unchanged in number.
  - pi_keeper: 6.64 -> 7.07 g est.
  - tub: 96.4 -> 96.8 g est.
- Tub features: 2 keeper bosses -> 1 boss + 1 keyed seat.
- Tools: unchanged (straight PH1, the step-8 driver). No new release tool.

## 6. Trade-off

One screw and one boss go away, and the keeper is better restrained (shorter levers, positive x/y keying). The costs:

- one more short push in the insertion (-Y 3);
- a seat block in the right-wall corner, about 0.5 cm3 of tub material;
- keeper retention at the arm end now depends on the printed fit of the seat: 0.15 clearance, so up to 0.3 total
  vertical play if printed nominally. In r2 that end was clamped by a screw.

A tight print could bind the tongue; a loose one rattles. That is what G-KEEP-1r has to settle.

## 7. Computed vs physically unverified

**Computed (CAD, this machine):** geometry, mass estimates, overlaps and gaps, keep-outs, sweeps, removals, driver
access, boss audit, the critical-feature chords and the stack-lift LP.

**Not verified:**
- the 0.15 seat fit after printing in ASA (elephant foot on the wall-down tub, hole shrink);
- tongue-to-ledge interlayer strength (the ledge is bridged on 3 sides, but its layers run across the lift load);
- the rattle and play feel;
- G-PI-1: the X1203 edge parts in the finger zones, now including the 3 mm -Y approach of the port fingers at 0.1 over
  the board;
- the real X1203 and Pi dimensions.

## 8. Physical gates and coupons

**G-KEEP-1r** replaces G-KEEP-1 for this candidate. Its criteria are in coupons_fr_keeper.py (proposed, not run).
Coupons, exported by coupons_fr_keeper.py to out/stl/coupons-fr/:
- seat (tub corner, x2);
- tongue stub (x2);
- tub floor strip;
- whole keeper;
- X1203 and Pi stand-ins.

G-PI-1 must also cover the port-finger approach strip.

## 9. Validation results

**Joint-alone full build** (`D2_FR=keeper build_d2.py --fast`, 2 mm sweeps; out/_keeper-1, built 10:54:38, 574 s):
all 21 check categories pass in checks.json, and cad_release_candidate is true (CAD checks only).

| Category | Result |
|---|---|
| interference | 53/53 |
| keepouts | 81/81 |
| thin_wall | 11/11 |
| critical_features | 99 pass + 6 info, 0 fail |
| driver | 6/6, s_k2 included |
| sweeps | 12/12, keeper_in and pi_in included |
| removals | 11/11 |
| service_driver | 5/5 |
| stack_retention | pass: CoM margin 16.7, post gap 0.15, worst boss lift 0.189 of 1.9 allowed |
| layout_self_check | 126/126 |

Output hashes:
- pi_keeper.stl: 630d80c7...
- tub.stl: d376d352... (this tub also carries the other fork roles' toggled-off code; with D2_FR=keeper only the
  keeper seat is on).

**Baseline untouched:** D2_FR=none `--part pi_keeper` and `--part tub` gave sha256 eada966e... and 683c74ec..., the
same as ../out/stl (r2) for both parts. Output in out/_keeper-none.

**Probe** (test_fr_keeper.py, 1 mm sweeps): every number in section 4 and all 20 required ids of FR joint
`J9_keeper_fr` pass. Feature chords:

| Feature | Chord |
|---|---|
| tongue | 5.8 |
| tongue root | 8.0 |
| ledge | 3.0 |
| side walls | 1.7 / 1.7 |
| back | 5.1 |
| jaw | 9.65 |
| s_k2 boss | 2.85 |
| s_k2 seam | 2.35 |

The checks have no clearance zone for the tongue in the seat; integrate-fork has been asked to add one (NOTES).
