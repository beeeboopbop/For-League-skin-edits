"""Battle Bunny (Rose Quartz) VFX on the Aurora Bunnysuit body.

usage: python build.py <bunnysuit.fantome> <battle-bunny-rose-quartz-vfx.fantome> <out.fantome>

Skin 9 (Rose Quartz chroma) keeps all of its recoloured VFX, but its body is switched to the
bunnysuit: mesh, skeleton, texture and (via the base animation graph) the bunnysuit animations.
"""
import sys, os, io, json, zipfile
T=os.path.join(os.path.dirname(os.path.abspath(__file__)),'../../aurora-reaper-angelic/tools'); sys.path.insert(0,T)
import pyritofile as prf
from pyritofile.bin import name_to_hex
from wadlib import read_wad, write_wad, h

def wad_from_fantome(p):
    z=zipfile.ZipFile(p); tmp=io.BytesIO(z.read('WAD/Aurora.wad.client'))
    path=p+'.wad.tmp'; open(path,'wb').write(tmp.getvalue())
    try: _,e=read_wad(path)
    finally: os.remove(path)
    return {x['hash']:x['data'] for x in e}, json.loads(z.read('META/info.json'))

B='ASSETS/Characters/Aurora/Skins/Base/'
SKN=B+'Aurora_Base.Aurora.skn'; SKL=B+'Aurora_Base.Aurora.skl'; TEX=B+'Aurora_Base_TX_CM.Aurora.tex'
SKIN9='data/characters/aurora/skins/skin9.bin'
GRAPH0='Characters/Aurora/Animations/Skin0'

def fnv(s):
    x=0x811c9dc5
    for c in s.lower().encode(): x=((x^c)*0x01000193)&0xffffffff
    return x

def edit_skin9(raw):
    b=prf.BIN(); b.read('',raw=raw)
    sk=[e for e in b.entries if e.type==name_to_hex('SkinCharacterDataProperties')]; assert len(sk)==1
    done=set()
    for f in sk[0].data:
        if f.hash==name_to_hex('skinAnimationProperties'):
            for g in f.data:
                if g.hash==name_to_hex('animationGraphData'): g.data='%08x'%fnv(GRAPH0); done.add('graph')
        if f.hash==name_to_hex('skinMeshProperties'):
            keep=[]
            for g in f.data:
                if g.hash==name_to_hex('skeleton'): g.data=SKL; done.add('skl')
                elif g.hash==name_to_hex('simpleSkin'): g.data=SKN; done.add('skn')
                elif g.hash==name_to_hex('texture'): g.data=h(TEX); done.add('tex')
                elif g.hash==name_to_hex('initialSubmeshToHide'): g.data='weapon'; done.add('hide')
                # the Iridescent body material and per-submesh overrides are laid out for the
                # Battle Bunny UVs/submeshes; drop them so the bunnysuit texture is used as-is
                elif g.hash in (name_to_hex('material'),name_to_hex('materialOverride')): done.add('mat'); continue
                keep.append(g)
            f.data=keep
    assert done=={'graph','skl','skn','tex','hide','mat'}, done
    b.links=[l.replace('Animations/Skin1.bin','Animations/Skin0.bin') for l in b.links]
    return b.write('',raw=True)

if __name__=='__main__':
    suit,_=wad_from_fantome(sys.argv[1]); bb,bbinfo=wad_from_fantome(sys.argv[2])
    for p in (SKN,SKL,TEX): assert h(p) in suit, p
    files=dict(suit); files.update(bb)          # no overlap: bunnysuit = base assets, VFX mod = skin 9
    assert len(files)==len(suit)+len(bb)
    files[h(SKIN9)]=edit_skin9(bb[h(SKIN9)])
    out=sys.argv[3]; wad=out+'.wad.tmp'; write_wad(wad,files)
    info={"Name":"Battle Bunny Bunnysuit Aurora (Rose Quartz)","Author":"Abdomera (bunnysuit) / Sunshine Builder (VFX)","Version":"1.0.0",
          "Description":"Select the Battle Bunny Rose Quartz chroma (skin 9): Aurora Bunnysuit body, skeleton and animations with the Rose Quartz Battle Bunny VFX. Base Aurora is the plain bunnysuit."}
    with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as zf:
        zf.write(wad,'WAD/Aurora.wad.client'); zf.writestr('META/info.json',json.dumps(info,indent=2))
    os.remove(wad); print('entries',len(files),'->',out)
