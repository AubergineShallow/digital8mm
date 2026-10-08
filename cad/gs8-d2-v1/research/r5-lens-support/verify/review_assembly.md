# r5 review: assembly, service and manufacturing

Reviewer: assembly. Run on 2026-10-06, 16:50-17:05 +0800, time-boxed (wind-down 18:00). This was a read-only review.
No repo file was edited except this one, and no build was run. Evidence comes from:
- `out/checks.json` and `out/build-receipt.json`;
- `out/parts-manifest.json` and `out/coupons-manifest.json`;
- `layout.py`, `printed_collar.py`, `printed_tub.py`, `printed_hood.py`;
- ASSEMBLY / FASTENER-POLICY / SPEC / MEASURED-PARTS;
- `electronics/gs8-d2-v1/bom.csv`.

The STL probes ran in the scratchpad:
- the release STLs were mapped back from print pose to the assembly frame with `FACE_DOWN_ROT` and the manifest bboxes;
- the map was checked against the manifest bboxes to within 0.05;
- a numpy ray-parity point-in-solid test was sanity-checked on known tub and hood solids.

## Verdict

The build order works. The camera and adapter go in first. The collar and s_c1..s_c3 go on with the panel off. The lens goes through the collar while the camera is held from the open left side. s_c4 is the last operation on the lens, then the panel goes on.

The order is consistent across:
- `layout.STEPS` 7-10;
- the INSERTIONS (`collar_on`, `lens_in` before `panel_on`);
- REMOVALS (`collar_off` needs the lens and s_c4 off; `camera_out` works with the collar left on);
- ASSEMBLY s2/s7;
- the driver audits.

I found no blocker and no major. The findings below are minor and note items: the washer seat, bed-layer walls, sacrificial bridges, the B0 order, step-text wording and the G-COL-1 procedure.

## Findings

**A1 (minor, confirmed): the s_c4 washer seat has no clearance.**
- Washer ISO 7089 OD 7.0, centred at (4.7, -31.3):
  - the -Y-side washer edge sits exactly on the bit-relief wall at y -27.8 (`COLLAR.lug.bit_relief_y`);
  - the +X-side edge (x 8.2) overhangs the 0.6 bed chamfer on the upper lug's +X edge.
- STL probe at z 66.05: solid only for y > -27.8.
- Upper-lug top at z 65.95: flat from x 1.1 to 8.05 only. The washer spans x 1.2..8.2 and y -34.8..-27.8.
- With the 3.4 clearance (+-0.2 float) and FDM wall growth, the washer can ride on the wall root or the chamfer. That tilts the head and makes the pinch preload unreliable.
- **Fix:** do one of these:
  - trim the bit relief to y >= about -27.2 (the bit gap only grows);
  - spot-face a dia 7.6 x 0.3 seat;
  - use an ISO 7092 small-series washer (OD 6.0).

  Keep the bed chamfer off the upper-lug top edge.

**A2 (minor, confirmed geometry; outcome plausible): the 3 anchor washer seats bridge without a sacrificial layer.**
- In print pose (+X down), each washer seat (x 2.8, 5.8 above the bed) is an unsupported annulus: r 1.7..3.75 over the dia 7.5 counterbore, with the 3.4 hole in the middle.
- `printed_collar.py` cuts the counterbore from the seat to the front face (l.123). The PRINT note calls it a bridge.
- Bridge lines end in the 3.4 hole, so the clamp face droops. The washer then crushes the droop, and the anchor preload relaxes (LOAD_MODEL anchor 100 N).
- **Fix:** add a 1-layer membrane at x 2.8 (pierce it with 3.4 after printing), or use the 2-layer crossed-bridge trick. Say so in PRINT-GUIDE and in G-COL-1.

**A3 (note, confirmed): the bed-layer wall round the ear counterbores is 0.7-0.8.**
- The ear wall is 1.25 (r 5.0 vs counterbore r 3.75). The 0.6 x 45 deg outer bed chamfer leaves 0.70 at x 8.58 and 0.80 at x 8.50 (STL radial probe, TL ear).
- That is about 1.5 extrusion widths in the first layers, plus elephant foot.
- It carries no load, since the seat is 5.8 higher. Option: ear r 5.6, or a 0.3 chamfer on the ear lobes.

**A4 (minor, confirmed in the text): bench B0 removes the camera's only natural support before the lens goes on.**
- B0.2 takes the tripod block off. B0.4 then puts the 215 g Kowa on and aims it at infinity on live view (ASSEMBLY l.73-83).
- B0 says nothing about supporting the lens, so the brief rule "never thread the lens into an unsupported camera" is not addressed on the bench.
- B0 does not say how bench live view is obtained (Pi powered, which FPC) before steps 1-6.
- **Fix:**
  - do B0.3-B0.4 with the tripod block still on and the camera on a tripod or clamp (lens load goes housing -> block, not through the PCB joint), or with the lens in a V-block;
  - then take the block off (B0.2 last);
  - add a line on the bench live-view setup.

**A5 (minor/note, confirmed by STL probe): the step 8 hand-hold wording.**
- Finger room is fine. The tub and hood have 0 points in the corridor x -26..-6, y 20..32.2, z 42..80 to the cover's +Y face. Behind the cover, x -45..-25.5, all y, z 57..80, is empty too (the FPC loop is below z 56).
- With the panel off there is no rear stop. The camera can slide back at least 11 mm (`camera_in` path), while the lens is stopped by the cone, so the thread engages only if the camera is held forward.
- **Fix:** step 8 should say "press the camera forward (+X) from behind its cover until the BFAR meets the lip, and hold it while the thread starts". Today it says "a finger holds the camera cover".
- Step 8 also says "back s_c4 off", but s_c4 is first added at step 8 (step 7 adds only s_c1..s_c3). Reword to "fit s_c4 loosely", or add it loosely at step 7.

**A6 (note, plausible): lens swap with the panel on.**
- The keeper rear catch is 3.5 behind the cover at s 0 (`j7_float` body/panel axial 3.5).
- The lens on the cone reaches 6.7 behind the C flange. That figure is "C thread + rear cell", and the real thread length is not modelled.
- If the camera has drifted to the keeper at small s, thread start-up margin is unverified.
- **Fix:** ASSEMBLY s7 lens swap should tell the user to tip the body nose-down (camera forward onto the lip) before threading. Record the Kowa thread length at G-LENS.

**A7 (note, plausible): G-COL-1 does not fix the bolting order.**
- In the build, s_c1..s_c3 are torqued (step 7) before the s_c4 pinch (step 8).
- So the pinch must close a bore whose two halves are both anchored: the upper arc by TL/TR, the lower arc by LL. LR is compression only.
- LOAD_MODEL books the whole pinch (120 N x 0.5) as band clamp.
- **Fix:** SPEC s10 G-COL-1 should state "s_c1..s_c3 at 0.25 N m first, then s_c4", so the coupon measures the clamp the build actually gets.

**A8 (note): the short insert is a class, not a part.**
- D2-35 is "M3 short L 4.0, OD 4.6 class (procure)".
- Bore depth 4.2, engagement 3.9 (engage_min 3.0).
- A shorter procured insert (L 3.0 class) would sit at the engagement minimum.
- **Fix:** name a part, or have G-COL-1 record the actual insert and re-run `check_inserts`.

## Verified OK
- **Receipt:** every source sha256 in `build-receipt.json` matches the current files.
- **Steps 7-10:** they follow brief choice 7 (preferred order) and the IMPL s3 decision 4.
- **Driver audits:**
  - step 7: s_c1..s_c3 (-X) pass without the lens, bit 0.5 in the dia 7.5 counterbore;
  - step 8: s_c4 (-Z) passes with lens and panel present, bit 0.25, handle 6.5 to the hood;
  - service audit: s_c1..s_c3 pass. The audit set leaves out the lens, consistent with "lens off first" in `collar_off` and ASSEMBLY s7 6c.
- **Removals:** all pass. `collar_off` needs the lens and s_c4 off. `camera_out` works with the collar on. The lens swap needs no panel removal.
- **`check_inserts`:**
  - bores 4.0; depth 4.2 / 6.0;
  - walls 2.0 / 2.0 / 1.706 / 1.685 (>= 1.6);
  - engagement 3.9 / 5.3; tips in a void; under-washer 5.5 / 5.0.
- **Screw lengths:**
  - M3x10: head point 3.3, tip -6.7, inside the insert at -2.8..-6.8;
  - M3x16: 66.5 to 50.5, inside the insert at z 50.1..55.8. Slit closure only increases engagement; the tip exits into free air below the lug.
- **Insert access (B1):** the tub inserts go in from the front face with the tub empty, before step 3. The lug insert goes in from below the lower lug, off-body.
- **Print poses:**
  - the tub insert bosses are teardrops with the apex -Y (print down);
  - the tub lip and counterbore teardrops open +Y;
  - the hood foot holes are teardrops; foot-hole rings 2.5 / 2.5 / 2.686 (>= 1.2);
  - the roll fin (4.0 x 2.25 x 56.8 tall in print) is tied by 2 webs (4.8 bridge) to the stack fin;
  - the collar bore entry has a 0.6 lead-in chamfer at the bed face (the slit puts the bore edge on the outer wire; probe r 21.70 at x 8.55).
- **G-COL-1:** 3 coupons (collar_tub_front -Y, collar_hood_plate +Z, collar_part +X), in the release print poses.
- **BOM:** D2-35..D2-39 and D2-74 are present. The tripod block and its 2 screws are noted on D2-05.

## Not reviewed (deadline)
- The baseline-r4 diff (which outputs changed and why).
- A rotational sweep of lens threading. The Kowa thumb screws sit at x >= 15, ahead of the collar front at 8.6, so this is likely clear.
- The Fujinon variant's assembly and collar.
- The hood fin's print stability on a slicer.
- Judge and dossier facts.
- A CadQuery re-measure.
