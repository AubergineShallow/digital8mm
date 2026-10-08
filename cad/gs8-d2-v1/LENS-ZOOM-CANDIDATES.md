# GS8 D2: parfocal C-mount zoom candidates (desk research, 2026-10-06)

This is a user question ("any parfocal C-mount zoom lens candidates, vintage or modern machine vision?"). It is
desk research only: nothing was bought, fitted or measured, and **no zoom is adopted**. D2's CAD still offers only
the Kowa LM6HC (default) and the Fujinon HF6XA-5M primes.

The full reports, with sources, are:
- [research/ZOOM-vintage-cine-2026-10-06.md](research/ZOOM-vintage-cine-2026-10-06.md) (Super 8 / 16 mm cine
  zooms);
- [research/ZOOM-machine-vision-2026-10-06.md](research/ZOOM-machine-vision-2026-10-06.md) (machine-vision,
  CCTV and broadcast zooms).

## What the sensor means for a zoom

- **Size:** the IMX296 is 5.02 x 3.75 mm (6.27 mm diagonal), almost exactly a Super 8 frame (7.08 mm). The crop
  against 35 mm is 6.9, so D2's 6 mm prime is about **41 mm equivalent**.
- **"Parfocal"** means the focus holds while zooming. Most CCTV "zooms" are **varifocal** and must be refocused
  after every zoom, which is useless for a cine camera. Both reports check this from the maker's wording.
- **Back focus helps.** The Global Shutter camera's back-focus ring is adjustable over 12.5-22.4 mm (Raspberry Pi
  product data), so a zoom's flange distance can be trimmed until it tracks. Set it at tele, zoom out, trim until
  the wide end stays sharp, then lock the ring.
  - The ring can only **lengthen** the flange distance.
  - D-mount (Double 8) lenses, with a 12.29 mm flange, fall below it and are excluded.
- **Rear clearance:** Raspberry Pi publishes no maximum rear protrusion. Its own 6 mm lens puts glass about
  10 mm behind a C flange, and every candidate below is quoted at about 6 mm or less. Measure before buying; this
  is gate G-LENS.

## Combined ranked shortlist for D2

| # | Lens | Range (35 mm eq on D2) | f/ | Mass | Parfocal | Used price (new) | Why / watch |
|---|---|---|---|---|---|---|---|
| 1 | **Computar H6Z0812, manual-iris version** (= Edmund #53-152) | 8-48 mm (55-331) | 1.2 | 305 g | yes (Computar's own definition of "zoom") | US$47-100, S$60-128 (US$645 new) | Best value. All-manual, 1/2 in coverage, rear glass about 6 mm behind the flange. Analogue-era: no MP rating, so expect softness at 3.45 um wide open. |
| 2 | **Schneider Optivaron 6-66 mm f/1.8 Macro** (Beaulieu C-mount, Super 8) | 6-66 mm (41-455) | 1.8 | about 600 g [derived] | yes | US$250-450, S$320-580 | The only common true zoom that keeps D2's 6 mm / 41 mm wide end; designed for this frame size. Its reported non-standard flange is trimmable. Heavy for D2's balance; check for haze and the Reglomatic box. |
| 3 | **Kowa LMZ68M** | 8-48 mm (55-331) | 1.0 | 280 g (lightest found) | likely; Kowa does not say "parfocal" [unconfirmed] | price and status unknown | Rated 100/60 lp/mm, 0.5 m minimum focus plus macro. Confirm parfocal behaviour and availability first. |
| 4 | **Angenieux 8-64 mm f/1.9** (Beaulieu C-mount) | 8-64 mm (55-442) | 1.9 | 500 g with its iris box (manual-zoom versions lighter) | yes | US$330-450 (Pro8mm collimated US$1,495) | Classic cine look, 49 mm filter. |
| 5 | **Computar M6Z1212-3S** (= Edmund #53-153) | 12.5-75 mm (86-518) | 1.2 | 483 g | yes | about US$85 (US$705 new) | The only 3 MP-rated parfocal C zoom found, so the sharpest on these pixels, but its wide end is a short telephoto. |

**Also seen:**
- ViewZ VZ-B6X8M: 8-48 mm f/1.0, 380 g, still in production at US$317.
- Pentax/Cosmicar H6Z810: 8-48 mm f/1.0, 440 g, US$55-200 used.
- Ricoh FL-CC6Z1218-VG: 12.5-75 mm, 320 g, the best rear clearance found.
- Angenieux 6-80 f/1.2: 41 mm eq, about 880 g, soft on digital sensors.
- Optivaron 6-70 f/1.4: about 900 g.
- Navitar Zoom 7000: 840 g.
- Canon V6x16: 620 g.

**Ruled out:**
- Tamron M13VM / M118VM, Tokina TVR, Theia, Goyo GMZ, Kowa LMVZ and Fujinon DV/YV: all varifocal.
- Navitar 6000/12X and Edmund VZM: macro-only.
- Bolex RX lenses: corrected for a reflex prism.
- 16 mm cine zooms: their wide ends sit at 66-117 mm equivalent on this sensor.
- Leicina-mount, Bauer-mount and Bolex-bayonet zooms: not C-mount.
- All D-mount lenses.
- Motorised or auto-iris versions: the iris parks closed without power, so buy the manual-iris models.

## What a zoom changes in D2

**Balance:** this is an estimate from the release mass model, checked against the receipt (the Fujinon case
reproduces the receipt's -8.9 mm). The lens centre of mass is assumed at about 40 % of its length from the flange.
The D2 target is 0 to +8 mm ahead of the grip axis.

| Lens | Mass | Centre of mass ahead of the grip axis |
|---|---|---|
| Kowa LM6HC (current) | 215 g | +3.7 mm |
| Kowa LMZ68M | 280 g | about +12 mm |
| Computar H6Z0812 | 305 g | about +15 mm |
| Angenieux 8-64 | 500 g | about +33 mm |
| Optivaron 6-66 | 600 g | about +41 mm |

The machine-vision zooms are mildly nose-heavy; the left hand on the zoom ring carries it, as on a Nizo. The
Super 8 zooms are strongly nose-heavy and would need a lens support or a rebalanced grip.

**Other changes:**
- **CAD:** a zoom needs a new `layout.LENSES` entry (segments, mass, centre of mass), a check of the hood
  turret, front plate and hand clearance, and a rebuild.
  - The Computar is 51.75 mm in diameter, slimmer than the Kowa's 54 mm, so the fit is likely, but it is 97 mm
    long against the Kowa's 57 mm.
- **Gate G-LENS:** measure the rear protrusion against the C-CS adapter and the filter, and set parfocal
  tracking on the bench.

## Suggested next step

Buy a used **Computar H6Z0812** (manual iris, about S$60-130). It is the cheap, low-risk way to try a true zoom on
the real camera: check rear clearance and tracking with the back-focus ring, and feel the balance. If the 55 mm
wide end is too tight, the Optivaron 6-66 is the only wide true zoom, and it costs a balance redesign.

## Load path: can the camera's own mount carry a zoom? (2026-10-06, user question)

**The user's observation:** the Global Shutter camera's lens mount is plastic and is screwed to the sensor PCB, not
to a chassis. Raspberry Pi publishes neither a mount material nor a lens-weight limit.

> **r5 correction (2026-10-06, `R5-BRIEF.md`; study `research/r5-lens-support/`).** The premise below is partly wrong,
> and the fix is now in the CAD:
> - **The lens mount is milled aluminium, not plastic** (Raspberry Pi HQ/GS product briefs and the filter-removal
>   procedure). The compliant link is the **housing-to-PCB joint**: 2 small M2 socket screws with nylon washers on a
>   sticky gasket. That joint, not the mount body, is where a hanging lens creeps. The real load path is lens -> C-CS
>   adapter -> back-focus ring (a fine external thread, about dia 28.8, wall about 1.7, pinched by the split-tab lock
>   screw) -> housing -> M2 screws, nylon washers and gasket -> PCB.
> - **D2's r4 camera model did not match the official drawing:** there are no 39.5 front lands (39.5 is the rear
>   cover), the C flange sat about 10 mm too far forward, and the 2 printed pins ended about 7 mm short of the PCB. So
>   "How D2 carries the lens today" below describes r4's model, not the real camera.
> - **Adopted fix: the J7-R float** (SPEC s3 J7, DESIGN s1). A printed, per-lens `lens_collar` clamps the lens on its
>   fixed rear band (Kowa: the dia 42 knurl at +2.2..+7.6 from the flange, to be confirmed at G-LENS) and is anchored on
>   the tub front wall by 3 M3 screws in heat-set inserts plus a compression foot. The camera hangs on the lens and
>   touches no printed part in service; a tub lip, a hood roll fin and the panel keeper are catches with gaps. This is
>   Raspberry Pi's own advice (support a heavy lens, let the camera float), and any creep in the printed parts moves
>   lens and sensor together: an aim change, never a focus tilt. Option 2 below, made concrete.
> - **Zoom rule:** a zoom can use D2 only if it has a **fixed (non-rotating, non-translating) band of at least
>   15 mm** for its own collar (`layout.LOAD_MODEL['zoom_band_min']`; `checks.check_lens_support`). The Computar
>   H6Z0812 is a data-only `LENSES` entry: its dia 48.5 band (+1.0..+25.5, from the drawing) passes on paper (clamped
>   22.5; M_sep 0.71 N m against a static 0.09 N m) and is not built. Any lens over 150 g without a band FAILs.
> - **Plan B** (documented, not built; SPEC s10): if G-LENS shows that the Kowa band moves, a housing clamp (a printed
>   cradle in the tripod-block seat, a clip over the lock tab, 3 PT screws) holds the camera housing instead.
> - The gate below is now **G-CAM-2** (SPEC s10: 3x lens mass, 15 N side push, 50 g on the cover, 1 h at 50 C; the
>   corner-vs-centre focus change <= 4 um), with G-LENS extended and the collar coupon gate G-COL-1.

**How D2 carried the lens in r4 (J7; superseded by r5, see the correction above):**
- The mount's front lands rest on the front-wall inner face, which carries axial push.
- 2 printed pins locate the PCB, and a panel finger sits behind the cover.
- The back-focus ring runs in a dia 36.5 bore with **0.25 mm radial clearance**, unclamped so that it can turn.
- So every bending moment goes lens -> C-CS adapter -> plastic mount -> mount screws -> PCB -> pins. The bore
  catches the ring only after it has moved about 0.25 mm, which is about 0.8 deg of mount tilt.
- The depth of focus at f/1.8 with a 2-pixel circle is about +-12 um. Across the 5 mm sensor that allows only
  about 0.3 deg of tilt before one edge goes soft. **The bore stops damage, not focus error.**

**Bending moment at the mount face**, taking the lens centre of mass at about 40 % of its length from the flange:

| Lens | Mass | Arm | Static moment | Moment at a 5 g knock (G-LENS) |
|---|---|---|---|---|
| Kowa LM6HC | 215 g | about 44 mm | about 0.09 N m | about 0.46 N m |
| Computar H6Z0812 | 305 g | about 55 mm | about 0.16 N m | about 0.8 N m |
| Angenieux 8-64 | 500 g | about 66 mm | about 0.32 N m | about 1.6 N m |
| Optivaron 6-66 | 600 g | about 71 mm | about 0.42 N m | about 2.1 N m |

**Handling adds more.** Gripping the zoom ring adds 10-20 N of side load at 60-80 mm, about 0.6-1.6 N m.
Turning the zoom or focus ring puts its torque through the C thread into the mount.

**Risks:**
- Plastic creep at the warm closed-body temperature (the paused airflow study points to a warm interior) turns a
  small static moment into slow tilt and focus drift.
- Shock can crack the mount or pull its screws out of the PCB.

**Conclusion:**
- Even the Kowa prime relies on the mount and PCB alone, which is why G-LENS exists.
- A 280-600 g zoom, held and turned by hand, should **not** hang on the camera's mount.
- Any zoom needs the lens load taken into the body, with the camera module only locating the image plane.

**Options, cheapest first** (as written before r5; r5 adopted option 2 as the J7-R float, see above):
1. **Clamp the back-focus ring once back focus is set.** A split printed collar with one PH1 screw, in place of
   the 0.25 mm running clearance, takes the bending load into the tub and hood about 5 mm from the mount face.
   This bypasses the mount body and the PCB if the lens thread is carried by that ring, which needs checking on
   the real camera. It costs re-adjustment access (unscrew the collar first).
2. **A lens support collar** on a non-rotating section of the lens barrel, tied to the tub, base or hood. This is
   classic cine practice for heavy zooms. It needs the lens in hand to find a fixed section: many machine-vision
   zooms have rotating rings over most of their length.
3. **A chassis-mounted C-mount ring** (purchased metal adapter plate) with the camera module floating behind it.
   The strongest option, but the flange-distance stack (17.526 mm to a few hundredths) moves into the printed
   parts and the camera's back-focus ring leaves the chain. Not recommended without measurements.

**Gate (extends G-LENS):** with the real camera and lens, hang the lens mass x 3 and apply a 10-20 N side load at
the zoom ring. Measure the image shift and edge-to-edge focus change on a target, then repeat after 1 h at about
45 C to see creep. Pass: tilt small enough that edge focus stays within the depth of focus.
