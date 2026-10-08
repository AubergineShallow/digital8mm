"""Plate FE with stress output: tub front wall + rigid disc (LCB contact) of radius rd; left edge ss = panel tie (S2/S3)."""
import numpy as np, itertools, json
from d3_plate import acm_k
def solve(rd=28.5, t=2.5, E=2000.0, nu=0.35, h=1.9, left='ss', top='free', load='pitch', holes=True):
    y0, y1, z0, z1 = -35.0, 32.2, 0.0, 97.3
    ny, nz = int(round((y1-y0)/h)), int(round((z1-z0)/h)); ys, zs = np.linspace(y0,y1,ny+1), np.linspace(z0,z1,nz+1)
    a, b = ys[1]-ys[0], zs[1]-zs[0]
    def Dm(tt):
        d = E*tt**3/(12*(1-nu*nu)); return d*np.array([[1,nu,0],[nu,1,0],[0,0,(1-nu)/2]])
    hole_boxes = [(-26.5,17.5,25.9,29.7),(-31,-21,32,38),(3.2,14.8,17.2,23.8),(-11.5,0.5,15.9,18.6)]
    nn=(ny+1)*(nz+1); N=3*nn; K=np.zeros((N,N)); cache={}; elems=[]
    for i in range(ny):
        for j in range(nz):
            yc, zc = (ys[i]+ys[i+1])/2, (zs[j]+zs[j+1])/2
            tt = t
            if holes and any(p<=yc<=q and r<=zc<=s for p,q,r,s in hole_boxes): tt = 0.05
            if np.hypot(yc, zc-60) <= rd: tt = 40.0
            if tt not in cache: cache[tt] = acm_k(a, b, Dm(tt))
            ns=[i*(nz+1)+j,(i+1)*(nz+1)+j,(i+1)*(nz+1)+j+1,i*(nz+1)+j+1]
            dofs=np.array([[3*n,3*n+1,3*n+2] for n in ns]).ravel(); K[np.ix_(dofs,dofs)]+=cache[tt]
            elems.append((i,j,yc,zc,tt,dofs))
    fixed=set()
    for i in range(ny+1):
        for j in range(nz+1):
            n=i*(nz+1)+j
            if i==0 or j==0: fixed|={3*n,3*n+1,3*n+2}
            if i==ny and left=='ss': fixed|={3*n}
            if j==nz and top=='ss': fixed|={3*n}
    free=np.array(sorted(set(range(N))-fixed)); F=np.zeros(N)
    disc=[(i,j) for i in range(ny+1) for j in range(nz+1) if np.hypot(ys[i],zs[j]-60)<=rd-0.5]
    arm=np.array([(zs[j]-60) if load=='pitch' else ys[i] for i,j in disc]); f=arm/np.sum(arm*arm)*1000.0
    for (i,j),fi in zip(disc,f): F[3*(i*(nz+1)+j)]+=fi
    u=np.zeros(N); u[free]=np.linalg.solve(K[np.ix_(free,free)],F[free])
    w=np.array([u[3*(i*(nz+1)+j)] for i,j in disc]); rot=np.sum(w*arm)/np.sum(arm*arm)
    # curvature at element centres (polynomial fit of the ACM field)
    def P(x,y): return np.array([1,x,y,x*x,x*y,y*y,x**3,x*x*y,x*y*y,y**3,x**3*y,x*y**3])
    def Px(x,y): return np.array([0,1,0,2*x,y,0,3*x*x,2*x*y,y*y,0,3*x*x*y,y**3])
    def Py(x,y): return np.array([0,0,1,0,x,2*y,0,x*x,2*x*y,3*y*y,x**3,3*x*y*y])
    nodes=[(0,0),(a,0),(a,b),(0,b)]
    Ci=np.linalg.inv(np.array([row for (x,y) in nodes for row in (P(x,y),Px(x,y),Py(x,y))]))
    xc,yc_=a/2,b/2
    Pxx=np.array([0,0,0,2,0,0,6*xc,2*yc_,0,0,6*xc*yc_,0]); Pyy=np.array([0,0,0,0,0,2,0,0,2*xc,6*yc_,0,6*xc*yc_])
    Pxy=np.array([0,0,0,0,1,0,0,2*xc,2*yc_,0,3*xc*xc,3*yc_*yc_])
    smax={'sy':(0,None),'sz':(0,None)}
    d=E*t**3/(12*(1-nu*nu))
    for (i,j,yc,zc,tt,dofs) in elems:
        if tt!=t: continue
        c=Ci@u[dofs]; kyy, kzz = Pxx@c, Pyy@c
        my=-d*(kyy+nu*kzz); mz=-d*(kzz+nu*kyy)
        sy, sz = 6*abs(my)/t**2, 6*abs(mz)/t**2
        if sy>smax['sy'][0]: smax['sy']=(sy,(round(yc,1),round(zc,1)))
        if sz>smax['sz'][0]: smax['sz']=(sz,(round(yc,1),round(zc,1)))
    return rot, smax
out={}
for name, kw in [('LCB rd28.5 pitch (left ss, top free)', dict(rd=28.5)),
                 ('LCB rd28.5 yaw (left ss, top free)', dict(rd=28.5, load='yaw')),
                 ('LCB rd28.5 pitch (left free, top free)', dict(rd=28.5, left='free')),
                 ('today seat rd20 pitch (left free, top free)', dict(rd=20.0, left='free')),
                 ('today seat rd20 pitch (left ss, top free)', dict(rd=20.0))]:
    rot, s = solve(**kw); out[name]=dict(rot_deg_per_Nm=float(np.degrees(rot)), sigma_y_MPa_per_Nm=s['sy'], sigma_z_MPa_per_Nm=s['sz'])
    print(name, json.dumps(out[name]), flush=True)
json.dump(out, open('d3_plate3.json','w'), indent=1)
