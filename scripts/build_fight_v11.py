"""Dense MMA exchanges: kicks, knees, two-way wrestling and grounded recovery.

Run: python3 scripts/build_fight_v11.py (standard library only).
All human MMA poses are complete authored PNGs at one fixed scale. The v10
ground-contact footwork and articulated robot arms are reused unchanged.
"""
from pathlib import Path
from copy import deepcopy
import importlib.util
import xml.etree.ElementTree as ET
import tempfile
import shutil
import base64
import math
import json

ROOT=Path(__file__).resolve().parents[1]
NS='http://www.w3.org/2000/svg'
spec=importlib.util.spec_from_file_location('mma_engine',Path(__file__).with_name('build_fight_v10.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
e=m.e
ART=ROOT/'assets'/'fighter-v11'
SUPPORTS=json.loads((ART/'supports.json').read_text())
grapples=[];leg_windows=[];support_checks=[];LU=e.Track(0);LL=e.Track(0)
for item in e.ATTACKS.values():item['dur']=[max(55,round(v*.70)) for v in item['dur']]
for item in m.ROBOT.values():
    item['prep']=round(item['prep']*.62);item['flight']=round(item['flight']*.62)
    item['recover']=max(190,round(item['recover']*.62))

def frames(start,poses,durations):
    t=start
    for p,d in zip(poses,durations):e.P.put(t,p);t+=d
    return t

def move(target):
    # Short planted steps stay in the fight instead of long empty transitions.
    for _ in range(2):
        delta=target-e.PX.at(e.time)
        if abs(delta)<12:break
        if not m.step_once(1 if delta>0 else -1,295 if delta>0 else 340):break

def phase(label):e.phases.append((e.time,label))

def camera(t,amount=2):
    for dt,v in [(0,0),(35,amount),(75,-amount*.6),(140,0)]:e.CAMERA_X.put(t+dt,v)

def health(t,actor,damage):
    tr=e.B_HP if actor=='player' else e.P_HP
    tr.put(t,max(0,tr.at(t,True)-damage))

def event(t,end,actor,kind,result,damage,x,y,**extra):
    e.events.append(dict(t=t,end=end,actor=actor,kind=kind,result=result,damage=damage,x=x,y=y,
                         px=e.PX.at(t),bx=e.BX.at(t),high=True,finisher=False,**extra))
    if damage:health(t,actor,damage);camera(t,3 if 'throw' in kind or 'takedown' in kind else 1.8)

MMA={
    'low kick':dict(poses=[41,42,43,44,0],dur=[90,80,90,70,80],contact=(748,329),surface=772,body_y=315),
    'teep':dict(poses=[45,46,47,48,0],dur=[75,80,90,70,85],contact=(795,262),surface=772,body_y=292),
    'knee':dict(poses=[49,50,51,52,0],dur=[60,70,85,70,65],contact=(727,260),surface=772,body_y=292),
}

def strike(kind,result='hit',damage=0):
    # A teep loads onto the rear foot, so leave room behind that foot before
    # leaning back. Use the authored stepping cycle instead of a root slide.
    if kind=='teep':
        for _ in range(3):
            if e.PX.at(e.time)>=-5:break
            if not m.step_once(1,250):break
    spec=MMA[kind];start=e.time;cur=e.PX.at(start);impact=start+sum(spec['dur'][:2])
    e.PR.put(start,0)
    end=frames(start,spec['poses'],spec['dur'])
    support=m.FOOT['base']['rear' if kind=='teep' else 'lead']
    t=start;old_x=cur;old_y=0;impact_offset=0;impact_y=0
    for p,d in zip(spec['poses'],spec['dur']):
        if p>=40:
            foot=SUPPORTS[str(p-40)];offset=support['x']-foot['x'];yy=support['y']-foot['y']
        else:offset=0;yy=0
        e.PX.put(t-1,old_x);e.PX.put(t,cur+offset)
        m.PY.put(t-1,old_y);m.PY.put(t,yy)
        if p>=40:support_checks.append(dict(t=t,foot_x=foot['x'],world=cur+support['x']))
        if t==impact:impact_offset=offset;impact_y=yy
        old_x,old_y=cur+offset,yy;t+=d
    e.PX.put(end,cur);m.PY.put(end,0)
    x=spec['contact'][0]+cur+impact_offset;y=spec['contact'][1]+impact_y
    bx=x-spec['surface']+(36 if result=='miss' else 0);by=y-spec['body_y']
    for tr in (e.BX,e.BY,e.BR):m.pin(tr)
    e.BX.put(impact,bx);e.BY.put(impact,by);e.BR.put(impact,0)
    e.B.put(start,0)
    if result=='hit':
        e.B.put(impact,1);e.B.put(impact+160,0)
        e.BX.put(impact+65,bx+10);e.BX.put(end,bx+6)
        e.BR.put(impact+65,6);e.BR.put(end,0)
    elif result=='block':
        e.bot_guards.append((impact-65,impact+160));m.guard_arms(start+60)
        e.BX.put(end,bx+7)
    if kind=='knee':
        # The boxer controls the collar line while the folded knee enters the
        # chassis. The robot's arms engage the boxer's raised forearms.
        m.arm_at('near',start+65,(713,235));m.arm_at('far',start+65,(737,225))
    else:m.rest_arms(start+90)
    e.BY.put(end,by*.35);m.rest_arms(end)
    event(impact,end,'player',kind,result,damage,x,y)
    e.time=end

def leg_at(t,point):
    sx,sy=794,317;gx,gy=point;L1,L2=34,37
    dx,dy=gx-sx,gy-sy;d=min(math.hypot(dx,dy),L1+L2-.05)
    base=math.atan2(dy,dx);da=math.acos(max(-1,min(1,(L1*L1+d*d-L2*L2)/(2*L1*d))))
    aa=base-da;ex=sx+L1*math.cos(aa);ey=sy+L1*math.sin(aa)
    angles=[math.degrees(aa),math.degrees(math.atan2(gy-ey,gx-ex)-aa)]
    for tr,v in zip((LU,LL),angles):
        old=tr.at(t)
        while v-old>180:v-=360
        while v-old< -180:v+=360
        tr.put(t,v)

def robot_kick(result='block',damage=0):
    if result=='block' and e.PX.at(e.time)<-15:move(-1)
    start=e.time;cur=e.PX.at(start);impact=start+215;end=start+480
    check_offset=m.FOOT['base']['rear']['x']-SUPPORTS['0']['x'] if result=='block' else 0
    x=(735+cur+check_offset) if result=='block' else 741+cur
    y=338;bx=x-732
    e.P.put(start,0);e.P.put(start+100,40 if result=='block' else 1)
    e.P.put(impact+100,48 if result=='block' else 10);e.P.put(end-50,0)
    for tr in (e.PX,e.BX,e.BY,e.BR):m.pin(tr)
    e.BX.put(impact,bx);e.BY.put(impact,0);e.BR.put(impact,-3)
    e.BX.put(end,bx+15);e.BR.put(end,0)
    e.B.put(start+80,2);e.B.put(impact+140,0)
    leg_at(start,(803,333));leg_at(start+110,(777,347));leg_at(impact,(732,338));leg_at(end,(803,333))
    leg_windows.append((start+40,end))
    if result=='hit':
        e.PX.put(impact,cur);e.PX.put(impact+90,cur-5);e.PX.put(end,cur-3)
        e.PR.put(impact,0);e.PR.put(impact+60,-3);e.PR.put(impact+180,0)
    elif result=='block':
        rear=m.FOOT['base']['rear']
        for t,idx in ((start+100,0),(impact+100,8)):
            foot=SUPPORTS[str(idx)];offset=rear['x']-foot['x']
            e.PX.put(t-1,e.PX.at(t-1));e.PX.put(t,cur+offset)
            m.PY.put(t-1,m.PY.at(t-1));m.PY.put(t,rear['y']-foot['y'])
            support_checks.append(dict(t=t,foot_x=foot['x'],world=cur+rear['x']))
        e.PX.put(end-51,e.PX.at(end-51));e.PX.put(end-50,cur);e.PX.put(end,cur)
        m.PY.put(end-51,m.PY.at(end-51));m.PY.put(end-50,0);m.PY.put(end,0)
    event(impact,end,'robot','low kick',result,damage,x,y)
    e.time=end

def stand_up(cur):
    start=e.time
    frames(start,[61,62,53,0],[190,180,100,70])
    e.PX.put(start,cur);e.PX.put(start+540,cur);m.PY.put(start+540,0)
    e.PR.put(start,0)
    e.time=start+540

def robot_throw():
    start=e.time;cur=e.PX.at(start);impact=start+470
    ground_cur=max(-8,cur-13)
    frames(start,[49,53,61],[160,155,320])
    e.B.put(start,2);m.arm_at('near',start+100,(711,235));m.arm_at('far',start+100,(731,226))
    for tr in (e.PX,m.PY,e.PR,e.BX,e.BY,e.BR):m.pin(tr)
    e.BX.put(start+150,cur-10);e.BY.put(start+150,-15);e.BR.put(start+150,-8)
    e.PR.put(start+170,0);e.PR.put(start+295,-18);e.PR.put(start+315,0)
    e.PX.put(start+315,ground_cur);e.BR.put(impact,8);e.BY.put(impact,0)
    e.BX.put(start+635,cur+15);e.BR.put(start+635,0);e.B.put(start+635,0);m.rest_arms(start+635)
    event(impact,start+635,'robot','clinch throw','hit',10,672+cur,382)
    grapples.append(dict(kind='robot clinch trip',start=start,impact=impact,end=start+635))
    e.time=start+635;stand_up(ground_cur)

def sprawl():
    # Leave room for the long rear leg extension before the level change.
    # Reposition with the same planted-foot step, not a root teleport.
    for _ in range(3):
        if e.PX.at(e.time)>=-5:break
        if not m.step_once(1,295):break
    start=e.time;cur=e.PX.at(start);impact=start+300;end=start+720
    frames(start,[53,54,60,54,53,0],[90,80,230,130,100,90])
    e.B.put(start,2);m.rest_arms(start+80)
    for tr in (e.BX,e.BY,e.BR,e.PX):m.pin(tr)
    e.BX.put(impact,cur-55);e.BY.put(impact,90);e.BR.put(impact,-58)
    e.BX.put(end,cur+18);e.BY.put(end,0);e.BR.put(end,0);e.B.put(end,0)
    event(impact,end,'robot','takedown shot','block',0,777+cur,370)
    grapples.append(dict(kind='sprawl defence',start=start,impact=impact,end=end))
    e.time=end

def floor_alignment(px):
    # A point on the screen after a 87-degree fall: the ground punch and the
    # bot's tilted head share one actual world-space contact, not separate VFX.
    angle=math.radians(87);dx,dy=829-809,219-266
    head=(809+dx*math.cos(angle)-dy*math.sin(angle),266+dx*math.sin(angle)+dy*math.cos(angle))
    x,y=760+px,383
    return x-head[0],y-head[1],x,y

def takedown():
    start=e.time;cur=e.PX.at(start);impact=start+720;end=start+930
    frames(start,[53,54,55,56,57],[135,160,175,190,270])
    ground_px=cur+110;bx,by,x,y=floor_alignment(ground_px)
    for tr in (e.PX,e.BX,e.BY,e.BR,m.PY):m.pin(tr)
    e.PX.put(start+295,cur+12);e.PX.put(start+470,cur+24);e.PX.put(start+660,cur+65);e.PX.put(end,ground_px)
    e.BX.put(start+295,cur+7);e.BY.put(start+295,0);e.BR.put(start+295,0)
    e.BX.put(start+470,cur+18);e.BY.put(start+470,-22);e.BR.put(start+470,-15)
    e.BX.put(impact,bx);e.BY.put(impact,by);e.BR.put(impact,87)
    e.BX.put(end,bx);e.BY.put(end,by);e.BR.put(end,87)
    e.B.put(start,0);e.B.put(impact,1);e.B.put(end,0)
    m.guard_arms(start+180);m.rest_arms(start+600)
    event(impact,end,'player','double leg takedown','hit',7,x,y)
    grapples.append(dict(kind='player double leg',start=start,impact=impact,end=end))
    e.time=end

def ground_punch(damage):
    start=e.time;cur=e.PX.at(start);impact=start+95;end=start+285
    frames(start,[58,59,57],[95,105,85])
    bx,by,x,y=floor_alignment(cur)
    for tr in (e.BX,e.BY,e.BR):m.pin(tr)
    e.BX.put(impact,bx);e.BY.put(impact,by);e.BR.put(impact,87)
    e.B.put(impact,1);e.B.put(end,0)
    event(impact,end,'player','ground short punch','hit',damage,x,y)
    e.time=end

def scramble():
    start=e.time;old=e.PX.at(start);cur=max(-35,min(20,old-80));end=start+480
    e.P.put(start,57);e.P.put(start+170,61)
    e.PX.put(start,old);e.PX.put(start+350,cur)
    e.BR.put(start,87);e.BR.put(start+150,125);e.BR.put(end,0)
    e.BY.put(start+150,75);e.BY.put(end,0);e.BX.put(end,cur+35);e.B.put(end,0)
    e.time=end;stand_up(cur)
    grapples.append(dict(kind='robot roll escape and technical stand-up',start=start,impact=start+170,end=e.time))

def choreography():
    m.wait(400);m.wait(400,1);m.wait(400)
    phase('STRIKE & CHECK');move(-6)
    m.punch('jab','block');m.punch('cross','hit',4);strike('low kick','hit',5)
    m.robot('jab','block');m.robot('body','hit',10);robot_kick('block')
    m.punch('jab','hit',3);m.punch('cross','hit',4);strike('teep','block')
    m.robot('hook','hit',12);move(-43);strike('low kick','hit',4);m.robot('cross','block');m.robot('upper','miss');strike('knee','hit',5)
    phase('CLINCH & SCRAMBLE')
    strike('knee','hit',4);m.robot('body','hit',8);strike('knee','block');robot_throw()
    m.robot('hook','block');m.robot('overhand','hit',13);strike('teep','hit',5);robot_kick('hit',8);strike('low kick','hit',4)
    phase('WRESTLE FOR POSITION')
    sprawl();m.punch('upper','hit',4);strike('low kick','hit',4);m.robot('jab','block');m.robot('body','hit',13)
    move(-8);takedown();ground_punch(2);ground_punch(3);scramble()
    m.robot('cross','block');m.robot('hook','miss');m.punch('jab','hit',3);m.punch('cross','hit',4)
    phase('FIGHT THROUGH PRESSURE')
    m.robot('upper','hit',14);m.robot('jab','block');robot_kick('block');move(-7)
    strike('low kick','hit',4);strike('teep','hit',4);m.robot('cross','block');m.robot('hook','miss')
    strike('knee','hit',5);m.punch('jab','block');m.robot('body','block')
    phase('FINISH THE EXCHANGE')
    m.robot('overhand','miss');move(10);m.punch('cross','hit',5);strike('knee','hit',5)
    m.robot('jab','miss');m.punch('hook','hit',4);m.punch('upper','hit',8,finisher=True)
    e.P.put(e.time,22);e.time+=380;e.P.put(e.time,23);e.time+=2400
    e.P.put(e.time+300,0);e.B.put(e.time+300,0)
    for tr,val in ((e.PX,-24),(m.PY,0),(e.BX,35),(e.BY,0),(e.BR,0),(e.PR,0),(e.LIGHT,1),(e.P_HP,100),(e.B_HP,100)):
        tr.put(e.time+299,tr.at(e.time+299,tr in (e.P_HP,e.B_HP)));tr.put(e.time+300,val)
    m.rest_arms(e.time+300);e.time+=800;e.T=e.time

def validate():
    assert sum(n['damage'] for n in e.events if n['actor']=='player')==100
    assert sum(n['damage'] for n in e.events if n['actor']=='robot')==88
    assert e.P_HP.at(e.final_hit,True)==12 and e.B_HP.at(e.final_hit,True)==0
    assert all(n['damage']==0 for n in e.events if n['result']!='hit')
    assert all(n['t']<=e.final_hit for n in e.events)
    assert any(n['kind']=='knee' for n in e.events)
    assert any(n['kind']=='double leg takedown' for n in e.events)
    assert len(grapples)>=4
    assert all(err<.01 for err in m.foot_checks)
    assert all(abs(e.PX.at(c['t'],True)+c['foot_x']-c['world'])<.01 for c in support_checks)
    print(f'PASS: {len(e.events)} exchanges, {len(grapples)} wrestling/recovery passages, 12% HP win; {e.T/1000:.2f}s.')

def make_leg(parent):
    g=e.el(parent,'g',{'class':'v11leg','transform':'translate(794 317)'})
    upper=e.el(g,'g',{'class':'v11legupper'})
    e.el(upper,'path',{'d':'M0-6h34v12H0z','fill':'#68779a','stroke':'#11172b','stroke-width':2})
    e.el(upper,'rect',{'x':5,'y':-4,'width':23,'height':3,'fill':'#d0def0'})
    joint=e.el(upper,'g',{'transform':'translate(34 0)'})
    e.el(joint,'rect',{'x':-6,'y':-6,'width':12,'height':12,'fill':'#c0cee5','stroke':'#11172b','stroke-width':2})
    shin=e.el(joint,'g',{'class':'v11leglower'})
    e.el(shin,'path',{'d':'M0-5h33v-3h8v16h-8V5H0z','fill':'#a6b7d1','stroke':'#11172b','stroke-width':2})
    e.el(shin,'path',{'d':'M31-6h13v17H30V4h-3v-7h4z','fill':'#e0e9f9','stroke':'#11172b','stroke-width':2})
    e.el(shin,'rect',{'x':34,'y':-3,'width':5,'height':8,'fill':'#ff6398'})
    e.animation('v11legupper',LU,lambda v:f'transform:rotate({e.fmt(v)}deg)')
    e.animation('v11leglower',LL,lambda v:f'transform:rotate({e.fmt(v)}deg)')
    e.windows('v11leg',leg_windows)

def build():
    m.choreography=choreography;m.validate=validate
    with tempfile.TemporaryDirectory(prefix='fight-v11-') as tmp:
        stage=Path(tmp);(stage/'assets').mkdir();shutil.copy2(ROOT/'assets'/'fight-hero-v8.svg',stage/'assets'/'fight-hero-v8.svg')
        shutil.copytree(ROOT/'assets'/'fighter-v10',stage/'assets'/'fighter-v10')
        m.ROOT=stage;m.build()
        root=ET.parse(stage/'assets'/'fight-hero-v10.svg').getroot()
    player=next(n for n in root.iter() if n.get('class')=='v9react')
    for i in range(24):
        data=base64.b64encode((ART/f'mma-{i:02}.png').read_bytes()).decode()
        e.el(player,'image',{'class':'v9p'+str(40+i),'href':'data:image/png;base64,'+data,'x':541,'y':145,'width':320,'height':280,'preserveAspectRatio':'xMidYMid meet','style':'image-rendering:pixelated'})
        e.visibility('v9p'+str(40+i),e.P,40+i)
    bot=next(n for n in root.iter() if n.get('class')=='v9bot');make_leg(bot)
    # Dense combinations need short, non-overlapping cues: a previous DODGE
    # must disappear before the following knee / counter is labelled.
    cues=[]
    for anim in e.ANIMS:
        name=anim[0]
        if name.startswith('v9cue'):
            i=int(name[5:]);t=e.events[i]['t']
            end=min(t+310,e.events[i+1]['t']-20) if i+1<len(e.events) else t+310
            cues.append((name,t,end))
    names={c[0] for c in cues};e.ANIMS=[a for a in e.ANIMS if a[0] not in names]
    for name,t,end in cues:e.windows(name,[(t,max(t+60,end))])
    # Do not embed frames which this bout never shows. Every required image is
    # still kept as an editable source PNG beside the complete sprite sheet.
    used={int(n) for n in e.P.keys.values()}
    for node in list(player):
        c=node.get('class','')
        if node.tag.endswith('image') and c.startswith('v9p') and int(c[3:]) not in used:player.remove(node)
    root.find('{'+NS+'}style').text=e.timeline_css()
    root.set('aria-label','张健航 · AI 产品经理：密集拳腿、顶膝、抱摔、地面控制与起身反击，最终获胜')
    out=ROOT/'assets'/'fight-hero-v11.svg';out.write_text(ET.tostring(root,encoding='unicode'))
    review=ROOT/'verification'/'v11';review.mkdir(parents=True,exist_ok=True)
    picks={}
    for kind in ('low kick','teep','knee','clinch throw','takedown shot','double leg takedown','ground short punch'):
        actor='robot' if kind in ('clinch throw','takedown shot') else 'player'
        found=next(n for n in e.events if n['kind']==kind and n['actor']==actor)
        picks[kind.replace(' ','-')]=found['t']+35
    for g in grapples:
        if 'double leg' in g['kind']:
            picks['wrestle-entry']=g['start']+200;picks['wrestle-lift']=g['start']+395;picks['top-control']=g['end']+15
    picks['stand-up']=next(g['end'] for g in grapples if g['kind']=='robot clinch trip')+220
    picks['shin-check']=next(n['t'] for n in e.events if n['actor']=='robot' and n['kind']=='low kick' and n['result']=='block')+25
    picks['win']=e.final_hit+1600
    for name,ms in picks.items():
        frozen=deepcopy(root);frozen.find('{'+NS+'}style').text=e.timeline_css(ms)
        for parent in frozen.iter():
            for n in list(parent):
                c=n.get('class','')
                if n.tag.endswith('image') and ((c.startswith('v9p') and c!='v9p'+str(e.P.at(ms,True))) or (c.startswith('v9b') and c!='v9b'+str(e.B.at(ms,True)))):parent.remove(n)
        (review/(name+'.svg')).write_text(ET.tostring(frozen,encoding='unicode'))
    data=dict(duration_ms=e.T,final_hit_ms=e.final_hit,health_at_win=12,events=e.events,grapples=grapples,steps=m.steps,previews=picks)
    (ART/'bout.json').write_text(json.dumps(data,indent=2))
    print('Built',out.name,round(out.stat().st_size/1024),'KiB;',picks)

if __name__=='__main__':build()
