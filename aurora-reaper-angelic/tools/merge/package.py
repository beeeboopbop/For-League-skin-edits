import sys, os, struct, json, zipfile, pickle
S=os.path.dirname(os.path.abspath(__file__))+'/..'; sys.path.insert(0,S); sys.path.insert(0,S+'/merge'); os.chdir(S)
import zstandard, xxhash
from wadlib import read_wad, h
from recolor import recolor
from remap_masks import remap_bin
an=pickle.load(open('names.pkl','rb')); ai={v:k for k,v in an.items()}
bn=pickle.load(open('bunny_names.pkl','rb')); bi={v:k for k,v in bn.items()}
src='src/WAD/Aurora.wad.client'; d=open(src,'rb').read()
n,=struct.unpack_from('<I',d,268); toc=[struct.unpack_from('<QIIIBBHQ',d,272+32*i) for i in range(n)]
_,ae=read_wad(src); ad={x['hash']:x['data'] for x in ae}
_,be=read_wad('bunny/WAD/Aurora.wad.client'); bd={x['hash']:x['data'] for x in be}
A='assets/f1117fc3/characters/aurora/skins/base/'; B='assets/characters/aurora/skins/base/'
repl={}
# 1) ult clouds + red fix (from v2.3.0)
repl[h('assets/f1117fc3/reaperaurora/yeswall.skn')]=open('out/heaven_wall.skn','rb').read()
repl[h('assets/f1117fc3/reaperaurora/yorickwghoul_skin50_tx_cm.skins_yorick_skin50.dds')]=open('out/heaven_wall.dds','rb').read()
vb=ai['data/aurora_vfx_skin0.bin']; repl[vb],lg=recolor(ad[vb]); assert len(lg)==92
# 2) bunnysuit body: merged skn/skl, bunny texture, bunny animations
repl[ai[A+'aurora_base.aurora.skn']]=open('merge/merged.skn','rb').read()
repl[ai[A+'aurora_base.aurora.skl']]=open('merge/merged.skl','rb').read()
repl[ai[A+'aurora_base_tx_cm.aurora.tex']]=open('merge/baked_tex.tex','rb').read()   # Angelic outfit baked onto bunny UVs
anims=0
for nm,k in ai.items():
    if nm.startswith(A+'animations/'):
        f=nm.split('/')[-1]
        if B+'animations/'+f in bi: repl[k]=bd[bi[B+'animations/'+f]]; anims+=1
# 3) animation-graph masks re-indexed for the merged skeleton, in every Aurora skin bin
masks=0;bins=0
for nm,k in ai.items():
    if nm.startswith('data/characters/aurora/skins/skin') and nm.endswith('.bin'):
        out,c=remap_bin(ad[k]); masks+=c; bins+=1
        if c: repl[k]=out
print('anims swapped',anims,'skin bins',bins,'masks remapped',masks)
body=bytearray(); newtoc=bytearray(); pos=272+32*n; z=zstandard.ZstdCompressor(level=12)
for (hh,o,cs,ds,t,dup,sub,ck) in toc:
    if hh in repl:
        raw=repl[hh]; comp=z.compress(raw); cs,ds,t,dup,sub,ck=len(comp),len(raw),3,0,0,xxhash.xxh3_64_intdigest(comp)
    else: comp=d[o:o+cs]
    newtoc+=struct.pack('<QIIIBBHQ',hh,pos,cs,ds,t,dup,sub,ck); body+=comp; pos+=len(comp)
open('out/Aurora.wad.client','wb').write(d[:272]+bytes(newtoc)+bytes(body))
_,e=read_wad('out/Aurora.wad.client'); dd={x['hash']:x['data'] for x in e}
print('entries',len(e),'changed',sum(dd[k]!=ad[k] for k in ad),'verified',all(dd[k]==repl[k] for k in repl))
info={"Author":"Frog / Abdomera (bunnysuit base)","Name":"reaper auror - Angelic Bunnysuit","Version":"3.1.0",
      "Description":"Angelic edit on the Aurora Bunnysuit body (model, physics, animations by Abdomera): white wings, white/gold wand & VFX, Angelic outfit (white hair/ears, ivory & gold) baked onto the bunnysuit, heavenly cloud ult ring, no red ult VFX"}
with zipfile.ZipFile('out/Reaper-Angelic-Bunnysuit-v3_1_0.fantome','w',zipfile.ZIP_DEFLATED) as zf:
    zf.write('out/Aurora.wad.client','WAD/Aurora.wad.client'); zf.writestr('META/info.json',json.dumps(info,indent=2))
