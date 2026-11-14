#!/usr/bin/env python3
"""Render and inspect the report without changing any original evidence."""
from pathlib import Path
import hashlib
import json
import pymupdf
from PIL import Image, ImageDraw
from reportlab.pdfbase.ttfonts import TTFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = ROOT/'output/report-validation/20261114-e36'
OUT.mkdir(parents=True, exist_ok=True)
pdf = HERE/'phyrc-e36-integrated-review.ko.pdf'
doc = pymupdf.open(pdf)
font = TTFont('validation', '/usr/share/fonts/truetype/nanum/NanumGothic.ttf')
texts, thumbnails, outside, missing_glyphs = [], [], [], set()
links = 0
for i, page in enumerate(doc):
    assert (page.rect.width, page.rect.height) == (960, 540)
    text = page.get_text()
    texts.append(text)
    missing_glyphs.update(ch for ch in text if not ch.isspace() and not font.face.charToGlyph.get(ord(ch)))
    links += len(page.get_links())
    for block in page.get_text('blocks'):
        if block[0] < 0 or block[1] < 0 or block[2] > 960.5 or block[3] > 540.5:
            outside.append([i+1, *block[:4]])
    path = OUT/f'slide-{i+1:02}.png'
    page.get_pixmap(matrix=pymupdf.Matrix(1.25, 1.25), alpha=False).save(path)
    im = Image.open(path)
    im.thumbnail((320, 180))
    tile = Image.new('RGB', (320, 200), '#e9eef2')
    tile.paste(im, (0, 20))
    ImageDraw.Draw(tile).text((8, 4), f'{i+1:02}', fill='black')
    thumbnails.append(tile)
assert len(doc) == 18 and not outside and not missing_glyphs
assert all('PhyRC' in text and len(text)>180 for text in texts)
assert '-16.97' in texts[7] and '-0.97' in texts[7] and '-2.78' in texts[7] and '-1.23' in texts[7]
assert '새 base yaw 명령은 모두 0' in texts[1]
contact = Image.new('RGB', (960, 1200), 'white')
for i, im in enumerate(thumbnails):
    contact.paste(im, ((i%3)*320, (i//3)*200))
contact.save(OUT/'all-slides.png')
(OUT/'extracted-text.txt').write_text('\n\n'.join(texts))
provenance = json.loads((HERE/'provenance.json').read_text())
assert provenance['pdf_sha256'] == hashlib.sha256(pdf.read_bytes()).hexdigest()
for relative, expected in provenance['source_file_sha256'].items():
    assert hashlib.sha256((ROOT/relative).read_bytes()).hexdigest() == expected, relative
boundary = json.loads((HERE/'assets/provenance.json').read_text())
assert boundary['boundary_exclusive_step'] == 835
for item in boundary['files']:
    assert item['index'] == 834
    p = HERE/'assets'/item['file']
    assert hashlib.sha256(p.read_bytes()).hexdigest() == item['sha256']
    assert hashlib.sha256(Image.open(p).tobytes()).hexdigest() == item['pixel_sha256']
result = {'schema':'phyrc-slide-validation-v1','pages':len(doc),'page_size_points':[960,540],
          'all_pages_rendered':True,'korean_text_extractable':True,
          'missing_font_glyphs':[],'text_outside_page':[],'clickable_links':links,
          'negative_measurements_preserved':True,'source_hashes_match':True,
          'initial_comparison_boundary':835,'initial_comparison_hdf5_index':834,
          'pdf_sha256':provenance['pdf_sha256'],
          'limits':'Automated checks do not establish cloth passage or replace visual/content review.'}
(HERE/'validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result,ensure_ascii=False))
