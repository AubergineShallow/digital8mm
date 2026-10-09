# SPEC-C2: leads mated in a non-final pose (BX-2 QT lead, BX-10 header sockets)

**r7 fix-up correction (VERIFY-C2, 2026-10-09).** Step 8 had no support for the panel and needed a third hand: now a
helper holds the body upright by the grip, the panel is propped 60 mm off on a block about 110 mm tall (grip height),
the 18/24 PH junction is mated first with both hands, then the QT plug by its rear end with a fingernail push (one hand
steadies the panel, thumb behind the encoder +X edge). `mate_reach` inline rows fps_ph and usb_5v_evf carry
`hand2='pinch_ph1'` (20 x 22 x 26 [est]): two pinch boxes about the junction J (the window point nearest the midpoint
whose body-side pinch is beyond the opening; fps_ph J y 55.4, out_of 0.38, pass with shapes). header_housings gains rule
(f) (every used pin exactly one housing). The W-QT joint window moves +8 mm (joints 91-115, nothing outside 85-121).

Status: design spec, r7 blocker round, 2026-10-08 (23:00-23:50 MPST). Cluster C2. Nothing in the repo was changed
except this file. Probes (not in the repo): session scratchpad `r7/C2/` (`qt.py`, `reach2.py`, `reach3.py`, `geo*.py`,
`sweep4.py`, `plugsweep.py`). Geometry: `layout.py` imported; part STEP files `out/step/parts/*.step` (16:05 build).
Nothing is printed, bought or measured. Every COTS dimension below is a CAD proxy or a design range with a named gate.
Reviewed 2026-10-08 23:05-23:35 MPST (adversarial spec review, cluster C2): corrected in place; see s10 "Review notes".
Review probes: scratchpad `r7/C2-review/` (`reach.py`, `clash.py`, `hdr.py`, `stow2.py`, `col.py`, `fps.py`, `orient.py`,
`runleads.py`). This is the final spec: where a review note and the text differ, the text wins.

## 1. Problem, re-checked against the current code

### BX-2 (MAJOR): QT lead too short for the step-8 mating pose

The `cable_routes` row for `qt` passes (est 117.6, allowance 15.0, slack 17.4). That number is optimistic. The route
ends at the far end of `ko_lead_cross` (y 20, z <= 44). The plug is 13-17 mm further on.

Re-check (probe `reach2.py`). The QT sockets are on the encoder back: x -74.65..-70.35 (the -X socket, nearest the
cross run) and x -55.65..-51.35, y 19.6..24.1, z 54..60 (`cots.encoder`, an estimate). A side-entry JST-SH socket at
the board edge takes the plug along +X, so the plug wire exit W sits at x -74.65 - 4.5 (plug proxy) = -79.15,
y 21.85, z 57. The nearest point of `ko_lead_cross` to W is (-79.15, 20.0, 44.0).

| quantity | value |
|---|---|
| route up to that anchor point (cable_routes method, first-box half included) | 117.6 mm |
| free tail anchor -> W, final pose | 13.1 mm |
| final pose, 150 mm lead, 15 mm allowance kept | 4.3 mm left |
| final pose, allowance used up | 19.3 mm left |
| panel offset +Y that a 150 mm lead allows, 10 mm plug/bend margin | 16.4 mm |
| same, no margin at all | 27.8 mm |
| with the existing chain extended to the plug (new boxes, s3) | est 134.6, slack 0.4 at 150 mm |

So BLOCKERS is right in substance: "0-7 mm past the socket" (now 4.3) and "panel 15-20 mm off its seat" (now 16-28,
depending on margin). The socket sits 8.1-12.6 mm inside the panel inner face (y 32.2). At +16 mm offset the encoder
back is only 3.0 mm outside the tub opening. No finger fits. Nothing computes a mating pose: `cable_routes` checks
only the final pose, and its estimate stops at the route box, not at the plug.

### BX-10 (MINOR): header Dupont housings are tight

The COTS `gpio` feature box is y -32.3..-27.2 (0..5.1 from the board edge). BLOCKERS' gaps (1.2 mm to the right wall,
0.7 mm to the cooler) are right only if the header row centres sit 2.23 / 4.77 mm from the board edge (centreline 3.5 mm).
That is the Raspberry Pi mechanical-drawing value, recalled, not re-read: confirm it in RP-008347 before implementing.
With it and the largest housing section of the class range (2.6): even-row housings (pins 6, 34) outer face y -31.37,
1.13 mm from the tub right wall (STEP distance; `Y_RW_IN` -32.5); odd-row housings (1, 3, 5, 33, 37, 39) inner face
y -26.23, 0.68 mm from the cooler box (y0 -25.55); 0.75 mm above the `x1203_kit` box top (z 21.85); hood >= 2.27 mm
(probe `hdr.py`; with a 2.54 section the gaps are 1.16 / 0.71). With the current edge-based box
the wall gap would read 0.2 mm. So the `gpio` proxy is 0.96 mm off and has to be fixed before any housing check means
anything. No check models the housings today. Below the pi5 box top (z 36.1) they sit inside the pi5 COTS envelope;
above it they sit in `ko_qt_lead` / `ko_run_leads` (z 28.8..40), except one: the pin-39 housing reaches x -63.83
(the 2x20 header's -X end), 0.83 mm beyond `ko_run_leads` x0 -63.0, so `ko_run_leads` grows to x0 -64.5 (s3.1).
Housing type is not stated anywhere except C-3 (the run lead must stay as separate sockets, or one 2.54 x 5.1 unit,
to pass the floor hole).

## 2. Chosen fix and why

**Fix BX-2 with a longer lead, a defined mating pose and a defined stow space.**

- QT lead length `L_QT` = 250 mm nominal, accepted range 240-270 mm (end to end, socket tip to SH plug face).
- Mating pose: the panel held 60 mm off its seat along +Y (on the existing `panel_on` path, which starts at +70).
  The encoder back is then 46.6 mm outside the tub opening: an index-and-thumb pinch fits, and the whole fingertip
  envelope lies outside the body (y >= 71.85 vs the body's outer face y 35.0) and clears the panel inner face by 0.35 mm.
  At the BX-2 pose (+16.4) the same envelope dips 6.75 mm into the open tub; that is what the new `out_of` rule fails.
- Spare lead stows as a flat fold in a new keep-out `ko_lead_stow`, shared with the 18/24 lead's spare and its PH
  junction (that spare, about 117 mm plus the junction, had no home either). It lies along the panel inner face
  between the encoder and the 18/24 switch, on top of the HDMI run, 17 mm or more from the blower footprint. Worst-case
  QT spare: 270 - 134.6 = 135.4 mm (no allowance deducted).
- Lead construction (decided, all parts named and orderable): **Adafruit 4397** (150 mm, 4 premium 1-pin female
  sockets, as now) spliced on the bench to **Pololu #5521** (JST SH-style 4-pin cable, female SH housing on one end,
  unterminated, 30 cm, 28 AWG, Qwiic / STEMMA QT compatible, USD 2.04 listing seen on pololu.com 2026-10-08).
  Review re-check of pololu.com/product/5521 (2026-10-08): 4-pin female JST SH-style (1 mm) on one end, other end
  unterminated, 30 cm, 28 AWG to UL 1571, black wire = pin 1, rated 1 A / 50 V, USD 2.04; stock was not confirmed
  (buy-check; fallback the same cable in 75 cm, Pololu #5522, cut down). Make 4 staggered solder joints by SH pin
  number after a continuity map (not by colour alone). Splice position: the cross run (`ko_lead_cross`) spans 68-115
  mm of the estimated route from the header end; the estimate counts the header end short (housing 15 mm plus the
  bend into `ko_lead_wall`), so physically it is about 76-123 mm from the socket tip. The 4 joints therefore sit
  83-107 mm from the socket tip (centre 95, 8 mm stagger), one thin-wall sleeve each, then one adhesive 3:1 sleeve
  about 35 mm long over all (77.5-112.5 mm: inside the straight run either way). Cut the 4397 so its wires end at those
  joints (socket end about 85-109 mm kept); cut the 5521 so the finished lead is 250 +/- 10 mm. The cross run is
  straight and does not flex after step 4; no rigid sleeve may sit in the wall-to-cross corner or the rise into
  `ko_qt_tail`. G-QT-1 dry-fits the finished lead before step 4 is closed out.

Alternatives considered.
- A one-piece STEMMA QT to female-socket lead longer than 150 mm: none found. Adafruit 4401 (200 mm) and 5384 (300 mm)
  have JST-SH on both ends. SparkFun CAB-14988 / CAB-17261 (female jumper) are 150 mm. Pololu 5523-5527 are SH-SH. Pimoroni's
  4-pin JST-SH cable (review search) offers the DuPont-socket end only at 150 mm (SH-SH at 50 / 200 / 500 mm).
  No inline SH-to-SH coupler was found. A passive QT hub does exist (Adafruit 5625, Qwiic / STEMMA QT 5 Port Hub; its
  guide calls it passive; it carries a power LED), so "4397 + 4401 + hub" is possible without solder, but it adds a
  board with no home and no mount, an always-on LED and two more SH joints in the panel path. Rejected. A generic
  one-piece "JST-SH 4P to 4 x 1-pin Dupont, 240-270 mm" is allowed as a user choice (s8) if it passes the buy-check.
- 4397 plus 4 male-female Dupont extension jumpers: 4 loose joints and about 165 mm spare. Rejected.
- Tilting the panel about its bottom edge (BLOCKERS interim): at 25 deg the encoder back clears the tub plane by only
  about 12 mm. Tweezers only, no pinch. Rejected as the design pose. It stays acceptable as a hand variant inside
  the checked reach.
- Rerouting to a shorter path (over the cooler, `ko_run_cross` side): about 112 mm plus ends. It saves less than
  20 mm and crosses `ko_fpc_loop` and the HDMI run. Rejected.

**Fix BX-10 with a housing rule, a corrected header proxy and a computed housing check.** 1-pin housings everywhere.
A 1x2 housing is allowed only where both of its contacts land on used pins: 37/39 (along the odd row) or 33/34 (across
the rows). Never a 1x3, 2x3 or any shell that covers an unused pin. Seat-and-pull wording goes into step 4 and s3.
`ko_run_leads` x0 -63.0 -> -64.5 so the pin-39 housing top lies inside a keep-out (probe: 0 mm3 of every printed part,
hood column included; `cable_routes` run_lead est 169.9 -> 171.1, slack 53.9; fps_lead est 132.3 -> 132.6, slack 47.4).

**Generalize with two new computed checks.** `mate_reach` covers every lead plugged with one end in a non-final pose:
reach (with the same allowance as `cable_routes`), a fingertip envelope with a stated orientation that must clear
every part present and lie outside the body opening (`out_of`), and the tail path. `cable_stow` checks that every
routed cable whose spare exceeds its allowance has a sized home, summed per stow box. In addition, mated plugs that
ride with a moving set join that insertion's sweep (the `mated` field), and a stow box filled during an insertion is
swept against that insertion's moving set (the `stowed` field).

## 3. Exact implementation

### 3.1 layout.py (receipt source: forces a full release rebuild)

New KEEPOUTS (section 7). All three hold 0 mm3 of tub, hood, panel, pi_keeper, lens_collar and plunger (STEP probe,
re-run in review), and 0 mm3 of the panel swept 70 -> 0 and of the hood column (hood_on). They overlap no COTS box
present at step 10 (`ko_qt_plug` is 0.05 mm off the encoder box). They overlap only their own route boxes and
`ko_hdmi_run` (1 mm in z, cable on cable). `ko_run_leads` changes x0 -63.0 -> -64.5 (BX-10, s2).

```python
# r7 (C2, BX-2): QT tail from the cross run up to the encoder's -X socket, the mated plug, and the spare-lead stow.
'ko_qt_tail': B(-84.0, -78.3, 14.0, 23.0, 43.0, 61.0),   # x max 0.5 off the encoder side cradle hook (x -77.8..-75.6, z 45..50)
'ko_qt_plug': B(-80.0, -75.7, 19.0, 24.6, 51.0, 61.0),   # JST-SH plug on the -X socket; z >= 51 clears the hook by 1.0;
                                                         # 0.05 off COTS['encoder'] box (end reach)
'ko_lead_stow': B(-108.0, -78.3, 21.0, 31.7, 43.0, 75.0),  # QT + 18/24 spare and PH junction: on the HDMI run (1 mm
                                                         # overlap joins it to fps_lead's route), under the panel face
                                                         # (32.2), between the 18/24 switch (x <= -110.5) and the hook
# r7 (C2, BX-10): pin-39 housing (x -63.83..-61.23) inside the header-end keep-out
'ko_run_leads': B(-64.5, -50.0, -31.7, -25.8, 28.8, 40.0),      # was x0 -63.0
```

New sub-dict next to `ENCODER` (cots.py `encoder()` reads it instead of its literals 9.5 / 2.15 / 19.6 / 3.0, so the
proxy and the mating data cannot drift apart), and a plug proxy:

```python
ENCODER['qt_socket'] = dict(dx=(-9.5, 9.5), w=4.3, y0=19.6, h=6.0, entry=(1, 0, 0),   # entry: plug travel, -X socket
                            note='proxy: side entry at the board edge assumed (MP-ENC photos, MP-QT)')
PLUG = {'jst_sh_4': dict(len=4.5, len_max=5.5)}     # SH plug body behind the socket face (design <= 5.5, MP-QT)
def qt_plug_point(i=0):   # wire exit W of the plug in socket i (0 = -X socket), final pose
    e, q = ENCODER, ENCODER['qt_socket']
    return (e['c'][0] + q['dx'][i] - q['w'] / 2 - PLUG['jst_sh_4']['len'], (q['y0'] + e['pcb']['y'][0]) / 2, e['c'][1])
#   = (-79.15, 21.85, 57.0) today
```

CABLES `qt` row:

```python
dict(id='qt', name='QT lead 250 mm: Adafruit 4397 (sockets) spliced to Pololu 5521 (JST-SH)', frm='encoder',
     to='GPIO 1/3/5/6', via=['ko_qt_lead', 'ko_lead_wall', 'ko_lead_link', 'ko_lead_cross', 'ko_qt_tail', 'ko_qt_plug'],
     length=250, length_range=(240, 270), stow='ko_lead_stow', od=3.2, steps=(4, 8)),
```

Add `od` (bundle envelope diameter, design value until MP-QT) to every cable that gets a `stow` box. `fps_lead`
gets `pigtail=50.0`, `stow='ko_lead_stow'`, `od=2.6` and `junction_mm3=576` (2-pin PH inline pair, design envelope
6 x 8 x 12 until MP-QT measures it). Its spare is 200 + 50 - 132.6 = 117.4 mm plus the junction, and it had no
modelled home (an earlier draft left it out of scope and sized the stow for the QT lead alone, 168 mm).

New constant next to `PI`:

```python
PI['header_rows_y'] = (PI['y'][0] + 3.5 - 1.27, PI['y'][0] + 3.5 + 1.27)   # even row (2, 4, ...), odd row (1, 3, ...)
#   RP mechanical drawing: header centreline 3.5 from the board edge (re-read RP-008347 before release)
```

COTS `pi5` features `gpio` becomes `B(PX1 - 58.0, PX1 - 7.0, PI['y'][0] + 0.96, PI['y'][0] + 6.04, 20.2, 28.6)`.
The pi5 outer `box` does not change (containment holds), but the pi5 COTS solid does: cots.py `pi5()` builds the
header block from this feature (cots.py:95-99), so the block moves 0.96 mm +Y and ends 0.71 mm off the cooler box.
Interference and sweeps run on that solid; the release rebuild confirms them (no new contact is expected: the block
stays inside the pi5 box and clear of the cooler).

New registry `HEADER_HOUSINGS` (proxy section 2.5-2.6 square, the check uses 2.6; seat z 22.6 = PCB top 20.1 + 2.5
header plastic; length 14.0-15.0, the check uses 15.0: class values, MP-QT gate):

```python
HDR_HOUSING = dict(pitch=2.54, sec=(2.5, 2.6), seat_z=PI['pcb_z'][1] + 2.5, length=(14.0, 15.0), min_gap=0.3)
HEADER_HOUSINGS = [   # (cable, housing type, pins); type in ('1', '1x2'); a 1x2 only on 2 used pins
    ('qt', '1', (1,)), ('qt', '1', (3,)), ('qt', '1', (5,)), ('qt', '1', (6,)),
    ('fps_lead', '1x2', (33, 34)),        # D2-25 2-way end: across the rows (or 2 x '1')
    ('run_lead', '1', (37,)), ('run_lead', '1', (39,)),   # or ('run_lead', '1x2', (37, 39)): C-3 floor hole passes 2.54 x 5.1
]
```

Pin n sits at x = header pin-1 x - 2.54 x ((n - 1) // 2), in the odd row if n is odd. Pin-1 x is the +X end of the
`gpio` box minus 1.27 (pin 1 at the button end, as `ko_qt_lead` x -21..-11 already implies). Confirm at MP-QT.

New registry `MATE_POSES`: one row per lead end plugged in a pose other than its final pose.

```python
MATE_MARGIN = 10.0      # plug body + strain-relief bend; the margin used is max(MATE_MARGIN, ROUTE_ALLOWANCE share of
                        # length_min), i.e. never less than the final-pose cable_routes allowance (24 mm at 240 mm)
HAND_ENVELOPES = {      # (a: length behind the plug rear along -axis, t: along `thick`, r: along `row`)
    'pinch_sh':   (30.0, 20.0, 24.0),   # JST-SH 1.0 pitch: index + thumb on the 6 mm sides, fingers' width along t
    'pinch_ph':   (35.0, 22.0, 26.0),   # JST-PH 2.0 inline pair (box centred on the window midpoint, a along the lead)
    'pinch_xt30': (40.0, 30.0, 30.0),
    'pinch_zif':  (25.0, 20.0, 30.0),   # FPC into a ZIF on a part held in the other hand
}
# Orientation matters: with t and r swapped the qt_enc box takes 990 mm3 of the panel (review probe). Every plug row
# names `row` (pin-row direction); `thick` = axis x row. out_of = (signed axis, plane, margin): the whole hand box
# must lie beyond plane + margin on that side (the hand works outside the body, not in the open tub).
# W / far given as a symbolic tuple are resolved by checks.py at check time from the L passed in
# (`_plug_point(L, ('qt_socket', i))` = the qt_plug_point formula on L.ENCODER / L.PLUG; ('switch_lugs',) from
# L.SWITCH_1824), so a moved encoder or switch moves the plug point in tests on deep-copied layout data too.
MATE_POSES = [
    dict(id='qt_enc', cable='qt', step=8, insertion='panel_on', disp=(0, 60.0, 0), end='encoder',
         W=('qt_socket', 0), axis=ENCODER['qt_socket']['entry'], row=(0, 0, 1), anchor='ko_lead_cross',
         hand='pinch_sh', mated='ko_qt_plug', out_of=('+y', YL, 0.0)),
    dict(id='fps_ph', cable='fps_lead', step=8, insertion='panel_on', disp=(0, 60.0, 0), end='switch_1824',
         far=('switch_lugs',),     # = (SWITCH_1824 c x, body a0, c z) = (-123.0, 19.2, 57.0)
         inline='pigtail', anchor='ko_fps_up', hand='pinch_ph', row=(0, 0, 1), junction_out=15.0,
         out_of=('+y', YL, 0.0)),
    dict(id='fpc_cam', cable='fpc', step=7, insertion='camera_in', disp=(-11.1, 60.0, 2.0), end='gs_camera',
         W=(cam_cover_rear(0.0) - 0.2, 0.0, 43.2), axis=(1, 0, 0), row=(0, 1, 0), anchor='ko_fpc_link',
         hand='pinch_zif', out_of=('+y', YL, 0.0)),
    dict(id='oled_flex', cable='oled_flex', step=6, insertion='evf_pair_in', both_moving=True),   # info row
    # C1 (BX-1) owns: add dict(id='hdmi_evf', ...) ONLY if the HDMI plug is still mated outside the body; if it is
    #   plugged in situ through the rail gap (C-6), no row (final pose).
    # C3 (BX-3) owns: dict(id='xt30', cable='pigtail', step=10, insertion='pack_in', disp=(0, 0, dz), end='xt30_pair',
    #   W=<XT30 female wire entry>, axis=(0, 0, -1), row=<XT30 long side>, anchor=<C3 tie point id>,
    #   hand='pinch_xt30', out_of=('-z', GRIP['bay']['z'][0], 15.0))
]
```

INSERTIONS: `panel_on` gets `mated=['ko_qt_plug']` (the plug rides with the panel set from the +60 mating pose) and
`stowed={'ko_lead_stow': 30.0}` (the spares are laid at 30 mm off; from there on the stow box is an obstacle for the
moving set). Its path becomes `[(0, 70.0, 0), (0, 60.0, 0), (0, 30.0, 0), (0, 0, 0)]`: no-op waypoints that make
the mating and stow poses explicit. Why `stowed` is needed: `check_sweeps` drops a cable's route boxes from
`active_ko` when one of its ends is in the moving set, so in `panel_on` (encoder and switch moving) neither the qt
nor the fps boxes are ever obstacles, and a future panel rib swept through the fold would go unseen. Review probe:
panel swept 70 -> 0 against the stow box 0 mm3; the encoder (x >= -75.65) and switch (x <= -110.5) boxes miss it.

STEPS text: step 4 and step 8 `action` (wording in s5).

### 3.2 checks.py

1. Factor the polyline out of `check_cable_routes` as `_route_polyline(L, via, end_point=None)`. It returns
   (length, points, last-box point). With `end_point=None` it gives exactly today's estimate (centre of the last box
   plus half of its largest dimension), so existing rows do not move. With a point, it ends at the point of the last
   box nearest to it (clamp) instead of adding the half.
2. `check_cable_routes`: one addition. If the cable has a plug point in `MATE_POSES` (`W`, or `far` for an inline
   row), the last route box must lie within ROUTE_END_TOL of it (not only of the end part's COTS box). Today the qt
   chain ends 13.1 mm from W, yet it passes the end-part test at 0.2 mm, because `COTS['encoder']` is the whole board
   envelope. The qt row now runs to `ko_qt_plug`, which contains W (distance 0; est 134.6, s7). fpc: W lies on the
   `ko_fpc_cam` face (0). fps_lead: `far` is 0.2 from `ko_fps_up`. Because W comes from `qt_plug_point()`, moving the
   encoder without moving `ko_qt_plug` now fails here.
3. New `check_mate_reach(L, rows=None)`, one row per `MATE_POSES` entry:
   - Pose: the `end` part (and its `insertion` moving set) displaced by `disp`. Fail if `disp` is not on the polyline
     of that insertion's `path` (tol 0.01). The motion after mating must be a swept motion.
   - `both_moving`: status `info` ("both ends ride in one moving set").
   - Margin: `m = max(MATE_MARGIN, ROUTE_ALLOWANCE[0], ROUTE_ALLOWANCE[1] * length_min)` (`length_min` =
     `length_range[0]` if given, else `length`). A pigtail uses `max(MATE_MARGIN, ...)` of its own length.
   - Plug rows: `fixed` = `_route_polyline(via[:via.index(anchor) + 1], end_point=W + disp)`. `tail` = distance from the
     anchor point to W + disp. `slack = length_min - fixed - tail - m`. Pass if slack >= 0.
   - Inline rows (`inline`): r1 = length_min - fixed - m (lead side). r2 = pigtail - m_pigtail. d = |anchor - (far +
     disp)|. The feasible window on the anchor-to-far segment is the set of points within r1 of the anchor and within
     r2 of far + disp. Pass if r1 + r2 >= d and the window midpoint lies at least `junction_out` beyond the opening
     plane (panel: y >= SPLIT + 15).
   - Hand (when `rows` with shapes is given; build_d2 passes the sweep manifolds): the box from
     `HAND_ENVELOPES[hand]` = (a, t, r) spans a behind the plug rear along -axis, t along `thick` = axis x row and r
     along `row`, centred on the plug centreline (inline rows: a along the segment, centred on the window midpoint).
     It is tested in the mating pose against every part present at that step, printed shapes and COTS boxes alike:
     fixed parts in the final pose, the moving set displaced by `disp`, minus the `end` part. Pass if every overlap
     <= 0.5 mm3 (the sweeps' tolerance) AND the `out_of` rule holds (the whole box beyond plane + margin on the signed
     side). The `out_of` rule is what fails a too-small offset: at +16.4 the qt box overlaps nothing (it dips into
     the open tub, which is empty there) but reaches y 28.25 < 35.0.
   - Tail path: a dia 3 cylinder from the anchor point to W + disp, tested against the same set. Pass if <= 0.5 mm3.
     If blocked: fail "tail path blocked by <part>". The author then adds a `tail_via` list of waypoints, measured as
     a polyline.
   - Row fields: id, cable, step, pose, length_min, fixed_mm, anchor_pt, tail_mm, margin, slack_mm, hand_box,
     hand_hits, out_of_mm, tail_hits, status, estimate=True.
4. New `check_cable_stow(L)`, one row per stow box:
   - Every routed cable is screened: `spare = length_max + pigtail - est_route` (`length_max` = `length_range[1]` or
     `length`; `est_route` = the final-pose `cable_routes` estimate; no allowance deducted, because a short real route
     leaves more lead to stow, not less). Cables with a `stow` field are checked below (qt 135.4, fps_lead 117.4 today).
     Every other routed cable gets an `info` row with its spare and the route box meant to absorb it (fpc 139.1 in the
     `ko_fpc_loop` S-fold by design; usb_5v 107.2; run_lead 78.9; hdmi 57.3 in `ko_hdmi_coil`; pigtail 93.7;
     pack_lead 32.0). Those are not failed in this round (no existing cable turns red); s6 lists them as follow-up.
   - Per stow box: `demand = sum(spare_i * pi/4 * od_i^2 + junction_mm3_i)` over the cables that name it;
     `capacity = STOW_FILL * vol(stow)` with `STOW_FILL = 0.25`. Pass if demand <= capacity, the box overlaps one route
     box of every cable that names it with a passage >= ROUTE_PASSAGE, it overlaps no COTS box present at step 10,
     and it is >= 2.0 from the blower footprint in plan (`COTS['cooler']['features']['blower']` x/y).
5. New `check_header_housings(L, rows)`: build each housing box from `HEADER_HOUSINGS` (section 2.6, length 15.0).
   Pass if: (a) each type is '1', or a '1x2' whose two pins are both used and adjacent (same row, 2.54 apart, or
   across the rows at the same x); (b) the gap to every COTS box present at step 10 other than pi5 is >= 0.3 (cooler
   0.68, x1203_kit 0.75 now); (c) the shape distance to every printed part present at step 10 is >= 0.3 (tub right wall
   1.13, hood 2.27 now); (d) the part above the pi5 box top lies inside the cable's header-end route box (`ko_qt_lead`
   for qt; `ko_run_leads` for fps_lead and run_lead; pin 39 needs the x0 -64.5 change); (e) the boxes do not overlap
   each other.
6. `check_sweeps`: (a) for each id in `ins.get('mated', [])`, add `dc.box_solid(L.KEEPOUTS[id])` as an extra moving
   solid from the mating waypoint on. Its own cable's route and stow boxes are ignored for it, and the end part is
   exempt. (b) for each `(box, from_mm)` in `ins.get('stowed', {})`, the box is an obstacle for every moving part at
   path points no further than `from_mm` from the final pose. (c) `active_ko` also takes each active cable's `stow`
   box. (d) the header housings join the obstacle list from step 5 on. The same `mated` mechanism serves C1's
   `ko_hdmi_evf` in `evf_pair_in`. If C1 adds an equivalent field, keep one implementation.

Probe results for these sweep changes (current geometry). Mated `ko_qt_plug` swept -Y 60 -> 0 against tub, hood,
pi_keeper, lens_collar, base_grip, plunger, stick_sleeve and cap: 0 mm3 each (designer). Review: the panel swept
70 -> 0 (1 mm steps) against `ko_qt_tail`, `ko_qt_plug` and the old stow box, and (2 mm steps) against the final
`ko_lead_stow` z 43..75: 0 mm3 each; the hood holds 0 mm3 in the whole footprint column under `ko_lead_stow` (z 0..75)
and under the `ko_run_leads` extension, so `hood_on` cannot sweep through them. `pi_in` passes through these boxes,
but qt is not active there: it is plugged later in step 4, and the rule is `min(steps) < step`.

### 3.3 build_d2.py, make_tables.py

- `R['mate_reach'] = CK.check_mate_reach(L, man_rows)`, `R['cable_stow'] = CK.check_cable_stow(L)` and
  `R['header_housings'] = CK.check_header_housings(L, rows)`. Add them to `order` after `cable_routes` and to
  `info_neutral` like `cable_routes`. This cluster adds 3 categories (28 -> 31 if no other cluster adds any).
- make_tables.py: a "Mating poses" table in ASSEMBLY.md s3 (id, step, pose, margin, fixed, tail, slack, hand, out_of,
  status) and in WIRING.md s7. A "Header housings" table in WIRING.md (pin, cable, type, gap to cooler, gap to wall).
  A "Lead stow" table in WIRING.md (stow box, cables, spare per cable, demand, capacity).

### 3.4 Electronics files

- `electronics/gs8-d2-v1/make_bom.py` (then regenerate bom.csv / BOM.md).
  - D2-24: "QT lead part 1: Adafruit 4397 STEMMA QT to female sockets, 150 mm (cut so the socket end is about 85-109
    mm, s2)", qty 1, layout_id qt.
  - New D2-24B: "QT lead part 2: Pololu #5521 JST SH-style 4-pin cable, single-ended female, 30 cm, 28 AWG (SH end
    kept; cut so the finished lead is 250 +/- 10 mm)", qty 1, Pololu, unit USD 2.04 (listing seen 2026-10-08, not a
    quote; stock not confirmed; fallback Pololu #5522, 75 cm), layout_id qt, note "splice W-QT; or the one-piece class
    lead of s8".
  - D2-46 note: add "QT splice: 4 thin-wall sleeves about 1.5 mm x 10 mm + 1 adhesive 3:1 about 4.8 mm x 35 mm".
  - D2-25 note: "spare and PH junction fold into ko_lead_stow at step 8 (cable_stow)".
- `harness-schedule.csv` qt row: name, length 250 (240-270), routing `ko_qt_lead ko_lead_wall ko_lead_link ko_lead_cross
  ko_qt_tail ko_qt_plug`, stow `ko_lead_stow`, note "splice in the straight run of ko_lead_cross (y -29..17), joints
  83-107 mm from the socket tip". fps_lead row: stow `ko_lead_stow`.
- WIRING.md: new splice entry W-QT (s5 splices, next to the diode and fuse splices). Table edits are in s5 below.

## 4. New computed checks and planted-fault regressions

| check | what it stops | pass criterion |
|---|---|---|
| `mate_reach` (new) | a lead whose free end cannot reach its socket in the pose where it is plugged, or with no room for the hand there | slack >= 0 after the margin max(10, 10 % of `length_min`); oriented hand envelope and tail path <= 0.5 mm3 against the printed parts and COTS boxes present; hand envelope wholly beyond the opening (`out_of`); pose on the insertion path |
| `cable_stow` (new) | spare length with no sized home, two leads claiming the same space, or a stow near the blower inlet | per stow box: sum of spare x section + junctions <= 0.25 x volume (spare at `length_range[1]`, no allowance deducted); joined to every naming cable's route; no COTS overlap; >= 2.0 from the blower footprint in plan; info rows for the other cables' spare |
| `header_housings` (new) | wide shells, or housings touching the cooler or the wall | types '1' / legal '1x2'; gap >= 0.3 to COTS boxes and printed parts present at step 10; top inside the header-end lead keep-out; no mutual overlap |
| `cable_routes` (plug-point rule) | an estimate that stops short of the plug, or a keep-out left behind when the part moves | the last box lies within ROUTE_END_TOL 1.0 of the plug point (`W` / `far`, resolved from the part data) as well as the end part; with `ko_qt_plug` the distance is 0 |
| `sweeps` (`mated`, `stowed` fields) | a mated plug that rides in with a moving set but is not swept (the BX-1 class); a panel feature that would crush the fold | mated keep-out boxes join the moving set from the mating waypoint; stow boxes become obstacles from the stow waypoint |

Add `test_r7_c2_mate_reach.py` in the style of `test_r3_regressions.py::test_cable_routes_real_layout_and_synthetic_faults`
(`copy.deepcopy` of layout data, pure Python unless noted):

1. Real layout: `check_mate_reach` rows qt_enc, fps_ph and fpc_cam pass, oled_flex is `info`. `check_cable_stow` and
   `check_header_housings` pass. `summarize(..., info_neutral=True)` is 'pass'.
2. Planted: qt `length=150, length_range=None` -> qt_enc fails, slack -45.8 (margin 15; the BX-2 defect itself).
3. Planted: qt_enc `disp=(0, 80.0, 0)` -> fail "mate pose not on the insertion path" (the path starts at +70).
4. Planted: qt `length_range=(240, 400)` -> `cable_stow` fails (demand 265.4 x 8.04 + 117.4 x 5.31 + 576 = 3334 mm3 >
   capacity 2542).
5. Planted: `ko_lead_stow` = B(-84.0, -44.0, -10.0, 3.0, 43.0, 75.0) (over the blower footprint; still joined to
   `ko_lead_cross`, free of COTS boxes, capacity 4160) -> `cable_stow` fails on the blower distance only. (The
   designer's "x -72..-42" plant stays at y 21..31.7, 17 mm from the blower in y, so it would not have failed.)
6. Planted (needs shapes; mark `slow`, run in build tests): a synthetic 10 mm cube placed in the qt_enc hand envelope at
   the mating pose, added to `rows` as a printed part present at step 8 -> hand fail naming it.
7. Planted: `HEADER_HOUSINGS` run_lead `('1x3', (35, 37, 39))` -> fail (unused pin 35, illegal type). Separately:
   COTS cooler y0 moved to -26.0 -> fail, gap 0.23 < 0.3.
8. Planted: qt via without `ko_qt_tail` and `ko_qt_plug` -> `cable_routes` fails on the plug-point rule (13.1 mm >
   1.0). The old end-part test alone would still pass at 0.2 mm, which is the BX-2 blind spot.
9. Planted (slow): `panel_on` `mated=['ko_qt_plug']` plus a synthetic obstacle box at x -80..-76, y 40..44, z 52..60
   -> `sweeps` fail. Without `mated` the same obstacle passes. This documents why the field exists.
10. Planted: qt_enc `disp=(0, 20.0, 0)` with the real 250 mm lead (on the path; slack 73.0 passes) -> fail on `out_of`
    (hand box y min 31.85 < 35.0). This is the BX-2 geometry with a long lead: reach alone would accept it.
11. Planted: `ko_run_leads` x0 back to -63.0 -> `header_housings` (d) fails on pin 39 (0.83 mm outside).
12. Planted: `ENCODER['c']` x -63.0 -> -58.0 -> `cable_routes` qt fails on the plug-point rule (W x -74.15, 1.55 mm
    from `ko_qt_plug`). Proves W is derived, not a stale literal.
13. Planted (slow): a synthetic moving printed part B(-100.0, -90.0, 15.0, 20.5, 50.0, 60.0) added to `panel_on`
    (final pose below the stow, so the final-pose `keepouts` check cannot see it; it crosses y 21..31.7 on the way
    in) -> `sweeps` fails on `ko_lead_stow` through `stowed`; without `stowed` it passes (the `active_ko`
    end-in-moving-set exemption).

## 5. Document changes

**layout.py STEPS, step 4 action**: replace "plug the header ends: QT lead on pins 1/3/5/6 ..." with:
"With the top open and the header in sight, plug the header ends, one housing at a time: QT lead (250 mm) on pins
1/3/5/6 (red on pin 1, 3V3), the 18/24 lead on 33/34 and the run lead on 37/39 (count from pin 1; a housing one row over
puts 5 V from pin 2 on the QT 3V3 wire). Seat each housing straight down with closed tweezer tips on its top until it stops on
the header plastic. Fingers do not fit beside them. Then tug each wire straight up gently: no housing may lift. Use
single 1-pin housings (a 1x2 only on 33/34 or 37/39); never a 1x3 or 2x3 shell. Run the QT and 18/24 leads along the
right wall and across behind the blower inlet (`ko_lead_wall`, `ko_lead_cross`), with the QT splice sleeve in the straight
part of the cross run, not in a corner; park their free ends out of the open left side."

**layout.py STEPS, step 8 action**: replace "Panel: hold it beside the body; plug the QT lead into the encoder
(JST-SH) and mate the 18/24 PH junction (header ends went on at step 4). Push the panel on along -Y" with:
"Panel: hold it about a hand's width (60 mm) off the body, inner face toward it. Pinch the QT plug and push it into the
encoder's rear-side socket (the one nearest the lead) until it latches. Mate the 18/24 PH junction in the air. (The
header ends went on at step 4.) Move the panel toward the body along -Y. At about 30 mm off, lay the spare QT lead
as a flat fold in the space between the encoder and the 18/24 switch, on top of the HDMI cable; lay the 18/24 spare
and its PH junction in the same space at the switch end; keep both away from the blower. Then push the panel on (tongue into the hood groove ...". [Plan edit P2-3: replaced by "keep the body upright until the panel is fully home"; the
SPEC-C5 hood-down screw pose follows, with the fold closed in by the panel as in use. Merged text: PLAN.md s4.]

**ASSEMBLY.md** (generated by make_tables.py from STEPS; hand-written parts):
- s3 check after step 4: "Header: 8 contacts on pins 1, 3, 5, 6, 33, 34, 37, 39; single housings (or 1x2 on 33/34,
  37/39); all housing tops level; each wire tugged."
- s3 check after step 8: "Before the last 30 mm of panel travel the QT fold, the 18/24 spare and the PH junction lie
  between encoder and switch on the HDMI run; nothing over the blower inlet; the panel closes without pressure."
- s3: the new "Mating poses" table (generated).
- s7 item 4 (panel off): "Pull the panel straight out about 60 mm (the QT fold, the 18/24 spare and the PH junction come
  out with it). Pinch the QT plug
  (not the wire) to unplug it at the encoder. Part the 18/24 PH junction."
- Harness table row for step 8 (line ~223): "QT lead -> encoder JST-SH, panel held 60 mm off (mating pose `qt_enc`);
  QT spare, 18/24 spare and PH junction into `ko_lead_stow`".

**WIRING.md**: s6 cable table qt row (line ~340): "QT lead 250 mm (240-270): Adafruit 4397 sockets + Pololu 5521 SH,
spliced (W-QT)", length 250, routing plus `ko_qt_tail`, `ko_qt_plug`, stow `ko_lead_stow`. s7 step table: line ~369
gains "seat with closed tweezer tips; tug-test; 1-pin housings"; line ~377 "panel held 60 mm off; fold the spare into
ko_lead_stow; the 18/24 spare and PH junction too". New W-QT splice text: "Map continuity first (4397: SH pin 1 GND
black, 2 3V3 red, 3 SDA blue, 4 SCL yellow; Pololu 5521: black is pin 1, the other three by meter). Join by SH pin
number, never by colour alone. Joints 83-107 mm from the socket tip, 8 mm apart, one thin-wall sleeve each, one
adhesive 3:1 sleeve about 35 mm over all; no joint or sleeve outside 77-113 mm. Finished length 250 +/- 10, socket tip
to SH plug face."
New tables "Header housings" and "Lead stow" (generated).

**BOM.md / bom.csv**: from make_bom.py (s3.4). BOM.md notes: one line "QT lead is spliced (W-QT); a one-piece 240-270
mm lead of the same ends may replace D2-24 + D2-24B (buy-check MP-QT)".

**MEASURED-PARTS.md**: new record **MP-QT: QT lead and header housings** (add MP-QT to the summary id list).
- Measure: finished lead length (240-270); SH plug body length (CAD 4.5, design <= 5.5); bundle envelope OD (CAD 3.2,
  design <= 3.2, or re-run `cable_stow`); Dupont housing section (<= 2.6) and length (14-15); header row offsets
  from the Pi board edge (CAD 2.23 / 4.77, centreline 3.5); which way the 5880 QT sockets open (CAD: +X entry at the
  board's -X edge); the 18/24 lead bundle (design OD 2.6) and the PH inline junction envelope (design 6 x 8 x 12).
- Gate **G-QT-1** (bench, panel coupon or first print): dry-fit the finished lead at step 4 (splice sleeve wholly in the
  straight cross run); with the panel held 60 mm off, plug and unplug the QT 5 times by pinch; fold both spares and the
  PH junction and close the panel 3 times; no pull on the plug when closed (it still sits fully latched).
- Gate **G-HDR-1**: all 8 housings seat level with daylight to the cooler shroud and the wall (>= 0.3 feeler, or
  visible gap); tug test; continuity map of the splice; `i2cdetect` sees 0x37 at the configured bus speed and the
  encoder reads clean for 10 min (the 250 mm lead is within Adafruit's own 300 mm warning; it joins G-W9).
- If it fails: socket opening along -Y instead of X -> update `ENCODER` QT boxes and `MATE_POSES` W/axis, re-run.
  OD > 3.2 or junction > 6 x 8 x 12 -> re-run `cable_stow`; `ko_lead_stow` is bounded by the switch (x -110.5), the
  cradle hook (x -77.8) and the panel face (y 32.2); above z 75 is unprobed (probe before enlarging), or shorten within
  the range.

MP-ENC "Photos" adds: "the QT socket opening direction".

**guide/guide_steps.py**:
- ISSUES `'8b'` BX-2 entry: delete it once `mate_reach` passes in the receipt. TIPS `'8b'` gains: "Hold the panel a
  hand's width off. Pinch the QT plug in. Fold both spare leads and the small junction between the dial and the switch before the panel closes."
- TIPS `'4d'` BX-10: keep as a tip, reworded: "Seat each socket straight down with closed tweezer tips on its top, then
  tug each wire. Single sockets only (a 2-way only on 33/34 or 37/39)." BX-10 is already a TIP, not an ISSUE;
  drop the "BX-10:" prefix once `header_housings` passes.
- The step-4 parts panel shows the 250 mm QT lead with its splice sleeve; the step-8 picture shows the 60 mm mating pose.

## 6. Interactions and risks

| area | effect |
|---|---|
| EVF restraint, thin walls, critical features, print_overhang, bed fit, j7_float, driver / service_driver | No printed geometry changes and no screw changes, so these are unaffected. The new boxes lie on no screw line (s_b1/s_b2 from below, s_r1/s_r2 from the right are elsewhere). |
| keepouts | +3 boxes and `ko_run_leads` x0 -64.5, all 0 mm3 printed overlap (probe). `ko_qt_tail` and `ko_lead_stow` are 0.5 mm off the encoder side cradle hook, and `ko_lead_stow` 0.5 mm under the panel inner face. Any later panel feature near the encoder or between encoder and switch must stay out of them (`stowed` sweeps it too). |
| sweeps | `panel_on` gains one moving box (`mated`, 0 mm3 probe) and one stow obstacle (`stowed`, 0 mm3); `hood_on` sees the new boxes (hood column 0 mm3). Box-level sweeps of every other insertion miss them, except `pi_in`, where qt is not active yet. |
| cable_routes | qt: est 117.6 -> 134.6, slack 17.4 -> 90.4 (now the stowed spare). run_lead 169.9 -> 171.1 (slack 53.9) and fps_lead 132.3 -> 132.6 (slack 47.4) from the `ko_run_leads` change. The other rows do not change (the helper refactor is exact). |
| mass / CoM | `mass_com` excludes cables ("cables and solder not included"), so nothing changes. The lead weighs a few grams more (not measured). |
| COTS proxy `gpio` | Moved 0.96 mm inboard. The pi5 outer box does not change, so containment does not move; the pi5 solid's header block moves with it (0.71 off the cooler; re-checked by interference in the rebuild). If RP-008347 gives another centreline, the housing gaps change and the check reports them. |
| C1 (BX-1, HDMI) | Shares the `mated` sweep field and owns an `hdmi_evf` row if the plug is still mated outside. Numbers from the current geometry at the `evf_pair_in` start (+45 Y): HDMI slack 17.3 mm if the coil is laid first (anchor `ko_hdmi_coil`), 37.9 mm if the coil is left loose (anchor `ko_panel_link`). USB 5 V to the board 52.7 mm (the PH junction is mated in situ today, so no row is needed). Those slacks used a 10 mm margin; under the final margin rule (max(10, 10 %), 20 mm for a 200 mm lead) they are 7.3 / 27.9 / 42.7. |
| C3 (BX-3, XT30) | Owns the tie point, the pigtail length and the `xt30` row. Generic number: anchor at the bottom of `ko_pig_drop`, no tie detour, XT30 top 15 mm below the grip mouth (z -125), 180 mm pigtail: slack 2.2 mm after a 10 mm margin, so -5.8 mm under the final margin rule (18 mm for 180 mm): C3 must lengthen the pigtail (at least about 187 mm plus any tie detour, with the final margin at the new length) or raise the mating pose. Any tie detour fails 180 mm, which is consistent with BX-3. |
| BX-5 cluster (knob at step 2) | The knobs join the `panel_on` set outside the panel (+Y). The hand envelope sits on the -Y side, so there is no effect. A printed encoder backer, if added, must keep out of the three new boxes. |
| BX-13 (body upright) | The fold relies on the body being upright from step 8 on, and BX-13 already asks for that. |
| other leads' spare (follow-up, not this round) | `cable_stow` info rows: fpc 139.1 (in the `ko_fpc_loop` S-fold by design), usb_5v 107.2, pigtail 93.7, run_lead 78.9, hdmi 57.3 (`ko_hdmi_coil`), pack_lead 32.0 mm. usb_5v and run_lead have no named home for their spare: a later round should give them `stow` boxes and make the screen a fail for every routed cable. |

Risks.
- The socket opening direction is a proxy assumption (+X entry at the board's -X edge). If the real 5880 sockets open
  along -Y, W moves by less than 5 mm and the hand envelope moves to the -Y side. Re-run; gate MP-QT / MP-ENC photos.
- 4 solder joints in 28 AWG: a wrong colour pair puts 3V3 on SDA. Mitigation: continuity map before soldering (W-QT)
  and G-HDR-1.
- I2C over 250 mm: within Adafruit's warning range for 300 mm at 400 kHz. G-HDR-1 runs the encoder at the configured
  speed for 10 min.
- The fold may spring out while the panel closes. G-QT-1 closes the panel 3 times. The shared stow is at 90 % of its
  25 %-fill capacity (2288 of 2542 mm3 bundle volume, worst-case lengths): enough on paper, but the junction envelope
  and both ODs are design values (MP-QT).
- The hand envelope is a box, not a hand. At +60 it clears the panel inner face by only 0.35 mm, and the fps_ph box
  clears the body face by 0.88 mm. G-QT-1 is the real confirmation.
- The splice position relies on the route estimate (header end counted short by about 8 mm); G-QT-1 dry-fits it.
- Pololu 5521 stock was not confirmed (product page listed; a category snippet showed an out-of-stock note that may
  belong to a neighbour). Fallback Pololu 5522 (75 cm) cut down, or the s8 one-piece lead.

## 7. Acceptance criteria

Computed. All numbers are estimates from the current geometry (review probes re-ran each one). All existing
categories still pass; this cluster adds 3 (28 -> 31 if no other cluster adds any).

| check / row | must hold | value now (probe) |
|---|---|---|
| cable_routes qt | pass, end_gap <= 1.0, plug-point distance <= 1.0 | est 134.6, allowance 25.0, slack 90.4 (L 250), end_gap 0.05, plug point 0 |
| cable_routes run_lead / fps_lead | pass | est 171.1 / 132.6, slack 53.9 / 47.4 (`ko_run_leads` x0 -64.5) |
| mate_reach qt_enc (+60) | slack >= 0 at L 240; hand and tail <= 0.5 mm3; out_of | fixed 117.6, tail 63.2, margin 24, slack 35.2; hand box x -109.15..-79.15, y 71.85..91.85, z 45..69: 0 mm3 (panel +60 clear by 0.35); out_of +36.85; tail path 0 mm3 |
| mate_reach fps_ph (+60) | r1 + r2 >= d; window midpoint >= SPLIT + 15; hand; out_of | fixed 131.4, r1 48.6 (margin 20) + r2 40.0 >= d 60.2; window y 39.2..67.6, midpoint 53.4 = SPLIT + 21.2; hand x -134..-112, y 35.9..70.9, z 44..70: 0 mm3; out_of +0.88 |
| mate_reach fpc_cam (camera_in start) | slack >= 0; hand; out_of | fixed 30.3, tail 41.4, margin 20, slack 108.2; tail path 0 mm3; hand x -60.1..-35.1, y 45..75, z 35.2..55.2: 0 mm3; out_of +10 |
| mate_reach oled_flex | info | both ends in `evf_pair_in` |
| cable_stow ko_lead_stow | demand <= capacity; joined; no COTS; blower >= 2.0 | qt 135.4 mm x 8.04 + fps 117.4 mm x 5.31 + junction 576 = 2288 mm3 <= 0.25 x 10169 = 2542; joined to `ko_qt_tail` and `ko_hdmi_run`; no COTS overlap; 17.9 from the blower footprint in plan |
| header_housings | gaps >= 0.3, legal types, (d) containment | cooler 0.68, x1203_kit 0.75, tub wall 1.13, hood 2.27; 4 + 1 + 2 housings; pin 39 inside the widened `ko_run_leads` |
| keepouts (3 new boxes, `ko_run_leads`) | 0 printed overlap | 0 mm3 tub, hood, panel, pi_keeper, lens_collar, plunger |
| sweeps panel_on with `mated` and `stowed` | pass | `ko_qt_plug` swept 60 -> 0: 0 mm3; panel swept 70 -> 0 vs `ko_lead_stow`: 0 mm3 |
| regressions | s4 cases 1-13 pass | to write |

Physical gates. MP-QT (lead length, plug, OD, housings, socket direction, 18/24 OD and PH junction), G-QT-1 (splice
dry-fit, pinch mating at 60 mm, fold both spares and close x3), G-HDR-1 (seating gaps, tug test, continuity, I2C soak). MP-ENC photos (socket direction).

## 8. User decisions

1. Optional, sourcing: buy a one-piece generic "JST-SH 1.0 4-pin (Qwiic order) to 4 x 1-pin 2.54 female Dupont,
   240-270 mm" lead instead of splicing D2-24 (Adafruit 4397) + D2-24B (Pololu 5521). No vendor or part number for it
   was confirmed. It saves the splice but needs the MP-QT buy-check (length, 1-pin housings, wire order, latch). The
   default is the splice (about USD 2 extra, no new tool: the build already has solder splices). Nothing else needs
   a user decision.

## 9. Effort and receipt sources

| work | hours |
|---|---|
| layout.py: 3 KEEPOUTS + `ko_run_leads`, qt / fps_lead rows, PI header rows, gpio proxy, ENCODER qt_socket / PLUG / qt_plug_point (+ cots.py encoder() reads it), HDR_HOUSING / HEADER_HOUSINGS, MATE_POSES, panel_on `mated` / `stowed` + waypoints, STEPS 4 and 8 | 1.25 |
| checks.py: `_route_polyline` refactor, `_plug_point`, `check_mate_reach` (margin rule, oriented hand box, out_of), `check_cable_stow` (per-box demand, screen), `check_header_housings`, sweeps `mated` / `stowed` / stow | 2.75 |
| build_d2.py registration, make_tables.py tables | 0.75 |
| test_r7_c2_mate_reach.py (13 cases, 3 slow) | 1.25 |
| make_bom.py, bom.csv, BOM.md, harness-schedule.csv, WIRING.md | 0.75 |
| ASSEMBLY.md s3 / s7, MEASURED-PARTS MP-QT, guide_steps.py | 0.75 |
| full release rebuild (run_locked) + receipt review | 1.0 |
| **total** | **about 8.5** |

Receipt sources touched: `layout.py`, `checks.py` and `cots.py` (`encoder()` reads `ENCODER['qt_socket']`, same
geometry; `pi5()` header block follows the corrected feature) (all force a full release rebuild through `run_locked.py`),
`build_d2.py` and `make_tables.py` (the generated tables in ASSEMBLY.md / DESIGN.md / WIRING.md). Outside the CAD
receipt: `electronics/gs8-d2-v1/make_bom.py` -> bom.csv / BOM.md. No printed part's STL changes. The gpio proxy and
the keep-outs change only COTS proxies and check data, so print readiness (PRINT_PREREQS) is not affected.

## 10. Review notes (adversarial review, 2026-10-08 23:05-23:35 MPST)

Verdict: the designer's fix does remove the BX-2 problem in the current geometry (a 240-270 mm lead reaches the
encoder with the panel 60 mm off, and nothing is in the way), and BX-10 is handled. The spec was not ready to
implement as written: the hand check could not catch the BX-2 pose, the stow ignored the 18/24 spare, one planted
test could not fail, and one housing check would have failed on the real layout. All are corrected above.

Verified by own probes (scratchpad `r7/C2-review/`, layout imported, part STEP files of the 16:05 build):
- Route numbers reproduce exactly: old qt est 117.6; new est 134.6; fixed to the cross-run anchor 117.6; tail 13.1
  (final) / 63.2 (+60); 150 mm at +60: -40.8 at a 10 mm margin (-45.8 at the final margin); 240 mm: 49.2 / 35.2.
- The three new boxes: 0 mm3 of tub, hood, panel, pi_keeper, lens_collar and plunger; no COTS overlap (`ko_qt_plug`
  0.05 off the encoder box); panel swept 70 -> 0 against each: 0 mm3.
- qt_enc hand box 0 mm3 in the stated orientation, 990 mm3 of panel with thickness and pin row swapped; tail
  cylinder 0 mm3; fps_ph and fpc_cam hand boxes 0 mm3 (not computed in the draft); fpc tail 0 mm3.
- Header housings (section 2.6): tub wall 1.13, cooler 0.68, x1203_kit 0.75, hood >= 2.27.
- Pololu #5521 confirmed on pololu.com (4-pin female SH-style one end, unterminated, 30 cm, 28 AWG, black = pin 1,
  USD 2.04; stock not confirmed). Adafruit 5625 passive QT hub exists (the draft said no coupler was found).
  Pimoroni: female-socket version 150 mm only.

Changed:
1. `mate_reach` hand test: added `row` (orientation; the result flips with it) and the `out_of` rule. Without it the
   hand box at the BX-2 pose (+16.4) overlaps nothing (it dips into the empty open tub), so a long lead plus a
   too-small offset would pass. New test 10.
2. Margin: max(10, 10 % of length_min), never below the `cable_routes` allowance (qt slack 35.2, fpc 108.2, fps
   r1 48.6). Consequence flagged for C3: the generic xt30 number goes from +2.2 to -5.8 mm at 180 mm.
3. Plug points derived, not literals: `ENCODER['qt_socket']`, `PLUG`, `qt_plug_point()`, symbolic W / far resolved
   in checks. cots.py `encoder()` reads the same data. New test 12 (moved encoder fails the plug-point rule).
4. Stow: `ko_qt_stow` (z 45..62, 5402 mm3) became the shared `ko_lead_stow` (z 43..75, 10169 mm3, probed clear).
   The 18/24 lead's spare (117.4 mm + PH junction) had no home and would land in the same space. `cable_stow` now
   sums demand per stow box, uses spare without deducting the allowance (worst case 135.4, not 108.4), checks COTS
   overlap, and lists every other cable's spare as info (usb_5v and run_lead flagged as follow-up).
5. Planted test 5 could not fail (the draft's x -72..-42 plant stays 17 mm from the blower in y); replaced. Test 2
   / 4 / 7 numbers corrected (-45.8; demand 3334 > 2542; gap 0.23, not -0.25). Tests 10-13 added.
6. Sweeps: `stowed` field added. `check_sweeps` drops qt and fps boxes in `panel_on` because their ends move, so
   the draft's "stow box in active_ko" never applied in the one insertion where the fold is laid. New test 13.
7. BX-10: pin-39 housing reaches x -63.83, outside `ko_run_leads` (x0 -63.0), so check (d) would have failed:
   `ko_run_leads` x0 -> -64.5 (probed clear; run_lead / fps_lead slack 53.9 / 47.4). (d) now names the header-end
   box (for run_lead it is the last box, not the first). Gaps restated for the 2.6 section the check uses; (b)/(c)
   now test everything present at step 10, not only step 4.
8. Splice position fixed to the straight cross run (joints 83-107 mm from the socket tip, sleeve about 35 mm) with
   the estimate's short header end allowed for; join by SH pin number; G-QT-1 dry-fits it.
9. gpio proxy: the draft said interference would not move; cots.py `pi5()` builds the header block from the feature,
   so the pi5 solid changes (0.71 off the cooler). Stated, left to the release rebuild. cots.py added to the receipt
   sources.
10. Smaller: "off-by-one" pin wording, step 8 / s3 / s7 / WIRING / MEASURED-PARTS / guide wording for the shared
    fold, Pololu 5522 fallback, D2-46 sleeve sizes, effort 7.75 -> 8.5 h.

Not changed (checked, holds): the 60 mm pose lies on the `panel_on` path; no screw, printed part, j7_float or
lens-handling change; power-last holds (bench splice, plug at step 8 with the pack out); the I2C length and socket
direction risks and their gates; the s8 user decision.

Not verified: the real 5880 socket direction and SH plug length; the real header centreline (RP-008347); the
generic one-piece lead (no vendor); a hand model beyond the fingertip box (G-QT-1); hood_on swept as a mesh (column
test only).

## Plan edits (integration, 2026-10-09 00:00-01:00 MPST; PLAN.md wins where it and this spec differ)

Plan edits: P2-1 The INSERTIONS `mated` field (3.1, 3.2-6a) is dropped. Mated plugs that ride with a moving set
come from SPEC-C1's PLUGS registry (one carried-box routine; `p_qt_enc` mated ('before', 'panel_on') is carried
along the whole `panel_on` path, which is stricter than "from the +60 waypoint"). Each MATE_POSES row gains
`plug=<PLUGS id>` (or `inline_of=<cable>` for the fps PH junction); the `mated='ko_qt_plug'` key goes. Test 9 becomes:
synthetic obstacle B(-80, -76, 40, 44, 52, 60) with PLUGS `p_qt_enc` mated ('before', 'panel_on') -> sweeps fail;
with `p_qt_enc` mated ('after', 'panel_on') -> pass. `stowed`, stow boxes in active_ko and the header housings as
obstacles from step 5 stay, implemented inside the same routine (PLAN.md s2).
Plan edits: P2-2 `ko_qt_plug` is C2's box (SPEC-C1 adopts it, KEEPOUT_KIND 'plug').
Plan edits: P2-3 Step 8: the sentence "Keep the body upright from here on: the fold rests on the HDMI run by
gravity" is replaced by "keep the body upright until the panel is fully home". Once the panel is home the fold is
closed in by the panel face, as in use, so SPEC-C5's hood-down screw pose that follows is allowed. The merged
step-8 text is in PLAN.md s4. The s6 row "BX-13 (body upright)" is void. The QT pinch sentence gains "with a
fingertip backing the encoder board" (handed over by SPEC-C5).
Plan edits: P2-4 MATE_POSES gains SPEC-C1's `usb_5v_evf` row (the EVF PH junction is now mated outside before the
slide) and SPEC-C3's `xt30` row as a REQUIRED row (C2 lands first). The xt30 row uses the PIGTAIL reach model
(`reach='pigtail'`: slack = `_pigtail_face_out(L)` - face_out_min, the same helper as lead_access
`pigtail_xt30_mouth`), so one length model gives one number; mate_reach adds the pose-on-path, hand, tail and
out_of rows. Its out_of is ('-z', GRIP['bay']['z'][0], 15.0). The `hdmi_evf` row is not added (in-situ mate).
Plan edits: P2-5 Margin helper `reach_margin(L, length)` (max(MATE_MARGIN, ROUTE_ALLOWANCE[0],
ROUTE_ALLOWANCE[1] x length)) is shared by mate_reach and lead_access; with ROUTE_ALLOWANCE (10.0, 0.10) it equals
C3's allowance(L), so C3 is not weakened.
Plan edits: P2-6 `cable_stow` info row for fpc names SPEC-C4's `cable_routes` fpc fold row as the home check.
All BOM edits go into make_bom.py `LINES` (bom.csv and BOM.md are generated). Receipt: cots.py is a receipt
source; the pi5 COTS STEP changes (gpio block), the encoder STEP must stay identical. Category count is computed.
