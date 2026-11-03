"""Finish the existing MMA bout with high kick -> German suplex -> tap-out.

Run: python3 scripts/build_finish_v12.py (standard library only).
The finisher uses complete paired sprites so grips stay coupled throughout
the backward arch, grounded back-control and safe release after submission.
"""
from pathlib import Path
from copy import deepcopy
import importlib.util
import xml.etree.ElementTree as ET
import tempfile
import shutil
import base64
import json

ROOT=Path(__file__).resolve().parents[1]
ART=ROOT/'assets'/'fighter-v12'
NS='http://www.w3.org/2000/svg'
spec=importlib.util.spec_from_file_location('submission_engine',Path(__file__).with_name('build_fight_v11.py'))
n=importlib.util.module_from_spec(spec);spec.loader.exec_module(n)
m=n.m;e=n.e
PAIR=[];MOMENTS={};PAIR_START=None;PAIR_END=None;FIRST_PAIR_EVENT=None
original_choreography=n.choreography
original_phase=n.phase

class FinishReached(Exception):pass

def stop_at_old_finish(label):
    if label=='FINISH THE EXCHANGE':raise FinishReached()
    original_phase(label)

def choreography():
    global PAIR_START,PAIR_END,FIRST_PAIR_EVENT
    # Preserve the dense standing exchanges, kicks, knees and two-way ground
    # passages. Only the previous final boxing knockout is replaced.
    n.phase=stop_at_old_finish
    try:original_choreography()
    except FinishReached:pass
    finally:n.phase=original_phase
    original_phase('CREATE THE FINISH')
    m.robot('overhand','miss');n.move(10)
    m.punch('hook','block');m.punch('cross','hit',3);n.strike('knee','hit',3)
    n.move(-8)
    start=e.time;PAIR_START=start;FIRST_PAIR_EVENT=len(e.events)
    # Individual durations leave the airborne arch and rear control readable.
    # A tap is followed immediately by release, not additional strikes.
    durations=[260,130,180,180,210,260,200,240,300,240,260,300,650,240,320,2200]
    t=start
    for i,d in enumerate(durations):
        PAIR.append(dict(frame=i,t0=t,t1=t+d));t+=d
    at={p['frame']:p['t0'] for p in PAIR}
    MOMENTS.update(high_kick=at[2]+35,waist_lock=at[5]+80,lift=at[6]+60,
                   german_arch=at[7]+90,landing=at[8]+80,back_control=at[10]+70,
                   choke_entry=at[11]+80,hold=at[12]+260,tap=at[13]+110,
                   release=at[14]+100,victory=at[15]+400)
    original_phase('HIGH KICK')
    e.phases.extend([(at[4],'REAR WAIST LOCK'),(at[6],'GERMAN SUPLEX'),
                     (at[10],'BACK CONTROL'),(at[11],'REAR NAKED CHOKE')])
    e.P.put(start,0);e.B.put(start,0)
    for tr in (e.PX,m.PY,e.BX,e.BY,e.BR):
        tr.put(start,tr.at(start));tr.put(t+299,tr.at(start))
    e.PR.put(start,0);e.LIGHT.put(start,1)
    n.event(at[2]+35,at[3],'player','high roundhouse','hit',4,813,202)
    n.event(at[8]+65,at[9],'player','German suplex','hit',6,741,392)
    n.event(at[13]+90,at[14],'player','rear naked choke','submission',6,781,338)
    n.camera(at[2]+35,2.4);n.camera(at[8]+65,3.2)
    e.final_hit=at[13]+90
    n.grapples.append(dict(kind='rear waist-lock German suplex',start=at[4],impact=at[8]+65,end=at[9]))
    n.grapples.append(dict(kind='rear control, rear naked choke, tap and release',start=at[10],impact=e.final_hit,end=at[14]+100))
    PAIR_END=t
    e.time=t
    # The arena transition hides restoration of the original start positions.
    e.P.put(t+300,0);e.B.put(t+300,0)
    for tr,val in ((e.PX,-24),(m.PY,0),(e.BX,35),(e.BY,0),(e.BR,0),(e.PR,0),(e.LIGHT,1),(e.P_HP,100),(e.B_HP,100)):
        tr.put(t+299,tr.at(t+299,tr in (e.P_HP,e.B_HP)));tr.put(t+300,val)
    m.rest_arms(t+300);e.time=t+800;e.T=e.time

def validate():
    assert sum(ev['damage'] for ev in e.events if ev['actor']=='player')==100
    assert sum(ev['damage'] for ev in e.events if ev['actor']=='robot')==88
    assert e.P_HP.at(e.final_hit,True)==12 and e.B_HP.at(e.final_hit,True)==0
    assert [ev['kind'] for ev in e.events[-3:]]==['high roundhouse','German suplex','rear naked choke']
    assert e.events[-1]['result']=='submission'
    assert MOMENTS['high_kick']<MOMENTS['german_arch']<MOMENTS['hold']<MOMENTS['tap']<MOMENTS['release']
    assert all(ev['t']<=e.final_hit for ev in e.events)
    assert all(ev['damage']==0 for ev in e.events if ev['result'] not in ('hit','submission'))
    print(f'PASS: ordered high kick / German suplex / rear choke; tap-out then release; 12% HP win; {e.T/1000:.2f}s.')

def build():
    n.choreography=choreography;n.validate=validate
    with tempfile.TemporaryDirectory(prefix='fight-v12-') as tmp:
        stage=Path(tmp);(stage/'assets').mkdir()
        shutil.copy2(ROOT/'assets'/'fight-hero-v8.svg',stage/'assets'/'fight-hero-v8.svg')
        for name in ('fighter-v10','fighter-v11'):shutil.copytree(ROOT/'assets'/name,stage/'assets'/name)
        n.ROOT=stage;n.ART=stage/'assets'/'fighter-v11';n.build()
        root=ET.parse(stage/'assets'/'fight-hero-v11.svg').getroot()

    camera=next(el for el in root.iter() if el.get('class')=='v9camera')
    scene=next(el for el in root if el.get('id')=='fight-v9')
    for el in root.iter():
        if el.get('class') in ('v9player','v9bot','v9pshadow','v9bshadow'):
            el.set('class',el.get('class')+' v12native')
    e.windows('v12native',[(0,PAIR_START),(PAIR_END+300,e.T)])
    # Remove the former knockout and its impact effects from the finishing
    # part. The paired artwork supplies the high-kick contact / actual grips.
    for parent in root.iter():
        for el in list(parent):
            c=el.get('class','')
            remove=c in ('v9ko','v9ring','v9win')
            for prefix in ('v9impact','v9cue','v9token','v9combo'):
                if c.startswith(prefix):
                    suffix=c[len(prefix):].split('_')[0]
                    if suffix.isdigit() and int(suffix)>=FIRST_PAIR_EVENT:remove=True
            if remove:parent.remove(el)
    pair_group=e.el(camera,'g',{'class':'v12paired'})
    e.el(pair_group,'ellipse',{'cx':766,'cy':411,'rx':140,'ry':7,'fill':'#05070f','opacity':.24})
    for p in PAIR:
        i=p['frame'];data=base64.b64encode((ART/f'finish-{i:02}.png').read_bytes()).decode()
        e.el(pair_group,'image',{'class':f'v12f{i}','href':'data:image/png;base64,'+data,
                                'x':542,'y':121,'width':448,'height':300,
                                'preserveAspectRatio':'xMidYMid meet','style':'image-rendering:pixelated'})
        end=p['t1']+300 if i==15 else p['t1']
        e.windows(f'v12f{i}',[(p['t0'],end)])
    e.windows('v12paired',[(PAIR_START,PAIR_END+300)])
    e.pixel_text(scene,'TAP OUT',808,180,4.8,e.GOLD,'v12tap')
    e.pixel_text(scene,'YOU WIN',700,143,3.4,e.CYAN,'v12win')
    e.windows('v12tap',[(e.final_hit,PAIR_END)])
    e.windows('v12win',[(e.final_hit+160,PAIR_END)])
    e.el(scene,'text',{'class':'v12sub','x':766,'y':132,'text-anchor':'middle',
                       'font-family':e.MONO,'font-size':10,'letter-spacing':1.5,'fill':'#9fcfd6'},'SUBMISSION')
    e.windows('v12sub',[(e.final_hit,PAIR_END)])
    # Short graphic tap rings at the mat make the surrender legible at profile
    # size without continuing the choke after the bot has submitted.
    pulse=e.el(camera,'g',{'class':'v12tapring','fill':'none','stroke':e.CYAN,'stroke-width':2})
    e.el(pulse,'path',{'d':'M718 399h12v5h-12zM712 395h24v13h-24z'})
    e.windows('v12tapring',[(e.final_hit,e.final_hit+120),(e.final_hit+170,e.final_hit+280)])
    # Old final-phase choreography must not bring back a KO/winner overlay.
    e.ANIMS=[a for a in e.ANIMS if a[0] not in ('v9ko','v9win','v9ring')]
    root.find('{'+NS+'}style').text=e.timeline_css()
    root.set('aria-label','张健航 · AI 产品经理：高扫衔接德式背摔，以裸绞降服获胜')
    out=ROOT/'assets'/'fight-hero-v12.svg';out.write_text(ET.tostring(root,encoding='unicode'))
    review=ROOT/'verification'/'v12';review.mkdir(parents=True,exist_ok=True)
    for name,ms in MOMENTS.items():
        frozen=deepcopy(root);frozen.find('{'+NS+'}style').text=e.timeline_css(ms)
        for parent in frozen.iter():
            for el in list(parent):
                c=el.get('class','')
                if el.tag.endswith('image') and c.startswith('v12f'):
                    i=int(c[4:]);p=PAIR[i]
                    if not p['t0']<=ms<p['t1']+(300 if i==15 else 0):parent.remove(el)
        (review/(name+'.svg')).write_text(ET.tostring(frozen,encoding='unicode'))
    metadata=dict(duration_ms=e.T,finish_start_ms=PAIR_START,tap_ms=e.final_hit,
                  finish_order=['high roundhouse','German suplex','rear naked choke'],
                  result='submission',health_at_win=12,events=e.events,paired_frames=PAIR,previews=MOMENTS)
    (ART/'bout.json').write_text(json.dumps(metadata,indent=2))
    print('Built',out.name,round(out.stat().st_size/1024),'KiB;',MOMENTS)

if __name__=='__main__':build()
