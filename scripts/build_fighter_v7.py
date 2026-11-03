"""Slice the generated fighter sheet and embed complete poses in the profile SVG.

No limb warping: each pose is a complete authored image. All cells use one
uniform scale, and are translated onto a common floor. Requires Pillow.
Run from any directory: python scripts/build_fighter_v7.py
"""
from pathlib import Path
from PIL import Image, ImageDraw
import base64
import io
import re
import json
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / 'assets' / 'fighter-v7'
T = 10000
TIMELINE = [
    (0,0),(200,1),(400,0),(600,1),(800,0),(1000,2),
    (1160,3),(1270,4),(1370,5),(1440,0),
    (1580,3),(1710,4),(1800,5),(1870,0),(2100,1),
    (2280,10),(2460,11),(2550,12),(2700,13),(2880,0),
    (2970,6),(3050,7),(3220,8),(3320,9),(3410,17),(3490,0),
    (3610,14),(3690,15),(3840,16),(3970,17),(4150,0),
    (4310,1),(4490,0),(4670,18),(5100,18),(5350,19),
    (5540,20),(5680,21),(5820,17),(6000,0),(6450,22),
    (6700,23),(9050,22),(9300,0),(9550,1),(9775,0),(10000,0),
]

def png_uri(im):
    b=io.BytesIO(); im.save(b,format='PNG',optimize=True)
    return 'data:image/png;base64,'+base64.b64encode(b.getvalue()).decode()

def replace_rule(doc,name,body):
    pattern=r'@keyframes '+re.escape(name)+r'\{.*?\}\.'+re.escape(name)+r'\{[^}]*\}'
    doc,n=re.subn(pattern,body,doc,flags=re.S)
    assert n==1,(name,n)
    return doc

def main():
    sheet=Image.open(ART/'fighter-sheet.png').convert('RGBA')
    cw,ch=sheet.width//6,sheet.height//4
    assert sheet.width%6==sheet.height%4==0,sheet.size
    assert sheet.getchannel('A').getextrema()[0]==0,'Sheet must have real transparency'
    # Only extraction, common scaling and alignment; the generated artwork is
    # never recolored, re-drawn or stretched to make an animation frame.
    cells=[sheet.crop((c*cw,r*ch,(c+1)*cw,(r+1)*ch)) for r in range(4) for c in range(6)]
    # The generator includes very low alpha in empty pixels. Ignore that
    # invisible residue for bounds while preserving the authored alpha itself.
    bounds=[c.getchannel('A').point(lambda a:255 if a>128 else 0).getbbox() for c in cells]
    assert all(bounds),'All 24 pose cells must be populated'
    scale=234/(bounds[0][3]-bounds[0][1])
    frames=[]; metadata=[]
    for i,(cell,bb) in enumerate(zip(cells,bounds)):
        # Keep each frame's anatomy and its authored width-to-height ratio.
        # Align to the ankles and the torso centre, not to the bounding-box edge
        # (a punch changes the bounding box without moving the torso).
        y0=bb[1]+round((bb[3]-bb[1])*.28)
        y1=bb[1]+round((bb[3]-bb[1])*.50)
        alpha=cell.getchannel('A')
        xs=[]
        for y in range(y0,y1):
            row=alpha.crop((0,y,cw,y+1)).getbbox()
            if row: xs.append((row[0]+row[2])/2)
        # Art sheet already carries coherent centres; use cell centre as the
        # primary reference so natural torso rotation remains visible.
        scaled=cell.resize((round(cw*scale),round(ch*scale)),Image.Resampling.NEAREST)
        out=Image.new('RGBA',(320,280))
        ox=round(145-cw*.5*scale)
        oy=round(260-bb[3]*scale)
        out.alpha_composite(scaled,(ox,oy))
        # Export optimization for an embedded web sprite: discard effectively
        # invisible alpha residue and index the colors without dithering.
        # This is uniform for all poses; anatomy and artwork stay untouched.
        out.putalpha(out.getchannel('A').point(lambda a:0 if a<32 else 255 if a>230 else a))
        out=out.quantize(colors=128,method=Image.Quantize.FASTOCTREE,dither=Image.Dither.NONE).convert('RGBA')
        out.save(ART/f'pose-{i:02d}.png',optimize=True)
        frames.append(out)
        metadata.append(dict(frame=i,bounds=bb,offset=[ox,oy]))
    (ART/'manifest.json').write_text(json.dumps(dict(sheet=list(sheet.size),scale=scale,frames=metadata,timeline=TIMELINE),indent=2))

    doc=(ROOT/'assets'/'fight-hero-v6.svg').read_text()
    # Remove all old procedural human art and its animation rules.
    doc=re.sub(r'<image class="p_[^"]+"[^>]*/>','',doc)
    doc=re.sub(r'@keyframes p_[a-zA-Z0-9_]+\{.*?\}\.p_[a-zA-Z0-9_]+\{[^}]*\}','',doc,flags=re.S)
    css=[]
    for i in range(24):
        points={0:0,100:0}
        for j,(start,p) in enumerate(TIMELINE[:-1]):
            if p==i:
                points[start/100]=1
                points[TIMELINE[j+1][0]/100]=0
        if TIMELINE[0][1]==i: points[0]=1
        if TIMELINE[-2][1]==i: points[100]=1
        key=''.join(f'{t:g}%{{opacity:{v}}}' for t,v in sorted(points.items()))
        css.append(f'@keyframes v7p{i}{{{key}}}.v7p{i}{{opacity:0;animation:v7p{i} {T}ms step-end infinite}}')
    # Locomotion moves the entire body. It does not scale limbs or change the
    # proportions of the character. Keep contact distance readable.
    feet=[(0,0),(1000,0),(1270,4),(1440,0),(1710,4),(1900,0),
          (2280,0),(2550,-12),(2800,-12),(2970,0),(3220,7),(3500,0),
          (3610,10),(3690,17),(3840,25),(4200,0),(4670,-2),
          (5300,0),(5400,20),(5540,45),(5680,40),(5900,8),
          (6450,0),(10000,0)]
    rule='@keyframes feet{'+''.join(f'{ms/100:g}%{{transform:translateX({x}px)}}' for ms,x in feet)+'}.feet{animation:feet 10000ms linear infinite}'
    doc=replace_rule(doc,'feet',rule)
    doc=doc.replace('</style>',''.join(css)+'</style>')
    images=''.join(f'<image class="v7p{i}" href="{png_uri(im)}" x="541" y="145" width="320" height="280" preserveAspectRatio="xMidYMid meet" style="image-rendering:pixelated"/>' for i,im in enumerate(frames))
    # The original human group is now empty, immediately before charge effects.
    doc,n=re.subn(r'<g class="feet"></g>',lambda m:'<g class="feet">'+images+'</g>',doc,count=1)
    assert n==1,'Human group not found'
    # A more modest KO label leaves the winning character's face visible.
    doc=doc.replace('<g class="tKO">','<g class="tKO" transform="translate(40 -25) translate(796 200) scale(.72) translate(-796 -200)">')
    # Keep 100% of the rest of the README and its site link unchanged.
    # Retarget impact particles to the NEW drawn fists. The old rig had very
    # different hand coordinates; reusing its effects would look like misses.
    ns='http://www.w3.org/2000/svg'
    ET.register_namespace('',ns)
    root=ET.fromstring(doc)
    hits=[(793,214),(793,214),(805,210),(780,230),(779,196)]
    charge=(671,291)
    for el in root.iter():
        cls=el.get('class','')
        m=re.fullmatch(r'sp([0-4])[sb]',cls)
        if m:
            hx,hy=hits[int(m[1])]
            el.set('x',str(hx-float(el.get('width'))/2))
            el.set('y',str(hy-float(el.get('height'))/2))
        m=re.fullmatch(r'tk([0-4])_\d+',cls)
        if m:
            hx,hy=hits[int(m[1])]; el.set('x',str(hx)); el.set('y',str(hy))
        if cls=='wave': el.set('cx',str(hits[-1][0])); el.set('cy',str(hits[-1][1]))
        if cls=='glow': el.set('cx',str(charge[0])); el.set('cy',str(charge[1]))
        if re.fullmatch(r'cv\d+',cls): el.set('x',str(charge[0])); el.set('y',str(charge[1]+4))
    style=root.find('{'+ns+'}style')
    for cls,point in [('wave',hits[-1]),('glow',charge)]:
        style.text=re.sub(r'(\.'+cls+r'\{[^}]*transform-origin:)[^;}]+',lambda m:m[1]+f'{point[0]}px {point[1]}px',style.text)
    style.text=style.text.replace('opacity:.55','opacity:.22')
    doc=ET.tostring(root,encoding='unicode')
    (ROOT/'assets'/'fight-hero-v7.svg').write_text(doc)

    # Review sheet and standalone loop make the character easy to inspect
    # without the tiny GitHub card or an overlapping HUD.
    contact=Image.new('RGB',(4*340,3*310),'#131b2b')
    draw=ImageDraw.Draw(contact)
    selected=[0,4,8,10,12,13,14,15,16,18,20,23]
    for j,i in enumerate(selected):
        contact.paste(frames[i],((j%4)*340+10,(j//4)*310+10),frames[i])
        draw.text(((j%4)*340+16,(j//4)*310+289),f'POSE {i:02d}',fill='#a4c4d8')
    contact.save(ART/'character-review.png')
    gif=[]; durations=[]
    for j,(ms,i) in enumerate(TIMELINE[:-1]):
        canvas=Image.new('RGB',(400,320),'#131b2b')
        d=ImageDraw.Draw(canvas)
        d.line((16,286,384,286),fill='#344859',width=1)
        d.text((20,16),'JIANHANG / SHADOWBOXING',fill='#a4c4d8')
        canvas.paste(frames[i],(40,26),frames[i])
        gif.append(canvas)
        durations.append(TIMELINE[j+1][0]-ms)
    gif[0].save(ART/'fighter-preview.gif',save_all=True,append_images=gif[1:],duration=durations,loop=0,optimize=True)
    print('Built',ROOT/'assets'/'fight-hero-v7.svg',len(doc),'bytes')

if __name__=='__main__': main()
