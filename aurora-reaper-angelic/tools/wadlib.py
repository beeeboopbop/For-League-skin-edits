import struct, zstandard, gzip, xxhash
def read_wad(path):
    d=open(path,'rb').read()
    assert d[:2]==b'RW'; major,minor=d[2],d[3]
    off=4+256+8 if major==3 else None
    n,=struct.unpack_from('<I',d,off); off+=4
    ents=[]
    for i in range(n):
        h,o,cs,ds,t,dup,sub,ck=struct.unpack_from('<QIIIBBHQ',d,off); off+=32
        raw=d[o:o+cs]; ty=t&15
        if ty==0: data=raw
        elif ty==1: data=gzip.decompress(raw)
        elif ty in (3,4): data=zstandard.ZstdDecompressor().decompress(raw,max_output_size=ds) if raw[:4]==b'\x28\xb5\x2f\xfd' else raw
        else: data=None
        ents.append(dict(hash=h,type=t,size=ds,data=data))
    return (major,minor),ents
def write_wad(path,files):  # files: dict hash->bytes
    hs=sorted(files); n=len(hs)
    hdr=bytearray(b'RW'+bytes([3,3])+b'\0'*256+struct.pack('<Q',0)+struct.pack('<I',n))
    toc_size=32*n; off=len(hdr)+toc_size; blobs=[]; toc=bytearray()
    c=zstandard.ZstdCompressor(level=6)
    for h in hs:
        raw=files[h]; comp=c.compress(raw)
        toc+=struct.pack('<QIIIBBHQ',h,off,len(comp),len(raw),3,0,0,xxhash.xxh3_64_intdigest(comp))
        blobs.append(comp); off+=len(comp)
    open(path,'wb').write(bytes(hdr)+bytes(toc)+b''.join(blobs))
def h(p): return xxhash.xxh64_intdigest(p.lower().encode())
