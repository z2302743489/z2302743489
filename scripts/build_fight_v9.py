"""A complete two-way fight using the existing 24 authored fighter poses.

Run: python3 scripts/build_fight_v9.py
No dependencies. The SVG uses CSS only, with all sprite bitmaps embedded.
The timeline, collisions, damage, previews and CSS share one choreography.
"""
from pathlib import Path
from copy import deepcopy
from bisect import bisect_right
import xml.etree.ElementTree as ET
import math
import json

ROOT=Path(__file__).resolve().parents[1]
NS='http://www.w3.org/2000/svg'
ET.register_namespace('',NS)
MONO="'SF Mono',Menlo,Consolas,monospace"
CN="'PingFang SC','Hiragino Sans GB','Microsoft YaHei',sans-serif"
CYAN='#6ee7ed'; GOLD='#ffd65c'; RED='#ff6a86'

def el(parent,tag,attrs=None,text=None):
    node=ET.SubElement(parent,'{'+NS+'}'+tag,{k:str(v) for k,v in (attrs or {}).items()})
    node.text=text
    return node

def fmt(v): return f'{v:.3f}'.rstrip('0').rstrip('.') or '0'

class Track:
    def __init__(self,initial): self.keys={0:initial}
    def put(self,t,v): self.keys[round(t)]=v
    def at(self,t,step=False):
        ts=sorted(self.keys);i=max(0,bisect_right(ts,t)-1);a=ts[i]
        if step or i==len(ts)-1:return self.keys[a]
        b=ts[i+1];u=(t-a)/(b-a)
        return self.keys[a]+(self.keys[b]-self.keys[a])*u

P=Track(0); B=Track(0)
PX=Track(-24); BX=Track(35); BY=Track(0); BR=Track(0)
PR=Track(0); LIGHT=Track(1); CAMERA_X=Track(0); CAMERA_Y=Track(0)
P_HP=Track(100); B_HP=Track(100)
events=[];phases=[];guards=[];bot_guards=[];time=0;final_hit=None

def pose(p): P.put(time,p)
def bot_state(state): B.put(time,state) # idle / hit / punch / ko
def pin(track): track.put(time,track.at(time))

def hold(ms,p=0,px=None,bx=None,by=0,phase=None):
    global time
    pose(p);bot_state(0)
    if phase: phases.append((time,phase))
    for tr,v in ((PX,px),(BX,bx),(BY,by),(BR,0)):
        pin(tr)
        if v is not None:tr.put(time+ms,v)
    time+=ms

# Fist centres measured from the authored PNGs. These are never scaled or
# stretched; only the fighter's entire body moves in world space.
ATTACKS={
 'jab':dict(poses=[2,3,4,5,0],dur=[100,90,105,85,130],hand=(786,214),reach=797),
 'cross':dict(poses=[6,7,8,9,0],dur=[110,100,115,95,140],hand=(793,210),reach=805),
 'hook':dict(poses=[14,15,16,17,0],dur=[120,105,130,100,145],hand=(749,230),reach=763),
 'upper':dict(poses=[18,19,20,21,0],dur=[180,110,160,120,170],hand=(727,190),reach=741),
}

def player_attack(kind,result='hit',damage=0,px=-12,finisher=False):
    global time,final_hit
    start=time;spec=ATTACKS[kind];ds=spec['dur'];impact=start+ds[0]+ds[1];end=start+sum(ds)
    # Bring the striking fist to the left edge of the bot's head. A miss has a
    # real gap; a guarded hit has contact but inflicts no HP damage.
    target_bx=spec['reach']+px-762
    if result=='miss':target_bx+=42
    pin(PX);pin(BX);pin(BY);pin(BR)
    PX.put(start+ds[0],(PX.at(start)+px)/2);PX.put(impact,px);PX.put(end,px-3)
    BX.put(impact,target_bx);BY.put(impact,0);BR.put(impact,0)
    bot_state(0)
    t=start
    for p,d in zip(spec['poses'],ds):P.put(t,p);t+=d
    hx,hy=spec['hand'];hx+=px+8
    event=dict(t=impact,end=end,actor='player',kind=kind,result=result,damage=damage,
               x=hx,y=hy,px=px,bx=target_bx,high=True,finisher=finisher)
    events.append(event)
    if result=='hit':
        B.put(impact,3 if finisher else 1)
        B_HP.put(impact,max(0,B_HP.at(impact,True)-damage))
        if finisher:
            final_hit=impact
            BX.put(impact+140,target_bx+30);BY.put(impact+140,-34);BR.put(impact+140,24)
            BX.put(impact+620,35);BY.put(impact+620,99);BR.put(impact+620,87)
        else:
            BX.put(impact+85,target_bx+13);BR.put(impact+85,5 if kind!='upper' else -8)
            BY.put(impact+85,-10 if kind=='upper' else 0)
            BX.put(end,target_bx+6);BY.put(end,0);BR.put(end,0);B.put(impact+230,0)
    elif result=='block':
        bot_guards.append((impact-110,impact+260))
        BX.put(impact+75,target_bx+4);BX.put(end,target_bx+10)
    else:
        BX.put(end,target_bx+4)
    if result=='hit':
        strength=5 if finisher else 1.5
        for dt,mul in [(0,0),(35,1),(70,-.7),(110,.4),(155,0)]:
            CAMERA_X.put(impact+dt,strength*mul);CAMERA_Y.put(impact+dt,-strength*mul*.45)
    time=end

def robot_attack(result='block',high=True,px=-24,damage=0):
    global time
    start=time;impact=start+260;end=start+690
    prev_px=PX.at(start)
    target_y=-42 if high else -12
    if result=='miss':
        # Aim where the head was. The player both retreats and gets BELOW the
        # punch, rather than the fist phasing through the player's head.
        target_bx=21+prev_px
        pseq=[(0,10),(130,11),(210,12),(390,13),(530,0)]
    elif result=='block':
        target_bx=21+px
        pseq=[(0,0),(130,11),(430,13),(560,0)]
        guards.append((impact-70,impact+210))
    else:
        target_bx=-11+px
        pseq=[(0,0),(260,1),(390,10),(540,0)]
    for dt,p in pseq:P.put(start+dt,p)
    for tr in (PX,BX,BY,BR,PR,LIGHT):pin(tr)
    PX.put(impact,px)
    BX.put(start+130,BX.at(start)+9);BY.put(start+130,target_y*.5);BR.put(start+130,4)
    BX.put(impact,target_bx);BY.put(impact,target_y);BR.put(impact,0)
    B.put(start,0);B.put(start+190,2);B.put(impact+160,0)
    BX.put(impact+180,target_bx+4);BX.put(end,target_bx+23)
    BY.put(impact+180,target_y);BY.put(end,0);BR.put(end,0)
    x=701+target_bx;y=274+target_y
    events.append(dict(t=impact,end=end,actor='robot',kind='high jab' if high else 'body cross',
                       result=result,damage=damage,x=x,y=y,px=px,bx=target_bx,high=high,finisher=False))
    if result=='hit':
        P_HP.put(impact,max(0,P_HP.at(impact,True)-damage))
        PX.put(impact+90,px-10);PX.put(end,px-7)
        PR.put(impact,0);PR.put(impact+70,-3);PR.put(impact+210,0)
        LIGHT.put(impact-1,1);LIGHT.put(impact,1.45);LIGHT.put(impact+140,1)
        for dt,v in [(0,0),(35,-1.5),(75,1),(140,0)]:CAMERA_X.put(impact+dt,v)
    elif result=='block':
        PX.put(impact+75,px-4);PX.put(end,px-3)
    else:PX.put(end,px+5)
    time=end

def choreograph():
    global time
    hold(400,0);hold(400,1);hold(400,0)
    hold(320,0,px=-18,bx=28,phase='READ & REACT')
    player_attack('jab','block',px=-18)
    player_attack('jab','hit',7,px=-15)
    robot_attack('block',px=-22)
    robot_attack('hit',False,px=-28,damage=12)
    hold(230,0,px=-28,bx=30)
    hold(220,1,px=-30,bx=35,phase='UNDER PRESSURE')
    robot_attack('miss',px=-43)
    robot_attack('block',px=-35)
    robot_attack('hit',False,px=-36,damage=12)
    hold(230,0,px=-24,bx=16)
    player_attack('cross','hit',8,px=-12)
    player_attack('jab','hit',6,px=-14)
    player_attack('cross','block',px=-12)
    hold(300,0,px=-28,bx=42)
    hold(180,1,phase='TRADE & COUNTER')
    robot_attack('miss',px=-43)
    player_attack('hook','hit',10,px=12)
    robot_attack('hit',False,px=-1,damage=12)
    player_attack('upper','hit',10,px=28)
    hold(300,0,px=-8,bx=40)
    player_attack('jab','miss',px=-10)
    robot_attack('block',px=-12)
    hold(220,0,px=-22,bx=30)
    hold(200,1,phase='FIND THE OPENING')
    robot_attack('block',px=-26)
    robot_attack('miss',px=-43)
    player_attack('cross','hit',9,px=-12)
    player_attack('hook','hit',9,px=18)
    robot_attack('miss',px=-10)
    player_attack('jab','hit',7,px=-5)
    hold(450,18,px=10,bx=18,phase='COUNTER WINDOW')
    player_attack('cross','hit',9,px=0)
    player_attack('hook','hit',10,px=28)
    player_attack('upper','hit',15,px=40,finisher=True)
    # Allow the defeated robot to finish falling before the victory salute.
    P.put(time,22);time+=220
    P.put(time,23);time+=2600
    # Reset all tracks under a brief dark arena transition for a clean loop.
    P.put(time+300,0);B.put(time+300,0)
    for tr,v in ((PX,-24),(BX,35),(BY,0),(BR,0),(PR,0),(LIGHT,1),(P_HP,100),(B_HP,100)):
        tr.put(time+299,tr.at(time+299, tr in (P_HP,B_HP)))
        tr.put(time+300,v)
    time+=800
    return time

T=choreograph()
ANIMS=[]

def animation(cls,keys,render=lambda v:f'opacity:{fmt(v)}',step=False):
    if isinstance(keys,Track):keys=keys.keys
    keys=dict(keys)
    # The last key of an interpolated track must HOLD its previous value to
    # the loop boundary; otherwise CSS interpolates back across the victory.
    keys.setdefault(T,keys[max(keys)])
    ANIMS.append((cls,keys,render,step))

def windows(cls,intervals):
    keys={0:0,T:0}
    for a,b in intervals:keys[a]=1;keys[b]=0
    animation(cls,keys,step=True)

def visibility(cls,tr,value):
    animation(cls,{t:int(v==value) for t,v in tr.keys.items()},step=True)

def transform_track(cls,tracks,render,step=False):
    ts=set().union(*(tr.keys for tr in tracks))
    keys={t:tuple(tr.at(t,step) for tr in tracks) for t in ts}
    animation(cls,keys,render,step)

def timeline_css(freeze=None):
    result=[]
    for cls,keys,render,step in ANIMS:
        if freeze is not None:
            ts=sorted(keys);i=max(0,bisect_right(ts,freeze)-1);v=keys[ts[i]]
            if not step and i<len(ts)-1:
                a,b=ts[i],ts[i+1];u=(freeze-a)/(b-a)
                if isinstance(v,tuple):v=tuple(x+(y-x)*u for x,y in zip(v,keys[b]))
                else:v=v+(keys[b]-v)*u
            result.append('.'+cls+'{'+render(v)+'}')
        else:
            frames=''.join(fmt(t/T*100)+'%{'+render(v)+'}' for t,v in sorted(keys.items()))
            result.append('@keyframes '+cls+'{'+frames+'}.'+cls+'{animation:'+cls+' '+str(T)+'ms '+('step-end' if step else 'linear')+' infinite}')
    return ''.join(result)

GLYPHS={
'A':['01110','10001','10001','11111','10001','10001','10001'],
'B':['11110','10001','10001','11110','10001','10001','11110'],
'C':['01111','10000','10000','10000','10000','10000','01111'],
'D':['11110','10001','10001','10001','10001','10001','11110'],
'E':['11111','10000','10000','11110','10000','10000','11111'],
'F':['11111','10000','10000','11110','10000','10000','10000'],
'G':['01111','10000','10000','10111','10001','10001','01110'],
'H':['10001','10001','10001','11111','10001','10001','10001'],
'I':['11111','00100','00100','00100','00100','00100','11111'],
'J':['00111','00010','00010','00010','10010','10010','01100'],
'K':['10001','10010','10100','11000','10100','10010','10001'],
'L':['10000','10000','10000','10000','10000','10000','11111'],
'M':['10001','11011','10101','10101','10001','10001','10001'],
'N':['10001','11001','10101','10011','10001','10001','10001'],
'O':['01110','10001','10001','10001','10001','10001','01110'],
'P':['11110','10001','10001','11110','10000','10000','10000'],
'Q':['01110','10001','10001','10001','10101','10010','01101'],
'R':['11110','10001','10001','11110','10100','10010','10001'],
'S':['01111','10000','10000','01110','00001','00001','11110'],
'T':['11111','00100','00100','00100','00100','00100','00100'],
'U':['10001','10001','10001','10001','10001','10001','01110'],
'V':['10001','10001','10001','10001','10001','01010','00100'],
'W':['10001','10001','10001','10101','10101','11011','10001'],
'X':['10001','10001','01010','00100','01010','10001','10001'],
'Y':['10001','10001','01010','00100','00100','00100','00100'],
'Z':['11111','00001','00010','00100','01000','10000','11111'],
'0':['01110','10011','10101','10101','11001','10001','01110'],
'1':['00100','01100','00100','00100','00100','00100','01110'],
'2':['01110','10001','00001','00010','00100','01000','11111'],
'3':['11110','00001','00001','01110','00001','00001','11110'],
'4':['00010','00110','01010','10010','11111','00010','00010'],
'5':['11111','10000','10000','11110','00001','00001','11110'],
'!':['00100','00100','00100','00100','00100','00000','00100'],
'.':['00000','00000','00000','00000','00000','01100','01100'],
' ':['000']*7,
}

def pixel_text(parent,text,x,y,size,color=GOLD,cls=None,anchor='middle'):
    width=sum((len(GLYPHS[c][0])+1)*size for c in text)-size
    xx=x-width/2 if anchor=='middle' else x-width if anchor=='end' else x
    path=[]
    for c in text:
        for row,bits in enumerate(GLYPHS[c]):
            for col,bit in enumerate(bits):
                if bit=='1':path.append(f'M{fmt(xx+col*size)} {fmt(y+row*size)}h{fmt(size)}v{fmt(size)}h-{fmt(size)}z')
        xx+=(len(GLYPHS[c][0])+1)*size
    g=el(parent,'g',{'class':cls} if cls else {})
    el(g,'path',{'d':''.join(path),'fill':color,'stroke':'#0b0f1e','stroke-width':max(.5,size*.35),'paint-order':'stroke'})
    return g

def validate():
    assert sum(e['damage'] for e in events if e['actor']=='player')==100
    assert sum(e['damage'] for e in events if e['actor']=='robot')==36
    assert P_HP.at(final_hit,True)==64 and B_HP.at(final_hit,True)==0
    assert all(e['damage']==0 for e in events if e['result']!='hit')
    assert all(e['t']<=final_hit for e in events)
    for e in events:
        if e['actor']=='player':
            tip=ATTACKS[e['kind']]['reach']+e['px']
            edge=762+e['bx']
            assert (abs(tip-edge)<.01 if e['result']!='miss' else edge-tip>=40),e
        else:
            assert abs((701+e['bx'])-e['x'])<.01
            if e['result']=='block':assert e['high']
            if e['result']=='miss':assert P.at(e['t'],True)==12
        assert -50<=e['px']<=45 and -55<=e['bx']<=80,e
    print(f'PASS: {len(events)} attacks, 11 player hits / 3 robot hits, guarded hits do no damage; 64% HP victory; {T/1000:.2f}s loop.')

def build():
    validate()
    source=ET.parse(ROOT/'assets/fight-hero-v8.svg').getroot()
    root=deepcopy(source)
    style=root.find('{'+NS+'}style');style.text=''
    old_scene=next(n for n in root if n.get('clip-path')=='url(#clip)')
    old_shake=next(n for n in old_scene if n.get('class')=='shake')
    images={e.get('class'):deepcopy(e) for e in source.iter('{'+NS+'}image')}
    scene=ET.Element('{'+NS+'}g',{'clip-path':'url(#clip)','id':'fight-v9'})
    el(scene,'rect',{'x':548,'y':58,'width':436,'height':368,'fill':'url(#arena)'})
    camera=el(scene,'g',{'class':'v9camera'})
    for node in list(old_shake)[:15]:camera.append(deepcopy(node))
    # Shadows follow horizontal motion, not the sprite's hover or hit rotation.
    pshadow=el(camera,'g',{'class':'v9pshadow'})
    el(pshadow,'ellipse',{'cx':680,'cy':411,'rx':61,'ry':7,'fill':'#05070f','opacity':.38})
    bshadow=el(camera,'g',{'class':'v9bshadow'})
    el(bshadow,'ellipse',{'cx':809,'cy':407,'rx':47,'ry':7,'fill':'#05070f','opacity':.4})
    bg=el(camera,'g',{'class':'v9bot','style':'transform-origin:809px 266px'})
    for state,old in enumerate(('idle','hit','punch','ko')):
        node=deepcopy(images['b_'+old]);node.set('class','v9b'+str(state));bg.append(node)
        visibility('v9b'+str(state),B,state)
    shield=el(bg,'g',{'class':'v9botguard','fill':'none','stroke':CYAN,'stroke-width':3})
    # Pixel-edged forearm energy guard at the front of the display, not over it.
    el(shield,'path',{'d':'M760 199h-8v10h-5v31h5v10h8','stroke-linecap':'square'})
    el(shield,'path',{'d':'M741 210h-4v29h4','opacity':.4,'stroke-width':2})
    pg=el(camera,'g',{'class':'v9player'})
    react=el(pg,'g',{'class':'v9react','style':'transform-origin:690px 273px'})
    for i in range(24):
        node=deepcopy(images['v7p'+str(i)]);node.set('class','v9p'+str(i));react.append(node)
        visibility('v9p'+str(i),P,i)

    transform_track('v9player',[PX],lambda v:f'transform:translateX({fmt(v[0])}px)')
    transform_track('v9pshadow',[PX],lambda v:f'transform:translateX({fmt(v[0])}px)')
    transform_track('v9bshadow',[BX],lambda v:f'transform:translateX({fmt(v[0])}px)')
    transform_track('v9bot',[BX,BY,BR],lambda v:f'transform:translate({fmt(v[0])}px,{fmt(v[1])}px) rotate({fmt(v[2])}deg)')
    transform_track('v9react',[PR,LIGHT],lambda v:f'transform:rotate({fmt(v[0])}deg);filter:brightness({fmt(v[1])})')
    transform_track('v9camera',[CAMERA_X,CAMERA_Y],lambda v:f'transform:translate({fmt(v[0])}px,{fmt(v[1])}px)')
    windows('v9botguard',bot_guards)

    # Every impact gets a short readable cue; no damage flash on blocks/misses.
    for i,e in enumerate(events):
        t=e['t'];x=e['x'];y=e['y'];hit=e['result']=='hit';blocked=e['result']=='block'
        cls=f'v9impact{i}'
        fx=el(camera,'g',{'class':cls})
        if e['result']!='miss':
            size=26 if e['finisher'] else 17 if hit else 13
            col=GOLD if hit else CYAN
            for j in range(8):
                angle=j*math.pi/4;inner=4;outer=size if j%2==0 else size*.7
                x1=x+math.cos(angle)*inner;y1=y+math.sin(angle)*inner
                x2=x+math.cos(angle)*outer;y2=y+math.sin(angle)*outer
                el(fx,'path',{'d':f'M{fmt(x1)} {fmt(y1)}L{fmt(x2)} {fmt(y2)}','stroke':col,'stroke-width':3,'fill':'none'})
            el(fx,'rect',{'x':x-3,'y':y-3,'width':6,'height':6,'fill':'#f7fdff'})
            if blocked:
                el(fx,'path',{'d':f'M{x-9} {y-20}h15l8 8v25l-14 10-14-10v-25z','fill':'#4cd9e7','fill-opacity':.1,'stroke':CYAN,'stroke-width':2})
            windows(cls,[(t,t+(190 if e['finisher'] else 105))])
        else:windows(cls,[])
        text=None
        if blocked:text='BLOCK'
        elif e['result']=='miss':text='DODGE' if e['actor']=='robot' else 'MISS'
        elif e['actor']=='player' and i>0 and events[i-1]['actor']=='robot':text='COUNTER'
        if text:
            tx=min(914,max(626,x));ty=159 if not e['finisher'] else 153
            c=f'v9cue{i}';pixel_text(scene,text,tx,ty,1.9,CYAN if e['result']!='hit' else GOLD,c)
            windows(c,[(t,t+400)])
        if hit:
            # Two tiny token chips reinforce the AI opponent without drowning
            # out the character or the physical contact point.
            for j in range(2):
                name=f'v9token{i}_{j}'
                el(camera,'text',{'class':name,'x':x,'y':y-5,'font-family':MONO,'font-size':10,'font-weight':700,'fill':CYAN if j else RED},'01'[j])
                animation(name,{0:(0,0,0),t-1:(0,0,0),t:(1,0,0),t+320:(0,22 if j else -18,-35),T:(0,0,0)},
                          lambda v:f'opacity:{fmt(v[0])};transform:translate({fmt(v[1])}px,{fmt(v[2])}px)')

    # Restrained charge effect and a short cyan shock ring on the final punch.
    charge_start=phases[-1][0]
    glow=el(camera,'g',{'class':'v9charge'})
    el(glow,'circle',{'cx':681,'cy':291,'r':23,'fill':'url(#aiglow)'})
    el(glow,'path',{'d':'M661 277h-5v12m43-12h6v12m-44 19h-5v-10m43 10h6v-10','stroke':CYAN,'stroke-width':2,'fill':'none'})
    windows('v9charge',[(charge_start,charge_start+450)])
    final_event=events[-1];fx=el(camera,'g',{'class':'v9ring','style':f'transform-origin:{final_event["x"]}px {final_event["y"]}px'})
    el(fx,'circle',{'cx':final_event['x'],'cy':final_event['y'],'r':65,'fill':'none','stroke':CYAN,'stroke-width':4})
    animation('v9ring',{0:(0,.1),final_hit-1:(0,.1),final_hit:(.9,.1),final_hit+400:(0,1),T:(0,1)},lambda v:f'opacity:{fmt(v[0])};transform:scale({fmt(v[1])})')

    # Reuse the original HUD geometry, now with TWO health bars responding to
    # actual landed hits. Blocked or dodged attacks leave HP unchanged.
    old_hud=next(n for n in old_scene if n.tag.endswith('g') and n.get('font-family'))
    hud=deepcopy(old_hud)
    for node in hud:
        if node.get('class')=='hp':node.set('class','v9bhp')
        elif node.get('class')=='trail':node.set('class','v9btrail')
        elif node.tag.endswith('rect') and node.get('fill')=='#ffd447':node.set('class','v9php')
        elif node.tag.endswith('rect') and node.get('fill')=='#fff1a8':node.set('class','v9php')
    scene.append(hud)
    animation('v9php',P_HP,lambda v:f'transform:scaleX({fmt(v/100)});transform-origin:563px 0',step=True)
    animation('v9bhp',B_HP,lambda v:f'transform:scaleX({fmt(v/100)});transform-origin:970px 0',step=True)
    trail={0:100,T:100}
    for t,hp in B_HP.keys.items():
        if t:trail[max(0,t-1)]=B_HP.at(t-1,True);trail[t+240 if t+240<T else T]=hp
    animation('v9btrail',trail,lambda v:f'transform:scaleX({fmt(v/100)});transform-origin:970px 0')
    for i,(t,label) in enumerate(phases):
        end=phases[i+1][0] if i+1<len(phases) else final_hit
        c=f'v9phase{i}'
        el(scene,'text',{'class':c,'x':766,'y':132,'text-anchor':'middle','font-family':MONO,'font-size':10,'letter-spacing':1.3,'fill':'#9aaed2'},label)
        windows(c,[(t,end)])

    # A combo only counts uninterrupted successful player strikes; it resets
    # on a block, dodge, or robot attack instead of counting across the bout.
    combo=0
    for i,e in enumerate(events):
        if e['actor']=='player' and e['result']=='hit':combo+=1
        else:combo=0
        if combo>=2:
            c=f'v9combo{i}';pixel_text(scene,f'{combo} HIT',563,400,2.1,CYAN,c,'start')
            end=events[i+1]['t'] if i+1<len(events) else time-500
            windows(c,[(e['t'],end)])

    pixel_text(scene,'ROUND 1',766,192,4.5,'#e6e9f2','v9round')
    pixel_text(scene,'FIGHT!',766,192,6,GOLD,'v9fight')
    pixel_text(scene,'K.O.',871,168,6.5,GOLD,'v9ko')
    pixel_text(scene,'YOU WIN',718,144,3.4,CYAN,'v9win')
    windows('v9round',[(0,600)]);windows('v9fight',[(600,1200)])
    windows('v9ko',[(final_hit+300,final_hit+500),(final_hit+620,final_hit+850),(final_hit+960,time-500)])
    windows('v9win',[(final_hit+1050,time-500)])
    # Brief arena-only transition hides the reset without disturbing the text.
    el(scene,'rect',{'class':'v9reset','x':548,'y':58,'width':436,'height':368,'fill':'#0d1226'})
    animation('v9reset',{0:0,time-800:0,time-501:1,time-400:1,time:0})
    index=list(root).index(old_scene);root.remove(old_scene);root.insert(index,scene)
    style.text=timeline_css()
    root.set('aria-label','张健航 · AI 产品经理：双方攻防、闪躲反击，最终击倒 AI 幻觉机器人')
    output=ROOT/'assets'/'fight-hero-v9.svg'
    output.write_text(ET.tostring(root,encoding='unicode'))
    # Self-contained static previews use the SAME animation tracks, sampled
    # directly. They make block, dodge and impact spacing reviewable in UI.
    review=ROOT/'verification'/'v9';review.mkdir(parents=True,exist_ok=True)
    picks={
        'botguard':events[0]['t']+35,
        'probe':events[1]['t']+20,
        'guard':next(e['t'] for e in events if e['actor']=='robot' and e['result']=='block')+35,
        'hurt':next(e['t'] for e in events if e['actor']=='robot' and e['result']=='hit')+60,
        'dodge':next(e['t'] for e in events if e['actor']=='robot' and e['result']=='miss')+20,
        'counter':next(e['t'] for i,e in enumerate(events) if e['actor']=='player' and e['kind']=='hook')+35,
        'finish':final_hit+50,
        'win':final_hit+1700,
    }
    for name,ms in picks.items():
        frozen=deepcopy(root);frozen.find('{'+NS+'}style').text=timeline_css(ms)
        # Keep only the visible character / robot frame in static snapshots.
        for parent in frozen.iter():
            for child in list(parent):
                c=child.get('class','')
                if child.tag.endswith('image') and ((c.startswith('v9p') and c!='v9p'+str(P.at(ms,True))) or (c.startswith('v9b') and c!='v9b'+str(B.at(ms,True)))):
                    parent.remove(child)
        (review/(name+'.svg')).write_text(ET.tostring(frozen,encoding='unicode'))
    (review/'timeline.json').write_text(json.dumps(dict(duration_ms=T,final_hit_ms=final_hit,events=events,phases=phases,previews=picks),indent=2))
    print(f'Built {output.name}: {output.stat().st_size/1024:.0f} KiB. Preview moments: {picks}')

if __name__=='__main__':build()
