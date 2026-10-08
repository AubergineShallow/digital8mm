"""fix-candidate VC-M1 evidence (no CAD, trimesh on the built STLs): local ray-thickness scan (the checks.thin_wall cone method,
dense, within 3 mm) round the unclassified thin spot reported only by the screw1 builds. STLs are in print pose (tub face_down -Y);
they are mapped back to assembly coordinates: x = px - 154, y = pz - 35, z = 97.3 - py. Run from the repo root."""
import sys, numpy as np, trimesh, hashlib, math
sys.path.insert(0,r'C:\Users\Pre-Installed User\Claude\Projects\8mm\cad\gs8-d2-v1\candidate-fr1')
from checks import _ray_hits
P=np.array([float(x) for x in sys.argv[1:4]]) if len(sys.argv)>3 else np.array([-12.95,31.85,20.75])
R=3.0
base=r'C:\Users\Pre-Installed User\Claude\Projects\8mm\cad\gs8-d2-v1'
for tag,p in [('r2 ../out',base+r'\out\stl\tub.stl'),('fr all',base+r'\candidate-fr1\out\stl\tub.stl'),('fr none',base+r'\candidate-fr1\out\_none\stl\tub.stl'),('fr screw1',base+r'\candidate-fr1\out\_int-hood-screw1-r3m\stl\tub.stl'),('fr yslide',base+r'\candidate-fr1\out\_int-hood-yslide-r3m\stl\tub.stl')]:
    m=trimesh.load(p); V0=np.asarray(m.vertices); V=np.c_[V0[:,0]-154.0, V0[:,2]-35.0, 97.3-V0[:,1]]; F=np.asarray(m.faces); m=trimesh.Trimesh(V,F,process=False)
    a,b,c=V[F[:,0]],V[F[:,1]],V[F[:,2]]
    cen=(a+b+c)/3
    lo=np.minimum(np.minimum(a,b),c); hi=np.maximum(np.maximum(a,b),c); keep=np.linalg.norm(np.clip(P,lo,hi)-P,axis=1)<R
    cr=np.cross(b-a,c-a); ar=np.linalg.norm(cr,axis=1)/2; N0=m.face_normals
    rng=np.random.default_rng(1); idx=np.where(keep&(ar>1e-9))[0]
    pick=rng.choice(idx,size=20000,p=ar[idx]/ar[idx].sum())
    r1,r2=rng.random(20000),rng.random(20000); fl=r1+r2>1; r1[fl],r2[fl]=1-r1[fl],1-r2[fl]
    pts=a[pick]+r1[:,None]*(b[pick]-a[pick])+r2[:,None]*(c[pick]-a[pick]); N=N0[pick]
    s=np.linalg.norm(pts-P,axis=1)<R; pts,N=pts[s],N[s]
    O=pts-N*1e-3
    th=_ray_hits(V,F,O,-N); th=np.where(np.isfinite(th),th,6.0)
    ref=np.where(np.abs(N[:,0:1])<0.9,np.array([[1.,0,0]]),np.array([[0,1.,0]]))
    U=np.cross(N,ref);U/=np.linalg.norm(U,axis=1)[:,None];W=np.cross(N,U)
    ct,st=math.cos(math.radians(30)),math.sin(math.radians(30))
    for k in range(6):
        ph=math.radians(60*k);Dk=-N*ct+(U*math.cos(ph)+W*math.sin(ph))*st
        dk=_ray_hits(V,F,O,Dk);th=np.maximum(th,np.where(np.isfinite(dk),dk,6.0)*ct)
    i=np.argmin(th)
    print(tag, hashlib.sha256(open(p,'rb').read()).hexdigest()[:8], 'n=%d min=%.3f at %s nrm %s; share<1.15=%.3f; bbox<1.15 %s'%(len(th),th[i],np.round(pts[i],2),np.round(N[i],2),(th<1.15).mean(), (np.round(pts[th<1.15].min(0),2).tolist(),np.round(pts[th<1.15].max(0),2).tolist()) if (th<1.15).any() else '-'))
