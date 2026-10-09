# GS8 D2 assembly guide (`cad/gs8-d2-v1/guide`)

An IKEA-style assembly guide for the D2 fork. It has pictures, written instructions on every page, and the wiring steps.
It was built on 2026-10-08 from the r6 CAD (layout.py, 5bb2384). Nobody has assembled a D2 yet: the guide is a DRAFT
of the computed build sequence.

## What is in it

`out/GS8-D2-assembly-guide.pdf`, `out/index.html` and `out/pages/d2-NNN.png` (A4 landscape, 150 dpi):
- **Front pages.** Cover; 0.1 rules; 0.2 the 14 tools; 0.3 hardware bags; 0.4/0.5 parts inventory with pictures;
  0.6 gates before assembly; W wiring overview (every cable route and step); 0.7 contents.
- **Bench pages.** B0 camera and lens; B1 heat-set inserts.
- **Step 1 wiring.** 1a fuse splice, 1b pigtail to the X1203, 1c EVF 5 V lead with diode, 1d EVF board pigtail,
  1e 18/24 switch pigtail, 1f encoder address, then 1g the bench stack.
- **Steps 2-10.** These follow `layout.STEPS`, split into sub-steps a/b/c. The header leads (4d) and the EVF mating
  (6b) each have their own diagram page.
- **Last pages.** S service isolation (P1-P4), and ! the physical blocker check (`BLOCKERS-2026-10-08.md`).

Every rendered step shows at least three points of view:
- **A:** the motion, with arrows.
- **B:** the same motion seen across it.
- **C:** a close-up of the result.

New parts are highlighted. Installed parts are grey. A new part hidden behind an installed one has a dashed outline.
Open design issues from the blocker check appear in a red box on the page of the step concerned (`guide_steps.ISSUES`).

## Files

| File | Role |
|---|---|
| `guide_steps.py` | All page text: rules, tools, bags, gates, steps, open issues. It paraphrases ASSEMBLY.md (r6) and WIRING.md s5-s7; where they differ, those documents win |
| `build_guide.py` | Page composer: multi-view renders, right-hand text column, front pages, PDF, HTML |
| `lineart.py` | Line-art renderer: VTK offscreen ID, depth and normal passes plus image-space edges |
| `diagrams.py` | Wiring diagrams (PIL, schematic) |
| `BLOCKERS-2026-10-08.md` | Physical blocker review of the build sequence |
| `_cache/meshes.npz` | Part meshes in assembly pose (git-ignored; `--remesh` rebuilds them from build_d2) |

## Rebuild

Run from the repo root (about 3 minutes; add `--remesh` after any CAD change, about 2 more minutes):

    .venv-cad/Scripts/python.exe cad/gs8-d2-v1/run_locked.py -- cad/gs8-d2-v1/guide/build_guide.py

`--only 4a,7b` renders single pages to `out/pages/only-<id>.png` for checking. The guide reads layout.py and the
meshes and writes only under `guide/out/` and `guide/_cache/`. It changes no CAD source and no receipt input.
