> **STATUS (r4 label, 2026-10-05, audit d2-readiness-2026-10-05-r3): PARTIAL, SUPERSEDED MODEL OUTPUT. NOT A HARDWARE RESULT.**
> The study was paused by the user at 14:20 before completion; no `AIRFLOW.md` exists. Known defects in these tables: the "UA 0.20" block reuses the UA 0.095 values (each cell says so), and any thermal-gate "FAIL" printed beside the extreme interim model temperatures is a model flag, **not** a G-W11 result. The model omits buoyancy, had its wall-loss scaling corrected after these runs, and shows large finer-grid uncertainty (airflow/NOTES.md). Use these numbers only as a reason to investigate cooling; G-W11 and G-W12 stay open until measured. This label was added by hand; `variants.py` would drop it on a re-run (fix the generator first).

| quantity | existing |
|---|---|
| run status / steps | converged / 10000 |
| fan Q (cm3/s) [CFM] | 346 [0.73] |
| fan dp delivered / on curve (Pa) | 19.9 / 19.9 |
| through-flow in / out (cm3/s) | 7.5 / 7.6 |
| through-flow / fan flow | 2 % |
| mass balance (out-in)/in | 0.8 % |
| fin inlet / fin exit face flow (cm3/s) | 338 / -29 |
| recirculation R (fan-heat source method) | 0.973 |
| fin-exit tag at fan intake | 0.797 |
| mean age interior air / fan intake (s) | n/a / 71.1 |
| vent inlet_roof (cm3/s, + = out) | -7.3 |
| vent out_band (cm3/s, + = out) | -0.2 |
| vent out_corner (cm3/s, + = out) | +2.9 |
| vent out_wall (cm3/s, + = out) | +4.7 |
| vent x1203 (cm3/s, + = out) | -0.0 |
| fan intake air from inlet_roof | 0.87 |
| fan intake air from out_band | 0.12 |
| fan intake air from out_corner | 0.00 |
| fan intake air from out_wall | 0.01 |
| fan intake air from x1203 | 0.00 |

**S2, wall loss UA 0.20 W/K** (air temperatures COMPUTED, deg C; SoC = ESTIMATE)

| quantity | existing |
|---|---|
| fan intake air (flux mean) | 190 (UA 0.095) |
| fin exit air | 202 (UA 0.095) |
| EVF board air | 402 (UA 0.095) |
| X1203 air | 409 (UA 0.095) |
| camera air | 203 (UA 0.095) |
| USB stick air | 528 (UA 0.095) |
| Pi board air | 409 (UA 0.095) |
| fin inlet air | 192 |
| R_sink nominal (K/W) | 4.8 |
| SoC ESTIMATE, R_jc low | 210 |
| SoC ESTIMATE, R_jc nominal | 211 |
| SoC ESTIMATE, R_jc high | 217 |
| G-W11 SoC < 80 (nominal / high R_jc) | FAIL / FAIL |
| X1203 air < 70 | FAIL |
| energy balance (rel) | -7e-08 |
**S2, adiabatic walls** (air temperatures COMPUTED, deg C; SoC = ESTIMATE)

| quantity | existing |
|---|---|
| fan intake air (flux mean) | 1121 |
| fin exit air | 1098 |
| EVF board air | 1714 |
| X1203 air | 1791 |
| camera air | 1136 |
| USB stick air | 1536 |
| Pi board air | 1369 |
| fin inlet air | 1120 |
| R_sink nominal (K/W) | 4.8 |
| SoC ESTIMATE, R_jc low | 1138 |
| SoC ESTIMATE, R_jc nominal | 1140 |
| SoC ESTIMATE, R_jc high | 1145 |
| G-W11 SoC < 80 (nominal / high R_jc) | FAIL / FAIL |
| X1203 air < 70 | FAIL |
| energy balance (rel) | 2e-08 |
**S3, wall loss UA 0.20 W/K** (air temperatures COMPUTED, deg C; SoC = ESTIMATE)

| quantity | existing |
|---|---|
| fan intake air (flux mean) | 330 (UA 0.095) |
| fin exit air | 356 (UA 0.095) |
| EVF board air | 509 (UA 0.095) |
| X1203 air | 695 (UA 0.095) |
| camera air | 351 (UA 0.095) |
| USB stick air | 921 (UA 0.095) |
| Pi board air | 654 (UA 0.095) |
| fin inlet air | 333 |
| R_sink nominal (K/W) | 4.8 |
| SoC ESTIMATE, R_jc low | 377 |
| SoC ESTIMATE, R_jc nominal | 380 |
| SoC ESTIMATE, R_jc high | 394 |
| G-W11 SoC < 80 (nominal / high R_jc) | FAIL / FAIL |
| X1203 air < 70 | FAIL |
| energy balance (rel) | 4e-08 |
**S3, adiabatic walls** (air temperatures COMPUTED, deg C; SoC = ESTIMATE)

| quantity | existing |
|---|---|
| fan intake air (flux mean) | 1997 |
| fin exit air | 1961 |
| EVF board air | 2672 |
| X1203 air | 3163 |
| camera air | 2022 |
| USB stick air | 2718 |
| Pi board air | 2366 |
| fin inlet air | 1995 |
| R_sink nominal (K/W) | 4.8 |
| SoC ESTIMATE, R_jc low | 2039 |
| SoC ESTIMATE, R_jc nominal | 2043 |
| SoC ESTIMATE, R_jc high | 2057 |
| G-W11 SoC < 80 (nominal / high R_jc) | FAIL / FAIL |
| X1203 air < 70 | FAIL |
| energy balance (rel) | 9e-10 |
**Fin flow along the fin block** (COMPUTED x-flux through the fin section) and the SoC ESTIMATE on the length-mean fin flow (same sink law as af-run, which uses the fin INLET flow; air that leaves the open top early does not wash the whole fin length, so the inlet basis is optimistic)

| quantity | existing |
|---|---|
| fin flow at mid-length (cm3/s) | 27 |
| length-mean fin flow, negatives as 0 (cm3/s) | 89 |
| SoC ESTIMATE length-mean basis, S2 wall_UA0.20 (R_jc nominal / high) | 236 / 241 (UA 0.095) |
| SoC ESTIMATE length-mean basis, S2 adiabatic (R_jc nominal / high) | 1164 / 1170 |
| SoC ESTIMATE length-mean basis, S3 wall_UA0.20 (R_jc nominal / high) | 441 / 454 (UA 0.095) |
| SoC ESTIMATE length-mean basis, S3 adiabatic (R_jc nominal / high) | 2103 / 2117 |

**Buoyancy hand ESTIMATE** (not simulated; the LBM has no buoyancy): stack dp = rho g H dT / T_abs, H 67 mm: dT 5 K -> 0.012 Pa, dT 10 K -> 0.025 Pa, dT 20 K -> 0.050 Pa, dT 40 K -> 0.099 Pa

| case | largest forced vent dp from the loss law (Pa) | S2 wall-case body air rise at the EVF (K) | stack dp at that rise (Pa) |
|---|---|---|---|
| existing | 0.021 | n/a | n/a |

Source of the existing-arrangement column: out/metrics-2.0-pass1-10k.json (af-run); tables made 2026-10-05 14:15:27.
