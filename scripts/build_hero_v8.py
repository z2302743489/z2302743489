"""Refine the profile's editorial panel while preserving the v7 fight scene.

Run: python3 scripts/build_hero_v8.py
Uses only Python's standard library. Edit PRINCIPLES or CLOSING to change copy.
"""
from pathlib import Path
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
NS = 'http://www.w3.org/2000/svg'
ET.register_namespace('', NS)
CN = "'PingFang SC','Hiragino Sans GB','Microsoft YaHei','Noto Sans CJK SC',sans-serif"
SANS = "Inter,'Helvetica Neue',Arial,sans-serif"
MONO = "'SF Mono',Menlo,Consolas,monospace"

PRINCIPLES = [
    ('01', 'PROBLEM FIRST', '好问题，先于好答案。'),
    ('02', 'AGENCY & CONTROL', '让 AI 行动，让人保有判断。'),
    ('03', 'EVIDENCE OVER CONFIDENCE', '用真实反馈，校准每次判断。'),
]
CLOSING = '在不确定中，交付值得信任的体验。'


def element(parent, tag, attrs, text=None):
    el = ET.SubElement(parent, '{'+NS+'}'+tag, {k:str(v) for k,v in attrs.items()})
    el.text = text
    return el


def main():
    source = ROOT/'assets'/'fight-hero-v7.svg'
    output = ROOT/'assets'/'fight-hero-v8.svg'
    root = ET.fromstring(source.read_text())
    # Remove the two red-circled terminal labels and the left terminal group,
    # which also contains the red-circled footer and all green-circled copy.
    old_panel = next(el for el in root if el.tag.endswith('g') and 'whoami' in ''.join(el.itertext()))
    index = list(root).index(old_panel)
    root.remove(old_panel)
    for el in list(root):
        if el.tag.endswith('text') and 'portfolio — fight mode' in ''.join(el.itertext()):
            root.remove(el)
            index -= 1

    panel = ET.Element('{'+NS+'}g', {'id':'editorial-panel-v8', 'font-family':CN})
    # A clear typographic anchor replaces the old prompt / large name stack.
    element(panel,'text',dict(x=46,y=130,fill='#17232f',**{'font-size':32,'font-weight':650,'letter-spacing':-.8}), '张健航 · AI 产品经理')
    element(panel,'line',dict(x1=46,y1=164,x2=500,y2=164,stroke='#dfe6eb',**{'stroke-width':1}))

    for i,(number,label,copy) in enumerate(PRINCIPLES):
        y=202+i*66
        element(panel,'text',dict(x=46,y=y+4,fill='#6f9390',**{'font-family':MONO,'font-size':12,'font-weight':500,'letter-spacing':.5}), number)
        element(panel,'line',dict(x1=72,y1=y-11,x2=72,y2=y+17,stroke='#d5e2df',**{'stroke-width':1}))
        element(panel,'text',dict(x=88,y=y-7,fill='#78868f',**{'font-family':SANS,'font-size':9,'font-weight':600,'letter-spacing':1.7}), label)
        element(panel,'text',dict(x=86,y=y+20,fill='#2b3b47',**{'font-size':20,'font-weight':500,'letter-spacing':.1}),copy)

    element(panel,'line',dict(x1=46,y1=374,x2=500,y2=374,stroke='#dfe6eb',**{'stroke-width':1}))
    element(panel,'line',dict(x1=46,y1=401,x2=68,y2=401,stroke='#6f9390',**{'stroke-width':2}))
    element(panel,'text',dict(x=82,y=407,fill='#546874',**{'font-size':17,'font-weight':450,'letter-spacing':.1}), CLOSING)
    root.insert(index,panel)

    # The removed command no longer needs its typing/cursor animations.
    style = root.find('{'+NS+'}style')
    for name in ('type','blink'):
        style.text = re.sub(r'@keyframes '+name+r'\{.*?\}\.'+name+r'\{[^}]*\}', '', style.text, flags=re.S)
    document = ET.tostring(root,encoding='unicode')
    ET.fromstring(document)
    for removed in ('whoami','jianhang@lab','./fight hallucination','portfolio — fight mode','点击进入我的个人网站','[ OK ]'):
        assert removed not in document,removed
    # The scene must be byte-for-byte equivalent at the element level.
    original_scene=next(el for el in ET.fromstring(source.read_text()) if el.get('clip-path')=='url(#clip)')
    new_scene=next(el for el in root if el.get('clip-path')=='url(#clip)')
    assert ET.tostring(original_scene)==ET.tostring(new_scene)
    output.write_text(document)
    print(f'Built {output.name}: removed all marked terminal labels; fight scene unchanged.')


if __name__=='__main__':
    main()
