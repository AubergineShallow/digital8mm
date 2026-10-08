> Cloud-polish fork note (2026-10-07 SGT): this pre-r5 study is historical and has not been rebased on the J7-R
> floating-camera/collar geometry. Its turret/pin assumptions cannot authorize adoption or a current thermal claim.
> Re-export and validate current geometry before resuming; physical airflow/power gates remain open.

# D2 airflow study: brief (basic fan airflow + thermal simulation of the existing arrangement)

Opened 2026-10-05 11:30 machine time (Singapore). The r3 rules in `../R3-BRIEF.md` (fit language, no hardware claims,
no downloads, no commits, output size, records on disk, deadlines) apply here too. This is a SEPARATE job running
alongside the r3 workflow; it must not disturb it.

## The user's request (verbatim, chat message at about 11:20)

> Could you do a basic airflow simulation for the fan as well with the existing arrangement and setup? Will be
> necessary for the cooling issue.

"Existing arrangement and setup" = the baseline D2 release in `cad/gs8-d2-v1/` (r2 geometry, unchanged in r3:
`layout.py` J14 VENTS, the Active Cooler proxy in `cots.py`, `ko_exhaust` plenum, the deleted exhaust baffle, the hood
roof inlet, the front-wall windows, the right-wall slots, the X1203 slots). Not the FR1 candidate (you may NOTE which
FR1 changes could touch the flow paths, without simulating them). The "cooling issue" is the open thermal question:
G-W11 (10 min record at 30 C ambient: SoC < 80 C, no throttling, X1203 boost < 70 C), G-W12 P4, the deleted baffle
(DESIGN J14, SPEC "Thermal"), warm exhaust near the hand (SPEC mock-ups).

## Time (machine clock = Singapore time; `date` before every long step)

- HARD STOP for every airflow agent: **17:15**; each role has its own finish-by time. The user stops the machine work at
  18:00. Never start a run that cannot finish before your limit; save partial results with clear "partial" labels.

## Where to work

- Write ONLY in `cad/gs8-d2-v1/airflow/` (sources) and `cad/gs8-d2-v1/airflow/out/` (results). Progress records in
  `cad/gs8-d2-v1/airflow/NOTES.md` under "## <role>". Never edit baseline sources, docs, `out/`, `candidate-fr1/`,
  `R3-BRIEF.md` or the audit folder. Never edit the r3 NOTES.md.
- The r3 workflow is running CAD builds through the shared lock until about 16:45. The ONLY airflow step that may take
  the CAD lock is the one-time assembly mesh export (CadQuery/OCP):
  `.venv-cad/Scripts/python.exe cad/gs8-d2-v1/run_locked.py --max-wait-min 4 -- cad/gs8-d2-v1/airflow/<script>.py`
  (exit 75 = busy: retry later). Everything else (voxels, solver, thermal, plots) is plain numpy/trimesh/vtk/matplotlib
  OUTSIDE the lock, with these limits: before a run check free RAM (>= 1.2 GB free, else wait and retry); keep a run
  under about 600 MB; at start lower the process priority (Windows: ctypes
  `windll.kernel32.SetPriorityClass(windll.kernel32.GetCurrentProcess(), 0x4000)` = BELOW_NORMAL) so CAD builds win.
  Long runs: foreground Bash with timeout 600000 and checkpoint/restart files, or ONE background run with ONE
  until-loop wait that also matches failure; never pile up waits; never re-issue a timed-out foreground command.
- Available: numpy 2.5, trimesh 5.1 (+ manifold3d), vtk 9.3 (offscreen), matplotlib 3.11, PIL. NOT available: scipy,
  numba, pyamg, skimage, rtree, shapely. Do not install anything.

## Update 11:45 (main session; read `NOTES.md` "MAIN SESSION UPDATE")

Fan data was searched at the user's request: the official brief gives only 1.09 CFM max and 8000 rpm +-15 % (no
static pressure, no curve); the heatsink is a PIN-FIN array open on top (not the plate fins of the cots.py proxy). Use
the estimated pressure range and the pin-fin porous model given there.

## Update 13:58 (main session): fix variants

af-run's existing-arrangement result: the blower recirculates about 97 % of its flow inside the body (through-flow
about 2 %). A separate role **af-variants** (13:58-15:30) runs the same model on suggested fixes: V1 intake shroud to
the roof inlet, V2 = V1 + exhaust baffle/duct, V3 = V2 + covered fins. Its results: `out/variants/VARIANTS.md` and
`out/variants/metrics-variants.json`. **af-verify must check them too; af-report must include them in AIRFLOW.md** as
evaluated SUGGESTIONS (no CAD change), next to the existing arrangement. If they are missing or partial at report time,
say so.

## Update 14:00 (main session): user constraint on fixes

The user (chat, about 14:00): "ensure that it stays within the bound of the redesign intent 'Less is more'". Every
suggested cooling fix must be integral to an existing printed part where possible (e.g. an intake collar on the hood
roof underside, a baffle rib on the hood), with +0 parts, +0 steps, +0 tools as the target; no gaskets, foam, extra
fans, extra screws or extra steps, and nothing that blocks the Pi stack drop or the hood drop. Fixes that would need
any of those are named as such and ranked below integral ones. AIRFLOW.md must give the part/step/tool delta of each
fix and rank fixes by benefit per added complexity ("Less is more" as the tie-breaker).

## Method (decided; roles may refine with reasons)

1. **Lumped network model** (fast, the quantitative cross-check): fan curve (Active Cooler blower: data from at most 3
   web searches; if no published curve, a documented range of 25-30 mm 5 V blower curves with sensitivity) against the
   system impedance (each vent as a perforated/slotted plate with a loss coefficient from a stated correlation using
   its open-area ratio slot_w/pitch and wall thickness; fin channel loss; internal paths), giving the operating flow,
   the flow split per vent, the bulk air temperature rise dT = P / (rho cp Q) for the workload states of
   `electronics/gs8-d2-v1/WIRING.md` s4.2 (S1, S2, S3), and sensitivity (fan speed 50/100 %, K +-50 %, curve range).
2. **3D voxel flow simulation** of the body interior with the real CAD geometry (printed parts + COTS proxies in
   assembly position): lattice Boltzmann D3Q19 in numpy (float32), BGK + Smagorinsky subgrid viscosity (to run near
   real-air Reynolds number; if unstable, raise viscosity and state the Reynolds factor), halfway bounce-back walls,
   vents as Forchheimer porous zones calibrated to the same loss coefficients (so slot resolution does not set the
   loss), a thin outside buffer at ambient pressure beyond each vent (open boundary), and the blower as a body-force
   actuator in its housing, from its intake to the fin exit (+X), with the fin block as an anisotropic porous zone. The
   actuator force is iterated so the simulated (Q, dp) sits on the fan curve. Grid: 2.0 mm main, 1.5 mm check (or
   finer if time allows). Air at 30-40 C (nu about 1.6e-5 m2/s).
3. **Thermal + tracers** on the converged flow: steady advection-diffusion of temperature (upwind FV on the same grid,
   pseudo-time to convergence, alpha + nu_t/Pr_t with Pr_t 0.85), heat sources from WIRING s4.2 (SoC heat into the
   fin block air; X1203 boost IC, EVF board, camera, USB stick, Pi board remainder into the air cells next to their
   proxies), ambient 30 C at the open boundaries, walls adiabatic as the conservative case (optionally a simple
   exterior loss with h about 5-10 W/m2K as a second case). Tracers: per-vent inflow tracers (which vents feed the fan
   intake) and the mean age of air or an exhaust-tagged tracer to measure internal recirculation of hot exhaust back
   to the fan intake (the deleted baffle question).
4. **Component temperature estimates**: air temperature at each component; the SoC estimate = intake air temperature
   + P_soc x R_sink(Q) with R_sink from a stated source or range (label ESTIMATE); compare with G-W11 / G-W12 P4.

## Honesty rules

- This is a basic simulation with proxy geometry, an estimated fan curve and estimated heat loads. It is not a
  measurement and does not close G-W11 / G-W12. Say what each number rests on. Report grid and parameter sensitivity.
  Mass balance, convergence history and the network-model cross-check must be shown before any result is quoted.
- Never tune parameters to reach a desired answer. Report bad news plainly (e.g. recirculation, hot spots, a margin
  that does not hold). Design suggestions are allowed as SUGGESTIONS for the user (no geometry change in this job).

## Deliverables (in `airflow/`)

`network.py`, `params.json` (every input with its source), `export_meshes.py`, `voxelize.py`, `lbm.py`, `thermal.py`,
`run_airflow.py`, `post.py`, tests (`test_lbm.py`, `test_thermal.py`), `out/` (domains, fields, metrics JSON, figures:
velocity and temperature slices through the cooler/fins/exhaust/EVF, streamlines, per-vent flow bar chart), and
**`AIRFLOW.md`**: question, model, inputs, validation, results, sensitivity, limits, implications for the cooling
issue, suggested design options and the physical tests that would confirm them (smoke/tuft test, anemometer at the
vents, thermocouples, G-W11).
