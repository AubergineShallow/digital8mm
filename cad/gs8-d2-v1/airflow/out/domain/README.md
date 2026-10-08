# D2 air domain (af-domain), baseline r2 arrangement

Made 2026-10-05 by `airflow/export_meshes.py` (run once under the CAD lock, 129 s) and `airflow/voxelize.py`
(run outside the lock, about 30 s for both grids). Geometry: the baseline release pipeline (`build_d2.build_printed` +
`build_cots`, default lens kowa_lm6hc, no FR1 changes). There were no stubs, and all 38 meshes are watertight
2-manifolds (`out/meshes/index.json` has the bounds, triangle counts and source hashes). Purchased parts are proxies.
Nothing here is a measurement.

## Files

- `../domain-2.0.npz`, `../domain-1.5.npz`: the shared interface from `airflow/NOTES.md`. Keys: `dx`, `origin`
  (centre of cell (0,0,0), assembly mm), `solid`, every `mask__*`, and `meta_json`. Two extra keys: `label` (int8,
  legend in meta) and `part` (int16 index into `part_legend`, -1 = none).
- `summary-<dx>.json`: the same meta as readable JSON (vents, fan, heat, pockets, plugs, connectivity, counts).
- `slice-<dx>-<axis><value>.png`: label slices through the cooler (z 27), the blower top / out_corner (z 33), the
  X1203 sandwich (z 13), the exhaust plenum (x -7), the EVF board (x -140), the roof inlet over the blower (x -58),
  roof inlet - blower - fins - front (y -10), and the right wall (y -33.6). Dark red dots mark air cells that
  receive heat.
- `voxelize.log`: per-part occupancy, timings and results.

## How the domain is built

- **Grid.** Cell faces lie on multiples of dx, so x = 0 (the front face) and z = 0 (the body bottom) are cell faces.
  dx 2.0 gives 86 x 45 x 60 cells; dx 1.5 gives 112 x 57 x 77.
- **Occupancy.** Each part is sliced (manifold3d) at 3 levels per cell and scan-converted with the even-odd rule at
  3 x 3 points per cell, giving 27 sub-samples. The shells (tub, hood, panel, base_grip) are solid where ANY
  sub-sample is inside, which keeps walls of dx/3 or more closed. All other parts are solid where 14 or more of the
  27 sub-samples are inside.
- **Body interior.** First the vent zones and the plugs are closed and the outside is flood-filled from the grid
  boundary. Nothing leaks: the interior never meets the outside except through a vent. The main interior is the
  connected air that holds the fan intake. The outside is inactive (solid) except in the vent buffers.
- **Closed holes (label 10, `mask__leak__*`).** The grip/battery bay is excluded. The floor lead holes
  (`floor_pigtail`, `floor_run_lead`) are treated as closed by the leads and a grommet. The microSD tweezer slot
  through both front walls (`ko_sd`, about 12 x 2.3 mm less the card) is treated as closed with the card in place.
  It is a real leak path. Opening it as a sensitivity also needs an outside buffer there, which is not built.
- **Vents (`mask__vent__<id>`, label 5).** A vent zone is the set of cells that overlap the wall along the normal and
  whose centre lies inside the vent's lateral box. The front vents are the tub window and the hood plate in series
  (x -5.2..0). The slots are not resolved; the porous zone carries the loss. The meta gives each vent's normal,
  thickness in cells, face cells, discrete/box area ratio (1.00 to 1.29), slot_w/pitch and its shortest air path
  from the fan intake and from the fin exit.
- **Outside buffer.** Beyond each vent face there are 5 buffer cells (label 3), grown 2 cells laterally, plus an
  ambient layer (label 4, `mask__ambient`) on the far face and the lateral rim.
- **Fan.** The proxy blower box (x -72.8..-42.8, y -24..4, z 23.4..36.3) is turned into housing walls one cell thick
  (-X, +-Y, top; the floor is the cooler plate) and an interior actuator (`mask__fan_actuator`, force unit +X). The
  top wall has an intake disc of r 9.0 at the proxy hub circle (`mask__fan_intake`). That radius is an ESTIMATE: no
  published intake size was used. The +X housing face is open only over the fin height (z 23.4..30.5) and is wall
  above it.
- **Fins.** `mask__fin_block` covers x -42.8..-9.5, y -25.55..16.95, z 23.4..30.5. The plates are normal to Y and
  open on top in the proxy, which models no shroud. So the block should be porous with low resistance along X (and
  along Z between the plates) and high resistance along Y. `mask__fan_outlet` is the first cell layer past the fins
  (x about -9). The SoC heat goes into the fin block (`mask__heat__soc`).
- **Heat masks.** Each mask is the interior air within 1 cell (26-neighbour) of its proxy:
  - X1203: the charger/boost field box.
  - EVF board.
  - Camera: gs_camera.
  - USB stick.
  - Pi board remainder: the PCB slab plus the underside parts (z 16..21.4); the jack blocks get no heat.
- **Probes.** Each probe is a set of air cells to average over:
  - `fan_intake_air`: the 2 layers above the intake.
  - The 5 component probes. Each one is the same set of cells as that component's heat mask.
  - `exhaust_plenum`: the ko_exhaust box.
  - `fin_exit`.
  - `roof_inlet_inner`: the layer under the roof zone.
  - `outside_<vent>`: the first buffer layer beyond each vent.

## Checks

| | dx 2.0 | dx 1.5 |
|---|---|---|
| interior air | 656 cm3 (82 051 cells) | 678 cm3 (200 983 cells) |
| fluid components | 1 | 1 |
| every vent reaches the fan intake and the fin exit through air | yes | yes |
| dropped pockets (no path to the fan or a vent) | 19, 9.6 cm3 | 11, 5.4 cm3 |
| fin block cells / actuator cells / intake cells | 1008 / 816 / 62 | 2576 / 2210 / 113 |
| fin section discrete / proxy | 252 / 302 mm2 | 252 / 302 mm2 |
| blower outlet open discrete / proxy | 144 / 199 mm2 | 153 / 199 mm2 |

**Dropped pockets.** The pockets are sealed air with no forced flow, so they are solid in the model.
- The largest (5-9 cm3) is the hood lens-collar cavity in front of the front wall, around the camera ring and C-CS
  adapter.
- Next come the small EVF optics cavities behind the board (hmx039 / eyepiece / foam).
- The rest are single cells: around the stack standoffs and screw bosses, plus a 40 mm3 corner by the X1203 at
  dx 2.0.

## Findings for the solver and the report (geometry, not flow results)

- **x1203 slots.** The proxy pogo-pin field (x -64..-13, y -31.8..-27.3, z 7.6..16) sits directly behind the x1203
  slots (x -65..-49, z 9.5..17.5). The slots only reach the sandwich through a band about one cell high above the
  pins (z 16..17.5) and around the ends. Their path from the fan intake (49 / 61 cells) is the longest of the vents.
  The pogo box is an estimate, so this needs checking on the real board.
- **out_wall slots.** The Pi 5 GPIO header and the board edge (0.2 mm off the right wall) sit behind the lower part
  of the slots, and the QT lead keep-out sits behind the upper part. At dx 1.5, 20 zone cells are pi5 solid.
- **Shortest paths.** The fin exit is 2 cells from out_band, 4 from out_corner and 7 from out_wall. The roof inlet is
  31 / 41 cells from the fan intake through the tall open chamber over the blower. There is NO wall between the fin
  exit / plenum and the space above the fins (the deleted baffle), so recirculation of exhaust to the intake is
  geometrically open.
- **Not modelled.** Cables and keep-out volumes (ribbon S-fold, HDMI coil, leads) are not modelled as solids, so
  they add blockage the model does not include. Fin height is 3 cells at dx 2.0 and 4 cells at dx 1.5 (6.0 mm
  against 7.1 mm), and the solver should scale the porous loss by the section ratio above.
