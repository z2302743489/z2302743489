"""Extract the generated 4x4 boxing footwork sheet and measure shoe contacts.

Uses a single uniform scale for the whole sheet, never warps legs or feet.
Pillow is only used for grid extraction, PNG optimization and QA annotations.
"""
from pathlib import Path
from PIL import Image, ImageDraw
import json

ROOT=Path(__file__).resolve().parents[1]
ART=ROOT/'assets'/'fighter-v10'

def contacts(image):
    im=image.convert('RGBA');w,h=im.size
    # White socks separate the tan shoes from the skin; keep color components
    # below the knees and find the two lowest substantial shoe components.
    points=set()
    for y in range(190,h):
        for x in range(w):
            r,g,b,a=im.getpixel((x,y))
            if a>128 and r>75 and g>55 and r-b>28 and g-b>14:
                points.add((x,y))
    groups=[]
    while points:
        p=points.pop();stack=[p];group=[p]
        while stack:
            x,y=stack.pop()
            for dx,dy in [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)]:
                q=x+dx,y+dy
                if q in points:points.remove(q);stack.append(q);group.append(q)
        if len(group)>=22:
            xs=[p[0] for p in group];ys=[p[1] for p in group]
            groups.append(dict(size=len(group),box=[min(xs),min(ys),max(xs),max(ys)]))
    groups.sort(key=lambda g:(g['box'][3],g['size']),reverse=True)
    selected=[]
    for g in groups:
        x0,y0,x1,y1=g['box']
        if y1-y0>38:continue
        if any(abs((x0+x1)/2-(q['box'][0]+q['box'][2])/2)<22 for q in selected):continue
        selected.append(g)
        if len(selected)==2:break
    assert len(selected)==2,groups
    selected.sort(key=lambda g:g['box'][0])
    # Ball of the foot, slightly behind each trainer's toe, is the pivot.
    return {name:dict(x=g['box'][2]-7,y=g['box'][3],box=g['box'])
            for name,g in zip(('rear','lead'),selected)}

def main():
    original=Image.open(ART/'footwork-sheet.png').convert('RGBA')
    w,h=original.size
    cells=[original.crop((round(c*w/4),round(r*h/4),round((c+1)*w/4),round((r+1)*h/4))) for r in range(4) for c in range(4)]
    bounds=[im.getchannel('A').point(lambda a:255 if a>128 else 0).getbbox() for im in cells]
    scale=234/(bounds[0][3]-bounds[0][1])
    metadata=[]
    review=Image.new('RGB',(4*340,4*310),'#131b2b');d=ImageDraw.Draw(review)
    for i,(im,bb) in enumerate(zip(cells,bounds)):
        im=im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.NEAREST)
        out=Image.new('RGBA',(320,280))
        ox=round(145-cells[0].width*.5*scale);oy=round(260-bb[3]*scale)
        out.alpha_composite(im,(ox,oy))
        out.putalpha(out.getchannel('A').point(lambda a:0 if a<32 else 255 if a>230 else a))
        out=out.quantize(colors=128,method=Image.Quantize.FASTOCTREE,dither=Image.Dither.NONE).convert('RGBA')
        out.save(ART/f'foot-{i:02}.png',optimize=True)
        feet=contacts(out)
        metadata.append(dict(index=i,**feet))
        x=(i%4)*340+10;y=(i//4)*310+4
        review.paste(out,(x,y),out)
        for which,color in [('rear','#ffbd66'),('lead','#6ee7ed')]:
            px,py=feet[which]['x']+x,feet[which]['y']+y
            d.ellipse((px-3,py-3,px+3,py+3),outline=color,width=2)
        d.text((x+10,y+286),f'{i:02}  REAR {feet["rear"]["x"]}  LEAD {feet["lead"]["x"]}',fill='#d0d9e3')
    base=contacts(Image.open(ROOT/'assets'/'fighter-v7'/'pose-00.png'))
    data=dict(scale=scale,base=base,frames=metadata)
    (ART/'footwork.json').write_text(json.dumps(data,indent=2))
    review.save(ART/'footwork-review.png')
    print('Measured contacts:',[(m['index'],m['rear']['x'],m['lead']['x']) for m in metadata])

if __name__=='__main__':main()
