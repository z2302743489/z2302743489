"""Extract paired finishing poses without scaling individual bodies or limbs.

Pillow is needed only for this source extraction / web-export step. Every
paired frame has one shared physical scale, including the grounded frames.
"""
from pathlib import Path
from PIL import Image, ImageDraw
import json

ROOT=Path(__file__).resolve().parents[1]
ART=ROOT/'assets'/'fighter-v12'
LABELS=['GUARD','HIGH LOAD','HIGH CONTACT','RETRACT','GO BEHIND','REAR WAIST LOCK',
        'LIFT','GERMAN ARCH','LANDING','ROLL BEHIND','BACK CONTROL','CHOKE ENTRY',
        'HOLD','TAP OUT','RELEASE','VICTORY']

def components(im):
    a=im.getchannel('A');w,h=im.size
    points={(x,y) for y in range(h) for x in range(w) if a.getpixel((x,y))>128}
    groups=[]
    while points:
        seed=points.pop();todo=[seed];xs=[];ys=[]
        while todo:
            x,y=todo.pop();xs.append(x);ys.append(y)
            for dx,dy in ((-1,0),(1,0),(0,-1),(0,1),(-1,-1),(1,1),(-1,1),(1,-1)):
                p=x+dx,y+dy
                if p in points:points.remove(p);todo.append(p)
        if len(xs)>150:groups.append((len(xs),(min(xs),min(ys),max(xs)+1,max(ys)+1)))
    return sorted(groups,reverse=True)

def main():
    source=Image.open(ART/'finish-sheet.png').convert('RGBA');w,h=source.size
    cells=[source.crop((round(c*w/4),round(r*h/4),round((c+1)*w/4),round((r+1)*h/4))) for r in range(4) for c in range(4)]
    bounds=[im.getchannel('A').point(lambda a:255 if a>128 else 0).getbbox() for im in cells]
    groups=components(cells[0]);assert len(groups)>=2,groups
    human=min(groups[:2],key=lambda pair:pair[1][0])[1]
    human_h=human[3]-human[1]
    scale=min(234/human_h,414/max(b[2]-b[0] for b in bounds),278/max(b[3]-b[1] for b in bounds))
    # A fixed horizontal composition for all 16 poses; the entire paired image
    # moves together so hands and grips cannot separate from the opponent.
    minx=min(b[0] for b in bounds);maxx=max(b[2] for b in bounds)
    common_x=round(224-(minx+maxx)*scale/2)
    rows=[];review=Image.new('RGB',(4*458,4*330),'#131b2b');draw=ImageDraw.Draw(review)
    for i,(cell,bb) in enumerate(zip(cells,bounds)):
        out=Image.new('RGBA',(448,300))
        smaller=cell.resize((round(cell.width*scale),round(cell.height*scale)),Image.Resampling.NEAREST)
        y=round(284-bb[3]*scale)
        out.alpha_composite(smaller,(common_x,y))
        out.putalpha(out.getchannel('A').point(lambda a:0 if a<32 else 255 if a>230 else a))
        indexed=out.quantize(colors=160,method=Image.Quantize.FASTOCTREE,dither=Image.Dither.NONE)
        indexed.save(ART/f'finish-{i:02}.png',optimize=True)
        out=indexed.convert('RGBA')
        xx=(i%4)*458+5;yy=(i//4)*330+2
        review.paste(out,(xx,yy),out);draw.text((xx+15,yy+307),f'{i:02} {LABELS[i]}',fill='#c8d8e5')
        rows.append(dict(index=i,label=LABELS[i],bounds=out.getbbox(),source_bounds=bb,offset=[common_x,y]))
    review.save(ART/'finish-review.png')
    metadata=dict(scale=scale,human_source_bounds=human,rendered_standing_height=human_h*scale,frames=rows)
    (ART/'poses.json').write_text(json.dumps(metadata,indent=2))
    print('Extracted 16 paired finishing frames; standing human height:',human_h*scale)

if __name__=='__main__':main()
