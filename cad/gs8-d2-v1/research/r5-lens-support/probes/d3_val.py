import numpy as np
from d3_plate import acm_k
# cantilever strip: length L along y (clamped y=0), width W along z, end force P at y=L -> tip w = P L^3/(3 D W)
L, W, t, E, nu = 60.0, 20.0, 2.5, 2000.0, 0.35
ny, nz = 30, 10
a, b = L/ny, W/nz
d = E*t**3/(12*(1-nu*nu)); Dm = d*np.array([[1,nu,0],[nu,1,0],[0,0,(1-nu)/2]])
ke = acm_k(a, b, Dm)
nn=(ny+1)*(nz+1); N=3*nn; K=np.zeros((N,N))
for i in range(ny):
  for j in range(nz):
    ns=[i*(nz+1)+j,(i+1)*(nz+1)+j,(i+1)*(nz+1)+j+1,i*(nz+1)+j+1]
    dofs=np.array([[3*n,3*n+1,3*n+2] for n in ns]).ravel(); K[np.ix_(dofs,dofs)]+=ke
fixed={3*n+k for n in range(nz+1) for k in range(3)}
free=np.array(sorted(set(range(N))-fixed)); F=np.zeros(N); P=1.0
for j in range(nz+1): F[3*(ny*(nz+1)+j)] += P/(nz+1)
u=np.zeros(N); u[free]=np.linalg.solve(K[np.ix_(free,free)],F[free])
tip=np.mean([u[3*(ny*(nz+1)+j)] for j in range(nz+1)])
print('FE tip', tip, 'beam(D) ', P*L**3/(3*d*W), 'beam(E)', P*L**3/(3*E*W*t**3/12))
