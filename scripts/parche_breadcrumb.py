# -*- coding: utf-8 -*-
"""Parche unico: anade BreadcrumbList (con itemListElement) a las paginas de post."""
import io, sys

PATH = 'scripts/build.py'
src = io.open(PATH, encoding='utf-8').read()

if 'BreadcrumbList' in src:
    print('ya parcheado')
    sys.exit(0)

old = """        if p['og_image']:
            schema['image'] = DOMAIN + p['og_image']
        extra = f\"\"\"<meta property="og:title" content="{p['title']}">"""

new = """        if p['og_image']:
            schema['image'] = DOMAIN + p['og_image']
        cat_bc = next((c['name'] for c in p['categories'] if c['name'] not in ('Sin categoría', 'Software Medico')), 'Noticias')
        breadcrumb = json.dumps({
            '@context': 'https://schema.org', '@type': 'BreadcrumbList',
            'itemListElement': [
                {'@type': 'ListItem', 'position': 1, 'name': 'Inicio', 'item': DOMAIN + '/'},
                {'@type': 'ListItem', 'position': 2, 'name': cat_bc, 'item': f'{DOMAIN}/categoria/{slugify(cat_bc)}/'},
                {'@type': 'ListItem', 'position': 3, 'name': p['title'], 'item': canonical},
            ],
        }, ensure_ascii=False)
        extra = f\"\"\"<script type="application/ld+json">{breadcrumb}</script>
<meta property="og:title" content="{p['title']}">"""

assert old in src, 'patron no encontrado'
src = src.replace(old, new, 1)
io.open(PATH, 'w', encoding='utf-8').write(src)

import ast
ast.parse(src)
print('parche aplicado y sintaxis verificada')
