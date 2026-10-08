
### 6.7 Docs
- **SPEC s9/s10:** the J7 contract becomes "the collar carries the lens; the camera hangs on it and touches no
  printed part; no chassis feature loads the PCB". Turret rows deleted.
- **DESIGN:** J7, parts, mass/CoM (Kowa about +1.5).
- **ASSEMBLY:** s6.8.
- **FASTENER-POLICY:** a new section, "M3 machine screws and square nuts (lens collar)". Rationale:
  - the Pi drop limits tub bosses to 2.4 deep;
  - collar swaps need unlimited reuse;
  - same PH1 and the M3 class of section E.
  Torques 0.2 / 0.15-0.2 N m.
- **PRINT-GUIDE:** collar print; hood without turret supports.
- **MEASURED-PARTS:** MP-CAM rewritten; MP-LENS; G-CAM-2; G-COL-1.
- **LENS-ZOOM-CANDIDATES "Load path":** correct the premise (aluminium mount; creep link = PCB joint) and record
  the adopted fix plus the zoom rule (a fixed section >= 15 mm).
- **HANDOFF, NOTES.**
- **Flag for candidate-fr1:** a Y-sliding hood must clear the collar feet (collar off first) and carry the roll
  fin.

### 6.8 Assembly text (steps)
- **B0 (bench, before 7):**
  1. Remove the tripod block (2 screws; bag them).
  2. Fit the C-CS adapter hand-tight.
  3. Fit the Kowa at infinity, f/1.8, aimed at a target >= 50 m away.
  4. Loosen the lock screw 1/4 turn, turn the BFAR to peak focus, tighten the lock screw, and check the 0.3 m mark.
  5. Record s = (BFAR protrusion ahead of the housing face) - 1.2.
  6. Remove the Kowa; leave the adapter on.
- **3:** press nut_c1..c3 into their slots until they bottom (test-thread an M3 from the front, then remove it).
- **7:** camera with its adapter, on the existing path, until the BFAR face stops on the lip.
- **8:** panel, then the collar (feet through the 4 hood holes), then s_c1..s_c3 from the front at 0.2 N m.
- **9:**
  1. Lens through the open collar into the adapter (the fin holds camera roll).
  2. Push the lens back until its knurl seats on the collar cone.
  3. Turn lens and camera together until the cover's -Y face just touches the fin.
  4. Snug s_c4 to 0.15 N m.
- **10:** pack and cap.
- **10b:** power on and check level on live view. If it is off, loosen s_c4 half a turn, turn, and re-snug to
  0.2 N m.
- **Lens swap:** loosen s_c4 one turn, unscrew the lens. Swap the collar only if the band differs (3 bolts).

### 6.9 Bench gates
- **G-CAM-1 (rewritten).** Measure:
  - BFAR head OD and thickness, and its exposed front annulus;
  - adapter OD, face-to-face (5.00) and band;
  - housing OD; tab width, height and rear face; lock-screw size and head side;
  - that the tripod block comes off with 2 screws and leaves nothing below r 18 in front of the PCB;
  - cover centring +-0.2;
  - s at Kowa infinity and the full s range; FPC exit.

  Pass: everything inside the `CAM_R` tolerances. Otherwise update `CAM_R` and re-run the suite before printing
  the tub, hood or collar.
- **G-LENS (extended).**
  - Kowa: the dia 42 knurl neither turns nor moves axially over full focus and iris travel (mark it and watch).
  - Knurl OD +-0.02; rear-face position from the flange +-0.1.
  - CoM by knife edge; thumb-screw head height.
  - If the knurl moves, use Plan B (D2 cradle + clip).
- **G-COL-1 (new).** Kowa collar on a tub-front coupon (2.5 wall, one nut block) and a plate coupon, pinch at
  0.15 N m. Pass:
  - roll slip >= 1.0 N m; axial pull >= 50 N;
  - 1.1 kg (5x Kowa) at the lens CoM: lens-front deflection <= 0.05 mm, returning to <= 0.01;
  - after 24 h at 50 C under the static load: change <= 0.02 and roll slip >= 0.5 N m;
  - 20 pinch cycles without a crack.
  - If it fails warm: PC or ASA-CF collar, or a spring under the pinch head.
- **G-CAM-2 (new).** Lens clamped in the collar coupon, camera hanging; 0/50/100 g hung on the cover. Pass: the
  edge-focus change is < 1/4 of the depth of focus (about 0.05 deg); repeat after 1 h at 50 C.
- **G-W11** unchanged; it sets the creep derating.

### 6.10 Plan B (only if G-LENS fails): D2 with fixes
- Cradle widened to y +-19 (pin-hole walls >= 1.2).
- Hook gap checked against the measured housing OD (>= 0.3).
- Same J7-R phase-1 model; turret deleted; 3 PT screws through hood and tub.
- `check_j7_float` replaced by D2's `j7_load_path` (PCB/cover >= 0.5 from every printed part; capacity >= 1.5 x the
  5 g moment).
