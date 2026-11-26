#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Сборка книги «Доминанта» из markdown-глав в валидный EPUB (только stdlib)."""
import os, re, html, zipfile, uuid, datetime

CHAPTERS_DIR = r"D:\Knowledge\Vault\90-Projects\доминанта-экосистема\книга"
OUT_EPUB = r"D:\Knowledge\Vault\90-Projects\доминанта-экосистема\Доминанта-книга.epub"
TITLE = "Доминанта: от физиологии внимания к логике мыслящего агента"
AUTHOR = "Экосистема «Доминанта»"
LANG = "ru"
SKIP = {"00-титул-и-оглавление.md"}

def inline(text: str) -> str:
    text = html.escape(text, quote=False)
    # links [text](url)
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)
    # bold **x**
    text = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', text)
    # italic *x*
    text = re.sub(r'(?<!\*)\*([^*\n]+)\*(?!\*)', r'<em>\1</em>', text)
    # code `x`
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    # wikilinks [[x]]
    text = re.sub(r'\[\[([^\]]+)\]\]', r'<span class="wl">\1</span>', text)
    return text

def convert(md: str) -> str:
    lines = md.splitlines()
    out = []
    i = 0
    in_quote = False
    in_list = None  # 'ul' or 'ol'
    in_table = False
    # strip frontmatter
    if lines and lines[0].strip() == '---':
        j = 1
        while j < len(lines) and lines[j].strip() != '---':
            j += 1
        lines = lines[j+1:]
    while i < len(lines):
        line = lines[i]
        s = line.strip()
        if not s:
            if in_list:
                out.append(f"</{in_list}>"); in_list = None
            if in_table:
                out.append("</table>"); in_table = False
            if in_quote:
                out.append("</blockquote>"); in_quote = False
            i += 1
            continue
        # heading
        m = re.match(r'^(#{1,6})\s+(.*)$', s)
        if m:
            if in_list:
                out.append(f"</{in_list}>"); in_list = None
            if in_table:
                out.append("</table>"); in_table = False
            if in_quote:
                out.append("</blockquote>"); in_quote = False
            lvl = len(m.group(1))
            out.append(f"<h{min(lvl+1,6)}>{inline(m.group(2))}</h{min(lvl+1,6)}>")
            i += 1
            continue
        # blockquote
        if s.startswith('>'):
            if in_list:
                out.append(f"</{in_list}>"); in_list = None
            if in_table:
                out.append("</table>"); in_table = False
            if not in_quote:
                out.append("<blockquote>"); in_quote = True
            out.append(f"<p>{inline(s.lstrip('>').strip())}</p>")
            i += 1
            continue
        # table
        if s.startswith('|') and i + 1 < len(lines) and re.match(r'^\|[\s\-:|]+\|?$', lines[i+1].strip()):
            if in_list:
                out.append(f"</{in_list}>"); in_list = None
            if in_quote:
                out.append("</blockquote>"); in_quote = False
            header = [c.strip() for c in s.strip().strip('|').split('|')]
            out.append("<table>")
            out.append("<tr>" + "".join(f"<th>{inline(c)}</th>" for c in header) + "</tr>")
            i += 2
            in_table = True
            while i < len(lines) and lines[i].strip().startswith('|'):
                cells = [c.strip() for c in lines[i].strip().strip('|').split('|')]
                out.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in cells) + "</tr>")
                i += 1
            out.append("</table>"); in_table = False
            continue
        # ul
        m = re.match(r'^[-*•]\s+(.*)$', s)
        if m:
            if in_table:
                out.append("</table>"); in_table = False
            if in_quote:
                out.append("</blockquote>"); in_quote = False
            if in_list != 'ul':
                if in_list: out.append(f"</{in_list}>")
                out.append("<ul>"); in_list = 'ul'
            out.append(f"<li>{inline(m.group(1))}</li>")
            i += 1
            continue
        # ol
        m = re.match(r'^\d+[.)]\s+(.*)$', s)
        if m:
            if in_table:
                out.append("</table>"); in_table = False
            if in_quote:
                out.append("</blockquote>"); in_quote = False
            if in_list != 'ol':
                if in_list: out.append(f"</{in_list}>")
                out.append("<ol>"); in_list = 'ol'
            out.append(f"<li>{inline(m.group(1))}</li>")
            i += 1
            continue
        # paragraph
        if in_list:
            out.append(f"</{in_list}>"); in_list = None
        if in_table:
            out.append("</table>"); in_table = False
        if in_quote:
            out.append("</blockquote>"); in_quote = False
        out.append(f"<p>{inline(s)}</p>")
        i += 1
    if in_list: out.append(f"</{in_list}>")
    if in_table: out.append("</table>")
    if in_quote: out.append("</blockquote>")
    return "\n".join(out)

def main():
    files = sorted(f for f in os.listdir(CHAPTERS_DIR) if f.endswith('.md') and f not in SKIP)
    chapters = []
    for f in files:
        p = os.path.join(CHAPTERS_DIR, f)
        with open(p, encoding='utf-8') as fh:
            md = fh.read()
        body = convert(md)
        chapters.append((f, body))
    uid = "urn:uuid:" + str(uuid.uuid4())
    now = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    css = "body{font-family:serif;line-height:1.6;margin:1.2em;max-width:42em}\n" \
          "h1,h2,h3,h4{line-height:1.25}\nblockquote{border-left:4px solid #999;margin-left:0;padding-left:1em;color:#444}\n" \
          "table{border-collapse:collapse}th,td{border:1px solid #999;padding:.3em .6em;text-align:left}\n" \
          "code{background:#f2f2f2;padding:.1em .3em;border-radius:3px}a{color:#2563eb}.wl{color:#666}"
    manifest_items = []
    spine_items = []
    for idx, (f, body) in enumerate(chapters, 1):
        cid = f"ch{idx}"
        manifest_items.append(f'<item id="{cid}" href="{cid}.xhtml" media-type="application/xhtml+xml"/>')
        spine_items.append(f'<itemref idref="{cid}"/>')
    manifest = "\n".join(manifest_items)
    spine = "\n".join(spine_items)

    nav_li = []
    for idx, (f, body) in enumerate(chapters, 1):
        title = f[:-3]
        title = re.sub(r'^\d+\-', '', title).replace('-', ' ').strip()
        nav_li.append(f'<li><a href="ch{idx}.xhtml">{html.escape(title)}</a></li>')

    container = '<?xml version="1.0" encoding="UTF-8"?>\n' \
        '<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">\n' \
        '  <rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/></rootfiles>\n' \
        '</container>'

    content_opf = f'''<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="uid">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="uid">{uid}</dc:identifier>
    <dc:title>{html.escape(TITLE)}</dc:title>
    <dc:language>{LANG}</dc:language>
    <dc:creator>{html.escape(AUTHOR)}</dc:creator>
    <meta property="dcterms:modified">{now}</meta>
  </metadata>
  <manifest>
    <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>
    <item id="css" href="style.css" media-type="text/css"/>
{manifest}
  </manifest>
  <spine>
{spine}
  </spine>
</package>'''

    nav = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="{LANG}" lang="{LANG}">
<head><title>{html.escape(TITLE)}</title><link rel="stylesheet" href="style.css"/></head>
<body>
<nav epub:type="toc"><h1>Оглавление</h1><ol>
{chr(10).join(nav_li)}
</ol></nav>
</body></html>'''

    with zipfile.ZipFile(OUT_EPUB, 'w') as z:
        z.writestr('mimetype', 'application/epub+zip', compress_type=zipfile.ZIP_STORED)
        z.writestr('META-INF/container.xml', container)
        z.writestr('OEBPS/content.opf', content_opf)
        z.writestr('OEBPS/nav.xhtml', nav)
        z.writestr('OEBPS/style.css', css)
        for idx, (f, body) in enumerate(chapters, 1):
            title = html.escape(re.sub(r'^\d+\-', '', f[:-3]).replace('-', ' ').strip())
            xhtml = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="{LANG}" lang="{LANG}">
<head><title>{title}</title><link rel="stylesheet" href="style.css"/></head>
<body>
{body}
</body></html>'''
            z.writestr(f"OEBPS/ch{idx}.xhtml", xhtml)
    print(f"OK: {OUT_EPUB}")
    print(f"chapters: {len(chapters)}")
    for f, _ in chapters:
        print(" -", f)

if __name__ == '__main__':
    main()
