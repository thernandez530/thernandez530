"""Convert the chosen illustration to self-typing ASCII SVG + real stats."""
import argparse, html, json, pathlib
from PIL import Image, ImageOps, ImageEnhance, ImageFilter, ImageDraw
import math
ROOT=pathlib.Path(__file__).resolve().parents[1]

def panel(width,body,title):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="440" viewBox="0 0 {width} 440" role="img"><title>{html.escape(title)}</title><style>text{{font-family:Consolas,"Liberation Mono",monospace}}.row{{animation:print 0.6s ease-out both;clip-path:inset(0 0 0 0)}}@keyframes print{{from{{clip-path:inset(0 100% 0 0)}}to{{clip-path:inset(0 0 0 0)}}}}.fade{{animation:fade .7s ease both}}@keyframes fade{{from{{opacity:0}}to{{opacity:1}}}}@media(prefers-reduced-motion:reduce){{.row,.fade{{animation:none}}}}</style><rect x=".5" y=".5" width="{width-1}" height="439" rx="12" fill="#0d1117" stroke="#30363d"/>{body}</svg>'''

def txt(x,y,value,size=13,color='#c9d1d9'):
    return f'<text x="{x}" y="{y}" fill="{color}" font-size="{size}">{html.escape(str(value))}</text>'

def portrait(source):
    image=Image.open(source).convert('RGB')
    # Isolate the head from the supplied 864×1536 illustration.
    width,height=image.size
    outline=[(402,300),(420,278),(424,254),(464,246),(458,231),
             (492,235),(522,231),(556,227),(608,244),(659,269),
             (683,309),(701,321),(693,348),(698,401),(678,456),
             (661,509),(662,540),(647,582),(609,596),(564,639),
             (501,681),(438,720),(389,714),(379,685),(380,637),
             (366,589),(355,551),(352,511),(353,472),(350,443),
             (351,419),(366,407),(383,359)]
    mask=Image.new('L',image.size,0)
    ImageDraw.Draw(mask).polygon(
        [(round(x*width/864),round(y*height/1536)) for x,y in outline],
        fill=255)
    isolated=Image.new('RGB',image.size,'white')
    isolated.paste(image,(0,0),mask)
    crop=isolated.crop((round(width*330/864),round(height*215/1536),
                       round(width*720/864),round(height*735/1536)))
    crop=ImageOps.contain(crop,(360,390),method=Image.Resampling.LANCZOS)
    image=Image.new('RGB',(360,390),'white')
    image.paste(crop,((360-crop.width)//2,(390-crop.height)//2))
    gray=ImageOps.grayscale(image)
    pixels=list(gray.tobytes());subject=[value<250 for value in pixels]
    width_px,height_px=gray.size
    # Same bilateral kernel, implemented with Pillow and Python's standard
    # library so the existing workflow needs no new dependency or permission.
    range_weight=[math.exp(-difference*difference/(2*35**2)) for difference in range(256)]
    kernel=[(dx,dy,math.exp(-(dx*dx+dy*dy)/8))
            for dy in range(-2,3) for dx in range(-2,3)]
    smooth=pixels
    for _ in range(3):
        filtered=[]
        for y in range(height_px):
            for x in range(width_px):
                center=smooth[y*width_px+x]
                if not subject[y*width_px+x]:
                    filtered.append(255);continue
                numerator=denominator=0.0
                for dx,dy,spatial in kernel:
                    xx=min(width_px-1,max(0,x+dx));yy=min(height_px-1,max(0,y+dy))
                    neighbor=smooth[yy*width_px+xx]
                    weight=spatial*range_weight[abs(neighbor-center)]
                    numerator+=weight*neighbor;denominator+=weight
                filtered.append(round(numerator/denominator))
        smooth=filtered
    values=sorted(value for value,inside in zip(smooth,subject) if inside)
    if not values: raise ValueError('No portrait subject found in the selected source')
    lo=values[round((len(values)-1)*.02)];hi=values[round((len(values)-1)*.90)]
    smoothed=Image.new('L',gray.size);smoothed.putdata(smooth)
    fine=list(smoothed.filter(ImageFilter.GaussianBlur(1.5)).tobytes())
    coarse=list(smoothed.filter(ImageFilter.GaussianBlur(6)).tobytes())
    tones=[]
    for value,f,c,inside in zip(smooth,fine,coarse,subject):
        tone=min(1,max(0,(value-lo)/max(hi-lo,1)))
        ridge=min(1,max(0,(c-f)/40))
        tones.append(round(max(0,min(1,tone-.6*ridge))*255) if inside else 255)
    image=Image.new('L',gray.size);image.putdata(tones)
    image=image.resize((180,104),Image.Resampling.LANCZOS)
    ramp=" .`:-=+*cs#%@"
    width,height=740,880
    body='<defs>'
    cols,rows=image.size;cell_w=684/cols;cell_h=750/rows
    duration=5.8/rows
    for row in range(rows):
        body+=f'<clipPath id="line-{row}"><rect x="28" y="{74+row*cell_h:.3f}" width="0" height="{cell_h:.3f}"><animate attributeName="width" from="0" to="684" begin="{row*duration:.3f}s" dur="{duration:.3f}s" fill="freeze"/></rect></clipPath>'
    body+='</defs><style>.portrait-row{clip-path:var(--row-clip)}@media(prefers-reduced-motion:reduce){.portrait-row{clip-path:none}.typing-cursor{display:none}}</style>'
    body+='<rect x=".5" y=".5" width="739" height="879" rx="20" fill="#0d1117" stroke="#30363d"/>'
    body+='<line x1="0" y1="52" x2="740" y2="52" stroke="#30363d"/>'
    for i,color in enumerate(['#ff5f57','#febc2e','#28c840']):
        body+=f'<circle cx="{28+i*26}" cy="26" r="7" fill="{color}"/>'
    body+=txt(130,34,'tomas@github ~ $ ./portrait.sh',19,'#8b949e')
    for row in range(rows):
        chars=[]
        for x in range(cols):
            lum=(image.getpixel((x,row))/255)**1.0
            chars.append(' ' if lum>=.83 else ramp[round((1-lum)*(len(ramp)-1))])
        y=74+row*cell_h;delay=row*duration
        body+=f'<g class="portrait-row" style="--row-clip:url(#line-{row})"><text xml:space="preserve" x="28" y="{y+cell_h*.78:.3f}" fill="#c9d1d9" font-size="{cell_h*.86:.3f}" textLength="684" lengthAdjust="spacing">{html.escape("".join(chars))}</text></g>'
        body+=f'<rect class="typing-cursor" y="{y:.3f}" width="{cell_w:.3f}" height="{cell_h:.3f}" fill="#c9d1d9" opacity="0"><animate attributeName="x" from="28" to="712" begin="{delay:.3f}s" dur="{duration:.3f}s" fill="freeze"/><set attributeName="opacity" to=".8" begin="{delay:.3f}s"/><set attributeName="opacity" to="0" begin="{delay+duration:.3f}s"/></rect>'
    body+='<line x1="0" y1="836" x2="740" y2="836" stroke="#30363d"/>'
    body+=txt(28,865,'tomas@github ~ $ whoami  Tomás Hernández',18,'#8b949e')
    svg=f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img"><title>Retrato ASCII animado de Tomás Hernández</title><style>text{{font-family:Consolas,"Liberation Mono",monospace}}</style>{body}</svg>'
    (ROOT/'assets/portrait.svg').write_text(svg,encoding='utf-8')

def stats():
    data=json.loads((ROOT/'data/contributions.json').read_text())
    days=sorted([d for w in data['weeks'] for d in w['contributionDays']],key=lambda d:d['date'])
    streak=longest=0
    for d in days:
        streak=streak+1 if d['contributionCount']>0 else 0
        longest=max(longest,streak)
    end=len(days)-1
    # An incomplete zero-contribution today does not break yesterday's streak.
    if days[end]['contributionCount']==0: end-=1
    current=0
    while end>=0 and days[end]['contributionCount']>0:
        current+=1;end-=1
    active=sum(d['contributionCount']>0 for d in days)
    best=max(d['contributionCount'] for d in days)
    body=txt(20,27,'tomas@github ~ $ stats',12,'#8b949e')
    body+=txt(20,59,'Tomás Hernández',22,'#f0f6fc')+txt(20,82,'Full Stack · Santiago, Chile',13,'#3fb950')
    for i,(label,value) in enumerate([('Racha actual',f'{current} día' if current==1 else f'{current} días'),('Racha más larga',f'{longest} día' if longest==1 else f'{longest} días'),('Contribuciones',data['totalContributions']),('Días activos',active),('Mejor día',best),('Promedio / día',round(data['totalContributions']/len(days),1))]):
        x=20+(i%2)*230;y=115+(i//2)*62
        body+=txt(x,y,label,11,'#8b949e')+txt(x,y+26,value,23,'#3fb950' if i==0 else '#f0f6fc')
    monthly={}
    for d in days: monthly[d['date'][:7]]=monthly.get(d['date'][:7],0)+d['contributionCount']
    monthly=list(monthly.items())[-12:]; maximum=max(v for _,v in monthly) or 1
    body+=txt(20,310,'Contribuciones por mes · últimos 12 meses',11,'#8b949e')
    names=['ene','feb','mar','abr','may','jun','jul','ago','sep','oct','nov','dic']
    for i,(month,value) in enumerate(monthly):
        x=20+i*38; height=round(value/maximum*70)
        body+=f'<rect class="fade" style="animation-delay:{i*.05}s" x="{x}" y="{390-height}" width="25" height="{max(height,1)}" rx="2" fill="#3fb950"><title>{month}: {value} contribuciones</title></rect>'
        body+=txt(x,407,names[int(month[5:])-1],9,'#8b949e')
    body+=txt(20,429,'Datos reales · '+data['updated'][:10]+' UTC',10,'#8b949e')
    (ROOT/'assets/stats.svg').write_text(panel(490,body,'Estadísticas reales y contribuciones mensuales de Tomás Hernández'),encoding='utf-8')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--source-file','--avatar-file',dest='source_file');args=parser.parse_args()
    source=args.source_file or ROOT/'assets/portrait-source.jpg'
    portrait(source);stats()
