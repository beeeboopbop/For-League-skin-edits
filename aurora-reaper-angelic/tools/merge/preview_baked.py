import sys,os; D=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,D); sys.path.insert(0,D+'/..'); os.chdir(D+'/..')
from wadlib import *
from sknlib import read_skn, vfields
from texlib import tex_to_image
from render_multi import render_multi
from PIL import Image
import pickle
an=pickle.load(open('names.pkl','rb')); ai={v:k for k,v in an.items()}
_,ae=read_wad('src/WAD/Aurora.wad.client'); ad={x['hash']:x['data'] for x in ae}
A='assets/f1117fc3/characters/aurora/skins/base/'
tex={'base':Image.open('merge/baked_tex.png'),'weapon':tex_to_image(ad[ai[A+'aurora_base_weapon_tx_cm.aurora.tex']]),'wingsmat':tex_to_image(ad[ai[A+'wingstexture.dds']])}
m=read_skn(open('merge/merged.skn','rb').read()); P,_,_,_,UV=vfields(m)
wings=len(sys.argv)>2
g=[(m['idx'][s['is_']:s['is_']+s['ic']].astype(int).reshape(-1,3),tex.get(s['name'].lower(),tex['base'])) for s in m['subs'] if wings or s['name']!='wingsmat']
views=[(0,'front'),(180,'back'),(60,'side')]
for az,nm in views: render_multi(P.astype(float),UV,g,f'merge/baked_{nm}.png',azim=az,W=600,H=800)
c=Image.new('RGB',(2400,800),(60,70,90)); c.paste(Image.open('merge/angelic_front.png').resize((600,686)),(0,57))
for i,(_,nm) in enumerate(views): c.paste(Image.open(f'merge/baked_{nm}.png'),((i+1)*600,0))
c.save(sys.argv[1] if len(sys.argv)>1 else 'merge/baked_sheet.png')
