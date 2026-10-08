# SPDX-License-Identifier: MIT
"""GS8 D2 release layer: the single source of truth for geometry (no CAD dependency).

Import it from any build module:  import layout as L   (or  from layout import *).
Run it (plain python, no CadQuery) to self-check and print a summary:  python cad/gs8-d2-v1/layout.py

FRAME (all numbers in mm, assembly coordinates):
  X forward (toward the lens), Y to the operator's LEFT (panel side), Z up.
  Origin: body-bottom centre at the front plate, i.e. x = 0 is the hood front-plate OUTER face, y = 0 the body
  centre plane, z = 0 the tub floor underside (body bottom). The black base hangs below z = 0.
  The concept (concepts/nizo-evf-2026-10-03/D2/build_concept.py) had x = 0 at mid-length; every concept x is
  shifted by SHIFT = -77.0 (use cx()). y and z are unchanged.
Every number below comes from the concept unless a comment says CHANGED (then SPEC.md section 9 says why).
Purchased-part numbers are proxies (datasheet / listing / repo / estimate as tagged); nothing is printed, bought
or measured.

BOX convention: B(x0, x1, y0, y1, z0, z1) -> {'x': (x0, x1), 'y': (y0, y1), 'z': (z0, z1)}.
"""
import math

REVISION = 'GS8 D2 release v1 (cad/gs8-d2-v1)'
SHIFT = -77.0                      # concept x -> D2 x


def cx(*xs):
    """Concept x -> D2 x (one value, or a tuple for several)."""
    r = tuple(round(x + SHIFT, 4) for x in xs)
    return r[0] if len(r) == 1 else r


def B(x0, x1, y0, y1, z0, z1):
    return {'x': (round(x0, 4), round(x1, 4)), 'y': (round(y0, 4), round(y1, 4)), 'z': (round(z0, 4), round(z1, 4))}


def CYL(axis, c0, c1, r, a0, a1, r_in=None):
    """Cylinder along `axis` ('x'|'y'|'z'); (c0, c1) = the other two coordinates in xyz order; a0..a1 along the axis."""
    d = {'axis': axis, 'c': (round(c0, 4), round(c1, 4)), 'r': r, 'a': (round(a0, 4), round(a1, 4))}
    if r_in is not None:
        d['r_in'] = r_in
    return d


# =============================================================================== 1. FDM rules (from release_common.py)
FDM = dict(
    NOZZLE=0.4, LAYER=0.2,
    MIN_WALL=1.2, MIN_WALL_LOADED=1.6, MIN_FEATURE=0.8,
    SLIDE=0.25, LOCATE=0.15, SEAM=0.3,                  # per side
    MAX_OVERHANG_DEG=45.0, MAX_BRIDGE=30.0, TEARDROP_ABOVE_D=8.0,
    BED_CHAMFER=0.6,                                    # 45 deg chamfer on bed-face edges, no fillets on the bed face
    ENGRAVE_DEPTH=0.4, ENGRAVE_MIN_STROKE=0.6,
    ENGRAVE_TEXT_GROW=0.15,                             # FIXER P1: glyph outlines grow 0.15 per side (strokes >= 0.8)
    ENGRAVE_MAX_THIN_SHARE=0.20,                        # FIXER P1: groove check, share of a glyph under MIN_STROKE
    KNOB_BORE_OFFSET=0.10,                              # FIXER P10: radial D-bore growth over the shaft (coupon sets it)
    SNAP_GUSSET=0.8,                                    # FIXER P2: 45 deg root gusset leg on snap beams
    SNAP_KT=1.5,                                        # FIXER P2: strain concentration with the 0.8 gusset (r/t 0.5)
    ASA_DENSITY=1.07e-3,                                # g/mm3
)
PRINT_BEDS = {'250x210x220 (Prusa MK4/Core One class)': (250, 210, 220),
              '256x256x256 (Bambu X1/P1 class)': (256, 256, 256)}
# infill factor for mass = solid volume x ASA density x factor (4 walls, 25 % gyroid; small parts 100 %)
INFILL_FACTOR = {'shell': 0.85, 'base_grip': 0.6, 'small': 1.0, 'tpu': 1.0, 'thin': 1.0}
TPU_DENSITY = 1.21e-3

# =============================================================================== 2. global datums and body
L, W, H = 154.0, 70.0, 100.0
X_FRONT = 0.0                       # hood front-plate outer face
X_REAR = -154.0                     # tub rear outer face (concept X0 = -77)
T = 2.5                             # tub wall
XT1 = -2.7                          # tub front-wall outer face (concept X1 - 2.7)
X_FW_IN = XT1 - T                   # -5.2 tub front-wall inner face = CAMERA SEAT and Pi-edge reference
X_RW_IN = X_REAR + T                # -151.5 tub rear-wall inner face
ZT1 = 97.3                          # tub wall tops = hood band underside (declared contact)
YR, YL = -35.0, 35.0                # right wall outer face, panel outer face
Y_RW_IN = YR + T                    # -32.5 right-wall inner face
SPLIT = YL - 2.8                    # 32.2 panel inner face / tub-panel joint plane
RV = 5.0                            # vertical edge radius of the body outline (tub + panel)
FLOOR_Z = (0.0, T)                  # tub floor
LENS_AXIS = (0.0, 60.0)             # (y, z) of the optical axis
EYE_AXIS = (16.0, 78.0)             # (y, z) of the EVF axis
DIAL_Z = 57.0                       # control line on the panel
EXP_X, FPS_X = cx(14.0), cx(-46.0)  # -63.0 exposure dial, -123.0 18/24 selector

# --- printed part envelopes (outer bounding boxes in assembly coordinates; build owners stay inside them)
TUB_BOX = B(X_REAR, XT1, YR, YL, -3.65, ZT1)            # incl. keyhole tongues under the floor (z -3.65..0)
PANEL = dict(box=B(X_REAR, XT1, SPLIT, YL, 8.2, ZT1 - FDM['SEAM']),   # wall; z 8.2..97.0
             t=YL - SPLIT, z_low=8.2)
PANEL_BOX = B(X_REAR, XT1, YR + 2.7, YL, 2.6, ZT1 - FDM['SEAM'])     # incl. posts and bosses (boss z 2.6)
LIP = B(X_REAR + RV, XT1 - RV, SPLIT, YL, T, 7.9)       # tub left lip below the panel (seam 0.3 to z 8.2)
HOOD = dict(
    y=(YR + 2.65, YL),                # -32.35..35 (INTEGRATOR: was YR + 3.0; LOCATE 0.15 to the right-wall inner face
                                      # closes the 0.5 open slit along the roof's right edge; hood_panel request 1)
    band_z=(ZT1, H),                  # 97.3..100 (2.7 thick; CHANGED: rests on the wall tops, concept 97.5)
    band_x=(X_REAR - 0.2, X_FW_IN + T + 0.2),   # -154.2..-2.5
    plate_x=(XT1 + 0.2, X_FRONT),     # -2.5..0 front plate (0.2 gap to the tub front wall)
    plate_z=(0.3, H),                 # bottom 0.3 above the base top (seam)
    turret=CYL('x', 0.0, 60.0, 30.0, 0.0, 6.0, r_in=18.25),       # Ø60 x 6 (concept bezel); bore CHANGED 30.4 -> 36.5
    turret_b=CYL('x', 0.0, 60.0, 28.5, 6.0, 8.5, r_in=18.25),     # Ø57 x 2.5 step (concept bezel_b)
    housing=B(-170.2, -154.2, -8.0, YL, 55.0, H),   # eyepiece housing, open at -x; CHANGED z0 56 -> 55, gap 0.1 -> 0.2
    housing_wall=1.6, housing_top_wall=1.5, housing_r=6.0,
    housing_window=dict(side='+y', x=(-170.2, -154.2), z=(66.0, 90.0)),  # diopter reach; barrel stands 0.25 past y 35
)
HOOD_BOX = B(-170.2, 8.5, Y_RW_IN, YL, 0.3, H)     # INTEGRATOR: y0 -32.5 (hk1/hk2 tooth tips reach y -32.25)
BASE = dict(
    x=(cx(-40.0), -0.5), y=(YR - 0.2, YL + 0.2), z=(-8.0, 0.0),   # -117..-0.5; plate y +-35.2 (skirts separate)
    front_chamfer=5.0,                  # 45 deg at the front underside edge: (x -5.5, z -8) -> (x -0.5, z -3)
)
# --- R2 (finding 3): the skirts are ELIMINATED (no part, no step, no mate). SKIRTS and SKIRT_JOINT stay defined only
#     until ... (INTEGRATOR r2: both deleted once test_common.py stopped using them; r1 text: baseline-r1-2026-10-04.zip).
SKIRTS_ELIMINATED = True   # --- R2 end
GRIP = dict(x=(cx(6.0), cx(54.0)), y=(-15.0, 15.0), z=(-110.0, BASE['z'][0]), er=9.0, wall=2.5)
#            GR -71 .. GF -23                     column below the base
GRIP['axis_x'] = (GRIP['x'][0] + GRIP['x'][1]) / 2              # -47.0 grip axis
GRIP['top_z'] = BASE['z'][0]                                    # -8.0 the web of the hand
GRIP['bay'] = B(GRIP['x'][0] + 2.5, GRIP['x'][1] - 2.5, -12.5, 12.5, -110.0, -10.0)   # 43 x 25 battery bay, open below
CAP = dict(box=B(GRIP['x'][0], GRIP['x'][1], -15.0, 15.0, -116.0, -105.8),   # R2: z1 -106.5 -> -105.9; FIXER r2 -105.8 (key head tip 1.5, hook class 1.6)
           er=9.0, open_dir='+x', travel=52.0)
GRIP_BASE_BOX = B(BASE['x'][0], BASE['x'][1], BASE['y'][0], BASE['y'][1], GRIP['z'][0], 0.0)

# =============================================================================== 3. interfaces (joint contracts)
# Each joint names the part that CARRIES each feature. Clearances are per side unless stated.
SL, LO, SE = FDM['SLIDE'], FDM['LOCATE'], FDM['SEAM']

# --- J1 hood -> tub: the hood DROPS STRAIGHT DOWN (-Z) (CHANGED from "slide back": the front plate and the eyepiece
#     housing embrace the tub ends, so no x slide is possible). 4 cantilever snap hooks hang from the band underside
#     and click under catch ledges on the tub wall inner faces. Catch face 90 deg (positive) on hk1/hk2, 45 deg return on
#     hk3/hk4; release (FIXER r2, below): 2 pins through the right-wall holes, then lift. Hook: length 10.5, t 1.6, w 8.0,
#     tooth 0.65 (land 0.6, 45 deg lead-in below), 0.8 x 45 deg root gussets both faces; ledge 0.8 proud of the
#     wall, z 88.15..89.75 (45 deg chamfer on top); tooth top z 88.05 (play 0.1). Deflection 0.40.
# INTEGRATOR r2 (finding 2): the tooth root section (land + lead run at the beam face) was 1.05 (land 0.4), under
#     MIN_WALL 1.2 for a lug in shear (the tub ledge is held to the same rule). Land 0.4 -> 0.6 (root 1.25) with the
#     beam length kept at 10.5 (the hk4 tip keeps its 0.25 over the rear-wall block); the catch plane and the tub
#     ledges move up 0.2 to match (catch_z 87.95 -> 88.15, tooth top 87.85 -> 88.05). Registry: hood_tooth_hk*.
# FIXER P2: length 9.0 -> 10.5 and tooth 0.8 -> 0.65 (reach over the ledge 0.55 -> 0.40); catch face z 97.3 - 9.45
#     = 87.85, ledge catch_z 87.95. Strain 1.5 x 1.6 x 0.40 / 10.5^2 = 0.87 % nominal, x Kt 1.5 (gusset) = 1.31 %.
#     (11.0 put the hk4 tip 0.25 into the rear-wall block below z 86.55; 10.5 leaves 0.25 above it.)
# FIXER r2 (verifier M-V-MPS-6, lug class 1.6): land 0.6 -> 1.0 (tooth root 1.65; 1.62 at the probe 0.03 in), catch
#     plane and tub ledges up 0.4 (catch_z 88.15 -> 88.55, tooth top 88.05 -> 88.45); ledge_h 1.6 -> 1.7 (1.65 at the
#     0.05 probe under the 45 deg top chamfer). Beam length 10.5 and the hk4 tip clearance unchanged.
# FIXER r2 (verifier M-V-MPS-2, hood service): hk1/hk2 keep the 90 deg positive catch and get a dia 1.6 RELEASE HOLE
#     through the right wall at the tooth (z 87.7, under the ledge): a dia 1.5 pin pushed straight in from the right
#     deflects the tooth 0.55 (0.15 clear of the ledge) and stays in by friction (hold-open), one hook at a time.
#     hk3/hk4 (front/rear walls, no straight access from outside that does not cross the hood) get a 45 deg RETURN
#     catch: they cam out on a straight lift once hk1/hk2 are held open (same 0.4 deflection as on insertion). In use
#     the hood is held by hk1/hk2 (positive) + the J2 panel tongue (left edge) + hk3/hk4 (45 deg return).
HOOK = dict(length=10.5, t=1.6, w=8.0, tooth=0.65, land=1.0, lead_deg=45.0, catch_z=88.55, tooth_top_z=88.45, ledge=0.8,
            ledge_h=1.7, play=0.1, max_strain=0.025)
HOOD_RELEASE = dict(hole_d=1.6, pin_d=1.5, z=87.7, push=0.55,
                    tool='2 x dia 1.5 steel pins (dowel ISO 8734 1.5 x 16, or the shank of a 1.5 mm drill)')
HOOD_HOOKS = [   # id, wall, station (x or y along the wall), inward normal of the wall face (tooth points against it)
    dict(id='hk1', wall='right', x=-45.0, y_face=Y_RW_IN, normal=(0, 1, 0), ret_deg=0.0, release_hole=True),
    dict(id='hk2', wall='right', x=-125.0, y_face=Y_RW_IN, normal=(0, 1, 0), ret_deg=0.0, release_hole=True),
    dict(id='hk3', wall='front', y=22.0, x_face=X_FW_IN, normal=(-1, 0, 0), ret_deg=45.0, release_hole=False),
    dict(id='hk4', wall='rear', y=-20.0, x_face=X_RW_IN, normal=(1, 0, 0), ret_deg=45.0, release_hole=False),
]
# beam outer face = wall face + ledge + SLIDE along the normal; the tooth overlaps the ledge by 0.55

# --- J2 panel -> hood (and the "rebate holding the hood's left edge"): the panel top tongue (concept panel_tongue)
#     enters a groove in a rail block under the hood band's left edge as the panel goes on along -Y.
PANEL_TONGUE = B(-134.0, -12.0, 26.0, SPLIT, 92.0, 94.6)       # CHANGED x -142..-12 -> -134..-12 (EVF board slot)
HOOD_RAIL = dict(box=B(-134.5, -11.5, 23.9, 32.0, 90.0, ZT1),   # FIXER P4: z0 90.15 -> 90.0 keeps the lip 1.6
                 # rail block on the band underside (hood); y0 25.5 -> 23.9
                 piers=[(x, x + 3.0) for x in (-134.5, -110.5, -86.5, -62.5, -38.5, -14.5)],   # INTEGRATOR (J2 bridges)
                 groove=B(-134.5, -11.5, 25.75, 32.0, 92.0 - 0.4, 94.6 + SL),   # FIXER P4: 0.4 under the tongue (bridged floor)   # open toward +Y; ends open
                 lower_lip_outer_chamfer_deg=45.0)            # the lip under the groove: 45 deg outer face (print)
# panel top edge z 97.0 under the band (seam 0.3), outer faces flush at y 35.

# --- J3 panel -> tub: the panel inner face bears on the tub front/rear wall end faces at y = SPLIT (declared
#     contact). 2 locating ribs (1.2 thick, 30 long, LOCATE) on the panel inner face sit inside the front and
#     rear walls. The 2 panel bosses pass the tub lip through 2 notches; their tabs fill the notches flush (R2: no
#     skirt covers them any more).
PANEL_LOCATE_RIBS = [B(X_FW_IN - LO - 1.2, X_FW_IN - LO, 24.0, SPLIT, 41.3, 70.0),   # INTEGRATOR z0 40 -> 41.3 (rib_l)
                     B(X_RW_IN + LO, X_RW_IN + LO + 1.2, 24.0, SPLIT, 20.0, 50.0)]
LIP_NOTCHES = [B(x - 4.3, x + 4.3, SPLIT, YL, T, 7.9) for x in (cx(-14.0), cx(-28.0))]

# --- J4 base -> tub: 2 keyhole T-tongues under the tub floor (tub) drop through windows in the base top and slide
#     10 mm BACK relative to the base (the base slides 10 mm forward) under 1.6 mm lips. Then 2 x PT screws lock it.
#     CHANGED: tongue_f x 48 (concept) -> -18.0 D2 (= concept 59), clear of the run-lead and pigtail floor holes;
#     tongue 8 long (concept 6); T head 36 wide, neck 26 (concept one 48 x 2.7 block).
BASE_SLIDE = 10.0
TONGUE = dict(length=8.0, neck_w=26.0, neck_h=1.85, head_w=36.0, head_h=1.8, minus_y_end_chamfer_deg=45.0)
TONGUES = [dict(id='tongue_f', x=-18.0), dict(id='tongue_r', x=cx(-2.0))]          # final x centres (-18, -79)
for _t in TONGUES:
    xc = _t['x']
    _t['neck'] = B(xc - 4.0, xc + 4.0, -13.0, 13.0, -1.85, 0.0)
    _t['head'] = B(xc - 4.0, xc + 4.0, -18.0, 18.0, -3.65, -1.85)
    _t['base_lips_z'] = (-1.6, 0.0)
    _t['base_neck_slot'] = B(xc - 4.25, xc + 4.25 + BASE_SLIDE, -13.25, 13.25, -1.6, 0.0)
    _t['base_pocket'] = B(xc - 4.25, xc + 4.25 + BASE_SLIDE, -18.25, 18.25, -3.9, -1.6)
    _t['base_window'] = B(xc + BASE_SLIDE - 4.25, xc + BASE_SLIDE + 4.25, -18.25, 18.25, -1.6, 0.0)
del _t, xc

# --- J5 ELIMINATED (R2, finding 3; record only, no part uses it). Was: skirts -> base, separate strips: each skirt slid +X into a 45-deg dovetail groove
#     in the base side face (closed at the front, x -1.5) and clicks a barb at its rear end. SKIRT_JOINT deleted (r2).

# --- J6 cap -> grip: slides +X (forward) to open, 2 dovetail rails (45 deg) along the grip side walls at the bottom,
#     detent bump 0.4 high near the rear; closed stop = a lip on the grip rear wall.
CAP_JOINT = dict(rail_z=(-108.6, -105.55),   # R2: top -106.25 -> -105.65 (FIXER r2: -105.55); grooves in the bay side walls, closed at x -60
                 rail_depth=1.2, dovetail_deg=45.0, detent_h=0.4, clearance=SL)

# --- J7 camera -> tub (CHANGED: GS camera stack per the stills R1 record, see SPEC s9; camera now goes in AFTER the
#     hood, from the open left side, then +X onto 2 pins).
CAM = dict(
    seat_x=X_FW_IN,                       # lands face on the front-wall inner face (declared contact)
    lands=39.5, depth=19.27,              # 39.5 sq lands/PCB/cover, 19.27 deep -> cover rear x -24.47
    ring=CYL('x', 0.0, 60.0, 18.0, X_FW_IN, X_FW_IN + 5.8),          # back-focus ring Ø36 (rotates; never clamped)
    cs_ring=CYL('x', 0.0, 60.0, 15.375, X_FW_IN + 5.8, X_FW_IN + 10.8),  # Ø30.75; CS flange x +5.6
    c_adapter=CYL('x', 0.0, 60.0, 15.0, X_FW_IN + 10.8, X_FW_IN + 15.8),  # C-CS adapter 5 mm (OD 30 estimate)
    holes=[(-15.0, 45.0), (15.0, 45.0), (-15.0, 75.0), (15.0, 75.0)],    # (y, z), Ø2.2 (stills R1; palette says 2.7)
    pins=[(-15.0, 75.0), (15.0, 45.0)],   # 2 diagonal printed pins; INTEGRATOR T1: other diagonal (CS ring clears)
    pin_d=1.9, pin_len=3.0, pin_tip_chamfer=0.4,
    wall_bore_d=36.5,                     # front wall, hood plate and turret: Ø36.5 (0.25 round the Ø36 ring)
    keeper=B(-28.0, X_FW_IN - 19.27 - 0.2, 4.0, SPLIT, 66.0, 76.0),   # panel finger, 0.2 behind cover
    insert=dict(start_dx=-11.1, path='-Y through the open left side 2 mm high, down 2 at y 0, then +X 11.1'),
)
CAM['rear_x'] = X_FW_IN - CAM['depth']    # -24.47
C_FLANGE_X = X_FW_IN + 15.8               # +10.6 C-mount flange (CHANGED from concept +9.5: lens 1.1 forward)
CS_FLANGE_X = X_FW_IN + 10.8              # +5.6
# 2 load ribs (tub): rib_l x -13..-5.2, y 24.1..27.4, z 2.5..41 (CHANGED top 45 -> 41: the camera ring passes over it);
# rib_r x -15..-5.2, y -32.5..-23.6, z 41..80 (CHANGED: grown from the right wall, printable). Both print-safe (s5).
RIBS = {'rib_l': B(-13.0, X_FW_IN, 24.1, SPLIT, T, 41.0)}
# INTEGRATOR T3/T4: rib_r deleted (it lay over the Pi stack drop path); rib_l is a 45 deg gusset out to the panel plane

# --- J8 EVF (EVF-A: 0PE039-16X + HMX039 + Hicenda board). Flange datum F on the tub rear outer face (declared contact;
#     CHANGED F -154.2 -> -154.0). The eyepiece goes in from the rear along +X through the open housing (after the
#     hood); the spigot locates in a 29.3 bore (rear wall + inner half-collar, tub) and is clamped by the panel cap
#     (+Y half, r 14.4 = 0.1 crush). Never a printed thread. Bench gate G-EVF-1: pull-out >= 20 N, diopter turns freely.
F_EVF = X_REAR                               # -154.0
EVF = dict(
    F=F_EVF, axis=EYE_AXIS,
    barrel=CYL('x', 16.0, 78.0, 19.25, F_EVF - 20.3, F_EVF),          # dia 38.5, F to the eye lip (x -174.3)
    spigot=CYL('x', 16.0, 78.0, 14.5, F_EVF, F_EVF + 4.5),            # M29x0.75 x 4.5
    display_x=F_EVF + 6.0,                                            # -148.0 OLED emitter plane (nominal)
    bore_d=29.3, collar=B(X_RW_IN, F_EVF + 4.4, -0.5, 16.0, 61.0, 95.0),   # -y half-collar (tub), x -151.5..-149.6
    cap=B(-151.4, -145.0, 24.0, SPLIT, 63.0, 93.0),                   # panel cap envelope (U face r 14.4 + OLED finger)
    cap_clamp_r=14.4,
    oled=B(F_EVF + 6.0, F_EVF + 6.0 + 1.93, 16.0 - 7.8, 16.0 + 7.8, 78.0 - 6.8, 78.0 + 6.8),   # 15.6 x 13.6 x 1.93
    oled_cell=dict(pocket=B(F_EVF + 6.0, F_EVF + 9.0, 16.0 - 7.95, 16.0 + 8.0, 78.0 - 6.95, 78.0 + 6.95),
                   front_ledge_w=1.0, window=(10.0, 8.0), open_side='+y',
                   pad='1.0 mm closed-cell foam behind the panel (x -146.07..-145.07)'),
    board=B(-144.8, -136.8, 1.0, 28.0, 64.0, 92.5),                   # Rev I 28.5 x 27, 6-8 thick (estimate)
    board_pcb_x=(-138.4, -136.8),                                     # PCB plane; parts face -X (toward the OLED)
    board_slot=dict(groove_w=1.6 + 2 * SL, groove_depth=1.5, top_z=92.5, bottom_z=64.0, stop_y=0.7,
                    bottom_rail_gaps=[(4.0, 17.0)], open_side='+y',   # gap for the micro-HDMI plug
                    gap_clear=1.0, plug_x_clear=0.6, zif_relief=0.4),
    # FIXER r2 (M-V-MPS-3): bottom rail cut back 1.0 round the receptacle/plug (y 3.0..18.0); in that gap the +X spine
    # stands 0.6 off the plug envelope's +X face below the groove (and grows 0.65 outward, 1.6 wide); the top rail's
    # -X groove wall is relieved 0.4 on its underside over the ZIF (y 6..21) so neither stops the board before the PCB
    diopter_clear=1.25,                                               # radial, round the rotating knurl
    cup_lip_x=X_REAR - 33.6,                                          # -187.6 TPU cup lip (33.6 proud)
)
EYECUP = dict(box=B(-187.6, F_EVF - 20.3 + 3.0, 16.0 - 23.0, 16.0 + 23.0, 78.0 - 23.0, 78.0 + 23.0), r_lip=23.0,
              r_base=19.4, r_in=12.5, sleeve=dict(x=(F_EVF - 20.3, F_EVF - 20.3 + 3.0), r_in=18.05, wall=1.6),
              grip_on='sleeve over the eyepiece eye-end body (dia 36.7, repo) x -174.3..-171.3, 0.3 interference '
                      '(TPU); 1.1 mm short of the housing end (x -170.2)')

# --- R1 J9 (owner R1, r2 finding 1; R1 edits this block)
# --- J9 Pi stack -> tub: 4 floor bosses (OD 8.8, top z 6.0; head pockets 5.6 x 2.4 locate the kit screw heads in
#     x/y) carry and locate the stack: these are its positive locating surfaces. r2 (R1): a removable printed keeper
#     (pi_keeper) on 2 x PT 3.0 x 12 PH1 (s_k1, s_k2, into 2 tub bosses) holds it down. Its 4 fingers reach 0.65
#     over the X1203 top at the r1 hook stations (2 USB edge, 2 port edge; the GPIO edge is 0.2 from the right wall
#     and the button edge 0.8 from the front wall: no room there), 0.1 above the X1203 and 0.25 off its edges, so the
#     keeper carries no positioning load. r1's 4 floor snap hooks are DELETED (no release access: removal broke the
#     tub). Bench gate G-PI-1: X1203 edge parts clear of the 4 finger zones.
PI = dict(x=(cx(-14.0), cx(71.0)), y=(-32.3, 23.7),                   # -91 (USB end) .. -6 (button end)
          x1203_z=(6.0, 7.6), pcb_z=(18.5, 20.1), cooler_top=36.3)
PI['holes'] = [(x, y) for x in (PI['x'][1] - 3.5, PI['x'][1] - 61.5) for y in (PI['y'][0] + 3.5, PI['y'][1] - 3.5)]
PI_BOSS = dict(od=9.0,   # INTEGRATOR T4: 7.0 left a 0.7 wall round the 5.6 head pocket; R1 r2: 8.8 -> 9.0 (wall 1.7)
                z=(T, 6.0), head_pocket_d=5.6, head_pocket_depth=2.4)
PI_HOOK = dict(t=1.6, w=6.0, root_z=1.2, form='45 deg leaning slab (tub owner); strain: snap_strains()',
               top_z=9.0, tooth=0.9, land=0.4, catch_z=7.7, lead_deg=45.0, gap=SL,
               max_strain=0.03, root_pocket='1.5 deep floor relief round the root so the beam is 6.7+ long')
# reach over the board = tooth - gap = 0.65; FIXER P6: strain from snap_strains() (leaning slab, t 1.6, root z 1.2):
# 1.5 x 1.6 x (0.65 x sqrt2) / ((7.7 - 1.2) x sqrt2)^2 = 2.61 % nominal (one-time class, bench gate G-SNAP-1)
PI_HOOKS_R1 = [dict(id='pih1', edge='usb', face=('x', PI['x'][0]), at=-20.0, normal=(1, 0, 0)),     # r1 record
               dict(id='pih2', edge='usb', face=('x', PI['x'][0]), at=12.0, normal=(1, 0, 0)),
               dict(id='pih3', edge='port', face=('y', PI['y'][1]), at=-80.0, normal=(0, -1, 0)),
               dict(id='pih4', edge='port', face=('y', PI['y'][1]), at=-45.0, normal=(0, -1, 0))]
PI_HOOKS = []          # R1 r2: the hooks are deleted (PI_HOOK above stays only as the r1 record); see PI_KEEPER
# PI_KEEPER (printed_keeper.py builds it, printed_tub.py builds its 2 bosses). One flat top (z 15.6, on the bed in
# print), body underside z 9.8 on the 2 boss tops. USB arm along the USB edge (runs under the stick-guide rail,
# z 17.15); bridge z >= 12.5 over the panel bosses boss_b1/b2 (z <= 12.0; the panel goes on later along -Y); port bar
# along the port edge (y to 31.9 = panel face 32.2 - SEAM). Fingers: block 2.5 deep from the arm/bar face down to
# z 7.7 (X1203 top 7.6 + 0.1), tip reaching 0.65 over the board edge, 1.6 thick with a 45 deg back. Bosses: the tub
# prints right wall down (+Y up), so each boss is a teardrop (chin toward -Y); s_k2's chin apex stops at y 23.95
# (0.25 off the X1203 edge), which sets its centre y 28.9 with r 3.5 and a 1.0 long obround along X (walls >= 2.25).
# s_k1 head in a counterbore, s_k2 head on a spot-face notch across the bar. Insertion (keeper_in): from the open left
# side 0.5 high and 1.2 back, -Y 60, +X 1.2 (the USB fingers go under the Pi), down 0.5; removal is the exact reverse.
PI_KEEPER = dict(
    gap_z=0.1, gap_xy=SL, reach=0.65, tip_t=1.6, finger_w=6.0, finger_block=2.5, under_z=9.8, top_z=15.6,
    arm=B(-105.0, PI['x'][0] - SL, -23.0, 23.85, 9.8, 15.6),
    bridge=B(-105.0, -86.0, 23.85, 31.9, 12.85, 15.6),   # FIXER r2: z0 12.5 -> 12.85 (boss tops 12.6 + SLIDE)
    bar=B(-86.5, -41.0, PI['y'][1] + SL, 31.9, 9.8, 15.6),
    fingers=[dict(id='kf1', edge='usb', at=-20.0), dict(id='kf2', edge='usb', at=12.0),      # = r1 pih1..pih4 stations
             dict(id='kf3', edge='port', at=-80.0), dict(id='kf4', edge='port', at=-45.0)],
    bosses={'s_k1': dict(c=(-99.5, 16.0), r=3.8, obround=0.0, clip_y=None),
            's_k2': dict(c=(-64.0, 28.25), r=3.6, obround=1.0, clip_y=31.9, chin_y=23.95)},
    # FIXER r2 (verifier M-V-MPS-1): s_k2 centre y 28.9 -> 28.25 so the +Y wall above the lip gusset (z 7.6..9.8) is
    #     min(r 3.6, 31.9 - 28.25) - 1.25 = 2.35 (was 1.75; PT rule 2.25; r 3.5 left exactly 2.25); the teardrop chin
    #     is cut flat at y 23.95 (0.25 off the X1203 edge): a 2.6 wide flat, bridged in print (+Y up). Engage 7.5.
    boss_top=9.8, pilot_bottom_z=1.2, head_z=14.3, cbore_d=7.0, notch_x=7.0,
    path=[(-1.2, 60.0, 0.5), (-1.2, 0.0, 0.5), (0.0, 0.0, 0.5), (0.0, 0.0, 0.0)])
# --- R1 J9 end
# beam inner face = board edge + gap along -normal; tooth tip reaches 1.0 past the edge over the board.
PI_BUTTON = dict(x_face=PI['x'][1] + 0.45, y=PI['y'][1] - 18.4, z=21.0, travel=0.45)    # -5.55, y 5.3 (z estimate)
PI_LED = dict(y=PI['y'][1] - 13.3, z=20.8)
FLOOR_HOLES = {'run_lead': B(-34.0, -28.0, 1.5, 9.0, 0.0, T),
               'pigtail': B(-45.0, -34.0, -13.0, -4.0, 0.0, T)}      # CHANGED 7 x 7 -> 11 x 9: the XT30 passes

# --- J10 power plunger (natural ASA light pipe) -> hood + tub. CHANGED: flange pocket in the hood plate, face 1.3
#     behind the plate face (concept 2.5); axis y 9.0, z 20.5 to clear the SD slot and the exhaust band.
PLUNGER = dict(
    axis=(9.0, 20.5),
    stem=B(-5.0, -1.3, 3.5, 14.5, 17.5, 23.5),             # 11 x 6; front face = finger face at x -1.3
    nib=CYL('x', PI_BUTTON['y'], PI_BUTTON['z'], 1.25, -5.3, -5.0),   # presses the button (0.25 gap at rest)
    flange=B(-2.5, -1.3, 9.0 - 6.8, 9.0 + 6.8, 20.5 - 3.9, 20.5 + 3.9),   # 13.6 x 7.8 x 1.2 (INTEGRATOR: MIN_WALL; tub recess 0.4)
    travel=0.6,                                            # flange stops on the floor of a 0.4 recess in the tub (x -3.1)
    hood_pocket=B(-2.5, -1.3, 9.0 - 7.1, 9.0 + 7.1, 0.3, 20.5 + 4.2),   # INTEGRATOR: channel open at the plate foot
    hood_opening=B(-1.3, 0.0, 9.0 - 5.8, 9.0 + 5.8, 20.5 - 3.3, 20.5 + 3.3),   # 11.6 x 6.6 (guard lip 1.3)
    tub_hole=B(X_FW_IN, XT1, 9.0 - 5.8, 9.0 + 5.8, 20.5 - 3.3, 20.5 + 3.3),    # 11.6 x 6.6 through the front wall
)
SD_SLOT = B(X_FW_IN, X_FRONT, -11.5, 0.5, 15.9, 18.6)       # through the tub front wall and the hood plate

# --- J11 USB stick -> tub: rear scoop (finger recess 10 deep) + guide channel to the USB3 port (middle column, lower).
STICK = dict(axis=(-5.3, 24.4), body=B(-153.0, -94.0, -5.3 - 10.65, -5.3 + 10.65, 24.4 - 5.7, 24.4 + 5.7),
             plug=B(-94.0, -82.0, -5.3 - 6.0, -5.3 + 6.0, 24.4 - 2.25, 24.4 + 2.25))
STICK_SLEEVE = dict(box=B(X_REAR, -138.0, -5.3 - 11.45, -5.3 + 11.45, 24.4 - 6.5, 24.4 + 6.5), wall=0.8,
                    end_flush_x=X_REAR, note='covers the slider in its out position (lock) + pull lip')
SCOOP = B(X_REAR, X_REAR + 10.0, -5.3 - 14.5, -5.3 + 14.5, 24.4 - 10.0, 24.4 + 10.0)   # opening in the rear wall
STICK_GUIDE = dict(x=(-148.6, -94.5), sleeve_section=(11.45 + SL, 6.5 + SL), stick_section=(10.65 + SL, 5.7 + SL),
                   sleeve_until_x=-138.0)                                              # half-widths (y, z)

# --- J12 panel controls. Encoder: Adafruit 5880 (PCB 25.6 x 25.3) in a 2-hook snap cradle; bushing hole 7.5.
ENCODER = dict(c=(EXP_X, DIAL_Z), pcb=B(EXP_X - 12.65, EXP_X + 12.65, 24.1, 25.7, DIAL_Z - 12.8, DIAL_Z + 12.8),
               body=B(EXP_X - 6.25, EXP_X + 6.25, 25.7, SPLIT, DIAL_Z - 6.75, DIAL_Z + 6.75),
               bushing=CYL('y', EXP_X, DIAL_Z, 3.5, SPLIT, SPLIT + 5.0),
               shaft=CYL('y', EXP_X, DIAL_Z, 3.0, SPLIT + 5.0, 44.0), shaft_flat=4.5,
               back_parts=B(EXP_X - 12.65, EXP_X + 12.65, 18.8, 24.1, DIAL_Z - 12.8, DIAL_Z + 12.8),
               panel_hole_d=7.5, i2c=0x37,
               cradle_hooks=dict(top=dict(z=DIAL_Z + 12.8, w=8.0), sides=dict(z=(45.0, 50.0), w=5.0), tooth=0.40,   # FIXER P2: reach 0.55 -> 0.40
                                 play=0.1, note='INTEGRATOR (hood_panel 5): no hook under the PCB (ko_hdmi_run); G-ENC-1'))
SWITCH_1824 = dict(c=(FPS_X, DIAL_Z), body=CYL('y', FPS_X, DIAL_Z, 12.5, 19.2, SPLIT),
                   bushing=CYL('y', FPS_X, DIAL_Z, 4.75, SPLIT, SPLIT + 6.0),
                   shaft=CYL('y', FPS_X, DIAL_Z, 3.175, SPLIT + 6.0, 42.0),   # INTEGRATOR: cut to y 42.0 at step 2
                   nut=dict(af=12.7, t=2.4, y=(YL, YL + 2.4)), panel_hole_d=10.0,
                   anti_rot=dict(r=7.9, angle_deg=0.0, tab=(1.2, 2.5, 1.5), slot=(1.7, 3.0, 2.0)))   # slot in the panel
KNOBS = {'knob_exp': dict(c=(EXP_X, DIAL_Z), d=28.0, y=(YL + 0.2, YL + 9.2), bore='D 6.0/4.5', knurl=60),
         'knob_fps': dict(c=(FPS_X, DIAL_Z), d=20.0, y=(YL + 0.2, YL + 7.2), bore='D 6.35/4.8', index_deg=45.0,
                          nut_recess=(16.0, 3.0))}

# --- J13 grip: run button, tripod nut, strap, base opening.
RUN_BTN = dict(body=B(-35.0, -26.5, -6.0, 6.0, -27.5, -14.5), cap=CYL('x', 0.0, -21.0, 6.5, -26.5, -20.5),
               wall_hole_d=13.6, pad=dict(y=(-6.0, 6.0), z=(-35.0, -7.0), depth=1.5))   # pad recessed in the grip face
BASE_OPENING = B(-45.0, -25.5, -13.0, 9.0, -8.0, 0.0)      # switch drop-in, run lead and pigtail (under the floor)
TRIPOD = dict(x=cx(-30.0), y=0.0, nut_af=11.1, nut_t=5.6, nut_z=(-5.7, -0.1), pocket_af=11.4, hole_d=6.6,
              bearing_wall=2.3)                            # CHANGED nut z (concept -7.2..-1.6): 2.3 bearing wall
STRAP = dict(width=12.0, upper_slots=[B(x - 1.75, x + 1.75, -34.0, -21.0, -8.0, 0.0) for x in (-76.5, -82.0)],
             upper_recess=B(-82.0, -76.5, -34.0, -21.0, -2.0, 0.0),
             lower_slots=[B(GRIP['x'][0], GRIP['x'][0] + 2.5, -8.5, 4.5, z - 1.75, z + 1.75) for z in (-104.0, -97.0)])
# R2: heel slots y -14..-1 -> -8.5..4.5 (13 wide, same 12 mm webbing): in the er 9 rear corner the old slots ended
#     blind against the curved bay wall, leaving 0.5-1.0 skins at the strap anchor (r2 trial screen 0.97)

# --- J14 vents (slot width 2.0, web >= 1.4). Hood roof inlet over the blower; exhaust through the tub front wall
#     (one window each) and the hood plate slots; right-wall slots (tub).
VENTS = {
    'inlet_roof': dict(part='hood', face='+z', box=B(cx(19.0) - 13.0, cx(19.0) + 13.0, -24.0, 4.0, ZT1, H),
                       slot_w=2.0, pitch=3.6, slot_along='y'),
    'out_band': dict(part='hood', face='+x', box=B(-2.5, 0.0, -26.5, 17.5, 25.9, 29.7), slot_w=2.0, pitch=3.4,
                     slot_along='z', tub_window=B(X_FW_IN, XT1, -26.5, 17.5, 25.9, 29.7)),
    'out_corner': dict(part='hood', face='+x', box=B(-2.5, 0.0, -31.0, -21.0, 32.0, 38.0), slot_w=2.0, pitch=3.4,
                       slot_along='z', tub_window=B(X_FW_IN, XT1, -31.0, -21.0, 32.0, 38.0)),
    'out_wall': dict(part='tub', face='-y', box=B(-19.0, -5.0, YR, Y_RW_IN, 21.0, 37.0), slot_w=2.0, pitch=3.4,
                     slot_along='z'),
    'x1203': dict(part='tub', face='-y', box=B(cx(20.0) - 8.0, cx(20.0) + 8.0, YR, Y_RW_IN, 9.5, 17.5), slot_w=2.0,
                  pitch=4.4, slot_along='z'),
}
# INTEGRATOR T3: BAFFLE deleted. Its box lay over the Pi PCB edge (x -6.0), so any wall there blocks the stack drop.
# The exhaust is the 2 front-wall windows + the right-wall slots; ko_exhaust stays clear as the plenum.
THIN_OK = {'stick_sleeve': dict(min=0.8, reason='non-structural slider cover; 0.8 >= MIN_FEATURE; a 1.2 wall changes '
                                'the tub stick channel section (STICK_GUIDE)')}

# --- J15 engraving (panel face, 0.4 deep, paint-filled). pol(): angle 0 = up, positive = clockwise seen from +Y
#     (toward -X). Text min height 3.0 on the bed face (CHANGED from 2.2/2.7: 0.4 nozzle).
def pol(c, r, deg):
    a = math.radians(deg)
    return (round(c[0] - r * math.sin(a), 3), round(c[1] + r * math.cos(a), 3))


ENGRAVE = dict(
    face_y=YL, depth=FDM['ENGRAVE_DEPTH'], font='DejaVu Sans (bold for digits)',
    items=[
        dict(id='exp_arc', kind='arc', c=(EXP_X, DIAL_Z), r=17.0, deg=(-100.0, 100.0), stroke=0.9),
        dict(id='exp_ticks', kind='ticks', c=(EXP_X, DIAL_Z), r=(15.8, 18.2), deg=[-100.0, 100.0], stroke=0.9),
        dict(id='exp_arrows', kind='arrowheads', c=(EXP_X, DIAL_Z), r=17.0, deg=[-100.0, 100.0], size=(2.4, 1.3), stroke=0.9),
        dict(id='exp_m', kind='text', at=pol((EXP_X, DIAL_Z), 22.5, -112.0), text='-', h=3.4),
        dict(id='exp_p', kind='text', at=pol((EXP_X, DIAL_Z), 22.5, 112.0), text='+', h=3.4),
        dict(id='exp_lbl', kind='text', at=(EXP_X, DIAL_Z - 20.5), text='exposure', h=3.0),
        dict(id='fps_ticks', kind='ticks', c=(FPS_X, DIAL_Z), r=(11.6, 14.2), deg=[-45.0, 45.0], stroke=1.2),
        dict(id='fps_18', kind='text', at=pol((FPS_X, DIAL_Z), 18.0, -45.0), text='18', h=3.0),
        dict(id='fps_24', kind='text', at=pol((FPS_X, DIAL_Z), 18.0, 45.0), text='24', h=3.0),
        dict(id='badge', kind='text', at=(-26.0, ZT1 - 10.0), text='GS8', h=3.8),
    ])

# =============================================================================== 4. the 4 PT screw stations
PT = dict(spec='PT 3.0 x 12 thread-forming screw for plastics, pan head, PH1 (EJOT PT K30x12 WN 1411 class / '
               'Delta PT 30x12 class; confirm the head on receipt)',
          d=3.0, length=12.0, head_d=6.0, head_h=2.4, drive='PH1', pilot_d=2.5, clear_d=3.4, cbore_d=7.0,
          boss_od_min=7.0, boss_od=8.0, engage_min=7.0, tip_reserve=1.0,
          torque_Nm=(0.35, 0.5), reuse_max=5, insert_fallback='M3 heat-set (4.0 pilot x 6.7) + M3 x 10 pan A2')
DRIVER = dict(bit_d=6.5, bit_len=40.0, handle_d=30.0, handle_len=100.0, bit_d_range=(5.0, 6.5),
              handle_d_range=(28.0, 30.0))
# head_point = the face the screw head bears on; axis = direction the screw advances; the driver comes from
# head_point - axis * (bit_len + handle_len). engage = thread length inside the boss.
SCREWS = [
    dict(id='s_b1', joins=['base_grip', 'tub'], into='panel boss_b1', head_part='base_grip', axis=(0, 0, 1),
         head_point=(cx(-14.0), 27.85, -2.0), tip=(cx(-14.0), 27.85, 10.0), engage=7.4, step=8,
         cbore=dict(part='base_grip', d=7.0, z=(-8.0, -2.0)), note='up through a 6 mm counterbore; boss z 2.6..12'),
    dict(id='s_b2', joins=['base_grip', 'tub'], into='panel boss_b2', head_part='base_grip', axis=(0, 0, 1),
         head_point=(cx(-28.0), 27.85, -2.0), tip=(cx(-28.0), 27.85, 10.0), engage=7.4, step=8,
         cbore=dict(part='base_grip', d=7.0, z=(-8.0, -2.0)), note='as s_b1'),
    dict(id='s_r1', joins=['tub'], into='panel post_f', head_part='tub', axis=(0, 1, 0),
         head_point=(-31.5, -32.4, 85.5), tip=(-31.5, -20.4, 85.5), engage=10.0, step=8,
         cbore=dict(part='tub', d=7.0, y=(YR, -32.4)), note='from the right; wall + 2.0 pad (y -35..-30.5)'),
    dict(id='s_r2', joins=['tub'], into='panel post_r', head_part='tub', axis=(0, 1, 0),
         head_point=(cx(-66.5), -32.4, 47.5), tip=(cx(-66.5), -20.4, 47.5), engage=10.0, step=8,
         cbore=dict(part='tub', d=7.0, y=(YR, -32.4)), note='as s_r1'),
]
PANEL_BOSSES = {'boss_b1': B(cx(-14.0) - 4.0, cx(-14.0) + 4.0, 24.1, SPLIT, 2.6, 12.6),     # CHANGED 7 -> 8 wide
                'boss_b2': B(cx(-28.0) - 4.0, cx(-28.0) + 4.0, 24.1, SPLIT, 2.6, 12.6)}
# FIXER r2 (verifier M-V-MPS-6, boss class 1.6): boss top 12.3 -> 12.6 (cap over the pilot end 1.6); the keeper bridge
#     underside goes 12.5 -> 12.85 so the panel bosses still slide under it at SLIDE 0.25 (M-V-MPS-8).
# R2: boss top 12.0 -> 12.3 so the cap over the blind pilot end (z 11.0) is 1.3, not 1.0 (r2 trial thin-wall screen)
PANEL_POSTS = {'post_f': B(-35.5, -27.5, -30.4, SPLIT, 81.5, 89.5),                         # CHANGED 7 -> 8 square
               'post_r': B(cx(-66.5) - 4.0, cx(-66.5) + 4.0, -30.4, SPLIT, 43.5, 51.5)}
RIGHT_WALL_PADS = {'pad_r1': dict(c=(-31.5, 85.5), d=12.0, y=(Y_RW_IN, -30.5)),
                   'pad_r2': dict(c=(cx(-66.5), 47.5), d=12.0, y=(Y_RW_IN, -30.5))}
X1203_KIT = dict(standoff='4 x M2.5 F-F hex 5 AF brass, 10.9 long (stack gap estimate; kit length on receipt)',
                 screws='8 x M2.5 x 5 pan, PH (kit): 4 down through the Pi, 4 up through the X1203',
                 head=(4.5, 1.75), torque_Nm=0.2, standoff_z=(PI['x1203_z'][1], PI['pcb_z'][0]))

# =============================================================================== 5. lens (swappable by parameter)
LENS = 'kowa_lm6hc'                       # 'kowa_lm6hc' (default) | 'fujinon_hf6xa'
LENSES = {
    'kowa_lm6hc': dict(name='Kowa LM6HC 6 mm f/1.8 1in C-mount', mass=215.0, com_from_flange=28.3,
                       src='datasheet: Baumer ZVL-LM6HC, dia 54 x 56.6 from the flange, <= 215 g',
                       segments=[(12.7, -4.5, 0.0, 'C thread 1in-32'), (25.5, 0.0, 5.0, 'rear'),
                                 (27.0, 5.0, 15.0, 'iris ring'), (26.0, 15.0, 23.0, 'mid'),
                                 (27.0, 23.0, 45.0, 'focus ring'), (26.5, 45.0, 56.6, 'front')],
                       lock_screws=[dict(x_from_flange=10.0, y=-28.8, d=5.2, len=4.0),
                                    dict(x_from_flange=34.0, y=-28.8, d=5.2, len=4.0)]),
    'fujinon_hf6xa': dict(name='Fujinon HF6XA-5M 6 mm C-mount', mass=100.0, com_from_flange=25.3,
                          src='repo: PALETTE.md dia 39 x 51, 100 g',
                          segments=[(12.7, -4.5, 0.0, 'C thread 1in-32'), (19.5, 0.0, 51.0, 'body')],
                          lock_screws=[]),
}


def lens_spec(name=None):
    """Lens dict with absolute x ranges: segments -> (r, x0, x1, label); com x."""
    d = dict(LENSES[name or LENS])
    d['segments_abs'] = [(r, C_FLANGE_X + a, C_FLANGE_X + b, lab) for r, a, b, lab in d['segments']]
    d['com'] = (C_FLANGE_X + d['com_from_flange'], 0.0, LENS_AXIS[1])
    return d

# =============================================================================== 6. COTS placements (proxies)
# id: name, pn/class, source tag, envelope box (assembly frame), mass g, step fitted, features/keep-outs.
# The cots owner models realistic shapes INSIDE each box (stills pattern) and adds the listed features.
PX0, PX1 = PI['x']
COTS = {
    'pi5': dict(name='Raspberry Pi 5 (4/8 GB)', pn='SC1111/SC1112', src='datasheet RP-008347', mass=46.0, step=4,
                box=B(PX0 - 3.0, PX1 + 0.45, PI['y'][0], PI['y'][1], 16.0, 36.1),
                features=dict(pcb=B(PX0, PX1, PI['y'][0], PI['y'][1], 18.5, 20.1),
                              jacks=B(PX0 - 3.0, PX0 + 18.0, PI['y'][0], PI['y'][1], 20.2, 36.1),
                              gpio=B(PX1 - 58.0, PX1 - 7.0, PI['y'][0], PI['y'][0] + 5.1, 20.2, 28.6),
                              hdmi0=dict(x=PX1 - 25.8, y_edge=PI['y'][1]), cam1=dict(x=(PX1 - 54.0, PX1 - 44.0)),
                              usbc=dict(x=PX1 - 11.2), button=PI_BUTTON, led=PI_LED, holes=PI['holes'],
                              underside=B(PX0, PX1, PI['y'][0], PI['y'][1], 16.0, 18.5))),
    'cooler': dict(name='Raspberry Pi Active Cooler', pn='SC1148', src='datasheet RP-008188', mass=25.0, step=1,
                   box=B(PX1 - 66.8, PX1 - 3.5, PI['y'][0] + 6.75, PI['y'][0] + 49.25, 20.2, 36.3),
                   features=dict(blower=B(PX1 - 66.8, PX1 - 36.8, -24.0, 4.0, 22.0, 36.3), fin_exit='+x')),
    'x1203': dict(name='Geekworm X1203 UPS (pogo pins, XH lead to any 1S pack)', pn='X1203', src='listing; height estimate',
                  mass=30.0, step=1, box=B(PX0, PX1, PI['y'][0], PI['y'][1], 6.0, 16.0),
                  features=dict(pcb=B(PX0, PX1, PI['y'][0], PI['y'][1], 6.0, 7.6), pads='battery pads: position open (Q2)')),
    'x1203_kit': dict(name='X1203 kit standoffs + screws', pn='kit', src='listing (estimate)', mass=6.0, step=1,
                      box=B(PX1 - 64.4, PX1 - 0.6, PI['y'][0] + 1.0, PI['y'][1] - 1.0, 4.25, 21.85), kit=X1203_KIT),
    'gs_camera': dict(name='Raspberry Pi Global Shutter Camera', pn='SC0926 class', src='stills R1 record s1.1-1.2',
                      mass=34.0, step=7, box=B(CAM['rear_x'], CS_FLANGE_X, -19.75, 19.75, 40.25, 79.75),
                      features=dict(ring=CAM['ring'], cs_ring=CAM['cs_ring'], holes=CAM['holes'], hole_d=2.2,
                                    fpc='15-pin 1 mm connector at the lower rear, FPC exits -X')),
    'c_cs_adapter': dict(name='C-CS adapter ring 5 mm (with the camera)', pn='kit', src='listing (OD estimate)',
                         mass=6.0, step=9, box=B(CS_FLANGE_X, C_FLANGE_X, -15.0, 15.0, 45.0, 75.0), cyl=CAM['c_adapter']),
    'lens': dict(name='C-mount lens (LENS parameter)', pn='see LENSES', src='see LENSES', mass=None, step=9,
                 box=B(C_FLANGE_X - 4.5, C_FLANGE_X + 56.6, -32.0, 27.0, 33.0, 87.0)),
    'eyepiece': dict(name='Display Components 0PE039-16X glass eyepiece', pn='0PE039-16X', src='repo EVF-SELECTION.md',
                     mass=35.0, step=6, box=B(F_EVF - 20.3, F_EVF + 4.5, 16.0 - 19.25, 16.0 + 19.25, 78.0 - 19.25, 78.0 + 19.25),
                     features=dict(barrel=EVF['barrel'], spigot=EVF['spigot'], eye_lip_x=F_EVF - 20.3)),
    'hmx039': dict(name='Hicenda HMX039-V1 micro-OLED + 50 mm flex', pn='HMX039 kit', src='repo', mass=2.0, step=6,
                   box=EVF['oled'], features=dict(flex_w=12.4, flex_len=50.4)),
    'evf_board': dict(name='Hicenda HDMI driver board Rev I', pn='HMX039 kit', src='repo; thickness estimate',
                      mass=8.0, step=6, box=EVF['board'], features=dict(pcb_x=EVF['board_pcb_x'], hdmi='lower edge, y 4..17')),
    'usb_stick': dict(name='SanDisk Extreme PRO USB 3.2 SSD stick', pn='SDCZ880', src='listing 71 x 21.3 x 11.4',
                      mass=22.0, step=9, box=B(STICK['body']['x'][0], STICK['plug']['x'][1], *STICK['body']['y'],
                                               *STICK['body']['z'])),
    'encoder': dict(name='Adafruit 5880 I2C QT rotary encoder (A0 bridged, 0x37)', pn='5880', src='listing; depth estimate',
                    mass=8.0, step=2, box=B(EXP_X - 12.65, EXP_X + 12.65, 18.8, 44.0, DIAL_Z - 12.8, DIAL_Z + 12.8),
                    features=ENCODER),
    'switch_1824': dict(name='mini 2-position rotary switch + nut + washer', pn='Lorlin CK1049 class', src='estimate',
                        mass=12.0, step=2, box=B(FPS_X - 12.5, FPS_X + 12.5, 19.2, 42.0, DIAL_Z - 12.5, DIAL_Z + 12.5),
                        features=SWITCH_1824),
    'run_button': dict(name='pre-wired momentary, red cap (Squid Button class)', pn='Pi Hut Squid', src='estimate',
                       mass=4.0, step=3, box=B(-35.0, -20.5, -6.5, 6.5, -27.5, -14.5), features=RUN_BTN),
    'pack': dict(name='1S2P 18650 pack, BMS, XT30 male lead, pull ribbon', pn='class', src='estimate', mass=105.0,
                 step=10, box=B(-64.5, -26.5, -10.0, 10.0, -108.8, -36.8)),
    'xt30_pair': dict(name='XT30 pair (pigtail female + pack male) + 180 mm 18 AWG pigtail', pn='XT30U', src='estimate',
                      mass=11.0, step=10, box=B(-63.0, -37.0, -5.1, 5.1, -20.0, -14.8)),   # INTEGRATOR: inside ko_xt30
    'tripod_nut': dict(name='1/4-20 UNC hex nut, steel', pn='ISO 4032 class', src='standard', mass=4.0, step=3,
                       box=B(TRIPOD['x'] - 6.4, TRIPOD['x'] + 6.4, -6.4, 6.4, *TRIPOD['nut_z'])),
    'strap': dict(name='12 mm hand strap with buckle', pn='class', src='estimate', mass=15.0, step=3,
                  box=B(-96.0, -70.0, -34.0, -21.0, -108.0, 0.0), note='exterior; passes the 4 strap slots'),
    'microsd': dict(name='microSD card (OS), 32 GB A2 class', pn='consumable class', mass=0.4, step=5,   # FIXER A-F2
                    src='PALETTE.md: protrudes ~2-3 mm past the Pi edge (2.5 used); socket part inside the pi5 underside '
                        'proxy is not modelled (proxy x -12.4..-3.5)',
                    box=B(PI['x'][1] - 6.4, PI['x'][1] + 2.5, -11.0, 0.0, 16.9, 17.9)),
    'pt_screws': dict(name='4 x PT 3.0 x 12 PH1', pn=PT['spec'], src='standard class', mass=3.2, step=8, box=None),
    'foam_pad': dict(name='closed-cell foam 16 x 14 x 1.0 (OLED pad)', pn='consumable', src='estimate', mass=0.1,
                     step=6, box=B(-146.07, -145.07, 8.2, 23.8, 71.2, 84.8)),
}
CABLES = [
    dict(id='fpc', name='Pi 5 22-to-15 FPC, 200 mm', frm='Pi 5 CAM/DISP 1 (port edge)', to='GS camera (lower rear)',
         via=['ko_fpc_up', 'ko_fpc_run', 'ko_fpc_loop', 'ko_fpc_cam'], length=200, steps=(4, 7)),
    dict(id='hdmi', name='micro-HDMI to micro-HDMI 200 mm, 90 deg up plug at the Pi', frm='Pi 5 HDMI0',
         to='EVF board lower edge', via=['ko_hdmi_pi', 'ko_hdmi_run', 'ko_hdmi_coil', 'ko_hdmi_evf'], length=200,
         steps=(4, 6)),
    dict(id='usb_5v', name='USB-A to 2-pin 5 V lead, 1N5817 in the + conductor, JST PH 2-pin junction at the board end',
         frm='Pi 5 upper USB 2 port', to='EVF board 5 V',
         via=['ko_usb_evf', 'ko_5v_up', 'ko_5v_end'], length=200, steps=(4, 6)),
    dict(id='oled_flex', name='OLED flex 50 mm (kit)', frm='HMX039', to='EVF board ZIF', via=[], length=50, steps=(6,)),
    # FIXER A-F1: header ends of qt, fps_lead and run_lead plug at step 4 (top open); the panel-side joints at step 8
    #   are the QT JST-SH at the encoder and a 2-pin JST PH inline junction on the 18/24 lead.
    dict(id='qt', name='STEMMA QT to female sockets 150 mm (Adafruit 4397)', frm='encoder', to='GPIO 1/3/5/6',
         via=['ko_qt_lead', 'ko_lead_wall', 'ko_lead_cross'], length=150, steps=(4, 8)),
    dict(id='run_lead', name='run button lead (pre-wired, Dupont)', frm='run button', to='GPIO26 + GND (pins 37/39)',
         via=['ko_run_drop', 'ko_run_floor', 'ko_run_rise', 'ko_run_cross', 'ko_lead_wall', 'ko_run_leads'], length=250,
         steps=(3, 4)),
    dict(id='fps_lead', name='2-way Dupont-to-JST PH lead 200 mm + 50 mm PH pigtail on the switch (2 joints)',
         frm='18/24 switch', to='GPIO13 + GND (pins 33/34)',
         via=['ko_run_leads', 'ko_lead_wall', 'ko_lead_cross', 'ko_hdmi_run', 'ko_fps_up'], length=200, steps=(1, 4, 8)),
    dict(id='pigtail', name='XT30 pigtail 18 AWG 180 mm', frm='X1203 battery pads', to='XT30 junction in the grip',
         via=['ko_pig_wrap', 'ko_pig_under', 'ko_pig_in', 'ko_pig_drop', 'ko_xt30'], length=180, steps=(1, 4)),
    dict(id='fan', name='Active Cooler fan lead (native, JST-SH 4)', frm='Active Cooler', to='Pi 5 FAN header', via=[],
         length=60, steps=(1,)),   # INTEGRATOR (docs request): length estimate
    dict(id='pack_lead', name='pack lead 18 AWG', frm='1S2P BMS', to='XT30 male', via=['ko_xt30'], length=60, steps=(10,)),
]
CABLE_ENDS = {'fpc': ('pi5', 'gs_camera'), 'hdmi': ('pi5', 'evf_board'), 'usb_5v': ('pi5', 'evf_board'),   # INTEGRATOR
              'oled_flex': ('hmx039', 'evf_board'), 'qt': ('encoder', 'pi5'), 'run_lead': ('run_button', 'pi5'),
              'fps_lead': ('switch_1824', 'pi5'), 'pigtail': ('x1203', 'xt30_pair'), 'pack_lead': ('pack', 'xt30_pair'),
              'fan': ('cooler', 'pi5')}
for _c in CABLES:
    _c['ends'] = CABLE_ENDS[_c['id']]
del _c

# =============================================================================== 7. cable and plug keep-outs
# Concept keep-outs shifted to the D2 frame; y clipped to <= 32.0 (panel inner face 32.2). Printed parts stay out of
# these (check: overlap volume with each printed solid; the cable's own COTS ends are exempt).
KEEPOUTS = {
    'ko_qt_lead': B(-21.0, -11.0, -31.7, -25.8, 28.8, 40.0),        # QT sockets on GPIO 1/3/5/6
    'ko_run_leads': B(-63.0, -50.0, -31.7, -25.8, 28.8, 40.0),      # run + 18/24 sockets on pins 33-39
    'ko_usb_evf': B(-125.0, -94.0, -32.0, -16.5, 27.2, 37.0),       # USB-A plug of the EVF 5 V lead + bend
    'ko_5v_up': B(-131.0, -125.0, -32.0, -24.0, 27.2, 70.0),
    'ko_5v_end': B(-136.5, -130.0, -24.0, 1.5, 64.0, 70.0),         # INTEGRATOR: +1 x for the diode splice + PH junction
    'ko_sd': B(-5.8, X_FRONT, -11.5, 0.5, 16.1, 18.4),               # microSD edge + tweezer path (through both walls)
    'ko_hdmi_pi': B(-36.6, -27.0, 24.0, 32.0, 17.0, 41.0),           # 90 deg up plug on HDMI0 (<= 8.5 off the board: Q2)
    'ko_hdmi_run': B(-113.0, -36.8, 20.0, 32.0, 39.6, 44.0),
    'ko_hdmi_coil': B(-139.0, -113.5, -12.0, 18.0, 37.3, 60.0),
    'ko_hdmi_evf': B(-144.8, -136.8, 4.0, 17.0, 52.0, 63.8),
    'ko_fpc_up': B(-60.0, -50.0, 24.0, 32.0, 20.2, 36.5),
    'ko_fpc_run': B(-50.0, -42.6, 17.2, 32.0, 30.0, 39.4),
    'ko_fpc_loop': B(-42.5, -29.7, 2.0, 19.5, 36.6, 56.0),           # S-fold, 9 layers x 2 mm, bend r >= 1
    'ko_fpc_cam': B(-29.7, CAM['rear_x'] - 0.2, -8.0, 8.0, 39.4, 47.0),   # CHANGED x: camera rear now -24.47
    'ko_exhaust': B(-9.4, -5.3, -27.4, 16.9, 22.6, 36.2),            # air plenum (the baffle shapes it)
    'ko_run_floor': B(-34.0, -22.0, 1.5, 31.0, 2.7, 5.8),
    'ko_run_rise': B(-26.0, -22.0, 24.1, 31.0, 2.7, 37.0),
    'ko_pig_in': B(-43.0, -19.0, -14.0, -5.0, 2.7, 5.8),
    'ko_run_drop': B(-34.0, -28.0, 1.5, 9.0, -14.2, 2.7),
    'ko_pig_drop': B(-43.0, -36.0, -12.0, -5.0, -12.3, 2.7),
    'ko_xt30': B(-65.0, -37.0, -10.0, 10.0, -36.5, -12.5),
    # FIXER A-F4: lead bodies get reserved space (QT, 18/24 and run leads plugged on the header at step 4)
    'ko_lead_wall': B(-64.0, -11.0, -32.3, -26.0, 36.6, 44.0),       # along the right wall above the GPIO sockets
    'ko_lead_cross': B(-84.0, -74.0, -32.3, 20.0, 36.6, 44.0),       # across behind the blower inlet, over the jacks
    'ko_run_cross': B(-27.0, -21.0, -32.3, 24.1, 36.6, 39.8),        # run lead over the cooler shroud, under the camera
    'ko_fps_up': B(-128.0, -113.0, 14.0, 19.0, 44.0, 57.0),          # 18/24 lead up to the switch lugs (PH junction)
    'ko_pig_wrap': B(-40.5, -35.5, 23.7, 26.5, 2.7, 10.0),           # pigtail round the X1203 port edge (pads: Q2)
    'ko_pig_under': B(-40.5, -35.5, -5.0, 23.7, 2.7, 5.8),           # under the X1203 to ko_pig_in
}
EXTERIOR_KEEPOUTS = {
    'ko_tripod_clamp': dict(box=B(TRIPOD['x'] - 25.0, TRIPOD['x'] + 25.0, -25.0, 25.0, -23.0, BASE['z'][0]),
                            ignore=['strap'], note='50 x 50 x 15 clamp; clears the grip by 11; the soft strap folds aside'),
    'ko_driver_handle': dict(note='straight-driver model, see DRIVER and SCREWS'),
}

# =============================================================================== 8. printed parts table
# face_down: the assembly-frame face that lies on the bed ('-Z' = as assembled). envelope: owners stay inside it.
PARTS = {
    'tub': dict(module='printed_tub.py', material='ASA', colour='satin silver', face_down='-Y', owner='tub',
                infill='shell', envelope=TUB_BOX, supports='2 paint-on supports under the T-tongue -Y wings (about 7.8 x 1.6 '
                'each, about 17 mm above the bed); nothing else'),   # FIXER P3
    'hood': dict(module='printed_hood.py', material='ASA', colour='black', face_down='+Z', owner='hood_panel',
                 infill='shell', envelope=HOOD_BOX, supports='tree, 2 places: the print-lower half of the lens turret and '
                 'the eyepiece housing +Y strip under its window; nothing else (the housing ceiling bridges)'),   # FIXER P3
    'panel': dict(module='printed_panel.py', material='ASA', colour='satin silver', face_down='+Y', owner='hood_panel',
                  infill='shell', envelope=PANEL_BOX, supports='none'),
    'base_grip': dict(module='printed_grip.py', material='ASA', colour='black', face_down='+Z', owner='grip_small',
                      infill='base_grip', envelope=GRIP_BASE_BOX, supports='none (bay bridges <= 30 the short way)'),
    # R2 (finding 3): skirt_l / skirt_r eliminated (were 2 black 1.6 strips on J5 dovetails; NOTES "r2 R2 options")
    'cap': dict(module='printed_grip.py', material='ASA', colour='black', face_down='-Z', owner='grip_small',
                infill='small', envelope=CAP['box'], supports='none'),
    'plunger': dict(module='printed_small.py', material='ASA natural (translucent; clear PETG allowed)',
                    colour='clear/natural', face_down='+X', owner='grip_small', infill='small',
                    envelope=B(-5.3, -1.3, 2.2, 15.8, 16.6, 24.4), supports='none'),
    'knob_exp': dict(module='printed_small.py', material='ASA', colour='black', face_down='+Y', owner='grip_small',
                     infill='small', envelope=B(EXP_X - 14.0, EXP_X + 14.0, YL + 0.2, YL + 9.2, DIAL_Z - 14.0, DIAL_Z + 14.0),
                     supports='none'),
    'knob_fps': dict(module='printed_small.py', material='ASA', colour='black', face_down='+Y', owner='grip_small',
                     infill='small', envelope=B(FPS_X - 10.0, FPS_X + 10.0, YL + 0.2, YL + 7.2, DIAL_Z - 10.0, DIAL_Z + 10.0),
                     supports='none'),
    'eyecup': dict(module='printed_small.py', material='TPU 95A', colour='black', face_down='+X', owner='grip_small',
                   infill='tpu', envelope=EYECUP['box'], supports='none'),
    'stick_sleeve': dict(module='printed_small.py', material='ASA', colour='satin silver', face_down='-X',
                         owner='grip_small', infill='thin', envelope=STICK_SLEEVE['box'], supports='none'),   # FIXER P8: 0.8 walls
}
OWNERS = {'tub': ['printed_tub.py'], 'hood_panel': ['printed_hood.py', 'printed_panel.py'],
          'grip_small': ['printed_grip.py', 'printed_small.py'], 'cots_build': ['cots.py', 'build_d2.py', 'checks.py'],
          'docs': ['../../electronics/gs8-d2-v1/*', 'PRINT-GUIDE.md', 'ASSEMBLY.md', 'DESIGN.md (skeleton)']}

# Declared mates: pairs allowed to touch, or to overlap by design (kind 'interference' gives the allowed depth).
MATES = [
    ('tub', 'hood', 'contact'), ('tub', 'panel', 'contact'), ('tub', 'base_grip', 'contact'), ('hood', 'panel', 'slide'),
    ('base_grip', 'cap', 'slide'),   # R2: base_grip/skirt mates removed with the skirts
    ('tub', 'gs_camera', 'contact'), ('hood', 'gs_camera', 'clearance'), ('tub', 'eyepiece', 'contact'),
    ('panel', 'eyepiece', 'interference 0.1'), ('eyecup', 'eyepiece', 'interference 0.3'), ('hood', 'eyepiece', 'clearance'),
    ('tub', 'x1203', 'contact'), ('tub', 'x1203_kit', 'contact'), ('base_grip', 'tripod_nut', 'press'),
    ('panel', 'encoder', 'contact'), ('panel', 'switch_1824', 'contact'), ('base_grip', 'run_button', 'contact'),
    ('base_grip', 'strap', 'contact'), ('tub', 'usb_stick', 'slide'), ('stick_sleeve', 'usb_stick', 'press'),
    ('tub', 'stick_sleeve', 'slide'), ('knob_exp', 'encoder', 'press'), ('knob_fps', 'switch_1824', 'press'),
    ('hood', 'plunger', 'slide'), ('tub', 'plunger', 'slide'), ('tub', 'hmx039', 'contact'), ('panel', 'hmx039', 'contact'),
    ('tub', 'evf_board', 'slide'), ('tub', 'foam_pad', 'contact'), ('panel', 'foam_pad', 'interference 0.3'),
    ('hmx039', 'foam_pad', 'contact'), ('c_cs_adapter', 'gs_camera', 'thread'), ('lens', 'c_cs_adapter', 'thread'),
    ('pi5', 'x1203_kit', 'contact'), ('x1203', 'x1203_kit', 'contact'), ('pi5', 'cooler', 'contact'),
    ('pi5', 'usb_stick', 'press'), ('xt30_pair', 'pack', 'contact'),
]
# every PT screw 'pierces' the parts it joins (thread-forming into a 2.5 pilot): exempt by id prefix 's_'.

# =============================================================================== 9. assembly steps
# adds: ids that enter the assembly at this step (printed ids, COTS ids, screw ids). Bench steps (1, 2) build
# sub-assemblies off the body; their parts enter the body at the step listed in brackets.
STEPS = [
    dict(step=1, name='Bench: power stack', tool='soldering iron; multimeter; kit driver (PH1 or as supplied)',
         action='Solder the 180 mm XT30 pigtail to the X1203 battery pads (2 joints). Solder the EVF 5 V lead (1N5817 '
                'in the + conductor + PH junction, 3 joints) and check it with a multimeter. Stack X1203 + Pi 5 with the kit '
                '(4 standoffs, 8 M2.5 screws, 0.2 N m), fit the Active Cooler; tie the pigtail to a standoff (strain '
                'relief). Bridge encoder A0 (1). Solder the 50 mm JST PH pigtail to the 18/24 switch (2). Flash the '
                'microSD (G-W3), then take it OUT of the Pi for steps 3-4.', adds=[], bench=['x1203', 'x1203_kit', 'pi5', 'cooler'], in_body=False),
    dict(step=2, name='Bench: panel', tool='paint pen; 12.7 mm (1/2 in) socket or spanner for the switch nut; '
         'junior hacksaw + file',
         action='Paint-fill the engraving. Snap the encoder into its cradle. Fit the 18/24 switch (tab in its slot) '
                'and its nut, finger-tight + 1/8 turn. Cut the switch shaft 7.0 mm above the panel face (to y 42.0) '
                'and deburr.', adds=[], bench=['panel', 'encoder', 'switch_1824'], in_body=False),
    dict(step=3, name='Base + grip', tool='tweezers (press the nut with a flat bar)',
         action='Press the tripod nut into its pocket from '
                'the top. Drop the run button into its cradle through the base opening, then press its red cap on '
                'through the grip-face hole. Thread the strap. Lower the tub onto the base with the base 10 mm '
                'back, tongues through the windows, slide the base 10 mm forward (unlocked until step 8). Only now '
                'fish the run lead up through the floor hole with tweezers from inside the open tub (the base opening '
                'and the hole overlap only at the final pose).',
         adds=['tub', 'base_grip', 'tripod_nut', 'run_button', 'strap']),   # R2: skirt_r removed
    # --- R1 step 4 (owner R1): keeper + s_k1/s_k2 replace the r1 floor hooks
    dict(step=4, name='Pi stack + keeper + header leads',
         tool='straight PH1 screwdriver as step 8 (keeper screws s_k1, s_k2); ESD strap; the microSD is out',
         action='Lay the run lead in its floor channel. Feed the XT30 pigtail round the port edge and down through the '
                'pigtail hole. Lower the '
                'stack about 3 mm back from the front wall and 2 mm off the right wall; below the right-wall pads move '
                'it to the right wall; just above the floor slide it 2.8 forward and set it down on its 4 bosses (the '
                'kit screw heads drop into the boss pockets; nothing clicks). Keeper: hold it level from the open '
                'left side, 0.5 above its 2 bosses and 1.2 behind its place, slide it in -Y under the stick-guide '
                'rail until its port fingers are over the X1203 edge, push it 1.2 forward (the 2 USB fingers go '
                'under the Pi), lower it onto its bosses and drive s_k1 and s_k2 straight down: 0.35-0.5 N m, stop '
                'at head contact. Plug the HDMI (90 deg plug) on '
                'HDMI0, the FPC on CAM1 (camera end loose), the EVF 5 V lead in the upper USB 2 port. With the top '
                'open and the header in sight, plug the header ends: QT lead on pins 1/3/5/6 (red on pin 1, 3V3), the '
                '18/24 lead on 33/34 and the run lead on 37/39 (count from pin 1; an off-by-one plug puts 5 V on the '
                'QT 3V3 wire). Run the QT and 18/24 leads along the right wall and across behind the blower inlet '
                '(ko_lead_wall, ko_lead_cross); park their free ends out of the open left side. The run lead crosses '
                'over the cooler shroud (ko_run_cross).',
         adds=['x1203', 'x1203_kit', 'pi5', 'cooler', 'pi_keeper', 's_k1', 's_k2']),
    # --- R1 step 4 end
    dict(step=5, name='Plunger + hood + microSD', tool='tweezers',
         action='Hold the plunger in the front-wall hole (flange outside). Lower the hood straight down until the 4 hooks '
                'click; the front plate traps the plunger. Push the microSD home through the front slot (both walls) '
                'with tweezers, contacts up, until it latches.', adds=['plunger', 'hood', 'microsd']),
    dict(step=6, name='EVF', tool='tweezers',
         action='Push the eyepiece spigot +X into the rear-wall bore through the housing, flange on the rear face. '
                'Outside the body: flex into the board ZIF (latch closed), HDMI plug into the board, 5 V PH junction '
                'mated (pull the lead ends out of the open left side). Then slide the OLED and the board in together as '
                'a tethered pair (OLED into its cell, foam pad behind it, board into its slot). Coil the HDMI slack '
                'over the stick guide (ko_hdmi_coil); tuck the PH junction into ko_5v_end.',
         adds=['eyepiece', 'hmx039', 'foam_pad', 'evf_board']),
    dict(step=7, name='Camera', tool='none',
         action='Plug the FPC into the camera. Bring the camera in from the left, 11 mm behind its seat, then push it '
                '+X: ring through the bore, 2 pins into 2 holes, lands on the seat (path: in at 2 mm high, lower 2 mm, '
                'then +X 11.1). Fold the FPC slack into its loop.',
         adds=['gs_camera']),
    dict(step=8, name='Panel + 4 screws', tool='PH1 screwdriver, 40 mm+ blade, dia <= 6.5 shank (hand only)',
         action='Hold the panel beside the body; plug the QT lead into the encoder (JST-SH) and mate the 18/24 PH '
                'junction (header ends went on at step 4). Push the panel on along -Y (tongue into the hood groove, '
                'boss tabs into the lip notches, flush). '
                'Drive s_b1, s_b2 up from below and s_r1, s_r2 from the right: 0.35-0.5 N m, stop at head contact.',
         adds=['panel', 'encoder', 'switch_1824', 's_b1', 's_b2', 's_r1', 's_r2']),   # R2: skirt_l removed
    dict(step=9, name='Exterior', tool='none',
         action='Push the knobs on (D shafts), the eyecup over the barrel. Screw the C-CS adapter and the lens on; clock '
                'the Kowa lock screws to the right. Fit the sleeve to the stick, push the stick in from the rear.',
         adds=['knob_exp', 'knob_fps', 'eyecup', 'c_cs_adapter', 'lens', 'usb_stick', 'stick_sleeve']),
    dict(step=10, name='Power', tool='none',
         action='Plug the pack XT30 into the pigtail at the grip mouth, push the junction and the pack up, slide the '
                'cap on (-X) until the detent clicks.', adds=['xt30_pair', 'pack', 'cap']),
]
INSERTIONS = [   # displacement waypoints of the moving set relative to its final position (last = (0, 0, 0))
    dict(id='base_on', step=3, moving=['base_grip', 'tripod_nut', 'run_button', 'strap'],   # R2: skirt_r removed
         path=[(-10.0, 0, -15.0), (-10.0, 0, 0), (0, 0, 0)]),
    dict(id='pi_in', step=4, moving=['x1203', 'x1203_kit', 'pi5', 'cooler'],   # INTEGRATOR T2 (tub sweep 0 mm3)
         path=[(-2.8, 2.1, 80.0), (-2.8, 2.1, 40.0), (-2.8, 0, 40.0), (-2.8, 0, 5.0), (0, 0, 5.0), (0, 0, 0)],
         snaps=[]),                                                     # --- R1: no snaps (r1 pih1..4 deleted)
    dict(id='keeper_in', step=4, moving=['pi_keeper'], path=PI_KEEPER['path']),   # --- R1: -Y slide, +X 1.2, down 0.5
    dict(id='hood_on', step=5, moving=['hood'], path=[(0, 0, 60.0), (0, 0, 0)], snaps=['hk1', 'hk2', 'hk3', 'hk4']),
    dict(id='eyepiece_in', step=6, moving=['eyepiece'], path=[(-30.0, 0, 0), (0, 0, 0)]),
    dict(id='sd_in', step=5, moving=['microsd'], path=[(30.0, 0, 0), (0, 0, 0)]),                      # FIXER A-F2
    dict(id='evf_pair_in', step=6, moving=['hmx039', 'evf_board'], path=[(0, 45.0, 0), (0, 0, 0)]),   # FIXER A-F10
    dict(id='camera_in', step=7, moving=['gs_camera'], path=[(-11.1, 60.0, 2.0), (-11.1, 0, 2.0), (-11.1, 0, 0), (0, 0, 0)],
         ignore=['ko_fpc_loop', 'ko_fpc_cam']),
    dict(id='panel_on', step=8, moving=['panel', 'encoder', 'switch_1824'], path=[(0, 70.0, 0), (0, 0, 0)]),
    dict(id='stick_in', step=9, moving=['usb_stick', 'stick_sleeve'], path=[(-70.0, 0, 0), (0, 0, 0)]),
    dict(id='pack_in', step=10, moving=['pack', 'xt30_pair'], path=[(0, 0, -80.0), (0, 0, 0)]),
    dict(id='cap_on', step=10, moving=['cap'], path=[(CAP['travel'], 0, 0), (0, 0, 0)]),
]


def present_at(step):
    """Ids in the body at the END of `step` (printed + COTS + screws)."""
    out = []
    for s in STEPS:
        if s['step'] <= step:
            out += s['adds']
    return out


def screw_audit_set(screw_id):
    """Ids present when the screw is driven (its own step, all its adds already in place)."""
    s = next(s for s in SCREWS if s['id'] == screw_id)
    return [i for i in present_at(s['step']) if not i.startswith('s_')]


def mass_g(volume_mm3, part_id):
    """Printed mass estimate: volume x density x infill factor of the part's class."""
    p = PARTS[part_id]
    rho = TPU_DENSITY if p['material'].startswith('TPU') else FDM['ASA_DENSITY']
    return volume_mm3 * rho * INFILL_FACTOR[p['infill']]

# =============================================================================== 9b. r2 rectification registries
# --- R3 (owner R3: checks.py reads these; usage in NOTES.md "r2 R3 API"; R1/R2 append in their blocks below)
LOAD_BEARING_PARTS = ['tub', 'panel', 'hood', 'base_grip', 'skirt_l', 'skirt_r', 'cap']  # each needs >= 1 entry
# CRITICAL_FEATURES: dict(id, part, origin=(x,y,z) inside the material at the narrowest section (assembly frame),
#   direction=(dx,dy,dz) across the section (thickness = ray entry-to-exit through origin), span=(n, step_mm, axis)
#   optional (n parallel rays centred on origin, stepped along axis; min taken), min_mm, structural, note).
#   An origin outside the material FAILS (the entry is stale). A later entry with the same id replaces an earlier one.
_X, _Z = (1, 0, 0), (0, 0, 1)
CRITICAL_FEATURES = [   # R3 seeds on the r1 geometry (owners replace by id when they change a feature). min_mm: FDM
    # MIN_WALL_LOADED 1.6 for hooks, lips, wings and lugs that carry a joint load; MIN_WALL 1.2 for walls and lands.
    *[dict(id='tub_tongue_%s_wing_%s' % (t['id'][-1], s), part='tub', origin=(t['x'], sg * 15.5, -2.75), direction=_Z,
           span=(3, 3.0, _X), min_mm=1.6, structural=True,
           note='J4 keyhole T-head wing (head_h 1.8): carries base-to-tub pull-off and the grip moment')
      for t in TONGUES for s, sg in (('l', 1), ('r', -1))],
    *[dict(id='tub_ledge_%s' % h['id'], part='tub', structural=True, direction=_Z, min_mm=1.2,
           origin=((h['x'], h['y_face'] + 0.05, 88.75) if h['wall'] == 'right' else
                   (h['x_face'] - 0.05 if h['wall'] == 'front' else h['x_face'] + 0.05, h['y'], 88.75)),
           note='J1 catch ledge root, 0.05 off the wall face (0.8 lug, 45 deg top chamfer, 1.6 at the root by design); '
                'lug in shear, so MIN_WALL; not part of the r1 loaded zones') for h in HOOD_HOOKS],
    dict(id='tub_front_wall_seat', part='tub', origin=(X_FW_IN + T / 2, -20.0, 30.0), direction=_X, min_mm=1.6,
         structural=True, note='J7 camera seat wall (lens + camera load)'),
    *[dict(id='hood_hook_%s' % h['id'], part='hood', structural=True, min_mm=1.6, span=(3, 2.0, _Z),
           origin=((h['x'], h['y_face'] + HOOK['ledge'] + SL + HOOK['t'] / 2, 92.0) if h['wall'] == 'right' else
                   (h['x_face'] - HOOK['ledge'] - SL - HOOK['t'] / 2, h['y'], 92.0) if h['wall'] == 'front' else
                   (h['x_face'] + HOOK['ledge'] + SL + HOOK['t'] / 2, h['y'], 92.0)),
           direction=(0, 1, 0) if h['wall'] == 'right' else _X, note='J1 snap beam t 1.6 (hood retention)')
      for h in HOOD_HOOKS],
    dict(id='hood_groove_lower_lip', part='hood', origin=(-70.0, 28.0, 90.8), direction=_Z, span=(4, 12.0, _X),
         min_mm=1.6, structural=True, note='J2 lip under the panel-tongue groove (carries the panel top edge)'),
    dict(id='hood_band', part='hood', origin=(-140.0, -20.0, 98.65), direction=_Z, min_mm=1.2, structural=True,
         note='band (roof) over the tub walls'),
    dict(id='panel_tongue', part='panel', origin=(-70.0, 29.0, 93.3), direction=_Z, span=(5, 25.0, _X), min_mm=1.6,
         structural=True, note='J2 tongue in the hood groove'),
    dict(id='panel_wall', part='panel', origin=(-80.0, 33.6, 30.0), direction=(0, 1, 0), min_mm=1.2, structural=True,
         note='panel wall 2.8'),
    dict(id='panel_end_land_rear', part='panel', origin=(-153.0, 32.5, 38.6), direction=(0, 1, 0), min_mm=1.2,
         structural=True, note='J3 rear end land on the tub wall end face, 0.5 in from the R5 feather tip (review: '
                               'panel end land open)'),
    dict(id='panel_end_land_front', part='panel', origin=(-3.7, 32.4, 38.6), direction=(0, 1, 0), min_mm=1.2,
         structural=True, note='J3 front end land, 0.5 in from the R5 feather tip'),
    *[dict(id='base_keyhole_lip_%s_%s' % (t['id'][-1], s), part='base_grip', origin=(t['x'], sg * 15.75, -0.8),
           direction=_Z, min_mm=1.6, structural=True, note='J4 base lip over the tongue head (pull-off load)')
      for t in TONGUES for s, sg in (('l', 1), ('r', -1))],
    dict(id='grip_column_wall', part='base_grip', origin=(GRIP['axis_x'], 13.75, -60.0), direction=(0, 1, 0),
         min_mm=1.6, structural=True, note='grip column side wall 2.5 (hand load)'),
    dict(id='base_strap_bridge', part='base_grip', origin=(-79.25, -27.5, -4.0), direction=_X, min_mm=1.6,
         structural=True, note='bridge between the upper strap slots (strap load)'),
]
del _X, _Z
NONSTRUCTURAL_EXCEPTIONS = []    # dict(part, id, measured_mm, why, at=(x,y,z) optional): named nonstructural details only
# Not in LOAD_BEARING_PARTS (thin_wall screen only): knob_exp / knob_fps (finger torque on a D-shaft), plunger (button
# press < 5 N, compression), eyecup (TPU), stick_sleeve (THIN_OK, slider cover). R1/R2 add any new load-bearing part.
# REMOVALS (service-path sweeps, the reverse of insertion): dict(id, moving=[ids], path=[(0,0,0) .. out] or
#   reverse_of='<INSERTIONS id>', off=[ids already removed, incl. screw ids], unscrew=[screw ids removed at this
#   step: driver audit in the service state], release=[snap_zones() ids or B() boxes a stated tool deflects],
#   keepouts=[KEEPOUTS ids still active], tool='...', note='...')
REMOVALS = []
# EVF board restraint: gap from the board to the nearest arresting surface along each of +-X, +-Y, +-Z (translation
# sweep, mesh boolean). Limit 0.6 = the groove's own total float (2 x SL = 0.5) + 0.1: more than that lets the board
# shuttle on the micro-HDMI plug and the OLED flex. Arresting = the printed parts listed (cables and the OLED are not stops).
EVF_RESTRAINT = dict(part='evf_board', arrest=['tub', 'panel', 'hood'], limit_mm=0.6, max_travel_mm=8.0)
# Section renders (out/renders/section-<id>.png): dict(id, axis='x'|'y'|'z', at=mm, window=(u0, u1, v0, v1) in the
#   two remaining axes (order x, y, z), parts=[ids], title)
SECTIONS = [dict(id='evf-board-z78', axis='z', at=78.0, window=(-156.0, -128.0, -4.0, 36.0),
                 parts=['tub', 'panel', 'hood', 'evf_board', 'hmx039', 'eyepiece'], title='EVF board, section z 78'),
            dict(id='evf-board-x137', axis='x', at=-137.6, window=(-4.0, 36.0, 58.0, 100.0),
                 parts=['tub', 'panel', 'hood', 'evf_board'], title='EVF board PCB plane, section x -137.6'),
            dict(id='pi-keeper-y-20', axis='y', at=-20.0, window=(-106.0, -78.0, -1.0, 24.0),
                 parts=['tub', 'pi_keeper', 'x1203', 'x1203_kit', 'pi5', 's_k1', 's_k2'],
                 title='Pi keeper finger kf1 (USB edge), section y -20')]   # R1 adds pi-keeper-x80 / -y12
# --- R3 end
# --- R1 registry entries (R1 edits this block only: CRITICAL_FEATURES += [...], REMOVALS += [...], SECTIONS += [...])
# R1 (finding 1): the removable Pi keeper (PI_KEEPER in J9) and its 2 PT screws; the r1 floor hooks are deleted.
_K = PI_KEEPER
PARTS['pi_keeper'] = dict(module='printed_keeper.py', material='ASA', colour='black', face_down='+Z', owner='tub',
                          infill='small', envelope=B(_K['arm']['x'][0], _K['bar']['x'][1], _K['arm']['y'][0],
                                                     _K['bar']['y'][1], PI['x1203_z'][1] + _K['gap_z'], _K['top_z']),
                          supports='none (top face on the bed; finger backs 45 deg)')
OWNERS['tub'] = OWNERS['tub'] + ['printed_keeper.py']
MATES += [('tub', 'pi_keeper', 'contact'), ('pi_keeper', 'x1203', 'clearance')]
SCREWS += [dict(id=_sid, joins=['pi_keeper', 'tub'], into='tub keeper boss %s' % _sid, head_part='pi_keeper',
                axis=(0, 0, -1), head_point=(*_b['c'], _K['head_z']), tip=(*_b['c'], _K['head_z'] - PT['length']),
                engage=round(_K['boss_top'] - (_K['head_z'] - PT['length']), 3), step=4,
                cbore=dict(part='pi_keeper', d=_K['cbore_d'], z=(_K['head_z'], _K['top_z'])),
                note='down through the keeper into a tub floor boss (top z 9.8); from above at step 4 (hood, panel off)')
           for _sid, _b in _K['bosses'].items()]
COTS['pt_screws'].update(name='%d x PT 3.0 x 12 PH1' % len(SCREWS), mass=round(0.8 * len(SCREWS), 2))   # 0.8 g each
LOAD_BEARING_PARTS += ['pi_keeper']
_X1, _Y1, _Z1 = (1, 0, 0), (0, 1, 0), (0, 0, 1)
_zt = PI['x1203_z'][1] + _K['gap_z']                       # 7.7 finger underside
CRITICAL_FEATURES += [
    *[dict(id='keeper_finger_%s' % f['id'], part='pi_keeper', structural=True, min_mm=_K['tip_t'], direction=_Z1,
           origin=((PI['x'][0] + _K['reach'] - 0.1, f['at'], _zt + 0.8) if f['edge'] == 'usb' else
                   (f['at'], PI['y'][1] - _K['reach'] + 0.1, _zt + 0.8)),
           span=(3, 2.0, _Y1 if f['edge'] == 'usb' else _X1),
           note='finger tip over the X1203 edge, 0.1 in from the tip (1.6 tip, 45 deg back): carries the stack lift-off')
      for f in _K['fingers']],
    dict(id='keeper_arm', part='pi_keeper', origin=(-97.0, -2.0, 12.7), direction=_Z1, span=(5, 2.0, _X1),
         min_mm=1.6, structural=True, note='USB-edge arm (low part, 5.8 deep), s_k1 to finger kf1 (31 mm under the stick rail)'),
    dict(id='keeper_bridge', part='pi_keeper', origin=(-91.0, 27.7, 14.0), direction=_Z1, span=(5, 3.0, _X1),
         min_mm=1.6, structural=True, note='bridge over panel boss_b1 (z >= 12.5): ties the arm to the port bar'),
    dict(id='keeper_bar', part='pi_keeper', origin=(-62.0, 27.8, 14.0), direction=_Z1, span=(5, 8.0, _X1),
         min_mm=1.6, structural=True, note='port bar (5.8 deep, 4.5 at the s_k2 spot face) carrying kf3/kf4'),
    *[dict(id='tub_keeper_boss_%s' % k, part='tub', origin=(b['c'][0] + PT['pilot_d'] / 2 + 1.0, b['c'][1], 6.0),
           direction=_X1, min_mm=(PT['boss_od_min'] - PT['pilot_d']) / 2, structural=True,
           note='PT boss wall round the 2.5 pilot (teardrop, +X side): carries a keeper screw')
      for k, b in _K['bosses'].items()],
    *[dict(id='tub_pi_boss_%d' % i, part='tub', origin=(hx + PI_BOSS['head_pocket_d'] / 2 + 0.8, hy,
                                                         PI_BOSS['z'][1] - 1.2), direction=_X1, min_mm=1.6,
           structural=True, note='Pi floor boss wall round the kit-head pocket: the stack sits and locates here')
      for i, (hx, hy) in enumerate(PI['holes'])],
    *[dict(id='tub_pad_%s_under_head' % k, part='tub', origin=(p['c'][0] + 2.6, (-32.4 + p['y'][1]) / 2, p['c'][1]),
           direction=_Y1, min_mm=1.6, structural=True, note='right-wall pad under the s_r head (counterbore shoulder)')
      for k, p in RIGHT_WALL_PADS.items()],
    *[dict(id='tub_%s_neck' % t['id'], part='tub', origin=(t['x'], 0.0, -0.9), direction=_X1, min_mm=1.6,
           structural=True, note='J4 T-tongue neck (base pull-off in tension)') for t in TONGUES],
    *[dict(id='tub_cam_pin_%d' % i, part='tub', origin=(X_FW_IN - 1.0, py, pz), direction=_Y1, min_mm=1.6,
           structural=True, note='J7 camera locating pin (dia 1.9)') for i, (py, pz) in enumerate(CAM['pins'])],
]
REMOVALS += [
    dict(id='keeper_out', moving=['pi_keeper'], reverse_of='keeper_in',
         off=['cap', 'pack', 'xt30_pair', 'usb_stick', 'stick_sleeve', 'lens', 'c_cs_adapter', 'eyecup', 'knob_exp',
              'knob_fps', 's_b1', 's_b2', 's_r1', 's_r2', 'panel', 'encoder', 'switch_1824', 'gs_camera', 'eyepiece',
              'hmx039', 'foam_pad', 'evf_board', 'microsd', 'hood', 'plunger'],
         unscrew=['s_k1', 's_k2'], release=[], keepouts=[], tool='straight PH1 screwdriver (the step 8 driver)',
         note='hood and panel off, HDMI/FPC/5 V lead and header leads unplugged; 2 screws out, lift 0.5, back 1.2, '
              'slide out +Y 60 through the open left side. Nothing flexes.'),
    dict(id='pi_out', moving=['x1203', 'x1203_kit', 'pi5', 'cooler'], reverse_of='pi_in',
         off=['cap', 'pack', 'xt30_pair', 'usb_stick', 'stick_sleeve', 'lens', 'c_cs_adapter', 'eyecup', 'knob_exp',
              'knob_fps', 's_b1', 's_b2', 's_r1', 's_r2', 'panel', 'encoder', 'switch_1824', 'gs_camera', 'eyepiece',
              'hmx039', 'foam_pad', 'evf_board', 'microsd', 'hood', 'plunger', 'pi_keeper', 's_k1', 's_k2'],
         unscrew=[], release=[], keepouts=[], tool='none (ESD strap)',
         note='after keeper_out: lift 5, -X 2.8, up 35, +Y 2.1, up 40 (reverse of pi_in); no latch, nothing breaks'),
]
SECTIONS += [dict(id='pi-keeper-x80', axis='x', at=-80.0, window=(-36.0, 36.0, -2.0, 40.0),
                  parts=['tub', 'pi_keeper', 'x1203', 'x1203_kit', 'pi5', 'panel'], title='Pi keeper, section x -80 (kf3)'),
             dict(id='pi-keeper-y12', axis='y', at=12.0, window=(-110.0, -80.0, -2.0, 40.0),
                  parts=['tub', 'pi_keeper', 'x1203', 'pi5'], title='Pi keeper USB finger kf2, section y 12')]
del _K, _X1, _Y1, _Z1, _zt
# --- R1 registry end
# --- R2 registry entries (R2 edits this block only: CRITICAL_FEATURES += [...], REMOVALS += [...],
#     NONSTRUCTURAL_EXCEPTIONS += [...], LOAD_BEARING_PARTS edits for parts R2 adds or removes)
LOAD_BEARING_PARTS = [p for p in LOAD_BEARING_PARTS if p not in ('skirt_l', 'skirt_r')]   # finding 3: eliminated
# EVF board +Y stop (finding 6): a rib on the panel inner face, 0.3 off the PCB +Y edge. It bears on the bare laminate
# edge (PCB x -138.4..-136.8 +- the 0.25 groove float) between the rails (z 61.5..65.25 / 91.25..94.0): the proxy has
# no part there (components y <= 26, ZIF y 7..20 z 86.9..90.9, micro-HDMI y 4..17 z 64..68, OLED flex x <= -138.4 y <= 24).
# Board arrest, 6 directions: -Y groove ends (tub, stop_y 0.7, gap 0.3); +Y this stop (panel, gap 0.3); +-X groove
# walls (tub, 2.1 on a 1.6 PCB, 0.25 each); +-Z groove floors (tub, z 63.75 / 92.75, 0.25 each). Cables are not stops.
EVF_STOP = dict(part='panel', box=B(-138.9, -136.3, EVF['board']['y'][1] + 0.3, SPLIT, 70.0, 86.0), gap=0.3,
                gate='G-EVF-2: with the real board, feeler 0.1-0.5 at the stop; board cannot shuttle on the HDMI plug')
_FW, _RE = XT1 - RV, X_REAR + RV                      # R5 end-corner centres (panel end land, printed_panel.END_LAND)
CRITICAL_FEATURES += [
    # panel
    dict(id='panel_end_land_front', part='panel', origin=(_FW + 3.566, 32.8, 50.0), direction=(0, 1, 0),
         span=(5, 10.0, (0, 0, 1)), min_mm=1.2, structural=True, note='front R5 end: 1.2 land square to the inner face (replaces the R3 seed)'),
    dict(id='panel_end_land_rear', part='panel', origin=(_RE - 3.566, 32.8, 50.0), direction=(0, 1, 0),
         span=(5, 10.0, (0, 0, 1)), min_mm=1.2, structural=True, note='rear R5 end land (eyepiece side)'),
    dict(id='panel_tongue_tooth', part='panel', origin=(-121.0, 29.0, 93.3), direction=(0, 0, 1),
         span=(5, 4.0, (1, 0, 0)), min_mm=1.2, structural=True, note='J2 top tongue tooth: holds the panel top in z'),
    dict(id='panel_boss_b1_wall', part='panel', origin=(-91.0, 25.3, 7.0), direction=(0, 1, 0), min_mm=1.6,
         structural=True, note='s_b1 boss wall round the 2.5 pilot (-Y side, thinnest); tab fills the lip notch'),
    dict(id='panel_boss_b2_wall', part='panel', origin=(-105.0, 25.3, 7.0), direction=(0, 1, 0), min_mm=1.6,
         structural=True, note='s_b2 boss wall'),
    dict(id='panel_post_f_wall', part='panel', origin=(-34.1, -25.0, 85.5), direction=(1, 0, 0), min_mm=1.6,
         structural=True, note='s_r1 post wall round the pilot'),
    dict(id='panel_evf_clamp_prong', part='panel', origin=(-149.8, 24.3, 64.0), direction=(0, 0, 1), min_mm=1.2,
         structural=True, note='EVF cap U clamp, lower prong at its -Y tip (spigot clamp, G-EVF-1)'),
    dict(id='panel_evf_stop', part='panel', origin=(-137.6, 29.5, 78.0), direction=(1, 0, 0),
         span=(5, 3.0, (0, 0, 1)), min_mm=1.2, structural=True, note='EVF board +Y stop rib (finding 6)'),
    dict(id='panel_cam_keeper', part='panel', origin=(-26.3, 15.0, 71.0), direction=(1, 0, 0), min_mm=1.2,
         structural=True, note='camera keeper finger behind the cover (-X restraint)'),
    dict(id='panel_encoder_hook_top', part='panel', origin=(-63.0, 28.0, 70.85), direction=(0, 0, 1), min_mm=1.2,
         structural=True, note='encoder cradle top hook beam (t 1.6)'),
    # base_grip
    # J4 keyhole lips: R3's seeds base_keyhole_lip_* (min 1.6) cover them; R2 adds no duplicate
    dict(id='base_strap_web', part='base_grip', origin=(-79.25, -27.5, -5.0), direction=(1, 0, 0),
         span=(5, 2.5, (0, 1, 0)), min_mm=1.2, structural=True, note='strap anchor: web between the 2 upper slots'),
    dict(id='grip_strap_bar', part='base_grip', origin=(-69.75, -3.0, -100.5), direction=(1, 0, 0),
         span=(3, 2.0, (0, 1, 0)), min_mm=1.6, structural=True, note='strap anchor: heel bar between the lower slots'),
    dict(id='base_tripod_wall', part='base_grip', origin=(-102.5, 0.0, -6.9), direction=(0, 0, 1), min_mm=1.6,
         structural=True, note='1/4-20 nut bearing wall (tripod load)'),
    dict(id='base_sb1_head_floor', part='base_grip', origin=(-88.4, 27.85, -1.0), direction=(0, 0, 1), min_mm=1.6,
         structural=True, note='material under the s_b1 head (clamps base + tub floor to the panel boss)'),
    dict(id='grip_cap_lip_l', part='base_grip', origin=(-45.0, 12.6, -109.2), direction=(0, 0, 1),
         span=(5, 5.0, (1, 0, 0)), min_mm=1.2, structural=True, note='battery retention: 45 deg lip under the +Y cap groove'),
    dict(id='grip_cap_lip_r', part='base_grip', origin=(-45.0, -12.6, -109.2), direction=(0, 0, 1),
         span=(5, 5.0, (1, 0, 0)), min_mm=1.2, structural=True, note='battery retention: lip under the -Y cap groove'),
    dict(id='grip_cap_detent_arm', part='base_grip', origin=(-50.0, 14.25, -107.0), direction=(0, 1, 0),
         span=(3, 3.0, (1, 0, 0)), min_mm=1.2, structural=True, note='cap detent arm: the side-wall strip outside the '
         'groove that flexes 0.1 as the bump passes'),
    dict(id='grip_cap_detent_dimple_wall', part='base_grip', origin=(-57.0, 14.4, -106.8), direction=(0, 1, 0),
         min_mm=1.2, structural=True, note='detent arm at the dimple (thinnest point of the arm)'),
    # cap
    dict(id='cap_key_web_l', part='cap', origin=(-45.0, 11.45, -108.6), direction=(0, 1, 0),
         span=(5, 5.0, (1, 0, 0)), min_mm=1.2, structural=True, note='battery retention: key web (+Y)'),
    dict(id='cap_key_web_r', part='cap', origin=(-45.0, -11.45, -108.6), direction=(0, 1, 0),
         span=(5, 5.0, (1, 0, 0)), min_mm=1.2, structural=True, note='battery retention: key web (-Y)'),
    dict(id='cap_key_head_root', part='cap', origin=(-45.0, 12.3, -107.0), direction=(0, 0, 1), min_mm=1.2,
         structural=True, note='key head at the web face (shear section of the 45 deg hook)'),
    dict(id='cap_key_head_tip', part='cap', origin=(-45.0, 13.1, -106.6), direction=(0, 0, 1),
         span=(5, 5.0, (1, 0, 0)), min_mm=1.2, structural=True, note='key head tip (was 0.8, now 1.4 nominal)'),
    dict(id='cap_detent_bump', part='cap', origin=(-57.0, 13.3, -106.6), direction=(1, 0, 0), min_mm=1.2,
         structural=True, note='detent bump root along the slide (load) direction; NOT a nonstructural exception: '
         'it alone holds the cap shut against +X (lens-down carry, knocks)'),
    dict(id='cap_floor', part='cap', origin=(-45.0, 5.0, -114.5), direction=(0, 0, 1), min_mm=1.6,
         structural=True, note='plate floor under the top pocket (pack side)'),
]
CRITICAL_FEATURES += [
    dict(id='grip_front_wall_pad_top', part='base_grip', origin=(-25.0, 0.0, -8.5), direction=(1, 0, 0),
         span=(5, 2.5, (0, 1, 0)), min_mm=1.2, structural=True, note='grip front wall at the run-pad recess top '
         '(grip/base junction); was 1.0, the pad boss now runs to z -6'),
    dict(id='grip_cap_groove_corner', part='base_grip', origin=(-30.0, 13.9, -106.5), direction=(0, 1, 0),
         min_mm=1.2, structural=True, note='cap groove outer wall at the front-corner exit (cut out forward of x -29.7)'),
    dict(id='grip_heel_slot_end', part='base_grip', origin=(-69.75, -8.0, -100.5), direction=(1, 0, 0), min_mm=1.6,
         structural=True, note='heel strap bar at the -Y slot end (slots moved to y -8.5..4.5, clear of the er 9 corner)'),
    dict(id='panel_boss_b1_cap', part='panel', origin=(-91.0, 27.85, 11.6), direction=(0, 0, 1), min_mm=1.2,
         structural=True, note='boss material over the blind s_b1 pilot end (z 11.0): 1.3, was 1.0'),
]
# The cap detent bump is NOT an exception: it alone holds the cap shut against +X, so it is a structural entry above.
NONSTRUCTURAL_EXCEPTIONS += [
    dict(part='panel', id='antirot_slot_skin', measured_mm=0.8, at=(-122.5, 34.2, 64.9),   # at: INTEGRATOR r2
         why='face skin over the blind 18/24 anti-rotation slot (slot 2.0 deep in the 2.8 wall): it closes the face '
             'only; the switching torque bears on the slot side walls through the 1.2 x 2.5 tab. Sample (-122.5, 34.2, '
             '64.9), r2 trial screen. A shallower slot waits for the measured tab height (MEASURED-PARTS).'),
    dict(part='panel', id='badge_glyph_ridge', measured_mm=0.33, at=(-23.9, 35.0, 88.0),   # at: INTEGRATOR r2
         why='ridge of face material between 2 engraved strokes of the "GS8" badge (0.4 deep, paint-filled); '
             'decoration only, no load. Sample (-23.9, 35.0, 88.0), r2 trial screen.'),
]
REMOVALS += [
    dict(id='panel_off', moving=['panel', 'encoder', 'switch_1824', 'knob_exp', 'knob_fps'], reverse_of='panel_on',
         off=['s_b1', 's_b2', 's_r1', 's_r2'], unscrew=['s_b1', 's_b2', 's_r1', 's_r2'], release=[], keepouts=[],
         tool='PH1 straight driver only (s_b1, s_b2 from below; s_r1, s_r2 from the right)',
         note='finding 3: no skirt, no barb, no blade; strap, cap, pack, lens, stick and eyecup stay fitted; the '
              'knobs ride out on their shafts. A tripod plate must come off first (it covers s_b1/s_b2).'),
]
SECTIONS += [dict(id='base-edge-x91', axis='x', at=-91.0, window=(14.0, 40.0, -10.0, 16.0),
                  parts=['tub', 'panel', 'base_grip'], title='Base edge at s_b1: base, tub lip notch, panel boss tab')]
# (the EVF +Y stop shows in R3's section evf-board-x137: the panel rib z 70..86 stands 0.3 off the PCB edge)
del _FW, _RE
# --- R2 registry end
# --- INTEGRATOR r2 registry entries (hood: no r2 owner). J1 hook tooth root, the shear section of the catch lug: 0.03
#     in from the beam face, across z (root = land 0.6 + lead run 0.65 = 1.25; 1.22 at the probe). Lug in shear: MIN_WALL.
CRITICAL_FEATURES += [
    dict(id='hood_tooth_%s' % h['id'], part='hood', structural=True, min_mm=1.2, direction=(0, 0, 1),
         span=(3, 2.5, (1, 0, 0) if h['wall'] == 'right' else (0, 1, 0)),
         origin=((h['x'], h['y_face'] + h['normal'][1] * (HOOK['ledge'] + SL - 0.03), ZT1 - HOOK['length'] + 0.62)
                 if h['wall'] == 'right' else
                 (h['x_face'] + h['normal'][0] * (HOOK['ledge'] + SL - 0.03), h['y'], ZT1 - HOOK['length'] + 0.62)),
         note='J1 hook tooth root (catch lug in shear: holds the hood down); was 1.05 in r1 (unclassified screen spot)')
    for h in HOOD_HOOKS]
# --- INTEGRATOR r2 registry end
# --- FIXER r2 registry (verifier findings M-V-MPS-1/2/6/8/9, 2026-10-05)
# Feature classes (M-V-MPS-6). check_critical_features grades each structural entry at max(entry min_mm, class floor),
# so an entry literal cannot lower the rule; a structural entry that matches no class FAILs. 'flexure' (a spring strip
# whose stiffness is the design variable) keeps the MIN_WALL floor only with a named physical gate (FEATURE_GATES);
# the check prints it as a gated exception, the gate stays "not run".
FEATURE_CLASS_MIN = dict(hook=FDM['MIN_WALL_LOADED'], lug=FDM['MIN_WALL_LOADED'], lip=FDM['MIN_WALL_LOADED'],
                         boss=FDM['MIN_WALL_LOADED'], wing=FDM['MIN_WALL_LOADED'], pin=FDM['MIN_WALL_LOADED'],
                         neck=FDM['MIN_WALL_LOADED'], bar=FDM['MIN_WALL_LOADED'],
                         wall=FDM['MIN_WALL'], land=FDM['MIN_WALL'], flexure=FDM['MIN_WALL'])
FEATURE_CLASS_GATED = ('flexure',)
FEATURE_CLASS_RULES = [   # (regex on the entry id, class); first match wins
    (r'^tub_tongue_._wing_', 'wing'), (r'^tub_ledge_', 'lug'), (r'^tub_front_wall_seat$', 'wall'),
    (r'^hood_hook_', 'hook'), (r'^hood_groove_lower_lip$', 'lip'), (r'^hood_band$', 'wall'), (r'^hood_tooth_', 'lug'),
    (r'^panel_tongue', 'lug'), (r'^panel_wall$', 'wall'), (r'^panel_end_land_', 'land'), (r'^panel_boss_', 'boss'),
    (r'^panel_post_', 'boss'), (r'^panel_evf_(clamp_prong|stop)$', 'lug'), (r'^panel_cam_keeper$', 'lug'),
    (r'^panel_encoder_hook', 'hook'), (r'^base_keyhole_lip_', 'lip'), (r'^grip_column_wall$', 'wall'),
    (r'^base_strap_(bridge|web)$', 'bar'), (r'^grip_strap_bar$', 'bar'), (r'^grip_heel_slot_end$', 'bar'),
    (r'^base_tripod_wall$', 'wall'), (r'^base_sb1_head_floor$', 'boss'), (r'^grip_cap_lip_', 'lip'),
    (r'^grip_cap_(detent_arm|detent_dimple_wall|groove_corner)$', 'flexure'), (r'^cap_key_', 'hook'),
    (r'^cap_detent_bump$', 'lug'), (r'^cap_floor$', 'wall'), (r'^grip_front_wall_pad_top$', 'wall'),
    (r'^keeper_finger_', 'hook'), (r'^keeper_(arm|bridge|bar)$', 'bar'), (r'^tub_keeper_boss_', 'boss'),
    (r'^tub_pi_boss_', 'boss'), (r'^tub_pad_', 'boss'), (r'^tub_tongue_._neck$', 'neck'), (r'^tub_cam_pin_', 'pin'),
    (r'^tub_evf_groove_', 'wall'), (r'^tub_evf_collar_', 'lug'), (r'^tub_j4_lock_boss$', 'boss'),
]
FEATURE_GATES = {   # flexure entries: the strip outside the cap-key groove is the detent spring (1.5 nominal, 1.25 at
    # the dimple, 1.275 at the front-corner exit). Below the 1.6 lug rule; kept only against the physical gate.
    'grip_cap_detent_arm': 'G-CAP-1', 'grip_cap_detent_dimple_wall': 'G-CAP-1', 'grip_cap_groove_corner': 'G-CAP-1'}
_Y1, _Z1, _X1 = (0, 1, 0), (0, 0, 1), (1, 0, 0)
CRITICAL_FEATURES += [
    dict(id='tub_keeper_boss_s_k2_seam', part='tub', origin=(-64.0, 31.0, 9.0), direction=_Y1,
         min_mm=(PT['boss_od_min'] - PT['pilot_d']) / 2, structural=True,
         note='s_k2 boss +Y wall above the lip gusset (z 7.6..9.8, where the PT thread starts): verifier M-V-MPS-1'),
    # EVF board rails (M-V-MPS-9): the board's +-X, +-Z and -Y arrest. Inertial load of a ~6 g board only, so class
    # 'wall' (MIN_WALL); the -X/+X groove walls are 1.3 by design, the top-rail roof 1.25 (rail top 0.3 under the hood).
    *[dict(id='tub_evf_groove_wall_%s_%s' % (r, s), part='tub', origin=(x, y, z), direction=_X1, min_mm=1.2,
           span=(3, 0.5, _Y1) if r == 'bot' else (5, 5.0, _Y1), structural=True,
           note='EVF board %s rail, %s groove wall (board +-X arrest; 1.3 by design)' % (r, s))
      for r, z, y in (('bot', 64.5, 2.0), ('top', 92.0, 12.0)) for s, x in (('mx', -139.3), ('px', -135.9))],
    dict(id='tub_evf_groove_floor_bot', part='tub', origin=(-137.6, 2.0, 62.5), direction=_Z1, min_mm=1.2,
         structural=True, note='EVF bottom rail under the groove (board -Z arrest), y 0.7..3.0 before the plug gap'),
    dict(id='tub_evf_groove_roof_top', part='tub', origin=(-137.6, 12.0, 93.4), direction=_Z1, min_mm=1.2,
         structural=True, note='EVF top rail over the groove (board +Z arrest; rail top 94.0, 0.3 under the hood lip)'),
    *[dict(id='tub_evf_groove_end_%s' % r, part='tub', origin=(-137.6, 0.2, z), direction=_Y1, min_mm=1.2,
           structural=True, note='EVF %s groove end at y 0.7 (board -Y arrest)' % r)
      for r, z in (('bot', 64.5), ('top', 92.0))],
    dict(id='tub_evf_collar_radial', part='tub', origin=(-150.5, 0.4, 78.0), direction=_Y1, min_mm=1.6,
         structural=True, note='eyepiece half-collar under the 29.3 bore (G-EVF-1 20 N pull-out, spigot clamp)'),
    dict(id='tub_evf_collar_axial', part='tub', origin=(-152.0, 0.4, 78.0), direction=_X1, min_mm=1.6,
         structural=True, note='rear wall + half-collar along the eyepiece axis (G-EVF-1 pull-out)'),
]
# Parts kept out of LOAD_BEARING_PARTS, each with a named rationale (M-V-MPS-9); the thin-wall screen still runs on them.
PART_RATIONALE = {
    'stick_sleeve': 'slider cover over the USB stick (THIN_OK 0.8): the stick pull-out load goes stick -> its own USB '
                    'socket; the sleeve carries finger friction only. Physical check: G-STICK (MEASURED-PARTS MP-STICK).',
    'knob_exp': 'D-bore knob on the encoder shaft: finger torque < 0.05 N m and an encoder push (< 5 N, compression). '
                'Bore fit and torque: the knob-bore coupons (PRINT-GUIDE s6), not run.',
    'knob_fps': 'D-bore knob on the 18/24 switch shaft: as knob_exp. Knob-bore coupons, not run.',
    'plunger': 'button plunger: compression < 5 N only.', 'eyecup': 'TPU push-on sleeve: no structural load.'}
# Pin hold-open release (M-V-MPS-2). checks.check_release_access: a straight pin from outside along the hole axis must
# reach the hook tooth through the tub hole with 0 mm3 overlap on any other part, and push it `push` mm.
RELEASE_ACCESS = [dict(id='pin_%s' % h['id'], hook=h['id'], part='hood', axis=_Y1, pin_d=HOOD_RELEASE['pin_d'],
                       start=(h['x'], YR - 25.0, HOOD_RELEASE['z']),
                       tooth_face=(h['x'], h['y_face'] + HOOK['ledge'] + SL - HOOK['tooth'], HOOD_RELEASE['z']),
                       push=HOOD_RELEASE['push'], tool=HOOD_RELEASE['tool'])
                  for h in HOOD_HOOKS if h.get('release_hole')]
_SVC_PANEL = ['panel', 'encoder', 'switch_1824', 'knob_exp', 'knob_fps', 's_b1', 's_b2', 's_r1', 's_r2']
REMOVALS += [
    dict(id='hood_off', moving=['hood'], reverse_of='hood_on',
         off=_SVC_PANEL + ['lens', 'c_cs_adapter', 'eyecup', 'gs_camera', 'eyepiece', 'hmx039', 'foam_pad', 'evf_board',
                           'microsd', 'plunger'],
         unscrew=[], release=['hk1', 'hk2', 'hk3', 'hk4'], keepouts=[],
         tool=HOOD_RELEASE['tool'] + ' for hk1/hk2 (right wall, straight from the right); hk3/hk4 cam out',
         note='panel, camera, eyepiece and EVF pair out; push a pin into each right-wall release hole (it stays: '
              'hold-open), lift the hood straight up 60; hk3/hk4 (45 deg return) cam out at the insertion strain. '
              'Refit: pins out, drop the hood on.'),
    dict(id='camera_out', moving=['gs_camera'], reverse_of='camera_in',
         off=_SVC_PANEL + ['lens', 'c_cs_adapter'], unscrew=[], release=[], keepouts=[],
         tool='none (hands; FPC unplugged at the Pi, ESD strap)',
         note='panel and lens off; -X 11.1 off the 2 pins and out of the bore, out through the open left side'),
    dict(id='eyepiece_out', moving=['eyepiece'], reverse_of='eyepiece_in',
         off=_SVC_PANEL + ['eyecup'], unscrew=[], release=[], keepouts=[], tool='none (hands)',
         note='panel off (its cap is the spigot clamp), eyecup off; eyepiece -X 30 out of the housing'),
    dict(id='evf_out', moving=['hmx039', 'evf_board'], reverse_of='evf_pair_in',
         off=_SVC_PANEL + ['eyecup', 'eyepiece', 'foam_pad'], unscrew=[], release=[], keepouts=[],
         tool='none (hands; HDMI and 5 V leads unplugged)', note='panel off; board + OLED pair +Y 45 out of the grooves'),
]
# Every non-screw id named in a REMOVALS 'off' list needs its own REMOVALS entry or a latch-free reason here.
LATCH_FREE = {
    'cap': 'battery door: slides +X 52 on its dovetail keys over a 0.35 detent, by hand (G-CAP-1)',
    'pack': 'drops out of the bay once the cap is off; no latch', 'xt30_pair': 'friction connector, unplugged by hand',
    'usb_stick': 'slides -X out of its socket and channel; no latch', 'stick_sleeve': 'slides off with the stick',
    'lens': 'C-mount thread, unscrewed by hand', 'c_cs_adapter': 'C-CS thread, unscrewed by hand',
    'eyecup': 'TPU push-on sleeve, pulled off by hand', 'foam_pad': 'loose foam pad, lifted out',
    'microsd': 'friction slot, pulled with tweezers (tool 8)', 'plunger': 'loose in the hood pocket, lifted out',
    'encoder': 'rides with the panel', 'switch_1824': 'rides with the panel', 'knob_exp': 'rides with the panel',
    'knob_fps': 'rides with the panel', 'gs_camera': 'see camera_out', 'eyepiece': 'see eyepiece_out',
    'hmx039': 'see evf_out', 'evf_board': 'see evf_out'}
SERVICE_REQUIRED_EXTRA = [('hood (Pi service path)', 'hood')]
# J4 base lock independent of the panel screws (verifier M-V-MPS-5). r2 made s_b1/s_b2 both the panel screws and the
# only J4 lock, so panel service left the body free to slide 10 mm off the base. s_j: one more PT 3.0 x 12 PH1, up
# through a base counterbore into a tub floor boss at (-111, -20), driven at step 3 (base on), never removed for panel
# or Pi service. The boss is 0.8 clear of the keeper arm's -X 1.2 insertion offset and outside every keep-out.
J4_LOCK = dict(c=(-111.0, -20.0), od=PT['boss_od'], top=12.6, screw='s_j')
SCREWS += [dict(id='s_j', joins=['base_grip', 'tub'], into='tub j4 lock boss', head_part='base_grip', axis=(0, 0, 1),
                head_point=(*J4_LOCK['c'], -2.0), tip=(*J4_LOCK['c'], 10.0), engage=10.0, step=3,
                cbore=dict(part='base_grip', d=PT['cbore_d'], z=(-8.0, -2.0)),
                note='J4 base lock (r2 fixer): up through a base counterbore into a tub floor boss (z 0..12.6)')]
COTS['pt_screws'].update(name='%d x PT 3.0 x 12 PH1' % len(SCREWS), mass=round(0.8 * len(SCREWS), 2))
_st3 = next(s for s in STEPS if s['step'] == 3)
_st3['adds'] = list(_st3['adds']) + ['s_j']
_st3['tool'] = 'tweezers (press the nut with a flat bar); the straight PH1 screwdriver (s_j)'
_st3['action'] = _st3['action'].replace('slide the base 10 mm forward (unlocked until step 8).',
                                        'slide the base 10 mm forward, then drive s_j up through the base counterbore '
                                        'at (-111, -20) into the tub floor boss: 0.35-0.5 N m, stop at head contact '
                                        '(the J4 lock; the panel screws no longer lock the base).')
CRITICAL_FEATURES += [dict(id='tub_j4_lock_boss', part='tub', origin=(J4_LOCK['c'][0] + PT['pilot_d'] / 2 + 1.0,
                                                                      J4_LOCK['c'][1], 8.0),
                           direction=(1, 0, 0), min_mm=(PT['boss_od_min'] - PT['pilot_d']) / 2, structural=True,
                           note='J4 lock boss wall round the 2.5 pilot (base pull-off and slide lock)')]
del _st3
# Far-side stack retention (verifier M-V-MPS-4). The keeper's 4 fingers sit on 2 adjacent edges, so the stack CoM
# (about (-54.5, -7.4)) lay 16-21 mm outside their hull and a knock could hinge the stack about the kf1-kf4 line. A
# post hangs from the hood roof over the far kit screw head (-9.5, -28.8; head top z 21.85) with a 0.15 gap: no
# positioning load. It goes on with the hood (straight down) and comes off with it. Narrow (4.2 x 3.7) below z 45.5 to
# stay 0.3 clear of the QT lead keep-outs (x <= -11) and ko_exhaust (y >= -27.4); a 17.5 wide fin above (free length
# about 23 mm: Euler about 165 N for ASA, estimate). Check: checks.check_stack_retention.
HOOD_STACK_STOP = dict(post=B(-10.7, -6.5, -31.3, -27.6, 22.0, 45.5), fin=B(-24.0, -6.5, -31.3, -27.6, 45.0, ZT1 + 0.5),
                       gap=0.15, head=(-9.5, -28.8), head_top_z=PI['pcb_z'][1] + X1203_KIT['head'][1],
                       stack=['pi5', 'x1203', 'x1203_kit', 'cooler'])
CRITICAL_FEATURES += [dict(id='hood_stack_post', part='hood', origin=(-8.6, -29.45, 30.0), direction=(0, 1, 0),
                           span=(3, 1.5, (1, 0, 0)), min_mm=1.6, structural=True,
                           note='far-side stack stop post (3.7 thick in y): compression stop over the kit screw head')]
FEATURE_CLASS_RULES += [(r'^hood_stack_post$', 'bar')]
NONSTRUCTURAL_EXCEPTIONS += [
    dict(part='hood', id='plunger_channel_vent_web', measured_mm=1.08, at=(0.86, 9.68, 23.8),
         why='hood front plate: the web between the top of the plunger channel (z 24.7) and the exhaust band slots '
             '(z 25.9) is 1.2 nominal, 1.08 at a slot edge; no joint load (the plunger stops on the tub recess). '
             'Pre-existing; surfaced when the screen samples moved in the fixer build. Open: lower the channel top '
             '0.2 or raise the band.')]
NONSTRUCTURAL_EXCEPTIONS += [   # FIXER r2: screen spots that surfaced in the r2 fixer builds (sample positions moved)
    dict(part='panel', id='exposure_label_glyph_ridge', measured_mm=0.30, at=(-56.01, 34.99, 35.71),
         why='face material between engraved strokes of the "exposure" label (0.4 deep, paint-filled); decoration.'),
    dict(part='panel', id='exposure_label_glyph_ridge_2', measured_mm=0.44, at=(-58.27, 34.91, 37.04),
         why='as exposure_label_glyph_ridge (second sample, 2.6 mm away).'),
    dict(part='tub', id='stick_rail_lip_tip', measured_mm=0.19, at=(-117.56, 7.34, 20.18),
         also_at=[(x, 7.5, 20.3) for x in range(-131, -93, 4)],
         why='last 0.2-0.8 mm of the 45 deg print lip on the stick floor rail, x -131.5..-94.5 (a chamfer feather, '
             'y 5.6..7.65, z 18.4..20.5); the lip root is 2.05 deep. Pre-existing in r1/r2; it surfaced when the '
             'screen samples moved (0.19..0.79 in the fixer builds).'),

]
del _Y1, _Z1, _X1, _SVC_PANEL
# --- FIXER r2 registry end

# =============================================================================== 10. MODULE CONTRACT (binding)
MODULE_CONTRACT = """
Every printed_*.py module (printed_tub.py, printed_hood.py, printed_panel.py, printed_grip.py, printed_small.py):
 1. exposes  build(layout) -> dict {part_id: cadquery.Workplane}  for exactly the PARTS ids whose 'module' is
    that file. Each Workplane wraps ONE valid closed Solid in ASSEMBLY coordinates (this file's frame), final pose.
    `layout` is this module object; read every number from it (never re-type a layout number).
 2. exposes  PRINT = {part_id: dict(face_down=<PARTS face_down>, supports=<str>, notes=<str>)}  at module level.
    face_down uses the PARTS convention; build_d2.py rotates the solid by it for STL export and bed checks.
 3. may expose  build_part(layout, part_id) -> Workplane  for --part runs (fast single-part rebuilds).
 4. imports only: math, cadquery, d2_common (helpers + FDM constants) and the layout object passed in. Never another
    printed_*.py, never cad/gs8-pxl-v3/build_camera.py, no file I/O at import time, no global CadQuery work.
 5. stays inside the part's PARTS[...]['envelope'] box (0.0 tolerance) and out of every KEEPOUTS box and every COTS
    box except the declared MATES (contact/slide/press/interference as stated).
 6. models the interface features exactly as section 3 states (who carries what); FDM rules from d2_common.FDM:
    walls >= 1.2 (1.6 loaded, bosses, hooks, lips), clearances SLIDE/LOCATE/SEAM per side, 45 deg chamfers on bed
    edges and no fillets on the bed face, overhangs <= 45 deg unless bridged (<= 30 mm) or listed in supports,
    teardrops on horizontal holes > 8 mm, PT bosses via d2_common.pt_boss (pilot 2.5, OD 8, depth engage + 1).
 7. records geometry it could not finish in NOTES.md under its owner heading; requests for a layout change go to
    NOTES.md "Interface requests" (do not edit layout.py or another owner's file).
COTS (cots.py): build_all(layout) -> {cots_id: dict(shape=Workplane, mass=g, src=str, box=...)}; shapes inside the
COTS box; LENS chosen by layout.LENS (build_d2.py --lens kowa_lm6hc|fujinon_hf6xa sets it before building).
Screws (s_b1, s_b2, s_r1, s_r2): cots.py makes each from PT + SCREWS (shank dia 3.0 from head_point to tip, head
dia 6.0 x 2.4 behind head_point).
"""


def box_dims(b):
    return tuple(round(b[k][1] - b[k][0], 3) for k in 'xyz')


def boxes_overlap(a, b, margin=0.0):
    return all(a[k][0] < b[k][1] - margin and b[k][0] < a[k][1] - margin for k in 'xyz')


def print_dims(part_id):
    """Envelope dims (bed x, bed y, height) in print orientation (face_down rotation of the envelope box)."""
    dx, dy, dz = box_dims(PARTS[part_id]['envelope'])
    fd = PARTS[part_id]['face_down']
    h = {'X': dx, 'Y': dy, 'Z': dz}[fd[1]]
    rest = sorted([v for k, v in (('X', dx), ('Y', dy), ('Z', dz)) if k != fd[1]], reverse=True)
    return rest[0], rest[1], h


def snap_strains():
    """FIXER P2/P6: the one record of every snap-beam strain (1.5 t d / L^2, nominal and x SNAP_KT at a gussetted root)."""
    kt = FDM['SNAP_KT']
    out = {}
    d = HOOK['tooth'] - SL                             # reach over the ledge (beam front face is SLIDE off the ledge)
    e = 1.5 * HOOK['t'] * d / HOOK['length'] ** 2
    out['hood_hooks'] = dict(t=HOOK['t'], L=HOOK['length'], d=round(d, 3), nominal=round(e, 4), with_kt=round(e * kt, 4),
                             gusset=FDM['SNAP_GUSSET'], limit=0.02, layers='across (beam along print Z)')
    c = ENCODER['cradle_hooks']
    Lc = SPLIT - (ENCODER['pcb']['y'][0] - c['play']) + 0.4 + (c['tooth'] + SL)
    dc_ = c['tooth']                                   # layout 'tooth' = reach over the PCB; printed tooth = reach + SLIDE
    e = 1.5 * 1.6 * dc_ / Lc ** 2
    out['encoder_cradle'] = dict(t=1.6, L=round(Lc, 2), d=round(dc_, 3), nominal=round(e, 4), with_kt=round(e * kt, 4),
                                 gusset=FDM['SNAP_GUSSET'], limit=0.02, layers='across (beam along print Z)')
    P = PI_HOOK
    if PI_HOOKS:                                       # R1 r2: the Pi hooks are deleted (pi_keeper); no record
        dp = (P['tooth'] - P['gap']) * math.sqrt(2)
        Lp = (P['catch_z'] - P['root_z']) * math.sqrt(2)
        e = 1.5 * P['t'] * dp / Lp ** 2
        out['pi_hooks'] = dict(t=P['t'], L=round(Lp, 2), d=round(dp, 3), nominal=round(e, 4), with_kt=round(e * kt, 4),
                               gusset=0.0, limit=P['max_strain'], layers='45 deg to the layers; one-time class (G-SNAP-1)')
    return out


def self_check():
    """Plain-python consistency checks of the layout numbers (not geometry checks)."""
    res = []

    def chk(name, ok, detail=''):
        res.append(dict(check=name, ok=bool(ok), detail=detail))

    for s in SCREWS:
        chk('engage>=7 ' + s['id'], s['engage'] >= PT['engage_min'], s['engage'])
        length = math.dist(s['head_point'], s['tip'])
        chk('length=12 ' + s['id'], abs(length - PT['length']) < 1e-6, round(length, 3))
    chk('boss OD >= 7', PT['boss_od'] >= PT['boss_od_min'], PT['boss_od'])
    for k, v in snap_strains().items():
        lim = v['limit']
        val = v['nominal'] if k == 'pi_hooks' else v['with_kt']
        chk('snap strain %s <= %.1f %%' % (k, lim * 100), val <= lim, v)
    for k, b in list(PANEL_BOSSES.items()) + list(PANEL_POSTS.items()):
        w = min(box_dims(b)[0], box_dims(b)[2]) if k.startswith('post') else min(box_dims(b)[0], box_dims(b)[1])
        chk('boss/post section >= 8 ' + k, w >= PT['boss_od'] - 1e-9, w)
    for pid in PARTS:
        bx, by, h = print_dims(pid)
        for bed, (BX, BY, BZ) in PRINT_BEDS.items():
            ok = (bx <= BX and by <= BY and h <= BZ) or (bx <= BY and by <= BX and h <= BZ)
            chk('bed envelope %s %s' % (pid, bed.split()[0]), ok, (bx, by, h))
    chk('display plane F+6', abs(EVF['display_x'] - (EVF['F'] + 6.0)) < 1e-9, EVF['display_x'])
    chk('cup lip 33.6 proud', abs(X_REAR - EVF['cup_lip_x'] - 33.6) < 1e-9, EVF['cup_lip_x'])
    chk('turret bore clears ring', HOOD['turret']['r_in'] - CAM['ring']['r'] >= 0.25 - 1e-9,
        HOOD['turret']['r_in'] - CAM['ring']['r'])
    chk('lens clears turret front', C_FLANGE_X - HOOD['turret_b']['a'][1] >= 1.0, round(C_FLANGE_X - 8.5, 2))
    hb = HOOD['housing']
    w = HOOD['housing_wall']
    chk('housing clears barrel -y/bottom/top by 1.25',
        min(16.0 - 19.25 - (hb['y'][0] + w), 78.0 - 19.25 - (hb['z'][0] + w), hb['z'][1] - HOOD['housing_top_wall'] - (78.0 + 19.25)) >= 1.25 - 0.1 - 1e-9,
        'top 1.25, bottom %.2f, -y %.2f' % (78.0 - 19.25 - (hb['z'][0] + w), 16.0 - 19.25 - (hb['y'][0] + w)))
    gap = PLUNGER['nib']['a'][0] - PI_BUTTON['x_face']
    chk('plunger travel presses button >= 0.2', PLUNGER['travel'] - gap >= 0.2 and PLUNGER['travel'] - gap <= PI_BUTTON['travel'],
        'gap %.2f, travel %.2f, press %.2f' % (gap, PLUNGER['travel'], PLUNGER['travel'] - gap))
    for t in TONGUES:
        ok = not boxes_overlap(t['base_pocket'], BASE_OPENING) and not any(
            boxes_overlap(t['head'], h) or boxes_overlap(t['neck'], h) for h in FLOOR_HOLES.values())
        chk('tongue clear of holes ' + t['id'], ok)
    ids = set(PARTS) | set(COTS) | {s['id'] for s in SCREWS}
    for s in STEPS:
        for i in s['adds']:
            chk('step id known %s' % i, i in ids)
    for a, b, _ in MATES:
        chk('mate ids known %s/%s' % (a, b), a in ids and b in ids)
    return res


if __name__ == '__main__':
    r = self_check()
    bad = [x for x in r if not x['ok']]
    for x in bad:
        print('FAIL', x)
    print('%s: %d layout checks, %d failed' % (REVISION, len(r), len(bad)))
    print('parts:', len(PARTS), ' COTS:', len(COTS), ' screws:', len(SCREWS), ' steps:', len(STEPS),
          ' keepouts:', len(KEEPOUTS), ' lens:', LENS, lens_spec()['com'])
