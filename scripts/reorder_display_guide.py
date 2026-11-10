"""Update only the robot comparison figures in the historical repository guide.

Requires PyMuPDF and the display images from reorder_display_media.py.
Always reads the pinned original PDF from Git, never a previously edited PDF.
"""
from pathlib import Path
import argparse
from io import BytesIO
import subprocess

import fitz
from fontTools import subset
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[1]
SOURCE = '3a255108a1c8e65428f19fa7caebb4b4684bc50f'
GUIDE = 'docs/guide/PhyRC_2027_Repository_Guide_KR.pdf'
ASSETS = ROOT / 'docs/gallery/assets/robot-layout-20261110'


def main(font_file):
    original = subprocess.check_output(['git', 'show', f'{SOURCE}:{GUIDE}'], cwd=ROOT)
    document = fitz.open(stream=original, filetype='pdf')
    for index, filename in ((10, 'e11-00000-wrists.png'),
                            (11, 'e15-current-wrist-depth.png')):
        page = document[index]
        image_xref = page.get_images()[0][0]
        rectangle = page.get_image_rects(image_xref)[0]
        page.delete_image(image_xref)
        if index == 10:
            rectangle = fitz.Rect(47, 123, 617, 443)
        page.insert_image(rectangle, filename=str(ASSETS / filename), keep_proportion=True)
        page.insert_text((48, 115), 'Display: robot_1 LEFT | robot_0 RIGHT (2026-11-10)',
                         fontsize=9, fontname='helv', color=(0, .42, .44))
        if index == 11:
            # The relaid-out figure is a display derivative of the actual E15 input.
            # Retain the rest of the original caption, replacing its opening only.
            spans = [span for block in page.get_text('dict')['blocks'] if 'lines' in block
                     for line in block['lines'] for span in line['spans']
                     if span['text'].startswith('E15의 실제 현재')]
            assert len(spans) == 1
            span = spans[0]
            page.add_redact_annot(fitz.Rect(span['bbox']), fill=(1, 1, 1))
            page.apply_redactions(images=0, graphics=0)
            # The original font is a subset; new caption glyphs need a full font.
            caption = 'E15 당시 입력의 표시용 재배치입니다. invalid는 빈 공간이 아니며, 회색값을 정밀 거리로 역산하지 않습니다.'
            font = TTFont(str(font_file), fontNumber=0)
            subsetter = subset.Subsetter()
            subsetter.populate(text=caption)
            subsetter.subset(font)
            buffer = BytesIO()
            font.save(buffer)
            page.insert_font(fontname='KRDisplay', fontbuffer=buffer.getvalue())
            page.insert_text(span['origin'], caption,
                fontsize=13, fontname='KRDisplay', color=(.345, .384, .447))
    output = ROOT / GUIDE
    document.save(output, garbage=4, deflate=True)
    print(f'Updated comparison figures on pages 11 and 12; retained {len(document)} pages')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--font', type=Path,
        default=Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'))
    main(parser.parse_args().font)
