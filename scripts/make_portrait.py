"""Convert the chosen illustration to self-typing ASCII SVG + real stats."""
import argparse, html, json, pathlib
from PIL import Image, ImageOps, ImageEnhance, ImageFilter, ImageDraw
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
    image=ImageOps.autocontrast(ImageOps.grayscale(image),cutoff=.5)
    image=ImageEnhance.Contrast(image).enhance(1.25)
    image=image.filter(ImageFilter.UnsharpMask(radius=1.4,percent=150,threshold=3))
    # Monospace glyphs are ~0.6 times as wide as tall. Match the grid to
    # those dimensions and keep full line height so characters never overlap.
    image=image.resize((100,66),Image.Resampling.LANCZOS)
    ramp=' .:-=+*#%@'
    body=txt(18,25,'tomas@github ~ $ avatar',11,'#8b949e')
    for row in range(image.height):
        chars=''.join(ramp[round((255-image.getpixel((x,row)))/255*(len(ramp)-1))] for x in range(image.width))
        body+=f'<text class="row" style="animation-delay:{row*.035:.3f}s" x="13" y="{48+row*5.6:.2f}" font-size="5.7" fill="#e6edf3" xml:space="preserve">{html.escape(chars)}</text>'
    body+=txt(18,426,'Retrato ilustrado · @thernandez530',10,'#8b949e')
    (ROOT/'assets/portrait.svg').write_text(panel(370,body,'Retrato ASCII animado de Tomás Hernández, generado desde la ilustración elegida por el usuario'),encoding='utf-8')

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
