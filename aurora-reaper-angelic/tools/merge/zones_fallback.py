"""Zone map (torso/feet keep the bunny design) + Angelic-palette recolour of the bunny texture."""
import sys, os; D=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,D); sys.path.insert(0,D+'/..')
import numpy as np, colorsys
from PIL import Image
from skllib import read_skl
from sknlib import read_skn, vfields
from texlib import tex_to_image
S=read_skl(open(D+'/bunny.skl','rb').read()); names=[j['name'] for j in S['joints']]
ZONE={'R_Clavicle','L_Clavicle','R_Shoulder','L_Shoulder','Spine','Spine2','Chest','Pelvis','R_Breast1','R_Breast2','L_Breast1','L_Breast2','Bag','FrontCloth1','FrontCloth2',
      'Coattail1','Coattail2','L_Foot','L_Toe','R_Foot','R_Toe','L_Foot_SNAP','R_Foot_SNAP'}
SB=read_skn(open(D+'/bunny.skn','rb').read()); pb,ib,wb,nb,ub=vfields(SB)
zv=np.zeros(len(pb))
for k in range(4):
    j=np.array([names[S['influences'][i]] for i in ib[:,k]]); zv+=wb[:,k]*np.isin(j,list(ZONE))
TS=1024; zt=np.zeros((TS,TS)); cov=np.zeros((TS,TS),bool)
base=[s for s in SB['subs'] if s['name']=='Base'][0]
for t3 in SB['idx'][base['is_']:base['is_']+base['ic']].astype(int).reshape(-1,3):
    uv=ub[t3]*TS-0.5; x=uv[:,0]; y=uv[:,1]
    x0,x1=max(int(np.floor(x.min())),0),min(int(np.ceil(x.max())),TS-1); y0,y1=max(int(np.floor(y.min())),0),min(int(np.ceil(y.max())),TS-1)
    if x1<x0 or y1<y0: continue
    gx,gy=np.meshgrid(np.arange(x0,x1+1),np.arange(y0,y1+1))
    d=(y[1]-y[2])*(x[0]-x[2])+(x[2]-x[1])*(y[0]-y[2])
    if abs(d)<1e-12: continue
    l0=((y[1]-y[2])*(gx-x[2])+(x[2]-x[1])*(gy-y[2]))/d; l1=((y[2]-y[0])*(gx-x[2])+(x[0]-x[2])*(gy-y[2]))/d; l2=1-l0-l1
    m=(l0>=-0.02)&(l1>=-0.02)&(l2>=-0.02)
    zt[gy[m],gx[m]]=(l0*zv[t3[0]]+l1*zv[t3[1]]+l2*zv[t3[2]])[m]; cov[gy[m],gx[m]]=True
np.save(D+'/zone.npy',zt)
# recolour bunny texture into the Angelic palette
TB=np.asarray(tex_to_image(open(D+'/bunny_tex.tex','rb').read()).convert('RGBA'),float)
rgb=TB[...,:3]/255
mx=rgb.max(-1); mn=rgb.min(-1); v=mx; s=np.where(mx>0,(mx-mn)/np.maximum(mx,1e-6),0)
r,g,b=rgb[...,0],rgb[...,1],rgb[...,2]
hue=np.zeros_like(v); dl=np.maximum(mx-mn,1e-6)
hue=np.where(mx==r,((g-b)/dl)%6,np.where(mx==g,(b-r)/dl+2,(r-g)/dl+4))*60
lum=0.3*r+0.59*g+0.11*b
out=rgb.copy()
redbrown=((hue<32)|(hue>330))&(s>0.42)&(v<0.72)                 # cuffs, belt, shoes, straps
teal=(hue>150)&(hue<220)&(s>0.2)
grey=s<0.16
gold_lo=np.array([0.55,0.40,0.18]); gold_hi=np.array([0.98,0.84,0.52])
t=np.clip((lum-0.1)/0.5,0,1)[...,None]
out[redbrown]=(gold_lo+(gold_hi-gold_lo)*t)[redbrown]
iv=np.array([1.0,0.975,0.935])
out[grey]=np.clip((0.25+0.8*lum[...,None])*iv,0,1)[grey]
out[teal]=np.clip((0.4+0.6*lum[...,None])*iv,0,1)[teal]
F=TB.copy(); F[...,:3]=out*255
np.save(D+'/fallback.npy',F)
Image.fromarray(F.astype(np.uint8)).save(D+'/fallback.png')
print('zone texels',(zt>0.5).sum(),'redbrown',redbrown.sum())
