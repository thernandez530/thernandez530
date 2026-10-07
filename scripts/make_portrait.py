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
    body=txt(24,29,'ACTIVITY.MONITOR / últimos 12 meses',12,'#67e8f9')
    for i,(label,value) in enumerate([('Contribuciones',data['totalContributions']),('Racha actual',current),('Racha más larga',longest),('Días activos',active),('Mejor día',best),('Promedio diario',round(data['totalContributions']/len(days),1))]):
        x=24+(i%3)*166;y=72+(i//3)*79
        body+=txt(x,y,label,11,'#94a3b8')+txt(x,y+37,value,30,'#d8b4fe' if i==0 else '#f1f5f9')
    body+='<line x1="514" y1="53" x2="514" y2="222" stroke="#29445f"/>'
    monthly={}
    for d in days: monthly[d['date'][:7]]=monthly.get(d['date'][:7],0)+d['contributionCount']
    monthly=list(monthly.items())[-12:];maximum=max(v for _,v in monthly) or 1
    body+=txt(538,65,'CONTRIBUTIONS / MONTH',11,'#67e8f9')
    names=['ene','feb','mar','abr','may','jun','jul','ago','sep','oct','nov','dic']
    for i,(month,value) in enumerate(monthly):
        x=538+i*25;height=round(value/maximum*105)
        bar_color=["#a78bfa","#67e8f9"][i%2]
        body+=f'<rect class="boot" style="animation-delay:{i*.07:.2f}s" x="{x}" y="{195-height}" width="17" height="{max(height,1)}" rx="2" fill="{bar_color}"><title>{month}: {value} contribuciones</title></rect>'
        body+=txt(x-1,214,names[int(month[5:])-1],8,'#94a3b8')
    body+=txt(24,248,'Datos reales de GitHub · actualizado '+data['updated'][:10]+' UTC',10,'#94a3b8')
    (ROOT/'assets/stats.svg').write_text(terminal(body,265,'Estadísticas reales de GitHub: contribuciones, rachas y actividad mensual'),encoding='utf-8')

def terminal(body,height,label,width=860):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img"><title>{html.escape(label)}</title><defs><linearGradient id="surface" x2="1" y2="1"><stop stop-color="#080d23"/><stop offset="1" stop-color="#141d42"/></linearGradient></defs><style>text{{font-family:Consolas,"Liberation Mono",monospace}}.boot{{animation:boot .7s ease both}}@keyframes boot{{from{{opacity:0;transform:translateY(4px)}}to{{opacity:1;transform:translateY(0)}}}}@media(prefers-reduced-motion:reduce){{.boot{{animation:none}}}}</style><rect x="1" y="1" width="{width-2}" height="{height-2}" rx="12" fill="url(#surface)" stroke="#67e8f9" stroke-opacity=".65"/>{body}</svg>'''

def system_profile():
    raw=(ROOT/'assets/portrait.svg').read_text()
    # Nested self-contained SVG: no external image requests, JS or fonts.
    raw=raw.replace('width="740" height="880"','x="25" y="72" width="300" height="357"',1)
    raw=raw.replace('#0d1117','#0a1029').replace('#30363d','#284d70')
    raw=raw.replace('#c9d1d9','#d8b4fe')
    body='<line x1="1" y1="42" x2="859" y2="42" stroke="#29445f"/>'
    for i,c in enumerate(['#fb7185','#fde047','#34d399']):
        body+=f'<circle cx="{22+i*17}" cy="22" r="4" fill="{c}"/>'
    body+=txt(93,27,'thernandez530.connect()',12,'#94a3b8')+txt(692,27,'● SYSTEM ONLINE',11,'#67e8f9')
    body+=txt(26,62,'VISUAL.MAP',10,'#94a3b8')+raw
    body+='<line x1="347" y1="65" x2="347" y2="429" stroke="#29445f"/>'
    body+=txt(373,71,'SYSTEM.INFO',12,'#67e8f9')+txt(373,107,'Tomás Hernández Oñate',26,'#f1f5f9')
    body+='<rect x="373" y="123" width="169" height="23" rx="4" fill="#7c3aed"/>'
    body+=txt(386,139,'FULL STACK DEVELOPER',11,'#f5f3ff')
    fields=[('Origin','Santiago, Chile'),('Education','Ing. Informática / UBO'),('Status','Freelance / abierto a oportunidades'),('Core.Frontend','React · Next.js · TypeScript'),('Core.Backend','Node.js · Express · APIs REST'),('Core.Database','Supabase · MongoDB · MySQL'),('Core.Infrastructure','AWS · Docker · Git · GitHub'),('AI.Toolchain','Claude · Codex · APIs de IA'),('Grid.Portfolio','tomasghernandez.dev'),('Grid.Contact','devstomash@gmail.com')]
    for i,(key,value) in enumerate(fields):
        y=172+i*24
        body+=f'<g class="boot" style="animation-delay:{.2+i*.1:.2f}s">'+txt(373,y,key,11,'#67e8f9')+txt(535,y,value,12,'#dbeafe')+'</g>'
    body+='<line x1="1" y1="447" x2="859" y2="447" stroke="#29445f"/>'
    body+=txt(26,469,'$ construir / integrar / automatizar',11,'#a5b4fc')+txt(642,469,'PROFILE.READY [✓]',11,'#67e8f9')
    (ROOT/'assets/system-profile.svg').write_text(terminal(body,486,'Perfil terminal de Tomás Hernández: retrato ASCII, formación, stack y contactos'),encoding='utf-8')

def project_cards():
    projects=[('portfolio','01','Portafolio personal','Presentación de proyectos y experiencia.','Diseño web y desarrollo de aplicaciones.',['Next.js','TypeScript','Tailwind CSS']),('psiconectados','02','Psiconectados','Agenda, consentimientos digitales y pagos.','Plataforma de atención psicológica.',['Full Stack','Supabase','Mercado Pago'])]
    for slug,number,name,line1,line2,tags in projects:
        body=txt(22,27,'PROJECTS.LIST / '+number,10,'#67e8f9')
        body+=txt(22,65,name,22,'#f1f5f9')+txt(22,95,line1,12,'#cbd5e1')+txt(22,116,line2,12,'#94a3b8')
        x=22
        for tag in tags:
            w=len(tag)*6.5+18
            body+=f'<rect x="{x}" y="140" width="{w}" height="24" rx="12" fill="#6d28d9" fill-opacity=".55" stroke="#a78bfa" stroke-opacity=".35"/>'+txt(x+9,156,tag,10,'#e9d5ff');x+=w+8
        body+='<circle cx="381" cy="49" r="10" fill="none" stroke="#67e8f9" stroke-width="2"/>'
        body+=txt(22,195,'↗ ABRIR PROYECTO',11,'#67e8f9')
        (ROOT/f'assets/project-{slug}.svg').write_text(terminal(body,216,name+' — '+line1,width=420),encoding='utf-8')


def extra_sections():
    calendar=json.loads((ROOT/'data/contributions.json').read_text())
    days=sorted([d for w in calendar['weeks'] for d in w['contributionDays']],key=lambda d:d['date'])
    longest=run=0
    for d in days:
        run=run+1 if d['contributionCount'] else 0; longest=max(longest,run)
    end=len(days)-1
    if days and not days[end]['contributionCount']: end-=1
    current=0
    while end>=0 and days[end]['contributionCount']:
        current+=1;end-=1
    body=txt(26,30,'STREAK.MONITOR',12,'#67e8f9')
    for x,value,label,color in [(154,calendar['totalContributions'],'Contribuciones / 12 meses','#a78bfa'),(430,current,'Racha actual / días','#67e8f9'),(706,longest,'Mejor racha / días','#a78bfa')]:
        body+=f'<circle cx="{x}" cy="109" r="51" fill="none" stroke="#243352" stroke-width="7"/><circle cx="{x}" cy="109" r="51" fill="none" stroke="{color}" stroke-width="7" stroke-dasharray="280 41" transform="rotate(-90 {x} 109)"/>'
        body+=f'<text x="{x}" y="119" text-anchor="middle" fill="#f1f5f9" font-size="32">{value}</text><text x="{x}" y="187" text-anchor="middle" fill="#94a3b8" font-size="12">{label}</text>'
    (ROOT/'assets/streaks.svg').write_text(terminal(body,213,'Contribuciones y rachas reales de GitHub'),encoding='utf-8')
    path=ROOT/'data/profile-metrics.json'
    metrics=json.loads(path.read_text()) if path.exists() else {}
    body=txt(26,30,'GITHUB.STATS',12,'#67e8f9')+txt(449,30,'MOST USED LANGUAGES',12,'#67e8f9')
    body+='<line x1="421" y1="52" x2="421" y2="282" stroke="#29445f"/>'
    rows=[('Estrellas / repos públicos','stars'),('Commits / últimos 12 meses','commits'),('Pull requests / 12 meses','prs'),('Issues / últimos 12 meses','issues'),('Repos con commits / 12 meses','contributed'),('Repositorios públicos propios','repositories')]
    for i,(label,key) in enumerate(rows):
        y=72+i*35
        body+=txt(26,y,label,12,'#cbd5e1')+txt(367,y,metrics.get(key,'—'),16,'#d8b4fe')
    languages=sorted(metrics.get('languages',{}).items(),key=lambda pair:pair[1]['bytes'],reverse=True)
    total=sum(d['bytes'] for _,d in languages)
    if total:
        top=languages[:5]
        if len(languages)>5: top.append(('Otros',{'bytes':sum(v['bytes'] for _,v in languages[5:]),'color':'#94a3b8'}))
        for i,(name,data) in enumerate(top):
            y=70+i*34;percent=data['bytes']/total*100;color=html.escape(data['color'],quote=True)
            body+=txt(449,y,name,12,'#cbd5e1')+txt(760,y,f'{percent:.1f}%',11,'#d8b4fe')
            body+=f'<rect x="449" y="{y+8}" width="355" height="7" rx="3" fill="#243352"/><rect class="boot" style="animation-delay:{i*.12}s" x="449" y="{y+8}" width="{355*percent/100:.2f}" height="7" rx="3" fill="{color}"/>'
    else:
        body+=txt(449,90,'Sincronizando datos de GitHub…',12,'#94a3b8')
    body+=txt(449,293,'Bytes de código público · excluye este perfil',10,'#94a3b8')
    body+=txt(26,318,'GitHub API / '+metrics.get('updated',calendar['updated'])[:10]+' UTC',10,'#94a3b8')
    (ROOT/'assets/github-overview.svg').write_text(terminal(body,337,'Estadísticas de GitHub y distribución de lenguajes en repositorios públicos'),encoding='utf-8')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--source-file','--avatar-file',dest='source_file');args=parser.parse_args()
    source=args.source_file or ROOT/'assets/portrait-source.jpg'
    portrait(source);stats();system_profile();project_cards();extra_sections()
