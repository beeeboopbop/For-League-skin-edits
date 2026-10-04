import sys, os; D=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,D); sys.path.insert(0,D+'/..')
import numpy as np
from PIL import Image, ImageFilter
from texlib import tex_to_image
z=np.load(D+'/bake_raw.npz'); cov=z['cov']; dist=z['dist']; col=z['col']
TB=np.asarray(tex_to_image(open(D+'/bunny_tex.tex','rb').read()).convert('RGBA'),float)
fallback=np.load(D+'/fallback.npy') if os.path.exists(D+'/fallback.npy') else TB
T0,T1=float(sys.argv[1]) if len(sys.argv)>1 else 4.0, float(sys.argv[2]) if len(sys.argv)>2 else 10.0
w=np.clip((T1-dist)/(T1-T0),0,1); w[~np.isfinite(dist)]=0
zone=np.load(D+'/zone.npy')[cov]
w=w*(1-np.clip((zone-0.25)/0.5,0,1))   # torso & feet: keep the (recoloured) bunny design
out=fallback.copy()
fb=fallback[cov]
out[cov,:3]=col[:,:3]*w[:,None]+fb[:,:3]*(1-w[:,None]); out[cov,3]=255
# pad Base islands outward a few texels so mip/bilinear sampling doesn't bleed seams
img=Image.fromarray(np.clip(out,0,255).astype(np.uint8),'RGBA')
mask=Image.fromarray((cov*255).astype(np.uint8))
pad=img.copy()
for _ in range(4):
    pad=Image.composite(pad,pad.filter(ImageFilter.MaxFilter(3)),mask)
    mask=mask.filter(ImageFilter.MaxFilter(3))
grown=np.array(mask)>0; o=np.asarray(img).copy(); p=np.asarray(pad)
ring=grown&~cov
# only paint the padding ring over texels no other submesh (Notepad) uses
note=np.load(D+'/notepad_mask.npy') if os.path.exists(D+'/notepad_mask.npy') else np.zeros_like(cov)
ring&=~note
o[ring]=p[ring]
Image.fromarray(o,'RGBA').save(D+'/baked_tex.png')
Image.fromarray((np.clip(w,0,1)*255).astype(np.uint8)).save(D+'/bake_weight_dbg.png') if False else None
print('transfer weight mean',w.mean().round(3),'full',(w>=1).mean().round(3))
