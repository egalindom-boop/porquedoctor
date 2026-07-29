# -*- coding: utf-8 -*-
"""Bot diario de porquedoctor.com: genera un articulo de salud con la API de Claude.

Marcadores de seccion inmunes a errores de escape JSON:
===TITULO=== ===SLUG=== ===DESCRIPCION=== ===CUERPO=== ===FIN===
"""
import json, os, re, sys, time, unicodedata
import urllib.request
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API_KEY = os.environ.get('ANTHROPIC_API_KEY')
MODEL = 'claude-sonnet-4-5'

LINKS = {
    'dricloud': 'Incluye de forma natural UN enlace: <a href="https://dricloud.com" target="_blank" rel="noopener">software médico DriCloud</a> (o con anchor "programa médico" o "software para clínicas").',
    'xdentalcloud': 'Incluye de forma natural UN enlace: <a href="https://xdentalcloud.com" target="_blank" rel="noopener">software dental XDentalCloud</a> (o con anchor "gestión dental").',
    'gestiondental': 'Incluye de forma natural UN enlace: <a href="https://gestiondental.org" target="_blank" rel="noopener">gestión dental</a>.',
    'gestionmedica': 'Incluye de forma natural UN enlace: <a href="https://gestionmedica.org" target="_blank" rel="noopener">gestión de clínicas médicas</a>.',
    'mejorsoftware': 'Incluye de forma natural UN enlace: <a href="https://mejorsoftware.org/software-clinicas/" target="_blank" rel="noopener">comparador de software para clínicas</a>.',
    'palmbeach': 'El artículo debe tocar el estilo de vida saludable en Florida/EEUU e incluir de forma natural UN enlace: <a href="https://palmbeachestatesmls.com" target="_blank" rel="noopener">casas en Palm Beach, Florida</a>.',
}


def slugify(text):
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')


def elegir_tema():
    lineas = [l.strip() for l in open(os.path.join(ROOT, 'temas.txt'), encoding='utf-8')
              if l.strip() and not l.startswith('#')]
    usados_path = os.path.join(ROOT, 'temas_usados.json')
    usados = json.load(open(usados_path, encoding='utf-8')) if os.path.exists(usados_path) else []
    pendientes = [l for l in lineas if l not in usados]
    if not pendientes:
        usados, pendientes = [], lineas
    linea = pendientes[0]
    usados.append(linea)
    json.dump(usados, open(usados_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    partes = [x.strip() for x in linea.split('|')]
    cat = partes[0]
    tema = partes[1]
    link = partes[2] if len(partes) > 2 and partes[2] else ''
    return cat, tema, link


def llamar_claude(cat, tema, link):
    instruccion_link = LINKS.get(link, 'No incluyas enlaces externos.')
    prompt = f"""Eres redactor/a de "Por qué Doctor" (porquedoctor.com), una revista de salud online en español activa desde 2013.
Escribe un artículo NUEVO y ORIGINAL para la categoría {cat} sobre: {tema}

Estilo de la revista:
- Español de España, tono divulgativo, cercano y riguroso; explica los términos médicos la primera vez.
- Entre 700 y 1000 palabras, con subtítulos <h2> útiles (síntomas, causas, consejos, cuándo consultar...).
- Usa <p>, <h2>, <ul>/<li> y <strong>. NO uses <h1>, imágenes ni scripts.
- {instruccion_link}
- Cierra recordando que el contenido es divulgativo y no sustituye la consulta con un profesional sanitario.

Responde EXACTAMENTE en este formato, sin nada antes ni después:
===TITULO===
(título atractivo, máximo 70 caracteres, sin comillas)
===SLUG===
(slug-en-minusculas-con-guiones, máximo 8 palabras)
===DESCRIPCION===
(meta descripción de 140-155 caracteres)
===CUERPO===
(el artículo completo en HTML)
===FIN===
"""
    body = json.dumps({'model': MODEL, 'max_tokens': 4000,
                       'messages': [{'role': 'user', 'content': prompt}]}).encode('utf-8')
    req = urllib.request.Request('https://api.anthropic.com/v1/messages', data=body, headers={
        'x-api-key': API_KEY, 'anthropic-version': '2023-06-01', 'content-type': 'application/json'})
    with urllib.request.urlopen(req, timeout=180) as r:
        return json.loads(r.read().decode('utf-8'))['content'][0]['text']


def extraer(t, a, b):
    m = re.search(re.escape(f'==={a}===') + r'(.*?)' + re.escape(f'==={b}==='), t, re.S)
    return m.group(1).strip() if m else None


def generar():
    cat, tema, link = elegir_tema()
    print(f'Tema [{cat}]: {tema} (link: {link or "ninguno"})')
    for intento in range(1, 4):
        try:
            texto = llamar_claude(cat, tema, link)
            titulo = extraer(texto, 'TITULO', 'SLUG')
            slug = extraer(texto, 'SLUG', 'DESCRIPCION')
            desc = extraer(texto, 'DESCRIPCION', 'CUERPO')
            cuerpo = extraer(texto, 'CUERPO', 'FIN')
            if not all([titulo, slug, desc, cuerpo]):
                raise ValueError('Faltan secciones')
            if len(cuerpo) < 500 or '<p>' not in cuerpo:
                raise ValueError('Cuerpo corto o sin <p>')
            if 'xclinics' in (titulo + cuerpo).lower():
                raise ValueError('Contenido no permitido')
            slug = slugify(slug)[:80]
            break
        except Exception as e:
            print(f'Intento {intento} fallido: {e}')
            if intento == 3:
                sys.exit(1)
            time.sleep(20)

    posts_path = os.path.join(ROOT, 'posts.json')
    posts = json.load(open(posts_path, encoding='utf-8'))
    existentes = {p['slug'] for p in posts}
    base, i = slug, 2
    while slug in existentes:
        slug = f'{base}-{i}'
        i += 1
    ahora = datetime.utcnow()
    posts.append({
        'id': f'bot-{ahora.strftime("%Y%m%d%H%M")}',
        'title': titulo, 'slug': slug,
        'postdate': ahora.strftime('%Y-%m-%d %H:%M:%S'),
        'status': 'publish', 'author': 'Redacción Por qué Doctor',
        'content': cuerpo, 'excerpt': desc,
        'categories': [{'name': cat, 'slug': slugify(cat)}], 'tags': [],
    })
    json.dump(posts, open(posts_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'Post añadido: {titulo} -> /{slug}/ [{cat}]')


if __name__ == '__main__':
    if not API_KEY:
        print('Falta ANTHROPIC_API_KEY')
        sys.exit(1)
    generar()
