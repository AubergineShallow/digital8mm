# FR1 joint study: side panel, 4 -> 2 PT screws (fr-panel, 2026-10-05)

EXPLORATORY candidate in `cad/gs8-d2-v1/candidate-fr1/` (toggle `D2_FR=panel`). The validated r2 baseline in
`cad/gs8-d2-v1/` is untouched. Nothing here was printed, sliced, bought, measured or assembled: every "pass" below is a
computed CAD check, and every mechanical number marked "estimate" is a hand calculation.

**r3 follow-up (fr-panel-2):** sections 1-10 are the first iteration (concept A). Under the same toggle A is now
replaced by **A2 = A + an integral inner-face stiffening frame** (bottom chord, diagonal tie to post_r, two uprights);
the bottom-edge comparison, the rejected screw re-sitings and the checks are in section 11.

## 1. Task and baseline

Baseline panel retention (r2): J2 top tongue in the hood groove (Z, entered along -Y), J3 locate ribs inside the front
and rear walls (X), 2 boss blocks whose tabs fill the tub lip notches, and 4 PT 3.0 x 12 screws:

| screw | from | into | role |
|---|---|---|---|
| s_b1, s_b2 | below, through base_grip counterbores and the tub floor (x -91 / -105, y 27.85) | panel bosses boss_b1/b2 (z 2.6..12.6) | clamp the bottom edge (Z), shank holds Y within the hole play |
| s_r1 | right wall pad (-31.5, z 85.5) | panel post_f (crosses the body) | Y closure, upper front |
| s_r2 | right wall pad (-143.5, z 47.5) | panel post_r | Y closure, mid rear |

User intent: replace the LOWER screw interfaces with integral keys, keep two separated accessible closure screws, keep
straight side removal, do not assume a long captive dovetail fits round the camera keeper, EVF stop/cap, eyepiece clamp
and the wired encoder / 18/24 switch.

## 2. Constraint that decides the comparison

The panel can only move along Y: the hood front plate (x -2.5..0, full height) and the eyepiece housing (x < -154.2,
z 55..100) block X, and the J2 tongue in the hood groove fixes Z at the top. Every integral feature therefore engages by
a straight -Y push. A feature engaged by a straight Y motion can locate X and Z but cannot hold +Y; +Y retention of
the bottom edge needs either a screw, a flexure (snap/detent), or a different motion (tilt-in).

## 3. Concepts compared

| | A. straight-Y shear/seat keys (CHOSEN) | B. bottom hook-in / tilt-in edge | C. A + 45 deg return detent on each key |
|---|---|---|---|
| geometry | the 2 boss blocks become keys key_b1/key_b2 (8 x 10.9 x 10, no pilot, 1.0 lead chamfers); pass the existing lip notches (0.3 side play), seat 0.1 over the tub floor, slide 0.25 under the keeper bridge | inward hook on the panel bottom drops behind a tub upstand, then the panel rotates top-in | a 0.3-0.4 bump on a key flexure clicks behind a notch-face dimple |
| +Y retention of the bottom edge | none positive: by the 2 screws through panel bending (estimate s. 5) | positive (hook) | light, positive until the cam-out force |
| motion | one straight -Y push (unchanged) | lower 2 mm at the bottom, then tilt 4.24 deg top-in (computed from the tongue depth 6.2 + 0.25) | one straight push, a click |
| sweeps (tilt B, computed from layout) | unchanged panel_on path | post tips (y -30.4) move 4.5-4.6 mm in z and 3.2-6.1 in y during the tilt, right at the right-wall pads; camera keeper finger 2.0 z; EVF cap U clamp arrives 0.55 z / 4.2 y off-axis on the eyepiece spigot; encoder/switch bodies 0.9 z | as A |
| wired controls | encoder + switch ride with the panel along Y (leads plugged beside the body, as at step 8) | leads must follow a 2-stage arc | as A |
| printability | keys and chamfers grow -Y in the face-down print: no overhang | hook under-cut in print direction needs a 45 deg flank; tub upstand inside the lip (2.8) | flexure 1.2-1.6 needs the G-CAP-1 style gated class |
| removal | 2 screws out from the right, pull +Y | screws out, tilt, lift | screws out, pull past the detent: the only grip on the flush panel is the knobs, which are push-on and would pull off first |
| verdict | implement | REJECT: 2-stage arc with 62 mm cross-body posts, EVF clamp and camera keeper finger arriving off-axis, not "straightforward side removal" | REJECT: adds a flexure + gate, and the release pull would be applied through push-on knobs |

Not pursued (outside the 4-hour scope and other roles' space): moving s_r2 lower toward the bottom edge (post_r would
have to cross the Pi / stick region) or adding a third side screw (defeats the count target).

## 4. Implemented geometry (concept A, under `FR['panel']`)

- `layout.py` `# --- FR panel` block: `PANEL_KEY` (lead 1.0); `PANEL_BOSSES` -> `{key_b1, key_b2}` (same boxes
  x -95..-87 / -109..-101, y 24.1..32.2 + tab to 35.0, z 2.6..12.6); s_b1/s_b2 removed from `SCREWS`, step 8 text and
  adds, every REMOVALS off/unscrew list; `COTS['pt_screws']` recounted; panel_off note/tool; probes and joints (s. 7).
- `printed_panel.py` `_key_leads()`: 1.0 x 45 deg chamfers on both x edges and the bottom edge of each key's -Y end
  (they lead into the notches and onto the floor; the -Y end is the top of the face-down print, no overhang).
- Data-driven deletions (no code edits needed): base_grip loses the 2 dia 7 x 6 counterbores + dia 3.4 holes, the tub
  floor loses the 2 dia 3.4 holes, the keys have no pilots. Volume deltas vs r2 STL: panel +57 mm3, base_grip +497 mm3,
  tub +45 mm3 (holes filled).
- Unchanged on purpose: lip notches (x +-4.3, 0.3 side play: the J3 ribs remain the X locators, a 0.15 notch would
  over-constrain X against them), the keeper bridge (0.25 over the keys), s_r1/s_r2, posts and pads, J2, J3, the J4
  tongues and the J4 lock s_j (the panel is not a base lock).

Key dimensions: key 8.0 wide (X) x 10.9 deep (Y, incl. the 2.8 tab in the notch) x 10.0 tall (Z 2.6..12.6); notch 8.6
wide x 2.8 lip + 45 deg gusset (5.47 deep in Y at z 5.2) x 5.4 tall; seat 0.1 over the floor; lip web between the
notches 5.4.

## 5. Bottom-edge retention and panel stiffness (ESTIMATE, hand calculation, not FEA, not measured)

Outward (+Y) load F on the bottom edge between the keys (x -98, z 8). Nearest +Y restraint: s_r2 at (-143.5, 47.5),
60.3 mm away; s_r1 is 103 mm away. Panel 2.8 ASA, E 1.6-2.0 GPa (FDM, 1.8 used).
- Strip cantilever (upper bound), width 30, L 60: I = 30 x 2.8^3 / 12 = 54.9 mm4, d/F = L^3 / 3EI = 0.73 mm/N.
- 45 deg spreading wedge plate (lower bound): d/F = 3 L^2 / (E t^3) = 0.27 mm/N.
So about 0.3-0.7 mm/N: 2 N outward opens the bottom seam 0.5-1.5 mm (estimate); baseline r2 holds that edge within the
s_b shank play (<= 0.2). Between the screws the panel is held as a near-rigid plate by s_r1 + s_r2 bearing on the front
and rear wall end faces on both sides of the screw line, so the panel as a whole cannot lift off; only the local bottom
strip can bow. In use the bottom strip sees inward hand pressure; outward loads are small (prying, print bow, knob
pulls at z 57, which sit 20-40 mm from a screw). This is the main trade-off and is a physical gate (G-FRP-1).

## 6. Assembly and reverse service (step 8 / panel_off)

Assembly: hold the panel beside the body, plug the QT lead (encoder) and mate the 18/24 PH junction, push the panel on
along -Y (70 mm path, computed sweep `panel_on` pass, 37 positions, 0 hits): tongue into the hood groove, keys through
the lip notches and onto the floor seat, under the keeper bridge. Drive s_r1, s_r2 from the right (PH1, 0.35-0.5 N m).
Service: shut down and disconnect the battery first (audit item A); s_r1, s_r2 out from the right; pull the panel +Y
(knobs ride with it); unplug the two leads beside the body. No base screw, so no tripod plate or base handling.
Computed removal `panel_off` pass (service state; strap, s_j, cap and pack fitted as geometry evidence only).

## 7. Nearby clearances and computed checks (build `out/_panel-3`, D2_FR=panel, `--fast`, sweeps 2 mm)

All 21 categories pass (contract 11, cots 20, interference 51, mate_overlap 30, clearance 12, keepouts 81, bed_fit 11,
stl_mesh 11, thin_wall 11, critical_features 103 (97 pass + the named exceptions), evf_restraint 6, driver 5,
engrave 10, boss_geometry 5, sweeps 12, removals 11, service_driver 4, release_access 2, stack_retention 1, layout
self-check 123, mass/CoM). `cad_release_candidate: True` is the fork pipeline's computed flag only.

| item | value | check id |
|---|---|---|
| keys under the Pi keeper bridge (z 12.85) | 0.25 (SLIDE) | clearance "J9 keeper bridge over panel bosses" |
| key_b1 -Y face to the X1203 envelope (y 23.7) | 0.4 in y (unchanged from r2; lead chamfer adds 1.0 at the corner) | interference pass |
| keys to the nearest cable keep-out | 24.5 (ko_lead_cross), 25.8 (ko_hdmi_coil), 27.0 (ko_hdmi_run); 18/24 lead ko_fps_up 32.1 | keepouts pass (layout box gaps) |
| panel_on insertion (-Y 70, wired encoder + switch ride along) | 0 hits / 37 positions | sweeps `panel_on` |
| panel_off removal, strap + s_j + base fitted | 0 hits / 37 positions | removals `panel_off` |
| s_r1, s_r2 straight PH1 driver (bit 6.5 x 40, handle 30 x 100) at step 8 and in service | bit 0.25 to the tub counterbore, handle clear | driver, service_driver |
| strap: upper slots x -83.8..-74.8, y -34..-21, z -8..0 (right side, below the base top) | far from the panel path (panel z >= 2.6, y >= 24.1) | removals context includes `strap` |
| key probes panel_key_b1/b2_shear 8.0 (x), _tab 10.9 (y) | min 1.6 (lug) | critical_features |
| tub_lip_web_b12 5.4, tub_lip_cheek_b1/b2 5.47 | min 1.6 (lip) | critical_features |
| panel_post_r_wall 2.75 (new probe; post_f 2.75 existing) | min 1.6 (boss) | critical_features |

Registry: `FR_JOINTS` = FR_panel_keys (required: the 4 key probes + 3 lip probes; replaces s_b1, s_b2 and the 4 removed
probes) and FR_panel_closure (required: panel_post_f_wall, panel_post_r_wall, tub_pad_pad_r1/r2_under_head,
panel_tongue_tooth, hood_groove_lower_lip). `FR_REMOVED_FEATURES` = panel_boss_b1_wall, panel_boss_b2_wall,
panel_boss_b1_cap, base_sb1_head_floor. `FR_VIEWS`: frp-sec-x91, frp-sec-z5 (sections through the keys), frp-motion-off
(panel + wired controls off along +Y with hood ghosted, strap/base/s_j shown), frp-bottom-after (base underside).

D2_FR=none identity (built from the fork with the toggle off, `out/_panel-none`): panel, tub and base_grip STL sha256
equal to `cad/gs8-d2-v1/out/stl/` (db433e49..., 683c74ec..., 9c36007e...).

## 8. Part, fastener and tool changes (before -> after)

| | r2 baseline | FR panel |
|---|---|---|
| PT 3.0 x 12 PH1 for the panel | 4 (s_b1, s_b2, s_r1, s_r2) | 2 (s_r1, s_r2) |
| PT body screws total (toggle panel only) | 7 | 5 (s_r1, s_r2, s_k1, s_k2, s_j); with keeper FR also on: 4 |
| printed parts | 11 | 11 (no new part, no loose piece) |
| base_grip | 2 counterbores dia 7 x 6 + 2 holes | plain (s_j counterbore kept) |
| tub floor | 2 clearance holes dia 3.4 at the panel stations | none |
| tools for panel service | PH1 from below (tripod plate off) and from the right | PH1 from the right only |
| assembly motion | push -Y, 4 screws from 2 directions | push -Y, 2 screws from 1 direction |
UPS kit screws/standoffs (X1203 kit: 8 x M2.5 x 5, 4 standoffs) are unchanged and not counted above.

## 9. Computed vs physically unverified; gates

Computed (CAD only): geometry, clearances, sweeps, driver access, wall probes above. NOT verified: key fit and seat in
print (notch and key print orientation differ: tub -Y down, panel +Y down), bottom-seam stiffness/bow (s. 5 is a hand
estimate), PT pull-out in the 2 remaining posts under the full panel load, knob-pull behaviour.
- **G-FRP-1** (new, proposed, not run): coupon fit (`out/stl/coupons-fr/coupon-frp-*`) and the full-panel seam-gap
  test under 2 N / 5 N outward pull at the bottom edge, plus panel bow; criteria in `coupons_fr_panel.py` GATE.
- G-PT-1 (existing): s_r post pilots, now carrying all panel Y retention.
- G-PANEL-1 (existing base-edge coupon set in make_coupons.py) is superseded under this toggle; make_coupons.py still
  reads PANEL_BOSSES['boss_b1'] and s_b1 and will fail under D2_FR=panel (interface request to integrate-fork).

## 10. Verdict: USER CHOICE (leaning recommend if G-FRP-1 passes)

For: -2 screws, -2 counterbores and -2 floor holes, no new part, the same single -Y motion, panel service from one side
with one tool and no tripod-plate removal, every computed check passes, the base keeps its independent lock s_j.
Against: the bottom edge loses its positive +Y hold; estimate 0.3-0.7 mm/N of seam opening between the keys (s. 5).
If the seam test fails, the fallback is the r2 joint (toggle off), or a later study of a lower s_r2 post position.
Tilt-in hook (B) and detent keys (C) are rejected (s. 3).

## 11. r3 follow-up: bottom-edge stiffness (fr-panel-2, 2026-10-05 10:30-12:40)

Sections 1-10 describe concept A as the **first iteration**. Under the same `FR['panel']` toggle it is now replaced by
**A2 = A + an integral stiffening frame** on the panel inner face (decision below). Nothing here is printed, measured or
tested; every stiffness number is an ESTIMATE.

### 11.1 Method (ESTIMATE, one model for every option)

Grillage (Hambly) model of the panel as a flat 2.8 ASA plate, E 1.8 GPa, nu 0.35, x -152.1..-4.6 (the bearing lines on
the tub rear/front wall end faces), z 8.2..97.0, 37 x 22 cells (about 4 x 4 mm); member I = b t^3/12, torsion
c = b t^3/6 per strip. Out-of-plane w = +Y (outward). Supports: each screw station is its 8 x 8 footprint held at w = 0
(post_f, post_r, or a boss clamped by a screw from below); the inner face bears on the front and rear wall end faces as a
**unilateral** contact (w >= 0, solved as a small contact problem); the J2 tongue, J3 ribs, keys, lip and keeper give no
Y restraint. Existing panel ribs (tongue teeth, EVF cap block, J3 ribs, cradle) are ignored in every option
(conservative, same for all); a new rib is an extra member along its line with the composite I of the rib (w x d) on a
20 mm plate strip. Load: 1 N outward at one node; the number is the deflection there (mm/N). Screw preload, friction,
print anisotropy and creep are not modelled. Scripts: [estimates/](estimates/README.md) `grill.py`, `opts.py`, `opts2.py`
(copied into the fork 15:16 by fix-candidate, VC-M3; `estimates/opts2-output.txt` is a re-run that reproduces the s. 11.2
table; ESTIMATE). Compared with s. 5 (hand bounds 0.27-0.73 mm/N for A at x -98) the grillage gives 0.24 for the
same load: the s. 5 numbers stand as bounds, the table below is the like-for-like comparison.

### 11.2 Options and results (mm per N outward; ESTIMATE)

| option | screws (all PT 3.0 x 12) | seam x -98 | keys zone max (x -112..-84) | bottom edge worst (front corner x -4.6) | EVF cap (-148, 78) | EVF stop (-137.6, 78) | encoder (-63, 57) | 18/24 switch (-123, 57) | cam keeper (-26, 71) |
|---|---|---|---|---|---|---|---|---|---|
| r2 baseline | s_b1, s_b2 (below), s_r1, s_r2 | 0.001 | 0.002 | 0.67 | 0.081 | 0.061 | 0.032 | 0.014 | 0.010 |
| A (first iteration) | s_r1, s_r2 | 0.24 | 0.29 | 0.93 | 0.085 | 0.064 | 0.057 | 0.015 | 0.012 |
| 1a A + bottom chord only | s_r1, s_r2 | 0.21 | 0.27 | 0.89 | 0.084 | 0.063 | 0.056 | 0.015 | 0.011 |
| 1d A + diagonal tie only | s_r1, s_r2 | 0.08 | 0.13 | 0.84 | 0.078 | 0.060 | 0.046 | 0.013 | 0.011 |
| 1b A + chord + tie | s_r1, s_r2 | 0.064 | 0.094 | 0.76 | 0.078 | 0.060 | 0.041 | 0.013 | 0.011 |
| 1c 1b + rear upright | s_r1, s_r2 | 0.062 | 0.091 | 0.76 | 0.046 | 0.042 | 0.040 | 0.012 | 0.011 |
| **A2 = 1c + front upright + link (CHOSEN)** | s_r1, s_r2 | **0.057** | **0.084** | **0.47** | **0.046** | **0.041** | **0.038** | **0.012** | **0.006** |
| 1g A + front upright only | s_r1, s_r2 | 0.21 | 0.24 | 0.51 | 0.085 | 0.064 | 0.050 | 0.015 | 0.007 |
| 2 rear-bottom screw from below (x -140, no base there) replaces s_r2/post_r | s_r1, s_rb | 0.13 | 0.19 | 0.88 | 0.47 | 0.35 | 0.060 | 0.12 | 0.011 |
| 2b option 2 + chord + rear upright | s_r1, s_rb | 0.017 | 0.033 | 0.71 | 0.22 | 0.18 | 0.042 | 0.071 | 0.010 |
| 3 s_r1 + s_b2 (below, through the base), s_r2/post_r dropped | s_r1, s_b2 | 0.007 | 0.039 | 0.78 | 0.73 | 0.52 | 0.042 | 0.19 | 0.011 |

Bottom-edge profile (x = -150, -135, -120, -105, -98, -90, -75, -60, -45, -30, -15, -4.6), mm/N:
r2 0.12 0.06 0.01 0 0 0 0.02 0.08 0.17 0.31 0.46 0.67; A 0.18 0.14 0.16 0.21 0.24 0.27 0.33 0.40 0.48 0.60 0.73 0.93;
A2 0.03 0.02 0.03 0.04 0.06 0.07 0.10 0.14 0.19 0.25 0.32 0.47. The front bottom corner is the weakest point in every
option, r2 included (it is 86 mm from s_b1 and 77 mm from post_f); A2 is the only 2-screw option below r2 there.
At 2 N outward between the keys (the G-FRP-1 load): r2 about 0, A about 0.5, A2 about 0.11 mm (ESTIMATE).

### 11.3 Why options 2 and 3 are rejected, and what limits option 1

- **2 (rear-bottom screw from below, s_r2 and post_r dropped)**: geometrically possible (behind the base, x < -117:
  bit 14.7 clear of the base end, outside `ko_tripod_clamp`; free floor and inner-face space at x -144..-136), and it
  would delete the 62 mm cross-body post_r. But the panel carries the EVF cap clamp (x -151.4..-145, z 63..93) and the
  EVF board +Y stop (x -138.9..-136.3, z 70..86); post_r is the nearest Y hold to both (30 mm). Without it they sit
  70 mm above the nearest screw: EVF cap 0.47 mm/N (0.22 even with a rear upright) against 0.081 in r2, the 18/24
  switch 0.12 (r2 0.014). It also needs a third lip notch, a floor hole and a head under the open rear overhang, and
  it splits panel service between two directions (right + below, camera turned over). REJECT: rigidity of the EVF
  restraint and a second drive direction.
- **3 (s_r1 + s_b2 from below, s_r2 dropped)**: the seam is the stiffest (0.007) because s_b2 clamps it, but the
  rear-mid / top-rear region (EVF cap 0.73, EVF stop 0.52, switch 0.19) has no hold within 64 mm, and panel service
  again needs the base underside (tripod plate off). REJECT: EVF restraint rigidity and service access.
- **Option 1 limits found on the inner-face free-depth map** (ray map of the r2 tub, hood, keeper, sleeve and base
  STEP parts plus the COTS boxes and cable keep-outs behind y 32.2): a continuous bottom flange cannot run forward of
  key_b1, because the Pi keeper bar (x -86.5..-41, y 23.9..31.9, z 9.8..15.6) leaves only 1.35 mm under it (below
  MIN_WALL_LOADED 1.6), and `ko_run_rise` / `ko_pig_wrap` / the tub `rib_l` block the front bottom. Any rib from the
  bottom to post_f is cut by `ko_hdmi_run` (x -113..-36.8, z 39.6..44) and `ko_hdmi_pi`. The rear-lower quadrant
  (x -151..-109, z 8.2..43) is free 8+ mm deep, and a 3 mm column at x -21..-18 is free full height: the frame uses
  exactly those zones.

### 11.4 Implemented geometry (A2, under `FR['panel']`)

`layout.PANEL_FRAME` (FR panel block) + `printed_panel._frame()` (fused after the key lead chamfers):

| member | box / line | section | clearance (computed from layout; checks in 11.5) |
|---|---|---|---|
| bottom chord | x -150.15..-87.0, y 24.4..32.2, z 8.2..12.6 (through key_b2, web, key_b1) | 4.4 x 7.8 | 0.25 under the keeper bridge (z 12.85, as the keys); 0.5 off the keeper arm (y 23.9) and bar (x -86.5); 0.3 over the lip top; 1.35 off the rear wall |
| diagonal tie | (-107.5, 11.0) -> (-143.5, 47.5), runs into post_r; y 25.2..32.2 | 3.0 x 7.0 | 2.2 off the keeper bridge, 2.9 off the 18/24 switch box, 7+ off ko_hdmi_coil / ko_hdmi_run |
| rear upright | x -150.15..-147.15, y 25.2..32.2, z 8.2..58.3 (fuses the rear J3 rib and post_r's rear gusset) | 3.0 x 7.0 | 0.5 under the eyepiece box (z 58.8); 1.35 off the rear wall inner face |
| front upright | x -20.75..-17.75, y 25.2..32.2, z 8.2..87.0 | 3.0 x 7.0 | 0.25 off ko_run_cross (x -21), 1.25 off ko_run_rise, 1.5 off the X1203 (y 23.7), 4.75 off the tub rib_l, 3.0 under the hood rail |
| link to post_f | x -27.6..-17.75, y 25.2..32.2, z 84.0..87.0 | 3.0 x 7.0 | inside post_f's height band; clear of the camera keeper (z 66..76) |

All members grow from the inner face, i.e. upward in the face-down print: no overhang, no support, no bridge; the
frame adds about 5.3 cm3 (about 5 g ASA, estimate). Motion, tool and parts are unchanged from A: one straight -Y push
(the frame passes over the lip with the panel's own 0.3 seam and under the keeper bridge at 0.25), s_r1 + s_r2 from
the right with a PH1 straight driver, 2 PT screws, 11 printed parts, no loose piece, no flexure, no catch.
Registry (FR panel block): probes `panel_frame_chord_web`, `_chord_rear`, `_diag`, `_rear`, `_front`, `_link` (cls bar,
min 1.6, each at the member's narrowest section); `FR_JOINTS` += `FR_panel_frame` (required: the 6 frame probes +
panel_post_r_wall + panel_post_f_wall); `panel_off` note; `FR_VIEWS` += frp2-sec-y29 (section 3.5 mm inside the face
through the whole frame), frp2-sec-x125 (chord + tie), frp2-motion-on (assembly push). FR_REMOVED_FEATURES unchanged.

Support sensitivity (same model, each screw station as ONE pinned node plus a rotational spring 3EI/L of the 8 x 8 x 62
post, 29.7 N m/rad, instead of a held 8 x 8 footprint): seam x -98 r2 0.001 / A 0.31 / A2 0.10 / 2b 0.04 / 3 0.007;
bottom-edge worst r2 0.79 / A 1.13 / A2 0.65 / 2b 0.83 / 3 0.89; EVF cap r2 0.085 / A 0.093 / A2 0.050 / 2b 0.49 /
3 0.97. The ranking does not change; A2's seam is 0.06-0.10 mm/N over the two support assumptions (A 0.24-0.31).

### 11.5 Computed checks (build `out/_panel2-2`, D2_FR=panel, `--fast`, sweeps 2 mm, 11:34-11:42)

All 21 categories pass: contract 11, cots 20, interference 51, mate_overlap 30, clearance 12 (keeper bridge over the
keys 0.25), keepouts 81, bed_fit 11, stl_mesh 11, thin_wall 11, critical_features 109 (103 pass + the named
exceptions; the 6 new frame probes measure chord 4.4 / 4.4, diagonal 3.0, rear 3.0, front 3.0, link 3.0 against the
bar floor 1.6), evf_restraint 6, driver 5, engrave 10, boss_geometry 5, sweeps 12 (panel_on 37 positions, 0 hits),
removals 11 (panel_off 37 positions, 0 hits, strap + s_j + cap + pack fitted as geometry evidence), service_driver 4,
release_access 2, stack_retention 1, layout self-check 123, mass/CoM. Panel mass model 46.6 -> 51.3 g (manifest
estimate); body total 891 g with the Kowa lens. `cad_release_candidate: True` is the fork pipeline's computed flag only.
D2_FR=none `--part panel` (`out/_panel2-none`): panel.stl sha256 db433e49... = `../out/stl/panel.stl` (r2, identical).
printed_tub.py and printed_grip.py were not edited, so tub/base_grip are unchanged from A (`out/_panel-none` hashes).
Not run here: a merged D2_FR=all build (integrate-fork), renders of the new FR_VIEWS (render_fr1.py).

### 11.6 Decision and verdict

**Decision: A2 replaces A under `FR['panel']`.** It is the only 2-screw option that keeps the bottom edge, the EVF
restraint and the controls at or better than r2 except right at the old screw stations (seam between the keys 0.06
vs r2 about 0; ESTIMATE), with no extra screw, part, flexure, catch, tool or motion: still one straight -Y push and two
PH1 screws from the right. Trade-offs: +about 5 g ASA and a busier inner face (5 ribs, all support-free); the bottom
edge still has no positive +Y catch between the screws, it is stiff rather than held (2 N gives about 0.1 mm by
ESTIMATE); the front upright runs 0.25 from the run-lead crossing keep-out. Options 2 and 3 are rejected for EVF
restraint rigidity (EVF cap 3-9x softer than r2) and a second drive direction / base access (s. 11.3).
**Verdict: USER CHOICE, recommended over A**; physical gate G-FRP-1 (now incl. (c): front corner, EVF cap, frame roots)
decides. Computed: geometry, clearances, sweeps, probes. Not verified: every stiffness number (hand/grillage
ESTIMATE, no FEA, nothing printed or measured), print quality of the 7 mm ribs, PT post pull-out.

Re-run after integrate-fork merged the r3 checks into the fork (12:06): `out/_panel2-3` (D2_FR=panel, `--fast`, 2 mm
sweeps, 12:13-12:21): all 21 categories pass; critical_features 128 (119 pass + named exceptions) with CRITICAL_JOINTS
coverage: FR_panel_keys, FR_panel_closure and FR_panel_frame pass, every frame probe origin and span ray in material.
`panel_locate_rib_r` (r3 probe) now measures the rear J3 rib fused with the rear upright: 4.2 (floor 1.2).
A D2_FR=all build started during that merge (`out/_panel2-all`, 12:06-12:12, half-merged sources) had 2 failures, both
outside the panel: `tub_evf_groove_wall_bot_px` (new r3 missing-ray rule, offset -0.5) and "no CRITICAL_JOINTS
registry" (layout not yet merged when it started); interference, keepouts, sweeps and removals passed with the keeper
and hood changes in, and the 6 frame probes passed. The merged D2_FR=all result belongs to integrate-fork.
