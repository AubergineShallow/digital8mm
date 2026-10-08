> Fork note: the captured r5 brief below is preserved as design history. In `r5-cloud-polish-20261007`,
> `CLOUD-POLISH-NOTES.md` records the narrow superseding changes: every lens needs its collar at any mass,
> conservative anchor screening/torque, washer/print preparation and explicit unmeasured datum/operation gates.

# D2 r5 brief: heavy-lens support ("J7-R float + lens collar")

Opened 2026-10-06, machine time (Singapore, UTC+8). `RELEASE-BRIEF.md`, `RECTIFICATION-BRIEF.md` and `R3-BRIEF.md` still
bind:
- rules, fit language and FDM rules;
- the fastener policy;
- the straight-driver rule;
- the stills fork stays untouched;
- never import `cad/gs8-pxl-v3/build_camera.py`;
- build only through `run_locked.py`.

This file adds the r5 task.

## The user's request (verbatim)

> Fix the sagging issue for the heavy lens first

Context: the load-path section of `LENS-ZOOM-CANDIDATES.md`. A heavy lens hangs on the Raspberry Pi Global Shutter
(GS) camera's own lens mount, which is fixed to the sensor PCB.

## What the design study found

The study is in [research/r5-lens-support/](research/r5-lens-support/):
- 2 fact dossiers;
- 3 designs;
- 3 judges, who verified claims against the code and the Raspberry Pi drawing;
- probe scripts.

The findings change the premise.

1. **The GS lens mount is milled aluminium, not plastic.** Sources: the Raspberry Pi HQ/GS briefs and the
   filter-removal procedure.
   - The compliant link is the housing-to-PCB joint: 2 small M2 socket screws with nylon washers on a sticky gasket.
   - The real lens load path is lens -> C-CS adapter -> back-focus adjustment ring (BFAR: a fine external thread, about
     dia 28.8, pitch 0.75-0.79, wall about 1.7, pinched by the split-tab lock screw) -> housing -> M2 screws, nylon
     washers and gasket -> PCB.
   - Raspberry Pi's engineers advise supporting a heavy lens and letting the camera float behind it.
2. **D2's camera model (layout `CAM`, cots `gs_camera`) does not match the official GS drawing.**
   `research/m12-drawings/gs_side.png` (measured at 10.05 px/mm) shows, from the front:
   - the C-CS adapter, dia 30.75 x about 5.8 with its spigot (face-to-face 5.0);
   - the BFAR head, dia 36 x 1.2;
   - a round housing, dia about 35.5 x 10.35, with a split lock tab at the top (10.16 wide, 0.8 slot) and a tripod block
     at the bottom (13.97 wide, 12.04 deep);
   - the PCB, 38 sq x 1.4, and the plastic rear cover, 39.5 sq x 6.49.

   As a result:
   - D2's C flange sits about 10 mm too far forward (+10.6 against about +0.6).
   - There is no 39.5 front land: 39.5 is the rear cover.
   - The 2 printed pins end about 7 mm short of the PCB, so they locate nothing.
   - The keeper sits about 1.2 behind the real cover.
   - The real camera can rock about 5 deg nose-down today.
   - The tripod block, seated as D2 places the camera, collides with the Active Cooler / Pi envelope. It must come off
     at the bench (2 screws, [unconfirmed]).
3. **Kowa LM6HC.** Kowa's drawing shows:
   - the focus ring at the rear and the iris ring at the front, each with an M2 thumb screw;
   - a dia 42 knurled rear ring at about +2.2..+7.6 from the flange, which is the only fixed band. It is inferred from
     the scale and index layout and must be confirmed at G-LENS.

   D2's `LENSES` segment table has the rings reversed.

## Decision (main session, 2026-10-06)

**Adopt the J7-R float architecture.**
- The base spec is judge 3's implementation spec ([judge_3.md](research/r5-lens-support/judge_3.md) s6-s7; summary in
  [specs_j1_j3.txt](research/r5-lens-support/specs_j1_j3.txt)).
- Judge 1's spec ([judge_1.md](research/r5-lens-support/judge_1.md) s6) supplies any detail judge 3 leaves open.
- Two of the three judges recommended it, and it scored highest overall.

**How it works.**
- A printed, per-lens **lens collar** clamps the lens on its fixed rear band and is anchored on the tub front wall.
- The camera (housing, BFAR, adapter, PCB, cover) hangs on the lens and touches no printed part in service.
- A tub lip, a hood roll fin and the panel keeper are catches with gaps, never seats.

**Why:**
- It removes the lens moment, and the focus/iris ring torques, from every camera joint, not just the PCB joint. That
  is Raspberry Pi's own advice.
- Any creep, preload loss or chassis flex in the printed parts moves lens and sensor together. That is an aim change,
  never a focus tilt.
- It is the only route that also suits the 300-600 g zooms under study, provided they have a fixed band of at least
  15 mm.

**Binding choices** (resolving the judges' differences):
1. **Real camera model.**
   - Rebuild `CAM` and the `gs_camera` proxy as tagged sub-solids, parametric in the BFAR screw-out s (0..3.0, nominal
     1.25).
   - Use the values above. Mark every one that is not measured `'drawing'`/`'unconfirmed'` and list it under MP-CAM in
     `MEASURED-PARTS.md`.
   - Remove the tripod block from the model (bench step B0).
   - Model the lock-screw head envelope on both sides until MP-CAM.
2. **Datum chain** (judge 3 s1):
   - lip land x -3.9..-2.7;
   - lip gap 0.5;
   - BFAR face / CS flange x -4.4;
   - C flange x +0.6;
   - housing front at x -5.6 - s.
   - The lens's axial position comes from a **45 deg cone seat in the collar** that takes the rear edge of its fixed
     band. The lip and keeper are catches only.
3. **Collar.**
   - One per lens that has a `support` band (Kowa and Fujinon; the Fujinon band is `'assumed'`).
   - Bore = band + 0.3 diametral; slit 2.0 on the -Y side.
   - Front at most 2 mm behind the first moving segment.
   - Prints face-down on +X, ASA (PC if G-W11 finds the camera zone above 50 C).
   - Replaces the hood turret's look and envelope.
4. **Anchors.**
   - M3 heat-set inserts (FASTENER-POLICY s E hardware) in 3 short tub bosses at x -7.6 or more (the Pi-drop rule), at
     TL (11, 90.5), TR (-11, 90.5) and LL (24.5, 36).
   - LR (-19, 44) is a compression-only foot.
   - M3 x 10 ISO 7045 PH1 + ISO 7089 washers, driven along -X from the front.
   - The bosses must show **0 mm3** against the `pi_in` sweep, the `hood_on` and `camera_in` sweeps, **and** the
     pi5 / x1203 / cooler COTS boxes. Judge 2 found 29 mm3 between an OD 8.8 LL boss and the pi5 box. If LL cannot
     clear, move it, keeping the lens axis inside the anchor polygon with at least 10 mm edge distance.
5. **Pinch.**
   - External lugs on the -Y side, inside the body outline (|y| <= 35) if at all possible.
   - M3 x 16 + washer into an M3 insert in the lower lug, axis -Z, driven from above.
   - It is the last operation.
6. **Hood.**
   - Delete the turret.
   - 4 foot holes, dia 8.6 (teardrop -Z), each with a full ring of at least 1.2.
   - Roll fin + webs (judge 3 s5).
   - The bore tool covers only x -2.8..+0.3.
7. **Assembly order: never thread the lens into an unsupported camera.** Preferred order:
   1. camera + adapter (step 7);
   2. collar + s_c1..s_c3, with the panel still off;
   3. lens screwed through the collar into the adapter while a finger holds the camera body through the open left
      side;
   4. lens pushed back onto the cone;
   5. level on live view later (a step 10 re-check), then s_c4;
   6. panel on (step 8, the keeper becomes the rear catch).

   If this order breaks a check (for example a panel-screw driver audit with the lens present), keep judge 3's order
   and document the hand-hold procedure instead. Record which was chosen.
8. **Fasteners.**
   - New FASTENER-POLICY section: M3 + heat-set inserts, lens collar only, with reasons.
   - Every `SCREWS` entry gets a `kind`. PT checks and counts apply to kind PT only; the M3 kind gets its own checks
     (`check_inserts`).
   - The driver audit applies to every kind.
9. **Checks** (judge 3 s11 + judge 1 s4):
   - `check_j7_float` at s 0, nominal and max;
   - `check_lens_support`: FAIL for a lens over 150 g without a support, WARN if the support is not `'measured'`;
   - `check_lens_clamp` (LOAD_MODEL; anchor polygon);
   - `check_inserts`;
   - new clearance zones;
   - the PT-kind filter.

   Do not weaken existing checks. If an existing check's premise was the wrong camera model (pins, the 36.5 ring/bore
   zones, the turret), replace it with the real-model equivalent and say so in RECTIFICATION.md.
10. **Lens variants.**
    - The `kowa_lm6hc` (default) and `fujinon_hf6xa` builds must both pass.
    - Report the balance numbers (expected about +1.4 Kowa, about -11 Fujinon) under the existing mass_com rules,
      unchanged.
    - The Computar H6Z0812 may be added as a data-only `LENSES` entry, not built.
11. **Plan B** (judge 2's housing cradle + clip) is documented in SPEC s10 / LENS-ZOOM-CANDIDATES only. Not built. It
    is used only if G-LENS shows the Kowa band moves.
12. **Bench gates** (in MEASURED-PARTS.md / SPEC s10 so `hardware_gates()` picks them up):
    - G-CAM-1 rewritten as MP-CAM;
    - G-LENS extended;
    - new G-COL-1 (collar coupon);
    - new G-CAM-2 (sag acceptance: corner-vs-centre focus change of 4 um or less under 3x lens mass, a 15 N side push,
      50 g on the cover, and 1 h at 50 C).
13. **Revision label r5.** Keep r4's STLs reproducible from `baseline-r4-2026-10-06.zip`.
    - Expected to change: the tub, hood and panel STLs, the new collar STL(s), modifiers, coupons if any.
    - Report which outputs changed and why.
14. **Docs.**
    - SPEC (J7 contract, camera stack, parts, steps, s10 gates);
    - DESIGN (s1 state, CoM);
    - ASSEMBLY (B0, inserts, steps 7-10, lens swap, removal order);
    - FASTENER-POLICY, PRINT-GUIDE, MEASURED-PARTS, HANDOFF, RECTIFICATION (r5 section), NOTES.
    - LENS-ZOOM-CANDIDATES "Load path": correct the plastic-mount premise and record the adopted fix and the zoom rule.
    - Electronics BOM: M3 inserts, screws and washers; the tripod block as INCLUDED_IN.
    - candidate-fr1: a note only (its Y-sliding hood must take the collar off first and carry the roll fin). Do not
      edit fr1 code.

**Not in r5 scope:**
- the M12 / helicoid / anamorphic ideas (LENS-M12-ANAMORPHIC.md);
- the paused airflow study;
- WIRING changes, beyond any FPC keep-out the new camera position forces.
