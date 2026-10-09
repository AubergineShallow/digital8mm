# SPEC-C1: EVF pair slide with the HDMI plug (BX-1 BLOCKER, C-16, BX-7, BX-9)

Status: FINAL design spec after adversarial review (designer 2026-10-08 22:45-23:10; review 23:12-00:35 MPST). Nothing
in the repo was changed except this file. Review corrections are folded into the sections below and listed in section 10
(Review notes); review probes: session scratchpad `r7/C1-review/` (`rv1.py`, `rv2.py`, `rv3.py` + logs).

**r7 fix-up correction (VERIFY-C1, 2026-10-09).** The floor model below is wrong where it says "floor z 36.0 open from y 4
to the open side". The tub top at z 36 under the plug is only the stick-guide block (y 0..10.8). From y 11 to 26 the
slot is open down to the tub floor (z 2.5), which ramps to z 8 at the opening (y 32). So the tool-10 floor-edge lever
cannot be executed and is withdrawn everywhere: the push is a fingertip flat on the stick-guide top, or straight up
from the open well (`ACCESS acc_hdmi_evf_push_well`, B(-146, -132, 11, 26, 3, 46), push_of `p_hdmi_evf`, 0 mm3,
43 mm of room), with tool 10 only as an upright push stick. Every lever statement below is superseded by this note.
Source: `guide/BLOCKERS-2026-10-08.md` (BX-1, BX-7, BX-9, C-5, C-6, C-16). Geometry: `layout.py` (imported) and the
r6 assembly-pose part STEPs in `out/step/parts/` (16:05 build). Probes (session scratchpad `r7/C1/`, not in the repo):
`carry.py` (carried bodies swept along INSERTIONS, the suggested tub cut, rail sections), `insitu.py` (in-situ plug
path, hand and tweezer corridors, foam pad, FPC stiffener), `neck.py` (rail sections, HDMI boot path). Method: an
axis-aligned box swept along a piecewise axis-aligned path is a union of hull boxes. Each is intersected (cadquery,
exact) with the printed STEPs, the COTS boxes from `layout.COTS`, and the active keep-outs of that step's `sweeps` row
in `out/checks.json`.

## 1. Problem, re-checked against the current code

| item | BLOCKERS says | re-check (r7 probe) | verdict |
|---|---|---|---|
| BX-1 clash | mated plug (`ko_hdmi_evf` x -144.8..-136.8, z 52..63.8) swept y 4 -> 62 hits tub 63.3 mm3, bbox x -139.95..-136.8, y 18.0..28.5, z 61.5..63.75; hood 0 | tub **63.26 mm3**, bbox **x -139.95..-136.8, y 18.0..28.5, z 61.5..63.75**. No other step-6 obstacle and no active keep-out is hit | confirmed, numbers correct |
| why the sweep missed it | plug not in the `evf_pair_in` moving set | `check_sweeps` sweeps only `ins['moving']` part rows. A cable keep-out joins the obstacles only when **neither** end of its cable is moving (`checks.py` ~608). `hdmi` ends = (pi5, evf_board), so `ko_hdmi_evf` is neither swept nor an obstacle | confirmed: a defect class, not a one-off |
| what is in the way | "rail body below the groove floor stays full width from y 18" | Rail sections (x -141..-133, z 60..66): y 0.7..3.0 full rail (31.2 mm3, x -139.95..-135.25, z 61.5..65.25). y 3..18 +X spine only (x -136.55..-134.6). **y 18.9..28.5: a floor slab only**, x -139.95..-136.56, z 61.5..63.75 (67.5 mm3). The switch-box cut (`sw['y'][0] - SEAM` = 18.9) already removed the +X wall there. The slab hangs from the spine through a 0.9 mm root (sections: y 18.45 6.45 mm2, y 19.2 3.24 mm2, y 22..25 7.63 mm2) | BLOCKERS' "keep the +X spine" has nothing to keep beyond y 18.9 |
| what the slab does | not stated | It is the **only -Z arrest under the PCB's +Y half**. The other floor is y 1.0..3.0, 2 mm long. `evf_restraint` -Z = 0.25 (tub) holds because it only translates the board | new finding (see 2) |
| C-16 / s7 item 7 | inherits BX-1 | same clash in reverse (`evf_out` uses `reverse_of='evf_pair_in'`) | confirmed |
| BX-7 foam pad | pad is an obstacle in `eyepiece_in` and `evf_pair_in` | `eyepiece_in` and `evf_pair_in` obstacle lists both contain `foam_pad`; `evf_out` lists it in `off` ("loose foam pad, lifted out") | confirmed |
| BX-9 junction tuck | 30-56 mm in, under the hood, ahead of the board | `ko_5v_end` y -24..1.5 vs the open side y 32.2: 30.7..56.2 mm deep. A corridor beside the board's +X face, above the bottom rail (x -136.4..-130.1, y -24..32.2, z 65.6..80), is **0 mm3** against every step-6 part and keep-out | confirmed; a clear path exists |

## 2. Decision

**Chosen fix (A): sequence change, made a computed procedure.** At step 6, mate the OLED flex and the 5 V PH outside
the body, with the foam pad stuck to the OLED. Slide the pair home. Then push the HDMI plug **up into the board through
the existing rail gap** (y 3..18) from the open left side. No printed geometry changes. The defect class is closed by
checks: rigid connector bodies that are already mated ride with every later insertion that moves their part (section
4).

**The suggested tub cut (B) was evaluated and rejected.** B cuts the bottom rail under the plug from g1 to yend, full
height. It clears the plug path: computed 0 mm3, and still 0 mm3 with the envelope grown 0.6 in +X. It removes 69.7 mm3
of tub. But it deletes the y 18.9..28.5 slab, the only -Z support under the PCB's +Y half. The plug envelope spans the
whole PCB thickness (x -144.8..-136.8 vs PCB -138.4..-136.8), and every y from 4 to 62 lies on its slide path. So no tub
support under the PCB edge beyond y 3 can survive a slide with the plug mated. The 18/24 switch box (x >= -135.5,
y >= 19.2) also blocks any support from the +X side. With B, the board rests on the y 1..3 floor only and is free to
tilt in its plane (+Y end down) with the panel off. The top edge leaves its 1.5 mm groove at about 2.5 deg, with
nothing below to stop it. That happens between steps 6 and 8, and in every service with the panel off. With the panel
on, its EVF stop (z 70..86, gap 0.3) caps the +Y lower-corner drop at 0.25 + 25 x 0.3/22.25 = **0.59 mm** (hand
calculation from the layout numbers; limit 0.6). `evf_restraint` would still pass, because it only translates the
board. B therefore swaps a hard stop for an unsupported board. A panel heel would fix only the panel-on state.

Other options considered: (C) rotate the board in its plane so the receptacle faces -Y and the plug leads the slide
between the rails. That is a re-layout around an unmeasured board (receptacle and ZIF positions are estimates), so it
was rejected for r7. (D) Fit the board from above before the hood, with a hood-borne top groove. That is a major
re-architecture of steps 5 and 6. (E) A separate printed heel slid under the PCB after the slide. Its only seat would
be the 1.6 mm spine or the plug path. All three rejected.

Why A is acceptable: the in-situ plug path and finger-size hand corridors compute **0 mm3** (section 3.4), so the space
exists. [R] The real room round the plug (review probes, step-6 parts): the slot under the board is x -149.4..-131.6
(17.8 wide; rear wall at x -151.5, eyepiece at x <= -149.5 above z 58.75), floor (tub top) at **z 36.0**, open from
y 4 to the open side y 32.2; the -X side of the plug has 6.6 mm to the wall (4.7 above z 58.75), the +X side is open.
A fingertip therefore cannot sit under the plug while it travels under the slab (plug bottom z 40, 4 mm above the
floor) and cannot pinch the plug's -X face. So the mate is done in two phases: (1) the plug, held by its +X face and
its +Y end, goes in -Y under the slab end and is lifted to the receptacle mouth (hand-guided, no force); (2) the
mating stroke is pushed from below with a fingertip, which has z 36.0..(52 - stroke) = **10 mm** of room for a 6 mm
stroke [estimate, MP-HDMI], or, if the fingertip does not fit, with the steel rule (tool 10) used as a lever on the
floor edge at the open side. The mating push (+Z) goes PCB -> top groove roof (z 92.75, continuous over y 1..28,
computed; gap 0.25) -> top rail -> hood right-edge lip (rail top 0.3 under the lip). The plug is keyed and pushed
straight up. Its weak point is service unplugging (pull -Z): no finger fits the 6.6 mm -X gap, so the plug is pulled
with smooth-jaw long-nose pliers (jaws in x on the overmold's -Y half, y 4..12, z 52..61.4; both jaw boxes compute
0 mm3). That load reaches the y 18.9..28.5 slab, whose root is weak (section 6), so a fingertip from the +X side backs
the slab's free end (y 23..28.5, computed 0 mm3) while the plug is pulled. This is a physical gate on the first print
(G-EVF-3, section 7); the joint two-hand configuration is not computed, only each corridor.

BX-7: **the pad is stuck to the OLED back** (PSA side or a dot of the kit's adhesive) on the bench and travels with
the pair. BX-9: **sequence**. The junction rides in above the bottom rail beside the board and is pushed into `ko_5v_end`
once the board is home, before the HDMI plug, along a computed corridor. No keep-out change.

## 3. Implementation

### 3.1 Printed parts and COTS

No change to `printed_tub.py`, `printed_panel.py`, `printed_hood.py` or `cots.py`. The rail gap, the slab and the
`plug_x_clear` spine stay as in r6. Do not touch `printed_tub.py`, not even its comments: it is a receipt source and
its STL must stay byte-identical. The note goes into the `layout.EVF['board_slot']` comment instead: "r7 C1: the HDMI
plug is pushed up through the gap AFTER the slide. It cannot ride the slide: the y 18.9..28.5 slab is the board's -Z
arrest. See SPEC-C1."

### 3.2 layout.py

1. **STEPS step 6 `action`** (replace the text):
   "Push the eyepiece spigot +X into the rear-wall bore through the housing, flange on the rear face. On the bench:
   stick the foam pad to the OLED back (adhesive side to the OLED, centred). Fit the flex into the board ZIF and close
   the latch. Mate the 5 V PH junction (pull the lead ends out of the open left side). Do NOT plug the HDMI yet. Slide
   the OLED and the board in together as a tethered pair (OLED and pad into the cell, board into its slot) until the
   board stops. Keep the PH junction riding above the bottom rail, beside the board's +X face. When the board is home,
   push the junction -Y and down into ko_5v_end with the 120 mm tweezers. Then (only after gate G-W7 passed) hold the
   right-angle HDMI plug by its +X face and +Y end, cable leading -Y, and feed it in from the open left side low over
   the floor (plug top below z 52) under the bottom-rail end to below the board's receptacle. Lift it to the
   receptacle mouth, then push it straight up until it seats, with a fingertip under the plug; if the fingertip does
   not fit, lay the steel rule (tool 10) on the floor with its tip under the plug and press its outer end down over
   the floor edge at the open side. Never lever against the board. Coil the HDMI slack over the stick guide
   (ko_hdmi_coil)."
   (The junction is tucked before the HDMI plug: it is tied to the board by its pigtail, and its corridor, x >= -136.4,
   z >= 65.6, never crosses the plug's corridor, x <= -136.8, z <= 63.8.)
   `adds` unchanged. `tool` = 'tweezers (120 mm, tool 8); steel rule (tool 10) as an HDMI push lever if a fingertip
   does not fit'.
2. **INSERTIONS `evf_pair_in`**: `moving=['hmx039', 'foam_pad', 'evf_board']`, path unchanged. Comment: "r7 C1: pad
   stuck to the OLED (BX-7); HDMI plug mated after (PLUGS p_hdmi_evf)". This also takes `foam_pad` out of the
   `eyepiece_in` obstacle list (it becomes a later same-step mover). That is correct: the pad arrives with the pair.
3. **MATES: no change** [R]. Keep `('hmx039', 'foam_pad', 'contact')`. (The designer's 'bonded PSA' kind would have
   weakened two checks: `check_mate_overlap` only tests kinds contact/slide/clearance, so the hmx039/foam_pad
   no-overlap row would silently disappear, and `check_interference` exempts every declared non-interference kind.)
   A PSA bond is a zero-gap contact face, which is exactly what 'contact' checks. Record the bond instead in
   `LATCH_FREE` (item 9), the step text and the BOM D2-45 text. Leave `COTS['foam_pad']` unchanged (its proxy and the
   COTS STEPs stay byte-identical). Thickness: the pad's +X face has no tub material along the whole slide up to the
   board envelope (x -145.07..-144.8 swept, 0 mm3, review probe), so pad + PSA may be up to 1.25 thick before it
   touches the board envelope; G-EVF-1 (focus with the foam pad) and MP-EVF record the real thickness.
4. **New `PLUGS` registry**, placed after `CABLE_ENDS`, with one entry per cable end. Fields:
   - `id`, `cable`, `end` (a part id);
   - `box`: a KEEPOUTS id or a `B(...)`, final pose; `None` when the connector body lies inside the end part's own
     box, or when it is a flexible tail only;
   - `rigid` (bool);
   - `mated`: `('before'|'after', insertion id)`, or `('bench', step)` for joints made before the part's first
     insertion;
   - optional `path`: displacement waypoints of the plug's own in-situ mating move, last = (0, 0, 0);
   - optional `head` (box, final pose) and `stroke` (mm) [R]: the plug shell/tongue that enters the end part's
     receptacle zone. `plug_in` sweeps body + head; the head's last `stroke` mm of travel is the mating and is exempt
     against the end part only. For `p_hdmi_evf`: head = `B(-144.8, -138.4, 4.0, 17.0, 63.8, 63.8 + stroke)` (the
     receptacle footprint of `checks._evf_board_zones`), `stroke = 6.0` [estimate; MP-HDMI measures it];
   - `why`.
   Rows needed [R]: one per (cable, end) of `CABLE_ENDS` = **20 entries** (10 cables x 2). The designer's table had 19:
   `(pack_lead, xt30_pair)` was missing, which would make the new coverage row fail on the first build.

   | id | cable | end | box | rigid | mated | path / note |
   |---|---|---|---|---|---|---|
   | p_hdmi_evf | hdmi | evf_board | ko_hdmi_evf | yes | ('after', 'evf_pair_in') | [(0, 30, -12), (0, 0, -12), (0, 0, 0)], in situ through the rail gap; head + stroke 6.0 [R] |
   | p_hdmi_pi | hdmi | pi5 | ko_hdmi_pi | yes | ('after', 'keeper_in') | C-13 |
   | p_fpc_pi | fpc | pi5 | None | no | ('after', 'keeper_in') | latch on the Pi; the flex is the tail |
   | p_fpc_cam | fpc | gs_camera | ko_fpc_stiff (new) | yes | ('before', 'camera_in') | stiffener 3 mm behind the cover |
   | p_usb_pi | usb_5v | pi5 | ko_usb_evf | yes | ('after', 'keeper_in') | USB-A |
   | p_5v_board | usb_5v | evf_board | None | no | ('before', 'evf_pair_in') | pigtail + PH junction: flexible tail (BX-9) |
   | p_flex_oled, p_flex_board | oled_flex | hmx039, evf_board | None | no | ('bench', 6) | both ends ride together |
   | p_qt_enc | qt | encoder | ko_qt_plug (new) | yes | ('before', 'panel_on') | JST-SH at the encoder |
   | p_qt_hdr | qt | pi5 | ko_qt_lead | yes | ('after', 'keeper_in') | |
   | p_run_btn | run_lead | run_button | None | no | ('bench', 3) | pre-wired inside the button box |
   | p_run_hdr, p_fps_hdr | run_lead, fps_lead | pi5 | ko_run_leads | yes | ('after', 'keeper_in') | |
   | p_fps_sw | fps_lead | switch_1824 | None | no | ('bench', 2) | lugs inside the switch box; PH pigtail and junction flexible |
   | p_pig_pads | pigtail | x1203 | None [Plan edit P1-2] | no [P1-2] | ('bench', 1) [R: soldered at step 1] | solder pads + RTV bead inside the x1203 box; the pre-formed wrap and leg are C3 `pi_in` riders |
   | p_pig_xt30 | pigtail | xt30_pair | None | no | ('before', 'pack_in') | the xt30_pair box is itself in `pack_in` (BX-3 owns the mate pose) |
   | p_pack | pack_lead | pack | None | no | ('bench', 10) | the pack's own lead, inside ko_xt30 and the pack |
   | p_pack_xt30 [R, was missing] | pack_lead | xt30_pair | None | no | ('before', 'pack_in') | the male XT30 half lies inside the `xt30_pair` box, a `pack_in` mover |
   | p_fan_cooler, p_fan_pi | fan | cooler, pi5 | None | no | ('bench', 1) | both ends ride together in `pi_in` |

5. **New KEEPOUTS** (geometry only). The `keepouts` check then keeps printed parts out of them, as for every keep-out.
   - `ko_fpc_stiff` = `B(cam_cover_rear() - 3.0, cam_cover_rear(), -w/2, w/2, zs, zs + h)`, where
     `w, h = CAM['fpc_socket']['w'], ['h']` and `zs` = camera axis z - `CAM['cover']['sq']`/2 +
     `fpc_socket['z_above_bottom']`. At the assembly pose this is x -28.09..-25.09, y -8.5..8.5, z 41.25..46.25. It
     lies inside `ko_fpc_cam` (x -32.07..-24.04), so the reserved volume does not grow. Derive it from
     `cam_cover_rear` so it follows the J7-R `s`. Tag "estimate (FPC stiffener about 3 mm proud; MP-CAM)".
   - [Plan edit P1-1: box superseded by SPEC-C2's `B(-80.0, -75.7, 19.0, 24.6, 51.0, 61.0)`, which C2 adds to the
     `qt` via.] `ko_qt_plug`: the JST-SH plug on the used encoder socket. That socket is at `ENCODER['c']` x - 9.5 (x
     -74.65..-70.35, y 19.6..24.1, z ez +-3). The plug and the wire bend protrude 8 mm in -X:
     `B(ex - 11.65 - 8.0, ex - 11.65, 19.0, 24.1, ez - 3.5, ez + 3.5)` = x -82.65..-74.65, y 19.0..24.1,
     z 53.5..60.5. **Do not add it to the `qt` `via` in C1.** `ko_lead_cross` ends at z 44, about 9.5 below it, so
     `cable_routes` continuity would fail; that link belongs to the BX-2 cluster (QT lead length and route). If BX-2
     adds a link keep-out, append `ko_qt_plug` after it. If BX-2 changes the socket in use, re-derive this box with the
     same formula. Tag "estimate (SHR-04V-S + bend; MP-ENC)".
   - Probe (`qtko.py`): both new boxes, and the +X-socket alternative, hold 0 mm3 of panel, hood, tub, lens_collar
     and pi_keeper in the final pose. The `keepouts` check stays green.
6. **New `KEEPOUT_KIND`** dict. `'plug'` for `ko_hdmi_pi`, `ko_hdmi_evf`, `ko_usb_evf`, `ko_qt_lead`,
   `ko_run_leads`, `ko_qt_plug`, `ko_fpc_stiff` and `ko_xt30`; default `'cable'` for every other keep-out (runs,
   links, coils, loops, wraps). Used only by the carried-body rule in 4.1.
7. **New `ACCESS` list**: hand or tool corridors that must be empty at a given moment. Each entry is
   `dict(id, step, after=<insertion id> | state='service:<REMOVALS id>', box=B(...), tool, why)`:
   [R] The designer's hand boxes were 9 mm wide (x -146..-137), narrower than a fingertip (14-16 [estimate]), and the
   "finger column" put a finger where the plug is. Replaced by finger- and tool-size boxes; an optional `ignore` lists
   the destination keep-out of a tuck. All computed 0 mm3 against the parts present then and overlap no other
   keep-out except where noted (review probe `rv3.py`):
   - `acc_hdmi_evf_hand`: step 6, after `evf_pair_in`, `B(-149.4, -131.6, 4.0, SPLIT, 36.0, 58.5)`. "Hand and plug
     travel under the bottom-rail end, low over the floor (z 36.0)." 0 mm3. [fix-up: z 36 is the stick-guide top at
     y < 10.8 only; beyond it the open well, tub floor z 2.5]
   - `acc_hdmi_evf_push`: step 6, after `evf_pair_in`, `B(-146.0, -132.0, 4.0, 17.0, 36.0, 52.0 - stroke)` (z1 = 46.0
     at stroke 6.0). "Fingertip under the plug for the mating stroke." 0 mm3. Extra pass rule: height z1 - 36.0 >=
     `FINGERTIP_MM` = 9.0 [estimate]; below that the row passes only as `lever` (the tool-10 method, which needs only
     the hand box) and says so.
   - `acc_5v_tuck`: step 6, after `evf_pair_in`, `B(-136.4, -130.1, -24.0, SPLIT, 65.6, 76.0)`, tool 8 (120 mm
     tweezers), `ignore=['ko_5v_end']` (its destination). "The PH junction is pushed -Y over the bottom-rail spine
     (top z 65.25) beside the board, then into ko_5v_end (BX-9)." 0 mm3.
   - `acc_hdmi_evf_jaws`: state 'service:evf_out', two boxes `B(-147.0, -144.8, 4.0, 12.0, 52.0, 61.4)` and
     `B(-136.8, -134.6, 4.0, 12.0, 52.0, 61.4)`. "Smooth-jaw long-nose pliers grip the overmold's -Y half (tip <= 2.0
     thick; -X gap 6.6 mm)." 0 / 0 mm3. Gripping at y 4..12 (pull line about y 8) also cuts the slab's share of the
     pull from about 40 % to about 28 % (lever estimate, section 6).
   - `acc_evf_slab_back`: state 'service:evf_out' (panel off), `B(-140.0, -128.0, 23.0, 28.5, 51.0, 61.4)`.
     "Fingertip from the +X side under the slab's free end while the plug is pulled." 0 mm3.
   - `acc_hdmi_evf_hand_svc`: state 'service:evf_out', same box as `acc_hdmi_evf_hand`. 0 mm3.
8. **REMOVALS `evf_out`**: `moving=['hmx039', 'foam_pad', 'evf_board']`. Remove `'foam_pad'` from `off`. New field
   `unplug=['p_hdmi_evf']`: plugs parted in place before the move, so they are not carried (see 4.1). `tool='smooth-jaw
   long-nose pliers (new tool, next free number) on the HDMI overmold, -Y half, pulled straight down through the rail gap first with a
   fingertip from +X under the slab free end; tweezers (tool 8) lift the PH junction out of ko_5v_end'`.
   `note='panel off; HDMI out first; pair + pad +Y 45 out of the grooves'`. [R] Also remove `'eyepiece'` from
   `evf_out['off']`: the s7 text slides the pair out before the eyepiece (reverse order), and the reversed path with
   the eyepiece present is the `evf_pair_in` sweep, which passes with the eyepiece as an obstacle; this makes the
   removal row stricter, not weaker.
   Also add `unplug` to **REMOVALS `pi_out`**: `['p_hdmi_pi', 'p_usb_pi', 'p_qt_hdr', 'p_run_hdr', 'p_fps_hdr']`, as
   s7 item 10a already unplugs the header leads, HDMI, FPC and 5 V lead before the stack lifts. `p_pig_pads` stays carried (reverse
   of `pi_in`, computed 0 mm3). `camera_out` (FPC parted at the Pi) carries `p_fpc_cam`: same soft 0.75 mm as
   camera_in. `panel_off` carries `p_qt_enc` (computed 0). The other entries carry nothing.
9. **LATCH_FREE['foam_pad']** = "stuck to the OLED back (PSA); comes out with the pair (r7 C1)". The other REMOVALS
   entries keep `foam_pad` in their `off` lists.
10. [R] **`FINGERTIP_MM = 9.0`** (estimate, used only by the `acc_hdmi_evf_push` row) next to the ACCESS list, and
   `CARRY_SOFT_MM = 1.0` (section 4.1) next to `SWEEP_TOL` in checks.py.

### 3.3 make_tables.py (the harness rows behind ASSEMBLY step 6 and WIRING s7)

Replace the three step-6 rows (lines 93-95) with:
- `(6, 'flex -> EVF board ZIF', 'on the bench, contacts per the kit; foam pad stuck to the OLED back first',
  'ESD: grounded mat')`
- `(6, 'EVF 5 V lead PH -> board pigtail PH', 'outside the body, before the slide; junction rides in above the bottom
  rail and is pushed into ko_5v_end once the board is home', '**never mate live** (pack unplugged)')`
- `(6, 'micro-HDMI -> EVF board', 'in the body, AFTER the pair is home: plug fed in low under the rail end, lifted to
  the receptacle, pushed up (+Z) through the bottom-rail gap with a fingertip (or the tool-10 lever); right-angle plug,
  cable leaves -Y', '**only after gate G-W7 passed**')`

Also change the `oled_flex` routing string (line 49) to "...mated outside the body (pad stuck to the OLED), then the
OLED and the board go in together...".

### 3.4 Computed evidence for A (current r6 geometry)

| probe | box / path | result |
|---|---|---|
| plug in situ, board home | `ko_hdmi_evf` along (0,30,-12) -> (0,0,-12) -> (0,0,0); also dz -13 | 0 mm3 against all 20 step-6 ids and the 24 active keep-outs |
| boot (cable leaves -Y), hypothetical | x -143.3..-138.3, y -10..4, z 53..61, same path | 0 mm3. Tub material in x -144.8..-136.8, y -12..4, z 40..61.45: none |
| hand corridor (designer; superseded by `acc_hdmi_evf_hand`) | x -146..-137, y 4..32.2, z 40..60 | 0 mm3 |
| finger column (designer; superseded by `acc_hdmi_evf_push`, see 3.2-7) | x -146..-137, y 4..17, z 37..63.8 | 0 mm3 (an empty box, but too narrow for a finger and overlapping the plug's own path) |
| tuck corridor | x -136.4..-130.1, y -24..32.2, z 65.6..70 / 76 / 80 | 0 / 0 / 0 mm3 |
| foam pad with the pair | pad box along (0,45,0) -> 0 | 0 mm3 |
| r6 order (plug carried) | `ko_hdmi_evf` along `evf_pair_in` | 63.26 mm3 of tub: the regression the new rule must catch |
| [R] BX-1 re-run (review `rv1.py`) | same | **63.26 mm3** tub, bbox x -139.95..-136.8, y 18.0..28.5, z 61.5..63.75; hood and pi_keeper 0 |
| [R] floor under the PCB lower edge (tub top in x -138.4..-136.8, z 62.9..64, 1 mm y slices) | r6 tub | z 63.75 (gap 0.25) at y 1..3 and y 18..28; nothing at y 3..18 |
| [R] roof over the PCB top edge (tub + hood, z 92.5..93.6) | r6 | z 92.75 (gap 0.25) over every slice y 1..28 |
| [R] room round the plug | step-6 parts | slot x -151.5 (wall)..-131.6+, tub top z 36.0 only at y 0..10.8 (stick-guide block), open well to the tub floor z 2.5 at y 11..26, z 3..8 at y 27..34 [fix-up correction; was 'floor z 36.0 at y 4..32.2']; eyepiece x <= -149.5 above z 58.75; 15-wide finger boxes x -146..-131 and -149..-134, z 38..52: 0 mm3; z 27..40 under the start pose: tub (floor at 36) |
| [R] plug body + head (stroke 6) to the receptacle mouth | (0,30,dz) -> (0,0,dz) -> (0,0,-6), dz -12 and -9 | 0 mm3 against all step-6 parts incl. the board |
| [R] corrected ACCESS boxes (3.2-7) | step 6 / service evf_out | all 0 mm3; only `acc_5v_tuck` overlaps a keep-out (`ko_5v_end`, its destination) |
| [R] pad +X face to the board envelope | x -145.07..-144.8 swept along the slide | 0 mm3 of tub and hood (pad + PSA may be up to 1.25 thick) |

## 4. New and extended computed checks

### 4.1 `sweeps` (extended): mated connector bodies ride with their insertion

In `checks.check_sweeps`, add a helper `carried_plugs(L, ins)`. It returns the PLUGS entries with
`rigid and box and end in ins['moving'] and seq(mated) < seq(ins)`. Here `seq(ins)` = (step, index in INSERTIONS);
`('before', J)` sorts at J - 0.5, `('after', J)` at J + 0.5, and `('bench', s)` at (s, -1). For removals the
service state has every plug mated. So every rigid plug whose `end` is in `rem['moving']` is carried, unless its id
is in `rem['unplug']` (parted in place before the move).

Sweep each carried box as an extra mover (a box manifold), along the same path, against the same targets as the parts.
The cable's own keep-outs stay excluded: they already drop out because the cable has a moving end. Contact classes:
- **hard**: every solid, and every keep-out with `KEEPOUT_KIND == 'plug'`. Any overlap > `SWEEP_TOL` FAILs, as for
  part movers.
- **soft**: a `'cable'` keep-out (a flexible bundle that a hand can press aside). Penetration = the smallest extent of
  the intersection bbox. It passes when <= `CARRY_SOFT_MM` = 1.0 and is listed in a new row field `soft_contacts`.
  More than 1.0 FAILs.

New row fields: `carried` (plug ids) and `soft_contacts`. `check_removals` gets the same extension through
`reverse_of`. No existing pass criterion changes: part movers keep their current hard rule against every keep-out.

[R] **Second half of the defect class: the fixed end.** Today a cable with one moving end loses ALL its keep-outs from
the obstacle list, including the rigid plug at its other, fixed end. Add: for every cable with exactly one end in
`ins['moving']` (or `rem['moving']`), the `box` of the PLUGS entry at the non-moving end stays an obstacle (hard) when
that plug is mated at that moment (same `seq` rule). Its flexible via boxes stay excluded (the run follows the move by
design). Expected r7 values, by bbox separation (no boolean needed): evf_pair_in keeps `ko_hdmi_pi` (x >= -36.6) and
`ko_usb_evf` (x >= -125) as obstacles, movers at x <= -136.8: 0; panel_on keeps `ko_qt_lead` and `ko_run_leads`
(y <= -25.8), encoder and switch boxes at y >= 18.8 and the panel is the +Y side wall: expected 0 (the row computes
it); pack_in keeps `ko_pig_wrap` (z >= 2.7), pack and XT30 boxes at z <= -14.8: 0; camera_in: `p_fpc_pi` has no box:
nothing. Row field `fixed_end_obstacles`.

[R] Note on volumes: `check_sweeps` reports the worst single-position overlap (2 mm steps), not the swept-hull volume
of the probes. For BX-1 the plug (13 long in y) covers the whole y 18.0..28.5 slab at offsets y 11.5..14, which the
2 mm grid samples, so the row's worst value equals the hull figure (about 63 mm3, tessellation tolerance aside).

Expected results with the r7 layout (audit of every insertion; the computed numbers are from the r7 probes):

| insertion | step | rigid bodies mated earlier that ride with the moving set | computed | row |
|---|---|---|---|---|
| base_on | 3 | none (run-button joint inside its box; the lead is a flexible tail, BX-16) | - | pass, carried [] |
| pi_in | 4 | p_pig_pads (`ko_pig_wrap`); the pre-formed `ko_pig_under` was also probed | 0 / 0 mm3 | pass |
| keeper_in, hood_on, eyepiece_in, sd_in, collar_on, lens_in, stick_in, cap_on | - | none | - | pass, carried [] |
| evf_pair_in (r6 order) | 6 | p_hdmi_evf | **63.26 mm3 tub (hard)** | FAIL: BX-1 reproduced |
| evf_pair_in (r7 order) | 6 | none (HDMI mated after; flex, PH pigtail and pad are not rigid plugs; the pad is now a mover) | pad 0 | pass |
| camera_in | 7 | p_fpc_cam (`ko_fpc_stiff`) | solids 0; `ko_hdmi_run` (cable) 21.5 mm3, **0.75 mm** deep, x -39.19..-36.8, y 20..32, z 43.25..44 | pass, 1 soft contact (guide: press the HDMI run flat) |
| panel_on | 8 | p_qt_enc (`ko_qt_plug`); the +X socket alternative was probed too | 0 mm3 (both sockets) | pass |
| pack_in | 10 | XT30 junction = `xt30_pair`, already a mover | existing row pass | pass |
| pi_in: HDMI 90 deg plug? | 4 | no: mated after `keeper_in` (C-13) | - | not carried |

Note: with `ko_fpc_cam` (the whole S-fold box) taken as rigid, camera_in would show 198.7 mm3 in `ko_hdmi_run` and
18.9 mm3 in `ko_run_cross`. That box is a flexible loop, so it is not used.

### 4.2 New category `mate_paths` (registered in build_d2 next to `sweeps`: 28 -> 29 categories)

Row kinds:
1. **plug_in**: every PLUGS entry with a `path`. Sweep its box, and its `head` [R], along `path` at its mate moment,
   against `present_at(step)` (minus later same-step movers, minus screws), plus the end part, plus the hard keep-outs
   active then. The head's last `stroke` mm is exempt against the end part only (that is the mating). Its own cable's
   keep-outs are excluded, because the coil is laid after the plug. Pass: 0 mm3 (`SWEEP_TOL`) against everything.
   Expected `p_hdmi_evf`: 0 (computed for body + head, dz -12 and -9). Also report the final-pose gap to the board box
   (0.2 at z 63.8/64) and the head top while under the slab (57.8 vs slab bottom 61.5 at dz -12, stroke 6).
2. **access**: every `ACCESS` entry. Intersect its box with the parts present at that moment. For `after=J` that is
   present_at(step) with J's movers in their final pose; for `state='service:R'` it is the service state of R. Also
   intersect with the hard keep-outs active then (minus the entry's `ignore`). Pass: 0 mm3, plus the push-room
   height rule of `acc_hdmi_evf_push`. Expected: all six 0; push room 10.0 >= 9.0.
3. **coverage**: every (cable, end) pair in `CABLE_ENDS` has exactly one PLUGS entry (20 today [R]). Every `box` id exists in
   KEEPOUTS. Every `mated` insertion id exists. Every rigid plug whose `end` is moved by any insertion after its mate
   moment appears in that insertion's `carried` list. Pass: no gaps. This is what stops a new cable or a new insertion
   from silently skipping the rule.
4. **reach** (flexible tails mated in a pose other than the final one): for each cable whose end E is mated before an
   insertion that moves E, take straight distance d = |centre of E's plug box (or E's box) at the insertion's first
   waypoint - centre of the cable's last fixed via box|. Required: d + the cable's `cable_routes` route estimate of
   the fixed part + 2 x end allowance <= length. Rows for the C1 cables: usb_5v at the `evf_pair_in` start (C-5: about
   88 mm direct, length 200), fpc at the `camera_in` start (C-4: about 41 mm), oled_flex (both ends move: info). The
   qt (panel_on) and pigtail/pack rows are computed by the same code. Their pass/fail and any lead-length change
   **belong to the BX-2 and BX-3 clusters**. If those clusters have not yet landed, state `info`, not fail, with the
   number shown.

### 4.3 `evf_restraint` (extended): support span under the PCB edge

Add rows `support_span_final` (arrest tub + panel + hood) and `support_span_prepanel` (arrest tub + hood: the state
from step 6 to step 8 and in service with the panel off). Crop the PCB zone to its lower 1.0 mm band (z 64..65) in
1.0 mm y-slices. For each slice, find the -Z first contact with `_first_contact` (limit `max_travel_mm`). A slice is
"supported" when its gap <= `limit_mm` (0.6). Pass: a supported slice within 3.0 mm of **each** y end of the PCB
(y 1.0 and y 28.0), in both states. Expected r6/r7: supported y 1..3 and y 18.9..28 -> pass. With B's cut the +Y end
has no support within 8 mm -> FAIL. This makes the trade-off that rejected B computable. The existing six
translation rows are unchanged.

### 4.4 Planted-fault regressions (new `test_r7_c1.py`, style of `test_r3_regressions.py`; run through run_locked.py)

| test | plant | must happen |
|---|---|---|
| `test_bx1_plug_carried_fails` | copy of layout with `p_hdmi_evf['mated'] = ('before', 'evf_pair_in')` (the r6 order); rows built from the r6 STEPs or `build_d2` part cache | `sweeps` row evf_pair_in: status fail, a hit by `p_hdmi_evf` on `tub`, volume 60-66 mm3, bbox y 18.0..28.5 |
| `test_r7_order_passes` | real layout | evf_pair_in pass, `carried == []`; `mate_paths` plug_in p_hdmi_evf pass |
| `test_coverage_missing_plug` | delete the PLUGS entry for (hdmi, evf_board) | `mate_paths` coverage fail naming hdmi/evf_board |
| `test_soft_limit` | grow `ko_fpc_stiff` z0 by -1.5 (penetration about 2.25 mm into `ko_hdmi_run`) | camera_in fail, soft contact > 1.0 |
| `test_hard_plug_keepout` [R: was not deterministic; moving `ko_qt_plug` +y 10 hits nothing hard, the qt keep-outs are its own cable's] | add a synthetic cable `t_fix` (ends pi5 + tub, steps (4,)) whose via is one keep-out `ko_t` = `B(-80.0, -77.0, 26.0, 26.8, 55.0, 59.0)`: on the `ko_qt_plug` panel_on path only (x outside the encoder box x >= -75.65), 0.8 thick in y. Run twice: `KEEPOUT_KIND['ko_t'] = 'plug'` and `= 'cable'` | 'plug': panel_on fail, hit by `p_qt_enc` on `ko_t`; 'cable': pass with one soft contact of 0.8 (<= 1.0). Proves the hard/soft split |
| `test_fixed_end_obstacle` [R, new] | copy of layout with `ko_hdmi_pi` moved to `B(-142.0, -139.0, 40.0, 44.0, 70.0, 80.0)` (on the `evf_pair_in` path) | evf_pair_in fail, hit on `ko_hdmi_pi` listed in `fixed_end_obstacles` (today's code would pass it) |
| `test_mate_overlap_row_kept` [R, new] | real layout | `mate_overlap` still has the (hmx039, foam_pad) 'contact' row; MATES unchanged |
| `test_coverage_count` [R, new] | real layout | 20 PLUGS entries, one per `CABLE_ENDS` (cable, end); deleting `p_pack_xt30` fails coverage |
| `test_push_room` [R, new] | `p_hdmi_evf['stroke'] = 8.0` | `acc_hdmi_evf_push` height 8.0 < 9.0: row state `lever` (not fail), named in the row |
| `test_access_blocked` | add a synthetic 2 x 2 x 2 box solid at (-141, 25, 50) to the step-6 rows | `acc_hdmi_evf_hand` fail |
| `test_support_span_cut` | tub minus B's cut (two boxes from SPEC-C1 s2: x -140.05..-136.8 and -136.81..-136.2, y 18.0..28.6, z 61.4..65.35) | `support_span_prepanel` and `support_span_final` fail; the six translation rows still pass (shows why the new rows are needed) |
| `test_pad_moves_with_pair` | real layout | `foam_pad` not in the obstacles of `eyepiece_in` or `evf_pair_in`; `evf_out` moving contains it |

## 5. Document changes

- **ASSEMBLY.md step 6** (inside `<!-- BEGIN:steps -->`, generated): regenerate with make_tables after 3.2/3.3. The
  Motion row then reads `evf_pair_in (hmx039, foam_pad, evf_board)`. Add one Motion line, generated from PLUGS
  `path`: "`p_hdmi_evf` (HDMI plug): from offset (0, 30, -12) -Y 30 under the rail end, then +Z 12 into the board".
- **ASSEMBLY.md s3 checks, row 6** (line 264, hand-written), replace with: "Spigot flange flat on the rear face. OLED
  in its cell with the foam pad stuck to its back; board fully home in its slot; flex in the ZIF, latch closed (mated
  outside, pair slid in together). PH junction in `ko_5v_end`, clear of the bottom rail. HDMI plug pushed fully up
  into the board through the rail gap (no gap between the plug and the board edge: seen from the open left side with a small mirror, or felt with a fingertip).
  HDMI coil over the stick guide (`ko_hdmi_coil`), clear of the cooler inlet."
- **ASSEMBLY.md s7 item 7** (line 388), replace with: "7. EVF (reverse `evf_pair_in`, `eyepiece_in`; pack out, item
  1): uncoil the HDMI. Lift the 5 V PH junction out of `ko_5v_end` with tweezers (tool 8). Unplug the HDMI straight
  down through the bottom-rail gap: one fingertip, coming from the right of the board (+X), pushes up under the free
  end of the bottom-rail slab (y 23-28) while the pliers (new tool) grip the plug body on its left and right faces at
  its deep half and pull it straight down; never pull the cable, never rock the plug. Then slide the OLED, the pad
  and the board out together along +Y 45. Outside the body, part the PH junction and the flex. Pull the eyepiece out
  -X 30 through the housing." This closes C-16.
- **WIRING.md s7** (plug-order table, generated from the make_tables harness rows): regenerate. Check that the step-6
  rows read as in 3.3. Add to the WIRING s7 notes: "The EVF-end HDMI is mated in the body after the pair is home (r7
  C1, SPEC-C1): a plug mated outside cannot pass the bottom rail."
- **electronics/gs8-d2-v1/harness-schedule.csv**: in `hdmi` routing/notes, the board end is "plugged in the body after
  the pair is home, upward (+Z) through the bottom-rail gap from the open left side". In `oled_flex`: "...mated outside
  the body (foam pad stuck to the OLED back), then the OLED and the board go in together...". In `usb_5v`: "PH junction
  mated outside; rides in above the bottom rail beside the board; pushed into ko_5v_end once the board is home".
- **bom.csv D2-45** (then make_bom.py -> BOM.md): "Closed-cell foam sheet 1.0 mm, pressure-sensitive adhesive one
  side (OLED pad 16 x 14; stuck to the OLED back)". Same class and price figure. No other BOM row changes: D2-21 HDMI,
  the leads and the kit are unchanged.
- **MEASURED-PARTS.md**:
  - MP-HDMI gate text (line 113): replace "the board-end plug passes the slot gap y 4..17" with "the board-end plug
    overmold fits `ko_hdmi_evf` (x -144.8..-136.8, y 4..17, z 52..63.8) and its -Y boot stays below z 61 for y < 4;
    the plug is mated in situ (G-EVF-3)".
  - MP-ENC: "QT plug + bend protrude <= 8 mm beyond the socket (`ko_qt_plug`)".
  - MP-CAM: "FPC stiffener <= 3 mm proud of the cover rear (`ko_fpc_stiff`)".
  - MP-HDMI [R]: also record the board-end plug's **mating stroke** (shell/tongue length above the overmold; design
    value 6.0 [estimate]) and the overmold width; the `acc_hdmi_evf_push` room is 52 - stroke - 36.0.
  - New gate **G-EVF-3** (assembly operation, first print): five in-situ HDMI mate/unmate cycles through the gap,
    mating by fingertip (or the tool-10 lever: record which), unmating with the pliers on the -Y half and the
    fingertip backing from +X. Pass: the plug seats with fingertip force or the lever, never against the board; the
    board stays on its groove floor (feeler <= 0.6 at the +Y lower corner); no whitening or crack at the slab root
    (y 18.9) or the spine root (y 3.0); the PH junction goes into `ko_5v_end` with tool 8 in one attempt.
    Registration [R]: no build_d2 code change. `hardware_gates()` collects every `G-...` id from MEASURED-PARTS.md and
    SPEC.md by regex, and `STATE_GATES` classes `G-EVF-3` as `assembly_operation` (catch-all; the coupon regex only
    matches `EVF-2`), bound to every production STL. Do NOT use a `/whole` id: that suffix exists only for coupon
    gates split in `WHOLE_PART_TESTS`. Add G-EVF-3 to the MP-EVF row's gate list (MEASURED-PARTS s1 table) and to the
    SPEC.md physical-gate list next to G-EVF-2. The receipt's physical-gate count goes up by one.
- **ASSEMBLY.md tool list** [R]: add "smooth-jaw long-nose pliers, jaws >= 35 long, tips <= 2.0 thick (service item
  7: HDMI unplug)" at the next free tool number (15 unless another r7 cluster takes it first; then renumber the text
  references). The inspection mirror (head <= 15 mm) is optional and gets the number after it. Tool 10 (steel rule)
  gains "HDMI push lever (6)" in its "Used for" column.
- **guide/guide_steps.py**:
  - Page 6b `do`: insert first "Stick the foam pad to the OLED back (adhesive side to the OLED)". Keep "Do NOT plug
    the HDMI yet: it goes in after the slide (page 6c)" (drop "BX-1").
  - Page 6c `do`, in order: slide the pair home; "keep the PH junction riding above the bottom rail; when the board is
    home, push it -Y and down into its space with the 120 mm tweezers"; "hold the HDMI plug by its right face, feed it
    in low under the rail end, lift it to the socket, then push it straight up with a fingertip (or the steel-rule
    lever on the floor edge)"; coil the slack. `caution`: "Push the HDMI straight up. If it does not go, pull it back
    and re-aim; never lever against the board." `check`: "HDMI fully home (mirror or fingertip)", "junction in its
    space". `tools` = [8, 10, 12]. [R] Add the pliers to the guide's TOOLS list (guide_steps.py keeps its own copy of
    the ASSEMBLY tool table) with the same number.
  - Delete `ISSUES['6b']`. Replace `ISSUES['6c']` with a NOTE (no longer an issue): "Designed order (r7): the HDMI is
    plugged after the slide; first-print gate G-EVF-3." Delete the BX-7 and BX-9 entries in `TIPS['6c']` (now plain
    steps). The service page for s7 item 7 takes the new item-7 text. Rebuild the guide.
- **HANDOFF.md** (top): r7 C1 entry: decision A, B rejected (with its numbers), new checks and the gate.
- **DESIGN.md**: no "outside the body" or HDMI-plug wording found by grep, so no change. Any EVF-slot sentence gets
  "HDMI mated in situ after the slide".
- `guide/BLOCKERS-2026-10-08.md`: leave the record unchanged. The r7 response (main session) marks BX-1, C-16, BX-7 and
  BX-9 as resolved by SPEC-C1, and C-6 as now the designed procedure.

## 6. Interactions and risks

| check / area | effect |
|---|---|
| evf_restraint (6 translation rows) | no geometry change: +X 0.25, -X 0.25, +Y 0.30 (panel), -Y 0.31, +Z 0.25, -Z 0.25 stay. New support_span rows pass on r6 geometry |
| thin_wall, critical_features (J8_evf: groove walls and floor at y 2.0..3.0, roof, ends), print_overhang, bed_fit, stl_mesh, print_modifiers, boss_geometry, inserts | no printed geometry change; STL hashes must stay byte-identical (a receipt check) |
| keepouts | +2 keep-outs, both computed clear of every printed part (0 mm3) |
| sweeps | evf_pair_in gains `foam_pad` as a mover (computed 0); eyepiece_in loses `foam_pad` as an obstacle (it arrives later: correct; the eyepiece spigot ends at x -149.5, 3.4 short of the pad); camera_in reports 1 soft contact (0.75 mm into the HDMI run cable space); [R] every row gains `fixed_end_obstacles` (all 0 by separation) |
| mate_overlap, interference [R] | unchanged: MATES is not edited, so the (hmx039, foam_pad) 'contact' row stays |
| removals / service_driver | evf_out moves 3 ids; [R] `eyepiece` leaves its `off` list (stricter; same geometry as the passing evf_pair_in sweep); no screws involved |
| driver (11/11), j7_float, lens_support, lens_clamp | untouched (no screws, camera or collar change; `ko_fpc_stiff` lies inside `ko_fpc_cam`) |
| cable_routes | unchanged (`ko_qt_plug` is not added to the `qt` via; see 3.2-5) |
| mass_com | unchanged (pad mass already counted; no part added) |
| other clusters | BX-2 (QT lead, panel pose) owns the qt reach row and any QT link keep-out. BX-3 owns the XT30 reach row. Anyone changing the EVF slot, bottom rail, `ko_hdmi_evf`, `ko_5v_end`, the hood lip or the stick guide must re-run `mate_paths`. C1 edits only guide pages 6b/6c and s7 item 7 |

Risks:
1. **In-situ mating by feel.** The receptacle faces down and cannot be seen directly from the left opening. The path
   and corridors are computed clear; a small inspection mirror helps (optional tool, no BOM row). [R] The pushing
   fingertip has 10 mm under the plug only if the real stroke is about 6 mm (MP-HDMI); a fingertip is about 8-12
   thick [estimate]. The fallback lever (tool 10 on the floor edge, inner arm about 22 mm) needs no new part.
   Gate G-EVF-3 records which method worked.
2. **Service unplug loads the bottom-rail slab** (estimate). A 20 N straight pull at y 10.5, reacted at the y 1..3
   floor and the slab (centroid y 23.5), puts about 8 N on the slab, about 4.6 mm from its root. The root section is
   about 1.3 x 2.25 mm at y 18.9 (probe: 3.24 mm2 at y 19.2). That gives a bending stress of about 34 MPa, across the
   print layers (the tub prints right wall down, so +Y is the build direction). This is above an ASA interlayer
   strength of about 15-25 MPa [estimate]. Without backing, the slab can crack. The service text's fingertip backing
   puts the slab in compression, so it is required wording, and G-EVF-3 checks it. Assembly mating pushes +Z and does
   not load the slab. The r6 design already relies on this slab as the -Z arrest, so the risk is not new; only the
   service load is. [R] Re-check: lever split 20 x (10.5 - 2)/(23.5 - 2) = 7.9 N, section 1.44 x 2.25 (3.24 mm2),
   Z = 1.2 mm3, M = 7.9 x 4.6 = 36 N mm, about 30 MPa: same order as the designer's 34 MPa. A new micro-HDMI plug may
   need more than 20 N to pull (the class allows up to roughly 40 N [estimate, not a datasheet value]), which doubles
   it. Gripping the -Y half (pull line about y 8) cuts the share to about 28 % (5.6 N at 20 N). The backing finger is
   therefore required, not optional. If G-EVF-3 shows whitening, the fallback is a local root reinforcement of the
   slab at y 18.0..19.2 (printed_tub.py, outside the plug path x <= -136.8 / z <= 63.8 envelope), designed then; it is
   not designed in r7.
3. **Mating push path.** About 10-40 N +Z (micro-HDMI class insertion force [estimate]) goes PCB -> top groove roof ->
   top rail, which closes its 0.3 gap to the hood right-edge lip. The hood is on (step 5), so it is fine.
4. Envelope estimates (`ko_hdmi_evf`, boot, head/stroke, `ko_qt_plug`, `ko_fpc_stiff`) are unmeasured. MP-HDMI,
   MP-ENC and MP-CAM confirm them.
5. [R] **Two hands in one slot (service).** The pliers' jaws and the backing fingertip each have a computed clear box,
   but they share the slot under the board; the joint configuration (pliers inclined up from the opening, finger from
   the +X side above the jaws' path) is not computed. G-EVF-3 tests it.

## 7. Acceptance criteria (after the change and a full release rebuild through run_locked.py)

- All 28 existing categories pass. Numbers stay identical to r6 except: `sweeps` evf_pair_in moving = 3 ids with
  `foam_pad` gone from its obstacles and from eyepiece_in's; every row gains `carried`, `soft_contacts` and
  `fixed_end_obstacles`; camera_in shows `soft_contacts` = [ko_hdmi_run, 0.75 +-0.05 mm]; `removals` evf_out moving =
  3 ids with `eyepiece` as an obstacle; `mate_overlap` row count unchanged (hmx039/foam_pad 'contact' kept).
- New category `mate_paths` (29th) passes: plug_in p_hdmi_evf (body + head) 0 mm3; six access rows 0 mm3 and push
  room 10.0 >= 9.0; coverage 20/20 PLUGS entries, 0 gaps; reach usb_5v and fpc pass (qt, pigtail and pack rows pass or
  `info`, per BX-2 and BX-3).
- `evf_restraint`: the six translation rows unchanged, plus support_span_final and support_span_prepanel pass
  (supported slices y 1..3 and y 18..28, gap 0.25).
- `test_r7_c1.py` passes all 12 cases, including the planted r6-order failure (60-66 mm3 on the tub), the B-cut
  support_span failure, the hard/soft pair and the fixed-end plant. All existing test files still pass.
- STL hashes unchanged (no printed geometry change); COTS STEPs unchanged (no COTS edit).
- Hardware gates: G-EVF-3 appears as an `assembly_operation` item (auto-collected), physical-gate count +1.
- Physical: G-EVF-3 (new), G-HDMI (plug, boot and stroke within the envelopes), G-EVF-2 (existing stop feeler),
  MP-ENC, MP-CAM.

## 8. User decisions

One small item [R]: the service unplug needs smooth-jaw long-nose pliers (a hand tool, no BOM row; the user may
already own one). Confirm it can be added to the tool list. Without it, the HDMI can only be pulled by the cable or by
fingertips that do not fit the 6.6 mm -X gap. A uses no new parts and no printed geometry change. For the record: bench mating of the EVF HDMI (B) is
possible only with the tub cut, a panel heel, and a rule to keep the body right-wall-down whenever the panel is off.
Without that rule the board is unsupported at its +Y end during steps 6-8 and in every service. Not recommended;
choose it only if G-EVF-3 fails on the first print.

## 9. Effort and receipt sources

| work | hours |
|---|---|
| layout.py: STEPS[6], INSERTIONS, PLUGS (20), 2 KEEPOUTS, KEEPOUT_KIND, ACCESS (6), REMOVALS, LATCH_FREE, FINGERTIP_MM | 1.5 |
| checks.py: carried bodies + fixed-end obstacles in sweeps and removals, `mate_paths` (4 row kinds, head/stroke), support_span | 3.0 |
| build_d2.py: register `mate_paths` (29 categories); no gate code (G-EVF-3 is auto-collected); test_build_outputs category count | 0.25 |
| make_tables.py harness rows; regenerate ASSEMBLY/WIRING tables | 0.25 |
| test_r7_c1.py (12 cases) | 2.0 |
| docs: ASSEMBLY s3/s7 + tool list, harness-schedule.csv, bom.csv + make_bom, MEASURED-PARTS, SPEC gate list, HANDOFF | 1.0 |
| guide_steps.py (pages, TOOLS) and guide rebuild | 0.75 |
| full release rebuild + verification (one CAD job at a time) | 1.0 |
| **total** | **about 9.75** |

Receipt sources touched: `layout.py`, `checks.py`, `build_d2.py`, `make_tables.py`. These force a full release
rebuild and a new receipt. No `printed_*.py` or `cots.py` change, and no `COTS` entry change, so the STLs and part
STEPs should come out byte-identical; the receipt verifies that.

## 10. Review notes (adversarial review, 2026-10-08 23:12-00:35 MPST)

Review probes (session scratchpad `r7/C1-review/`): `rv1.py` (BX-1 re-run, neighbours, finger boxes, floor and roof
per y slice), `rv2.py` (floor height, start-pose finger room, pad +X face, fixed-end keep-out positions), `rv3.py`
(corrected ACCESS boxes, plug body + head path). All run through `run_locked.py`, one at a time, against the r6
assembly-pose STEPs (16:05 build). No repo file other than this spec was touched.

**Verified (own probes, numbers reproduced):**
- BX-1: 63.26 mm3 of tub, bbox x -139.95..-136.8, y 18.0..28.5, z 61.5..63.75; hood and pi_keeper 0. The miss is
  real: `check_sweeps` drops every keep-out of a cable with a moving end (code read at checks.py `active_ko`).
- The slab is the only -Z arrest at the board's +Y half: tub top z 63.75 (gap 0.25) under the PCB at y 1..3 and
  y 18..28, nothing at y 3..18. So B (the review's rail cut) removes all +Y support; rejecting B stands. The 0.59 mm
  panel-on corner figure for B was not re-derived (B is rejected on the computed support gap alone).
- The roof over the PCB top edge is continuous (z 92.75, gap 0.25, y 1..28): the in-situ push has a reaction.
- In-situ plug path clear: body and body + 6 mm head, dz -12 and -9, 0 mm3 against every step-6 part incl. the board.
- Foam pad stuck to the OLED: swept 0 mm3; its +X face has no tub along the slide (thickness tolerance up to 1.25).
- PH tuck corridor clear (0 mm3; only its destination `ko_5v_end` overlaps).
- Read from the designer's logs, not re-run: camera_in stiffener 0.75 mm into `ko_hdmi_run`, QT plug 0 mm3 on
  panel_on, `ko_pig_wrap` 0 mm3 on pi_in, removed volume of cut B 69.69 mm3.

**Changed (errors fixed):**
1. MATES `'bonded PSA'` withdrawn: it would have removed the hmx039/foam_pad row from `mate_overlap` (only
   contact/slide/clearance are tested) and exempted the pair in `interference`, a silent weakening. Kept 'contact'.
2. PLUGS coverage: the table had 19 of the 20 (cable, end) pairs; `(pack_lead, xt30_pair)` was missing, so the new
   coverage row would have failed. Added `p_pack_xt30`; `p_pig_pads` and `p_pack` mate moments made 'bench'.
3. G-EVF-3 registration: `/whole` ids exist only for coupon gates split in `WHOLE_PART_TESTS`. A plain G-EVF-3 in
   MEASURED-PARTS/SPEC is auto-collected and classed `assembly_operation`. No build_d2 gate code.
4. Hand access was not physically shown: the designer's corridors were 9 mm wide (narrower than a fingertip) and the
   "finger column" sat where the plug is. Real room computed: floor z 36.0, slot x -149.4..-131.6, -X gap 6.6 mm.
   Consequences: (a) no fingertip fits under the plug at the start pose (4 mm), so the mate is two-phase with the
   push from below over the last stroke (10 mm room at a 6 mm stroke [estimate]) and a tool-10 lever fallback;
   (b) no fingertip can pinch the plug for the service pull, so smooth-jaw long-nose pliers on the -Y half are
   specified (new hand tool, user confirmation in section 8), with the backing fingertip from the +X side. ACCESS
   boxes replaced by six finger/tool-size boxes, all computed 0 mm3.
5. Plug model: added `head` + `stroke` so `plug_in` covers the shell that enters the receptacle (it must pass under
   the slab: head top 57.8 vs 61.5 at dz -12).
6. Generalization completed: the fixed-end rigid plug of a cable whose other end moves now stays an obstacle (today it
   is dropped with the rest of the cable). Expected 0 everywhere in r7, by separation.
7. `test_hard_plug_keepout` was not deterministic (nothing hard on its path); replaced by a synthetic 0.8 mm keep-out
   run as 'plug' (must fail) and as 'cable' (must pass soft). Added fixed-end, mate_overlap-row, coverage-count and
   push-room tests (12 cases).
8. `evf_out`: `eyepiece` leaves `off` (the text slides the pair out first; stricter row, same passing geometry).
   COTS `foam_pad` left unchanged so the COTS STEPs stay byte-identical; the PSA is recorded in LATCH_FREE and the BOM.
9. Service slab stress re-checked (about 30 MPa at 20 N, same order as 34); a pull force above 20 N is possible, so
   backing is mandatory, and a root-reinforcement fallback is named for a G-EVF-3 failure (not designed in r7).

**Brief coverage:** rail-cut design evaluated and rejected with computed evidence (support gap, not just stiffness);
plug path computed along the whole in-situ move; carried-connector mechanism designed and every insertion audited
(15 rows, section 4.1); BX-7 (pad stuck, moves with the pair, obstacle lists fixed) and BX-9 (sequence + computed
corridor) closed; C-16 closed by the s7 item-7 text. Not met, by design: the brief hoped the step-6 order (all mates
outside) could be kept and the guide's interim order dropped. That is impossible without removing the board's
+Y support, so the interim order becomes the designed procedure, gated by G-EVF-3.

## Plan edits (integration, 2026-10-09 00:00-01:00 MPST; PLAN.md wins where it and this spec differ)

Plan edits: P1-1 `ko_qt_plug` geometry is owned by SPEC-C2: use C2's `B(-80.0, -75.7, 19.0, 24.6, 51.0, 61.0)`
(0.05 off the encoder box), not the 3.2-5 formula above. C2 adds it to the `qt` via. KEEPOUT_KIND stays 'plug'.
Re-run `test_hard_plug_keepout` with C2's box (hand check: the plug sweep still crosses `ko_t` y 26..26.8, hit about
9.6 mm3 as 'plug'; soft penetration 0.8 as 'cable').
Plan edits: P1-2 PLUGS `p_pig_pads`: `box=None, rigid=False` (the solder joints and RTV bead sit inside the x1203
box). The formed U and taped leg are SPEC-C3 `INSERTIONS['pi_in']['riders'] = ['ko_pig_wrap', 'ko_pig_under']`,
swept by the same carried-box routine (kind 'rider': hard against every obstacle). The 4.1 table row pi_in becomes
"riders ko_pig_wrap, ko_pig_under: 0 / 0 mm3".
Plan edits: P1-3 One carried-box routine in check_sweeps/check_removals serves C1 (PLUGS carried, hard/soft,
fixed-end obstacles), C2 (`stowed`, stow boxes in active_ko, header housings as obstacles from step 5) and C3
(`riders`, carried boxes become final-pose obstacles for LATER insertions of the same step). C2's INSERTIONS
`mated` field is dropped: `p_qt_enc` (mated ('before', 'panel_on')) is carried along the whole `panel_on` path.
Row field names: `carried` (plug ids and rider keep-out ids), `soft_contacts`, `fixed_end_obstacles`, `stowed`.
Plan edits: P1-4 `mate_paths` loses its `reach` row kind. Reach for every lead mated in a non-final pose is
SPEC-C2 `mate_reach` (one function, one margin helper `reach_margin(L, length)` = max(MATE_MARGIN,
ROUTE_ALLOWANCE[0], ROUTE_ALLOWANCE[1] x length), shared with C3). C1 owns a new MATE_POSES **inline** row `usb_5v_evf` (the PH junction joins the lead to the board's own 5 V pigtail): `inline_of='usb_5v'`, insertion `evf_pair_in`, `pigtail` credit 0.0 (the board pigtail is not modelled; MP-EVF records its length and exit point), `far` = (-136.8, 1.0, 67.0) (board +X face, -Y end, ko_5v_end z centre: the deepest credible pigtail root, estimate), anchor `ko_5v_up`, hand `pinch_ph`, row (0, 0, 1), `junction_out` 15, out_of ('+y', YL, 0.0), **disp (0, 60, 0)**. At disp 45 the junction point would sit only 13.8 beyond the opening (hand calculation, < 15), so `evf_pair_in` gets a start waypoint: path [(0, 60, 0), (0, 45, 0), (0, 0, 0)] (the pair is held a hand's width out while the junction is mated; the extra 15 mm is in free air). Step-6 text: 'Mate the 5 V PH junction with the pair held about 60 mm out of the open left side'. Hand calculation from the r6 cable_routes estimate (usb_5v 92.8): r1 about 200 - 70 - 20 = 110 against d about 86. The hand-box and out_of rows are 'info' with gate MP-EVF while the pigtail credit is 0 (the real junction sits further out than `far`); the reach and junction_out rows pass/fail. The fpc reach row is C2's `fpc_cam`.
Plan edits: P1-5 `mate_paths/coverage` gains the general rule (lands with SPEC-C2, step S3 of PLAN.md): for every
insertion J and every cable with exactly one end E moved by J, if the plug at E and the plug or inline junction at
the other end are both mated before J, a MATE_POSES row for (cable, J) must exist; rows whose both ends move are
'info'. Every MATE_POSES row names an existing PLUGS id (or `inline_of=<cable>`).
Plan edits: P1-6 Row status: `summarize` rejects unknown statuses, so the `acc_hdmi_evf_push` row is status
'pass' with field `push_method` = 'fingertip' or 'lever' (lever when the height < FINGERTIP_MM). `mate_paths` is
registered with `info_neutral=True`.
Plan edits: P1-7 Acceptance "STL hashes unchanged / COTS STEPs unchanged" is replaced by the combined r7 list in
PLAN.md s7 (tub, hood, collar_gauge and the new tools change; pi5 COTS STEP changes via C2). C1 alone still changes
no printed geometry. Category count: 36 in r7 (computed from the build summary, never hard-coded).
Plan edits: P1-8 Tool numbers (PLAN.md X-9): pliers = tool 15, optional inspection mirror = tool 17. Step-6 action
gets SPEC-C5's sentence appended ("From now until the panel is on (step 8) keep the body level or nose-down: only
the panel's EVF cap stops the eyepiece moving rearward."). All BOM text edits go into make_bom.py `LINES` (bom.csv
and BOM.md are generated).
Plan edits: P1-9 Box scan (integration, layout boxes only): `acc_hdmi_evf_hand` overlaps `ko_hdmi_coil` (2196 mm3)
and `ko_hdmi_evf` (676, the plug's destination); `acc_hdmi_evf_push` overlaps `ko_hdmi_coil` (792);
`acc_hdmi_evf_jaws` (+X box) overlaps `ko_hdmi_coil` (141). Not a clash in the designed order: the coil is laid
after the mate (step 6) and uncoiled first in service (s7 item 7). But the access rule must say so explicitly.
Give these ACCESS entries `ignore=['ko_hdmi_coil', 'ko_hdmi_evf']` with that reason, and add a coverage assertion:
an ignored keep-out must belong to a cable whose step text lays it after (or removes it before) the access moment.
Section 3.4's "only acc_5v_tuck overlaps a keep-out" holds for 'plug'-kind keep-outs only. The `switch_1824` COTS
box also overlaps `acc_hdmi_evf_hand`, `acc_5v_tuck` and `acc_evf_slab_back`. That is fine because the panel is off
at step 6 and in `evf_out`, but the access row must take its present set from the moment, never from step 10.
