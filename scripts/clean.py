import re
import unicodedata

def slugify(text):
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', '-', text)
    return text.strip('-')

BLOCK_TAGS = [
    'table','thead','tfoot','caption','col','colgroup','tbody','tr','td','th',
    'div','ul','ol','li','pre','form','blockquote','address','h1','h2','h3','h4','h5','h6',
    'fieldset','legend','section','article','aside','header','footer','nav','figure','figcaption',
    'iframe','script','style','details','summary','hr','p'
]

def wpautop(text):
    text = text.strip()
    if not text:
        return ''
    chunks = re.split(r'\n\s*\n+', text)
    out = []
    for chunk in chunks:
        c = chunk.strip()
        if not c:
            continue
        m = re.match(r'<\s*([a-zA-Z0-9]+)', c)
        if m and m.group(1).lower() in BLOCK_TAGS:
            out.append(c)
        else:
            c2 = re.sub(r'\n', '<br>\n', c)
            out.append(f'<p>{c2}</p>')
    return '\n\n'.join(out)


def extract_youtube_id(block):
    m = re.search(r'youtube\.com/(?:v|embed)/([a-zA-Z0-9_-]{6,15})', block)
    if m:
        return m.group(1)
    m = re.search(r'[?&]v=([a-zA-Z0-9_-]{6,15})', block)
    if m:
        return m.group(1)
    return None


DEAD_VIDEOS = {'I8zG0Oj5Li8'}  # videos eliminados de YouTube


def replace_video_embeds(html):
    # existing iframe youtube/vimeo embeds -> normalize to responsive wrapper (do this
    # BEFORE the <object> pass below, since that pass also emits <iframe> tags and we
    # don't want to double-wrap those)
    def iframe_repl(m):
        block = m.group(0)
        if 'youtube' not in block.lower() and 'vimeo' not in block.lower():
            return block
        vid = extract_youtube_id(block)
        if vid in DEAD_VIDEOS:
            return ''
        if vid:
            return (f'<div class="video-embed"><iframe src="https://www.youtube.com/embed/{vid}" '
                    f'title="Video" loading="lazy" allowfullscreen '
                    f'referrerpolicy="strict-origin-when-cross-origin"></iframe></div>')
        src_m = re.search(r'src="([^"]+)"', block)
        src = src_m.group(1) if src_m else ''
        return f'<div class="video-embed"><iframe src="{src}" title="Video" loading="lazy" allowfullscreen></iframe></div>'
    html = re.sub(r'<iframe[^>]*>.*?</iframe>', iframe_repl, html, flags=re.S | re.I)
    html = re.sub(r'<iframe[^>]*/>', iframe_repl, html, flags=re.I)

    # old-style <object>...</object> flash embeds
    def obj_repl(m):
        block = m.group(0)
        vid = extract_youtube_id(block)
        if not vid or vid in DEAD_VIDEOS:
            return ''
        return (f'<div class="video-embed"><iframe src="https://www.youtube.com/embed/{vid}" '
                f'title="Video" loading="lazy" allowfullscreen '
                f'referrerpolicy="strict-origin-when-cross-origin"></iframe></div>')
    html = re.sub(r'<object[^>]*>.*?</object>', obj_repl, html, flags=re.S | re.I)

    return html


def process_images(html, available_images, used_images):
    placeholders = []

    # 1. Handle [caption ...]...[/caption] shortcodes -> stash as placeholder tokens
    # so later blanket <img> handling doesn't re-wrap them.
    def caption_repl(m):
        inner = m.group(1)
        img_m = re.search(r'<img[^>]+>', inner)
        if not img_m:
            return ''
        img_tag = img_m.group(0)
        caption_text = inner[img_m.end():].strip()
        caption_text = re.sub(r'^</a>', '', caption_text).strip()
        caption_text = re.sub(r'<[^>]+>', '', caption_text).strip()
        new_img = rewrite_img_tag(img_tag, available_images, used_images)
        if not new_img:
            return ''
        if caption_text:
            block = f'<figure class="post-figure">{new_img}<figcaption>{caption_text}</figcaption></figure>'
        else:
            block = f'<figure class="post-figure">{new_img}</figure>'
        placeholders.append(block)
        return f'@@FIGURE{len(placeholders)-1}@@'

    html = re.sub(r'\[caption[^\]]*\](.*?)\[/caption\]', caption_repl, html, flags=re.S | re.I)

    # 2. Strip <a> wrappers that only wrap an <img>
    html = re.sub(r'<a\s+[^>]*href="[^"]*"[^>]*>\s*(<img[^>]+>)\s*</a>', r'\1', html, flags=re.I)

    # 3. Rewrite remaining bare <img> tags and wrap standalone ones in <figure>
    def bare_img_repl(m):
        img_tag = m.group(0)
        new_img = rewrite_img_tag(img_tag, available_images, used_images)
        if not new_img:
            return ''
        return f'<figure class="post-figure">{new_img}</figure>'

    html = re.sub(r'<img[^>]+>', bare_img_repl, html, flags=re.I)

    # 4. restore caption figures
    for i, block in enumerate(placeholders):
        html = html.replace(f'@@FIGURE{i}@@', block)

    return html


def rewrite_img_tag(img_tag, available_images, used_images):
    src_m = re.search(r'src="([^"]+)"', img_tag)
    if not src_m:
        return None
    src = src_m.group(1)
    basename = src.split('/')[-1].split('?')[0]
    if basename not in available_images:
        return None
    used_images.add(basename)
    stem, dot, ext = basename.rpartition('.')
    web_name = f'{stem}.webp' if ext.lower() in ('jpg', 'jpeg', 'png') else basename
    alt_m = re.search(r'alt="([^"]*)"', img_tag)
    alt = alt_m.group(1) if alt_m else ''
    return (f'<img src="/images/{web_name}" alt="{alt}" loading="lazy" decoding="async" class="post-img">')


def clean_content(html, available_images, used_images):
    html = html.replace('<!--more-->', '')
    # strip div/span/font editor artifacts (legacy WP classic-editor cruft)
    html = re.sub(r'<div[^>]*>\s*', '', html, flags=re.I)
    html = re.sub(r'</div>', '', html, flags=re.I)
    # unwrap span/font keeping inner text
    for _ in range(4):
        html = re.sub(r'<span[^>]*>(.*?)</span>', r'\1', html, flags=re.S | re.I)
        html = re.sub(r'<font[^>]*>(.*?)</font>', r'\1', html, flags=re.S | re.I)
    # &nbsp; -> space
    html = html.replace('&nbsp;', ' ')
    # internal links -> relative (keep SEO juice in-site)
    html = re.sub(r'href="https?://(?:www\.)?porquedoctor\.com/?([^"]*)"', r'href="/\1"', html)
    html = replace_video_embeds(html)
    html = process_images(html, available_images, used_images)
    # strip inline styles/attributes from paragraphs and headings
    html = re.sub(r'<(p|h[1-6]|li|ul|ol|blockquote)\s+[^>]*>', r'<\1>', html, flags=re.I)
    html = wpautop(html)
    # drop empty/whitespace-only paragraphs (e.g. leftover spacers)
    html = re.sub(r'<p[^>]*>(?:&nbsp;|\s|<br\s*/?>)*</p>', '', html, flags=re.I)
    html = re.sub(r'\n{3,}', '\n\n', html)
    return html.strip()


def make_excerpt(content_html, max_len=200):
    text = re.sub(r'<[^>]+>', ' ', content_html)
    text = re.sub(r'\s+', ' ', text).strip()
    if len(text) > max_len:
        text = text[:max_len].rsplit(' ', 1)[0] + '…'
    return text


MESES = ['enero','febrero','marzo','abril','mayo','junio','julio','agosto',
         'septiembre','octubre','noviembre','diciembre']

def format_date_es(dt):
    return f"{dt.day} de {MESES[dt.month-1]} de {dt.year}"
