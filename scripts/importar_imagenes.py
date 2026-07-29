# -*- coding: utf-8 -*-
"""Descarga una vez las imagenes originales del manifest a raw_images/ (se ejecuta en GitHub Actions)."""
import json, os, sys, time, urllib.request, urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEST = os.path.join(ROOT, 'raw_images')
os.makedirs(DEST, exist_ok=True)

urls = json.load(open(os.path.join(ROOT, 'imagenes_manifest.json')))
ok = fail = skip = 0
for u in urls:
    base = urllib.parse.unquote(u.split('/')[-1])
    dest = os.path.join(DEST, base)
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        skip += 1
        continue
    # codificar caracteres no ascii del path
    parts = u.split('/')
    safe = '/'.join(parts[:3]) + '/' + '/'.join(urllib.parse.quote(p) for p in parts[3:])
    try:
        req = urllib.request.Request(safe, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=60) as r:
            data = r.read()
        if len(data) < 100:
            raise ValueError('vacio')
        open(dest, 'wb').write(data)
        ok += 1
    except Exception as e:
        print('FALLO', base, e)
        fail += 1
    if 'web.archive.org' in u:
        time.sleep(1)
print(f'descargadas {ok}, ya existian {skip}, fallos {fail}')
