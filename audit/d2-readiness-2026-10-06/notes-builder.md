# D2 r5 audit: builder readiness (auditor 3 of 3, "builder")

2026-10-06, read-only. Scope: could a competent maker print, buy and assemble D2 r5 from the documents alone.
Read: HANDOFF s0, ASSEMBLY, PRINT-GUIDE, FASTENER-POLICY, SPEC s10, MEASURED-PARTS (head + MP-CAM), DESIGN (spots),
OPTIONS (spots), evidence/README, electronics BOM.md / make_bom.py, WIRING (G-W11), out/checks.json (driver,
service_driver, inserts, j7_float, lens_clamp), parts-manifest, print table, renders step-07 and section-j7-y0,
STL hashes Kowa vs `out/_fujinon-r5`. No build run. Own view formed first; the internal review
(`research/r5-lens-support/verify/review_*.md`) read afterwards and each finding labelled.

Verified OK (my own checks):
- Print table sums: mass as printed 297.2 g, 100 % 370.7 g, time 16.0 h; they match the totals and HANDOFF s0.
- Modifier meshes on disk: 18 (tub 10 incl. s_c1..s_c3, panel 4, base_grip 4), as PRINT-GUIDE s1.1 lists.
- BOM M3 lines are generated from the `SCREWS` kind-M3 rows (make_bom.py:40-46, 99-103): 3 short inserts + 2 spare,
  1 L 5.7 insert, 3 x M3 x 10 + 1, 1 x M3 x 16 + 1, 4 washers + 2. These match FASTENER-POLICY I, ASSEMBLY s4 and
  the parts-manifest `m3_hw` row. PT: 7 used + 4 spare (D2-30). Option-C regulator lines are qty 0 and say "candidate".
- Screw stack-ups: s_c1..s_c3 head 3.3 -> tip -6.7, insert -2.8..-6.8; s_c4 66.5 -> 50.5, insert z 50.1..55.8.
- Driver audit (checks.json `driver`): s_c1..s_c3 (step 7, no lens) bit 0.5 to the collar; s_c4 (step 8, lens +
  panel present) bit 0.25, handle 6.5 to the hood. The axes match ASSEMBLY s4 and the geometry I read.
- tub, hood, panel and base_grip STLs are byte-identical between the Kowa and Fujinon builds. Only `lens_collar`
  differs, so the body is independent of the lens (relevant to B-1 and G3).

## Findings

### B-1 (major): the print order lets tub, hood and panel be printed before MP-CAM / G-CAM-1
- Evidence: PRINT-GUIDE.md:218-227 (s7). Coupons, then base_grip, tub, hood, panel. Only the G-COL-1 coupons and the
  collar wait for MP-CAM / G-LENS (lines 220-221, 225-226). HANDOFF.md:46-51 "do first" also gates only the collar
  coupons. But MEASURED-PARTS.md:28-29 and :98 say the tub lip / counterbore, hood roll fin and panel keeper "follow
  `CAM`". MEASURED-PARTS.md:13 ("MP-CAM ... before the full print set") is the only place that says so.
- Failure: a maker follows PRINT-GUIDE s7 and prints the tub (4.9 h), hood (2.7 h) and panel (2.4 h) on drawing-only
  `CAM` values (every one is `drawing`/`unconfirmed`). The j7_float gaps sit at their rules: body/tub axial 0.4 = rule.
  G2's possible 0.8 shift turns the keeper catch into a seat at s > 2.2. If so, all three parts are reprinted.
- Fix: PRINT-GUIDE s7 item 3/4 and HANDOFF "do first": "tub, hood, panel only after MP-CAM (G-CAM-1) has passed or
  `CAM` was updated and rebuilt". The collar additionally waits for G-LENS and G-COL-1.
- Review label: CONFIRMS G3 (gaps at rules). DISAGREES G3 in part: tub and panel do not depend on `LENSES` (the
  hashes are identical across lenses). A band-position change is absorbed by rebuilding the collar. The real gate
  for the body prints is MP-CAM, and it also covers the hood.

### B-2 (major): a lens swap can leave the C-CS adapter on the old lens; the next C lens then screws straight into CS
- Evidence: ASSEMBLY.md:79 (B0.3 "C-CS adapter ... hand-tight"); :354-355 and :400-407 (lens removal and swap:
  "unscrew the lens by hand", nothing about the adapter). The adapter is a 5 mm ring threaded into the BFAR. The lens
  C thread and the adapter-to-BFAR thread are the same 1"-32 size, both hand-tight, so either joint can break loose
  first. Afterwards the adapter can come out with the lens: its OD 30.75 passes the lip dia 32.4 and the collar bore.
- Failure: with the adapter on the removed lens, the user threads the next C lens (or the same lens after a check)
  directly into the BFAR CS thread. The lens then sits 5 mm deeper. The Kowa's rear protrusion (C - 6.7,
  MEASURED-PARTS.md:95) can reach the camera's filter or sensor cover: a damaged-part risk. Focus at infinity is
  also impossible, and the user may then "fix" it by re-setting s (B0) and lose the recorded value.
- Fix: B0.3: seat the adapter firmly and mark adapter and BFAR with a paint-pen line. Lens swap and s7 item 6a:
  "check that the adapter stayed in the camera (the mark lines up); if it came out with the lens, unscrew it from the
  lens and refit it to the camera (camera out, B0) before any lens goes in". Add the mark to the step 7 check row.

### B-3 (minor): M3 x 10 into a blind 4.2 bore has 0.2 mm of tip void (0.184 at s_c3), less than the screw length tolerance
- Evidence: checks.json `inserts`: s_c1/s_c2 `bore_depth` 4.2 = need 4.2; s_c3 `bore_depth_local_min` 4.184 <
  `bore_depth_need` 4.2, yet the status is pass. `tip_from_head` 10.0 against a bore end at 10.2 from the head.
  FASTENER-POLICY.md:177 ("0.1 below the face", bore x -2.8..-6.8). The ISO 7045 length tolerance for l = 10 is
  js15, about +-0.29. The ISO 7089 0.5 washer is 0.45-0.55, and the printed foot thickness and elephant foot add more.
- Failure: a long-tolerance screw, a thin washer or a slightly short foot bottoms the tip on the ASA bore floor
  (0.7 thick, boss end x -7.6) before head contact. The "stop at head contact" cue never comes; the user keeps
  turning; the floor bulges or the insert is jacked forward; the anchor has no preload. The local-min shortfall at
  s_c3 also shows that `check_inserts` passes a depth below its own need (tolerance hidden).
- Fix: add a dia 3.2 relief 0.5 deeper (to x -7.4) below the 4.0 insert bore. The insert keeps its seat, the tip
  gets 0.7 of void, and the boss envelope (x -7.6, `pi_in`) is unchanged. Make `check_inserts` compare
  local_min >= need. Also add "screw length <= 10.0 measured" to the B1 check.

### B-4 (minor): bench B0 hangs the 215 g lens on a bare camera, against the r5 lens rule; the live-view setup is unstated
- Evidence: ASSEMBLY.md:76-83 (B0.2 block off, then B0.4 lens on, live view, set BFAR) against :23 and SPEC.md:172
  "never thread the lens into an unsupported camera". B0 sits "before step 1", but live view needs a Pi with a
  flashed card (G-W3 is in step 1, :92), a bench PSU and the FPC.
- Failure: the user lays the camera on the bench on its cover with the lens cantilevered, or holds it by the PCB
  while turning the BFAR ring. This loads exactly the housing-to-PCB joint that r5 protects, before s is recorded.
  Or the user cannot do B0 at all until steps 1/G-W3 and finds out out of order.
- Fix: as A4. B0.3-4 with the tripod block still on and the camera on a tripod or clamp; block off last. Prerequisite
  line: "Pi on the bench PSU with the flashed card (G-W3) and the FPC; this is the only time the Pi runs before
  step 1".
- Review label: CONFIRMS A4.

### B-5 (minor): step 8 wording ("back s_c4 off"; "a finger holds the camera cover")
- Evidence: ASSEMBLY.md:191 and SPEC.md:168. s_c4 is first installed at step 8 (ASSEMBLY.md:196, :266), so there is
  nothing to back off. With the panel off, the camera has no rear stop.
- Failure: the user hunts for a screw that is not there, or fits s_c4 tight at step 7 and then cannot pass the band.
  Thread start-up is unreliable unless the camera is pressed forward.
- Fix: step 7: "start s_c4 2 turns, slit open". Step 8: "press the camera forward from behind the cover until the BFAR
  meets the lip, hold it while the thread starts".
- Review label: CONFIRMS A5.

### B-6 (minor): torque values 0.25 / 0.2 N m "by hand" cannot be held without a torque tool, and none is in the BOM
- Evidence: ASSEMBLY.md:22, :182, :198; FASTENER-POLICY.md:177-178. BOM tools D2-60..D2-76 have no torque driver.
- Failure: a firm hand on a PH1 gives 0.4-0.6 N m (FASTENER-POLICY C says "about 0.4 with firm fingers"). That is
  1.6-2.4 x the anchor spec and 2-3 x the pinch spec, on short inserts in ASA (G4: 0.25 N m alone is about 280-420 N
  of preload). Likely outcomes: insert pull-out (B-3 makes it worse), lug crack, or a crushed washer seat that relaxes.
- Fix: add a straight, adjustable torque screwdriver (0.1-0.6 N m, 1/4 in hex with a PH1 bit, dia <= 6.5 shank) to
  BOM F and tool 1. It also serves the PT T_spec. Or define the torque as "fingertip on the blade, not the handle"
  until G-COL-1. Apply G4's lower value in ASSEMBLY s1, s2 step 7, s4 and FASTENER-POLICY I (5 places).
- Review label: CONFIRMS G4. NEW: the missing tool.

### B-7 (minor): lens thread torque is reacted through the camera cover, so through the compliant housing-to-PCB joint
- Evidence: ASSEMBLY.md:191 (finger on the cover), :354 (removal "hold the camera cover"), :401-403 (swap: "the
  camera turns with it until its cover meets the roll fin, which then holds it"). HANDOFF.md:25-27: the compliant link
  is the housing-to-PCB joint (2 M2 screws, nylon washers, gasket). The torque path is lens -> adapter -> BFAR ->
  housing -> M2 joint -> PCB/cover -> finger or fin.
- Failure: breakaway torque on a snug C thread twists the housing on the PCB at every swap and level check. Sensor
  tilt or decentre then creeps in: exactly the error G-CAM-2 tests once, but swaps repeat.
- Fix: hold the BFAR / housing front (or the adapter flats), not the cover. If that is not reachable through the
  left side, say "lens hand-snug only (fingertips)". Make G-CAM-2 repeat its corner check after 5 lens swaps.
- Review label: NEW.

### B-8 (minor): "PC if G-W11 finds the camera zone above 50 C" has no measurement behind it and comes in the wrong order
- Evidence: PRINT-GUIDE.md:16, :65, :107; SPEC.md:70, :142; DESIGN.md:192. WIRING.md:479 G-W11 records the SoC
  temperature and the X1203 boost (thermocouple) only. No camera-zone point. G-W11 also runs in the closed body
  after step 10 (ASSEMBLY.md:246), long after the collar is printed.
- Failure: the maker cannot decide ASA vs PC before printing. If the zone does exceed 50 C, the tub that carries the
  same inserts is ASA either way.
- Fix: "print the collar in ASA; add a thermocouple at the collar foot / tub front wall to G-W11; if > 50 C, reprint
  the collar in PC and re-run G-COL-1 for PC". Or drop the clause.
- Review label: NEW.

### B-9 (minor): evidence/README.md is stale for r5
- Evidence: evidence/README.md:45 ("tub 7" modifiers; there are 10), :59-60 (slicer_review "the 11 printed parts",
  no `lens_collar`), :61-63 (coupon_validation list without G-COL-1). HANDOFF.md:22 says slicer 12, coupons 10 items.
- Failure: a builder files records per the README. The tub slicer record omits the s_c modifier meshes, and no
  lens_collar or G-COL-1 record is filed. `open_evidence` stays open with no explanation in the doc.
- Fix: 12 parts incl. `lens_collar`; tub 10 modifiers; add G-COL-1 (3 coupons) to coupon_validation.
- Review label: NEW (F4-F6 cover other stale text, not this).

### B-10 (minor): two stale numbers in builder docs
- PRINT-GUIDE.md:45 "The other 9 parts print at 100 %". The hood is one of the 9 and prints at 25 % gyroid
  (table line 55). Fix: "the other 9 parts have no modifier; hood 25 %, the small parts 100 %".
- DESIGN.md:284 "bench solder joints are 10". It is 12 since r4 (BOM.md, ASSEMBLY.md:45, OPTIONS.md:40). HANDOFF.md:170
  "10 solder joints" is inside the superseded s1, which is acceptable.
- Review label: NEW.

### B-11 (note): `service_driver` has no rows for s_c4 or s_j
- Evidence: checks.json `service_driver` screws = s_k1, s_k2, s_b1, s_b2, s_r1, s_r2, s_c1..s_c3. s_c4 is driven in
  the closed-body state at every level check and lens swap (ASSEMBLY.md:220, :402), with knobs, eyecup, stick, cap and
  pack present (they are not in its step-8 audit set). s_j comes out at s7 item 11.
- Risk is low: those parts are at the rear or below. Fix: add both to `service_driver` (FASTENER-POLICY G already
  claims "again in the service state").
- Review label: NEW.

### B-12 (note): the heat-set tip must fit the iron, and the iron is unspecified
- Evidence: BOM D2-63 "temperature-controlled soldering iron, class"; D2-74 "M3 heat-set tip for the iron". Tips are
  iron-system specific (900M/T12/TS100/Hakko). The secondhand pick H6 (YIHUA 928D) needs 900M-class tips.
- Fix: name the tip system on D2-74, or tie D2-74 to the D2-63 choice.

### B-13 (note): PRINT-GUIDE s5 item 6 dry-fits the collar "with the hood on" before the electronics
- Evidence: PRINT-GUIDE.md:159-161. The hood must then come off again for step 4 (Pi stack). That needs the 2
  release pins (s7 item 9) and spends one of the 5 hook cycles that G-SNAP-2/whole qualifies.
- Fix: do the dry fit on the G-COL-1 coupons (collar_tub_front + collar_hood_plate), or note the cycle on the tally.

### B-14 (note): B1 heat-setting into a 2.5 mm front wall from the front
- Evidence: ASSEMBLY.md:84-86; FASTENER-POLICY.md:184-186. The bosses (OD 8, to x -7.6) hang behind a 2.5 wall; the
  tub lies on its back.
- Fix: back the inner face (a block through the open left side), go slowly, check perpendicularity. For a small
  ASA boss, the insert going in crooked is the usual failure.

## Internal review findings checked against my reading
- A1 washer seat zero clearance: CONFIRMS A1 (not re-probed; PRINT-GUIDE gives no seat note).
- A2 no sacrificial bridge layer: CONFIRMS A2. PRINT-GUIDE.md:107 names the "3 washer-seat bridges" but gives no
  instruction. Add it to the print notes.
- A3 bed-layer ear wall: not re-checked (note).
- A4: CONFIRMS (B-4). A5: CONFIRMS (B-5).
- A6 lens swap thread start, panel on: agrees in kind. B-7 adds that the reaction path itself is the problem.
- A7 bolting order in G-COL-1: CONFIRMS A7. SPEC.md:430-435 gives no order.
- A8 short insert is a class: CONFIRMS A8. With B-3, a 3.0 insert also leaves the face recess / tip margins
  unverified.
- G3: CONFIRMS on the gaps, DISAGREES on the tub/panel dependence on `LENSES` (B-1).
- G4: CONFIRMS (B-6). G8 FPC spring on the floating camera: CONFIRMS (not quantified here).
- F4/F5 were done at 17:05. Stale r4 text still in builder docs: none found beyond B-9/B-10 (grep for pins / turret /
  front land / 36.5 bore in ASSEMBLY, PRINT-GUIDE, SPEC, DESIGN, MEASURED-PARTS, OPTIONS, FASTENER-POLICY,
  WIRING, BOM: only history-marked rows).
- Not reviewed: slicer behaviour of the hood roll fin; the Fujinon collar (`out/_fujinon-r5/stl/lens_collar.stl` is
  the only copy, in an underscore folder; PRINT-GUIDE.md:226 tells the maker to run a `--lens` build, which needs the
  CAD environment); prices beyond line presence.
