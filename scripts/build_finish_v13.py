"""Restore locomotion and keep the original robot through the submission.

Run: python3 scripts/build_finish_v13.py (standard library).
Opacity belongs on wrappers; an actor has exactly one transform animation.
The robot is never replaced by a generated paired bitmap.
"""
from pathlib import Path
from copy import deepcopy
import importlib.util
import xml.etree.ElementTree as ET
import tempfile
import shutil
import base64
import json
import math

ROOT=Path(__file__).resolve().parents[1]
ART=ROOT/'assets'/'fighter-v13'
NS='http://www.w3.org/2000/svg'
spec=importlib.util.spec_from_file_location('finish_engine',Path(__file__).with_name('build_finish_v12.py'))
f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)
n=f.n;m=f.m;e=f.e
old_choreography=f.choreography

# Position of the unchanged robot's (809,266) pivot in each authored pose.
# The waist and neck, not a newly generated robot silhouette, meet the hands.
BOT_POSES=[(856,266,0),(855,266,0),(856,266,12),(869,268,15),
           (788,258,0),(794,255,0),(778,220,-18),(640,211,-55),
           (654,339,-105),(797,310,-28),(791,312,-8),(791,312,-8),
           (791,312,-8),(791,312,-8),(822,312,-8),(851,311,-8)]
CLIPS={2:'M782 180h92v89h-92z',4:'M724 248h75v65h-75z',
       5:'M739 265h79v54h-79z',6:'M738 240h81v54h-81z',
       7:'M632 215h67v61h-67z',8:'M664 305h54v45h-54z',
       9:'M735 300h72v44h-72z',10:'M722 312h91v34h-91z',
       11:'M712 285h100v35h-100z',
       12:'M708 291L776 294L798 301V324H738L708 309z'}

def local_point(point,pose):
    x,y,deg=pose;a=math.radians(-deg);dx,dy=point[0]-x,point[1]-y
    return 809+dx*math.cos(a)-dy*math.sin(a),266+dx*math.sin(a)+dy*math.cos(a)

def choreography():
    old_choreography()
    start=f.PAIR_START;reset=f.PAIR_END+300
    for tr in (e.BX,e.BY,e.BR,*m.ARMS['near'],*m.ARMS['far']):
        tr.keys={t:v for t,v in tr.keys.items() if t<start or t>=reset}
    for p,pose in zip(f.PAIR,BOT_POSES):
        t=p['t0'];x,y,angle=pose
        # Complete human poses and robot grips change at the same boundary.
        # No different robot frame, body scaling or limb stretching is used.
        for tr,value in ((e.BX,x-809),(e.BY,y-266),(e.BR,angle)):
            tr.put(t,value);tr.put(p['t1']-1,value)
        i=p['frame']
        if i<4:
            m.guard_arms(t) if i in (1,2) else m.rest_arms(t)
        elif i<9:
            m.arm_at('near',t,(751,243));m.arm_at('far',t,(781,221))
        elif i<13:
            for side,point in (('near',(775,320)),('far',(814,317))):
                m.arm_at(side,t,local_point(point,pose))
        elif i==13:
            m.arm_at('near',t,local_point((754,395),pose))
            m.arm_at('far',t,local_point((827,292),pose))
        else:
            m.arm_at('near',t,(759,305));m.arm_at('far',t,(788,300))
        for side in m.ARMS:
            for tr in m.ARMS[side]:tr.put(p['t1']-1,tr.at(t))
    for tr,value in ((e.BX,BOT_POSES[-1][0]-809),(e.BY,BOT_POSES[-1][1]-266),(e.BR,-8)):
        tr.put(reset-1,value)
    # Final event coordinates now refer to the original robot's geometry.
    e.events[-3].update(x=848,y=224)
    e.events[-2].update(x=662,y=387)
    e.events[-1].update(x=791,y=312)

def remove_class(root,name):
    for parent in root.iter():
        for node in list(parent):
            if node.get('class')==name:parent.remove(node)

def wrapper(parent,node,cls):
    index=list(parent).index(node);parent.remove(node)
    outer=ET.Element('{'+NS+'}g',{'class':cls});outer.append(node);parent.insert(index,outer)
    return outer

def assert_animation_ownership(root):
    names={a[0] for a in e.ANIMS}
    for node in root.iter():
        controls=set(node.get('class','').split())&names
        assert len(controls)<=1,('CSS animation shorthand collision',node.tag,controls)
    for name in ('v9player','v9bot'):
        actor=next(node for node in root.iter() if node.get('class')==name)
        assert actor.get('class')==name
        animation=next(a for a in e.ANIMS if a[0]==name)
        assert len({a for t,a in animation[1].items() if t<f.PAIR_START})>15

def build():
    f.choreography=choreography
    with tempfile.TemporaryDirectory(prefix='fight-v13-') as tmp:
        stage=Path(tmp);(stage/'assets').mkdir()
        shutil.copy2(ROOT/'assets'/'fight-hero-v8.svg',stage/'assets'/'fight-hero-v8.svg')
        for name in ('fighter-v10','fighter-v11','fighter-v12'):
            shutil.copytree(ROOT/'assets'/name,stage/'assets'/name)
        f.ROOT=stage;f.ART=stage/'assets'/'fighter-v12';f.build()
        root=ET.parse(stage/'assets'/'fight-hero-v12.svg').getroot()

    camera=next(node for node in root.iter() if node.get('class')=='v9camera')
    scene=next(node for node in root if node.get('id')=='fight-v9')
    defs=root.find('{'+NS+'}defs')
    # v12 attached two animation shorthands to each actor. The opacity rule
    # won the cascade and silently stopped its position/rotation animation.
    # Restore the single transform class and hide only the human's wrapper.
    for node in root.iter():
        if 'v12native' in node.get('class','').split():
            node.set('class',' '.join(c for c in node.get('class').split() if c!='v12native'))
    for cls in ('v12paired','v12tapring'):remove_class(root,cls)
    native=next(node for node in camera if node.get('class')=='v9player')
    pshadow=next(node for node in camera if node.get('class')=='v9pshadow')
    bot=next(node for node in camera if node.get('class')=='v9bot')
    wrapper(camera,native,'v13nativeplayer');wrapper(camera,pshadow,'v13nativeshadow')
    e.windows('v13nativeplayer',[(0,f.PAIR_START),(f.PAIR_END+300,e.T)])
    e.windows('v13nativeshadow',[(0,f.PAIR_START),(f.PAIR_END+300,e.T)])
    e.ANIMS=[a for a in e.ANIMS if a[0] not in ('v12native','v10armsalive','v12tapring') and not a[0].startswith('v12f') and a[0]!='v12paired']
    e.windows('v10armsalive',[(0,e.T)])
    back=ET.Element('{'+NS+'}g',{'class':'v13finishback'})
    camera.insert(list(camera).index(bot),back)
    front=e.el(camera,'g',{'class':'v13finishfront'})
    for group in (back,front):e.windows(group.get('class'),[(f.PAIR_START,f.PAIR_END+300)])
    e.el(back,'ellipse',{'cx':750,'cy':410,'rx':120,'ry':6,'fill':'#05070f','opacity':.25})
    for p in f.PAIR:
        i=p['frame'];cls=f'v13human{i}'
        g=e.el(back,'g',{'class':cls})
        data=base64.b64encode((ART/f'human-{i:02}.png').read_bytes()).decode()
        image=e.el(g,'image',{'id':f'v13humanimage{i}','href':'data:image/png;base64,'+data,
                             'x':542,'y':121,'width':448,'height':300,
                             'preserveAspectRatio':'xMidYMid meet','style':'image-rendering:pixelated'})
        end=p['t1']+300 if i==15 else p['t1'];e.windows(cls,[(p['t0'],end)])
        if i in CLIPS:
            cp=e.el(defs,'clipPath',{'id':f'v13handsclip{i}','clipPathUnits':'userSpaceOnUse'})
            e.el(cp,'path',{'d':CLIPS[i]})
            overlay=e.el(front,'g',{'class':f'v13hands{i}','clip-path':f'url(#v13handsclip{i})'})
            e.el(overlay,'use',{'href':f'#v13humanimage{i}'})
            e.windows(f'v13hands{i}',[(p['t0'],end)])
    # The body/head PNG and all articulated robot limbs are exactly the same
    # elements used during regular fighting. Only its expression may change.
    strain=e.el(bot,'g',{'class':'v13strain'})
    e.el(strain,'rect',{'x':769,'y':199,'width':72,'height':44,'fill':'#101529'})
    for x in (783,819):
        e.el(strain,'path',{'d':f'M{x} 211l8 8m0-8l-8 8','stroke':'#ff4d8d','stroke-width':3,'fill':'none'})
    e.el(strain,'path',{'d':'M792 234h27','stroke':'#ff4d8d','stroke-width':3,'fill':'none'})
    e.windows('v13strain',[(f.PAIR[11]['t0'],f.PAIR[14]['t0'])])
    pulse=e.el(camera,'g',{'class':'v13tapring','fill':'none','stroke':e.CYAN,'stroke-width':2})
    e.el(pulse,'path',{'d':'M748 397h12v4h-12zM742 393h24v12h-24z'})
    e.windows('v13tapring',[(e.final_hit,e.final_hit+120),(e.final_hit+170,e.final_hit+280)])
    root.find('{'+NS+'}style').text=e.timeline_css()
    root.set('aria-label','张健航 · AI 产品经理：拳击进退、高扫衔接德式背摔，裸绞降服机器人')
    assert_animation_ownership(root)
    assert max(m.foot_checks)<.01
    assert {s['direction'] for s in m.steps}=={'advance','retreat'}
    source=ET.parse(ROOT/'assets'/'fight-hero-v11.svg').getroot()
    original=next(node for node in source.iter() if node.get('class')=='v9b0')
    assert next(node for node in bot if node.get('class')=='v9b0').attrib==original.attrib
    assert sum(1 for node in root.iter() if node.get('class')=='v9bot')==1
    assert not any(node.get('class','').startswith('v12f') for node in root.iter())
    out=ROOT/'assets'/'fight-hero-v13.svg';out.write_text(ET.tostring(root,encoding='unicode'))
    review=ROOT/'verification'/'v13';review.mkdir(parents=True,exist_ok=True)
    moments=dict(f.MOMENTS)
    for name in ('advance','retreat'):
        step=next(s for s in m.steps if s['direction']==name)
        moments[name]=step['start']+20;moments[name+'-end']=step['end']-5
    moments['normal']=6000
    for name,ms in moments.items():
        frozen=deepcopy(root);frozen.find('{'+NS+'}style').text=e.timeline_css(ms)
        (review/(name+'.svg')).write_text(ET.tostring(frozen,encoding='unicode'))
    data=dict(duration_ms=e.T,finish_start_ms=f.PAIR_START,tap_ms=e.final_hit,
              result='submission',health_at_win=12,events=e.events,steps=m.steps,
              robot_model='original v9bot (v11 assets), never swapped',
              robot_finish_poses=BOT_POSES,frames=f.PAIR,previews=moments,
              checks=dict(single_animation_per_element=True,single_robot_model=True,
                          planted_foot_max_error=max(m.foot_checks)))
    (ART/'bout.json').write_text(json.dumps(data,indent=2))
    print('PASS locomotion ownership; same robot PNG / group for entire bout;',len(m.steps),'planted steps.')
    print('Built',out.name,round(out.stat().st_size/1024),'KiB; previews',moments)

if __name__=='__main__':build()
