import numpy as np
from PIL import Image
def render_multi(P,UV,groups,out,W=700,H=800,elev=-10,azim=0,bg=(60,70,90),ext=None):
    a=np.radians(azim); e=np.radians(elev)
    R1=np.array([[np.cos(a),0,np.sin(a)],[0,1,0],[-np.sin(a),0,np.cos(a)]]); R2=np.array([[1,0,0],[0,np.cos(e),-np.sin(e)],[0,np.sin(e),np.cos(e)]])
    E=ext if ext is not None else P
    ctr=(E.min(0)+E.max(0))/2
    Q=(P-ctr)@R1.T@R2.T; QE=(E-ctr)@R1.T@R2.T
    s=min(W/np.ptp(QE[:,0]),H/np.ptp(QE[:,1]))*0.92
    X=Q[:,0]*s+W/2; Y=-Q[:,1]*s+H/2; Z=-Q[:,2]   # camera looks down -z (front = +z in model)
    img=np.zeros((H,W,3)); img[:]=np.array(bg)/255; zb=np.full((H,W),np.inf)
    for I,tex in groups:
        T=np.asarray(tex.convert('RGBA'),float)/255; th,tw=T.shape[:2]
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
            zz=l0*z[0]+l1*z[1]+l2*z[2]; sub=zb[y0:y1+1,x0:x1+1]; m&=zz<sub
            if not m.any(): continue
            uv=l0[...,None]*UV[t[0]]+l1[...,None]*UV[t[1]]+l2[...,None]*UV[t[2]]
            u=(np.mod(uv[...,0],1)*(tw-1)).astype(int); v=(np.mod(uv[...,1],1)*(th-1)).astype(int)
            c=T[v,u]; m&=c[...,3]>0.3
            im=img[y0:y1+1,x0:x1+1]; im[m]=c[...,:3][m]; sub[m]=zz[m]
    Image.fromarray((img*255).astype(np.uint8)).save(out)
