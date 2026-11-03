"""Export authored neck-lock and landing inbetweens. Requires Pillow."""
from pathlib import Path
from PIL import Image,ImageDraw
import json

ROOT=Path(__file__).resolve().parents[1]
ART=ROOT/'assets'/'fighter-v14'

def export(im,name,baseline=284):
    im=im.convert('RGBA').resize((448,300),Image.Resampling.NEAREST)
    a=im.getchannel('A');assert a.getextrema()[0]==0
    bb=a.point(lambda n:255 if n>128 else 0).getbbox()
    out=Image.new('RGBA',(448,300));out.alpha_composite(im,(0,baseline-bb[3]))
    out.putalpha(out.getchannel('A').point(lambda n:0 if n<32 else 255 if n>230 else n))
    out.quantize(colors=160,method=Image.Quantize.FASTOCTREE,dither=Image.Dither.NONE).save(ART/name,optimize=True)
    return out

def main():
    images=[export(Image.open(ART/'choke-source.png'),'choke.png')]
    sheet=Image.open(ART/'fall-sheet.png');w,h=sheet.size
    for i in range(4):
        c,r=i%2,i//2
        images.append(export(sheet.crop((round(c*w/2),round(r*h/2),round((c+1)*w/2),round((r+1)*h/2))),f'fall-{i}.png'))
    review=Image.new('RGB',(448*3,330*2),'#131b2b');d=ImageDraw.Draw(review)
    for i,im in enumerate(images):
        x=i%3*448;y=i//3*330;review.paste(im,(x,y),im)
        d.text((x+18,y+309),'CHOKE' if i==0 else f'FALL {i-1}',fill='#c8d8e5')
    review.save(ART/'review.png')
    print('Exported neck-lock and four landing poses with one scale; alpha preserved.')

if __name__=='__main__':main()
