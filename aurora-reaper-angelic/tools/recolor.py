import pyritofile as prf
from pyritofile.bin import BINType, name_to_hex
H=lambda s: name_to_hex(s)
VC=H('ValueColor'); AC=H('VfxAnimatedColorVariableData'); PAL=H('palleteSrcMixColor'); PALDEF=H('paletteDefinition')
SKIP=set()
for l in open('hashes.binfields.txt'):
    a,_,b=l.rstrip('\n').partition(' ')
    if 'mixer' in b.lower() or 'mixcolor' in b.lower() or b==('paletteDefinition'): SKIP.add(a)
from pyritofile.structs import Vector
def is_red(c):
    c=list(c)
    if len(c)!=4: return False
    r,g,b=c[0],c[1],c[2]
    return r>0.25 and r>g*1.6 and r>b*1.6
def gold(c):
    c=list(c); m=max(c[0],c[1],c[2])
    return Vector(m, 0.82*m, 0.45*m, c[3])
log=[]
def fix_vec4_list(lst,ctx):
    for i,c in enumerate(lst):
        if is_red(c):
            n=gold(c); log.append((ctx,list(c),list(n))); lst[i]=n
def walk(fields,ctx,in_color=False,skip=False):
    for f in fields or []:
        if f is None or not hasattr(f,'type'): continue
        name=f.hash
        s=skip or name in (PAL,PALDEF) or name in SKIP
        t=f.type
        if t==BINType.Vec4 and in_color and not s:
            if is_red(f.data):
                n=gold(f.data); log.append((ctx+'/'+str(name),list(f.data),list(n))); f.data=n
        elif t in (BINType.Pointer,BINType.Embed):
            col=f.hash_type in (VC,AC)
            walk(f.data,ctx+'/'+str(name),in_color or col,s)
        elif t in (BINType.List,BINType.List2):
            vt=f.value_type
            if vt==BINType.Vec4 and in_color and not s: fix_vec4_list(f.data,ctx+'/'+str(name))
            elif vt in (BINType.Pointer,BINType.Embed):
                for it in f.data:
                    if it is not None and hasattr(it,'data'): walk(it.data,ctx+'/'+str(name),in_color or it.hash_type in (VC,AC),s)
            elif vt==BINType.Embed or vt==BINType.Pointer: pass
def recolor(raw):
    b=prf.BIN(); b.read('',raw=raw); log.clear()
    for e in b.entries: walk(e.data,str(e.hash))
    return b.write('',raw=True), list(log)
