# -*- coding: utf-8 -*-
"""Generador estatico de porquedoctor.com (revista de salud)."""
import json, os, re, shutil, sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))
from clean import clean_content, make_excerpt, format_date_es, slugify

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.environ.get('SITE_OUT', os.path.join(ROOT, 'site'))
RAW_IMAGES = os.path.join(ROOT, 'raw_images')
DOMAIN = 'https://porquedoctor.com'

CAT_ORDER = ['Noticias','Embarazo','Pediatría','Estética','Antiaging','Dietética','Naturopatía',
             'Cirugía','Odontología','Psicología','Sexología','Deporte','Fisioterapia','Dermatología']

CSS = r"""
:root{--rojo:#b32112;--rojo2:#8f1a0e;--tinta:#1e2328;--suave:#5c6570;--linea:#e5e2de;--fondo:#f6f5f3;--blanco:#fff;--max:1180px}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'PT Sans',system-ui,sans-serif;color:var(--tinta);background:var(--fondo);line-height:1.65;font-size:16.5px}
h1,h2,h3,h4{font-family:'Oswald','PT Sans',sans-serif;font-weight:500;line-height:1.2}
a{color:var(--rojo);text-decoration:none}
a:hover{text-decoration:underline}
img{max-width:100%;height:auto}
.container{max-width:var(--max);margin:0 auto;padding:0 20px}
.topbar{background:#1e2328;color:#cfd4d9;font-size:.82rem}
.topbar .container{display:flex;justify-content:space-between;flex-wrap:wrap}
.topbar a{color:#cfd4d9;padding:8px 10px;display:inline-block}
.topbar a:hover{color:#fff;text-decoration:none}
.masthead{background:linear-gradient(135deg,var(--rojo) 0%,var(--rojo2) 100%);padding:28px 0}
.masthead .brand{color:#fff;font-family:'Oswald',sans-serif;font-size:2.3rem;letter-spacing:.01em}
.masthead .brand a{color:#fff;text-decoration:none}
.masthead .tag{color:#ffd9d2;font-size:.95rem;letter-spacing:.28em;text-transform:uppercase;margin-top:2px}
.mainnav{background:#14171a}
.mainnav .container{display:flex;flex-wrap:wrap}
.mainnav a{color:#e8e8e8;font-family:'Oswald',sans-serif;font-size:.85rem;text-transform:uppercase;letter-spacing:.06em;padding:13px 14px;display:inline-block}
.mainnav a:hover,.mainnav a.act{background:var(--rojo);color:#fff;text-decoration:none}
.layout{display:grid;grid-template-columns:minmax(0,1fr) 320px;gap:36px;padding:36px 0}
@media(max-width:920px){.layout{grid-template-columns:1fr}}
.card{background:var(--blanco);border:1px solid var(--linea);border-radius:8px;overflow:hidden;margin-bottom:22px}
.card .thumb{display:block;aspect-ratio:16/8.5;overflow:hidden;background:#e9e7e4}
.card .thumb img{width:100%;height:100%;object-fit:cover;display:block}
.card .body{padding:20px 24px}
.cat-pill{display:inline-block;background:var(--rojo);color:#fff;font-family:'Oswald',sans-serif;font-size:.72rem;text-transform:uppercase;letter-spacing:.08em;padding:3px 10px;border-radius:3px;margin-bottom:10px}
a.cat-pill:hover{text-decoration:none;background:var(--rojo2)}
.card h2{font-size:1.45rem;margin-bottom:6px}
.card h2 a{color:var(--tinta)}
.card h2 a:hover{color:var(--rojo);text-decoration:none}
.meta{font-size:.82rem;color:var(--suave);margin-bottom:10px}
.excerpt{color:var(--suave);font-size:.95rem}
.leer{display:inline-block;margin-top:10px;font-family:'Oswald',sans-serif;font-size:.82rem;text-transform:uppercase;letter-spacing:.05em}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:22px}
@media(max-width:680px){.grid2{grid-template-columns:1fr}}
.grid2 .card h2{font-size:1.15rem}
.article{background:var(--blanco);border:1px solid var(--linea);border-radius:8px;padding:36px 42px}
@media(max-width:600px){.article{padding:24px 18px}}
.article h1{font-size:2rem;margin:10px 0 8px}
.article .meta{padding-bottom:16px;border-bottom:1px solid var(--linea);margin-bottom:22px}
.article-content p{margin-bottom:1.05em}
.article-content h2,.article-content h3{margin:1.4em 0 .55em;color:var(--tinta)}
.article-content ul,.article-content ol{margin:0 0 1.05em 1.4em}
.article-content a{font-weight:700}
.post-figure{margin:1.4em auto;text-align:center}
.post-figure img{border-radius:6px}
.post-figure figcaption{font-size:.82rem;color:var(--suave);margin-top:6px;font-style:italic}
.video-embed{position:relative;padding-bottom:56.25%;height:0;margin:1.4em 0;border-radius:6px;overflow:hidden}
.video-embed iframe{position:absolute;top:0;left:0;width:100%;height:100%;border:0}
.sidebar .widget{background:var(--blanco);border:1px solid var(--linea);border-radius:8px;padding:20px 22px;margin-bottom:22px}
.sidebar h3{font-size:1rem;text-transform:uppercase;letter-spacing:.06em;border-bottom:2px solid var(--rojo);padding-bottom:8px;margin-bottom:12px}
.sidebar ul{list-style:none}
.sidebar li{padding:6px 0;border-bottom:1px dashed var(--linea);font-size:.92rem}
.sidebar li:last-child{border-bottom:none}
.sidebar .num{color:var(--suave);font-size:.8rem}
.pagination{display:flex;justify-content:center;gap:8px;margin:26px 0;flex-wrap:wrap}
.pagination a,.pagination span{padding:8px 14px;border:1px solid var(--linea);border-radius:6px;background:var(--blanco);font-family:'Oswald',sans-serif;font-size:.85rem}
.pagination span.cur{background:var(--rojo);color:#fff;border-color:var(--rojo)}
.sitefoot{background:#14171a;color:#b9c0c7;margin-top:44px;padding:44px 0 96px;font-size:.92rem}
.sitefoot h4{color:#fff;font-size:.95rem;text-transform:uppercase;letter-spacing:.06em;margin-bottom:12px}
.footgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:30px}
.sitefoot ul{list-style:none}
.sitefoot li{padding:3px 0}
.sitefoot a{color:#9fb4c8}
.sitefoot a:hover{color:#fff}
.footnote{border-top:1px solid rgba(255,255,255,.14);margin-top:30px;padding-top:16px;color:#8b939b;font-size:.82rem}
.footnote a{text-decoration:underline}
#cookie-bar{position:fixed;bottom:0;left:0;right:0;background:#14171a;color:#e4edf7;padding:14px 20px;z-index:1000;box-shadow:0 -2px 14px rgba(0,0,0,.35);transform:translateY(110%);transition:transform .3s ease}
#cookie-bar.visible{transform:translateY(0)}
#cookie-bar .cb-inner{max-width:var(--max);margin:0 auto;display:flex;align-items:center;gap:18px;flex-wrap:wrap;justify-content:space-between}
#cookie-bar p{font-size:.85rem;margin:0;flex:1 1 380px}
#cookie-bar a{color:#ff9c8c;text-decoration:underline}
#cookie-bar .cb-btns{display:flex;gap:10px}
#cookie-bar button{border:0;border-radius:6px;padding:9px 20px;font-weight:700;cursor:pointer;font-size:.85rem}
#cb-accept{background:var(--rojo);color:#fff}
#cb-reject{background:transparent;color:#cfd4d9;border:1px solid #56606a}
"""

COOKIE_JS = r"""
(function(){
  var KEY='cookie-consent-pqd';
  function grant(){
    window.dataLayer=window.dataLayer||[];
    function gtag(){dataLayer.push(arguments);}
    window.gtag=window.gtag||gtag;
    gtag('consent','update',{analytics_storage:'granted'});
  }
  var v=null;
  try{v=localStorage.getItem(KEY);}catch(e){}
  if(v==='accepted'){grant();}
  else if(v!=='rejected'){var bar=document.getElementById('cookie-bar');if(bar){bar.classList.add('visible');}}
  var a=document.getElementById('cb-accept'),r=document.getElementById('cb-reject');
  if(a)a.addEventListener('click',function(){try{localStorage.setItem(KEY,'accepted');}catch(e){}grant();document.getElementById('cookie-bar').classList.remove('visible');});
  if(r)r.addEventListener('click',function(){try{localStorage.setItem(KEY,'rejected');}catch(e){}document.getElementById('cookie-bar').classList.remove('visible');});
})();
"""


def head(title, description, canonical, extra=''):
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{description}">
<link rel="canonical" href="{canonical}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Oswald:wght@400;500;600&family=PT+Sans:wght@400;700&display=optional" rel="stylesheet" media="print" onload="this.media='all'">
<noscript><link href="https://fonts.googleapis.com/css2?family=Oswald:wght@400;500;600&family=PT+Sans:wght@400;700&display=optional" rel="stylesheet"></noscript>
<style>{CSS}</style>
<link rel="alternate" type="application/rss+xml" title="Por qué Doctor RSS" href="/rss.xml">
{extra}
</head>
<body>
"""


def header_nav(active=''):
    links = ''.join(
        f'<a href="/categoria/{slugify(c)}/"{" class=act" if c == active else ""}>{c}</a>'
        for c in CAT_ORDER)
    return f"""<div class="topbar"><div class="container">
  <div><a href="/">Revista de Salud. Por qué Doctor</a></div>
  <div><a href="/equipo/">Equipo</a><a href="/publicidad/">Publicidad</a><a href="/contacto/">Contacto</a></div>
</div></div>
<header class="masthead"><div class="container">
  <div class="brand"><a href="/">Por qué Doctor…</a></div>
  <div class="tag">Tu revista de salud</div>
</div></header>
<nav class="mainnav"><div class="container"><a href="/"{" class=act" if active == 'inicio' else ''}>Inicio</a>{links}</div></nav>
"""


def sidebar(cats_counts, recent):
    cats = ''.join(f'<li><a href="/categoria/{slugify(c)}/">{c}</a> <span class="num">({n})</span></li>' for c, n in cats_counts)
    rec = ''.join(f'<li><a href="/{p["slug"]}/">{p["title"]}</a></li>' for p in recent[:6])
    return f"""<aside class="sidebar">
  <div class="widget"><h3>Categorías</h3><ul>{cats}</ul></div>
  <div class="widget"><h3>Lo último</h3><ul>{rec}</ul></div>
  <div class="widget"><h3>Recursos recomendados</h3><ul>
    <li><a href="https://dricloud.com" target="_blank" rel="noopener">Software médico DriCloud</a></li>
    <li><a href="https://xdentalcloud.com" target="_blank" rel="noopener">Software dental XDentalCloud</a></li>
    <li><a href="https://gestionmedica.org" target="_blank" rel="noopener">Gestión médica de clínicas</a></li>
    <li><a href="https://gestiondental.org" target="_blank" rel="noopener">Gestión dental</a></li>
    <li><a href="https://mejorsoftware.org/software-clinicas/" target="_blank" rel="noopener">Comparador de software para clínicas</a></li>
  </ul></div>
</aside>"""


def footer():
    return f"""<footer class="sitefoot"><div class="container">
  <div class="footgrid">
    <div>
      <h4>Por qué Doctor</h4>
      <p>Tu revista de salud desde 2013: embarazo, pediatría, estética, dietética, psicología y mucho más, escrito en un lenguaje claro para todos.</p>
    </div>
    <div>
      <h4>Legal</h4>
      <ul>
        <li><a href="/aviso-legal/">Aviso legal</a></li>
        <li><a href="/politica-de-privacidad/">Política de privacidad</a></li>
        <li><a href="/cookies/">Política de cookies</a></li>
        <li><a href="/publicidad/">Publicidad</a></li>
        <li><a href="/contacto/">Contacto</a></li>
      </ul>
    </div>
    <div>
      <h4>Tecnología sanitaria</h4>
      <ul>
        <li><a href="https://dricloud.com" target="_blank" rel="noopener">Programa médico DriCloud</a></li>
        <li><a href="https://xdentalcloud.com" target="_blank" rel="noopener">Software dental XDentalCloud</a></li>
        <li><a href="https://gestionmedica.org" target="_blank" rel="noopener">Gestión Médica</a></li>
        <li><a href="https://gestiondental.org" target="_blank" rel="noopener">Gestión Dental</a></li>
        <li><a href="https://mejorsoftware.org/software-clinicas/" target="_blank" rel="noopener">Software para clínicas</a></li>
      </ul>
    </div>
  </div>
  <div class="footnote">
    <p><strong>Protección de datos:</strong> este sitio cumple el RGPD (UE) 2016/679. Responsable: Massive Bionics LLC · luki.negocios@gmail.com. Solo usamos cookies analíticas si las aceptas expresamente. Más información en la <a href="/politica-de-privacidad/">política de privacidad</a> y la <a href="/cookies/">política de cookies</a>.</p>
    <p style="margin-top:8px">© 2013–{datetime.now().year} porquedoctor.com · Los contenidos de esta revista son divulgativos y no sustituyen el diagnóstico ni el consejo de un profesional sanitario.</p>
  </div>
</div></footer>
<div id="cookie-bar"><div class="cb-inner">
  <p>Utilizamos cookies analíticas (Google Analytics) solo si las aceptas. Puedes rechazarlas sin que afecte a la navegación. Más información en la <a href="/cookies/">política de cookies</a>.</p>
  <div class="cb-btns"><button id="cb-accept">Aceptar</button><button id="cb-reject">Rechazar</button></div>
</div></div>
<script src="/js/cookies.js" defer></script>
</body></html>"""


def first_image(html):
    m = re.search(r'src="(/images/[^"]+)"', html)
    return m.group(1) if m else None


def card(p, small=False, featured=False):
    cat = next((c['name'] for c in p['categories'] if c['name'] != 'Sin categoría'), 'Noticias')
    img = p.get('og_image')
    attrs = 'fetchpriority="high"' if featured else 'loading="lazy"'
    thumb = f'<a class="thumb" href="/{p["slug"]}/"><img src="{img}" alt="{p["title"]}" {attrs}></a>' if img else ''
    exc = '' if small else f'<p class="excerpt">{p["excerpt"][:150]}…</p>'
    return f"""<article class="card">{thumb}<div class="body">
<a class="cat-pill" href="/categoria/{slugify(cat)}/">{cat}</a>
<h2><a href="/{p['slug']}/">{p['title']}</a></h2>
<div class="meta">{p['date_es']}{' · Por ' + p['author'] if p.get('author') else ''}</div>
{exc}<a class="leer" href="/{p['slug']}/">Leer más →</a>
</div></article>"""


def build():
    posts = json.load(open(os.path.join(ROOT, 'posts.json'), encoding='utf-8'))
    pages = json.load(open(os.path.join(ROOT, 'pages_raw.json'), encoding='utf-8'))
    available = set(f for f in os.listdir(RAW_IMAGES) if not f.startswith('.') and f != '__MACOSX')
    used = set()

    legacy_redirects = []
    for p in posts:
        if not p['slug'] or re.match(r'^\d+(-\d+)?$', p['slug']):
            old = p['slug']
            p['slug'] = slugify(p['title'])
            if old:
                legacy_redirects.append((f'/{old}/', f'/{p["slug"]}/'))
        p['dt'] = datetime.strptime(p['postdate'], '%Y-%m-%d %H:%M:%S')
        p['date_es'] = format_date_es(p['dt'])
        p['clean'] = clean_content(p['content'], available, used)
        p['excerpt'] = re.sub(r'<[^>]+>', ' ', p['excerpt']).strip() or make_excerpt(p['clean'])
        p['excerpt'] = re.sub(r'\s+', ' ', p['excerpt'])
        p['og_image'] = first_image(p['clean'])
    posts.sort(key=lambda p: p['dt'], reverse=True)

    if os.path.exists(SITE):
        shutil.rmtree(SITE)
    for d in ('css', 'js', 'images', 'categoria'):
        os.makedirs(os.path.join(SITE, d), exist_ok=True)
    open(os.path.join(SITE, 'css', 'estilo.css'), 'w').write(CSS)
    open(os.path.join(SITE, 'js', 'cookies.js'), 'w').write(COOKIE_JS)
    for img in used:
        src = os.path.join(RAW_IMAGES, img)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(SITE, 'images', img))
    # logo si existe
    if os.path.exists(os.path.join(RAW_IMAGES, 'pqd.png')):
        shutil.copy2(os.path.join(RAW_IMAGES, 'pqd.png'), os.path.join(SITE, 'images', 'pqd.png'))

    from collections import Counter, defaultdict
    cat_counts = Counter()
    cat_posts = defaultdict(list)
    for p in posts:
        for c in p['categories']:
            if c['name'] in ('Sin categoría', 'Software Medico'):
                continue
            cat_counts[c['name']] += 1
            cat_posts[c['name']].append(p)
    # Software Medico posts van a Noticias
    for p in posts:
        names = [c['name'] for c in p['categories']]
        if 'Software Medico' in names and 'Noticias' not in names:
            cat_counts['Noticias'] += 1
            cat_posts['Noticias'].append(p)
    cats_sorted = [(c, cat_counts[c]) for c in CAT_ORDER if c in cat_counts]
    sb = sidebar(cats_sorted, posts)

    # ---------- portada + paginacion ----------
    PER = 12
    pages_list = [posts[i:i+PER] for i in range(0, len(posts), PER)]
    for i, pp in enumerate(pages_list):
        num = i + 1
        if num == 1:
            destacado = card(pp[0], featured=True)
            rest = ''.join(card(x, small=True) for x in pp[1:])
            cuerpo = destacado + f'<div class="grid2">{rest}</div>'
        else:
            cuerpo = f'<div class="grid2">{"".join(card(x, small=True) for x in pp)}</div>'
        pag = ['<nav class="pagination">']
        for j in range(1, len(pages_list)+1):
            href = '/' if j == 1 else f'/pagina/{j}/'
            pag.append(f'<span class="cur">{j}</span>' if j == num else f'<a href="{href}">{j}</a>')
        pag.append('</nav>')
        title = 'Por qué Doctor · Revista de Salud: embarazo, pediatría, estética, dietética y más'
        if num > 1:
            title += f' · Página {num}'
        desc = 'Revista de salud en español: embarazo, pediatría, estética, dietética, psicología, sexología, odontología y noticias médicas explicadas con claridad.'
        canonical = DOMAIN + ('/' if num == 1 else f'/pagina/{num}/')
        html = head(title, desc, canonical) + header_nav('inicio')
        html += f'<div class="container layout"><main>{cuerpo}{"".join(pag)}</main>{sb}</div>' + footer()
        out = os.path.join(SITE, 'index.html') if num == 1 else os.path.join(SITE, 'pagina', str(num), 'index.html')
        os.makedirs(os.path.dirname(out), exist_ok=True)
        open(out, 'w', encoding='utf-8').write(html)

    # ---------- posts ----------
    for idx, p in enumerate(posts):
        catlinks = ', '.join(f'<a href="/categoria/{slugify(c["name"])}/">{c["name"]}</a>'
                             for c in p['categories'] if c['name'] not in ('Sin categoría', 'Software Medico'))
        canonical = f'{DOMAIN}/{p["slug"]}/'
        og_img = f'<meta property="og:image" content="{DOMAIN}{p["og_image"]}">' if p['og_image'] else ''
        schema = {
            '@context': 'https://schema.org', '@type': 'Article',
            'headline': p['title'][:110],
            'description': p['excerpt'][:160],
            'datePublished': p['dt'].strftime('%Y-%m-%d'),
            'author': {'@type': 'Person', 'name': p.get('author') or 'Redacción Por qué Doctor'},
            'publisher': {'@type': 'Organization', 'name': 'Por qué Doctor', 'url': DOMAIN},
            'mainEntityOfPage': canonical, 'inLanguage': 'es',
        }
        if p['og_image']:
            schema['image'] = DOMAIN + p['og_image']
        extra = f"""<meta property="og:title" content="{p['title']}">
<meta property="og:description" content="{p['excerpt'][:158]}">
<meta property="og:type" content="article">
<meta property="og:url" content="{canonical}">
{og_img}
<script type="application/ld+json">{json.dumps(schema, ensure_ascii=False)}</script>"""
        nav_links = []
        if idx < len(posts) - 1:
            nav_links.append(f'<a href="/{posts[idx+1]["slug"]}/">← {posts[idx+1]["title"][:46]}</a>')
        if idx > 0:
            nav_links.append(f'<a href="/{posts[idx-1]["slug"]}/" style="margin-left:auto">{posts[idx-1]["title"][:46]} →</a>')
        prevnext = f'<nav style="display:flex;gap:18px;margin-top:30px;padding-top:16px;border-top:1px solid var(--linea);font-size:.88rem;flex-wrap:wrap">{"".join(nav_links)}</nav>'
        cat = next((c['name'] for c in p['categories'] if c['name'] not in ('Sin categoría','Software Medico')), 'Noticias')
        html = head(f"{p['title']} · Por qué Doctor", p['excerpt'][:158], canonical, extra)
        html += header_nav(cat)
        html += f"""<div class="container layout"><main><article class="article">
<a class="cat-pill" href="/categoria/{slugify(cat)}/">{cat}</a>
<h1>{p['title']}</h1>
<div class="meta">{p['date_es']}{' · Por ' + p['author'] if p.get('author') else ''} · {catlinks}</div>
<div class="article-content">{p['clean']}</div>
{prevnext}</article></main>{sb}</div>"""
        html += footer()
        d = os.path.join(SITE, p['slug'])
        os.makedirs(d, exist_ok=True)
        open(os.path.join(d, 'index.html'), 'w', encoding='utf-8').write(html)

    # ---------- categorias ----------
    for cname, cposts in cat_posts.items():
        cslug = slugify(cname)
        cuerpo = f'<div class="grid2">{"".join(card(x, small=True) for x in cposts)}</div>'
        html = head(f'{cname} · Por qué Doctor',
                    f'Artículos de {cname} en la revista de salud Por qué Doctor.',
                    f'{DOMAIN}/categoria/{cslug}/')
        html += header_nav(cname)
        html += f'<div class="container layout"><main><h1 style="margin-bottom:22px">{cname}</h1>{cuerpo}</main>{sb}</div>' + footer()
        d = os.path.join(SITE, 'categoria', cslug)
        os.makedirs(d, exist_ok=True)
        open(os.path.join(d, 'index.html'), 'w', encoding='utf-8').write(html)

    # ---------- paginas estaticas ----------
    pages_map = {p['slug']: p for p in pages}
    LEGAL = ['politica-de-privacidad', 'aviso-legal', 'cookies']
    for slug in LEGAL:
        pg = pages_map.get(slug)
        body = clean_content(pg['content'], available, used) if pg and pg['content'] else '<p>Contenido disponible próximamente.</p>'
        # actualizar responsable
        html = head(f"{pg['title']} · Por qué Doctor", pg['title'], f'{DOMAIN}/{slug}/')
        html += header_nav()
        html += f'<div class="container layout"><main><article class="article"><h1>{pg["title"]}</h1><div class="article-content">{body}</div></article></main>{sb}</div>' + footer()
        d = os.path.join(SITE, slug)
        os.makedirs(d, exist_ok=True)
        open(os.path.join(d, 'index.html'), 'w', encoding='utf-8').write(html)

    extra_pages = {
        'contacto': ('Contacto', """<p>¿Quieres proponernos un tema, colaborar con la revista o informarnos de una errata? Escríbenos:</p>
<p><strong>Email:</strong> <a href="mailto:luki.negocios@gmail.com">luki.negocios@gmail.com</a></p>
<p>Respondemos habitualmente en un plazo de 48 horas laborables.</p>"""),
        'publicidad': ('Publicidad', """<p>Por qué Doctor es una revista de salud online con más de una década de trayectoria y contenido indexado en las principales categorías de salud y bienestar.</p>
<p>Si deseas anunciarte o patrocinar contenidos, contacta con nosotros en <a href="mailto:luki.negocios@gmail.com">luki.negocios@gmail.com</a> y te enviaremos las opciones disponibles.</p>"""),
        'equipo': ('Equipo de Redacción', """<p>En Por qué Doctor colabora un equipo multidisciplinar de redactores especializados en salud, junto con profesionales sanitarios que revisan y firman artículos: medicina, odontología, psicología, fisioterapia y nutrición.</p>
<p>Los artículos tienen carácter divulgativo y no sustituyen la consulta con un profesional sanitario.</p>"""),
    }
    for slug, (title, body) in extra_pages.items():
        html = head(f'{title} · Por qué Doctor', title, f'{DOMAIN}/{slug}/')
        html += header_nav()
        html += f'<div class="container layout"><main><article class="article"><h1>{title}</h1><div class="article-content">{body}</div></article></main>{sb}</div>' + footer()
        d = os.path.join(SITE, slug)
        os.makedirs(d, exist_ok=True)
        open(os.path.join(d, 'index.html'), 'w', encoding='utf-8').write(html)

    # ---------- sitemap / robots / rss / 404 / redirects ----------
    urls = [f'{DOMAIN}/'] + [f'{DOMAIN}/{p["slug"]}/' for p in posts]
    urls += [f'{DOMAIN}/categoria/{slugify(c)}/' for c, _ in cats_sorted]
    urls += [f'{DOMAIN}/{s}/' for s in LEGAL + list(extra_pages)]
    urls += [f'{DOMAIN}/pagina/{i}/' for i in range(2, len(pages_list)+1)]
    sm = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    sm += ''.join(f'  <url><loc>{u}</loc></url>\n' for u in urls) + '</urlset>\n'
    open(os.path.join(SITE, 'sitemap.xml'), 'w').write(sm)
    open(os.path.join(SITE, 'robots.txt'), 'w').write(f'User-agent: *\nAllow: /\n\nSitemap: {DOMAIN}/sitemap.xml\n')

    rss_items = ''
    for p in posts[:20]:
        rss_items += f"""  <item><title>{p['title'].replace('&','&amp;')}</title><link>{DOMAIN}/{p['slug']}/</link><guid>{DOMAIN}/{p['slug']}/</guid><pubDate>{p['dt'].strftime('%a, %d %b %Y %H:%M:%S +0000')}</pubDate><description><![CDATA[{p['excerpt']}]]></description></item>\n"""
    open(os.path.join(SITE, 'rss.xml'), 'w', encoding='utf-8').write(
        f'<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel><title>Por qué Doctor</title><link>{DOMAIN}</link><description>Tu revista de salud</description><language>es</language>\n{rss_items}</channel></rss>\n')

    html = head('Página no encontrada · Por qué Doctor', 'Error 404', f'{DOMAIN}/404.html')
    html += header_nav()
    html += '<div class="container layout"><main><article class="article"><h1>Página no encontrada</h1><div class="article-content"><p>La página que buscas no existe o ha cambiado de dirección.</p><p><a href="/">← Volver a la portada</a></p></div></article></main></div>' + footer()
    open(os.path.join(SITE, '404.html'), 'w', encoding='utf-8').write(html)

    with open(os.path.join(SITE, '_redirects'), 'w') as f:
        f.write('/feed /rss.xml 301\n/feed/ /rss.xml 301\n/home / 301\n/home/ / 301\n')
        f.write('/xclinics-software-medico-en-la-nube/ https://dricloud.com 301\n')
        f.write('/xclinics-software-medico-en-la-nube https://dricloud.com 301\n')
        for old, new in legacy_redirects:
            f.write(f'{old} {new} 301\n')

    n = sum(len(fs) for _, _, fs in os.walk(SITE))
    print(f'Build OK: {len(posts)} posts, {len(cats_sorted)} categorias, {len(used)} imagenes usadas, {n} archivos')


if __name__ == '__main__':
    build()
