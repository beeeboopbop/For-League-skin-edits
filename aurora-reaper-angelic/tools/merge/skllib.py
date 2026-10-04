import struct
from pyritofile.ermmm import Elf
def read_skl(d):
    fs,sig,ver,flags,nj,ni=struct.unpack_from('<IIIHHI',d,0)
    jo,ji,io,no,ao,jn=struct.unpack_from('<6i',d,20); res=struct.unpack_from('<5i',d,44)
    J=[]
    for i in range(nj):
        o=jo+100*i
        fl,jid,par,pad,hsh,rad=struct.unpack_from('<HhhHIf',d,o)
        vals=struct.unpack_from('<20f',d,o+16)
        rel,=struct.unpack_from('<i',d,o+96); e=d.index(b'\0',o+96+rel); name=d[o+96+rel:e].decode()
        J.append(dict(flags=fl,id=jid,parent=par,pad=pad,hash=hsh,radius=rad,lt=vals[0:3],ls=vals[3:6],lr=vals[6:10],it=vals[10:13],is_=vals[13:16],ir=vals[16:20],name=name))
    infl=list(struct.unpack_from('<%dH'%ni,d,io))
    return dict(flags=flags,joints=J,influences=infl,reserved=res)
def write_skl(s):
    J=s['joints']; nj=len(J); ni=len(s['influences'])
    jo=64; ji=jo+100*nj; io=ji+8*nj; jn=io+2*ni
    names=bytearray(); noff=[]
    for j in J:
        noff.append(jn+len(names)); names+=j['name'].encode()+b'\0'
        while (jn+len(names))%4: names+=b'\0'
    total=jn+len(names)
    b=bytearray(struct.pack('<IIIHHI',total,0x22FD4FC3,0,s['flags'],nj,ni)+struct.pack('<6i',jo,ji,io,0,0,jn)+struct.pack('<5i',*s['reserved']))
    for i,j in enumerate(J):
        o=jo+100*i
        b+=struct.pack('<HhhHIf',j['flags'],j['id'],j['parent'],j['pad'],j['hash'],j['radius'])
        b+=struct.pack('<20f',*j['lt'],*j['ls'],*j['lr'],*j['it'],*j['is_'],*j['ir'])
        b+=struct.pack('<i',noff[i]-(o+96))
    for j in J: b+=struct.pack('<hhI',j['id'],0,j['hash'])
    b+=struct.pack('<%dH'%ni,*s['influences'])+names
    assert len(b)==total
    return bytes(b)
