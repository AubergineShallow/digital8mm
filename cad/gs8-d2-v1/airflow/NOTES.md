# MAIN SESSION UPDATE (11:45): fan data searched at the user's request (af-data, af-domain, af-run: read this)

The user asked the main session to search online for the Active Cooler fan curve. Result (searches done; af-data need
not repeat them, but may add one more if it finds a better lead):
- Official product brief RP-008188 (Raspberry Pi Ltd, "Published January 2026", via pip.raspberrypi.com):
  max airflow **1.09 CFM** (0.514 L/s, free air), max speed **8000 rpm +-15 %**, MTTF 379,000 h at 25 C, 5 V PWM +
  tach. **No static pressure and no P-Q curve are published.** Envelope 63.50 x 42.50 x 13.70, blower 30 x 30.
  Firmware fan curve (retailer pages quoting Raspberry Pi): 0 % below 50 C, 30 % at 50 C, 50 % at 60 C, 70 % at
  67.5 C, 100 % at 75 C.
- **Geometry correction for the domain/solver: the heatsink is a PIN-FIN array (about 6 x 9 vertical pins), open on
  top, beside the 30 x 30 blower (product brief drawing and photos), not the 1.0 mm plate fins of the cots.py proxy.**
  So the fin block should be a porous zone with LOW resistance along Z (pins are vertical, air can rise out of the top
  of the pin field toward the hood roof) and moderate, roughly isotropic resistance in X/Y; the blower discharges into
  the pin field on the fin side. Model it that way (state it), or at least run it as a sensitivity case against the
  plate-fin (X-only) assumption. Do not change cots.py.
- Comparable data for a pressure range (not the same fan): Sunon UB5U3-700, 30 x 30 x 3 mm 5 V blower: 9500 rpm,
  0.63 CFM, 88 Pa max static pressure (distributor listings). Axial 30 x 30 x 7 5 V fans list 0.06-0.16 inH2O
  (15-40 Pa) at 2-3 CFM; blowers trade flow for pressure. Suggested blower range for the Active Cooler at 100 %:
  Q_max 1.09 CFM, p_max 60-150 Pa (central about 100 Pa), curve roughly p = p_max (1 - (Q/Q_max)^n), n 1.5-2;
  label it an ESTIMATE in params.json and carry low/central/high through the results.
- RAM note: at 11:40 only about 0.3 GB is available (a 3 GB Java process outside this project, browsers, memory
  compression). The CAD lock holder is waiting for RAM. Keep airflow runs small (2.0 mm first) and follow the brief's
  RAM check; do not kill other processes.
  UPDATE 11:36: the user had the other project's Android emulator and Gradle daemons stopped; about 3.4 GB is available again. The brief's RAM limits still apply.


## af-solver

- 11:25 started. Plan: lbm.py (D3Q19 BGK+Smagorinsky, Guo forcing, implicit Forchheimer porous zones, fan actuator on curve,
  ambient density reset), thermal.py (div-free projected face fluxes, upwind FV, local pseudo-time), tests, benchmark.
- Machine: 16 cores, 16 GB, but only ~0.37 GB available RAM at 11:25 (r3 CAD builds). Runs wait for >= 1.2 GB as the brief says.
- 11:47 lbm.py written; test_lbm.py: Poiseuille duct err 0.05 %, porous dp vs K err 0.2-0.3 % (iso/axis/diag),
  open duct with fan on curve: mass imbalance 1.5e-5, fan dp on curve 0.003 %; real-air jet (Re factor 1, tau0 0.5002,
  C_s 0.16) stable 3000 steps.  Lessons: (1) a blower's 100+ Pa against a few Pa of dynamic pressure makes the LBM
  density swing large -> dt now also limited by drho = 3 dp_max / p_scale <= 0.03 (u_lat at u_ref then ~0.04, more
  steps); (2) residual acoustics (+-5 % Q, ~200-step period) made a sampled fan controller 2-cycle -> fields are now
  window-averaged (sample every 5 steps, window 500) and the fan uses a dynamic model on window means; probes report
  mass flux / rho_ref; (3) float32 sum of D3Q19 weights != 1 drifted mass -> rest population closes the mass.
  Pin-fin note from main session handled by add_porous_diag (per-axis K, low along Z) besides the X-only 'axis' model.
- 12:15 thermal.py + test_thermal.py: all pass (1D adv-diff vs exact discrete 1e-10, vs analytic 1.7 % at Pe 6 /
  cell Pe 0.1 (upwind numerical diffusion); projection div 0.58 -> 6e-11; energy balance 2e-12 adiabatic, 6e-16 with
  h_ext 10; outlet age = V/Q within 0.8 %; per-vent tracers sum to 1 within 4e-7; BiCGSTAB = pseudo-time within
  1.5e-9 K in 51 vs 400 sweeps).  test_lbm.py all pass (jet at real-air Re, 6000 steps, stable; res_u stays ~0.2 =
  unsteady jet, so judge convergence on Q / fan / probe histories with long averaging windows).
- 12:15 interface sync with af-data / af-domain (read their notes + voxelize.py + params.json): build_solver now reads
  meta.vents[<id>].normal/thickness_cells, meta.fan.force_unit, meta.fins.porous_axis ('x') + plate_normal ('y');
  vents use dp = a_lin v + K 0.5 rho v|v| (a_lin_Pa_per_mps, Darcy term added to the implicit drag); fins use the
  dict K_per_mm {a_Pa_per_mps_per_mm, b_Pa_per_mps2_per_mm}.  Default fin model when meta.fins.plate_normal exists:
  'plates' = the params channel law along X and Z (open-top plate fins, as af-domain describes the proxy), blocked
  along Y (beta_t 4); 'axis' (X only) and 'diag' (pin-fin per-axis K) remain as sensitivity options.
  heat_source skips 'total' and '*worst*' keys of params.heat[S].  Checked on a synthetic domain with params.json.
- Benchmark (bench_solver.py, synthetic body-like box, out/tests/bench.json), machine shared with r3 CAD builds:
  LBM 0.068 s/step at 152k cells, 0.150 s/step at 399k cells (1 thread; 4 threads are no faster: GIL contention, so
  threads=1 is the default).  Thermal: setup (flood fill + CG projection, 550 / 767 CG iterations) 11 s / 44 s;
  pseudo-time 0.024 / 0.11 s per sweep (BiCGSTAB ~2 sweeps per iteration).
- 12:23 fan control redesigned after a body-like test with an internal loop (fan exit -> body -> intake, little
  resistance, near free delivery): the 500-step ratio controller drifted / limit-cycled (flow responds in ~80 steps,
  control lag 300-500).  Now: EMA (tau 100 steps) of sum(e.u), signed Q, rho; every 50 steps mag += 0.05 (curve(Q) /
  L_eff - mag), target may go negative past free delivery (windmilling), clamp [-0.5, 4] x initial.  Damped
  oscillation (period ~1000 steps) that settles; the duct test converges in ~5-8k steps.  Expect the fan point to need
  ~10-20k steps at 2.0 mm; start other cases from a converged one (init_fields) to save most of that.
- 12:35 fan model replaced again (final): LOCAL FAN LAW.  Each actuator cell gets F = lambda * dp_curve(A_act e.u) /
  L_act along e (A_act = actuator cells / length, L_act = actuator length along the dominant force axis), computed
  from the force-free velocity each step: no measurement lag, the curve's negative slope damps the loop.  lambda (start
  1) is trimmed slowly on 100-step moving averages so the integral point (Q at the intake probe, int F.u dV / Q) sits on
  the curve (clamp 0.5-2; it absorbs the non-uniform actuator flow).  Body-like test: fan point within 0.2 % of the curve
  after ~1000-3500 steps (lambda 1.13); duct test converged in 3500 steps; jet test stable at Re factor 1.  The uniform
  force (mag_phys, no curve) remains for the analytic tests.  History keys: fan_lambda, fan_force_mean_Npm3.
  Note for AIRFLOW.md: the actuator is a modelling device; with the local law the per-cell force follows the local
  through-flow, so a 2-3 % shift of the operating point vs a uniform force was seen in the viscous duct test.
- 12:43 SMOKE TEST ON THE REAL DOMAIN (out/domain-2.0.npz, 86x45x60 = 232k cells, 89k fluid; params.json; 600 steps
  only, NOT a result): build_solver wires all 5 vents (K + a_lin, zone 2-3 cells), plate-fin model, fan 816 cells,
  dt 3.3e-5 s, Re factor 1, 0.090 s/step (with another run in parallel).  thermal.Problem: 0 disconnected cells,
  projection 620 CG its, setup 14 s.  Findings for af-run:
  (a) heat keys: params 'pi_board_rest' -> mask__heat__pi_board and 'fan' -> fan_actuator air now aliased in
      thermal.heat_source; 'encoder' (0.1 W) has no mask and is reported as not applied.
  (b) fan_lambda rose to 1.9 within 600 steps (the blower interior flow is very non-uniform: intake from above, body
      force +X), so the trim range is now lam_range=(0.3, 4) and a lambda at a bound must be reported.
  (c) Q_fan_outlet (fin exit plane) ~0 vs fan intake 3.2e-4 m3/s at 600 steps: either the start-up transient or the
      air leaving the open-top plate fins upward before the exit plane (plates model lets it); check after convergence.
  (d) steps: internal loop time ~0.2 s = ~6000 steps; expect 20-30k steps (30-45 min) at 2.0 mm from rest; at 1.5 mm
      (x2.4 cells, dt x0.75) start from the 2.0 mm result via resample_fields + init_fields.
- 13:04 CONVERGENCE BENCH (bench_converge.py, synthetic 152k-cell body-like box with a ducted blower + fins; it turned
  out to have almost no through-flow: the fan loop closes inside the box, vents carry ~1e-6 m3/s - fine for timing,
  meaningless as physics).  out/tests/bench_converge_150000.json/.log.  LBM: 0.059 s/step, 16,276 steps in 16 min
  (0.35 s physical).  Fan point steady (Q within 1e-3) after ~4k steps; window-mean velocity change res_u 0.12 at 4k
  -> 0.07 at 16k (unsteady internal flow at real-air Re: it plateaus, it does not go to 1e-3).  The fan-curve
  convergence test was relative to a curve value near 0 (free delivery) and never passed; now floored at 10 % of the
  shut-off pressure.  Thermal on the result: Problem setup 11 s (560 CG its); BiCGSTAB 1046 its / 47 s to res 6e-7,
  energy balance 1.4e-8; pseudo-time CFL 0.4 reached only res 0.5 after 27,600 sweeps / 600 s -> the high-level
  functions (solve_temperature, vent_tracers, mean_age, recirculation_tracer) now default to method="bicgstab" (same
  discrete equations, verified equal to pseudo-time within 1.5e-9 K in test_thermal); pseudo stays the reference.
- ESTIMATE for the real case (af-run): 2.0 mm (232k cells, 0.09 s/step): 15-25k steps = 25-40 min from rest; judge
  convergence on probe Q / fan_lambda / fan_dp histories over >= 2000-step windows (res_u will plateau ~0.05-0.1);
  later cases (50 % speed, K +-50 %, curve low/high) from the converged 100 % field via init_fields: ~5-8k steps each.
  1.5 mm (~550k cells, ~0.22 s/step, dt x0.75): from the resampled 2.0 mm field ~8-10k steps = 30-40 min; from rest
  ~2 h (do not).  Thermal per state ~1 min (BiCGSTAB) at 2.0 mm, ~3 min at 1.5 mm; tracers ~1 min each.
- 13:05 af-solver DONE.  Files: airflow/lbm.py, thermal.py, test_lbm.py, test_thermal.py (all pass; numbers in
  out/tests/test_lbm.json, test_thermal.json), bench_solver.py + bench_converge.py (out/tests/bench*.json/.log,
  the bench checkpoint was deleted).

## af-data

- 11:35 started. Geometry read from layout.py/cots.py/d2_common.vent_slots. Fan data in repo: Active Cooler brief
  RP-008188 (via cad/gs8-pxl-v2/COMPUTE-OPTICS-COMPONENTS.md): 1.09 CFM max, 8000 rpm +-15 %, 63.5 x 42.5 x 13.7 envelope.
  Plan: <=3 web searches (static pressure, comparable 30 mm 5 V blower curve, sink R), then params.json -> network.py
  -> out/network.json + out/network.md.

## af-domain

(af-domain role: 3D air domain of the baseline r2 arrangement. Kept current so a re-spawned copy can continue.)

- 11:35 started. Plan: export_meshes.py (once, CAD lock) -> out/meshes/*.stl + index.json; voxelize.py (outside lock)
  -> out/domain-2.0.npz, out/domain-1.5.npz, out/domain/*.png, out/domain/README.md.
- Inside test: trimesh contains needs rtree (absent) -> use manifold3d slices + matplotlib Path even-odd per z-level,
  3x3x3 sub-samples per cell, solid if ANY sub-sample is inside a part (closes walls >= dx/3 thick; vent slots are
  then re-opened as porous zones, as the brief says the porous zone carries the loss).
- 11:37 af-data: network.py runs (numpy only, < 5 s): writes params.json, out/network.json, out/network.md. Searches
  used 3/3 (SC1148: only 1.09 CFM / 8000 rpm published, no static pressure; reference blower Delta BFB0305MA-A
  1.2 CFM / 51.3 Pa). Narrative of network.md in progress.
- Interface notes for af-domain / af-solver (additions to the shared interface):
  - params.vents[id]: K and a_lin_Pa_per_mps are referenced to the FACE velocity over the gross vent box
    (area_mm2 = box in-plane area): dp = a_lin*v + K*0.5*rho*v|v|. Porous zone through the wall thickness_mm:
    per-length coefficients = (a_lin, K*0.5*rho)/thickness. out_band/out_corner K include the tub window (+0.4).
  - EXTRA opening `sd_slot` (layout SD_SLOT, microSD access, x -5.2..0, y -11.5..0.5, z 15.9..18.6) is open through
    both walls in the existing CAD; included in the network as a body vent (K 4.17, 60 % open). af-domain: give it
    mask__vent__sd_slot or let the voxel geometry carry it.
  - params.fins.K_per_mm: dp/dx = a*u + b*u|u| per mm along +X, u superficial over frontal box (fins.frontal_box).
  - PROXY WARNING (decisive): cots.cooler blower is z 22..36.3 but the fins only z 23.4..30.5 and uncovered, so the
    proxy blower outlet has an open 5.8 mm strip over the fins. In the network this strip takes ~80 % of the fan flow
    and the fins see only 1.0e-4 m3/s (R_sink 9.8 K/W). The real SC1148 fin height/cover is not recorded in the repo.
    The network runs 'proxy' (as drawn) and 'covered' (full-height covered fins, real-cooler reading). Suggest the 3D
    study states which it uses (or runs both if time allows).
  - params.walls: UA = 0.20 W/K body wall loss (second thermal case only).
- 11:40 af-data DONE. Files: airflow/network.py (re-run: `.venv-cad/Scripts/python.exe cad/gs8-d2-v1/airflow/network.py`,
  < 5 s, numpy only, imports ../layout.py read-only), airflow/params.json, out/network.json (98 flow solves: 3 configs x
  jet 0/1 x curve nominal/low/high x speed 1/0.5 x K x0.5/1/1.5, plus variants), out/network.md (summary).
  params.heat has keys S1, S2, S3 plus 'basis' and 'placement' (strings/dicts): iterate over ('S1','S2','S3') only.
  params.heat[S].total includes the fan; x1203_worst_eta085 is an alternative X1203 loss, not an extra load.
  Cross-check numbers for the 3D study (nominal curve, 100 %): fan 0.92 CFM (covered fins, open plenum), 1.03 CFM
  (proxy as drawn), 0.88 CFM (ducted bound); recirculation plenum->body 51-54 % (covered), 78-87 % (proxy), 0 (ducted);
  through-flow 2.0-2.1e-4 / 0.6-1.1e-4 / 4.15e-4 m3/s; inlets inlet_roof, x1203, sd_slot; outlets out_band, out_corner,
  out_wall. Mass residual < 1e-13 m3/s, energy residual < 1e-8 W in all cases.
- 11:42 export_meshes.py + voxelize.py written (voxelize helpers unit-tested on cube/cylinder/morphology in scratch).
  Export retry loop running in background (run_locked busy with an r3 build; log out/export-tries.log, out/export.log).
  RESUME: if out/meshes/index.json exists, skip the export; run
  `.venv-cad/Scripts/python.exe cad/gs8-d2-v1/airflow/voxelize.py --dx 2.0` then `--dx 1.5` (outside the lock).
- Domain decisions: grid faces on multiples of dx (x=0 front face, z=0 body bottom); exterior beyond the vent buffers
  is inactive (label 2, solid); buffer = 5 cells + 1 ambient layer beyond each vent face, lateral +2 cells, ambient =
  far layer + lateral rim; vent zone = cells overlapping the wall interval along the normal (front vents: tub window
  + hood plate in series, x -5.2..0) with centre inside the lateral box; floor lead holes + microSD slot plugged
  (mask__leak__* kept for a sensitivity); extra npz keys: label (int8, legend in meta), part (int16 index into
  part_legend).

## af-solver API

(lbm.py / thermal.py; python 3.14 numpy 2.3 or .venv-cad numpy 2.5 both work; numpy only.)

**Loading**: `dom = lbm.load_domain("out/domain-2.0.npz")` -> dict `dx_mm, origin, solid, masks{name-without-"mask__"}, meta`.

**Meta keys lbm.build_solver reads** (af-domain: please provide these, or tell me the names you used):
- per-mask dict `meta["masks"][<name>]` (also accepted: `meta[<name>]`) with `normal` (outward for vents; flow direction
  for fan_intake / fan_outlet) and, for vents, `thickness_cells` (porous zone thickness). Also accepted:
  `meta["vent_normals"][<id>]`. Missing normal -> dominant axis of the mean flow; missing thickness -> slab thickness
  computed from the mask (cells / projected cells).
- `meta["fan_force_unit"]`: [x,y,z] (one vector) OR {suffix: [x,y,z]} with masks `mask__fan_actuator__<suffix>`
  (several directions, e.g. axial intake part + radial/+X discharge part). Default +X.
- `meta["fin_porous_axis"]` (or `fin_axis`, or `meta["masks"]["fin_block"]["axis"]`): default +X.
- optional `mask__exterior` (outside air not simulated) for the exterior-loss case; else the box boundary + ambient.

**params.json keys read**: `fluid.rho, fluid.nu` (cp used by thermal), `fan.curve_100` (or another key via
`curve_key`, e.g. range curves), `vents.<id>.K` (id = text after `mask__vent__`, case-insensitive), `fins.K_per_mm` |
`fins.K_total` (+ optional `fins.length_mm`, else the mask length along the axis) | `fins.K_per_mm_xyz` [kx,ky,kz]
(pin-fin model: per-axis loss, low along Z). Heat: thermal takes a plain {component: W} dict (e.g. `params.heat.S2`).

**LBM** (`lbm.py`):
- `s, notes = lbm.build_solver(dom, params, speed=1.0, curve_key="curve_100", vent_K_scale=1.0, fin_K_scale=1.0,
  fin_model=None|"axis"|"diag", u_ref=None, tau_min=0.5, cs_smag=0.16, threads=1, beta_t=4.0, log=file)`.
  Wires ambient (density reset), vents (Forchheimer iso, dp = K 0.5 rho u^2 over thickness, u = superficial velocity of
  the zone cells), fin block (axis: Forchheimer along axis + linear drag beta_t across = blocks the other two; diag:
  per-axis K), fan actuator (curve, fan laws for `speed`), probes `fan_intake`, `fan_outlet`, `vent__<id>`.
  dt = min(0.1 dx/u_ref, dx sqrt(rho 0.03 / (3 dp_max))): the second limit keeps the LBM density swing from the
  fan's max static pressure <= 3 % (it usually governs: u_lat at u_ref ~0.01-0.04). `tau_min=0.5` = real air
  (Re factor 1); raise it (e.g. 0.505-0.52) only if unstable and quote `s.info()["re_factor"]`.
- `status = s.run(nsteps, mon_every=500, sample_every=5, tol=2e-3, tol_q=3e-3, tol_fan=0.02, n_ok=3,
  checkpoint="out/x.ckpt.npz", ckpt_every=5000, deadline=time.time()+sec, verbose=True, log=f)` ->
  'converged' | 'maxsteps' | 'deadline' | 'diverged'. Fields are averaged over each 500-step window (residual
  acoustics and unsteady jets); converged = window-mean u change < tol, every probe Q change < tol_q and fan dp on
  the curve within 2 %, 3 windows in a row. At real Re the jets stay unsteady: res_u may plateau (0.2 in the jet test)
  -> judge on Q/fan/probe histories and use longer windows (mon_every 2000) for the averaged fields.
- `s.history` list of dicts per window: step, res_u, umax_lat/umax_mps (instantaneous), umean_max_mps, nut_max_lat,
  rho_min/max, Q_<probe> (m3/s at reference density, sign along the probe normal; vents: + = outward), fan_Q, fan_dp
  (delivered = int F.u dV / Q), fan_dp_curve, fan_mag_Npm3, wall_s.
- `f = s.fields()` (window mean): `u` float32[3,nx,ny,nz] m/s, `p` Pa gauge, `nu_t` m2/s, `rho` (lattice).
  `s.fan_state(u_lat, rho_lat)`, `s.probe_q(name, u_lat, rho_lat)`, `s.info()` (dx, dt, tau0, nu_lat, re_factor,
  u_scale, p_scale, drho_at_dp_max, ...). Checkpoint: `s.save(path)` / `s.load(path)` (same domain + setup; history
  and fan magnitude restored). `s.init_fields(u_phys, p_phys)` starts from another solution (e.g. 2.0 mm result
  resampled to 1.5 mm, or the 100 % case for the 50 % case) -> far fewer steps.
  `lbm.resample_fields(s.fields(), dom_2p0, dom_1p5)` does the nearest-cell resampling (same assembly frame).
- Low-level: `lbm.LBM(solid, dx_m=..., ...)`, `set_ambient`, `add_porous_iso(mask, K, thickness_cells)`,
  `add_porous_axis(mask, axis, K_per_cell, beta_t)`, `add_porous_diag(mask, K_per_cell_xyz, beta_xyz)`,
  `add_probe(name, mask, normal)`, `set_fan(mask, direction, curve=, speed=, q_probe=, mag_phys=, ctrl_every=50,
  relax=0.05, ctrl_tau=100)`: with a curve = local fan law + slow lambda trim (see log 12:35); without = uniform
  force density mag_phys (N/m3).
- `lbm.set_low_priority()` (BELOW_NORMAL), `lbm.free_ram_mb()` for the brief's RAM check.

**Thermal / tracers** (`thermal.py`), all on the converged mean fields:
- `prob = thermal.Problem(dom, f["u"], rho=f["rho"], nu_t=f["nu_t"], alpha=2.3e-5, Pr_t=0.85)`: open cells
  connected to ambient, face fluxes projected divergence-free (CG; `prob.proj` reports div before/after),
  `prob.summary()` (cells, disconnected fluid cells excluded, Q in/out at the ambient boundary).
- `T, info = thermal.solve_temperature(prob, dom, {"soc": W, "x1203": W, ...}, T_amb=30, h_ext=None|U_W_m2K,
  method="bicgstab" (default) | "pseudo", tol=1e-6, cfl=0.4)`: deg C (NaN in solids). Heat goes uniformly into the active cells of
  `mask__heat__<component>`; `info["heat_report"]` lists what was/was not applied; `info` has heat_in_W,
  enthalpy_out_W, shell_loss_W, balance_rel, iters, res, history. Use `method="bicgstab"` (same equations,
  ~50-200 iterations instead of thousands); pseudo-time (CFL 0.4) is the reference.
- `tr, labels, names, infos = thermal.vent_tracers(prob, dom, method="bicgstab", tol=1e-6)`: tr[vent] = fraction of
  local air that entered through that vent (ambient cells assigned to the nearest vent).
- `age, info = thermal.mean_age(prob, ...)` (s); `rc, info = thermal.recirculation_tracer(prob, dom, tag="fan_outlet")`
  (c at the fan intake = recirculated exhaust fraction).
- `thermal.probe_stats(prob, field, mask, weight="volume"|"flux")` -> cells, mean, max, min (+ flux_mean).

**Validation** (`python test_lbm.py`, `python test_thermal.py`; numbers in out/tests/*.json): see the af-solver log above.
- 12:15 export done (39 parts, all watertight, try3 2 under the lock, 129 s). Lock released.
- 12:20 DONE. out/domain-2.0.npz and out/domain-1.5.npz written (voxelize.py, both grids in ~30 s; rerun any time
  outside the lock with `.venv-cad/Scripts/python.exe cad/gs8-d2-v1/airflow/voxelize.py --dx 2.0 1.5`).
  Checks: 1 fluid component, every vent reaches the fan intake and the fin exit, no body leak, 19 / 11 small pockets
  dropped (largest = hood lens-collar cavity). Slices in out/domain/*.png were read; README in out/domain/README.md.
- Interface additions (af-solver / af-data please note):
  - npz extra keys: `label` (int8; legend in meta label_legend), `part` (int16 into `part_legend`).
  - meta vents[<id>]: normal, axis, thickness_cells, zone_cells, face_cells, face_area_discrete_mm2,
    face_area_box_mm2, area_ratio_discrete_to_box, slot_w, pitch, open_area_ratio_slots, path_cells_from_fan_intake,
    path_cells_from_fin_exit. Scale the porous K so the loss refers to the box (nominal) area, not the discrete one.
  - meta fan: force_unit [1,0,0], blower_cells, intake_r_mm 9.0 (ESTIMATE), fin_section_discrete_mm2 252 vs proxy
    302, blower_outlet_open_discrete_mm2 (144 / 153) vs proxy 199, fin_length_cells; meta fins: porous_axis x,
    plate_normal y, open on top (no shroud in the proxy).
  - extra masks: mask__heat__soc (= fin block), mask__probe__fin_exit, mask__probe__roof_inlet_inner,
    mask__probe__outside_<vent> (first buffer layer outside each vent), mask__leak__{floor_pigtail,floor_run_lead,
    sd_slot} (closed in the domain; opening sd_slot would also need an outside buffer, not built).
- Geometry findings: x1203 slots mostly blocked by the pogo-pin proxy (open only z 16..17.5 band); GPIO header /
  QT keep-out behind out_wall; no wall between fin exit and the space above the fins (deleted baffle) -> recirculation
  path open; cables/keep-outs not modelled as solids.

## af-run

- 13:08 started (finish-by 15:40, hard stop 17:15). Plan: run_airflow.py (2.0 mm, 100 % nominal curve, plate-fin
  proxy as drawn, open-top; vent K scaled by (A_grid/A_box)^2 so the loss refers to the nominal box area; sd_slot is
  CLOSED in the domain (card in place) while the network had it open -> cross-check against that difference) ->
  out/flow-2.0.npz; then thermal S2/S3 + tracers (run_thermal in post.py) -> out/metrics.json + out/figures/.
  Optional if time: 1.5 mm (from resampled 2.0), 50 % speed (from 2.0).
- 13:10 run_airflow.py written + smoke-tested (718 steps, outputs deleted). Launched in background (BELOW_NORMAL):
  `run_airflow.py --dx 2.0` (base, plates fin model = proxy as drawn) and `--case finaxis --fin-model axis`
  (sensitivity: fin block passes air only along +X, top closed). Logs out/run-2.0*.log, checkpoints out/ckpt-*.npz
  (RESUME: rerun the same command; it reloads the checkpoint). Outputs out/flow-2.0.npz, out/flow-2.0-finaxis.npz.
- 13:25 post.py (compute: thermal + tracers -> out/thermal-<tag>.npz, out/metrics-<tag>.json; figs; merge ->
  out/metrics.json + out/figures/vent_flows.png) and post_figs.py written; figs tested on a step-2000 test field
  (flow-zzztest, delete before finishing). Compute on a test field took > 10 min (BiCGSTAB slow when the
  through-flow is tiny) -> run compute in the background.
- 13:25 EARLY FINDING (base, steps 4-7.5k, fan point on the curve): fan intake 3.46e-4 m3/s (0.73 CFM, dp 19.8 Pa)
  but vent through-flow only ~7e-6 m3/s (~2 % of the fan flow): the blower jet leaves the open-top plate fins upward
  and circulates inside the body back to the intake; fin-exit plane ~2e-6. finaxis (top closed): through-flow
  2.3e-5, fan 2.4e-4 at 29.5 Pa. Network proxy had through-flow 6.2e-5. Caveat to state: no buoyancy in the LBM;
  stack dp ~0.1 Pa >> the mPa fan-driven vent dp -> real through-flow likely buoyancy-set.
- 13:26 convergence criteria tightened in run_airflow.py: the first pass "converged" at 8000 steps (0.26 s
  physical) on the fan point, but the vent flows were still drifting (inlet_roof -5.9 -> -7.3 cm3/s over 4k steps):
  the body circulation turnover is ~0.5-2 s. Now also each vent Q range over the window <= 5 % of the through-flow
  and --min-steps 20000. PLAN: when flow-2.0.npz / flow-2.0-finaxis.npz exist, rerun the same commands (they resume
  from out/ckpt-2.0*.npz) with --max-min 40; start 1.5 mm with --init out/flow-2.0.npz (resampled) as the grid check
  of the fan point / fin split (vent flows there will be PARTIAL); 50 % speed at 2.0 mm from the settled base.
  Helper: trend.py <tag> prints the window history.
- 13:29 pass 1 done: base "converged" (old criteria) at 10k steps -> kept as out/flow-2.0-pass1-10k.npz (interim);
  finaxis converged 10k (vent flows flat within 0.5 cm3/s from 2.5k to 10k steps: accepted, no rerun).
  Running now (background): base continuation from ckpt (--min-steps 20000, --max-min 45), 1.5 mm from the
  resampled pass-1 field (--max-min 70, vent flows there PARTIAL), post.py compute for 2.0-finaxis and
  2.0-pass1-10k. Then: compute + figs for the final base, 50 % speed from the final base, merge.
- 13:31 buoyancy_estimate.py -> out/buoyancy.json (ESTIMATE, not simulated): stack between the roof vent (z 98) and
  the low vents (area-weighted z 26, H 72 mm) with the params vent losses: body air +20 K -> 0.05 Pa, 35 cm3/s,
  carries 0.8 W; +40 K -> 55 cm3/s, 2.5 W. So natural draught alone exceeds the fan-driven through-flow of the
  existing arrangement (~7 cm3/s) and would run the OTHER way (out at the roof, in at the front/side), and neither
  removes more than a few W: the heat has to leave through the walls unless the fan exhaust is ducted to a vent.
- 13:50 BUGS found on the interim pass-1 metrics and fixed in post.py: (1) thermal.label_ambient_by_vent seeds only
  ambient cells touching a vent zone, but the outside buffer is 5 cells deep -> most reservoirs unlabelled, tracer
  sum at the intake 0.13. post.label_ambient_by_vent now grows from each vent zone through outside air (labels 3/4/5).
  (2) the domain shell for the wall loss has 0.031 m2 of air-cell faces vs the 0.066 m2 body area of params.walls ->
  wall cases now use U_eff = UA / A_shell for UA 0.20 W/K (= network) and 0.30 W/K (U_range high); the earlier
  'wall_loss' entries (raw U 3.07 -> UA 0.095 W/K) stay in the pass-1/finaxis metrics, labelled. post.py compute
  takes --parts tracers,recirc,thermal (partial recompute updates metrics/thermal npz in place).
  Pass-1 numbers (10k steps): fan 346 cm3/s (0.73 CFM) at 19.9 Pa ON the curve; through-flow 7.6 cm3/s (2 %);
  recirculation R (source method) 0.973; mean age of interior air 74 s; S2 adiabatic has no realistic steady state
  (fan intake air ~1100 C), S2 with UA 0.095 W/K ~190 C. Fin flow 338 cm3/s at the fin inlet, falls to 0 by
  2/3 of the fin length (air leaves through the open top) and reverses at the exit plane.

## af-variants

- 13:58 started (finish-by 15:30). Task: evaluate suggested fixes V1 (intake duct to inlet_roof), V2 (V1 + exhaust
  compartment over fins/plenum to out_band/out_corner/out_wall), V3 (V2 + lid on the fins) in the same model; no CAD
  change. Script `airflow/variants.py` (build | run <V> --flow-end HH:MM --end HH:MM | report); outputs in
  `out/variants/`. Functions copied from run_airflow.py/post.py (not imported) so af-run edits cannot change them.
- 14:02 `variants.py build` done: out/variants/domain-2.0-V{1,2,3}.npz + domain-edit-V*.png + domain-edits.json.
  V1 duct x -72..-44, y -24..4, z 36..96 (1722 wall cells, leak check 0 cells); V2 compartment x -42..-6, y -32..16,
  z 24..38 (lid at z 38-40, floor at the fin base; 688 wall cells; leak 0; reaches out_band/out_corner/out_wall only;
  the lowest out_wall row stays open to the body below the floor); V3 lid z 30-32 over the fin block (336 cells).
- 14:04 runs launched in ONE background command (3 processes, BELOW_NORMAL): flow from af-run's
  flow-2.0-pass1-10k.npz (init only), af-run criteria (min 6000 steps) until 14:50, then post (S2/S3 wall_UA0.20 and
  adiabatic, recirculation, age, vent tracers) until 15:12. Logs out/variants/run-V*.log. RESUME: rerun the same
  command (flow resumes from out/variants/ckpt-V*.npz; post reruns if flow-2.0-V*.npz exists).
- 14:05 USER CONSTRAINT "Less is more" (via coordinator): fixes must be integral to existing printed parts (hood
  collar / hood or tub rib), +0 parts/steps/tools, not blocking the Pi stack drop or the hood drop; VARIANTS.md ranks
  fixes by benefit per added complexity. Voxel edits only (no CAD).
- 14:12 (af-run re-spawned after the 14:05 session end; previous orphans left running, none duplicated). Base 2.0 mm
  continuation CONVERGED 14:11 at 22,000 steps (new criteria: Q range 0.02 %, fan dp on curve 0.2 %, mass in/out 1.0 %,
  vent ranges <= 2.5 %) -> out/flow-2.0.npz: fan 345.4 cm3/s at 19.94 Pa (curve 19.90), lambda 2.59 (inside 0.3-4),
  through-flow 7.65 in / 7.73 out cm3/s (inlet_roof -7.4, out_band -0.3, out_corner +2.9, out_wall +4.8, x1203 0),
  fin-exit plane +2.0 cm3/s. Same as pass 1 within 1 %. Started `post.py compute --tag 2.0` (all parts) in the
  background 14:12 (log out/post-2.0.log). Still running (orphans): 1.5 mm (step 5.5k at 14:09, deadline ~14:38 ->
  PARTIAL), speed50 (step 11.5k, deadline ~14:18), post 2.0-finaxis (S3 thermal left).
- 14:15 (continuation agent; predecessor killed ~14:05) runs V1/V2/V3 found ALIVE (venv launcher + child per run),
  ~2000 steps each at 14:11 (~0.26 s/step). Early windows (NOT results): V1 fan ~230 cm3/s, roof inlet ~223 cm3/s
  in (through-flow ~95 % of fan flow); V2 fan ~209, roof ~207; V3 fan ~96 at ~40 Pa, fin exit ~85 (lid forces the
  fins). No duplicates started. Plan: wait (one background loop) for flows (~14:57: 14:50 + 1500-step averaging
  window), then post until 15:12, then `variants.py report` + new `variants.py md` (writes VARIANTS.md tables);
  VARIANTS.md "Less is more" section written by hand.
- 14:15 figs for 2.0 (flow only) made and read: speed slices + streamlines readable; pressure slices showed a +-0.3 Pa
  lattice checkerboard -> post_figs.py now plots pressure through a 3x3x3 fluid-cell box filter (display only,
  labelled). merge() leaves the interim pass-1 out of the bar/profile figures (kept in metrics.json). Interim reads:
  speed50 at 12k steps: fan 168.6 cm3/s at 5.18 Pa (on the 50 % curve), through-flow 1.3 cm3/s (0.8 %); 1.5 mm at
  6k steps (PARTIAL): fan 352.6 cm3/s (+2.1 % vs 2.0 mm), through-flow 5.6 cm3/s (-25 %), out_band flips to outflow
  (+2.9) -> fan point grid-insensitive, the tiny vent split is NOT. Thermal projection: the divergence-free fluxes
  carry 10.5 cm3/s through the ambient boundary vs 7.7 at the LBM vent probes (state it).

## PAUSED by the user (main session, 14:20)
The user: "Ignore the airflow issue for now. Pause the airflow workflow." and "And the associated processes as well".
At 14:20 the main session stopped the airflow-finish workflow, the af-variants agent and every airflow python process
(run_airflow.py --dx 1.5 and --case speed50, post.py compute --tag 2.0, variants.py run V1/V2/V3). Nothing was deleted.
State on disk: network model done (out/network.md); domains done; solvers validated; base 2.0 mm flow finished
(out/flow-2.0.npz), finaxis flow + post done; 1.5 mm, speed50 and V1-V3 flows stopped mid-run (checkpoints
out/ckpt-*.npz, out/variants/ckpt-V*.npz: rerunning the same command resumes); no AIRFLOW.md, no verification.
Results so far are PARTIAL and unverified (network estimates + pass-1 3D: about 97 % internal recirculation).
Resume only on the user's instruction.

## r4 label (2026-10-05 evening, main session; study still PAUSED, nothing re-run)
- Audit `audit/d2-readiness-2026-10-05-r3/REVIEW.md` ("Airflow remains inconclusive"): `out/variants/VARIANTS-tables.md`
  now carries a hand-written STATUS banner: partial, superseded model output; the UA 0.20 block reuses the UA 0.095
  values; a printed thermal-gate "FAIL" is a model flag, not a G-W11 result. `variants.py` does not write the banner;
  before any re-run, fix the generator (label UA cases correctly, never print gate verdicts) instead of re-adding it.
- No process was started; no checkpoint, mesh or metric file was touched.
