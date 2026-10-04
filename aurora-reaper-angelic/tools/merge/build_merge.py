"""Merge: bunnysuit body (skn/skl/anims/physics) + Angelic wings & wand submeshes."""
import sys, os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))+'/..'); sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import numpy as np, copy
from skllib import read_skl, write_skl
from sknlib import read_skn, write_skn, vfields, pack_vertices
from mathlib import trs, decompose
from pyritofile.ermmm import Elf
D=os.path.dirname(os.path.abspath(__file__))
A=read_skl(open(D+'/angelic.skl','rb').read()); B=read_skl(open(D+'/bunny.skl','rb').read())
def globals_(s):
    G={}
    for j in s['joints']:
        L=trs(j['lt'],j['lr'],j['ls']); G[j['id']]=L if j['parent']<0 else G[j['parent']]@L
    return G
GA=globals_(A); GB=globals_(B)
aname={j['id']:j['name'] for j in A['joints']}; ajoint={j['name']:j for j in A['joints']}
M=copy.deepcopy(B); bid={j['name']:j['id'] for j in M['joints']}
GM={bid[n]:GB[bid[n]] for n in bid}
NEW=['joint1','joint2','joint3','joint4','joint5','joint6','joint7','joint8','weaponbuff','weaponbuff2']
for n in NEW:
    ja=ajoint[n]; pname=aname[ja['parent']]; pid=bid[pname]
    nid=len(M['joints'])
    L=trs(ja['lt'],ja['lr'],ja['ls']); G=GM[pid]@L; GM[nid]=G
    it,ir,is_=decompose(np.linalg.inv(G))
    M['joints'].append(dict(flags=ja['flags'],id=nid,parent=pid,pad=0,hash=Elf(n),radius=ja['radius'],lt=ja['lt'],ls=ja['ls'],lr=ja['lr'],
                            it=tuple(it),is_=tuple(is_),ir=tuple(ir),name=n))
    bid[n]=nid
# --- mesh ---
SA=read_skn(open(D+'/angelic.skn','rb').read()); SB=read_skn(open(D+'/bunny.skn','rb').read())
pa,ia,wa,na,ua=vfields(SA); pb,ib,wb,nb,ub=vfields(SB)
infl=list(M['influences'])
def infl_index(jid):
    if jid not in infl: infl.append(jid)
    return infl.index(jid)
P=[];I=[];W=[];N=[];U=[];IDX=[];subs=[];vbase=0;ibase=0
def add_sub(name,pos,inf,w,nrm,uv,idx):
    global vbase,ibase
    subs.append(dict(name=name,vs=vbase,vc=len(pos),is_=ibase,ic=len(idx)))
    P.append(pos);I.append(inf);W.append(w);N.append(nrm);U.append(uv);IDX.append(idx+vbase); vbase+=len(pos); ibase+=len(idx)
for s in SB['subs']:
    if s['name'].lower()=='weapon': continue          # bunny wand needs a base-game texture we don't have; use Angelic wand
    sl=slice(s['vs'],s['vs']+s['vc']); idx=SB['idx'][s['is_']:s['is_']+s['ic']].astype(int)-s['vs']
    add_sub(s['name'],pb[sl],ib[sl],wb[sl],nb[sl],ub[sl],idx)
for want in ['weapon','wingsmat']:
    s=[x for x in SA['subs'] if x['name']==want][0]
    sl=slice(s['vs'],s['vs']+s['vc']); idx=SA['idx'][s['is_']:s['is_']+s['ic']].astype(int)-s['vs']
    pos=pa[sl].astype(float); inf=ia[sl]; w=wa[sl].astype(float); nrm=na[sl].astype(float)
    newinf=np.zeros_like(inf); outp=np.zeros_like(pos); outn=np.zeros_like(nrm)
    for vi in range(len(pos)):
        acc=np.zeros((4,4))
        for k in range(4):
            if w[vi,k]<=0: continue
            ja=A['influences'][inf[vi,k]]; n=aname[ja]; jm=bid[n]
            newinf[vi,k]=infl_index(jm)
            # re-pose from Angelic bind to merged (bunny) bind
            acc+=w[vi,k]*(GM[jm]@np.linalg.inv(GA[ja]))
        outp[vi]=(acc@np.append(pos[vi],1))[:3]
        nn=acc[:3,:3]@nrm[vi]; outn[vi]=nn/(np.linalg.norm(nn)+1e-9)
    add_sub(want,outp,newinf,w,outn,ua[sl],idx)
M['influences']=infl
P=np.concatenate(P);I=np.concatenate(I);W=np.concatenate(W);N=np.concatenate(N);U=np.concatenate(U);IDX=np.concatenate(IDX)
assert len(P)<65536 and len(infl)<256
mn=P.min(0);mx=P.max(0);c=(mn+mx)/2;r=np.linalg.norm(P-c,axis=1).max()
out=dict(ver=(4,1),subs=subs,flags=SB['flags'],vsize=52,vtype=0,bbox=(*mn,*mx),bsphere=(*c,r),idx=IDX.astype(np.uint16),
         V=pack_vertices(P,I,W,N,U,None),tail=SB['tail'])
open(D+'/merged.skn','wb').write(write_skn(out)); open(D+'/merged.skl','wb').write(write_skl(M))
names_new=[j['name'] for j in M['joints']]
import json; json.dump(dict(angelic=[aname[i] for i in range(len(A['joints']))],merged=names_new,
                            parent={j['name']:(names_new[j['parent']] if j['parent']>=0 else None) for j in M['joints']}),open(D+'/joints.json','w'))
print('joints',len(M['joints']),'influences',len(infl),'verts',len(P),'tris',len(IDX)//3,[(s['name'],s['vc']) for s in subs])
