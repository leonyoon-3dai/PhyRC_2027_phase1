"""Small five-camera panels, written once per new public observation boundary."""
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from participant.collection.boundary import CONTRACT


POSITIONS = {'overview': (128, 0), 'robot_1_head': (0, 276), 'robot_0_head': (256, 276),
             'robot_1_wrist': (0, 552), 'robot_0_wrist': (256, 552)}


def write_boundary(directory: Path, obs: dict, step: int):
    rgb = np.asarray(obs['rgb'])
    if rgb.shape != (5, 256, 256, 3) or rgb.dtype != np.uint8:
        raise ValueError('unexpected camera data at segment boundary')
    panel = Image.new('RGB', (512, 828), (18, 24, 33))
    draw = ImageDraw.Draw(panel)
    for i, name in enumerate(CONTRACT['competition_access']['allowed_cameras']):
        x, y = POSITIONS[name]
        draw.text((x + 3, y + 3), name, fill='white')
        panel.paste(Image.fromarray(rgb[i]), (x, y + 20))
    draw.text((5, 8), f'Step {step}', fill='white')
    target = directory / f'{step:06d}.jpg'
    tmp = target.with_suffix('.tmp')
    panel.save(tmp, format='JPEG', quality=86)
    tmp.replace(target)
