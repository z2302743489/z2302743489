"""Neck contact, continuous suplex descent, impact expression and win stars.

Run with Python's standard library. Authored human poses are exported by
prepare_finish_v14.py; the original robot stays a single rigid SVG actor.
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
ART=ROOT/'assets'/'fighter-v14'
THIRD_PRINCIPLE='用行动检验假设，用反馈校准方向。'
NS='http://www.w3.org/2000/svg'
spec=importlib.util.spec_from_file_location('v13_engine',Path(__file__).with_name('build_finish_v13.py'))
g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
f=g.f;n=g.n;m=g.m;e=g.e
old_choreography=g.choreography
for i in (11,12,13):g.BOT_POSES[i]=(760,297,-8)
for i in (11,12):g.CLIPS[i]='M708 273H780V306H708z'
FALL=[];ROLL=[];IMPACT=None

def smooth(u):return u*u*(3-2*u)

def put_bot(t,x,y,deg):
    for tr,v in ((e.BX,x-809),(e.BY,y-266),(e.BR,deg)):tr.put(t,v)

def choreography():
    global IMPACT
    old_choreography()
    start=f.PAIR[7]['t0'];IMPACT=e.events[-2]['t'];end=f.PAIR[9]['t0']
    for tr in (e.BX,e.BY,e.BR):
        tr.keys={t:v for t,v in tr.keys.items() if not start<=t<end}
    # A continuous rigid-body trajectory. The hand anchor barely moves while
    # the robot rotates over it; the final descent accelerates into the mat.
    for t in sorted(set(range(start,IMPACT,16))|{start+90,start+260,IMPACT}):
        u=(t-start)/(IMPACT-start)
        hand_x=676+6*smooth(u)
        hand_y=236+12*smooth(min(1,u/.30))+46*smooth(max(0,(u-.62)/.38))
        angle=-55-69*smooth(u);a=math.radians(angle)
        x=hand_x+44*math.sin(a);y=hand_y-44*math.cos(a)
        put_bot(t,x,y,angle)
        FALL.append(dict(t=t,x=x,y=y,angle=angle,grip=[hand_x,hand_y]))
    final=FALL[-1]
    # A small rebound and settling motion, with no body squashing/scaling.
    for dt,dy,da in ((0,0,0),(25,2,.8),(65,-5,-1.6),(115,0,.5),(165,-.7,-.2),(205,0,0)):
        put_bot(IMPACT+dt,final['x'],final['y']+dy,final['angle']+da)
    put_bot(end-1,final['x'],final['y'],final['angle'])
    # Roll from the landing into seated back control without a one-frame
    # jump across the mat. The human's roll pose occupies this same passage.
    roll_end=f.PAIR[10]['t0'];target=g.BOT_POSES[10]
    for tr in (e.BX,e.BY,e.BR):
        tr.keys={t:v for t,v in tr.keys.items() if not end<=t<roll_end}
    for t in sorted(set(range(end,roll_end,16))|{roll_end}):
        u=smooth((t-end)/(roll_end-end))
        x=final['x']+(target[0]-final['x'])*u
        y=final['y']+(target[1]-final['y'])*u
        angle=final['angle']+(target[2]-final['angle'])*u
        put_bot(t,x,y,angle);ROLL.append(dict(t=t,x=x,y=y,angle=angle))
    for dt,x,y in ((0,0,0),(18,3,1),(42,-2,-.8),(74,1.2,.4),(112,-.5,0),(175,0,0)):
        e.CAMERA_X.put(IMPACT+dt,x);e.CAMERA_Y.put(IMPACT+dt,y)
    for i in (11,12):
        p=f.PAIR[i];pose=g.BOT_POSES[i]
        for side,point in (('near',(749,303)),('far',(777,295))):
            m.arm_at(side,p['t0'],g.local_point(point,pose))
            for tr in m.ARMS[side]:tr.put(p['t1']-1,tr.at(p['t0']))
    p=f.PAIR[13];pose=g.BOT_POSES[13]
    m.arm_at('near',p['t0'],g.local_point((742,391),pose))
    m.arm_at('far',p['t0'],g.local_point((803,281),pose))
    for side in m.ARMS:
        for tr in m.ARMS[side]:tr.put(p['t1']-1,tr.at(p['t0']))
    # The robot moves away only once the tap has been acknowledged.
    put_bot(e.final_hit+45,*g.BOT_POSES[13])
    for tr in (e.BX,e.BY,e.BR):tr.keys.pop(p['t1']-1,None)

def image(group,path,x=542):
    data=base64.b64encode(path.read_bytes()).decode()
    return e.el(group,'image',{'href':'data:image/png;base64,'+data,'x':x,'y':121,
                              'width':448,'height':300,'preserveAspectRatio':'xMidYMid meet',
                              'style':'image-rendering:pixelated'})

def face(bot,cls,intervals,dazed=False):
    group=e.el(bot,'g',{'class':cls})
    e.el(group,'rect',{'x':769,'y':199,'width':72,'height':44,'fill':'#101529'})
    if dazed:
        for x in (784,820):
            e.el(group,'path',{'d':f'M{x} 211h8v8h-8zM{x+2} 213h4v4h-4z',
                              'stroke':'#ffcf67','stroke-width':2,'fill':'none'})
        mouth='M792 235h5v-3h6v3h6v-3h6'
    else:
        for x,sgn in ((784,1),(828,-1)):
            e.el(group,'path',{'d':f'M{x} 210l{8*sgn} 5l{-8*sgn} 5',
                              'stroke':'#ff6396','stroke-width':3,'fill':'none','stroke-linejoin':'miter'})
        mouth='M791 236v-4h6v3h6v-3h6v4h6'
        e.el(group,'path',{'d':'M836 223h3v5h-3z','fill':e.CYAN})
    e.el(group,'path',{'d':mouth,'stroke':'#ff6396','stroke-width':2.5,'fill':'none'})
    e.windows(cls,intervals)

def build():
    g.choreography=choreography
    with tempfile.TemporaryDirectory(prefix='fight-v14-') as tmp:
        stage=Path(tmp);(stage/'assets').mkdir()
        for name in ('fight-hero-v8.svg','fight-hero-v11.svg'):
            shutil.copy2(ROOT/'assets'/name,stage/'assets'/name)
        for name in ('fighter-v10','fighter-v11','fighter-v12','fighter-v13'):
            shutil.copytree(ROOT/'assets'/name,stage/'assets'/name)
        for i in (11,12):shutil.copy2(ART/'choke.png',stage/'assets'/'fighter-v13'/f'human-{i:02}.png')
        g.ROOT=stage;g.ART=stage/'assets'/'fighter-v13';g.build()
        root=ET.parse(stage/'assets'/'fight-hero-v13.svg').getroot()
    panel=next(node for node in root if node.get('id')=='editorial-panel-v8')
    third=next(node for node in panel if node.text=='用真实反馈，校准每次判断。')
    third.text=THIRD_PRINCIPLE
    camera=next(node for node in root.iter() if node.get('class')=='v9camera')
    bot=next(node for node in root.iter() if node.get('class')=='v9bot')
    back=next(node for node in root.iter() if node.get('class')=='v13finishback')
    front=next(node for node in root.iter() if node.get('class')=='v13finishfront')
    defs=root.find('{'+NS+'}defs')
    start=f.PAIR[7]['t0'];end=f.PAIR[9]['t0']
    for cls in ('v13human8','v13hands7','v13hands8','v13strain'):
        g.remove_class(root,cls)
    remove={'v13human7','v13human8','v13hands7','v13hands8','v13strain'}
    e.ANIMS=[a for a in e.ANIMS if a[0] not in remove]
    e.windows('v13human7',[(start,start+90)])
    # Front forearms are clips of the exact same full-body pose, so no extra
    # hands or trainers can be introduced by the layering.
    poses=[('arch',ROOT/'assets'/'fighter-v13'/'human-07.png',542,start,start+90,'M648 213h51v60h-51z'),
           ('descent',ART/'fall-2.png',550,start+90,start+260,'M650 227h61v55h-61z'),
           ('land',ART/'fall-3.png',560,start+260,end,'M651 278h59v53h-59z')]
    for name,path,x,t0,t1,clip in poses:
        if name=='arch':node=next(node for node in back if node.get('class')=='v13human7')
        else:
            node=e.el(back,'g',{'class':'v14'+name});im=image(node,path,x)
            im.set('id','v14image'+name);e.windows('v14'+name,[(t0,t1)])
        cp=e.el(defs,'clipPath',{'id':'v14clip'+name,'clipPathUnits':'userSpaceOnUse'})
        e.el(cp,'path',{'d':clip})
        fg=e.el(front,'g',{'class':'v14hands'+name,'clip-path':'url(#v14clip'+name+')'})
        e.el(fg,'use',{'href':'#v13humanimage7' if name=='arch' else '#v14image'+name})
        e.windows('v14hands'+name,[(t0,t1)])
    # Pain begins at the mat contact, well before the later submission.
    face(bot,'v14pain',[(IMPACT,f.PAIR[14]['t0'])])
    face(bot,'v14dazed',[(f.PAIR[14]['t0'],f.PAIR_END+300)],True)
    stars=e.el(bot,'g',{'class':'v14stars'})
    win=f.PAIR[15]['t0'];e.windows('v14stars',[(win,f.PAIR_END+180)])
    for j,(x,y,size) in enumerate(((789,213,3),(814,209,2.5),(833,222,2.3),(803,218,1.9))):
        cls='v14star'+str(j);star=e.el(stars,'g',{'class':cls})
        # Tiny square-cluster stars, emerging at the face and drifting upward.
        shape=e.el(star,'g',{'transform':f'translate({x} {y}) scale({size})','fill':'#ffe489',
                             'stroke':'#644d2c','stroke-width':.45,'paint-order':'stroke'})
        e.el(shape,'path',{'d':'M-1-4h2v2h2v1h2v2H3v1H1v2h-2V2h-2V1h-2v-2h2v-1h2z'})
        keys={0:(0,0,0,.2),e.T:(0,0,0,.2)}
        for k in range(4):
            t=win+j*110+k*640
            if t>=f.PAIR_END:continue
            for dt,op,dx,dy,scale in ((0,0,0,0,.25),(75,1,-3+j*2,-6,.8),
                                      (225,1,(-1 if j%2 else 1)*13,-25,1),
                                      (430,.9,(-1 if j%2 else 1)*19,-43,.75),(580,0,0,-53,.2)):
                keys[min(t+dt,e.T)]=(op,dx,dy,scale)
        e.animation(cls,keys,lambda v:f'opacity:{e.fmt(v[0])};transform:translate({e.fmt(v[1])}px,{e.fmt(v[2])}px) scale({e.fmt(v[3])})')
        star.set('style',f'transform-origin:{x}px {y}px')
    # Place the tap indicator under the hand at the corrected rear-control pose.
    tap=next(node for node in camera if node.get('class')=='v13tapring')
    next(iter(tap)).set('d','M736 394h12v4h-12zM730 390h24v12h-24z')
    # A brief mat mark complements the rigid rebound; it never distorts actors.
    mark=e.el(camera,'g',{'class':'v14mat','stroke':'#5adbe8','stroke-width':2,'fill':'none'})
    e.el(mark,'path',{'d':'M570 405h72m-56-7l-8-5m45 5l10-5'})
    e.animation('v14mat',{0:0,IMPACT-1:0,IMPACT:.8,IMPACT+180:0})
    root.find('{'+NS+'}style').text=e.timeline_css()
    root.set('aria-label','张健航 · AI 产品经理：高扫、德式背摔与裸绞降服，机器人落地受挫、获胜冒星')
    g.assert_animation_ownership(root)
    assert len(FALL)>18 and all(b['t']>a['t'] for a,b in zip(FALL,FALL[1:]))
    assert max(abs(b['angle']-a['angle']) for a,b in zip(FALL,FALL[1:]))<7
    assert sum(1 for node in root.iter() if node.get('class')=='v9bot')==1
    out=ROOT/'assets'/'fight-hero-v14.svg';out.write_text(ET.tostring(root,encoding='unicode'))
    moments=dict(f.MOMENTS,fall_early=start+110,fall_late=start+235,
                 landing=IMPACT+30,pain=IMPACT+100,stars=win+410,stars_high=win+790)
    review=ROOT/'verification'/'v14';review.mkdir(parents=True,exist_ok=True)
    for name,ms in moments.items():
        frozen=deepcopy(root);frozen.find('{'+NS+'}style').text=e.timeline_css(ms)
        (review/(name+'.svg')).write_text(ET.tostring(frozen,encoding='unicode'))
    data=dict(duration_ms=e.T,impact_ms=IMPACT,tap_ms=e.final_hit,win_stars_ms=win,
              robot_model='original v9bot',fall_samples=FALL,roll_samples=ROLL,previews=moments,
              result='submission',health_at_win=12,events=e.events,
              checks=dict(single_animation_per_element=True,single_robot_model=True,
                          continuous_fall=True,neck_connector=[759,289],chest_y=338))
    (ART/'bout.json').write_text(json.dumps(data,indent=2))
    print('PASS continuous rigid fall, impact pain, neck hold and win stars; built',out.name)

if __name__=='__main__':build()
