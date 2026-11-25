"""Local-first, read-only website audit CLI."""
import argparse, json, html, time, urllib.request, urllib.parse, sys
from html.parser import HTMLParser
from pathlib import Path

class Page(HTMLParser):
    def __init__(self):
        super().__init__(); self.tags=[]; self.title=''; self.in_title=False
    def handle_starttag(self, tag, attrs):
        self.tags.append((tag,dict(attrs))); self.in_title = True if tag=='title' else self.in_title
    def handle_endtag(self, tag):
        if tag=='title': self.in_title=False
    def handle_data(self,data):
        if self.in_title: self.title+=data
    def all(self,tag): return [a for t,a in self.tags if t==tag]

def audit(source, url, headers=None):
    p=Page(); p.feed(source); checks=[]
    def check(id,category,ok,evidence,fix):
        checks.append(dict(id=id,category=category,status='pass' if ok else 'fail',evidence=evidence,fix=fix))
    metas={a.get('name','').lower():a.get('content','') for a in p.all('meta')}
    canon=[a.get('href','') for a in p.all('link') if 'canonical' in a.get('rel','').lower().split()]
    check('title','SEO',bool(p.title.strip()),p.title.strip() or 'Missing','Add a descriptive, unique title element.')
    check('description','SEO',bool(metas.get('description','').strip()),metas.get('description') or 'Missing','Add a page-specific meta description.')
    check('canonical','SEO',len(canon)==1 and urllib.parse.urlsplit(canon[0]).scheme in ('http','https'),str(canon),'Add one absolute canonical URL pointing to the preferred page.')
    check('h1','SEO',len(p.all('h1'))==1,str(len(p.all('h1')))+' H1 elements','Use one clear primary H1 heading (editorial heuristic).')
    check('indexability','SEO','noindex' not in (metas.get('robots','')+' '+metas.get('googlebot','')+' '+(headers or {}).get('x-robots-tag','')).lower(),'Inspect robots directives','Remove noindex only if the page is intended for indexing.')
    check('language','Accessibility',any(a.get('lang','').strip() for a in p.all('html')),'HTML language attribute','Set the correct lang attribute on HTML.')
    missing=sum('alt' not in a for a in p.all('img'))
    check('image-alt','Accessibility',missing==0,f'{missing} images lack alt attributes','Add meaningful alt text or empty alt for decorative images.')
    check('viewport','Mobile',bool(metas.get('viewport')),'Viewport metadata','Add width=device-width, initial-scale=1 viewport metadata.')
    check('https','Security',urllib.parse.urlsplit(url).scheme=='https',url,'Serve the public page over HTTPS.')
    mixed=sum(str(a.get(k,'')).startswith('http://') for t,a in p.tags for k in (('src',) if t in ('script','img','iframe','audio','video','source') else ('href',) if t=='link' else ()))
    check('mixed-content','Security',mixed==0 or not url.startswith('https:'),f'{mixed} HTTP asset references','Replace insecure resource URLs with HTTPS equivalents.')
    if headers is not None:
        for key,fix in [('content-security-policy','Design and test a Content Security Policy.'),('x-content-type-options','Set X-Content-Type-Options: nosniff.'),('referrer-policy','Set an appropriate Referrer-Policy.')]:
            check(key,'Security',bool(headers.get(key)),headers.get(key,'Missing'),fix)
    return dict(url=url,score=round(100*sum(c['status']=='pass' for c in checks)/len(checks)),checks=checks,limitations='Static HTML heuristics only; not a ranking prediction, vulnerability scan, rendered accessibility audit or Core Web Vitals measurement.')

def fetch(url):
    u=urllib.parse.urlsplit(url)
    if u.scheme not in ('http','https') or not u.hostname or u.username or u.password: raise ValueError('Use an HTTP(S) URL without credentials')
    req=urllib.request.Request(url,headers={'User-Agent':'PagePatch/0.1 (local audit)'})
    start=time.monotonic()
    with urllib.request.urlopen(req,timeout=15) as r:
        if r.headers.get_content_type() not in ('text/html','application/xhtml+xml'): raise ValueError('Expected HTML')
        data=r.read(2_000_001)
        if len(data)>2_000_000: raise ValueError('HTML exceeds 2 MB')
        result=audit(data.decode(r.headers.get_content_charset() or 'utf-8',errors='replace'),r.geturl(),{k.lower():v for k,v in r.headers.items()})
        result['response_ms']=round((time.monotonic()-start)*1000); result['html_bytes']=len(data); result['http_status']=r.status
        return result

def markdown(r):
    return '# PagePatch audit\n\nURL: '+r['url']+'\n\nHeuristic score: '+str(r['score'])+'/100\n\n'+r['limitations']+'\n\n## Fix plan\n\n'+'\n'.join('- '+c['id']+': '+c['fix']+' Evidence: '+c['evidence'].replace('\n',' ') for c in r['checks'] if c['status']=='fail')+'\n'

def dashboard(r):
    e=lambda x:html.escape(str(x))
    rows=''.join('<tr><td>'+e(c['category'])+'</td><td>'+e(c['id'])+'</td><td class="'+c['status']+'">'+e(c['status'].upper())+'</td><td>'+e(c['evidence'])+'</td><td>'+e(c['fix'])+'</td></tr>' for c in r['checks'])
    return '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>PagePatch audit</title><style>body{font:16px system-ui;background:#f1f5f9;color:#17263a;margin:0}main{max-width:1100px;margin:auto;padding:32px 20px}header{background:#14283f;color:white;padding:32px;border-radius:18px}h1{margin:0}strong{font-size:54px}section{background:white;border-radius:16px;padding:24px;margin-top:20px;overflow:auto}table{border-collapse:collapse;width:100%;font-size:14px}td,th{text-align:left;padding:12px;border-bottom:1px solid #e2e8f0;vertical-align:top}.pass{color:#16734b}.fail{color:#b93824}pre{white-space:pre-wrap;overflow-wrap:anywhere}button{padding:10px 16px;border:0;background:#176a67;color:white;border-radius:8px;cursor:pointer}</style><main><header><h1>PagePatch / Audit report</h1><p>'''+e(r['url'])+'''</p><strong>'''+str(r['score'])+'''/100</strong><p>Static checks · heuristic score</p></header><section><h2>Findings</h2><table><thead><tr><th>Area</th><th>Check</th><th>Status</th><th>Evidence</th><th>Recommended action</th></tr></thead><tbody>'''+rows+'''</tbody></table></section><section><h2>Copy-ready fix plan</h2><button onclick="navigator.clipboard.writeText(document.getElementById('plan').textContent).then(()=>this.textContent='Copied').catch(()=>this.textContent='Select and copy manually')">Copy plan</button><pre id="plan">'''+e(markdown(r))+'''</pre></section><p>'''+e(r['limitations'])+'''</p></main></html>'''

def main():
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument('url'); ap.add_argument('--file',type=Path,help='Audit local HTML instead of fetching URL'); ap.add_argument('--format',choices=['json','markdown','html'],default='markdown'); ap.add_argument('--output',type=Path); ap.add_argument('--min-score',type=int,choices=range(101),metavar='0-100'); a=ap.parse_args()
    try:
        r=audit(a.file.read_text(encoding='utf-8'),a.url) if a.file else fetch(a.url)
        text={'json':lambda r:json.dumps(r,indent=2),'markdown':markdown,'html':dashboard}[a.format](r)
        if a.output:
            with a.output.open('x',encoding='utf-8') as f:f.write(text)
        else: print(text)
        return 1 if a.min_score is not None and r['score']<a.min_score else 0
    except Exception as exc: print(f'PagePatch: {exc}',file=sys.stderr); return 2
if __name__=='__main__': sys.exit(main())
