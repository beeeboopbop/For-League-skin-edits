"""Heavenly cumulus ring for Aurora's R (replaces yeswall.skn) - v3.
Each puff is cube-mapped into its own tiles of a 2048x2048 atlas; every texel is baked
with surface detail noise, wrap lighting, ray-traced AO, gold rim and base glow."""
import numpy as np, struct
from PIL import Image
rng=np.random.default_rng(11)

# ---------------- geometry helpers ----------------
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
            ab,bc,ca=mid(a,b),mid(b,c),mid(c,a); NF+=[[a,ab,ca],[b,bc,ab],[c,ca,bc],[ab,bc,ca]]
        F=NF
    return np.array(V),np.array(F)
SPH={2:icosphere(2),3:icosphere(3)}

def make_billow(seed,n_lobes,amp=0.30):
    r=np.random.default_rng(seed)
    lob=[]
    for _ in range(n_lobes):
        c=r.normal(size=3); c[1]=abs(c[1])*0.7+0.05; c/=np.linalg.norm(c)
        lob.append((c,r.uniform(0.3,0.75),r.uniform(0.45,1.0)))
    a=r.normal(size=(5,3)); a/=np.linalg.norm(a,axis=1,keepdims=True); ph=r.uniform(0,6.3,5)
    def f(d):
        s=np.zeros(d.shape[:-1])
        for c,w,h in lob:
            x=np.clip((d@c-np.cos(w))/(1-np.cos(w)),0,1); s=np.maximum(s,h*np.sin(x*np.pi/2)**0.8)
        fine=sum(np.sin(7*(d@a[i])+ph[i]) for i in range(5))/5
        return 1+amp*s+0.03*fine
    return f

# ---------------- 3D value noise (detail texture) ----------------
PERM=np.random.default_rng(5).permutation(256); PERM=np.concatenate([PERM,PERM])
def vnoise(p):
    pi=np.floor(p).astype(int); pf=p-pi; u=pf*pf*(3-2*pf)
    X,Y,Z=pi[...,0]&255,pi[...,1]&255,pi[...,2]&255
    def h(i,j,k): return PERM[PERM[PERM[X+i]+Y+j]+Z+k]/255.0
    l=lambda a,b,t:a+(b-a)*t
    x0=l(l(h(0,0,0),h(1,0,0),u[...,0]),l(h(0,1,0),h(1,1,0),u[...,0]),u[...,1])
    x1=l(l(h(0,0,1),h(1,0,1),u[...,0]),l(h(0,1,1),h(1,1,1),u[...,0]),u[...,1])
    return l(x0,x1,u[...,2])*2-1
def fbm(p,oct=4):
    s=0;a=0.5;f=1
    for _ in range(oct): s+=a*vnoise(p*f); f*=2.03; a*=0.5
    return s

# micro-puffs: union of small soft domes on a jittered 3D grid (cauliflower surface)
def micro(p,scale,seed):
    q=p/scale; base=np.floor(q).astype(int); best=np.zeros(len(p))
    for dx in (-1,0,1):
        for dy in (-1,0,1):
            for dz in (-1,0,1):
                c=base+np.array([dx,dy,dz])
                hsh=(c[:,0]*73856093)^(c[:,1]*19349663)^(c[:,2]*83492791)^seed
                r=np.random.default_rng(0)  # deterministic jitter from hash
                jx=((hsh*1103515245+12345)&0xffff)/65535.0; jy=((hsh*22695477+1)&0xffff)/65535.0; jz=((hsh*134775813+7)&0xffff)/65535.0
                rad=0.55+0.35*(((hsh*48271)&0xff)/255.0)
                f=c+np.stack([jx,jy,jz],1)
                dd=np.linalg.norm(q-f,axis=1)/rad
                best=np.maximum(best,np.sqrt(np.clip(1-dd*dd,0,1)))
    return best
def micro_h(p): return 0.75*micro(p,17.0,17)+0.25*micro(p,9.0,91)

# ---------------- layout: slimmer, lower ring ----------------
R0=585.0; YB=-30.0
puffs=[]
def add(theta, rr, y, size, flat, sub, lobes):
    c=np.array([rr*np.cos(theta), y, rr*np.sin(theta)])
    rad=np.array([size*rng.uniform(1.0,1.2), size*flat, size*rng.uniform(1.0,1.2)])
    puffs.append(dict(c=c,r=rad,f=make_billow(int(rng.integers(1e9)),lobes),sub=sub))
for i in range(44):   # base billows (bottoms sink below ground)
    th=2*np.pi*(i+rng.uniform(-.3,.3))/44
    add(th, R0+rng.uniform(-25,25), YB+20, rng.uniform(60,72), 0.55, 3, 10)
for i in range(40):   # body
    th=2*np.pi*(i+0.5+rng.uniform(-.3,.3))/40
    add(th, R0+rng.uniform(-16,16), YB+58+rng.uniform(-6,9), rng.uniform(46,56), 0.8, 2, 9)
for i in range(26):   # cumulus heads
    th=2*np.pi*(i+rng.uniform(-.35,.35))/26
    add(th, R0+rng.uniform(-12,12), YB+94+rng.uniform(-6,10), rng.uniform(36,44), 0.85, 2, 8)
for i in range(10):   # crowns
    th=2*np.pi*(i+rng.uniform(-.4,.4))/10
    add(th, R0+rng.uniform(-10,10), YB+124+rng.uniform(-5,8), rng.uniform(28,34), 0.9, 2, 6)
for i in range(30):   # skirt wisps
    th=2*np.pi*(i+rng.uniform(-.5,.5))/30; side=1 if i%2 else -1
    add(th, R0+side*rng.uniform(52,70), YB+8, rng.uniform(26,34), 0.5, 2, 4)
NPF=len(puffs)

VIEW=np.array([0,-np.sin(np.radians(56)),np.cos(np.radians(56))]); TOCAM=-VIEW
L=np.array([-0.55,0.8,0.45]); L/=np.linalg.norm(L)        # sun behind the ring, upper-left
OC=np.array([p['c'] for p in puffs]); OR=np.array([p['r']*1.05 for p in puffs]); SR=OR.mean(1)*0.9

def surf(k,d):
    """surface point of puff k in direction(s) d"""
    p=puffs[k]; q=d*p['f'](d)[...,None]*p['r']
    q[...,1]=np.maximum(q[...,1],-p['r'][1]*0.4)
    return q+p['c']
def surf_normal(k,d):
    # finite differences on the sphere parameterisation
    t1=np.cross(d,np.array([0,1,0.0])); bad=np.linalg.norm(t1,axis=-1)<1e-3
    t1[bad]=np.cross(d[bad],np.array([1,0,0.0])); t1/=np.linalg.norm(t1,axis=-1,keepdims=True)
    t2=np.cross(d,t1); e=0.01
    nd=lambda v: v/np.linalg.norm(v,axis=-1,keepdims=True)
    a=surf(k,nd(d+e*t1))-surf(k,nd(d-e*t1)); b=surf(k,nd(d+e*t2))-surf(k,nd(d-e*t2))
    n=np.cross(a,b); n/=np.linalg.norm(n,axis=-1,keepdims=True)+1e-9
    flip=(n*(surf(k,d)-puffs[k]['c'])).sum(-1)<0; n[flip]*=-1
    return n
NEAR=[[j for j in range(NPF) if j!=k and np.linalg.norm(OC[j]-OC[k])<SR[j]+SR[k]+260] for k in range(NPF)]
dirs=np.random.default_rng(3).normal(size=(20,3)); dirs/=np.linalg.norm(dirs,axis=1,keepdims=True)
def ao(k,pts,nrm):
    occ=np.zeros(len(pts)); tot=np.zeros(len(pts)); o=pts+nrm*3
    for dv in dirs:
        w=np.clip(nrm@dv,0,1); hit=np.zeros(len(pts),bool)
        for j in NEAR[k]:
            oc=o-OC[j]; b=oc@dv; c=(oc**2).sum(1)-SR[j]**2; disc=b*b-c
            t=-b-np.sqrt(np.maximum(disc,0)); hit|=(disc>0)&(t>0)&(t<200)
        if dv[1]<0: hit|=(o[:,1]-(YB+5))/(-dv[1])<200
        occ+=w*hit; tot+=w
    return 1-occ/np.maximum(tot,1e-6)
def inside_any(k,pts):
    m=np.zeros(len(pts),bool)
    for j in NEAR[k]: m|=(((pts-OC[j])/(OR[j]*0.92))**2).sum(1)<1
    return m

# ---------------- cube-map tile projection ----------------
# face f: major axis index ax, sign sg; (s,t) in [0,1] across the face
FACES=[(0,1),(0,-1),(1,1),(1,-1),(2,1),(2,-1)]
def face_of(d):
    ax=np.argmax(np.abs(d),-1); sg=np.sign(d[np.arange(len(d)),ax]); return ax*2+(sg<0)
def proj(d,f):
    ax,sg=FACES[f]; o=[i for i in range(3) if i!=ax]
    m=np.abs(d[:,ax])
    return np.stack([(d[:,o[0]]/m*sg+1)/2,(d[:,o[1]]/m+1)/2],1)
def unproj(st,f):
    ax,sg=FACES[f]; o=[i for i in range(3) if i!=ax]
    d=np.zeros(st.shape[:-1]+(3,)); d[...,ax]=sg; d[...,o[0]]=(st[...,0]*2-1)*sg; d[...,o[1]]=st[...,1]*2-1
    return d/np.linalg.norm(d,axis=-1,keepdims=True)

ATL=2048; TILE=64; PADS=0.36          # each tile covers s,t in [-PADS,1+PADS]
PER=ATL//TILE
def tile_uv(st,slot):
    tx,ty=slot%PER,slot//PER
    s=(st+PADS)/(1+2*PADS)
    return np.stack([(tx+s[:,0])*TILE/ATL,(ty+s[:,1])*TILE/ATL],1)

# ---------------- build mesh ----------------
order=sorted(range(NPF),key=lambda k:-(OC[k]@VIEW))
allP=[];allN=[];allUV=[];allF=[];base=0;slots=[];culled=0
for k in order:
    SV,SF=SPH[puffs[k]['sub']]
    q=surf(k,SV.copy()); n=surf_normal(k,SV.copy())
    ins=inside_any(k,q)|(q[:,1]<YB-10)
    keep=~ins[SF].all(1); culled+=(~keep).sum(); F=SF[keep]
    fc=face_of(SV[F].mean(1))
    for f in range(6):
        Ff=F[fc==f]
        if len(Ff)==0: continue
        slot=len(slots); slots.append((k,f))
        used=np.unique(Ff); remap=-np.ones(len(SV),int); remap[used]=np.arange(len(used))
        st=proj(SV[used],f); assert st.min()>-PADS and st.max()<1+PADS, (st.min(),st.max())
        Fl=remap[Ff]; Fl=Fl[np.argsort(-(q[used][Fl].mean(1)@VIEW))]
        allP.append(q[used]);allN.append(n[used]);allUV.append(tile_uv(st,slot));allF.append(Fl+base);base+=len(used)
assert len(slots)<=PER*PER, len(slots)
# merge faces of the same puff into painter order: already grouped by puff (far first)
P=np.concatenate(allP);N=np.concatenate(allN);UV=np.concatenate(allUV);F=np.concatenate(allF)
print('puffs',NPF,'tiles',len(slots),'verts',len(P),'tris',len(F),'culled',culled,'y',P[:,1].min().round(),P[:,1].max().round(),
      'r',np.hypot(P[:,0],P[:,2]).min().round(),np.hypot(P[:,0],P[:,2]).max().round())
assert len(P)<65536

def write_skn(path,P,N,UV,F):
    b=bytearray(struct.pack('<IHH',0x00112233,1,1))
    b+=struct.pack('<I',1)+b'Body'.ljust(64,b'\0')+struct.pack('<IIII',0,len(P),0,F.size)
    b+=struct.pack('<II',F.size,len(P))+F.astype('<u2').tobytes()
    for p,n,uv in zip(P,N,UV): b+=struct.pack('<3f4B4f3f2f',*p,0,0,0,0,1.0,0.0,0.0,0.0,*n,*uv)
    open(path,'wb').write(bytes(b))
write_skn('out/heaven_wall.skn',P,N,UV,F)

# ---------------- bake atlas ----------------
keys=np.array([0.0,0.35,0.7,0.9,1.0])
WHITE=np.array([[170,146,120],[216,198,174],[242,236,228],[253,251,247],[255,255,255]],float)
GOLD=np.array([[160,124,78],[214,172,100],[246,206,128],[255,228,160],[255,242,200]],float)
def ramp(tab,x): return np.stack([np.interp(x,keys,tab[:,i]) for i in range(3)],-1)
atlas=np.zeros((ATL,ATL,3)); atlas[:]=(240,232,220)
g=(np.arange(TILE)+0.5)/TILE*(1+2*PADS)-PADS
ST=np.stack(np.meshgrid(g,g),-1)            # [ty][tx] -> (s,t)
gl=(np.arange(16)+0.5)/16*(1+2*PADS)-PADS
STl=np.stack(np.meshgrid(gl,gl),-1)
for slot,(k,f) in enumerate(slots):
    d=unproj(ST,f).reshape(-1,3); p=surf(k,d); n=surf_normal(k,d)
    dl=unproj(STl,f).reshape(-1,3); a_lo=ao(k,surf(k,dl),surf_normal(k,dl)).reshape(16,16)
    a=np.asarray(Image.fromarray((a_lo*255).astype(np.uint8)).resize((TILE,TILE),Image.BILINEAR),float).reshape(-1)/255
    # detail: soft billowy cells + fine wisps, in world space so it flows across puffs
    det=0.65*fbm(p/26.0)+0.35*fbm(p/9.0+13.1)
    # bump-map the micro-puffs: perturb the normal by the height-field gradient
    e=1.5; h0=micro_h(p)
    gx=(micro_h(p+[e,0,0])-h0)/e; gy=(micro_h(p+[0,e,0])-h0)/e; gz=(micro_h(p+[0,0,e])-h0)/e
    gr=np.stack([gx,gy,gz],1); gr-= (gr*n).sum(1,keepdims=True)*n
    nb=n-4.0*gr; nb/=np.linalg.norm(nb,axis=1,keepdims=True)
    lam=np.clip((nb@L+0.3)/1.3,0,1)
    crease=0.8+0.2*h0                         # soft shadow in the gaps between micro-puffs
    light=0.1+0.9*lam*(0.25+0.75*a**1.6)*crease
    light=light*(0.92+0.14*det)
    light=np.clip(light,0,1)
    rim=np.clip(1-np.clip(nb@TOCAM,0,1),0,1)**2.2
    hgt=(p[:,1]-YB)/160.0
    gold=np.clip(1.0*rim*(0.35+0.65*lam)+0.6*np.clip(1-hgt/0.25,0,1)**1.5+0.08*det,0,1)
    col=ramp(WHITE,light)*(1-gold[:,None])+ramp(GOLD,light)*gold[:,None]
    tx,ty=slot%PER,slot//PER
    atlas[ty*TILE:(ty+1)*TILE,tx*TILE:(tx+1)*TILE]=col.reshape(TILE,TILE,3)
img=np.dstack([np.clip(atlas,0,255),np.full((ATL,ATL),255.0)]).astype(np.uint8)
Image.fromarray(img,'RGBA').save('out/heaven_wall_atlas.png')
Image.fromarray(img[...,:3],'RGB').save('out/heaven_wall.dds',pixel_format='DXT1')
