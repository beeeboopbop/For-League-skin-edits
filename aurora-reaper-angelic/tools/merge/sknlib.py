import struct, numpy as np
def read_skn(d):
    sig,maj,mnr=struct.unpack_from('<IHH',d,0); assert sig==0x00112233 and maj in (1,2,4), (maj,mnr)
    o=8; ns,=struct.unpack_from('<I',d,o); o+=4; subs=[]
    for i in range(ns):
        name=d[o:o+64].split(b'\0')[0].decode(); vs,vc,is_,ic=struct.unpack_from('<4I',d,o+64); o+=80
        subs.append(dict(name=name,vs=vs,vc=vc,is_=is_,ic=ic))
    if maj==4:
        flags,ic,vc,vsize,vtype=struct.unpack_from('<5I',d,o); o+=20
        bbox=struct.unpack_from('<6f',d,o); o+=24; bs=struct.unpack_from('<4f',d,o); o+=16
    else:
        ic,vc=struct.unpack_from('<2I',d,o); o+=8; flags=0; vsize=52; vtype=0; bbox=None; bs=None
    idx=np.frombuffer(d,'<u2',ic,o).copy(); o+=2*ic
    V=np.frombuffer(d,np.uint8,vc*vsize,o).reshape(vc,vsize).copy(); o+=vc*vsize
    tail=d[o:]
    return dict(ver=(maj,mnr),subs=subs,flags=flags,vsize=vsize,vtype=vtype,bbox=bbox,bsphere=bs,idx=idx,V=V,tail=tail)
def vfields(m):
    V=m['V']
    pos=V[:,0:12].copy().view('<f4').reshape(-1,3); inf=V[:,12:16].copy(); w=V[:,16:32].copy().view('<f4').reshape(-1,4)
    nrm=V[:,32:44].copy().view('<f4').reshape(-1,3); uv=V[:,44:52].copy().view('<f4').reshape(-1,2)
    return pos,inf,w,nrm,uv
def pack_vertices(pos,inf,w,nrm,uv,extra):
    n=len(pos)
    parts=[pos.astype('<f4').view(np.uint8).reshape(n,12),inf.astype(np.uint8).reshape(n,4),w.astype('<f4').view(np.uint8).reshape(n,16),
           nrm.astype('<f4').view(np.uint8).reshape(n,12),uv.astype('<f4').view(np.uint8).reshape(n,8)]
    if extra is not None and extra.shape[1]: parts.append(extra.astype(np.uint8))
    return np.concatenate(parts,1)
def write_skn(m):
    b=bytearray(struct.pack('<IHH',0x00112233,*m['ver']))+struct.pack('<I',len(m['subs']))
    for s in m['subs']: b+=s['name'].encode().ljust(64,b'\0')+struct.pack('<4I',s['vs'],s['vc'],s['is_'],s['ic'])
    b+=struct.pack('<5I',m['flags'],len(m['idx']),len(m['V']),m['vsize'],m['vtype'])
    b+=struct.pack('<6f',*m['bbox'])+struct.pack('<4f',*m['bsphere'])
    b+=m['idx'].astype('<u2').tobytes()+m['V'].tobytes()+m['tail']
    return bytes(b)
