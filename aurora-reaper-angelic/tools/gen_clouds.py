import numpy as np, struct
from PIL import Image
rng=np.random.default_rng(7)

# ---------- icosphere ----------
def icosphere(sub):
    t=(1+5**.5)/2
    V=[[-1,t,0],[1,t,0],[-1,-t,0],[1,-t,0],[0,-1,t],[0,1,t],[0,-1,-t],[0,1,-t],[t,0,-1],[t,0,1],[-t,0,-1],[-t,0,1]]
    F=[[0,11,5],[0,5,1],[0,1,7],[0,7,10],[0,10,11],[1,5,9],[5,11,4],[11,10,2],[10,7,6],[7,1,8],[3,9,4],[3,4,2],[3,2,6],[3,6,8],[3,8,9],[4,9,5],[2,4,11],[6,2,10],[8,6,7],[9,8,1]]
    V=[np.array(v,float)/np.linalg.norm(v) for v in V]
    for _ in range(sub):
        cache={}; NF=[]
        def mid(a,b):
            k=(min(a,b),max(a,b))
            if k not in cache:
                m=V[a]+V[b]; V.append(m/np.linalg.norm(m)); cache[k]=len(V)-1
            return cache[k]
        for a,b,c in F:
            ab,bc,ca=mid(a,b),mid(b,c),mid(c,a); NF+= [[a,ab,ca],[b,bc,ab],[c,ca,bc],[ab,bc,ca]]
        F=NF
    return np.array(V),np.array(F)
SV,SF=icosphere(2)

# ---------- smooth 3D value noise for lumpy puffs ----------
G=rng.normal(size=(8,3)); Gp=rng.uniform(0,2*np.pi,8)
def lump(d,seed):
    r=np.random.default_rng(seed); a=r.normal(size=(6,3)); ph=r.uniform(0,2*np.pi,6); fr=r.uniform(1.5,3.5,6)
    s=np.zeros(len(d))
    for i in range(6): s+=np.sin(fr[i]*(d@ (a[i]/np.linalg.norm(a[i])))+ph[i])/ (1+i*0.6)
    return s/3.0

# ---------- lay out puffs around the ring ----------
R0=585.0; YB=-30.0
puffs=[]  # (center, radii xyz, seed)
def add(theta, rr, y, size, flat=0.75):
    c=np.array([rr*np.cos(theta), y, rr*np.sin(theta)])
    puffs.append((c, np.array([size*rng.uniform(1.0,1.25), size*flat, size*rng.uniform(1.0,1.25)]), int(rng.integers(1e9)), theta))
N1=44
for i in range(N1):  # broad low base layer (wide flat billows)
    th=2*np.pi*(i+rng.uniform(-.3,.3))/N1
    add(th, R0+rng.uniform(-35,35), YB+38, rng.uniform(78,96), flat=0.55)
N2=38
for i in range(N2):  # main body puffs
    th=2*np.pi*(i+0.5+rng.uniform(-.3,.3))/N2
    add(th, R0+rng.uniform(-25,25), YB+85+rng.uniform(-10,15), rng.uniform(62,80), flat=0.85)
N3=26
for i in range(N3):  # cumulus tops
    th=2*np.pi*(i+rng.uniform(-.35,.35))/N3
    add(th, R0+rng.uniform(-20,20), YB+135+rng.uniform(-10,15), rng.uniform(52,66), flat=0.9)
N4=12
for i in range(N4):  # a few towering crowns
    th=2*np.pi*(i+rng.uniform(-.4,.4))/N4
    add(th, R0+rng.uniform(-15,15), YB+175+rng.uniform(-8,12), rng.uniform(42,52), flat=0.95)
N5=40
for i in range(N5):  # small wisps hugging inner/outer skirts
    th=2*np.pi*(i+rng.uniform(-.5,.5))/N5; side=1 if i%2 else -1
    add(th, R0+side*rng.uniform(55,80), YB+14, rng.uniform(46,60), flat=0.5)

# painter's order for League's camera (south, looking north & down ~56deg): far puffs first
VIEW=np.array([0,-np.sin(np.radians(56)),np.cos(np.radians(56))])
puffs.sort(key=lambda p: -(p[0]@VIEW))
C=np.array([p[0] for p in puffs]); RAD=np.array([p[1] for p in puffs])
def inside_count(pts, skip):
    # how many other puffs contain each point (ellipsoid test) -> occlusion
    cnt=np.zeros(len(pts))
    for j,(c,r,_,_) in enumerate(puffs):
        if j==skip: continue
        q=((pts-c)/r)**2; cnt+= (q.sum(1)<1.0)
    return cnt

L=np.array([0.55,1.0,-0.65]); L/=np.linalg.norm(L)
allP=[];allN=[];allUV=[];allF=[]; base=0
for k,(c,r,seed,th) in enumerate(puffs):
    d=SV.copy()
    disp=1+0.16*lump(d,seed)
    p=d*disp[:,None]*r
    p[:,1]=np.maximum(p[:,1], -r[1]*0.35)          # flatten underside like real cumulus
    p=p+c
    p[:,1]=np.maximum(p[:,1], YB-8)
    # normals from faces
    n=np.zeros_like(p)
    fn=np.cross(p[SF[:,1]]-p[SF[:,0]], p[SF[:,2]]-p[SF[:,0]])
    for i in range(3): np.add.at(n,SF[:,i],fn)
    n/=np.linalg.norm(n,axis=1,keepdims=True)+1e-9
    # shading term -> u ; height -> v
    lam=0.5+0.5*(n@L)
    occ=inside_count(p+n*18.0,k)          # surfaces nestled against neighbours get soft shadow
    occ=np.clip(1-0.3*occ,0.4,1)
    out=np.array([np.cos(th),0,np.sin(th)])
    rim=np.clip(1-np.abs(n@np.array([0,1,0])),0,1)*0.0
    u=np.clip((lam**1.35)*occ,0,1)
    h=(p[:,1]-YB)/(260.0)
    v=np.clip(h,0,1)
    # within a puff, also draw far triangles first
    order=np.argsort(-(p[SF].mean(1)@VIEW)); SFo=SF[order]
    allP.append(p);allN.append(n);allUV.append(np.stack([0.03+0.94*u,0.97-0.94*v],1));allF.append(SFo+base); base+=len(p)
P=np.concatenate(allP);N=np.concatenate(allN);UV=np.concatenate(allUV);F=np.concatenate(allF)
print('verts',len(P),'tris',len(F),'y',P[:,1].min(),P[:,1].max(),'r',np.hypot(P[:,0],P[:,2]).min(),np.hypot(P[:,0],P[:,2]).max())
assert len(P)<65536

# ---------- write SKN v1.1 (same layout as original) ----------
def write_skn(path,P,N,UV,F):
    b=bytearray(struct.pack('<IHH',0x00112233,1,1))
    b+=struct.pack('<I',1)+b'Body'.ljust(64,b'\0')+struct.pack('<IIII',0,len(P),0,F.size)
    b+=struct.pack('<II',F.size,len(P))
    b+=F.astype('<u2').tobytes()
    for p,n,uv in zip(P,N,UV):
        b+=struct.pack('<3f4B4f3f2f',*p,0,0,0,0,1.0,0.0,0.0,0.0,*n,*uv)
    open(path,'wb').write(bytes(b))
write_skn('out/heaven_wall.skn',P,N,UV,F)
np.savez('out/heaven_wall.npz',P=P,N=N,UV=UV,F=F)

# ---------- ramp texture: x = light (shadow->sunlit), y = height (top->bottom) ----------
W=H=256
x=np.linspace(0,1,W)[None,:].repeat(H,0); y=np.linspace(0,1,H)[:,None].repeat(W,1)   # y=0 top of texture = high clouds
hgt=1-(y-0.03)/0.94
def lerp(a,b,t): return a+(b-a)*t[...,None]
shadow=np.array([206,182,140.]); mid=np.array([245,236,220.]); lit=np.array([255,252,246.]); hot=np.array([255,255,252.])
t=np.clip(x,0,1)
col=np.where((t<0.5)[...,None], lerp(shadow,mid,np.clip(t/0.5,0,1)**0.9), lerp(mid,lit,np.clip((t-0.5)/0.4,0,1)))
col=np.where((t>0.9)[...,None], lerp(lit,hot,np.clip((t-0.9)/0.1,0,1)), col)
# golden heavenly underglow near the base, matching the gold used across the skin's VFX (~0.70,0.57,0.31)
gold=np.array([236,198,118.])
g=np.clip(1-hgt/0.24,0,1)**1.4
col=col*(1-0.55*g[...,None])+gold*(0.55*g[...,None])
# soft sun-gold kiss on the very tops
top=np.clip((hgt-0.75)/0.25,0,1)*np.clip((t-0.6)/0.4,0,1)
col=lerp(col,np.array([255,240,205.]),0.35*top)
# subtle grain so DXT doesn't band
col+=rng.normal(0,1.2,col.shape)
alpha=np.clip(0.2+hgt/0.12,0,1)*255     # base dissolves into mist on the ground
img=np.dstack([np.clip(col,0,255),alpha]).astype(np.uint8)
Image.fromarray(img,'RGBA').save('out/heaven_wall_ramp.png')
