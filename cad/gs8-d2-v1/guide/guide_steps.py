# SPDX-License-Identifier: MIT
"""GS8 D2 assembly guide: the step script (all page text). Paraphrases cad/gs8-d2-v1/ASSEMBLY.md (r6) and
electronics/gs8-d2-v1/WIRING.md s5-s7; where they differ, ASSEMBLY.md and WIRING.md win.

Step fields: id, title, sub, step (layout.STEPS number, or None for bench pages), ctx (layout step whose present_at()
is the body already built; None = no body), plus (extra installed ids), minus (installed ids hidden), new (ids added
on this page, drawn at the start of their insertion path), still (added ids drawn in place), view (azimuth, elevation of
the camera direction; X forward, Y left, Z up), zoom, explode (factor on the insertion offset), marks [(id or point,
label)], diagram (diagrams.DIAGRAMS key, replaces the render), parts, hw, tools, torque, do, caution, check.
"""

TOOLS = [
    (1, 'PH1 screwdriver, straight (shank dia 6.5 or less, blade 40 mm or longer, handle dia 28-30)', 'D2-60'),
    (2, 'Temperature-controlled soldering iron + solder, flux, wick; M3 heat-set tip', 'D2-63, D2-47, D2-74'),
    (3, 'Wire stripper + flush cutter', 'D2-68'),
    (4, 'Heat gun (adhesive heat-shrink)', 'D2-68'),
    (5, 'Multimeter (continuity, diode test, no-short checks)', 'D2-64'),
    (6, '12.7 mm (1/2 in) socket or spanner (18/24 switch nut)', 'D2-61'),
    (7, 'Junior hacksaw + small flat file + caliper with depth rod + soft-jaw vise (cut the switch shaft off the panel)',
     'D2-69'),
    (8, 'Fine tweezers, 120 mm', 'D2-62'),
    (9, '2 hood release pins, dia 1.5 steel, 16 mm or longer (service only)', 'D2-71'),
    (10, 'Flat bar or steel rule (press the tripod nut; upright HDMI push stick at 6c)', '-'),
    (11, 'Paint pen (engraving fill, adapter mark)', 'D2-44'),
    (12, 'ESD mat + wrist strap', 'D2-70'),
    (13, 'Adjustable torque screwdriver 0.1-0.6 N m, straight, PH1 bit', 'D2-77'),
    (14, 'Collar centring gauge, printed, one per lens (stl/tools/collar_gauge.stl)', 'printed'),
    # r7 (PLAN X-9): fixed numbers; 18 belongs to another r7 cluster and is added only when it lands
    (15, 'Smooth-jaw long-nose pliers, jaws 35 mm or longer, tips 2.0 mm thick or less (EVF HDMI unplug, service)', '-'),
    (16, 'Printer paper, 2 strips (about 0.2 mm together: knob stop shim)', '-'),
    (17, 'Inspection mirror, head 15 mm or less (optional: see the EVF HDMI seat)', '-'),
]

RULES = [
    ('Power last', 'The battery pack goes in only at step 10, after the body is closed. Every lead in steps 1-9 is '
     'made with the pack out of the camera. Never plug or unplug an internal lead with the pack connected.'),
    ('Straight driver only', 'Every screw is driven with a straight PH1 driver along its own axis. No L-keys, hex keys, '
     'angled or ball-end drivers. One bench exception: the camera tripod block screws at B0, if they turn out to be hex.'),
    ('Torque', 'PT screws (plastic, thread-forming): 0.35-0.5 N m, stop at head contact; no threadlocker; do not '
     're-torque. Lens collar M3: s_c1, s_c2, s_c3 0.15 N m, s_c4 0.2 N m, always on the torque screwdriver (tool 13).'),
    # r7 C4 (BX-4): nobody holds the camera; the hood tab catch reacts the thread through metal (roll_catch)
    ('Lens rule', 'Never thread the lens into an unsupported camera. Nobody holds the camera: one fingertip pushes the '
     'cover centre forward (push only), and the hood tab catch holds the camera through its metal lock tab while the '
     'lens turns. Never grip, pinch or turn the cover or the circuit board. Check both paint marks at every lens '
     'change.'),
    ('ESD', 'Grounded mat and wrist strap for steps 1, 4, 6, 7 and bench step B0 (bare boards, OLED flex, camera).'),
    ('Re-assembly', 'At most 5 drives per plastic boss. Tally every drive on the build sheet; after 5, use the M3 insert '
     'fallback (FASTENER-POLICY D-E).'),
    ('Not yet built', 'Nobody has assembled a D2. These steps are checked by computed insertion sweeps and the '
     'straight-driver audit only. Stop and report if a part does not go where the picture shows.'),
]

GATES = [
    'WIRING G-W1 to G-W7: pack, X1203 identity, Pi on the bench supply, stack with a pack supply (G-W4) and under load '
    '(G-W5), EVF feed (G-W6), HDMI pin 19 (G-W7).',
    'G-W13 only if EVF-feed option C is adopted (WIRING s4.8).',
    'SPEC G-CAM-1 and G-LENS: the measured camera and lens (MEASURED-PARTS MP-CAM with its lens line) before any '
    'lens collar, tub, hood or panel is printed. r7: G-CAM-1 also records the lock-screw head side and size, which set '
    'the hood tab catch.',
    'Bench (r7): G-W2 sets the pigtail cut length (pads-to-W, page 1a; more than 25 mm pads-to-W: stop, do not cut); '
    'G-MP-PACK measures the rigid solder-cup and heat-shrink length at each XT30 end (0.8 mm allowed) and adds a '
    '10-cycle check of the folded pigtail above the pack (page 10a).',
    'Collar coupons G-COL-1, the print coupons (PRINT-GUIDE s6) and the measured-part records MP-PACK, MP-X1203, '
    'MP-CAM, MP-HDMI and the MP-EVF bench assembly.',
    'Open design item M1 (collar clamp spring and its thermal term) is to be fixed before the lens collar is printed.',
    'Before any claim that the powered camera works: WIRING G-W12 (full-workload power test).',
    'First print (r7): G-EVF-3, five in-body EVF HDMI mate/unmate cycles through the rail gap (page 6c, tools 10 and 15).',
    'First print (r7): G-QT-1 and G-HDR-1 (MEASURED-PARTS MP-QT): QT lead dry fit, 5 plug cycles with the panel 60 mm '
    'off (page 8b), 8 header housings level with a visible gap to the cooler and the wall (page 4d).',
]

BAGS = [
    ('A', 'PT 3.0 x 12 thread-forming screw for plastics, pan head, PH1 (EJOT PT K30x12 class)', 7,
     's_j (step 3), s_k1, s_k2 (step 4), s_b1, s_b2, s_r1, s_r2 (step 8c)'),
    ('B', 'M3 x 10 PH1 machine screw + flat washer', 3, 's_c1, s_c2, s_c3 (step 7a)'),
    ('C', 'M3 x 16 PH1 machine screw + flat washer', 1, 's_c4 (step 8a)'),
    ('D', 'M3 brass heat-set insert, short (D2-35)', 3, 'tub front wall TL, TR, LL (B1)'),
    ('E', 'M3 brass heat-set insert, L 5.7 (D2-36)', 1, 'lens collar lower lug (B1)'),
    ('F', 'X1203 kit: 4 standoffs + 8 M2.5 screws', 1, 'stack (step 1); if the kit screws are hex, M2.5 x 5 ISO 7045 PH1'),
    ('G', '1/4-20 UNC hex nut, steel', 1, 'tripod nut (step 3a)'),
]

STEPS = [
    # ------------------------------------------------------------------ bench: camera, inserts
    dict(id='B0', title='Camera and lens on the bench', sub='Bench, before any body part is printed (MP-CAM, G-CAM-1, G-LENS)',
         ctx=None, plus=[], new=['gs_camera', 'c_cs_adapter', 'lens'],
         offsets={'c_cs_adapter': (32, 0, 0), 'lens': (95, 0, 0)}, view=(30, 20), zoom=1.0, arrows=False,
         parts=['Raspberry Pi Global Shutter camera', 'C-CS adapter ring 5 mm', 'C-mount lens (Kowa LM6HC)'],
         tools=[11, 12, 5], torque=None,
         do=['Measure and photograph the camera and lens as MEASURED-PARTS MP-CAM asks. Record the C-flange-to-cover-rear '
             'distance at s = 0 and at the final s.',
             'Keep the tripod block on and clamp the camera to a bench tripod. Support the lens barrel in a padded V-block. '
             'Never let the lens hang on the camera alone.',
             'Seat the C-CS adapter firmly in the back-focus ring (BFAR). Draw one paint-pen line across adapter and BFAR.',
             'With the official Pi supply and an external monitor, set back focus with the lens at infinity (target more '
             'than 50 m away). Lock the BFAR split-tab screw. Record s; it must lie between 0 and 3.0.',
             'Remove the lens while the camera stays supported. Only then remove the tripod block and bag its 2 screws.'],
         caution=['Plug the camera FPC only with the power off.',
                  'Never screw the BFAR out past s = 3.0. If infinity needs more, stop: record both stops and update CAM '
                  'before printing.',
                  'If the tripod block will not come off cleanly, stop: the camera model must be updated first.'],
         check=['s recorded, inside 0-3.0', 'paint mark across adapter and BFAR', 'tripod block off, 2 screws bagged']),
    dict(id='B1', title='Heat-set inserts', sub='Bench, tub empty, any time before step 3 (collar insert: before step 7)',
         ctx=None, plus=['tub'], new=['lens_collar'], offsets={'lens_collar': (70, 0, 0)}, view=(25, 20), arrows=False,
         marks=[('s_c1', 'insert TL'), ('s_c2', 'insert TR'), ('s_c3', 'insert LL'), ('s_c4', 'collar lug insert (from below)')],
         parts=['tub (printed)', 'lens collar (printed)'], hw=[('D', 3), ('E', 1)], tools=[2], torque=None,
         do=['Heat the iron with the M3 heat-set tip.',
             'Press 3 short inserts (bag D) into the front-wall bosses TL, TR and LL from the front, square to the face, '
             'finishing 0.1 mm below it.',
             'Back each boss with a block through the open left side: the bosses hang behind a 2.5 mm wall. Go slowly.',
             'Press 1 long insert (bag E, L 5.7) into the lens collar lower lug from below.',
             'Let all inserts cool. Check that an M3 screw turns in by hand.',
             'Clear the 3 sacrificial 0.2 mm membranes in the collar with a 3.4 mm hand tool; remove the debris.'],
         caution=['A crooked insert is the usual failure in a small ASA boss: check squareness on every one.',
                  'Do not change the collar washer seats, cone or foot faces while clearing the membranes.'],
         check=['4 inserts square and flush', 'M3 screw turns in by hand in each', 'insert maker, OD, length recorded']),
    # ------------------------------------------------------------------ step 1: bench wiring (W pages)
    dict(id='1a', title='Fuse the battery pigtail', sub='Step 1, bench wiring (WIRING s7)', diagram='fuse',
         parts=['XT30 pigtail, 18 AWG silicone, cut to L_cut (XT30U female)', 'fuse 15 A Littelfuse 0251015.MXL',
                'adhesive heat-shrink 3:1'],
         tools=[2, 3, 4, 5],
         # r7 C3 (BX-3): cut-to-length pigtail (layout PIGTAIL; lead_access pigtail_range)
         do=['Cut the pigtail to L_cut = 200 mm + the G-W2 pads-to-W length, rounded up to 5 mm (200 mm if the pads are '
             'at W). L_cut runs from the pad joint to the XT30 rear and includes the fuse splice.',
             'If the pads-to-W length is more than 25 mm, stop: do not cut. The battery-lead drop would pass 0.15 V '
             '(gate G-W5); route the pair under the board straight to the hole, move W, or use 16 AWG, and re-check.',
             'Strip the red conductor about 20-25 mm from the XT30 female.',
             'Trim each fuse lead to 6.5 mm. Lap 5 mm of lead on the stripped conductor; leave a 1.5 mm stub at the fuse body.',
             'Solder each lead (350 C, 5 s at most).',
             'Shrink one adhesive 3:1 sleeve (about 28 mm) over the whole splice.',
             'Meter the red path end to end: less than 0.1 ohm.'],
         caution=['Never re-solder the XT30 female once the fuse is fitted.'],
         check=['red path < 0.1 ohm', 'splice fully covered']),
    dict(id='1b', title='Pigtail to the X1203 battery pads', sub='Step 1, bench wiring', diagram='pads',
         parts=['Geekworm X1203', 'fused pigtail (1a)', 'Kapton tape, 3 strips',
                'neutral-cure silicone RTV (not acetoxy)'], tools=[2, 3, 4, 5, 12],
         # r7 C3 (BX-3, BX-11): U at W and the leg taped on the bare board, then the RTV bead (no standoff tie)
         do=['Solder red to the + battery pad and black to the - pad.',
             'Shrink adhesive heat-shrink over both joints.',
             'Mark W with a pen on the port edge, 31.5 mm from the button-end edge.',
             'Lead the pair on the top face to W, straight in from inside the board (y < 23), not along the port edge: '
             'the keeper fingers kf3 and kf4 sit on that edge.',
             'Put one Kapton strip over the board edge at W. Fold the pair round the edge. Tape the leg flat under the '
             'board with 2 Kapton strips, straight in from W for about 32 mm, to above the pigtail hole. Keep the pair '
             'within 1 mm of the mark. The rest hangs free.',
             'Pads on the underside: run the pair straight under the board to that point and tape it, with no U.',
             'Strain relief: a neutral-cure silicone RTV bead over both joints and the first 8-10 mm of the pair, '
             'bonded to the board. Keep it off the pogo pads and the connectors.',
             'Meter + to - on the pigtail: no short.'],
         caution=['The pack is never connected at the bench.',
                  'No tie to a standoff: the RTV bead is the strain relief. Never acetoxy RTV (it corrodes).'],
         check=['no short + to -', 'joints insulated', 'U at the W mark (within 1 mm), leg taped flat',
                'RTV over both joints and 8-10 mm of the pair']),
    dict(id='1c', title='EVF 5 V lead with diode', sub='Step 1, bench wiring', diagram='diode',
         parts=['USB-A to 2-wire lead, 200 mm class', '1N5817 Schottky diode', 'JST PH 2-pin plug', 'adhesive heat-shrink'],
         tools=[2, 3, 4, 5],
         do=['Cut the + conductor near the free end. Solder the 1N5817 into it, band (cathode) toward the board end.',
             'Fit the JST PH 2-pin plug on the free end: + on pin 1, GND on pin 2.',
             'Shrink adhesive heat-shrink over the diode and both joints.',
             'Meter: VBUS to PH pin 1 forward through the diode; GND to pin 2.'],
         check=['diode band toward the PH plug', 'polarity metered']),
    dict(id='1d', title='EVF board pigtail', sub='Step 1, bench wiring', diagram='evfpig',
         parts=['Hicenda HDMI driver board Rev I', 'JST PH 2-pin pigtail'], tools=[2, 4, 12],
         do=['Photograph both sides of the board (EVF gate G1).',
             'Solder the PH 2-pin pigtail to the traced EXT+ and GND pads.',
             'Add heat-shrink strain relief.'],
         check=['photos taken', 'pin 1 = EXT+']),
    dict(id='1e', title='18/24 switch pigtail', sub='Step 1, bench wiring', diagram='switch',
         parts=['mini 2-position rotary switch', 'JST PH 2-pin pigtail, 50 mm'], tools=[2, 3, 4],
         do=['Solder the 50 mm JST PH pigtail to the common lug and the position-2 lug.',
             'Heat-shrink both joints.'],
         check=['lug 1 left free', 'both joints insulated']),
    dict(id='1f', title='Encoder address, QT lead splice', sub='Step 1, bench wiring', diagram='a0',
         parts=['Adafruit 5880 I2C QT rotary encoder',
                'QT lead parts: Adafruit 4397 (sockets) + Pololu 5521 (JST-SH), 4 thin sleeves, 1 adhesive sleeve'],
         tools=[2, 3, 4, 5, 12],
         do=['Bridge the A0 jumper with one solder blob (address 0x37).',
             'QT lead (WIRING W-QT): map continuity on both leads first. 4397: SH pin 1 GND black, 2 3V3 red, 3 SDA '
             'blue, 4 SCL yellow. Pololu 5521: black is pin 1, find the other three with the meter.',
             'Join by SH pin number, never by colour alone. Joints 91-115 mm from the socket tip, 8 mm apart, one thin '
             'sleeve each, one adhesive sleeve (about 35 mm) over all.',
             'Finished length 250 +/- 10 mm, socket tip to SH plug face.'],
         check=['A0 bridged', 'QT splice: 4 joints, pin 1 to pin 1, continuity end to end, no short',
                'no joint or sleeve outside 85-121 mm from the socket tip', 'QT lead 240-260 mm']),
    dict(id='1g', title='Bench stack: X1203 + Pi 5 + cooler', sub='Step 1, bench sub-assembly (joins the body at step 4)',
         ctx=None, plus=[], new=['x1203', 'x1203_kit', 'pi5', 'cooler'],
         offsets={'x1203': (0, 0, -40), 'x1203_kit': (0, 0, -20), 'pi5': (0, 0, 0), 'cooler': (0, 0, 40)},
         view=(-40, 28), arrows=False, parts=['X1203 (with pigtail)', 'X1203 kit: 4 standoffs, 8 M2.5 screws',
                                              'Raspberry Pi 5', 'Active Cooler', 'microSD card 32 GB'],
         hw=[('F', 1)], tools=[1, 12], torque='kit M2.5 screws 0.2 N m',
         do=['Stack only when the RTV bead (1b) is tack-free. Do not pull on the pigtail before the full cure the tube '
             'states.',
             'Stack the X1203 and the Pi 5 with the kit: 4 standoffs, 8 M2.5 screws, 0.2 N m, metal to PCB only.',
             'Fit the Active Cooler (pins seated). Plug its fan lead into the Pi FAN header; route it as the cooler ships.',
             'Flash the microSD (gate G-W3). Then take the card OUT of the Pi: it must stay out until step 5.'],
         caution=['The microSD hits the front wall on the stack path if it is left in.'],
         check=['stack square, cooler pins seated', 'fan lead plugged', 'pigtail leg still taped, RTV tack-free',
                'microSD out']),
    # ------------------------------------------------------------------ step 2: panel bench
    dict(id='2', title='Bench: panel', sub='Step 2, bench sub-assembly (joins the body at step 8)', ctx=None, plus=[],
         new=['panel', 'encoder', 'switch_1824', 'knob_exp', 'knob_fps'],
         offsets={'panel': (0, 0, 0), 'encoder': (0, -45, 0), 'switch_1824': (0, -45, 0),
                  'knob_exp': (0, 40, 0), 'knob_fps': (0, 40, 0)},
         view=(-50, 20), arrows=False, parts=['panel (printed, satin silver)', 'encoder (A0 bridged)',
                                              '18/24 switch + nut + washer', '2 knobs (printed)'],
         tools=[11, 6, 7, 16], torque='switch nut finger-tight + 1/8 turn (about 0.3 N m)',
         do=['Fill the engraving with the paint pen.',
             'Switch shaft, off the panel: fit the 18/24 switch dry (tab in its slot, washer as supplied, nut '
             'finger-tight). Measure how far the shaft stands above the panel face (P, caliper depth rod). Take the '
             'switch off.',
             'Clamp the shaft in soft vise jaws right next to the cut, the switch hanging free. Cut P - 6.9 mm off the '
             'shaft end and deburr. Never clamp the bushing thread; never saw with the switch on the panel.',
             'Refit the switch, tab in its slot, nut finger-tight + 1/8 turn.',
             'Snap the encoder into its cradle by pushing on the back of its board until all 3 hooks click.',
             'Lay the 2 paper strips on the panel face round the encoder shaft. Thumb flat on the back of the encoder '
             'board, press knob_exp onto its D shaft with the other palm until it stops on the paper. Press knob_fps on '
             'the same way, D flat to the shaft flat. Pull the paper out.'],
         caution=['From now on the knobs ride with the panel: never press a knob while the panel is on the body.'],
         check=['encoder under both hooks, shaft square', 'switch tab in its slot',
                'switch shaft 6.7-7.1 above the face', 'knobs 0.2 off the panel (paper drags)',
                'knob flat lines up with the 18 and 24 ticks at the stops']),
    # ------------------------------------------------------------------ step 3: base
    dict(id='3a', title='Base: tripod nut, run button, strap', sub='Step 3', ctx=None, plus=['base_grip'],
         new=['tripod_nut', 'run_button', 'strap'], offsets={'tripod_nut': (0, 0, 35), 'run_button': (0, 0, 40),
                                                              'strap': (0, -40, 0)},
         view=(35, 30), arrows=True, arrow_dirs={'tripod_nut': (0, 0, -1), 'run_button': (0, 0, -1)},
         parts=['base + grip (printed, black)', 'run button (pre-wired, red cap)', '12 mm hand strap'], hw=[('G', 1)],
         tools=[10, 8],
         do=['Press the tripod nut into its pocket from the top with a flat bar until it sits flush.',
             'Before the run button goes in: pass the run-lead socket end in through the base opening and push it up '
             'through the base passage from below (nothing is under the passage yet).',
             'Drop the run button into its cradle through the base opening, drawing the slack up through the passage. '
             'Press its red cap on through the grip-face hole.',
             'Thread the strap.'],
         check=['nut flush in its pocket', 'run cap 2.5 mm proud of the pad']),
    dict(id='3b', title='Tub onto the base, lock screw s_j', sub='Step 3', ctx=None, plus=['tub'],
         new=['base_grip', 'tripod_nut', 'run_button', 'strap', 's_j'], view=(40, -25), explode=2.5,
         parts=['tub (printed, satin silver)', 'base assembly (3a)'], hw=[('A', 1)], tools=[1, 13, 8],
         torque='s_j 0.35-0.5 N m, stop at head contact',
         # r7 C3 (BX-16): threaded before the tub goes down (lead_access run_lead_window 3.5 >= 3.2 at the slide start)
         do=['Hold the tub over the base with the base 10 mm to the rear. Push the run-lead sockets (separate 1-pin '
             'housings, already up through the base passage) on up through the rear (-X) end of the floor run-lead '
             'hole into the tub.',
             'Lower the tub, tongues through the windows. Keep the lead lightly pulled up so it stays in the rear end '
             'of the hole.',
             'Slide the base 10 mm forward until the tongues sit under the lips. The lead moves to the front end of the '
             'hole by itself.',
             'Drive s_j up through the base counterbore into the tub floor boss (straight PH1, from below).',
             'Lay the run lead in its floor lane and tape it flat with Kapton. Let the socket end hang out over the '
             'open +Y side.'],
         caution=['Thread the run lead before the tub goes down. Do not fish it up after the slide.'],
         check=['base slid the full 10 mm, does not lift off', 's_j at head contact (tally 1)',
                'run lead up through the -X end of the floor hole, not over the base top',
                'run lead not pinched between base and floor; taped flat in its lane']),
    # ------------------------------------------------------------------ step 4: Pi stack
    dict(id='4a', title='Lead routing, then the Pi stack', sub='Step 4 (ESD strap; microSD out)', ctx=3,
         new=['x1203', 'x1203_kit', 'pi5', 'cooler'], view=(70, 45), explode=1.0,
         parts=['bench stack (1g)'], tools=[12],
         # r7 C3 (BX-11): run lead taped at step 3; pigtail leg taped at 1b
         do=['Check that the run lead is still taped flat in its lane, its socket end held out over the open +Y side.',
             'Feed the XT30 end of the pigtail down through the pigtail hole into the grip (long side front to back); '
             'the leg under the board comes down with the stack. Once the stack is down, push the XT30 and the free '
             'pigtail up into the empty grip bay: nothing may hang below the grip mouth until step 10.',
             'Hold the stack\'s port edge away from the U: more than 10 mm from the W mark.',
             'Lower the stack about 3 mm behind the front wall and 2 mm off the right wall.',
             'Below the right-wall pads, move it against the right wall.',
             'Just above the floor, slide it 2.8 mm forward and set it down on its 4 bosses. Nothing clicks: the kit '
             'screw heads drop into the boss pockets.'],
         caution=['Nothing may lie under the stack: run lead taped in its lane, pigtail leg taped under the X1203, '
                  'XT30 down its hole.'],
         check=['stack flat on its 4 bosses, no rock', 'pigtail leg still taped flat under the X1203',
                'U at the W mark, not under the keeper finger kf4 or the bar (x -41 and beyond)']),
    dict(id='4b', title='Pi keeper, screws s_k1 and s_k2', sub='Step 4', ctx=3,
         plus=['x1203', 'x1203_kit', 'pi5', 'cooler'], new=['pi_keeper', 's_k1', 's_k2'], view=(75, 45), explode=1.0,
         parts=['Pi keeper (printed, black)'], hw=[('A', 2)], tools=[1, 13],
         torque='s_k1, s_k2 0.35-0.5 N m, stop at head contact',
         do=['Hold the keeper level from the open left side, 0.5 mm above its 2 bosses and 1.2 mm behind its place.',
             'Slide it in (toward the right wall) under the stick-guide rail until its port fingers are over the X1203 edge.',
             'Push it 1.2 mm forward: the 2 USB fingers go under the Pi.',
             'Lower it onto its bosses. Drive s_k1 and s_k2 straight down.'],
         check=['keeper fingers over the X1203 at all 4 stations', 'keeper flat on its 2 bosses',
                's_k1, s_k2 at head contact (tally 1 each)']),
    dict(id='4c', title='Plug the Pi end of HDMI, FPC and EVF 5 V lead', sub='Step 4 (top open)', ctx=4,
         new=[], view=(60, 55), zoom=1.0, focus='ctx_parts', focus_ids=['pi5', 'cooler', 'pi_keeper'],
         views=[dict(view=(60, 55), label='A'), dict(view=(95, 80), label='B', marks=True, zoom=1.1),
                dict(view=(150, 40), label='C', marks=True, zoom=1.1)],
         marks=[('ko_hdmi_pi', 'HDMI0: 90 deg plug, cable up'), ('ko_fpc_up', 'CAM/DISP 1: FPC, latch closed'),
                ('ko_usb_evf', 'upper USB 2: EVF 5 V lead')],
         parts=['micro-HDMI 200 mm (90 deg Pi plug)', 'camera FPC 22-to-15, 200 mm', 'EVF 5 V lead (1c)'], tools=[12],
         do=['micro-HDMI: 90 deg plug into HDMI0 (the one nearest the USB-C), cable leaving upward. Leave the EVF end loose.',
             'FPC: into CAM/DISP 1, contacts as printed on the cable; close the latch. Leave the camera end loose.',
             'EVF 5 V lead: USB-A into the upper USB 2 port. Leave the PH end loose.'],
         check=['3 plugs fully home at the Pi']),
    dict(id='4d', title='Header leads', sub='Step 4 (top open, header in sight)', diagram='header',
         parts=['QT lead, 250 mm (Adafruit 4397 sockets spliced to Pololu 5521 JST-SH, splice W-QT made at the bench)',
                '18/24 lead (Dupont to PH, 200 mm)', 'run lead (from step 3)'],
         tools=[8, 12],
         do=['Plug one housing at a time, top open, header in sight.',
             'QT lead on pins 1/3/5/6: red 1, blue 3, yellow 5, black 6.',
             '18/24 lead on 33/34: GPIO13 on 33, GND on 34.',
             'Run lead on 37/39: GPIO26 on 37, GND on 39.',
             'Seat each housing straight down with open tweezer tips straddling the wire, pressing on both sides of the '
             'housing top, until it stops on the header plastic. '
             'Fingers do not fit beside them. Then tug each wire straight up gently: no housing may lift.',
             'Run the QT and 18/24 leads along the right wall and across behind the blower inlet. Keep the QT splice '
             'sleeve in the straight part of the cross run, not in a corner. Park their free ends out of the open left '
             'side.',
             'Lay the run lead over the cooler shroud, below z 40.'],
         caution=['Count from pin 1. A housing one row over puts 5 V from pin 2 on the QT 3V3 wire.',
                  'Single 1-pin housings only (a 1x2 only on 33/34 or 37/39). Never a 1x3 or 2x3 shell.'],
         check=['QT red on pin 1, 18/24 on 33/34, run on 37/39', '8 contacts, all housing tops level, each wire tugged',
                'header photographed', 'QT splice sleeve in the straight cross run',
                'leads along the right wall, run lead over the shroud']),
    # ------------------------------------------------------------------ step 5: hood
    dict(id='5a', title='Plunger and hood', sub='Step 5', ctx=4, new=['plunger', 'hood'],
         offsets={'plunger': (45, 0, 0)}, view=(40, 30), explode=1.0,
         parts=['plunger (printed, black)', 'hood (printed, black)'], tools=[],
         do=['Hold the plunger in the front-wall hole, flange outside.',
             'Lower the hood straight down until all 4 hooks click. The front plate traps the plunger.'],
         caution=['Never rock the hood in: straight down only.'],
         check=['hood level on the wall tops all round', '4 hooks clicked', 'plunger moves in and returns']),
    dict(id='5b', title='microSD through the front slot', sub='Step 5', ctx=5, minus=[], new=['microsd'],
         view=(-25, 15), zoom=0.45, focus='new_final', explode=1.0,
         marks=[('microsd', 'slot: contacts up')], parts=['microSD (flashed at 1g)'], tools=[8],
         do=['Push the microSD through the slot low in the front plate (both walls) with tweezers, contacts up, until it '
             'latches.'],
         check=['card latched, tip about 2.5 mm proud of the Pi edge, inside the slot']),
    # ------------------------------------------------------------------ step 6: EVF
    dict(id='6a', title='Eyepiece', sub='Step 6', ctx=5, new=['eyepiece'], view=(-150, 25), explode=1.3, zoom=1.0,
         parts=['eyepiece 0PE039-16X'], tools=[],
         do=['Push the eyepiece spigot forward into the rear-wall bore through the housing, flange on the rear face.'],
         check=['spigot flange flat on the rear face']),
    dict(id='6b', title='Mate the EVF leads outside the body', sub='Step 6 (ESD mat; pack out)', diagram='evf_mate',
         parts=['HMX039 micro-OLED + 50 mm flex', 'EVF board (1d)', 'foam pad 16 x 14 x 1.0, adhesive one side'],
         tools=[8, 12],
         do=['Stick the foam pad to the OLED back (adhesive side to the OLED, centred).',
             'Flex into the board ZIF, latch closed.',
             'Pull the EVF 5 V lead end out of the open left side. Mate the 5 V PH junction with the pair held about '
             '60 mm (a hand\'s width) out of the open left side.',
             'Do NOT plug the HDMI yet: it goes into the board after the slide (page 6c).'],
         caution=['Never mate any lead with the pack connected.'],
         check=['pad stuck flat on the OLED back', 'flex square in the ZIF, latch closed', 'PH fully home',
                'HDMI still loose']),
    dict(id='6c', title='Slide the OLED and board in together', sub='Step 6', ctx=6, minus=['hmx039', 'evf_board', 'foam_pad'],
         plus=[], new=['hmx039', 'evf_board', 'foam_pad'], view=(140, 35), explode=1.0,
         parts=['OLED + pad + board tethered pair (6b)'], tools=[8, 10, 12, 17],
         do=['Slide the OLED and the board in together as a tethered pair until the board stops: OLED and pad into the '
             'cell, board into its slot.',
             'Keep the PH junction riding above the bottom rail, beside the board. When the board is home, push the '
             'junction -Y and down into its space (ko_5v_end) with the 120 mm tweezers.',
             'Only after gate G-W7 passed: pinch the right-angle HDMI plug\'s +Y end top and bottom (thumb under it), or '
             'hold it in the smooth-jaw pliers, cable leading -Y. Feed it in under the rail end, its bottom above '
             'the stick-guide top, lift it to the socket, then push it straight up: a fingertip flat on the stick-guide '
             'top, or straight up from the open well below (fingertip, or the steel rule held upright as a push stick).',
             'Coil the HDMI slack over the stick guide (ko_hdmi_coil), clear of the cooler inlet.'],
         caution=['Push the HDMI straight up. If it does not go, pull it back and re-aim; never lever against the '
                  'board or the guide edge.',
                  'From now until the panel is on (step 8), keep the body level or nose-down: only the panel cap stops '
                  'the eyepiece moving rearward.'],
         check=['OLED in its cell, pad on its back', 'board fully home', 'junction in its space, clear of the rail',
                'HDMI fully home (mirror or fingertip)', 'HDMI coil clear of the cooler inlet',
                'first print: gate G-EVF-3 (5 HDMI mate/unmate cycles) recorded']),
    # ------------------------------------------------------------------ step 7: collar + camera
    dict(id='7a', title='Lens collar, centred', sub='Step 7 (B0 done; camera still out)', ctx=6,
         new=['lens_collar', 's_c1', 's_c2', 's_c3'], view=(35, 25), explode=1.0, zoom=1.0, focus='new_final_ctx',
         parts=['lens collar (printed, black, with insert)', 'centring gauge for this lens (tool 14)'], hw=[('B', 3)],
         tools=[13, 14], torque='s_c1, s_c2, s_c3 0.15 N m (provisional cap), stop at head contact',
         do=['Put the collar feet through the 4 hood holes onto the tub face.',
             'Start s_c1, s_c2, s_c3 with washers, 2 turns each.',
             'Push the centring gauge through the collar until its rear cone seats in the tub lip and its front cone in '
             'the collar bore chamfer. Hold it home with a thumb.',
             'Tighten s_c1, s_c2, s_c3 from the front on the torque screwdriver, 0.15 N m. Pull the gauge out.'],
         caution=['Do this before the lens is fitted: with the lens on, the driver handle hits the lens barrel.',
                  'Never by hand: a hand-tight M3 is 2-3 times the value and can pull a short insert.'],
         check=['4 feet flat through the hood holes', 'gauge seated on both cones while tightening', 'washers under heads']),
    dict(id='7b', title='Camera and adapter into the cage', sub='Step 7 (ESD strap)', ctx=6, plus=['lens_collar', 's_c1',
                                                                                                    's_c2', 's_c3'],
         new=['gs_camera', 'c_cs_adapter'], view=(60, 35), explode=1.0,
         parts=['GS camera with adapter (B0)'], tools=[12],
         do=['Plug the FPC into the camera (15-pin end, latch closed).',
             'Bring the camera in from the open left side, 2 mm high and 11 mm behind its place.',
             'Lower it 2 mm, then push it 11.1 mm forward until the adapter has passed the tub lip and the lock tab has '
             'gone in between the two tab-catch tines under the hood. If the tab stops on a tine end, roll the camera '
             'level and push again.',
             'It rests in its cage (BFAR in the counterbore, tab near the wall) until the lens carries it.',
             'Fold the FPC slack into its loop space.'],
         check=['camera resting, not wedged (lifts and turns slightly)', 'adapter mark lines up',
                'FPC folded, clear of the blower inlet']),
    # ------------------------------------------------------------------ step 8: lens + panel
    dict(id='8a', title='Lens through the collar, s_c4', sub='Step 8 (panel still off)', ctx=7, new=['lens', 's_c4'],
         view=(40, 25), explode=1.0, parts=['C-mount lens (Kowa LM6HC)'], hw=[('C', 1)], tools=[13],
         torque='s_c4 0.2 N m, stop at head contact',
         # r7 C4 (BX-4): no hand holds the camera; the hood tab catch reacts the thread through metal (roll_catch)
         do=['Fit s_c4 loosely. Lay the body on its right side on the folded cloth, open left side up.',
             'From above, through the open left side, put one fingertip on the centre of the camera cover and press the '
             'camera forward (+X) onto its lip catch. Push only: never pinch or turn the cover.',
             'Pass the lens through the collar. Screw it into the adapter with fingertips until it stops, with no extra '
             'snug. The camera turns with it about 3 deg until its metal lock tab meets the hood tab catch, which '
             'holds it through metal.',
             'Set iris and focus; tighten the 2 thumb screws.',
             'Push the lens gently rearward until the knurl seats on the collar cone.',
             'Stand the camera upright, one hand on the grip until s_c4 is snug (it tips at about 6 deg if let go). '
             'With s_c4 still loose, turn lens and camera together the other way until the lock tab stops on the '
             'other tine (about 6.5 deg of free roll), then back about half way: the tab now floats between the tines '
             'and the camera hangs on the lens.',
             'Snug s_c4 straight down from above: 0.2 N m on the torque screwdriver.'],
         caution=['Never hold, pinch or turn the camera by the cover or the PCB: the tab catch takes the thread torque.',
                  's_c4 is always the last operation on the lens.'],
         check=['knurl seated on the cone, no axial play',
                'camera touches neither the lip, the counterbore nor the tab-catch tines',
                'by feel before s_c4: a soft stop each way at about 3 deg, tab left mid-way', 's_c4 at 0.2 N m']),
    dict(id='8b', title='Panel leads, then the panel', sub='Step 8', ctx=7, plus=['lens', 's_c4'],
         new=['panel', 'encoder', 'switch_1824', 'knob_exp', 'knob_fps'], view=(70, 25),
         explode=60.0 / 70.0,   # r7 C2: panel drawn at the 60 mm QT mating pose (panel_on starts at +70)
         parts=['panel assembly with both knobs (step 2)'], tools=[],
         do=['A helper holds the body upright by the grip until the panel is home (never leave it standing on its grip '
             'end: it tips at about 6 deg).',
             'Prop the panel about a hand\'s width (60 mm) off the body, inner face toward it, its bottom edge on a block '
             'or book stack as tall as the grip (about 110 mm).',
             'Mate the 18/24 PH junction first, with both hands, one on each housing. (The header ends went on at step '
             '4.)',
             'Then the QT: one hand steadies the panel, thumb behind the encoder\'s +X edge; the other holds the QT plug '
             'by its rear end and pushes it into the encoder\'s rear-side socket (the one nearest the lead), finishing '
             'with a fingernail on its back face. It is home when it stops (friction lock, no click).',
             'Move the panel toward the body, body upright. At about 30 mm off, reach down from above between the body and '
             'the panel and lay the spare QT lead as a flat fold '
             'between the encoder and the 18/24 switch, on top of the HDMI cable. Lay the 18/24 spare and its PH '
             'junction in the same space at the switch end. Keep both away from the blower.',
             'Keep the body upright until the panel is fully home.',
             'Push the panel on toward the right: tongue into the hood groove, boss tabs into the lip notches, flush. '
             'The keeper finger becomes the camera rear catch.'],
         check=['QT plug fully seated at the encoder before the panel moves in',
                'before the last 30 mm: QT fold, 18/24 spare and PH junction between encoder and switch on the HDMI '
                'run; nothing over the blower inlet',
                'panel closes without pressure, flush with the hood band and the tub', 'no lead pinched at the panel edge']),
    dict(id='8c', title='Four panel screws', sub='Step 8', ctx=8, minus=['s_b1', 's_b2', 's_r1', 's_r2'],
         new=['s_b1', 's_b2', 's_r1', 's_r2'], view=(-30, -35), explode=1.0,
         parts=[], hw=[('A', 4)], tools=[1, 13], torque='0.35-0.5 N m, stop at head contact',
         do=['Hold the panel home and turn the camera over onto its hood roof on a folded cloth at the bench edge, grip '
             'up, right side toward you, its right face within about 20 mm of the edge (the driver handle and your hand '
             'go past the edge).',
             'Lay a flat block no taller than 25 mm (a closed paperback) on the cloth against the left side, between the '
             'eyepiece and the lens, stood against a wall or a heavy object so it cannot slide. It bears on the hood band '
             'and the panel strip between the knobs and the cloth and keeps the panel home.',
             'Drive s_b1 and s_b2 first (now downward) through the 2 base counterbores into the panel bosses.',
             'Then drive s_r1 and s_r2 level from the right through the wall pads into the panel posts, the block '
             'taking the push; hold the grip with your other hand.',
             'Turn the camera upright, a hand on the grip; set it down only on its right side.'],
         caution=['Never lay the camera on its left side (the exposure knob would carry it), and never stand it on '
                  'its grip end (it tips at about 6 deg).'],
         check=['4 screws at head contact, none stripped (tally 1 each)', 'the dials turn; nothing rubs inside']),
    # ------------------------------------------------------------------ step 9: exterior
    dict(id='9', title='Eyecup, USB stick', sub='Step 9', ctx=8,
         new=['eyecup', 'usb_stick', 'stick_sleeve'],
         offsets={'eyecup': (-40, 0, 0)}, view=(130, 25), explode=1.0,
         parts=['eyecup (TPU)', 'USB SSD stick + sleeve (printed)'], tools=[],
         do=['Push the eyecup over the eyepiece barrel.',
             'Fit the sleeve to the stick. Push the stick in from the rear into the lower USB 3 port until the sleeve is '
             'flush with the rear face.'],
         check=['eyecup over the eye-end body', 'sleeve flush']),
    # ------------------------------------------------------------------ step 10: power
    dict(id='10a', title='Battery: XT30, pack, cap', sub='Step 10 (body closed)', ctx=9,
         new=['xt30_pair', 'pack', 'cap'], view=(40, -30), explode=1.0,
         parts=['1S2P 18650 pack (charged out of the camera)', 'cap (printed)'], tools=[],
         # r7 C3 (BX-3): face >= 15 mm out (lead_access pigtail_xt30_mouth, mate_reach xt30)
         do=['Lay the camera on its right side on the folded cloth (never on its left side; not on its hood roof now: '
             'the eyecup stands proud of it).',
             'Draw the pigtail XT30 out of the grip mouth until the whole XT30 housing and at least 15 mm of wire '
             'behind it are out (estimate: about 28 mm of wire or more). If it does not reach, stop: never mate it '
             'inside the bay. Re-check the cut length (G-W2).',
             'Hold the pack in your palm, its XT30 in your fingers, and plug it into the pigtail XT30, red to red, '
             'holding both housings (see the diagram on the next page).',
             'Push the junction and the folded pigtail into the bay ahead of the pack, then the pack, ribbon last. The '
             'XT30 pair ends up flat on the pack top under the run button, pigtail (female) end to the rear, fuse '
             'sleeve beside it, the pigtail fold above. The pigtail must leave the XT30 female straight (no bend at its '
             'solder cups): if it does not, stop (gate G-MP-PACK).',
             'Look up the mouth: nothing may hang in the gaps beside the pack.',
             'Slide the cap on rearward until the detent clicks.'],
         caution=['This powers the camera: the X1203 may start the Pi at once.'],
         check=['whole XT30 housing + 15 mm of wire out before mating', 'no loop beside the pack', 'cap detent clicked']),
    dict(id='10b', title='XT30 junction', sub='Step 10', diagram='xt30', parts=[], tools=[],
         do=['Mate by the housings, red to red.'], check=['fully mated, no wire strain']),
    dict(id='10c', title='Power on, level check, gates', sub='Step 10', ctx=10, new=[], view=(35, 25), zoom=1.0,
         parts=[], tools=[1, 13], torque='s_c4 0.2 N m',
         do=['Press the plunger: the EVF shows the boot screen (there are no LED indicators).',
             'Level the horizon on live view every time: loosen s_c4 half a turn, turn lens and camera together until '
             'it is level (window +-1.4 deg; a soft stop at about 3 deg means the tab is on a tine: come back; the '
             'lock-screw heads keep 0.3 mm or more off the tab-catch tines), push the lens back '
             'onto the cone, re-snug s_c4 to 0.2 N m.',
             'Run WIRING gates G-W8 to G-W12 in the closed body (G-W12: full-workload power test).'],
         caution=['Shut down before service: hold the plunger 2 s, wait for the EVF to go dark, wait 5 s more, then '
                  'cap off, pack out, XT30 parted (ASSEMBLY s7 P1-P4).',
                  'Set the camera down on its right side; never on its left side (the exposure knob), and never stand it '
                  'on its grip end (it tips at about 6 deg).'],
         check=['boot screen on the EVF', 'horizon level', 'G-W8 to G-W12 recorded']),
]

# Open design issues found by the physical blocker check of 2026-10-08 (guide/BLOCKERS-2026-10-08.md). They are not
# fixed in CAD; the interim wording below is untested advice, shown on the page of the step concerned.
# r7: entries are removed once their item is fixed in CAD (BX-1 removed: SPEC-C1, the HDMI is plugged after the slide by
# design; page 6c checks first-print gate G-EVF-3).
ISSUES = {
}
# r7: ISSUES['8a'] (BX-4) removed: SPEC-C4, the hood tab catch holds the camera through metal (check roll_catch).
# r7: ISSUES['1g'] and ISSUES['10a'] (BX-3) removed: SPEC-C3, cut-to-length pigtail, RTV at the pads, face >= 15 mm
#     out of the mouth (check lead_access, mate_reach xt30).
# r7: ISSUES['9'] and ISSUES['2'] (BX-5) removed: SPEC-C5, the knobs are pressed on at bench step 2 (page 2).
# r7: ISSUES['8b'] (BX-2) removed: SPEC-C2, a 250 mm QT lead plugged with the panel 60 mm off (check mate_reach).

# Handling tips from the same blocker check (MINOR findings): shown under TIPS on the page concerned.
# r7: TIPS['2'] (BX-14), TIPS['6c'] (BX-7, BX-9) and TIPS['8c'] (BX-13) removed: now plain steps on pages 2, 6b/6c, 8c.
TIPS = {
    '3b': ['Thread the run-lead sockets up through the floor hole before you lower the tub; keep the lead in the rear '
           '(-X) end of the hole while the tub drops and slides.',   # r7 C3 (BX-16 fixed)
           'BX-12: hold the strap aside for the s_j driver handle (2.35 mm clearance).'],
    '4a': ['C-2: feed the XT30 with its long side front-to-back; once it is in the bay, steer it rearward (below z -20 '
           'the run-button cradle wall is in the way).',
           'The pigtail leg is already taped under the X1203 (page 1b): just feed the XT30 down the hole as the stack '
           'comes down. Check that the run lead is still taped flat in its lane.'],   # r7 C3 (BX-11 fixed)
    '8a': ['Fingertip pushes the cover centre forward; turn the lens with fingertips until it stops. The camera stops '
           'on the tab catch. Never grip the cover. Before s_c4, turn lens and camera together the other way to the '
           'other tine, then back half way.'],   # r7 C4 (BX-4 fixed) + fix-up turn-back
    '4d': ['Seat each socket straight down with open tweezer tips straddling the wire (both sides of the top), then tug each wire. Single sockets only '
           '(a 2-way only on 33/34 or 37/39).'],   # r7 C2: BX-10 prefix dropped (check header_housings)
    '8b': ['A helper holds the body. Prop the panel a hand\'s width off on a block. Mate the small PH junction first, '
           'then push the QT plug in with a fingernail. Fold both spare leads and the small junction between the dial '
           'and the switch before the panel closes.'],   # r7 C2 + fix-up (VERIFY-C2)
    '5b': ['C-14: check on receipt whether the Pi 5 slot is push-push. If it is, removal is push-to-release, not pull.'],
    '5a': ['BX-6: rest the body nose-up on its rear face so the plunger stays in its hole by gravity, then lower the hood '
           'straight down onto the body.'],
    '7a': ['BX-15: thumb on the upper right of the gauge face while driving s_c3; on its lower half while driving s_c1 '
           'and s_c2.'],
    '7b': ['BX-8: pre-fold the FPC S-fold on the bench (bend radius 1 mm or more, held with a Kapton strip) before the '
           'camera goes in; it must not touch the blower inlet.'],
    'B0': ['BX-12 (buying tool 13): handle dia 30 or less; with a 1/4 in hex holder use a PH1 bit of 50 mm or more whose '
           'turned shank (6.5 or less) covers at least the first 8 mm.'],
}
