"""Encode the public camera panels from reset to a recorded boundary."""
from pathlib import Path
import tempfile

from PIL import GifImagePlugin, Image

if __package__:
    from .review_wide_media import wide_panel
else:
    from review_wide_media import wide_panel

GIF_TRAILER = b'\x3b'
SAMPLE_STEPS = 8
WIDTH = 320


def gif_delta(frames: Path, previous_end: int | None, end: int, *, widescreen=False) -> bytes:
    """Encode a segment once. The first chunk also carries the GIF header."""
    if end < 0 or (previous_end is not None and end < previous_end):
        raise ValueError('Cumulative GIF boundaries must be chronological')
    if previous_end == end:
        return b''
    first = 0 if previous_end is None else previous_end + 1
    aligned = first + (-first % SAMPLE_STEPS)
    steps = [*range(aligned, end, SAMPLE_STEPS), end]
    blocks = []
    for step in steps:
        with Image.open(frames / f'{step:06d}.jpg') as source:
            frame = source.convert('RGB')
            if widescreen:
                frame = wide_panel(frame)
            width = 960 if widescreen else WIDTH
            height = round(frame.height * width / frame.width)
            frame = frame.resize((width, height), Image.Resampling.LANCZOS)
            frame = frame.quantize(colors=128, dither=Image.Dither.NONE)
        if step == 0 and previous_end is None:
            header, _ = GifImagePlugin.getheader(frame, info={'loop': 0})
            blocks.extend(header)
        # A local palette lets earlier frames remain byte-identical as the run grows.
        blocks.extend(GifImagePlugin.getdata(frame, include_color_table=True, duration=100, disposal=1))
    return b''.join(blocks)


def write_cumulative_gif(path: Path, previous: Path | None, delta: bytes):
    prefix = previous.read_bytes() if previous else GIF_TRAILER
    if not prefix.endswith(GIF_TRAILER):
        raise ValueError(f'Invalid preceding GIF: {previous}')
    with tempfile.TemporaryDirectory(dir=path.parent) as tmp:
        staged = Path(tmp) / path.name
        with staged.open('wb') as output:
            output.write(memoryview(prefix)[:-1])
            output.write(delta)
            output.write(GIF_TRAILER)
        staged.replace(path)
