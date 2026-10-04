import numpy as np, pyritofile as prf
from PIL import Image
def load(path):
    skn=prf.SKN(); skn.read(path)
    P=np.array([[*v.position] for v in skn.vertices],float); UV=np.array([[*v.uv] for v in skn.vertices],float)
    I=np.array(skn.indices).reshape(-1,3); return skn,P,UV,I
def render(P,UV,I,tex,out,W=900,H=600,elev=25,azim=30,bg=(70,90,120)):
    tex=np.asarray(tex.convert('RGBA'),float)/255; th,tw=tex.shape[:2]
    a=np.radians(azim); e=np.radians(elev)
    R1=np.array([[np.cos(a),0,np.sin(a)],[0,1,0],[-np.sin(a),0,np.cos(a)]])
    R2=np.array([[1,0,0],[0,np.cos(e),-np.sin(e)],[0,np.sin(e),np.cos(e)]])
    Q=(P-P.mean(0))@R1.T@R2.T
    s=min(W,H)/ (np.ptp(Q[:,:2],0).max())*0.95
    X=Q[:,0]*s+W/2; Y=-Q[:,1]*s+H/2; Z=Q[:,2]
    img=np.zeros((H,W,3)); img[:]=np.array(bg)/255; zb=np.full((H,W),np.inf)
    for t in I:
        x=X[t];y=Y[t];z=Z[t]
        x0,x1=int(max(0,np.floor(x.min()))),int(min(W-1,np.ceil(x.max())));y0,y1=int(max(0,np.floor(y.min()))),int(min(H-1,np.ceil(y.max())))
        if x1<x0 or y1<y0: continue
        gx,gy=np.meshgrid(np.arange(x0,x1+1)+.5,np.arange(y0,y1+1)+.5)
        d=(y[1]-y[2])*(x[0]-x[2])+(x[2]-x[1])*(y[0]-y[2])
        if abs(d)<1e-9: continue
        l0=((y[1]-y[2])*(gx-x[2])+(x[2]-x[1])*(gy-y[2]))/d; l1=((y[2]-y[0])*(gx-x[2])+(x[0]-x[2])*(gy-y[2]))/d; l2=1-l0-l1
        m=(l0>=0)&(l1>=0)&(l2>=0)
        if not m.any(): continue
        zz=l0*z[0]+l1*z[1]+l2*z[2]
        uv=l0[...,None]*UV[t[0]]+l1[...,None]*UV[t[1]]+l2[...,None]*UV[t[2]]
        sub=zb[y0:y1+1,x0:x1+1]; m&=zz<sub
        if not m.any(): continue
        u=(np.clip(uv[...,0],0,1)*(tw-1)).astype(int); v=(np.clip(uv[...,1],0,1)*(th-1)).astype(int)
        c=tex[v,u]
        im=img[y0:y1+1,x0:x1+1]
        al=c[...,3:4]
        im[m]=(c[...,:3]*al+im*(1-al))[m]; sub[m]=zz[m]
    Image.fromarray((img*255).astype(np.uint8)).save(out)
