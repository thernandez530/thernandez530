"""Generate self-contained profile SVGs. Python 3.11+, no dependencies."""
import argparse, datetime as dt, html, json, pathlib, urllib.request
ROOT = pathlib.Path(__file__).resolve().parents[1]
USER = 'thernandez530'

def svg(body, height, label):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="860" height="{height}" viewBox="0 0 860 {height}" role="img" aria-label="{html.escape(label)}"><title>{html.escape(label)}</title><style>text{{font-family:ui-monospace,Consolas,monospace}}.reveal{{animation:reveal .6s ease both}}@keyframes reveal{{from{{opacity:0;transform:translateY(5px)}}to{{opacity:1;transform:translateY(0)}}}}@media(prefers-reduced-motion:reduce){{.reveal{{animation:none}}}}</style><rect width="860" height="{height}" rx="16" fill="#080d23"/><rect x=".5" y=".5" width="859" height="{height-1}" rx="16" fill="none" stroke="#29445f"/>{body}</svg>'''

def text(x,y,value,color='#c9d1d9',size=16,delay=0):
    return f'<text class="reveal" style="animation-delay:{delay}s" x="{x}" y="{y}" fill="{color}" font-size="{size}">{html.escape(value)}</text>'

def card():
    b=''.join(f'<circle cx="{32+i*20}" cy="26" r="5" fill="{c}"/>' for i,c in enumerate(['#ff5f57','#febc2e','#28c840']))
    b+=text(100,31,'tomas@github ~ $ whoami','#8b949e',13)
    b+=text(32,89,'Tomás Hernández Oñate','#f0f6fc',30,.1)
    b+=text(32,121,'Desarrollador Full Stack · Santiago, Chile','#67e8f9',18,.2)
    rows=[('Formación','Ingeniería en Informática · UBO'),('Trabajo','Desarrollo freelance · APIs · automatización'),('Frontend','React · Next.js · TypeScript · Tailwind CSS'),('Backend','Node.js · Express · APIs REST'),('Datos','Supabase · MongoDB · MySQL'),('Cloud','AWS · Docker · Git · GitHub'),('IA','Claude / Codex · integración de APIs de IA')]
    for i,(key,value) in enumerate(rows):
        y=170+i*30
        b+=text(32,y,key,'#79c0ff',14,.3+i*.08)+text(165,y,value,size=15,delay=.3+i*.08)
    b+=text(32,409,'$ construir → integrar → automatizar','#67e8f9',15,1)
    (ROOT/'assets/info-card.svg').write_text(svg(b,440,'Presentación y stack de Tomás Hernández'),encoding='utf-8')

def fetch():
    # GitHub Actions supplies its built-in token; no personal token required.
    import os
    token=os.environ.get('GH_TOKEN')
    if not token: raise RuntimeError('GH_TOKEN is required for --fetch (use the built-in GitHub Actions token).')
    query='query($login:String!){user(login:$login){contributionsCollection{contributionCalendar{totalContributions weeks{contributionDays{date contributionCount contributionLevel}}}}}}'
    req=urllib.request.Request('https://api.github.com/graphql',data=json.dumps({'query':query,'variables':{'login':USER}}).encode(),headers={'Authorization':'Bearer '+token,'Content-Type':'application/json','User-Agent':'profile-art'})
    with urllib.request.urlopen(req,timeout=30) as response: result=json.load(response)
    if result.get('errors'): raise RuntimeError(str(result['errors']))
    calendar=result['data']['user']['contributionsCollection']['contributionCalendar']
    if not calendar['weeks']: raise ValueError('Empty calendar; keeping previous assets.')
    (ROOT/'data').mkdir(exist_ok=True)
    calendar['updated']=dt.datetime.now(dt.timezone.utc).isoformat()
    (ROOT/'data/contributions.json').write_text(json.dumps(calendar,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def heatmap():
    path=ROOT/'data/contributions.json'
    b=text(32,36,'tomas@github ~ $ contributions','#67e8f9',16)
    if not path.exists():
        b+=text(32,88,'Calendario conectado a GitHub Actions.',size=18)
        b+=text(32,123,'Los datos reales aparecerán tras la primera ejecución.','#8b949e',15)
        height=165
    else:
        data=json.loads(path.read_text()); palette={'NONE':'#151b35','FIRST_QUARTILE':'#31215f','SECOND_QUARTILE':'#6d28d9','THIRD_QUARTILE':'#a855f7','FOURTH_QUARTILE':'#d8b4fe'}
        for week_i,week in enumerate(data['weeks']):
            for day in week['contributionDays']:
                date=dt.date.fromisoformat(day['date']); row=(date.weekday()+1)%7
                b+=f'<rect class="reveal" style="animation-delay:{min((week_i+row)*.015,1):.3f}s" x="{32+week_i*15}" y="{63+row*18}" width="12" height="14" rx="3" fill="{palette[day["contributionLevel"]]}"><title>{date}: {day["contributionCount"]} contribuciones</title></rect>'
        b+=text(32,221,f'{data["totalContributions"]} contribuciones · últimos 12 meses',size=15)
        b+=text(32,250,'Actualizado: '+data['updated'][:10]+' UTC','#8b949e',12)
        height=278
    (ROOT/'assets/contributions.svg').write_text(svg(b,height,'Calendario de contribuciones de GitHub'),encoding='utf-8')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--fetch',action='store_true'); args=parser.parse_args()
    if args.fetch: fetch()
    card(); heatmap()
