"""Extract complete authored MMA poses at one shared scale (Pillow required)."""
from pathlib import Path
from PIL import Image, ImageDraw
import json

ROOT=Path(__file__).resolve().parents[1]
ART=ROOT/'assets'/'fighter-v11'
LABELS=['CHECK','LOW LOAD','LOW SWING','LOW CONTACT','LOW RECOVER','TEEP LOAD',
        'TEEP EXTEND','TEEP CONTACT','TEEP RECOVER','CLINCH','KNEE LOAD','KNEE CONTACT',
        'KNEE RECOVER','LEVEL CHANGE','SHOOT','LIFT','DRIVE','TOP CONTROL',
        'GROUND LOAD','GROUND CONTACT','SPRAWL','GROUND GUARD','STAND UP','GUARD']

def main():
    src=Image.open(ART/'mma-sheet.png').convert('RGBA');w,h=src.size
    cells=[src.crop((round(c*w/6),round(r*h/4),round((c+1)*w/6),round((r+1)*h/4))) for r in range(4) for c in range(6)]
    bounds=[im.getchannel('A').point(lambda a:255 if a>128 else 0).getbbox() for im in cells]
    # The final cell is the upright reference. Crouches / ground poses are NOT
    # enlarged to the standing height; all 24 images use the same physical scale.
    scale=234/(bounds[23][3]-bounds[23][1])
    contact=Image.new('RGB',(6*330,4*305),'#131b2b');d=ImageDraw.Draw(contact)
    manifest=[];supports={}
    for i,(im,bb) in enumerate(zip(cells,bounds)):
        out=Image.new('RGBA',(320,280))
        small=im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.NEAREST)
        x=round(145-im.width*.5*scale);y=round(260-bb[3]*scale)
        out.alpha_composite(small,(x,y))
        out.putalpha(out.getchannel('A').point(lambda a:0 if a<32 else 255 if a>230 else a))
        out=out.quantize(colors=128,method=Image.Quantize.FASTOCTREE,dither=Image.Dither.NONE).convert('RGBA')
        out.save(ART/f'mma-{i:02}.png',optimize=True)
        if i<13:
            points=[]
            for yy in range(224,280):
                for xx in range(320):
                    rr,gg,bb,aa=out.getpixel((xx,yy))
                    if aa>128 and rr>75 and gg>55 and rr-bb>28 and gg-bb>14:points.append((xx,yy))
            bottom=max(yy for xx,yy in points)
            points=[(xx,yy) for xx,yy in points if yy>=bottom-18]
            supports[i]=dict(x=max(xx for xx,yy in points)-7,y=bottom)
        xx=(i%6)*330+5;yy=(i//6)*305+2
        contact.paste(out,(xx,yy),out);d.text((xx+12,yy+285),f'{i:02} {LABELS[i]}',fill='#c8d8e5')
        manifest.append(dict(index=i,label=LABELS[i],source_bounds=bb,offset=[x,y],visible_bounds=out.getbbox()))
    contact.save(ART/'mma-review.png')
    (ART/'poses.json').write_text(json.dumps(dict(scale=scale,frames=manifest),indent=2))
    (ART/'supports.json').write_text(json.dumps(supports,indent=2))
    print('Extracted 24 MMA frames at a single scale:',scale)

if __name__=='__main__':main()
