"""Transfer the Angelic outfit texture onto the bunnysuit mesh UVs (texture bake by surface proximity)."""
import sys, os; D=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,D); sys.path.insert(0,D+'/..')
import numpy as np
from PIL import Image
from scipy.spatial import cKDTree
from skllib import read_skl
from sknlib import read_skn, vfields
from mathlib import trs
from texlib import tex_to_image
def globals_(s):
    G={}
    for j in s['joints']:
        L=trs(j['lt'],j['lr'],j['ls']); G[j['id']]=L if j['parent']<0 else G[j['parent']]@L
    return G
A=read_skl(open(D+'/angelic.skl','rb').read()); M=read_skl(open(D+'/merged.skl','rb').read())
GA=globals_(A); GM=globals_(M); mid={j['name']:j['id'] for j in M['joints']}; aname={j['id']:j['name'] for j in A['joints']}
SA=read_skn(open(D+'/angelic.skn','rb').read()); SB=read_skn(open(D+'/bunny.skn','rb').read())
pa,ia,wa,na,ua=vfields(SA); pb,ib,wb,nb,ub=vfields(SB)
TA=np.asarray(tex_to_image(open(D+'/angelic_tex.tex','rb').read()).convert('RGBA'),float)
TB=np.asarray(tex_to_image(open(D+'/bunny_tex.tex','rb').read()).convert('RGBA'),float)
TS=TB.shape[0]

# --- Angelic body re-posed into the bunny bind pose ---
src_tris=[]
for s in SA['subs']:
    if s['name'] in ('wingsmat','weapon'): continue
    src_tris.append(SA['idx'][s['is_']:s['is_']+s['ic']].astype(int).reshape(-1,3))
src_tris=np.concatenate(src_tris)
X=np.zeros((len(pa),4,4))
for k in range(4):
    j=np.array([A['influences'][i] for i in ia[:,k]])
    T=np.stack([GM[mid[aname[jj]]]@np.linalg.inv(GA[jj]) for jj in range(len(A['joints']))])
    X+=wa[:,k,None,None]*T[j]
PA=np.einsum('nij,nj->ni',X,np.c_[pa,np.ones(len(pa))])[:,:3]
NA=np.einsum('nij,nj->ni',X[:,:3,:3],na); NA/=np.linalg.norm(NA,axis=1,keepdims=True)+1e-9

# dense surface samples (pos, normal, uv)
rng=np.random.default_rng(0)
a,b,c=PA[src_tris[:,0]],PA[src_tris[:,1]],PA[src_tris[:,2]]
area=0.5*np.linalg.norm(np.cross(b-a,c-a),axis=1)
cnt=np.maximum(1,np.round(area/0.06).astype(int))     # ~0.25 unit spacing
tri=np.repeat(np.arange(len(src_tris)),cnt)
r1=np.sqrt(rng.random(len(tri))); r2=rng.random(len(tri))
w0=1-r1; w1=r1*(1-r2); w2=r1*r2
t=src_tris[tri]
SP=w0[:,None]*PA[t[:,0]]+w1[:,None]*PA[t[:,1]]+w2[:,None]*PA[t[:,2]]
SN=w0[:,None]*NA[t[:,0]]+w1[:,None]*NA[t[:,1]]+w2[:,None]*NA[t[:,2]]; SN/=np.linalg.norm(SN,axis=1,keepdims=True)+1e-9
SU=w0[:,None]*ua[t[:,0]]+w1[:,None]*ua[t[:,1]]+w2[:,None]*ua[t[:,2]]
tree=cKDTree(SP); print('samples',len(SP))

# --- rasterise bunny Base in UV space ---
base=[s for s in SB['subs'] if s['name']=='Base'][0]
BT=SB['idx'][base['is_']:base['is_']+base['ic']].astype(int).reshape(-1,3)
texP=np.full((TS,TS,3),np.nan); texN=np.zeros((TS,TS,3))
for t3 in BT:
    uv=ub[t3]*TS-0.5; x=uv[:,0]; y=uv[:,1]
    x0,x1=int(np.floor(x.min())),int(np.ceil(x.max())); y0,y1=int(np.floor(y.min())),int(np.ceil(y.max()))
    x0,y0=max(x0,0),max(y0,0); x1,y1=min(x1,TS-1),min(y1,TS-1)
    if x1<x0 or y1<y0: continue
    gx,gy=np.meshgrid(np.arange(x0,x1+1),np.arange(y0,y1+1))
    d=(y[1]-y[2])*(x[0]-x[2])+(x[2]-x[1])*(y[0]-y[2])
    if abs(d)<1e-12: continue
    l0=((y[1]-y[2])*(gx-x[2])+(x[2]-x[1])*(gy-y[2]))/d; l1=((y[2]-y[0])*(gx-x[2])+(x[0]-x[2])*(gy-y[2]))/d; l2=1-l0-l1
    m=(l0>=-0.02)&(l1>=-0.02)&(l2>=-0.02)
    if not m.any(): continue
    P=l0[...,None]*pb[t3[0]]+l1[...,None]*pb[t3[1]]+l2[...,None]*pb[t3[2]]
    N=l0[...,None]*nb[t3[0]]+l1[...,None]*nb[t3[1]]+l2[...,None]*nb[t3[2]]
    texP[gy[m],gx[m]]=P[m]; texN[gy[m],gx[m]]=N[m]
cov=~np.isnan(texP[...,0]); print('base texels',cov.sum())
QP=texP[cov]; QN=texN[cov]; QN/=np.linalg.norm(QN,axis=1,keepdims=True)+1e-9
dist,idx=tree.query(QP,k=16)
dots=np.einsum('nkj,nj->nk',SN[idx],QN)
score=np.where(dots>0.25,dist,np.inf)        # ignore samples facing away (inner sides, back of collar...)
best=np.argmin(score,1); bd=score[np.arange(len(best)),best]; bi=idx[np.arange(len(best)),best]
uvq=SU[bi]
def bilinear(T,uv):
    h,w=T.shape[:2]; x=np.mod(uv[:,0],1)*w-0.5; y=np.mod(uv[:,1],1)*h-0.5
    x0=np.floor(x).astype(int); y0=np.floor(y).astype(int); fx=(x-x0)[:,None]; fy=(y-y0)[:,None]
    g=lambda yy,xx: T[np.mod(yy,h),np.mod(xx,w)]
    return (g(y0,x0)*(1-fx)+g(y0,x0+1)*fx)*(1-fy)+(g(y0+1,x0)*(1-fx)+g(y0+1,x0+1)*fx)*fy
col=bilinear(TA,uvq)
np.savez(D+'/bake_raw.npz',cov=cov,dist=bd,col=col,pos=QP)
print('dist pct',np.percentile(bd[np.isfinite(bd)],[50,75,90,95,99]),'inf',np.isinf(bd).sum())
