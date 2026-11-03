"""Plant-and-push boxing footwork and a six-attack robot, with a close win.

Run: python3 scripts/build_fight_v10.py (standard library only).
New footwork PNGs are complete authored poses. Ground contacts are measured
from the trainers; no limb / body stretching is used. Robot arms use fixed
length two-bone joints, not an image scaled longer to reach the opponent.
"""
from pathlib import Path
from copy import deepcopy
import importlib.util
import xml.etree.ElementTree as ET
import base64
import json
import math
import tempfile
import shutil

ROOT=Path(__file__).resolve().parents[1]
NS='http://www.w3.org/2000/svg'
ET.register_namespace('',NS)
spec=importlib.util.spec_from_file_location('fight_engine',Path(__file__).with_name('build_fight_v9.py'))
e=importlib.util.module_from_spec(spec);spec.loader.exec_module(e)
FOOT=json.loads((ROOT/'assets'/'fighter-v10'/'footwork.json').read_text())
steps=[];foot_checks=[];arm_checks=[]

# Start a fresh bout; importing v9 only supplies the SVG renderer and helpers.
for name,val in dict(P=0,B=0,PX=-24,BX=35,BY=0,BR=0,PR=0,LIGHT=1,CAMERA_X=0,CAMERA_Y=0,P_HP=100,B_HP=100).items():
    setattr(e,name,e.Track(val))
e.events=[];e.phases=[];e.guards=[];e.bot_guards=[];e.time=0;e.final_hit=None;e.ANIMS=[]
PY=e.Track(0)
ARMS={}
for side in ('near','far'):
    ARMS[side]=(e.Track(0),e.Track(0))
SHOULDERS={'near':(771,276),'far':(783,269)}
L1,L2=40,42

def arm_at(side,t,target,prefer=(-.2,1)):
    sx,sy=SHOULDERS[side];gx,gy=target
    dx,dy=gx-sx,gy-sy;dist=math.hypot(dx,dy)
    if dist>L1+L2-.1:
        gx=sx+dx*(L1+L2-.1)/dist;gy=sy+dy*(L1+L2-.1)/dist
        dx,dy=gx-sx,gy-sy;dist=L1+L2-.1
    a=math.atan2(dy,dx);da=math.acos(max(-1,min(1,(L1*L1+dist*dist-L2*L2)/(2*L1*dist))))
    candidates=[(sx+L1*math.cos(a+sg*da),sy+L1*math.sin(a+sg*da)) for sg in (-1,1)]
    ex,ey=max(candidates,key=lambda p:(p[0]-sx)*prefer[0]+(p[1]-sy)*prefer[1])
    aa=math.degrees(math.atan2(ey-sy,ex-sx));bb=math.degrees(math.atan2(gy-ey,gx-ex))-aa
    for tr,val in zip(ARMS[side],(aa,bb)):
        old=tr.at(t)
        while val-old>180:val-=360
        while val-old< -180:val+=360
        tr.put(t,val)
    arm_checks.append(dict(t=t,side=side,upper=math.hypot(ex-sx,ey-sy),fore=math.hypot(gx-ex,gy-ey)))

REST={'near':(751,256),'far':(782,247)}
GUARD={'near':(752,222),'far':(772,211)}
for side in ARMS:arm_at(side,0,REST[side])

def rest_arms(t):
    for side in ARMS:arm_at(side,t,REST[side])

def guard_arms(t):
    for side in ARMS:arm_at(side,t,GUARD[side])

def pin(tr):tr.put(e.time,tr.at(e.time))

def step_once(direction,duration=420):
    """Lead foot first on advance; rear foot first on retreat.

    During the push half, the driving foot has a constant WORLD coordinate.
    After the landing, the new support foot stays fixed while its partner
    follows. A small recoil / weight transfer is not treated as locomotion.
    """
    start=e.time;cur=e.PX.at(start);base=FOOT['base']
    r0,l0=base['rear']['x'],base['lead']['x']
    forward=direction>0
    ids=[1,2,3,4,5] if forward else [9,10,11,12,11]
    landing=FOOT['frames'][4 if forward else 12]
    width=landing['lead']['x']-landing['rear']['x']
    stride=width-(l0-r0)
    assert stride>=12,(direction,stride)
    end_x=cur+stride if forward else cur-stride
    if not -48<=end_x<=42:return False
    fractions=[0,.17,.34,.52,.70,.87,1]
    old_x=cur;old_y=0
    driving_world=cur+(r0 if forward else l0)
    landed_world=(cur+r0+width) if forward else (cur+l0-width)
    records=[]
    for j,idx in enumerate(ids):
        t=start+round(duration*fractions[j+1]);frame=FOOT['frames'][idx]
        driving=j<4
        which=('rear' if forward else 'lead') if driving else ('lead' if forward else 'rear')
        anchor=driving_world if driving else landed_world
        x=anchor-frame[which]['x']
        y=base[which]['y']-frame[which]['y']
        # Hold each support position between image changes; never slide a
        # planted trainer through space between two key poses.
        e.PX.put(t-1,old_x);e.PX.put(t,x)
        PY.put(t-1,old_y);PY.put(t,y)
        e.P.put(t,24+idx)
        records.append(dict(t=t,pose=24+idx,support=which,world=anchor,x=x))
        foot_checks.append(abs(x+frame[which]['x']-anchor))
        old_x,old_y=x,y
    end=start+duration
    e.PX.put(end-1,old_x);e.PX.put(end,end_x)
    PY.put(end-1,old_y);PY.put(end,0);e.P.put(end,0)
    steps.append(dict(start=start,end=end,direction='advance' if forward else 'retreat',from_x=cur,to_x=end_x,poses=records))
    e.time=end
    return True

def move_toward(target,maximum=2,fast=False):
    for _ in range(maximum):
        delta=target-e.PX.at(e.time)
        if abs(delta)<12:break
        if not step_once(1 if delta>0 else -1,350 if fast and delta>0 else 430):break

def wait(ms=160,pose=0,phase=None,bx=None):
    # Deliberately do not move PX here: all locomotion goes through step_once.
    e.hold(ms,pose,bx=bx,phase=phase)

def punch(kind,result='hit',damage=0,finisher=False):
    start=e.time;cur=e.PX.at(start)
    if result=='block':guard_arms(start+80)
    else:rest_arms(start+100)
    e.player_attack(kind,result,damage,px=cur,finisher=finisher)
    if result=='block':rest_arms(e.time)
    if result=='hit' and not finisher:rest_arms(e.time)

ROBOT={
    'jab':dict(side='near',wind=(752,246),mid=(730,236),end=(704,232),prep=160,flight=85,recover=300),
    'cross':dict(side='far',wind=(784,244),mid=(747,239),end=(709,242),prep=185,flight=95,recover=330),
    'body':dict(side='near',wind=(758,289),mid=(729,286),end=(695,275),prep=145,flight=90,recover=300),
    'hook':dict(side='near',wind=(779,221),mid=(743,206),end=(716,222),prep=230,flight=115,recover=370),
    'upper':dict(side='far',wind=(758,315),mid=(735,284),end=(724,248),prep=210,flight=100,recover=370),
    'overhand':dict(side='near',wind=(778,199),mid=(738,191),end=(712,224),prep=310,flight=130,recover=510),
}

def robot(kind,result='block',damage=0):
    start=e.time;spec=ROBOT[kind];impact=start+spec['prep']+spec['flight'];end=impact+spec['recover']
    cur=e.PX.at(start);side=spec['side'];other='far' if side=='near' else 'near'
    # Misses are overhead slips/rolls. Hits land at the near shoulder / torso;
    # blocks touch the guarding fist instead of passing through the head.
    target_x=(722 if result=='block' else 690 if result=='hit' else 718)+cur
    bx=target_x-spec['end'][0]
    for tr in (e.PX,e.BX,e.BY,e.BR,e.PR,e.LIGHT):pin(tr)
    e.B.put(start,0);e.B.put(start+100,2)
    e.BX.put(start+spec['prep']*.6,e.BX.at(start)+8)
    e.BX.put(impact,bx)
    e.BY.put(start+spec['prep'],-8 if kind in ('hook','overhand') else 3 if kind=='upper' else 0)
    e.BY.put(impact,0);e.BR.put(start+spec['prep'],6 if kind in ('cross','overhand') else -3);e.BR.put(impact,0)
    arm_at(side,start,REST[side]);arm_at(other,start+100,GUARD[other])
    arm_at(side,start+spec['prep']*.65,spec['wind'],(-.2,-1) if kind=='overhand' else (-.2,1))
    arm_at(side,start+spec['prep'],spec['mid'],(-.2,-1) if kind in ('overhand','hook') else (-.2,1))
    arm_at(side,impact,spec['end'],(-.2,-1) if kind=='hook' else (-.2,1))
    if result=='miss':
        pseq=[(0,0),(spec['prep']*.55,11),(spec['prep']*.9,12),(spec['prep']+spec['flight']+140,13),(end-start-90,0)]
    elif result=='block':
        pseq=[(0,0),(spec['prep']*.65,11),(end-start-170,13),(end-start-70,0)]
        e.guards.append((impact-60,impact+160))
    else:
        pseq=[(0,0),(impact-start,1),(impact-start+120,10),(end-start-80,0)]
    for dt,p in pseq:e.P.put(start+round(dt),p)
    x=target_x;y=spec['end'][1]
    e.events.append(dict(t=impact,end=end,actor='robot',kind=kind,result=result,damage=damage,x=x,y=y,
                         px=cur,bx=bx,high=kind!='body',finisher=False))
    if result=='hit':
        e.P_HP.put(impact,max(0,e.P_HP.at(impact,True)-damage))
        e.PX.put(impact,cur);e.PX.put(impact+90,cur-6);e.PX.put(end,cur-5)
        e.PR.put(impact,0);e.PR.put(impact+65,-4 if kind in ('hook','overhand') else -2);e.PR.put(impact+220,0)
        e.LIGHT.put(impact-1,1);e.LIGHT.put(impact,1.4);e.LIGHT.put(impact+130,1)
        for dt,v in [(0,0),(35,-2.5),(80,1.5),(160,0)]:e.CAMERA_X.put(impact+dt,v)
    elif result=='block':
        e.PX.put(impact,cur);e.PX.put(impact+65,cur-2);e.PX.put(end,cur)
    else:e.PX.put(end,cur)
    arm_at(side,impact+120,spec['end'],(-.2,-1) if kind=='hook' else (-.2,1))
    rest_arms(end)
    e.BX.put(impact+120,bx+3);e.BX.put(end,bx+20)
    e.BY.put(end,0);e.BR.put(end,0)
    e.B.put(impact+170,0)
    e.time=end

def choreography():
    wait(400);wait(400,1);wait(400)
    wait(120,phase='FIGHT FOR SPACE')
    move_toward(-6,fast=True)
    punch('jab','block');punch('jab','block');punch('cross','hit',7)
    robot('jab','block');robot('body','hit',12)
    move_toward(-33)
    robot('hook','hit',14);robot('cross','block');robot('upper','miss')
    move_toward(-10,fast=True);punch('hook','hit',10)
    wait(150,phase='BREAK THE RHYTHM')
    robot('overhand','hit',17)
    punch('jab','miss');robot('jab','block');robot('body','hit',16)
    move_toward(-44)
    robot('cross','block');robot('hook','miss')
    move_toward(-5,fast=True)
    punch('jab','hit',7);punch('cross','hit',10);punch('cross','block')
    robot('upper','hit',15)
    wait(210,1,phase='STAY COMPOSED')
    move_toward(-36)
    robot('overhand','miss')
    move_toward(-8,fast=True);punch('hook','hit',10)
    robot('jab','hit',14)
    robot('cross','block');robot('body','block');robot('hook','miss')
    wait(100,phase='MAKE THE OPENING')
    move_toward(5,fast=True);punch('cross','hit',13)
    robot('jab','miss')
    punch('jab','hit',8);punch('cross','hit',10)
    move_toward(25,fast=True)
    punch('hook','hit',10);punch('upper','hit',15,finisher=True)
    e.P.put(e.time,22);e.time+=380;e.P.put(e.time,23);e.time+=2500
    e.P.put(e.time+300,0);e.B.put(e.time+300,0)
    for tr,val in ((e.PX,-24),(PY,0),(e.BX,35),(e.BY,0),(e.BR,0),(e.PR,0),(e.LIGHT,1),(e.P_HP,100),(e.B_HP,100)):
        tr.put(e.time+299,tr.at(e.time+299,tr in (e.P_HP,e.B_HP)));tr.put(e.time+300,val)
    rest_arms(e.time+300)
    e.time+=800;e.T=e.time

def validate():
    assert sum(n['damage'] for n in e.events if n['actor']=='player')==100
    assert sum(n['damage'] for n in e.events if n['actor']=='robot')==88
    assert e.P_HP.at(e.final_hit,True)==12 and e.B_HP.at(e.final_hit,True)==0
    assert all(n['damage']==0 for n in e.events if n['result']!='hit')
    assert all(err<.01 for err in foot_checks)
    assert all(abs(a['upper']-L1)<.001 and abs(a['fore']-L2)<.001 for a in arm_checks)
    assert {s['direction'] for s in steps}=={'advance','retreat'}
    assert len({n['kind'] for n in e.events if n['actor']=='robot'})==6
    assert not any(n['t']>e.final_hit for n in e.events)
    print(f'PASS: {len(steps)} planted-foot steps; 6 robot attacks; {len(e.events)} exchanges; win with 12% HP; {e.T/1000:.2f}s.')

def make_arm(parent,side):
    shoulder=SHOULDERS[side]
    g=e.el(parent,'g',{'transform':f'translate({shoulder[0]} {shoulder[1]})','class':'v10armsalive'})
    upper=e.el(g,'g',{'class':'v10'+side+'upper'})
    # Stepped plates and narrow inner actuators match the pixel robot's armor.
    e.el(upper,'path',{'d':'M-4-6h9v2h31v-2h8v12h-8V4H5v2h-9z','fill':'#343a54','stroke':'#0c1020','stroke-width':2})
    e.el(upper,'rect',{'x':4,'y':-3,'width':32,'height':6,'fill':'#aebed6'})
    e.el(upper,'rect',{'x':8,'y':-3,'width':23,'height':2,'fill':'#e1eafa'})
    elbow=e.el(upper,'g',{'transform':f'translate({L1} 0)'})
    e.el(elbow,'rect',{'x':-6,'y':-6,'width':12,'height':12,'fill':'#626f91','stroke':'#10162b','stroke-width':2})
    fore=e.el(elbow,'g',{'class':'v10'+side+'fore'})
    e.el(fore,'path',{'d':'M0-5h29v-3h12v16H29V5H0z','fill':'#b2bed6','stroke':'#10162b','stroke-width':2})
    e.el(fore,'rect',{'x':4,'y':-3,'width':24,'height':2,'fill':'#e2ecfc'})
    fist=e.el(fore,'g',{'transform':f'translate({L2} 0)'})
    e.el(fist,'path',{'d':'M-8-9H7v3h4V7H7v3H-8z','fill':'#dbe6f6','stroke':'#0d1226','stroke-width':2})
    e.el(fist,'rect',{'x':-4,'y':-5,'width':7,'height':10,'fill':'#5f6e91'})
    e.el(fist,'rect',{'x':-2,'y':-3,'width':3,'height':6,'fill':'#ff6a95'})
    for part,tr in zip(('upper','fore'),ARMS[side]):e.animation('v10'+side+part,tr,lambda v:f'transform:rotate({e.fmt(v)}deg)')
    return g

def build():
    choreography();e.validate=validate
    with tempfile.TemporaryDirectory(prefix='fight-v10-') as tmp:
        stage=Path(tmp);(stage/'assets').mkdir();shutil.copy2(ROOT/'assets'/'fight-hero-v8.svg',stage/'assets'/'fight-hero-v8.svg')
        e.ROOT=stage;e.build()
        root=ET.parse(stage/'assets'/'fight-hero-v9.svg').getroot()
    player=next(n for n in root.iter() if n.get('class')=='v9react')
    for i in range(16):
        data=base64.b64encode((ROOT/'assets'/'fighter-v10'/f'foot-{i:02}.png').read_bytes()).decode()
        e.el(player,'image',{'class':'v9p'+str(24+i),'href':'data:image/png;base64,'+data,'x':541,'y':145,'width':320,'height':280,'preserveAspectRatio':'xMidYMid meet','style':'image-rendering:pixelated'})
        e.visibility('v9p'+str(24+i),e.P,24+i)
    # Replace only player translation with the grounded step controller.
    e.ANIMS=[a for a in e.ANIMS if a[0] not in ('v9player','v9php')]
    e.transform_track('v9player',[e.PX,PY],lambda v:f'transform:translate({e.fmt(v[0])}px,{e.fmt(v[1])}px)')
    e.animation('v9php',e.P_HP,lambda v:f'transform:scaleX({e.fmt(v/100)});transform-origin:563px 0;fill:{"#ff6a86" if v<=26 else "#ffd65c"}',step=True)
    bot=next(n for n in root.iter() if n.get('class')=='v9bot')
    idle=next(n for n in bot if n.get('class')=='v9b0')
    punch_image=next(n for n in bot if n.get('class')=='v9b2')
    punch_image.set('href',idle.get('href')) # old single piston is now obsolete
    far=ET.Element('{'+NS+'}g');make_arm(far,'far');bot.insert(0,far)
    make_arm(bot,'near')
    eyes=e.el(bot,'g',{'class':'v10eyes','fill':'#ff4d8d'})
    for x in (785.5,821.2):e.el(eyes,'rect',{'x':x,'y':209.5,'width':10,'height':7})
    e.visibility('v10eyes',e.B,2)
    e.windows('v10armsalive',[(0,e.final_hit+60),(e.T-500,e.T)])
    # Technique wins the exchange; keep the AI cues on the robot / hit chips,
    # and remove the earlier magic charging orb from the boxer's hands.
    for parent in root.iter():
        for node in list(parent):
            if node.get('class')=='v9charge':parent.remove(node)
    style=root.find('{'+NS+'}style');style.text=e.timeline_css()
    root.set('aria-label','张健航 · AI 产品经理：拳击进退步，六种机器人攻势，低血量反击获胜')
    output=ROOT/'assets'/'fight-hero-v10.svg';output.write_text(ET.tostring(root,encoding='unicode'))
    review=ROOT/'verification'/'v10';review.mkdir(parents=True,exist_ok=True)
    first_forward=next(s for s in steps if s['direction']=='advance')
    first_back=next(s for s in steps if s['direction']=='retreat')
    picks={
        'push-forward':first_forward['poses'][1]['t']+20,
        'lead-land':first_forward['poses'][3]['t']+20,
        'rear-follow':first_forward['poses'][4]['t']+20,
        'push-back':first_back['poses'][1]['t']+20,
        'rear-land':first_back['poses'][3]['t']+20,
        'lead-follow':first_back['poses'][4]['t']+20,
        'critical':next(n['t'] for n in e.events if n['actor']=='robot' and e.P_HP.at(n['t'],True)==12)+70,
        'win':e.final_hit+1650,
    }
    for kind in ROBOT:
        ev=next(n for n in e.events if n['actor']=='robot' and n['kind']==kind)
        picks[kind+'-wind']=ev['t']-ROBOT[kind]['flight']-25
        picks[kind]=ev['t']+25
    for name,ms in picks.items():
        frozen=deepcopy(root);frozen.find('{'+NS+'}style').text=e.timeline_css(ms)
        for parent in frozen.iter():
            for node in list(parent):
                cls=node.get('class','')
                if node.tag.endswith('image') and ((cls.startswith('v9p') and cls!='v9p'+str(e.P.at(ms,True))) or (cls.startswith('v9b') and cls!='v9b'+str(e.B.at(ms,True)))):parent.remove(node)
        (review/(name+'.svg')).write_text(ET.tostring(frozen,encoding='unicode'))
    data=dict(duration_ms=e.T,final_hit_ms=e.final_hit,health_at_win=12,events=e.events,steps=steps,previews=picks)
    (ROOT/'assets'/'fighter-v10'/'bout.json').write_text(json.dumps(data,indent=2))
    print('Built',output.name,round(output.stat().st_size/1024),'KiB; previews:',picks)

if __name__=='__main__':build()
