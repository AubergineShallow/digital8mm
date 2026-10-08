# GS8 D2 release layer: brief

Opened 2026-10-04 ~10:05 WIB. This file is the task statement for every agent that works in `cad/gs8-d2-v1/` and
`electronics/gs8-d2-v1/`.

## The user's request (verbatim)

> Ok, D2 looks good. I will review the lens for later. For now, refine the design further to make it as mature, print
> and assemble ready as the original EVF fork. Do note, I will need to turn of this machine by 1500H local Batam time.
> Pause activity by then.

## Hard time limit

- Batam is WIB (UTC+7). This machine's clock shows Singapore time (UTC+8). 15:00 WIB is 16:00 on this machine.
- **Every agent stops by 15:20 machine time (14:20 WIB).** Check with `date`. At that point finish the current edit,
  write progress to the folder's `NOTES.md` (what is done, what is half-done, and the next step), and end your turn.
  Do not start a CAD run that cannot finish before then.
- The main session stops everything at about 14:30 WIB, before the user shuts the machine down.

## What "as mature as the original EVF fork" means here

The reference is `cad/gs8-release-v1` (DESIGN.md, PRINT-GUIDE.md, ASSEMBLY-PATH.md) together with
`electronics/gs8-release-v1` (WIRING.md) and the release BOM. The newer `cad/gs8-stills-v1` pipeline (layout.json,
printed_*.py, cots.py, check_layout.py, build_stills.py, make_tables.py, PRINT-GUIDE.md, ASSEMBLY.md) is the template
to copy patterns from. **Never edit either folder.** For D2 this means:

1. **Real printed parts.** CadQuery solids for every printed part, with true wall thickness, bosses, ribs, snaps,
   tongues, slots, pockets, vents, engraving, chamfers, and clearances from the FDM rules below. These are not
   massing blocks.
2. **COTS proxies.** Every purchased part gets a proxy with its datasheet, listing or repo dimensions and its
   connector and plug keep-outs.
3. **One assembly** from a single source of truth for geometry (`layout.py`), plus checks with machine-readable
   results:
   - part-to-part interference (exact boolean volume), excluding declared mates;
   - clearance minimums;
   - bed fit on both printer classes;
   - min-wall / thin-feature screen;
   - the straight-driver audit (a bit about dia 5-6.5 x 40 mm plus a handle dia 28-30 x 100 mm, along each screw
     axis, against the parts present at that assembly step);
   - insertion paths for the key steps;
   - CoM and mass from the solids (ASA density 1.07 g/cm3 x an infill factor) plus COTS masses.
4. **Exports:** STL per printed part, in print orientation; a STEP assembly; a print manifest (orientation, supports,
   time and mass estimate, bed fit); rendered views (hero, exploded, x-ray).
5. **Documents:**
   - DESIGN.md: build results, part list, interfaces, decisions;
   - PRINT-GUIDE.md: settings, per-part orientation and supports, post-processing;
   - ASSEMBLY.md: numbered steps with a tool per step and screw torques for PT screws;
   - electronics `WIRING.md`: GPIO map, every cable with both ends, power path, EEPROM and software settings, I2C
     addresses;
   - `BOM.md` and `bom.csv`: every purchased line with SKU or class and quantity, priced where a price is known
     (reuse `outputs/bom-release-2026-09-25/prices.json` where the parts match);
   - an open-items / bench-gate list.
6. **Receipts:** build-receipt.json with source hashes and the check totals. `release_candidate` is true only if every
   check passes.

## Design source (D2 concept, frozen)

The design lives in `concepts/nizo-evf-2026-10-03/D2/`:
- `CONCEPT.md`: layout, construction, steps, cables, metrics;
- `build_concept.py`: every dimension;
- `tally.json`;
- `out/*.png`.

Component facts are in `concepts/nizo-evf-2026-10-03/research/PALETTE.md`. The EVF optics are in
`electronics/gs8-evf-v1/EVF-SELECTION.md`: flange datum F, display plane at F - 6.0, M29x0.75 spigot 4.5 long, barrel
dia 38.5.

D2 in short:
- **Body:** satin-silver ASA tub (open to the left) plus a silver dial panel, with a black hood (roof, eyepiece
  housing, front plate and lens turret).
- **Grip:** a black base, skirts and grip in one print. It drops onto 2 keyhole tongues and slides 10 mm forward.
- **Fasteners:** 4 x PT 3.0 x 12 (PH1).
- **Electronics:**
  - Pi 5 + Active Cooler on a Geekworm X1203 (pogo pins), lying flat on floor bosses under the camera;
  - GS camera on 2 pins in a collar;
  - EVF-A at the rear top;
  - USB SSD stick out of a rear scoop;
  - 1S2P 18650 pack + XT30 in the grip;
  - run button (pre-wired), exposure encoder (Adafruit 5880), 18/24 rotary, and a power plunger onto the Pi button.
- **Body size:** 154 x 70 x 100 mm, with the grip front 23 mm behind the front plate.

**Lens:** the user will review the lens later. Model a C-mount lens proxy that is swappable by parameter: Kowa
LM6HC (dia 54, 215 g) is the default, and Fujinon HF6XA-5M (dia 39, 100 g) the alternative. Report the CoM for both.

## Rules carried over from the EVF fork (binding)

- **Printing.** ASA for every rigid part, TPU for the eyecup. 0.4 mm nozzle, 0.2 mm layers. Enclosed printer. The parts
  must fit a 250 x 210 x 220 bed (Prusa MK4 / Core One) and a 256 x 256 x 256 bed (Bambu).
- **FDM rules** (cad/gs8-release-v1/release_common.py):
  - MIN_WALL 1.2 mm; 1.6 for loaded walls and bosses;
  - SLIDE 0.25 per side, LOCATE 0.15 per side, SEAM 0.3;
  - 45 deg chamfers on bed edges, no fillets on the bed face;
  - overhangs no worse than 45 deg unless bridged, or marked as supported;
  - no unsupported holes larger than 8 mm in a vertical wall without a teardrop.
- **Fasteners.**
  - PT 3.0 x 12 thread-forming screws for plastics (WN 1411 / Delta PT), PH1, into printed bosses:
    - pilot dia 2.5;
    - boss OD 7.0 or more;
    - engagement 7 mm or more;
    - 5 re-assemblies or fewer before the insert fallback (M3 heat-set) is needed.
  - Document this as D2's FASTENER-POLICY.md. It replaces the release's "no self-tapping" rule, as the user accepted
    in the concept.
  - The X1203 kit hardware (M2.5) stays.
- **Straight-driver rule (user):** every screw is drivable with a straight driver along its own axis at its step.
- **Fit language:** only check results may say "pass". Purchased parts are proxies, nothing is printed or measured,
  so state that nothing is hardware-verified.
- **Shared machine:**
  - RAM is tight, so run EVERY CadQuery/OCP process through
    `.venv-cad/Scripts/python.exe cad/gs8-d2-v1/run_locked.py -- <script> [args]`;
  - run in the foreground with a Bash timeout up to 600000 ms;
  - never start background wait loops;
  - never import cad/gs8-pxl-v3/build_camera.py.
- **Scope:** write only in `cad/gs8-d2-v1/` and `electronics/gs8-d2-v1/`, never in other folders. Do not commit.
- **Size:** keep every reply and tool call under about 8k tokens; write big files through generators or several edits.
- **Usage:** the user watches a usage limit, so work efficiently and skip web research unless one number is missing.
