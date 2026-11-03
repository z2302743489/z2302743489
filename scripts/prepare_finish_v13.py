"""Export the corrected human-only sheet. Requires Pillow.

Keep one physical scale for all sixteen poses. The original robot is rendered
separately by the SVG engine and is never present in these bitmaps.
"""
from pathlib import Path
from PIL import Image, ImageDraw
import json

ROOT=Path(__file__).resolve().parents[1]
ART=ROOT/'assets'/'fighter-v13'
LABELS=['GUARD','HIGH LOAD','HIGH CONTACT','RETRACT','GO BEHIND','WAIST LOCK',
        'LIFT','GERMAN ARCH','LANDING','ROLL','BACK CONTROL','CHOKE ENTRY',
        'HOLD','TAP','RELEASE','VICTORY']

def main():
    sheet=Image.open(ART/'human-sheet.png').convert('RGBA');w,h=sheet.size
    assert sheet.getchannel('A').getextrema()[0]==0,'Source needs genuine transparency'
    scale=1.04;records=[]
    review=Image.new('RGB',(4*458,4*330),'#131b2b');draw=ImageDraw.Draw(review)
    for i,label in enumerate(LABELS):
        c,r=i%4,i//4
        cell=sheet.crop((round(c*w/4),round(r*h/4),round((c+1)*w/4),round((r+1)*h/4)))
        bb=cell.getchannel('A').point(lambda a:255 if a>128 else 0).getbbox()
        assert bb
        y=round(284-bb[3]*scale)
        canvas=Image.new('RGBA',(448,300))
        cell=cell.resize((round(cell.width*scale),round(cell.height*scale)),Image.Resampling.NEAREST)
        canvas.alpha_composite(cell,(19,y))
        canvas.putalpha(canvas.getchannel('A').point(lambda a:0 if a<32 else 255 if a>230 else a))
        indexed=canvas.quantize(colors=160,method=Image.Quantize.FASTOCTREE,dither=Image.Dither.NONE)
        indexed.save(ART/f'human-{i:02}.png',optimize=True)
        out=indexed.convert('RGBA');x0=c*458+5;y0=r*330+2
        review.paste(out,(x0,y0),out);draw.text((x0+15,y0+307),f'{i:02} {label}',fill='#c8d8e5')
        records.append(dict(index=i,label=label,source_bounds=bb,offset=[19,y],bounds=out.getbbox()))
    review.save(ART/'human-review.png')
    (ART/'poses.json').write_text(json.dumps(dict(scale=scale,frames=records),indent=2))
    print('Exported sixteen human-only poses at fixed scale; no robot bitmaps.')

if __name__=='__main__':main()
