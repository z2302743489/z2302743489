"""Put the existing bout in a neon octagonal cage. Standard library only.

The v14 choreography, actor geometry, embedded sprites and original CSS remain
intact. Only the fifteen original scenery nodes are replaced, and ambient
light animations have their own groups and classes.
"""
from pathlib import Path
from copy import deepcopy
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
NS='http://www.w3.org/2000/svg'
ET.register_namespace('',NS)

def el(parent,tag,attrs,text=None):
    node=ET.SubElement(parent,'{'+NS+'}'+tag,{k:str(v) for k,v in attrs.items()})
    node.text=text
    return node

def points(p):return ' '.join(f'{x},{y}' for x,y in p)

def gradient(defs,name,stops,radial=False,**attrs):
    node=el(defs,'radialGradient' if radial else 'linearGradient',dict(id=name,**attrs))
    for offset,color,opacity in stops:
        el(node,'stop',{'offset':offset,'stop-color':color,'stop-opacity':opacity})

def led(parent,path,color,width=2):
    for w,op in ((width+7,.045),(width+3,.12),(width,1)):
        el(parent,'path',{'d':path,'stroke':color,'stroke-width':w,'opacity':op,'fill':'none','stroke-linejoin':'miter'})

def post(parent,x,top,bottom,color,near=False):
    w=11 if near else 8
    el(parent,'path',{'d':f'M{x-w/2} {top}h{w}v{bottom-top}h-{w}z','fill':'#030913','stroke':'#263b53','stroke-width':1})
    el(parent,'rect',{'x':x-w/2+1,'y':top+2,'width':2,'height':bottom-top-5,'fill':color,'opacity':.5})
    if near:
        y=top+(bottom-top)*.44
        el(parent,'path',{'d':f'M{x-9} {y}h16v64h-16z','fill':'#0c1424','stroke':'#30495f','stroke-width':1})
        el(parent,'rect',{'x':x-8,'y':y+3,'width':3,'height':57,'fill':color})
        for yy in (y+10,y+27,y+44):
            el(parent,'path',{'d':f'M{x-2} {yy}h7m-7 3h7','stroke':color,'stroke-width':1,'opacity':.45})
    el(parent,'rect',{'x':x-7,'y':top-3,'width':14,'height':5,'fill':'#14273a'})
    el(parent,'rect',{'x':x-5,'y':top-2,'width':10,'height':2,'fill':color})

def build():
    source=ET.parse(ROOT/'assets'/'fight-hero-v14.svg').getroot()
    root=deepcopy(source);defs=root.find('{'+NS+'}defs')
    scene=next(n for n in root if n.get('id')=='fight-v9')
    camera=next(n for n in scene if n.get('class')=='v9camera')
    original_actors=[ET.tostring(n) for n in list(camera)[15:]]
    original_css=root.find('{'+NS+'}style').text
    for node in list(camera)[:15]:
        assert not node.get('class'), 'Scenery boundary changed; inspect before rebuilding.'
        camera.remove(node)
    backdrop=ET.Element('{'+NS+'}g',{'id':'octagon-arena-v15'})
    camera.insert(0,backdrop)
    next(n for n in scene if n.tag.endswith('rect') and n.get('x')=='548').set('fill','#050a14')
    gradient(defs,'v15-night',[(0,'#050912',1),(.55,'#09162a',1),(1,'#07101f',1)],x1=0,y1=0,x2=0,y2=1)
    gradient(defs,'v15-haze',[(0,'#145d76',.35),(.6,'#163762',.12),(1,'#051020',0)],True,cx='.47',cy='.42',r='.7')
    gradient(defs,'v15-mat',[(0,'#172b43',1),(.55,'#132237',1),(1,'#0d1729',1)],x1=0,y1=0,x2=0,y2=1)
    gradient(defs,'v15-panel',[(0,'#0e1d31',.75),(.5,'#0c1b30',.85),(1,'#11273c',1)],x1=0,y1=0,x2=0,y2=1)
    gradient(defs,'v15-beam-cyan',[(0,'#98faff',.22),(1,'#35e5ef',0)],x1=0,y1=0,x2=0,y2=1)
    gradient(defs,'v15-beam-violet',[(0,'#cbb5ff',.20),(1,'#9a77ff',0)],x1=0,y1=0,x2=0,y2=1)
    mesh=el(defs,'pattern',{'id':'v15-mesh','width':14,'height':18,'patternUnits':'userSpaceOnUse'})
    el(mesh,'path',{'d':'M-7 9L0 0L14 18L21 9M0 18L14 0','stroke':'#45677e','stroke-width':.8,'fill':'none','opacity':.38})
    el(mesh,'path',{'d':'M0 0l1 1m12 16l1 1','stroke':'#91c5d6','stroke-width':1,'opacity':.22})
    grain=el(defs,'pattern',{'id':'v15-matgrain','width':12,'height':8,'patternUnits':'userSpaceOnUse'})
    el(grain,'path',{'d':'M1 1h1m7 4h1','stroke':'#8cb3c4','stroke-width':.65,'opacity':.065})
    octagon=[(622,305),(910,305),(977,349),(977,398),(910,425),(622,425),(555,398),(555,349)]
    cp=el(defs,'clipPath',{'id':'v15-matclip'});el(cp,'polygon',{'points':points(octagon)})
    el(backdrop,'rect',{'x':538,'y':48,'width':456,'height':390,'fill':'url(#v15-night)'})
    el(backdrop,'rect',{'x':538,'y':70,'width':456,'height':345,'fill':'url(#v15-haze)'})
    # Distant audience pixels and small LED ribbons sit beyond the wire mesh.
    crowd=el(backdrop,'g',{'opacity':.46})
    for row in range(5):
        for col in range(39):
            x=551+col*11+(row%2)*4;y=182+row*17+(col*7%5)
            color=('#1b3450','#1e3f57','#243456','#32647b','#3d355f')[(row*13+col*7)%5]
            el(crowd,'rect',{'x':x,'y':y,'width':3 if col%3 else 4,'height':2+(col%3),'fill':color})
    for x,col in ((555,'#42dfea'),(760,'#698bff'),(925,'#bb78ff')):
        el(backdrop,'rect',{'x':x,'y':176,'width':48,'height':2,'fill':col,'opacity':.4})
    # The three rear facets create a cage with visible receding side walls.
    panels=[([(557,188),(622,145),(622,305),(557,349)],'#0a1829'),
            ([(622,145),(910,145),(910,305),(622,305)],'url(#v15-panel)'),
            ([(910,145),(975,188),(975,349),(910,305)],'#0b162a')]
    for poly,fill in panels:
        el(backdrop,'polygon',{'points':points(poly),'fill':fill,'fill-opacity':.7,'stroke':'#253a50','stroke-width':1})
        el(backdrop,'polygon',{'points':points(poly),'fill':'url(#v15-mesh)'})
    # A high octagonal truss and two moving spotlights frame the combat space.
    truss='M557 164L622 120H910L975 164M622 120V127M910 120V127'
    el(backdrop,'path',{'d':truss,'stroke':'#1d334d','stroke-width':9,'fill':'none'})
    led(backdrop,'M557 164L622 120H910L975 164','#426182',1)
    led(backdrop,'M594 140L622 121H728','#54e4ec',1.3)
    led(backdrop,'M803 121H910L940 141','#b08aff',1.3)
    beam=el(backdrop,'g',{'class':'v15beamcyan','style':'transform-origin:630px 139px'})
    el(beam,'polygon',{'points':'620,137 635,137 795,374 586,374','fill':'url(#v15-beam-cyan)'})
    beam=el(backdrop,'g',{'class':'v15beamviolet','style':'transform-origin:903px 139px'})
    el(beam,'polygon',{'points':'897,137 911,137 953,375 732,375','fill':'url(#v15-beam-violet)'})
    for x,col in ((630,'#b0fbff'),(903,'#ddc8ff')):
        el(backdrop,'path',{'d':f'M{x-10} 133h20v7h-20z','fill':'#14263b','stroke':'#42617b','stroke-width':1})
        el(backdrop,'rect',{'x':x-7,'y':138,'width':14,'height':3,'fill':col})
    # Rear perimeter, pads and elevated vertical corner posts.
    led(backdrop,'M557 349L622 305H910L975 349','#2d5b70',2)
    led(backdrop,'M557 188L622 145H910L975 188','#324c66',2)
    post(backdrop,622,145,309,'#49dce9');post(backdrop,910,145,309,'#a481ff')
    post(backdrop,557,188,356,'#44e3ed',True);post(backdrop,975,188,356,'#c486ff',True)
    # The mat's eight distinct corners remain visible beneath the fighters.
    el(backdrop,'polygon',{'points':points([(x,y+7) for x,y in octagon]),'fill':'#030a14','stroke':'#1a2b42','stroke-width':1})
    el(backdrop,'polygon',{'points':points(octagon),'fill':'url(#v15-mat)','stroke':'#324c65','stroke-width':1.5})
    el(backdrop,'polygon',{'points':points(octagon),'fill':'url(#v15-matgrain)'})
    inner=[(630,313),(902,313),(966,354),(966,392),(901,416),(631,416),(566,392),(566,354)]
    el(backdrop,'polygon',{'points':points(inner),'fill':'none','stroke':'#44657d','stroke-width':.8,'opacity':.65})
    led(backdrop,'M555 349L555 398L622 425H758','#36dce7',1.7)
    led(backdrop,'M774 425H910L977 398V349','#b482ff',1.7)
    led(backdrop,'M622 305H910','#4a6f8b',1)
    circuit=el(backdrop,'g',{'clip-path':'url(#v15-matclip)','fill':'none','stroke':'#4d8caa','stroke-width':.8,'opacity':.12})
    for x in (588,633,899,945):
        el(circuit,'path',{'d':f'M{x} 331v31l13 8v25h20'})
        el(circuit,'rect',{'x':x+30,'y':392,'width':4,'height':4})
    # A subdued chip-shaped octagonal center mark ties the cage to AI.
    chip=el(backdrop,'g',{'transform':'translate(766 365) scale(1 .38)','opacity':.18})
    el(chip,'path',{'d':'M-40-40H40L58-22V22L40 40H-40L-58 22V-22z','stroke':'#63bdd1','stroke-width':2,'fill':'none'})
    for dx in (-24,-8,8,24):
        el(chip,'path',{'d':f'M{dx} -46v-8M{dx} 46v8','stroke':'#63bdd1','stroke-width':2})
    for dy in (-16,0,16):
        el(chip,'path',{'d':f'M-64 {dy}h-10M64 {dy}h10','stroke':'#63bdd1','stroke-width':2})
    el(chip,'text',{'x':0,'y':12,'text-anchor':'middle','font-family':'Arial,sans-serif','font-size':38,'font-weight':900,'letter-spacing':5,'fill':'#7dd9e5'},'AI')
    # Small segmented edge LEDs pulse gently, always behind the active actors.
    edge=el(backdrop,'g',{'class':'v15edgepulse'})
    for i in range(8):
        x=641+i*32
        el(edge,'rect',{'x':x,'y':420,'width':17,'height':2,'fill':'#54e8ef' if i<4 else '#bb92ff','opacity':.75})
    for x,col in ((570,'#6aeef3'),(949,'#cf9bff')):
        for i in range(4):
            el(backdrop,'path',{'d':f'M{x} {369+i*5}l10 5','stroke':col,'stroke-width':1,'opacity':.35})
    css='''
@keyframes v15beamcyan{0%,100%{transform:rotate(-6deg);opacity:.55}50%{transform:rotate(8deg);opacity:.9}}
.v15beamcyan{animation:v15beamcyan 8000ms ease-in-out infinite}
@keyframes v15beamviolet{0%,100%{transform:rotate(7deg);opacity:.6}50%{transform:rotate(-8deg);opacity:.9}}
.v15beamviolet{animation:v15beamviolet 9500ms ease-in-out infinite}
@keyframes v15edgepulse{0%,100%{opacity:.45}50%{opacity:1}}
.v15edgepulse{animation:v15edgepulse 3600ms ease-in-out infinite}
'''
    root.find('{'+NS+'}style').text=original_css+css
    root.set('aria-label','张健航 · AI 产品经理：在霓虹八角笼中迎战 AI，高扫、德式背摔与裸绞降服获胜')
    assert [ET.tostring(n) for n in list(camera)[1:]]==original_actors
    assert root.find('{'+NS+'}style').text.startswith(original_css)
    assert ET.tostring(next(n for n in root if n.get('id')=='editorial-panel-v8'))==ET.tostring(next(n for n in source if n.get('id')=='editorial-panel-v8'))
    out=ROOT/'assets'/'fight-hero-v15.svg';out.write_text(ET.tostring(root,encoding='unicode'))
    # Freeze only the original fight tracks for composition review. The new
    # arena is the same geometry in the animated and frozen versions.
    old_review=ROOT/'verification'/'v14'/'hold.svg'
    if old_review.exists():
        frozen=deepcopy(root);sample=ET.parse(old_review).getroot()
        frozen.find('{'+NS+'}style').text=sample.find('{'+NS+'}style').text+css
        review=ROOT/'verification'/'v15';review.mkdir(parents=True,exist_ok=True)
        (review/'hold.svg').write_text(ET.tostring(frozen,encoding='unicode'))
    print('PASS: new octagonal cage; all actor elements, choreography and profile copy preserved.')
    print('Built',out.name,round(out.stat().st_size/1024),'KiB')

if __name__=='__main__':build()
