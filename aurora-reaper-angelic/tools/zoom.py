import numpy as np, pyritofile as prf, sys
from render import render
from PIL import Image
s=prf.SKN(); s.read('out/heaven_wall.skn')
P=np.array([[*v.position] for v in s.vertices]);UV=np.array([[*v.uv] for v in s.vertices]);I=np.array(s.indices).reshape(-1,3)
t=Image.open('out/heaven_wall.dds')
m=(np.abs(P[:,0])<170)&(P[:,2]<-380); keep=m[I].all(1)
Ik=I[keep]; u,inv=np.unique(Ik,return_inverse=True)
render(P[u],UV[u],inv.reshape(-1,3),t,sys.argv[1],elev=-50,azim=0,bg=(48,62,44),W=1100,H=650)
