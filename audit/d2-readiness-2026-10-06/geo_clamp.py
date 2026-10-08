"""Auditor scratch: clamp / thermal / insert / stack numbers for notes-geometry.md (no CAD import)."""
import math
g = 9.81
# collar ring (Kowa): bore r 21.15, body r 30, length x 0.3..8.6
r_b, r_o, Lx = 21.15, 30.0, 8.3
A = (r_o - r_b) * Lx                      # hoop section mm2
r_m = (r_o + r_b) / 2
for E, a_p, a_l, dT in ((2000, 95e-6, 23e-6, 30), (1700, 95e-6, 23e-6, 30), (2000, 95e-6, 23e-6, 10)):
    T_loss = E * A * (a_p - a_l) * dT     # N hoop tension lost (ring is the dominant compliance)
    print('E %d dT %d: A %.1f mm2, hoop loss %.0f N; radial mismatch %.4f mm' % (E, dT, A, T_loss, r_b * (a_p - a_l) * dT))
# elastic radial interference produced by hoop tension T
for T in (60, 120, 300):
    print('T %d N -> radial %.4f mm' % (T, T * r_m * r_b / (2000 * A) / r_m))
# screw preload at torque (K 0.2..0.3)
for t in (0.10, 0.15, 0.20, 0.25):
    print('torque %.2f N m -> preload %.0f..%.0f N' % (t, t / (0.3 * 0.003), t / (0.2 * 0.003)))
# M_sep and friction capacities at F = 60 N
F, L, mu, rr = 60.0, 5.4, 0.3, 0.021
print('M_sep %.4f N m; axial friction %.0f N; roll friction %.2f N m' % (math.pi / 6 * F * L / 1e3, mu * 2 * math.pi * F,
                                                                         mu * 2 * math.pi * F * rr))
# free play if preload is lost: radial thermal gap 0.044 on a 5.4 band
gap = 0.044
ang = 2 * gap / 5.4
print('free tilt %.2f deg; at cover rear (30 mm behind band) %.2f mm; at lens front (51 mm) %.2f mm' % (
    math.degrees(ang), ang * 30.5, ang * 51))
# forward slide load lens-down at 5 g (lens + camera + adapter)
print('lens-down 1 g / 5 g axial %.1f / %.1f N' % (0.253 * g, 0.253 * g * 5))
# anchor pivot line LL(28,36)-LR(-19,44) at y 0
zp = 36 + 28 / 47 * 8
print('pitch pivot at y0 z %.1f; lever to top anchors %.1f mm; 5 g tension %.1f N' % (zp, 90.5 - zp,
                                                                                    0.316 / ((90.5 - zp) / 1e3)))
# lateral stack (worst / RSS) collar axis vs lip axis
items = dict(screw_clear=0.2, insert_pos=0.15, bore_pinch=0.15, print_holes=0.1)
print('lateral worst %.2f RSS %.2f vs BFAR 0.75 / adapter 0.825 / body 0.80' % (
    sum(items.values()), math.sqrt(sum(v * v for v in items.values()))))
# image plane (G1): C flange to PCB front = 5.0 + 1.2 + s + 10.35
for s in (0.0, 1.25, 3.0):
    print('s %.2f C->PCB %.2f; needed 17.526+0.37 = 17.90 + die' % (s, 16.55 + s))
