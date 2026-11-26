#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Сборка книги «Доминанта» из markdown-глав в .docx (python-docx)."""
import os, re
from docx import Document
from docx.shared import Pt, RGBColor

CHAPTERS_DIR = r"D:\Knowledge\Vault\90-Projects\доминанта-экосистема\книга"
OUT_DOCX = r"D:\Knowledge\Vault\90-Projects\доминанта-экосистема\Доминанта-книга.docx"
SKIP = {"00-титул-и-оглавление.md"}

def strip_frontmatter(lines):
    if lines and lines[0].strip() == '---':
        j = 1
        while j < len(lines) and lines[j].strip() != '---':
            j += 1
        return lines[j+1:]
    return lines

def add_runs(paragraph, text):
    # inline bold **x**
    parts = re.split(r'(\*\*[^*]+\*\*)', text)
    for p in parts:
        if p.startswith('**') and p.endswith('**'):
            r = paragraph.add_run(p[2:-2]); r.bold = True
        else:
            paragraph.add_run(p)

def build():
    doc = Document()
    doc.add_heading("ДОМИНАНТА", level=0)
    doc.add_heading("От физиологии внимания к логике мыслящего агента", level=1)
    files = sorted(f for f in os.listdir(CHAPTERS_DIR) if f.endswith('.md') and f not in SKIP)
    for f in files:
        with open(os.path.join(CHAPTERS_DIR, f), encoding='utf-8') as fh:
            lines = strip_frontmatter(fh.read().splitlines())
        in_list = None
        for line in lines:
            s = line.strip()
            if not s:
                continue
            m = re.match(r'^(#{1,6})\s+(.*)$', s)
            if m:
                lvl = min(len(m.group(1)), 4)
                doc.add_heading(m.group(2).strip(), level=lvl)
                in_list = None
                continue
            if s.startswith('>'):
                p = doc.add_paragraph()
                p.paragraph_format.left_indent = Pt(18)
                r = add_runs(p, s.lstrip('>').strip())
                for run in p.runs: run.italic = True
                in_list = None
                continue
            if s.startswith('|'):
                cells = [c.strip() for c in s.strip().strip('|').split('|')]
                if len(cells) >= 2 and not all(re.fullmatch(r'[-:]+', c) for c in cells):
                    tbl = doc.add_table(rows=1, cols=len(cells))
                    tbl.style = 'Table Grid'
                    for i, c in enumerate(cells):
                        tbl.rows[0].cells[i].text = c
                continue
            m = re.match(r'^[-*•]\s+(.*)$', s)
            if m:
                p = doc.add_paragraph(style='List Bullet')
                add_runs(p, m.group(1)); in_list = None; continue
            m = re.match(r'^\d+[.)]\s+(.*)$', s)
            if m:
                p = doc.add_paragraph(style='List Number')
                add_runs(p, m.group(1)); in_list = None; continue
            if s == '---':
                continue
            p = doc.add_paragraph()
            add_runs(p, s)
    doc.save(OUT_DOCX)
    print(f"OK: {OUT_DOCX}")
    print(f"chapters: {len(files)}")

if __name__ == '__main__':
    build()
