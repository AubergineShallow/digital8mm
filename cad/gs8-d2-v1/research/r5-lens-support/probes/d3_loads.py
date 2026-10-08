"""Designer 3 load-path arithmetic (D2 stack: C flange x 10.6, LCB/wall interface x -2.7)."""
import math, json
g = 9.81
E, t_s, CREEP = 2000.0, 3.5, 2.2          # MPa, sleeve wall, 1000 h / 45-50 C modulus knock-down
WALL = (0.079, 0.146)                      # deg per N m, plate FE (left tied by S2/S3 .. left free)
lenses = {  # mass kg, CoM from flange, band (x0, x1 from flange), band r, hand load (N, x from flange)
  'Kowa LM6HC 215 g':      (0.215, 28.3, (2.2, 7.6), 21.0, (15.0, 50.0)),
  'Fujinon HF6XA 100 g':   (0.100, 25.3, (1.0, 8.0), 19.5, (15.0, 45.0)),
  'Computar H6Z0812 305 g':(0.305, 39.2, (1.0, 23.0), 24.25, (20.0, 70.0)),
  'Optivaron 6-66 600 g':  (0.600, 55.2, (2.0, 22.0), 30.0, (20.0, 80.0)),
}
XF, XW = 10.6, -2.7
out = {}
for nm, (m, c, (b0, b1), rb, (Fh, xh)) in lenses.items():
    L = b1 - b0; bc = 0.5 * (b0 + b1)
    kw = E / t_s
    k_s = 0.5 * kw * (math.pi / 2) * rb * L**3 / 12.0          # N mm / rad, sleeve tilt (knurl/split factor 0.5)
    arm_w = XF + c - XW; arm_s = c - bc
    rows = {}
    for case, (F, xs) in {'static': (m * g, c), '5 g': (5 * m * g, c), 'hand': (Fh, xh)}.items():
        Mw = F * (XF + xs - XW) / 1000.0; Ms = F * (xs - bc) / 1000.0     # N m
        th = Ms * 1000 / k_s * 180 / math.pi + Mw * WALL[0]
        th_hi = Ms * 1000 / k_s * 180 / math.pi + Mw * WALL[1]
        rows[case] = dict(M_wall_Nm=round(Mw, 3), M_sleeve_Nm=round(Ms, 3),
                          aim_deg=(round(th, 3), round(th_hi, 3)),
                          wall_sigma_MPa=(round(Mw * 2.3, 2), round(Mw * 4.7, 2)))
    rows['static creep aim_deg'] = (round(rows['static']['aim_deg'][0] * CREEP, 3), round(rows['static']['aim_deg'][1] * CREEP, 3))
    rows['k_sleeve_Nmm_per_rad'] = round(k_s, -3)
    # today: wall at r 20 seat (0.48..0.74 deg/Nm) about the seat x -5.2 + 0.83 deg free rocking (Kowa only meaningful)
    Mt = m * g * (XF + c + 5.2) / 1000.0
    rows['today_static_M_seat_Nm'] = round(Mt, 3)
    rows['today_static_wall_deg'] = (round(Mt * 0.48, 3), round(Mt * 0.74, 3))
    out[nm] = rows
print(json.dumps(out, indent=0))
json.dump(out, open('d3_loads.json', 'w'), indent=1)
