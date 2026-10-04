"""Heavenly cumulus ring for Aurora's R (replaces yeswall.skn).
UV encodes baked lighting: u = light (shadow -> sunlit), v = gold amount (rim + base glow)."""
import numpy as np, struct
from PIL import Image
rng=np.random.default_rng(11)

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

def billow(d,seed,n_lobes,amp):
    """cauliflower lobes: sum of smooth bumps at random directions (upper hemisphere biased)"""
    r=np.random.default_rng(seed)
    s=np.zeros(len(d))
    for _ in range(n_lobes):
        c=r.normal(size=3); c[1]=abs(c[1])*0.7+0.05; c/=np.linalg.norm(c)
        w=r.uniform(0.3,0.75)                      # angular size
        x=np.clip((d@c-np.cos(w))/(1-np.cos(w)),0,1)
        s=np.maximum(s, r.uniform(0.45,1.0)*np.sin(x*np.pi/2)**0.8)
    # fine bumps
    a=r.normal(size=(5,3)); a/=np.linalg.norm(a,axis=1,keepdims=True); ph=r.uniform(0,6.3,5)
    f=sum(np.sin(7*(d@a[i])+ph[i]) for i in range(5))/5
    return amp*s+0.03*f

R0=585.0; YB=-30.0
puffs=[]
def add(theta, rr, y, size, flat, sub, lobes):
    c=np.array([rr*np.cos(theta), y, rr*np.sin(theta)])
    rad=np.array([size*rng.uniform(1.0,1.2), size*flat, size*rng.uniform(1.0,1.2)])
    puffs.append(dict(c=c,r=rad,seed=int(rng.integers(1e9)),sub=sub,lobes=lobes,th=theta))
for i in range(30):   # wide base billows, bottoms sink below ground
    th=2*np.pi*(i+rng.uniform(-.3,.3))/30
    add(th, R0+rng.uniform(-40,40), YB+30, rng.uniform(95,115), 0.55, 3, 10)
for i in range(28):   # main body
    th=2*np.pi*(i+0.5+rng.uniform(-.3,.3))/28
    add(th, R0+rng.uniform(-25,25), YB+92+rng.uniform(-10,15), rng.uniform(72,90), 0.8, 3, 9)
for i in range(18):   # cumulus heads
    th=2*np.pi*(i+rng.uniform(-.35,.35))/18
    add(th, R0+rng.uniform(-20,20), YB+150+rng.uniform(-10,18), rng.uniform(58,72), 0.85, 3, 8)
for i in range(8):    # towering crowns
    th=2*np.pi*(i+rng.uniform(-.4,.4))/8
    add(th, R0+rng.uniform(-15,15), YB+200+rng.uniform(-8,12), rng.uniform(44,54), 0.9, 3, 6)
for i in range(36):   # small skirt wisps inside/outside
    th=2*np.pi*(i+rng.uniform(-.5,.5))/36; side=1 if i%2 else -1
    add(th, R0+side*rng.uniform(80,110), YB+12, rng.uniform(40,55), 0.5, 2, 3)

VIEW=np.array([0,-np.sin(np.radians(56)),np.cos(np.radians(56))])   # League camera forward
TOCAM=-VIEW
L=np.array([-0.55,0.8,0.45]); L/=np.linalg.norm(L)                  # sun: upper-left, behind the ring (silver/gold lining)

# build geometry
geo=[]
for k,p in enumerate(puffs):
    SV,SF=SPH[p['sub']]
    d=SV.copy()
    disp=1+billow(d,p['seed'],p['lobes'],0.30)
    q=d*disp[:,None]*p['r']
    q[:,1]=np.maximum(q[:,1],-p['r'][1]*0.4)
    q+=p['c']
    geo.append([q,SF])
# occluders for AO / culling: approximate each puff by an ellipsoid ~ its displaced size
OC=np.array([p['c'] for p in puffs]); OR=np.array([p['r']*1.05 for p in puffs])
def inside_any(pts,skip):
    m=np.zeros(len(pts),bool)
    for j in range(len(puffs)):
        if j==skip: continue
        m|=(((pts-OC[j])/(OR[j]*0.92))**2).sum(1)<1
    return m
# ray-traced AO against occluder spheres (radius = mean ellipsoid radius)
dirs=rng.normal(size=(24,3)); dirs/=np.linalg.norm(dirs,axis=1,keepdims=True)
SR=OR.mean(1)*0.9
def ao(pts,nrm,skip):
    occ=np.zeros(len(pts)); tot=np.zeros(len(pts))
    for dvec in dirs:
        cosv=nrm@dvec; w=np.clip(cosv,0,1); 
        hit=np.zeros(len(pts),bool)
        o=pts+nrm*4
        for j in range(len(puffs)):
            if j==skip: continue
            oc=o-OC[j]; b=oc@dvec; c=(oc**2).sum(1)-SR[j]**2
            disc=b*b-c
            t=-b-np.sqrt(np.maximum(disc,0))
            hit|=(disc>0)&(t>0)&(t<260)
        # ground plane also occludes downward rays
        hit|=(dvec[1]<0)&((o[:,1]-(-25))/max(-dvec[1],1e-3)<260)
        occ+=w*hit; tot+=w
    return 1-occ/np.maximum(tot,1e-6)

order=sorted(range(len(puffs)),key=lambda k:-(puffs[k]['c']@VIEW))   # painter's order
allP=[];allN=[];allUV=[];allF=[];base=0;culled=0
for k in order:
    q,SF=geo[k]
    n=np.zeros_like(q); fn=np.cross(q[SF[:,1]]-q[SF[:,0]],q[SF[:,2]]-q[SF[:,0]])
    for i in range(3): np.add.at(n,SF[:,i],fn)
    n/=np.linalg.norm(n,axis=1,keepdims=True)+1e-9
    # cull triangles buried in other puffs or under the ground
    ins=inside_any(q,k)|(q[:,1]<YB-12)
    keep=~(ins[SF].all(1)); culled+=(~keep).sum(); F=SF[keep]
    used=np.unique(F); remap=-np.ones(len(q),int); remap[used]=np.arange(len(used))
    q=q[used]; n=n[used]; F=remap[F]
    a=ao(q,n,k)
    lam=np.clip((n@L+0.3)/1.3,0,1)
    light=np.clip(0.1+0.9*lam*(0.25+0.75*a**1.6),0,1)
    rim=np.clip(1-np.clip(n@TOCAM,0,1),0,1)**2.2
    hgt=(q[:,1]-YB)/240.0
    gold=np.clip(1.0*rim*(0.35+0.65*lam) + 0.6*np.clip(1-hgt/0.25,0,1)**1.5, 0,1)
    F=F[np.argsort(-(q[F].mean(1)@VIEW))]
    allP.append(q);allN.append(n);allUV.append(np.stack([0.02+0.96*light,0.02+0.96*gold],1));allF.append(F+base);base+=len(q)
P=np.concatenate(allP);N=np.concatenate(allN);UV=np.concatenate(allUV);F=np.concatenate(allF)
print('verts',len(P),'tris',len(F),'culled',culled,'y',P[:,1].min().round(),P[:,1].max().round())
assert len(P)<65536

def write_skn(path,P,N,UV,F):
    b=bytearray(struct.pack('<IHH',0x00112233,1,1))
    b+=struct.pack('<I',1)+b'Body'.ljust(64,b'\0')+struct.pack('<IIII',0,len(P),0,F.size)
    b+=struct.pack('<II',F.size,len(P))+F.astype('<u2').tobytes()
    for p,n,uv in zip(P,N,UV): b+=struct.pack('<3f4B4f3f2f',*p,0,0,0,0,1.0,0.0,0.0,0.0,*n,*uv)
    open(path,'wb').write(bytes(b))
write_skn('out/heaven_wall.skn',P,N,UV,F)

# ramp texture
W=H=256
x=np.linspace(0,1,W)[None,:].repeat(H,0); g=np.linspace(0,1,H)[:,None].repeat(W,1)
keys=np.array([0.0,0.35,0.7,0.9,1.0])
cols=np.array([[170,146,120],[216,198,174],[242,236,228],[253,251,247],[255,255,255]],float)  # warm shadow -> ivory -> white
col=np.stack([np.interp(x,keys,cols[:,i]) for i in range(3)],-1)
goldc=np.stack([np.interp(x,keys,np.array([[160,124,78],[214,172,100],[246,206,128],[255,228,160],[255,242,200]],float)[:,i]) for i in range(3)],-1)
col=col*(1-g[...,None])+goldc*g[...,None]
col+=rng.normal(0,1.0,col.shape)
img=np.dstack([np.clip(col,0,255),np.full((H,W),255.0)]).astype(np.uint8)
Image.fromarray(img,'RGBA').save('out/heaven_wall_ramp.png')
im=Image.open('out/heaven_wall_ramp.png'); im.save('out/heaven_wall.dds',pixel_format='DXT5')
dd=bytearray(open('out/heaven_wall.dds','rb').read()); struct.pack_into('<I',dd,20,65536); open('out/heaven_wall.dds','wb').write(dd)
