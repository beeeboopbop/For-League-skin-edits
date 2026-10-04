import json, os, pyritofile as prf
from pyritofile.bin import BINType, name_to_hex
D=os.path.dirname(os.path.abspath(__file__))
J=json.load(open(D+'/joints.json')); AN=J['angelic']; MN=J['merged']; PAR=J['parent']
aidx={n:i for i,n in enumerate(AN)}
WL=name_to_hex('mWeightList')
def remap(old):
    assert len(old)<=len(AN), len(old)
    old=list(old)+[0.0]*(len(AN)-len(old))   # lists may stop early; missing joints weigh 0
    out=[]
    for n in MN:
        m=n
        while m is not None and m not in aidx: m=PAR[m]   # bunny-only bones (breasts, book) inherit their parent's weight
        out.append(old[aidx[m]] if m is not None else 0.0)
    return out
def walk(fields,cnt):
    for f in fields or []:
        if f is None or not hasattr(f,'type'): continue
        if f.hash==WL and f.type in (BINType.List,BINType.List2): f.data=remap(list(f.data)); cnt[0]+=1
        elif f.type in (BINType.Pointer,BINType.Embed): walk(f.data,cnt)
        elif f.type in (BINType.List,BINType.List2) and f.value_type in (BINType.Pointer,BINType.Embed):
            for it in f.data:
                if it is not None and hasattr(it,'data'): walk(it.data,cnt)
        elif f.type==BINType.Map:
            vals=f.data.values() if isinstance(f.data,dict) else [v for _,v in f.data]
            for it in vals:
                if it is not None and hasattr(it,'data') and isinstance(it.data,list): walk(it.data,cnt)
def remap_bin(raw):
    b=prf.BIN(); b.read('',raw=raw); cnt=[0]
    for e in b.entries: walk(e.data,cnt)
    return b.write('',raw=True),cnt[0]
