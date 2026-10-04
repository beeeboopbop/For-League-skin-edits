import struct, io
from PIL import Image
def tex_to_image(data):
    if data[:4]==b'DDS ': return Image.open(io.BytesIO(data)).convert('RGBA')
    w,h=struct.unpack_from('<HH',data,4); fmt=data[9]; mip=data[11]; body=data[12:]
    if fmt in (10,11,12):
        bs=8 if fmt in (10,11) else 16
        top=((w+3)//4)*((h+3)//4)*bs
        lvl=body[-top:] if mip else body[:top]   # mips stored smallest-first
        fourcc=b'DXT1' if bs==8 else b'DXT5'
        hdr=b'DDS '+struct.pack('<7I',124,0x81007,h,w,top,0,0)+b'\0'*44+struct.pack('<2I4s5I',32,4,fourcc,0,0,0,0,0)+struct.pack('<5I',0x1000,0,0,0,0)
        return Image.open(io.BytesIO(hdr+lvl)).convert('RGBA')
    if fmt==20:
        top=w*h*4; lvl=body[-top:] if mip else body[:top]
        im=Image.frombytes('RGBA',(w,h),lvl); b,g,r,a=im.split(); return Image.merge('RGBA',(r,g,b,a))
    raise ValueError(fmt)
