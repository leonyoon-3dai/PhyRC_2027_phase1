"""Render a complete run or a published prefix from its public review frames.

Example from the repo root:
    .venv/bin/python scripts/export_demonstration_gif.py \
        output/operator-traces/RUN/segment-frames --end 1655 --out demo.gif
"""
import argparse
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

from PIL import Image, ImageDraw, ImageFont


# Each segment_frames.write_boundary image has five 256px RGB tiles and 20px labels.
TILES = (
    ("Overview", (128, 20), (0, 28), 256),
    ("R1 head", (0, 296), (260, 20), 128),
    ("R0 head", (256, 296), (390, 20), 128),
    ("R1 wrist", (0, 572), (260, 169), 128),
    ("R0 wrist", (256, 572), (390, 169), 128),
)
SIZE = (518, 297)
MIN_STRIDE = 12
MAX_INTERVALS = 230
SIMULATION_HZ = 20
PLAYBACK_SPEED = 6


def paint(source, step, end, font):
    panel = Image.new('RGB', SIZE, (19, 25, 33))
    draw = ImageDraw.Draw(panel)
    with Image.open(source) as img:
        if img.size != (512, 828):
            raise ValueError(f'Unexpected review frame size in {source}')
        for label, (sx, sy), (x, y), size in TILES:
            tile = img.crop((sx, sy, sx + 256, sy + 256))
            panel.paste(tile.resize((size, size), Image.Resampling.LANCZOS), (x, y))
            draw.text((x + 4, y - 17), label, fill='white', font=font)
    draw.text((252, 11), f'Step {step} / {end}', anchor='rt', fill='white', font=font)
    return panel


def export(frames, end, output, *, start=0, normal_tail=0, speed=PLAYBACK_SPEED):
    if not 0 <= start < end:
        raise ValueError('Expected at least one transition')
    if normal_tail < 0 or speed < 1:
        raise ValueError('Expected non-negative normal-speed tail and positive playback speed')
    # The explicit cutoff is stable even while the collector appends new frames.
    for i in range(start, end + 1):
        if not (frames / f'{i:06d}.jpg').is_file():
            raise ValueError(f'Missing transition boundary {i}')
    # Cap the number of frames on long runs while preserving playback speed.
    stride = max(speed if speed != PLAYBACK_SPEED else MIN_STRIDE,
                 (end - start + MAX_INTERVALS - 1) // MAX_INTERVALS)
    timing = []
    mux_options = []
    if normal_tail:
        boundary = max(start, end - normal_tail)
        # One early frame represents 12 transitions and lasts two 20 Hz ticks.
        early = list(range(boundary - MIN_STRIDE, start, -MIN_STRIDE))[::-1]
        steps = [start, *early] if start < boundary else []
        leading_ticks = max(1, round((boundary - start) / PLAYBACK_SPEED))
        if steps:
            offset = leading_ticks - 2 * (len(steps) - 1)
            timing = [f"setpts='if(eq(N,0),0,if(lt(N,{len(steps)}),"
                      f"{offset}+2*(N-1),{leading_ticks}+N-{len(steps)}))'"]
        steps.extend(range(boundary, end + 1))
        frame_rate = str(SIMULATION_HZ)
        mux_options = ['-vsync', 'vfr']
    else:
        steps = list(range(start, end, stride)) + [end]
        frame_rate = f'{SIMULATION_HZ * speed}/{stride}'
    output.parent.mkdir(parents=True, exist_ok=True)
    font = ImageFont.load_default(size=14)
    with TemporaryDirectory(dir=output.parent) as tmp:
        temp = Path(tmp) / 'render.gif'
        filters = ('split[frames][colors];[colors]palettegen=max_colors=48:reserve_transparent=1[pal];'
                   '[frames][pal]paletteuse=dither=none:diff_mode=rectangle')
        if timing:
            filters += ',' + timing[0]
        cmd = ['ffmpeg', '-nostdin', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
               '-s', f'{SIZE[0]}x{SIZE[1]}', '-r', frame_rate, '-i', 'pipe:0',
               '-filter_complex_threads', '1', '-filter_complex', filters, '-threads', '1',
               *mux_options, '-loop', '0', '-final_delay', '90', str(temp)]
        with subprocess.Popen(cmd, stdin=subprocess.PIPE) as process:
            try:
                for step in steps:
                    frame = paint(frames / f'{step:06d}.jpg', step, end, font)
                    process.stdin.write(frame.tobytes())
            finally:
                process.stdin.close()
            if process.wait():
                raise RuntimeError('ffmpeg could not encode the GIF')
        with Image.open(temp) as gif:
            if (gif.n_frames, gif.size, gif.info.get('loop')) != (len(steps), SIZE, 0):
                raise ValueError('Unexpected encoded GIF frame count, size or loop')
            for i in range(gif.n_frames):
                gif.seek(i)
                gif.load()
        temp.replace(output)
    print(f'{output}: steps {start}–{end}, {len(steps)} frames, {output.stat().st_size} bytes')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('frames', type=Path, help='segment-frames directory for one run')
    parser.add_argument('--end', required=True, type=int, help='inclusive final published transition')
    parser.add_argument('--start', default=0, type=int, help='first published transition')
    parser.add_argument('--normal-tail', default=0, type=int, help='final transitions played at 1×')
    parser.add_argument('--speed', default=PLAYBACK_SPEED, type=int, help='playback speed without a normal-speed tail')
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    export(args.frames, args.end, args.out, start=args.start, normal_tail=args.normal_tail, speed=args.speed)
