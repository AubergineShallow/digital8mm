import math
ZA=60.0; R=28.5; ZF=33.0; OFF=0.5
t=R*math.sqrt(.5); yflat=t-((ZA-t)-ZF)
def inside_lcb(y,z,off=OFF):
    # D-teardrop: circle r R (above the 45 deg tangent points) + 45 deg flanks + flat at ZF, offset by off
    dz=z-ZA
    if z < ZF-off: return False
    if math.hypot(y,dz) <= R+off: return True
    # region between flanks below the tangent points: |y| <= yflat + (z-ZF) (45 deg) widened by off*sqrt2
    if z <= ZA-t and abs(y) <= yflat+(z-ZF)+off*math.sqrt(2): return True
    return False
ears={'S1':(0,88.5),'S2':(27.0,74.0),'S3':(27.0,46.0)}
def inside_open(y,z):
    if inside_lcb(y,z): return True
    return any(math.hypot(y-a,z-b)<=4.7+OFF for a,b in ears.values())
boxes={'out_band':(-26.5,17.5,25.9,29.7),'out_corner':(-31,-21,32,38),'plunger_pocket':(1.9,16.1,0.3,24.7),
       'guard_rim':(2.0,16.0,16.0,25.0),'sd_slot':(-11.5,0.5,15.9,18.6),'plate_left_edge':(35.0,35.0,0.3,100),
       'plate_right_edge':(-32.35,-32.35,0.3,100),'plate_top':(-32.35,35,97.0,97.0)}
res={}
for nm,(y0,y1,z0,z1) in boxes.items():
    best=1e9
    for i in range(0,201):
        for j in range(0,201):
            y=y0+(y1-y0)*i/200; z=z0+(z1-z0)*j/200
            # distance from (y,z) to the opening boundary: brute force over a polar ring of candidate points
            pass
    # sample the opening boundary densely and take min distance to the box
    pts=[]
    for k in range(4000):
        a=2*math.pi*k/4000
        for rr in [x*0.05 for x in range(0,800)]:
            pass
    res[nm]=None
# simpler: grid scan of the plane at 0.1 mm, mark opening cells, compute min distance from each box to any opening cell
step=0.1
cells=[(y/10.0,z/10.0) for y in range(-360,361) for z in range(0,1000) if inside_open(y/10.0,z/10.0)]
for nm,(y0,y1,z0,z1) in boxes.items():
    d=min(math.hypot(max(y0-y,0,y-y1),max(z0-z,0,z-z1)) for y,z in cells)
    res[nm]=round(d,2)
ys=[c[0] for c in cells]; zs=[c[1] for c in cells]
print('opening y',min(ys),max(ys),'z',min(zs),max(zs)); print(res)
# bridge width of the flat (print roof)
print('flat half width at z %.2f: %.2f' % (ZF-OFF, yflat+OFF*math.sqrt(2)-OFF))
