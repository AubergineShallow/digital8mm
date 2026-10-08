# GS8 D2: M12 lenses on the Global Shutter camera, and add-on anamorphics (desk research, 2026-10-06)

This answers the user's question: "M12 lenses with an adapter to CS-mount? Also add-on anamorphic lenses (Moment
type) on top of them."

It is desk research only: nothing was bought, fitted or measured, and **nothing is adopted**. The CAD still offers
only the Kowa LM6HC and the Fujinon HF6XA-5M.

**r5 note (2026-10-06, later the same day):** this page was written against the r4 camera model. r5 corrected it (`R5-BRIEF.md`): the GS lens mount is aluminium, the C flange sits at about x +0.6 (not +10.6), and the camera now floats, hanging on a lens that a printed `lens_collar` clamps to the tub. An M12 front end therefore needs its own collar (or the documented Plan-B housing clamp), and the balance figures below must be recomputed on the r5 stack.

Full reports, with sources:
- [research/M12-lenses-2026-10-06.md](research/M12-lenses-2026-10-06.md)
- [research/ANAMORPHIC-addons-2026-10-06.md](research/ANAMORPHIC-addons-2026-10-06.md)
- The camera drawings are in [research/m12-drawings/](research/m12-drawings/).

## M12 (S-mount) on the Raspberry Pi GS camera

**The fit**

Raspberry Pi sells the GS camera only in C/CS-mount. Its mount is the HQ camera's, and the HQ's official M12
version (SC0870) takes lenses with a back focus of 2.6-11.8 mm.

On the GS camera, an M12 lens goes in through an adapter. The best one found is the Commonlands **CLA127**: a flat
3.5 mm disc the lens threads through, US$6. The alternatives are:
- the CLA-M12-CS 10 mm cup;
- the Arducam UB0225;
- Edmund's M12-to-C adapters, which suit long-backed lenses only.

**The one blocking unknown**

The GS drawing (`research/m12-drawings/gs_side.png`, checked) shows:
- a dia 22.4 bore;
- an 8.5 mm square window at the bottom of the throat;
- a 1.1 mm IR filter (Hoya CM500) just above the sensor.

A 12 mm M12 barrel stops on that window floor. A lens whose barrel must come within about 2.5 mm of the image plane
may hit it before reaching infinity. Nobody publishes the floor depth, and no one was found using M12 lenses on the
GS camera (they do work on the HQ camera). **Measure it first.**

**Lenses that cover the sensor**

| # | Lens + adapter | Focal (35 mm eq) | f/ | Price | Why / watch |
|---|---|---|---|---|---|
| 1 | Commonlands CIL068 + CLA127 | 6.8 mm (47) | 2.5 | about US$55 | All glass. Its long 6.6 mm back distance keeps it clear of the window. |
| 2 | Commonlands CIL083 + CLA127 | 8 mm (55) | 2.8 | about US$25 | 4 g, nearly distortion-free. Its shallow entrance pupil (5.4 mm) makes it the **best anamorphic host**. |
| 3 | Commonlands CIL059 + CLA-M12-CS | 5.9 mm (41) | 1.7 | about US$61 | Same framing as the Kowa and the fastest, but its short back distance needs the floor check. |
| 4 | Gaojia 8 mm (Raspberry Pi-recommended) + UB0225 | 8 mm (55) | 1.8 | about US$27 | Published chief ray angle 10.8 deg or less (the angle light hits the sensor). More barrel distortion. |
| 5 | Commonlands CIL043 + CLA127 | 4.4 mm (30) | 3.2 | about US$45 | Truly fixed-focus (sharp from 0.45 m to infinity when set at about 0.9 m), but the highest window risk. |

**What changes against the Kowa**

- **Weight:** lens + adapter is 10-20 g instead of 215 g. That removes the load on the plastic mount entirely.
- **Focus:** you turn the whole lens in its 0.5 mm thread. An 8 mm lens needs about 94 deg of turn from infinity to
  0.5 m, so a printed lever or collar on a preloaded lens is workable. Wide lenses can be fixed-focus, like a Nizo
  set by a distance scale.
- **No iris:** exposure is by shutter time and ND filters only.
- **Lens shading:** avoid phone-style lenses whose chief ray angle is 20-30 deg; they shade the corners in colour.
  Recalibrate the camera's shading table per lens.
- **No M12 zoom holds focus:** the only one found, the Marshall CV-2812, is varifocal.

## Add-on anamorphic adapters (phone type)

**Why they fit**

Phone anamorphics are built for main cameras of about 24-26 mm equivalent with 2-4 mm entrance pupils. An M12
lens of 5-8 mm on the IMX296 is the same geometry (34-55 mm equivalent, 1.4-6 mm pupils).

Estimated vignetting-free range on D2:
- **1.33x adapters:** about 5-12 mm (4 mm borderline).
- **1.55x adapters:** 6 mm and longer.

The heavy cine and camcorder adapters (Kowa, Iscorama, SLR Magic, Century, Panasonic, Sirui 1.25x and Moment's
own cine adapter) weigh 250-1,500 g, need 43-82 mm threads and often focus separately. They are ruled out.

**Shortlist**

| Rank | Adapter | Squeeze -> output | Weight | Price | Why |
|---|---|---|---|---|---|
| 1 | Moment Anamorphic 1.33x (T-Series, Mobile Lens II) | 1.33x -> 16:9 | 43.5 g | US$150 (S$192) | Best optics, indexed bayonet, largest rear opening |
| 2 | Ulanzi 1.33x Pro (3rd gen) | 1.33x -> 16:9 | 31.5 g | about US$60-80 [unconfirmed] | Cheapest proof of geometry; 17 mm thread |
| 3 | ShiftCam LensUltra 1.33x | 1.33x -> 16:9 | 34 g | about US$135 | Published close focus 70-90 cm |
| 4 | Moment 1.55x (T-Series) | 1.55x -> 2.07:1 | about 40 g | US$125-199 | Wider look, but softer edges and more vignetting |

**The output geometry is a natural fit**

The 4:3 sensor (1456 x 1088) with a 1.33x squeeze gives exactly **16:9**: desqueezed to 1941 x 1088. A 1.55x
squeeze gives 2.07:1. For 2.39:1, crop.

**Pipeline**
- rpicam-apps has no desqueeze option, but the Pi's image processor stretches a stream whose shape differs from
  the sensor crop. So record the full squeezed frame at 1456 x 1088, and request a 1024 x 576 preview stream,
  which arrives desqueezed for the 1024 x 768 EVF. This needs checking on a Pi 5, where the default crop may keep
  the aspect ratio.
- Tag the files with a 4:3 pixel aspect ratio using an ffmpeg metadata-only change (no re-encode). Resolve has a
  1.33x anamorphic setting.

**Mounting rules**
1. Mount the adapter to the **housing front plate, never to the M12 lens**: the lens turns when focusing, which
   would rotate the squeeze axis.
2. Its rear glass should sit within about 0.5-2 mm of the M12 lens front.
3. Add a light-tight sleeve over the gap.
4. Add a rotation index good to about 0.5-1 deg.

**Interfaces**
- Moment's stick-on mount;
- a 17 mm-thread backplate (Ulanzi);
- a printed bayonet.

No Raspberry Pi or M12-specific design was found, so D2's would be the first.

**Limits**
- Focus no closer than about 0.7-0.9 m without a +0.5 to +1 dioptre close-up lens.
- Stop down to f/2.4-2.8 against cylindrical softness. The M12 lenses are fixed-aperture, so choose an f/2.4-2.8
  one.
- Expect flare streaks (that is the look).

## What it does to D2's balance (estimate from the release mass model)

This uses the same model that reproduces the receipt's +3.7 mm (Kowa) and -8.9 mm (Fujinon). The target is 0 to
+8 mm ahead of the grip axis.

| Front end | Front mass | Centre of mass vs grip axis |
|---|---|---|
| Kowa LM6HC (current) | 215 g | +3.7 mm |
| M12 lens + adapter + printed front plate (about 15 + 15 g) | about 30 g | about -19 mm (rear-heavy) |
| The same + Moment 1.33x adapter (43.5 g) | about 74 g | about -13 mm |

To bring the M12 + anamorphic setup back to about +4 mm, about 170 g must sit roughly 80 mm ahead of the grip axis.
For example, the anamorphic mount could be a dense front collar or brass ring in the front plate. That is about the
Kowa's mass again, but carried by the housing, not the plastic mount. The alternative is accepting a rear-heavy
camera or moving the grip.

**CAD changes if adopted:**
- a new `layout.LENSES` entry for the M12 + adapter;
- a front plate carrying the anamorphic bayonet or thread, with an index, sleeve and ballast;
- the focus lever or collar;
- a rebuild.

## Non-rotating helicoid focus (2026-10-06, user question)

**The question:** can a helicoid adapter focus the M12 lens, with the anamorphic on the adapter's front, so the front
moves without rotating?

**Yes. This is a non-rotating (keyed) helicoid**, the way most manual photo lenses focus. It has three parts:
- a **fixed base**, threaded to the camera, with a straight keyway;
- a **focus ring** that turns on the base and is captured axially;
- a **carrier** that holds the M12 lens. It is threaded to the ring and keyed to the base, so it slides without
  turning.

The lens is screwed into the carrier once to set infinity, then locked with its jam nut. After that the lens never
rotates, which also removes the image wander from lens decentre while focusing.

**The travel is tiny** (Δ ≈ f²/(u - f)):

| Lens | Infinity to 0.9 m | Infinity to 0.7 m (anamorphic close focus) | Infinity to 0.5 m |
|---|---|---|---|
| CIL083 8 mm | 0.072 mm | 0.092 mm | 0.130 mm |
| CIL068 6.8 mm | 0.052 mm | 0.067 mm | 0.093 mm |

- The image-side depth of focus is about ±N·c: ±19 um at f/2.8 and ±17 um at f/2.5, with a 2-pixel circle of
  6.9 um. So the whole infinity-to-0.7 m range is only about 5 depths of focus.
- Hence a stroke of about 0.2-0.3 mm (focus plus margin) is enough. Infinity is set by the lens thread, not by the
  helicoid.
- **Throw against lead**, for the 8 mm lens from infinity to 0.7 m:
  - a 0.25 mm lead turns 133 deg;
  - a 0.5 mm lead turns 67 deg, the same as turning the bare lens;
  - the 1"-32 C thread (0.794 mm lead) turns 42 deg.

**Precision is the hard part, not the idea:**
- **Thread or slot play:** play of 0.05-0.15 mm (typical for FDM or cheap threads) is as large as the whole focus
  stroke. The carrier needs a wave-spring axial preload against one flank, as the M12 report already advises for
  a bare M12 thread.
- **Carrier tilt** must stay under about 0.4 deg: the 19 um depth of focus over the 2.5 mm half-width.
  - A clearance of 0.02 mm over an 8 mm guide gives about 0.14 deg, which passes.
  - 0.15 mm gives about 1 deg, which fails.
- **Conclusion:** the carrier, ring and base need machined metal or a good resin (SLA) print. FDM is fine only for
  the focus lever or gear, the sleeve and the front-plate tab.

**Put the anamorphic on the fixed base, not the moving carrier.** The base is still "the adapter's front".
- **The gap barely changes:** with the travel at 0.1-0.15 mm, the gap to the lens changes far less than the 0.5-2 mm
  window allowed.
- **Lighter moving part:** the helicoid moves only about 10 g instead of about 55 g.
- **The key stops mattering optically:**
  - The squeeze axis is set once, between the base and the camera.
  - If the anamorphic rode on the carrier, the key clearance would become squeeze-axis error. That is g/r: 0.15 mm
    at a 12 mm radius is about 0.7 deg, at the limit of the 0.5-1 deg index.
- **Load:** about 75-80 g at a 20-25 mm arm is about 0.02 N m static and 0.1 N m at 5 g. That is about a fifth of
  the Kowa's moment, so the base may hang on the camera's CS thread, which also keeps it aligned to the sensor.
- **Focus torque:** a radially free tab on the base, sitting in a front-plate slot, takes the focusing torque, so
  turning the ring cannot unscrew the base or move the back-focus ring.

**Off-the-shelf parts:**
- Edmund's TECHSPEC C-mount helicoid barrels (#57-649 and family) are non-rotating, with up to 16 mm travel.
  - They thread in at the C flange, so the optic sits 17.5 mm or more from the sensor. An M12 lens needs about
    3-7 mm.
  - So they cannot hold the M12 lens: they would give macro-only focus with no infinity. Photo macro helicoids are
    worse still (M42 and up, coarse lead).
- **The likely route is a custom carrier:**
  - a tube under 22 mm in diameter that holds the lens deep in the throat;
  - the helicoid thread in front of the CS ring, where there is room.
  - The Commonlands CLA-M12-CS (aluminium; lens thread in its bottom 5 mm; lock ring included) is a candidate
    starting part, with its 1"-32 spigot used as the male helicoid thread.

**Unknowns to measure** (alongside the throat-floor check in the next step):
- each lens's overall length, which sets where its front, and so the anamorphic's rear glass, sits ahead of the CS
  flange;
- how the GS back-focus ring is built and whether it can be removed.

**Status:** nothing has been modelled.

## Suggested next step (about US$75 + US$60-80)

1. Buy the CLA127 + CIL068 + CIL083 (about US$75).
2. Measure the GS throat-floor depth and confirm infinity focus with enough thread engaged.
3. Shoot flat fields per colour channel for vignetting and colour shading.
4. Then tape or print-mount a **Ulanzi 1.33x** in front of the 8 mm lens: check vignetting at 6.8 and 8 mm, the
   rotation alignment and close focus.
5. If it is clean, step up to the Moment 1.33x T-Series.
6. Keep the Kowa as the D2 default until these pass.
