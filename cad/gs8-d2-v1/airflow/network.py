"""D2 airflow study, role af-data: inputs (params.json) + lumped network model (out/network.json, out/network.md).

Run:  .venv-cad/Scripts/python.exe cad/gs8-d2-v1/airflow/network.py      (numpy only; no CAD kernel; seconds)

Everything here is an ESTIMATE resting on the sources named in params.json (field 'basis'). The baseline geometry is read
from ../layout.py (J14 VENTS, COTS cooler proxy, ko_exhaust, SD_SLOT); nothing in the baseline is edited.

Network (nodes): A ambient (p = 0, 30 C), B body interior (well mixed), F blower outlet / fin entry, P exhaust plenum
(ko_exhaust + the space in front of / over the fins). Branches: fan B->F (curve), fins F->P, over-fin bypass F->P (the
proxy as drawn: blower 22..36.3 high, fins only 23.4..30.5), plenum<->body opening P-B (no baffle: DESIGN J14 T3),
vents A<->B (inlet_roof, x1203, sd_slot) and A<->P (out_band, out_corner, out_wall). Flow directions are results.
"""
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import layout as L  # noqa: E402  (pure python, no cadquery)

OUT = os.path.join(HERE, 'out')
CFM = 0.0283168 / 60.0                       # m3/s per CFM
INH2O = 249.089                              # Pa per inch H2O

# ------------------------------------------------------------------------------------------------ air (35 C, 1 atm)
FLUID = dict(rho=1.146, mu=1.885e-5, nu=1.645e-5, cp=1007.0, k_air=0.0268, Pr=0.707, T_amb_C=30.0,
             basis='dry air at 35 C, 101.3 kPa (standard property tables; film temperature between 30 C ambient and '
                   'about 40 C interior). Singapore-level humidity changes rho*cp by < 1 %.')

# ------------------------------------------------------------------------------------------------ fan (SC1148 blower)
FAN_Q_MAX = 1.09 * CFM                       # 5.14e-4 m3/s, Active Cooler product brief RP-008188 (max airflow)
FAN_RPM = (8000.0, 0.15)                     # brief: 8000 rpm +-15 %
REF_BLOWER = dict(model='Delta BFB0305MA-A (30 x 30 x 10, 5 V blower, obsolete)', Q_max_CFM=1.2,
                  dp_max_inH2O=0.206, dp_max_Pa=51.3, P_W=0.40,
                  src='DigiKey listing 603-1560-ND, read 2026-10-05 from a search summary (not the PDF)')
# fan-law scaling of the reference to the Active Cooler's flow: dp ~ Q^2 for a geometrically similar blower
DP0_NOM = REF_BLOWER['dp_max_Pa'] * (FAN_Q_MAX / (REF_BLOWER['Q_max_CFM'] * CFM)) ** 2      # about 42 Pa
CURVES = {   # dp(Q) = dp0 * (1 - (Q/Qmax)^n); n sets the droop (blowers: flat near shut-off)
    'nominal': dict(Q_max=FAN_Q_MAX, dp0=DP0_NOM, n=1.6),
    'low': dict(Q_max=FAN_Q_MAX * 0.85, dp0=25.0, n=1.2),
    'high': dict(Q_max=FAN_Q_MAX * 1.15, dp0=70.0, n=2.0),
}


def fan_dp(Q, c, s=1.0):
    """Fan pressure rise (Pa) at flow Q (m3/s), curve c, speed fraction s (fan laws Q~s, dp~s^2).
    Q < 0 (reverse) and Q > Q_max are extended linearly so the curve stays strictly decreasing."""
    Qm, dp0, n = c['Q_max'] * s, c['dp0'] * s * s, c['n']
    if Q < 0.0:
        return dp0 - Q * 20.0 * dp0 / Qm
    if Q <= Qm:
        return dp0 * (1.0 - (Q / Qm) ** n)
    return -n * dp0 / Qm * (Q - Qm)


def curve_points(c, s=1.0, k=11):
    return [[round(q, 8), round(fan_dp(q, c, s), 3)] for q in np.linspace(0.0, c['Q_max'] * s, k)]


# ------------------------------------------------------------------------------------------------ loss correlations
def rect_fRe(alpha):
    """Laminar Darcy f*Re for a rectangular duct, aspect alpha = short/long (Shah & London 1978)."""
    a = min(alpha, 1.0 / alpha)
    return 96.0 * (1 - 1.3553 * a + 1.9467 * a ** 2 - 1.7012 * a ** 3 + 0.9564 * a ** 4 - 0.2537 * a ** 5)


def idelchik_thick_plate(f, lbar):
    """Inertial part of the loss of a thick perforated/slotted plate, referenced to the approach (face) velocity:
    zeta = [0.5(1-f)^0.75 + tau(1-f)^1.375 + (1-f)^2] / f^2,  tau = (2.4 - l)*10^-phi(l),
    phi = 0.25 + 0.535 l^8/(0.05 + l^8), l = thickness / hydraulic diameter of one hole (Idelchik, Handbook of
    Hydraulic Resistance, 3rd ed., diagram 8-3, thickened plates; friction is added separately as laminar)."""
    lb = min(lbar, 2.4)
    phi = 0.25 + 0.535 * lb ** 8 / (0.05 + lb ** 8)
    tau = (2.4 - lb) * 10.0 ** (-phi)
    return (0.5 * (1 - f) ** 0.75 + tau * (1 - f) ** 1.375 + (1 - f) ** 2) / f ** 2


def slot_field(box, slot_w, pitch, along, face):
    """Same slot count/size rule as d2_common.vent_slots (rounded-end slots)."""
    thin = face[1]
    ax_i, al_i = 'xyz'.index(thin), 'xyz'.index(along)
    rep_i = ({0, 1, 2} - {ax_i, al_i}).pop()
    lo, hi = box['xyz'[rep_i]]
    n = int((hi - lo - slot_w) // pitch) + 1
    a0, a1 = box['xyz'[al_i]]
    Ls = a1 - a0
    A1 = (Ls - slot_w) * slot_w + math.pi * slot_w ** 2 / 4.0
    P1 = 2 * (Ls - slot_w) + math.pi * slot_w
    t = box[thin][1] - box[thin][0]
    gross = (hi - lo) * Ls
    return dict(n=n, slot_len=Ls, slot_area=A1, d_h=4 * A1 / P1, t=t, gross=gross, open=n * A1,
                alpha=slot_w / Ls)


# ------------------------------------------------------------------------------------------------ vents (J14 + SD)
NODE_OF_VENT = {'inlet_roof': 'B', 'x1203': 'B', 'sd_slot': 'B', 'out_band': 'P', 'out_corner': 'P', 'out_wall': 'P'}
WINDOW_K = 0.4      # tub window entry from the plenum (window/plenum section about 0.28: 0.5*(1-0.28)^0.75), face vel.


def vent_params():
    rho, mu = FLUID['rho'], FLUID['mu']
    out = {}
    for vid, v in L.VENTS.items():
        s = slot_field(v['box'], v['slot_w'], v['pitch'], v['slot_along'], v['face'])
        f = s['open'] / s['gross']
        lbar = s['t'] / s['d_h']
        phi = 0.25 + 0.535 * min(lbar, 2.4) ** 8 / (0.05 + min(lbar, 2.4) ** 8)
        tau = (2.4 - min(lbar, 2.4)) * 10.0 ** (-phi)
        K_in = (0.5 * (1 - f) ** 0.75 + tau * (1 - f) ** 1.375 + 1.0) / f ** 2
        fRe = rect_fRe(s['alpha'])
        a_lin = fRe * mu * (s['t'] * 1e-3) / (2.0 * (s['d_h'] * 1e-3) ** 2 * f)       # Pa per (m/s face)
        win = 'tub_window' in v
        if win:
            K_in += WINDOW_K
        out[vid] = dict(
            node=NODE_OF_VENT[vid], part=v['part'], face=v['face'], box=v['box'],
            area_mm2=round(s['gross'], 2), open_area_mm2=round(s['open'], 2), open_area_ratio=round(f, 4),
            n_slots=s['n'], slot_w_mm=v['slot_w'], slot_len_mm=round(s['slot_len'], 2), pitch_mm=v['pitch'],
            thickness_mm=round(s['t'], 2), d_h_mm=round(s['d_h'], 3), l_over_dh=round(lbar, 3),
            K=round(K_in, 3), a_lin_Pa_per_mps=round(a_lin, 4),
            dp_model='dp = a_lin*v + K*0.5*rho*v*|v|, v = Q / area (face velocity over the gross box area)',
            basis=('Idelchik thick-plate inertial terms (entry 0.5(1-f)^0.75 + tau(1-f)^1.375) with the downstream '
                   'term replaced by the full exit loss 1.0 (wall vent between two large volumes); laminar slot '
                   'friction fRe = %.1f (Shah-London rectangle, aspect %.3f) on t/d_h; slot count/size as '
                   'd2_common.vent_slots' % (fRe, s['alpha']))
            + ('; + tub window entry K %.1f (window 2.5 thick, same box, 0.2 gap to the hood plate)' % WINDOW_K
               if win else ''))
    sd = L.SD_SLOT                                    # microSD access slot through the tub wall + hood plate
    w, h, t = sd['y'][1] - sd['y'][0], sd['z'][1] - sd['z'][0], sd['x'][1] - sd['x'][0]
    blk = 0.6                                         # [est] the card edge and socket fill part of the 2.7 mm height
    d_h = 2 * w * (h * blk) / (w + h * blk)
    a_lin = rect_fRe((h * blk) / w) * mu * t * 1e-3 / (2 * (d_h * 1e-3) ** 2 * blk)
    out['sd_slot'] = dict(node='B', part='tub+hood', face='+x', box=sd, area_mm2=round(w * h, 2),
                          open_area_mm2=round(w * h * blk, 2), open_area_ratio=blk, n_slots=1,
                          thickness_mm=t, d_h_mm=round(d_h, 3), K=round((0.5 + 1.0) / blk ** 2, 3),
                          a_lin_Pa_per_mps=round(a_lin, 4), dp_model=out['x1203']['dp_model'],
                          basis='NOT a J14 vent: the microSD access slot (layout SD_SLOT) is open through both walls in '
                                'the existing arrangement; card + socket block an estimated 40 %; K = (0.5 entry + 1 '
                                'exit)/f^2; laminar duct friction over 5.2 mm')
    return out


# ------------------------------------------------------------------------------------------------ cooler fins + paths
def fin_params():
    """Cooler proxy (cots.cooler): fins 1.0 thick at 2.5 pitch from y0+1, z 23.4..30.5, x blower end..box end.
    Blower outlet face = x blower[1], y blower y-range, z 23.4..36.3 (proxy blower top)."""
    c = L.COTS['cooler']
    b, fb = c['box'], c['features']['blower']
    y0, y1 = b['y']
    n_fin = int((y1 - y0 - 2) / 2.5)
    fins = [(y0 + 1.0 + 2.5 * i, y0 + 2.0 + 2.5 * i) for i in range(n_fin)]
    edges = [y0] + [e for f in fins for e in f] + [y1]
    gaps = [(edges[2 * i], edges[2 * i + 1]) for i in range(len(edges) // 2)]
    Lf = b['x'][1] - fb['x'][1]
    z_fin, z_top = (23.4, 30.5), fb['z'][1]
    hf = z_fin[1] - z_fin[0]
    fed = [g for g in gaps if g[0] >= fb['y'][0] - 1e-6 and g[1] <= fb['y'][1] + 1e-6]
    g = 1.5
    W = y1 - y0
    phi_all = sum(b_ - a_ for a_, b_ in gaps) / W
    mu, rho = FLUID['mu'], FLUID['rho']
    sigma = 0.6
    Cc = 0.61 + 0.39 * sigma ** 3
    K_c, K_e, K_inf = (1 / Cc - 1) ** 2, (1 - sigma) ** 2, 0.686
    return dict(
        n_fins=n_fin, fin_t_mm=1.0, pitch_mm=2.5, gap_mm=g, length_x_mm=round(Lf, 2), z_mm=z_fin, height_mm=hf,
        gaps_mm=[[round(a, 2), round(b_, 2)] for a, b_ in gaps], fed_channels=len(fed),
        fed_y_mm=list(fb['y']), blower_outlet_z_mm=[z_fin[0], z_top], bypass_height_mm=round(z_top - z_fin[1], 2),
        open_area_ratio=round(phi_all, 4), porous_axis='+X',
        frontal_box=dict(x=[fb['x'][1], b['x'][1]], y=[y0, y1], z=list(z_fin)),
        K_per_mm=dict(a_Pa_per_mps_per_mm=round(12 * mu / (g * 1e-3) ** 2 / phi_all * 1e-3, 5),
                      b_Pa_per_mps2_per_mm=round((K_c + K_e + K_inf) * 0.5 * rho / phi_all ** 2 / Lf, 6),
                      model='dp/dx = a*u + b*u*|u| per mm along +X, u = superficial velocity over the frontal box'),
        K_total=round(K_c + K_e + K_inf, 3), K_parts=dict(contraction=round(K_c, 3), expansion=round(K_e, 3),
                                                          developing_K_inf=K_inf),
        basis='laminar parallel-plate channels (Re_dh about 200-500): fully developed 12 mu v/g^2 per length plus '
              'Shah-London incremental K(inf) 0.686, abrupt contraction (1/Cc - 1)^2 with Cc = 0.61 + 0.39 sigma^3, '
              'Borda exit (1-sigma)^2, sigma = 0.6 (gap/pitch). Heat transfer: Stephan mean Nu for simultaneously '
              'developing flow between plates. Fin count/positions exactly as cots.cooler (proxy, not the real '
              'Active Cooler: real fin height and any top cover are not modelled in the repo).',
        proxy_warning='The proxy blower is 12.9 tall (z 23.4..36.3) but the fins only 7.1 (z 23.4..30.5) and have no '
                      'top cover, so 45 % of the blower outlet face opens over the fins straight into the plenum / body. '
                      'The real SC1148 envelope is 13.7 incl. spring pins; whether its fins are full height and covered '
                      'is not recorded. The network runs both (proxy as drawn = base; full-height covered fins = '
                      'variant).')


def channel_dp_coeffs(fp, n_ch, h_mm):
    """Fin path F->P for n_ch fed channels of height h: dp = a*Q + b*Q^2 (Q in m3/s)."""
    mu, rho = FLUID['mu'], FLUID['rho']
    g, Lf = fp['gap_mm'] * 1e-3, fp['length_x_mm'] * 1e-3
    A = n_ch * g * h_mm * 1e-3
    a = 12 * mu * Lf / g ** 2 / A
    b = fp['K_total'] * 0.5 * rho / A ** 2
    return a, b, A


def sink_R(Q_fin, fp, n_ch, h_mm, R_jc=1.0, k_al=150.0):
    """SoC junction -> fin INLET air (K/W) at fin flow Q_fin (m3/s): R_jc (die, lid, pad, base spreading) + 1/(eps C)
    with eps = 1 - exp(-NTU), NTU = h A eta / C (C = rho cp Q_fin); h from Stephan's mean Nu (plates, developing)."""
    if Q_fin <= 1e-9:
        return float('inf')
    rho, cp, k, nu, Pr = FLUID['rho'], FLUID['cp'], FLUID['k_air'], FLUID['nu'], FLUID['Pr']
    g, Lf, hf = fp['gap_mm'] * 1e-3, fp['length_x_mm'] * 1e-3, h_mm * 1e-3
    A_flow = n_ch * g * hf
    v = Q_fin / A_flow
    dh = 2 * g
    Re = v * dh / nu
    xs = Lf / (dh * Re * Pr)
    Nu = 7.55 + 0.024 * xs ** -1.14 / (1 + 0.0358 * Pr ** 0.17 * xs ** -0.64)
    h = Nu * k / dh
    m = math.sqrt(2 * h / (k_al * fp['fin_t_mm'] * 1e-3))
    eta = math.tanh(m * hf) / (m * hf)
    A = n_ch * (2 * hf * eta + g) * Lf
    C = rho * cp * Q_fin
    eps = 1 - math.exp(-h * A / C)
    return R_jc + 1.0 / (eps * C)


# ------------------------------------------------------------------------------------------------ heat loads
BOARD = {'S1': 4.5, 'S2': 6.0, 'S3': 12.5}                 # WIRING s4.2 Pi 5 board row
LOADS = {   # WIRING s4.2 rows (W at 5.1 V): hdmi5v, camera, fan, evf, stick, encoder
    'S1': dict(hdmi5v=0.26, camera=0.4, fan=0.3, evf=1.3, stick=0.3, enc=0.1, total=7.2),
    'S2': dict(hdmi5v=0.26, camera=0.4, fan=0.5, evf=1.3, stick=2.5, enc=0.1, total=11.1),
    'S3': dict(hdmi5v=0.26, camera=0.4, fan=0.5, evf=1.55, stick=4.6, enc=0.1, total=19.9)}
ETA_X1203 = dict(nominal=0.90, low=0.85, high=0.93)
SOC_IDLE, BOARD_IDLE, SOC_SHARE = 1.6, 3.3, 0.9
WALLS = dict(area_m2=2 * (L.L * L.W + L.L * L.H + L.W * L.H) * 1e-6, h_in=5.0, t_m=2.5e-3, k_asa=0.17, h_out=9.0,
             U_range=(2.0, 4.5),
             basis='[est] body box 154 x 70 x 100 (layout L, W, H) outer area; ASA wall 2.5 mm k 0.17; inside forced/'
                   'mixed convection h 5; outside natural convection 3-4 + radiation about 5-6 (emissivity 0.9) = 9. '
                   'Lens, turret, grip and the hand are not modelled. Second case only: the base case is adiabatic.')
WALLS['U'] = 1.0 / (1 / WALLS['h_in'] + WALLS['t_m'] / WALLS['k_asa'] + 1 / WALLS['h_out'])
WALL_UA = WALLS['U'] * WALLS['area_m2']


def heat_params():
    out = {}
    for s, bd in BOARD.items():
        ld = LOADS[s]
        soc = SOC_IDLE + SOC_SHARE * (bd - BOARD_IDLE)
        x_loss = ld['total'] * (1 / ETA_X1203['nominal'] - 1)
        out[s] = dict(soc=round(soc, 3), pi_board_rest=round(bd - soc, 3), x1203=round(x_loss, 3),
                      evf_board=round(ld['evf'] + ld['hdmi5v'], 3), camera=ld['camera'], usb_stick=ld['stick'],
                      fan=ld['fan'], encoder=ld['enc'])
        out[s]['total'] = round(sum(v for v in out[s].values()), 3)
        out[s]['x1203_worst_eta085'] = round(ld['total'] * (1 / ETA_X1203['low'] - 1), 3)
    out['basis'] = (
        'WIRING.md s4.2 (r2 table, all [est]/[pub] there) at 5.1 V: board S1 4.5 / S2 6.0 / S3 12.5 W split SoC vs rest '
        'as soc = %.1f + %.1f x (board - %.1f idle) [est: the CPU/ISP increment above the published 3.3 W idle is almost '
        'all BCM2712; idle SoC 1.6 W, RP1 + LPDDR4X + PMIC losses about 1.7 W]; X1203 boost loss = total output x '
        '(1/eta - 1), eta 0.90 (WIRING s4.7 estimate; 0.85 at a low cell = x1203_worst_eta085); evf_board = EVF board '
        '+ panel + HDMI pin-19 5 V (0.26 W limit); fan motor heat goes into the blower air; encoder + gauge as '
        '"encoder" (panel). The cells are outside the body air (grip) and are not counted.'
        % (SOC_IDLE, SOC_SHARE, BOARD_IDLE))
    out['placement'] = dict(soc='fin-block air (the cooler)', fan='blower air', pi_board_rest='air over the Pi PCB',
                            x1203='air at the X1203 boost IC (stack gap, z 7.6..18.5)', evf_board='EVF board box',
                            camera='camera box', usb_stick='stick box', encoder='panel / misc')
    return out


def build_params():
    fp = fin_params()
    curves = {k: dict(c, curve_points=curve_points(c)) for k, c in CURVES.items()}
    p = dict(
        fluid=FLUID,
        fan=dict(curve_100=curve_points(CURVES['nominal']), speed_fractions=[0.5, 1.0],
                 range=dict(low=curves['low']['curve_points'], high=curves['high']['curve_points']),
                 curves={k: dict(Q_max_m3s=c['Q_max'], dp0_Pa=round(c['dp0'], 3), n=c['n']) for k, c in CURVES.items()},
                 law='dp = dp0 (1 - (Q/Qmax)^n); speed s: Qmax*s, dp0*s^2 (fan laws); 50 % = half SPEED, not half PWM',
                 rpm=FAN_RPM[0], power_W=0.5, reference_blower=REF_BLOWER,
                 basis='Q_max 1.09 CFM = %.3e m3/s and 8000 rpm +-15 %% from the Active Cooler product brief '
                       'RP-008188 (via cad/gs8-pxl-v2/COMPUTE-OPTICS-COMPONENTS.md; confirmed by distributor listings, '
                       'search 2026-10-05). NO static pressure or curve is published (search 2026-10-05). dp0 nominal = '
                       'Delta BFB0305MA-A (30 x 30 x 10 5 V blower, 1.2 CFM, 51.3 Pa) scaled by the fan law (Q ratio)^2 '
                       '= %.1f Pa; low = 0.85 Qmax / 25 Pa / n 1.2, high = 1.15 Qmax / 70 Pa / n 2.0 (rpm tolerance and '
                       'impeller uncertainty; tip-speed bound rho (pi D n)^2 about 115 Pa for a 24 mm impeller). It is '
                       'not known whether 1.09 CFM is free air or through the cooler fins; treating it as the bare fan '
                       'is the conservative reading.' % (FAN_Q_MAX, DP0_NOM)),
        vents=vent_params(),
        fins=fp,
        paths=dict(
            bypass=dict(area_mm2=round(28.0 * fp['bypass_height_mm'], 2), K=1.0,
                        basis='proxy blower outlet strip over the fins (y -24..4, z 30.5..36.3); free jet, exit '
                              'dynamic head lost (K 1.0)'),
            plenum_body=dict(area_mm2_proxy=round(4.1 * 44.3 + 4.1 * 13.6 + 33.3 * 28.0, 1),
                             area_mm2_covered=round(4.1 * 44.3 + 4.1 * 13.6, 1), K=1.5,
                             basis='ko_exhaust (x -9.4..-5.3, y -27.4..16.9, z 22.6..36.2) top + +y end are open to the '
                                   'body since the baffle was deleted (J14 T3); proxy case adds the open top of the '
                                   'over-fin strip (33.3 x 28). K 1.5 (between a free exit, 1.0, and a sharp orifice, '
                                   '1/0.6^2 = 2.8)'),
            jet_credit=dict(beta=[0.0, 1.0], basis='fraction of the merged fin-exit dynamic pressure that stagnates on '
                                                   'out_band (4 mm ahead of the fins); 0 = conservative base')),
        heat=heat_params(),
        walls=dict(WALLS, UA_W_per_K=WALL_UA),
        sink=dict(R_jc_K_per_W=dict(nominal=1.0, low=0.6, high=2.4), k_fin_W_mK=150.0,
                  model='R_sink(Q_fin) = R_jc + 1/(eps rho cp Q_fin), eps = 1 - exp(-h A eta/(rho cp Q_fin)), Nu Stephan '
                        '(developing plates), A = fed channels only; referenced to the FIN INLET air (= fan intake + '
                        'fan motor heat)',
                  basis='[est] R_jc: BCM2712 die/lid + thermal pad (0.5 mm, k 3-6 W/mK over about 17 x 17 mm: 0.3-0.6 '
                        'K/W) + base spreading 0.2-0.4 K/W; no Raspberry Pi thermal-resistance figure is published (not '
                        'searched: search budget used on the fan). Heat into the PCB (parallel path) is ignored: '
                        'conservative for the SoC. Plausibility (not re-checked in this job, no search left): commonly cited open-air '
                        'Pi 5 + Active Cooler all-core results in the 60s C at room temperature imply about 4-5 K/W total, '
                        'i.e. R_jc nearer the high value 2.4; the nominal 1.0 may be optimistic.'),
        notes=['All values are estimates for a basic simulation; none closes G-W11 / G-W12 P4.',
               'Vent K and a_lin are referenced to the face velocity over the gross vent box area (area_mm2).',
               'Node of each vent (B body / P plenum) is the lumped network assignment; the 3D model uses geometry.'])
    return p


# ------------------------------------------------------------------------------------------------ network solver
def _flow(dp, a, b):
    """Invert dp = a v + b v|v| for v (signed)."""
    s, d = (1.0 if dp >= 0 else -1.0), abs(dp)
    if b <= 0:
        return s * d / a
    return s * (-a + math.sqrt(a * a + 4 * b * d)) / (2 * b)


def _fan_Q(dP, c, s):
    lo, hi = -2.0 * c['Q_max'] * s, 4.0 * c['Q_max'] * s
    for _ in range(80):
        m = 0.5 * (lo + hi)
        if fan_dp(m, c, s) > dP:
            lo = m
        else:
            hi = m
    return 0.5 * (lo + hi)


CONFIGS = {   # fin height used (mm), bypass present, plenum-body opening (key in params paths.plenum_body)
    'proxy': dict(h_fin=7.1, bypass=True, pb='area_mm2_proxy',
                  label='as drawn: proxy fins 7.1 high + open strip over them, no baffle (EXISTING CAD)'),
    'covered': dict(h_fin=12.9, bypass=False, pb='area_mm2_covered',
                    label='real-cooler reading: full-height covered fins (no over-fin strip), no baffle'),
    'ducted': dict(h_fin=12.9, bypass=False, pb=None,
                   label='REFERENCE BOUND only (not the existing setup): covered fins + plenum sealed from the body'),
}


def solve(prm, config='proxy', curve='nominal', speed=1.0, kscale=1.0, beta=0.0, out_wall_node='P'):
    rho = FLUID['rho']
    cf = CONFIGS[config]
    fp = prm['fins']
    a_fin, b_fin, A_fin = channel_dp_coeffs(fp, fp['fed_channels'], cf['h_fin'])
    a_fin, b_fin = a_fin * kscale, b_fin * kscale
    byp = prm['paths']['bypass']
    A_byp = byp['area_mm2'] * 1e-6
    pb = prm['paths']['plenum_body']
    A_pb = pb[cf['pb']] * 1e-6 if cf['pb'] else 0.0
    A_jet = 28.0e-6 * 12.9
    vents = prm['vents']
    node = {k: (out_wall_node if k == 'out_wall' else v['node']) for k, v in vents.items()}
    c = CURVES[curve]
    reg = 0.05                                             # Pa per (m/s): tiny linear term for open paths

    def flows(p):
        pB, pF, pP = p
        Qf = _fan_Q(pF - pB, c, speed)
        Qfin = _flow(pF - pP, a_fin, b_fin)
        Qbyp = A_byp * _flow(pF - pP, reg, kscale * byp['K'] * 0.5 * rho / 1.0) if cf['bypass'] else 0.0
        Qpb = A_pb * _flow(pP - pB, reg, kscale * pb['K'] * 0.5 * rho) if A_pb > 0 else 0.0
        vjet = (Qfin + Qbyp) / A_jet
        qv = {}
        for k, v in vents.items():
            drive = pB if node[k] == 'B' else pP
            if k == 'out_band':
                drive += beta * 0.5 * rho * vjet * abs(vjet)
            A = v['area_mm2'] * 1e-6
            qv[k] = A * _flow(drive, kscale * v['a_lin_Pa_per_mps'], kscale * v['K'] * 0.5 * rho)
        return Qf, Qfin, Qbyp, Qpb, qv

    def resid(p):
        Qf, Qfin, Qbyp, Qpb, qv = flows(p)
        oB = sum(q for k, q in qv.items() if node[k] == 'B')
        oP = sum(q for k, q in qv.items() if node[k] == 'P')
        return np.array([-Qf - oB + Qpb, Qf - Qfin - Qbyp, Qfin + Qbyp - Qpb - oP]) * 1e6   # cm3/s scale

    p = np.array([-1.0, c['dp0'] * speed ** 2 * 0.5, 0.5])
    r = resid(p)
    hist = [float(np.abs(r).max())]
    for it in range(200):
        J = np.zeros((3, 3))
        for j in range(3):
            dp = np.zeros(3)
            dp[j] = 1e-4 * max(1.0, abs(p[j]))
            J[:, j] = (resid(p + dp) - r) / dp[j]
        step = np.linalg.solve(J, -r)
        lam = 1.0
        while lam > 1e-4:
            pn = p + lam * step
            rn = resid(pn)
            if np.abs(rn).max() < np.abs(r).max():
                break
            lam *= 0.5
        p, r = pn, rn
        hist.append(float(np.abs(r).max()))
        if hist[-1] < 1e-7:
            break
    Qf, Qfin, Qbyp, Qpb, qv = flows(p)
    return dict(config=config, curve=curve, speed=speed, kscale=kscale, beta=beta, out_wall_node=out_wall_node,
                p_Pa=dict(B=p[0], F=p[1], P=p[2]), Q_fan=Qf, Q_fin=Qfin, Q_bypass=Qbyp, Q_plenum_to_body=Qpb,
                vents=qv, node=node, A_fin_m2=A_fin, h_fin=cf['h_fin'],
                mass_residual_m3s=float(sum(qv.values())), newton_iters=len(hist) - 1, resid_hist_cm3s=hist)


def thermal(sol, heat, prm, R_jc=1.0, x1203_key='x1203', UA=0.0):
    """Well-mixed nodes B, F, P; upwind enthalpy; ambient 30 C. Returns node temperatures and the SoC estimate."""
    C = FLUID['rho'] * FLUID['cp']
    Ta = FLUID['T_amb_C']
    idx = {'B': 0, 'F': 1, 'P': 2}
    M, rhs = np.zeros((3, 3)), np.zeros(3)
    P_F = heat['soc'] + heat['fan']
    P_B = sum(heat[k] for k in ('pi_board_rest', 'evf_board', 'camera', 'usb_stick', 'encoder')) + heat[x1203_key]
    rhs[0], rhs[1] = -P_B - UA * Ta, -P_F
    M[0, 0] -= UA                                   # body wall loss to ambient (UA W/K)

    def link(i, j, Q):       # flow Q from node i to node j (Q may be negative)
        if Q < 0:
            i, j, Q = j, i, -Q
        M[idx[i], idx[i]] -= C * Q
        M[idx[j], idx[i]] += C * Q
    link('B', 'F', sol['Q_fan'])
    link('F', 'P', sol['Q_fin'] + sol['Q_bypass'])
    link('P', 'B', sol['Q_plenum_to_body'])
    for k, q in sol['vents'].items():
        n = idx[sol['node'][k]]
        if q > 0:
            M[n, n] -= C * q
        else:
            rhs[n] -= C * (-q) * Ta
    T = np.linalg.solve(M, rhs)
    fp = prm['fins']
    T_fin_in = T[0] + heat['fan'] / (C * max(sol['Q_fan'], 1e-9))
    R = sink_R(sol['Q_fin'], fp, fp['fed_channels'], sol['h_fin'], R_jc=R_jc, k_al=prm['sink']['k_fin_W_mK'])
    Q_out = sum(q for q in sol['vents'].values() if q > 0)
    P_tot = P_F + P_B
    return dict(T_body_C=T[0], T_fan_outlet_C=T[1], T_plenum_C=T[2], T_fin_inlet_C=T_fin_in, R_sink_K_per_W=R,
                T_soc_est_C=T_fin_in + heat['soc'] * R, P_total_W=P_tot, Q_through_m3s=Q_out,
                dT_bulk_exhaust_K=P_tot / (C * Q_out) if Q_out > 0 else float('inf'),
                energy_residual_W=float(C * sum(q * (T[idx[sol['node'][k]]] - Ta) for k, q in sol['vents'].items()
                                                if q > 0) + UA * (T[0] - Ta) - P_tot),
                wall_loss_W=UA * (T[0] - Ta))


# ------------------------------------------------------------------------------------------------ study driver
def _r(x, n=4):
    return float('%.*g' % (n, x)) if isinstance(x, (float, np.floating)) and math.isfinite(x) else x


def case_record(prm, sol, states=('S1', 'S2', 'S3'), R_jc=1.0):
    rec = dict(config=sol['config'], curve=sol['curve'], speed=sol['speed'], kscale=sol['kscale'], beta=sol['beta'],
               out_wall_node=sol['out_wall_node'], p_Pa={k: _r(v) for k, v in sol['p_Pa'].items()},
               Q_fan_m3s=_r(sol['Q_fan']), Q_fan_CFM=_r(sol['Q_fan'] / CFM, 3), Q_fin_m3s=_r(sol['Q_fin']),
               Q_bypass_m3s=_r(sol['Q_bypass']), Q_plenum_to_body_m3s=_r(sol['Q_plenum_to_body']),
               recirculation_fraction=_r(max(sol['Q_plenum_to_body'], 0.0) / sol['Q_fan'], 3),
               vents_m3s_out_positive={k: _r(v) for k, v in sol['vents'].items()},
               Q_through_m3s=_r(sum(q for q in sol['vents'].values() if q > 0)),
               mass_residual_m3s=_r(sol['mass_residual_m3s'], 2), newton_iters=sol['newton_iters'],
               resid_hist_cm3s=[_r(h, 2) for h in sol['resid_hist_cm3s']], thermal={}, thermal_walls={})
    for s in states:
        t = thermal(sol, prm['heat'][s], prm, R_jc=R_jc)
        rec['thermal'][s] = {k: _r(v) for k, v in t.items()}
        tw = thermal(sol, prm['heat'][s], prm, R_jc=R_jc, UA=WALL_UA)
        rec['thermal_walls'][s] = {k: _r(v) for k, v in tw.items()}
    return rec


def main():
    os.makedirs(OUT, exist_ok=True)
    prm = build_params()
    with open(os.path.join(HERE, 'params.json'), 'w') as fh:
        json.dump(prm, fh, indent=1)
    base = dict(curve='nominal', speed=1.0, kscale=1.0)
    cases = []
    for cfg in CONFIGS:
        for beta in ((0.0, 1.0) if cfg != 'ducted' else (0.0,)):
            for curve in ('nominal', 'low', 'high'):
                for speed in (1.0, 0.5):
                    for ks in (1.0, 0.5, 1.5):
                        cases.append(case_record(prm, solve(prm, cfg, curve, speed, ks, beta)))
    variants = []
    for cfg in ('proxy', 'covered'):
        for beta in (0.0, 1.0):
            variants.append(dict(what='out_wall on the body node', **case_record(
                prm, solve(prm, cfg, beta=beta, out_wall_node='B'))))
    import copy
    for cfg in ('proxy', 'covered'):
        prm2 = copy.deepcopy(prm)
        prm2['paths']['plenum_body']['K'] *= 4.0
        for beta in (0.0, 1.0):
            variants.append(dict(what='plenum-body opening K x4 (half as effective: cables, camera, hood rib)',
                                 **case_record(prm2, solve(prm2, cfg, beta=beta))))
    rj = []
    for cfg, beta in (('proxy', 1.0), ('covered', 0.0), ('covered', 1.0), ('ducted', 0.0)):
        sol = solve(prm, cfg, beta=beta)
        for R_jc in (0.6, 2.4):
            r = case_record(prm, sol, states=('S3',), R_jc=R_jc)
            rj.append(dict(config=cfg, beta=beta, R_jc=R_jc, T_soc_S3=r['thermal']['S3']['T_soc_est_C']))
        h = dict(prm['heat']['S3'])
        t = thermal(sol, h, prm, x1203_key='x1203_worst_eta085')
        rj.append(dict(config=cfg, beta=beta, x1203_eta=0.85, T_body_S3=_r(t['T_body_C']),
                       T_soc_S3=_r(t['T_soc_est_C'])))
    res = dict(model='lumped network, see network.py docstring', configs={k: v['label'] for k, v in CONFIGS.items()},
               base=base, cases=cases, variants=variants, sink_and_x1203_sensitivity=rj,
               sink_R_vs_Qfin={cfg: [[_r(q, 3), _r(sink_R(q, prm['fins'], prm['fins']['fed_channels'],
                                                           CONFIGS[cfg]['h_fin']), 3)]
                                     for q in np.linspace(0.5e-4, 6e-4, 12)] for cfg in ('proxy', 'covered')},
               fan_curves={k: curve_points(c) for k, c in CURVES.items()})
    with open(os.path.join(OUT, 'network.json'), 'w') as fh:
        json.dump(res, fh, indent=1)
    write_md(prm, res)
    return res


def _find(res, cfg, beta=0.0, curve='nominal', speed=1.0, ks=1.0):
    for c in res['cases']:
        if (c['config'], c['beta'], c['curve'], c['speed'], c['kscale']) == (cfg, beta, curve, speed, ks):
            return c
    raise KeyError((cfg, beta, curve, speed, ks))


ROWS = [('proxy', 0.0), ('proxy', 1.0), ('covered', 0.0), ('covered', 1.0), ('ducted', 0.0)]


def _f(x, fmt='%.1f'):
    return fmt % x if isinstance(x, (int, float)) and math.isfinite(x) else str(x)


def tables(prm, res):
    t = []
    t.append('### Inputs\n\n| Vent | node | gross mm2 | open mm2 | open ratio | slots | t mm | K (face) | a_lin Pa/(m/s) |')
    t.append('|---|---|---|---|---|---|---|---|---|')
    for k, v in prm['vents'].items():
        t.append('| %s | %s | %.0f | %.0f | %.3f | %d | %.1f | %.2f | %.3f |' % (
            k, v['node'], v['area_mm2'], v['open_area_mm2'], v['open_area_ratio'], v['n_slots'], v['thickness_mm'],
            v['K'], v['a_lin_Pa_per_mps']))
    c = prm['fan']['curves']
    t.append('\nFan curves dp = dp0 (1 - (Q/Qmax)^n): ' + '; '.join(
        '%s Qmax %.2e m3/s (%.2f CFM), dp0 %.1f Pa, n %.1f' % (k, v['Q_max_m3s'], v['Q_max_m3s'] / CFM, v['dp0_Pa'], v['n'])
        for k, v in c.items()) + '.')
    t.append('\n### Operating points (nominal curve, 100 % speed, K x1)\n')
    t.append('| config | jet credit | Q fan CFM | Q fins m3/s | Q bypass | plenum->body m3/s | recirc. | Q through m3/s '
             '| p_B Pa | p_P Pa | mass resid. |')
    t.append('|---|---|---|---|---|---|---|---|---|---|---|')
    for cfg, b in ROWS:
        r = _find(res, cfg, b)
        t.append('| %s | %.0f | %.3f | %.2e | %.2e | %.2e | %.0f %% | %.2e | %.2f | %.2f | %.0e |' % (
            cfg, b, r['Q_fan_CFM'], r['Q_fin_m3s'], r['Q_bypass_m3s'], r['Q_plenum_to_body_m3s'],
            100 * r['recirculation_fraction'], r['Q_through_m3s'], r['p_Pa']['B'], r['p_Pa']['P'],
            r['mass_residual_m3s']))
    t.append('\n### Flow per vent (m3/s, + = out of the body; nominal, 100 %)\n')
    names = list(prm['vents'])
    t.append('| config | jet | ' + ' | '.join(names) + ' |')
    t.append('|---|---|' + '---|' * len(names))
    for cfg, b in ROWS:
        r = _find(res, cfg, b)
        t.append('| %s | %.0f | ' % (cfg, b) + ' | '.join('%+.2e' % r['vents_m3s_out_positive'][n] for n in names)
                 + ' |')
    for sp in (1.0, 0.5):
        t.append('\n### Temperatures, ambient 30 C (nominal curve, %d %% speed, K x1; all ESTIMATES)\n' % (100 * sp))
        t.append('| config | jet | state | P W | body air C | fin-inlet air C | exhaust bulk dT K | R_sink K/W '
                 '| SoC est. C | body air C, walls | SoC est. C, walls |')
        t.append('|---|---|---|---|---|---|---|---|---|---|---|')
        for cfg, b in ROWS:
            r = _find(res, cfg, b, speed=sp)
            for s in ('S1', 'S2', 'S3'):
                h, w = r['thermal'][s], r['thermal_walls'][s]
                t.append('| %s | %.0f | %s | %.1f | %s | %s | %s | %s | %s | %s | %s |' % (
                    cfg, b, s, h['P_total_W'], _f(h['T_body_C']), _f(h['T_fin_inlet_C']),
                    _f(h['dT_bulk_exhaust_K']), _f(h['R_sink_K_per_W'], '%.2f'), _f(h['T_soc_est_C']),
                    _f(w['T_body_C']), _f(w['T_soc_est_C'])))
    t.append('\n### Sensitivity, S3 SoC estimate C (100 % speed unless stated)\n')
    t.append('| config | jet | nominal | K x0.5 | K x1.5 | curve low | curve high | 50 % speed |')
    t.append('|---|---|---|---|---|---|---|---|')
    for cfg, b in ROWS:
        g = [_find(res, cfg, b)['thermal']['S3']['T_soc_est_C'], _find(res, cfg, b, ks=0.5)['thermal']['S3']['T_soc_est_C'],
             _find(res, cfg, b, ks=1.5)['thermal']['S3']['T_soc_est_C'],
             _find(res, cfg, b, curve='low')['thermal']['S3']['T_soc_est_C'],
             _find(res, cfg, b, curve='high')['thermal']['S3']['T_soc_est_C'],
             _find(res, cfg, b, speed=0.5)['thermal']['S3']['T_soc_est_C']]
        t.append('| %s | %.0f | ' % (cfg, b) + ' | '.join(_f(x) for x in g) + ' |')
    t.append('\nSink R_jc 0.6 / 2.4 K/W and X1203 at eta 0.85 (S3, adiabatic, nominal curve, 100 %):\n')
    for x in res['sink_and_x1203_sensitivity']:
        t.append('- ' + ', '.join('%s %s' % (k, v) for k, v in x.items()))
    t.append('\nNetwork variants (nominal curve, 100 %, adiabatic):\n')
    for v in res['variants']:
        t.append('- %s; %s jet %.0f: recirc. %.0f %%, Q through %.2e, out_wall %+.2e; S2 SoC %s C; S3 SoC %s C, '
                 'body %s C' % (v['what'], v['config'], v['beta'], 100 * v['recirculation_fraction'],
                                v['Q_through_m3s'], v['vents_m3s_out_positive']['out_wall'],
                                _f(v['thermal']['S2']['T_soc_est_C']), _f(v['thermal']['S3']['T_soc_est_C']),
                                _f(v['thermal']['S3']['T_body_C'])))
    return '\n'.join(t)


def write_md(prm, res):
    body = [NARRATIVE(prm, res), tables(prm, res)]
    with open(os.path.join(OUT, 'network.md'), 'w', encoding='utf-8') as fh:
        fh.write('\n\n'.join(body) + '\n')


def NARRATIVE(prm, res):
    g = lambda cfg, b=0.0, **kw: _find(res, cfg, b, **kw)                    # noqa: E731
    th = lambda r, s, k='T_soc_est_C', w=False: r['thermal_walls' if w else 'thermal'][s][k]   # noqa: E731
    d, cv0, cv1, px0, px1 = g('ducted'), g('covered'), g('covered', 1.0), g('proxy'), g('proxy', 1.0)
    d50 = g('ducted', speed=0.5)
    soc_rng = lambda s, rs, w=False: '%.0f-%.0f' % (min(th(r, s, w=w) for r in rs), max(th(r, s, w=w) for r in rs))  # noqa
    L_ = []
    L_.append('# D2 airflow: lumped network model (af-data)\n')
    L_.append('Generated by `airflow/network.py` (numpy only) from `airflow/params.json`; every input carries its '
              'basis there. Basic model, proxy geometry, estimated fan curve and heat loads: **not a measurement; it '
              'does not close G-W11 or G-W12 P4**. It is the quantitative cross-check for the 3D voxel study.\n')
    L_.append('## Model\n')
    L_.append('- Nodes: ambient A (30 C, 0 Pa), body interior B (well mixed), blower outlet F, exhaust plenum P '
              '(ko_exhaust plus the space in front of and over the fins). Branches: fan B->F (curve), fin channels '
              'F->P (laminar plates + entry/exit), the proxy over-fin strip F->P, the plenum-body opening P<->B (no '
              'baffle since J14 T3), vents A<->B (inlet_roof, x1203, sd_slot) and A<->P (out_band, out_corner, '
              'out_wall). Flow directions are solved, not assumed. Newton on the 3 node pressures; mass residual '
              'below 1e-13 m3/s and energy residual below 1e-8 W in every case.')
    L_.append('- Configurations: **proxy** = the CAD as drawn (fins 7.1 high under a 12.9 high blower, open strip '
              'over the fins); **covered** = the real-cooler reading (full-height fins under a cover, no strip); both '
              'with the open plenum of the existing arrangement. **ducted** = a REFERENCE BOUND only (plenum sealed '
              'from the body, i.e. what a working baffle/duct could at best give), not the existing setup.')
    L_.append('- Jet credit beta: fraction of the fin-exit dynamic pressure that stagnates on out_band, 4 mm ahead '
              'of the fins (0 = conservative, 1 = full). A lumped model cannot resolve the jet; the 3D study must.')
    L_.append('- Thermal: upwind enthalpy balance on B, F, P; SoC heat + fan motor heat into the cooler air, all '
              'other loads into the body air; walls adiabatic (base) or UA %.2f W/K (second case). SoC estimate = '
              'fin-inlet air + P_soc x R_sink(Q_fins), R_sink from laminar developing-channel heat transfer + R_jc '
              '1.0 K/W (range 0.6-2.4).\n' % prm['walls']['UA_W_per_K'])
    L_.append('## Findings (estimates)\n')
    L_.append('1. **The vents are not the bottleneck; the fan flow is.** With no recirculation (ducted bound) '
              'the fan delivers %.2f CFM (%.2e m3/s, about 80 %% of free delivery); the fins take %.1f Pa, the vents only %.1f Pa '
              'plenum / %.1f Pa body, of the about 42 Pa the fan can make at shut-off. '
              'Inlets: inlet_roof, x1203 slots and the microSD slot; outlets: out_band, out_corner, out_wall (in '
              'every configuration with out_wall on the plenum).' % (
                  d['Q_fan_CFM'], d['Q_fan_m3s'], d['p_Pa']['F'] - d['p_Pa']['P'], d['p_Pa']['P'], d['p_Pa']['B']))
    L_.append('2. **Recirculation decides the result, and the existing open plenum recirculates.** With the baffle '
              'deleted, the network sends %.0f-%.0f %% of the fan flow from the plenum back into the body '
              '(covered fins) and %.0f-%.0f %% (proxy as drawn): through-flow %.1e-%.1e m3/s instead of %.1e. '
              'Plenum and body differ by under 1 Pa, so small details (jet aim, cables, the camera above the '
              'plenum) move this; the 3D study must measure the recirculation fraction (exhaust-tagged tracer).' % (
                  100 * cv1['recirculation_fraction'], 100 * cv0['recirculation_fraction'],
                  100 * px1['recirculation_fraction'], 100 * px0['recirculation_fraction'],
                  px0['Q_through_m3s'], cv1['Q_through_m3s'], d['Q_through_m3s']))
    L_.append('3. **Even with no recirculation, S3 does not meet G-W11 on these estimates.** One 0.9 CFM blower '
              'carrying %.1f W gives a bulk exhaust rise of %.0f K; SoC estimate %.0f C adiabatic, %.0f C with '
              'wall loss (target < 80 C). S2 (%.1f W): %.0f C ducted; %s C with the open plenum (covered fins, '
              'adiabatic), %s C with wall loss. S1: %s C open plenum.' % (
                  th(d, 'S3', 'P_total_W'), th(d, 'S3', 'dT_bulk_exhaust_K'), th(d, 'S3'), th(d, 'S3', w=True),
                  th(d, 'S2', 'P_total_W'), th(d, 'S2'), soc_rng('S2', (cv0, cv1)), soc_rng('S2', (cv0, cv1), True),
                  soc_rng('S1', (cv0, cv1))))
    L_.append('4. **The CAD cooler proxy is not fit for a thermal answer as drawn.** Its open strip over the fins '
              'takes %.0f %% of the blower flow, leaving %.1e m3/s through the fins (R_sink %.1f K/W against '
              '%.1f with covered fins); the proxy results (S2 SoC %.0f-%.0f C adiabatic) are an artefact of the '
              'proxy until the real SC1148 fin height and cover are measured (MEASURED-PARTS).' % (
                  100 * px0['Q_bypass_m3s'] / px0['Q_fan_m3s'], px0['Q_fin_m3s'], th(px0, 'S2', 'R_sink_K_per_W'),
                  th(cv0, 'S2', 'R_sink_K_per_W'), th(px1, 'S2'), th(px0, 'S2')))
    L_.append('5. **Fan speed:** at 50 %% speed the through-flow halves and every rise doubles (ducted S2 SoC %.0f C, '
              'S1 %.0f C): on these numbers the fan should run at full speed whenever recording (suggestion).' % (th(d50, 'S2'), th(d50, 'S1')))
    L_.append('6. **Sensitivity:** vent/fin K x0.5-x1.5 moves the S3 SoC by %.0f/%+.0f K (covered, beta 0); the fan '
              'curve range low/high by %+.0f/%+.0f K; R_jc 0.6-2.4 by about -4/+14 K. The topology (recirculation, '
              'fin bypass) outweighs every coefficient.\n' % (
                  th(g('covered', ks=0.5), 'S3') - th(cv0, 'S3'), th(g('covered', ks=1.5), 'S3') - th(cv0, 'S3'),
                  th(g('covered', curve='low'), 'S3') - th(cv0, 'S3'),
                  th(g('covered', curve='high'), 'S3') - th(cv0, 'S3')))
    L_.append('## Suggestions for the user (no geometry was changed)\n')
    L_.append('- Restore a path that keeps the fin exhaust out of the body: a duct/baffle from the fin exit to the '
              'front windows (the reference bound roughly doubles the through-flow), placed so it does not block '
              'the stack drop (the reason the baffle was deleted).')
    L_.append('- Measure the real Active Cooler: fin height, whether the fins are covered, blower outlet height; '
              'then fix the proxy before trusting any thermal number.')
    L_.append('- S3 (22 W) exceeds what one 1 CFM blower can carry at 30 C even ideally ducted: cap the load (R-P3 '
              'CPU cap, stick choice) or add flow (second fan / larger blower); G-W12 P4 is expected to fail as '
              'S3 is defined.')
    L_.append('- Physical checks: smoke/tuft at the plenum (does exhaust curl back toward the blower intake?), '
              'anemometer at out_band / out_wall / inlet_roof, thermocouples at the fan intake, plenum, X1203 and '
              'body air, then G-W11.\n')
    L_.append('## Limits\n')
    L_.append('- Fan curve unpublished (range from a 30 mm 5 V reference blower + fan laws). Heat loads are the '
              'WIRING s4.2 estimates. Body node well mixed (overstates intake heating if the exhaust stratifies; '
              'understates local hot spots). No radiation inside; walls adiabatic in the base case. Vent K from '
              'Idelchik-type correlations at Re 100-500 where they are least certain (covered by K x0.5-1.5). The '
              'X1203 boost IC temperature needs its own junction-to-air resistance: only the body air temperature '
              'is given here. Unmodelled leaks: lens turret, seams, floor holes, hood/tub gaps.\n')
    L_.append('## Sources (searched 2026-10-05, 3 searches; read from search summaries, PDFs not opened)\n')
    L_.append('- Raspberry Pi Active Cooler product brief RP-008188 (1.09 CFM, 8000 rpm +-15 %), as recorded in '
              '`cad/gs8-pxl-v2/COMPUTE-OPTICS-COMPONENTS.md`; distributor listings repeat it, e.g. '
              'https://www.pishop.us/product/raspberry-pi-active-cooler/ . No static pressure published.')
    L_.append('- Reference blower Delta BFB0305MA-A (1.2 CFM, 0.206 inH2O = 51.3 Pa, 0.4 W): '
              'https://www.digikey.com/en/products/detail/delta-electronics/BFB0305MA-A/2560683')
    L_.append('- Correlations: Idelchik, Handbook of Hydraulic Resistance (thick perforated plates); Shah & London, '
              'Laminar Flow Forced Convection in Ducts (fRe, K(inf)); Stephan mean Nu for plates (VDI Heat Atlas).')
    L_.append('- Heat loads: `electronics/gs8-d2-v1/WIRING.md` s4.2 and s4.7 (estimates there).\n')
    return '\n'.join(L_)


if __name__ == '__main__':
    main()
    print('wrote params.json, out/network.json, out/network.md')
