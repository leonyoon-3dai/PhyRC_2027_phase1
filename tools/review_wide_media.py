"""Rearrange the recorded five-camera panel for gallery playback."""
import hashlib
from pathlib import Path
import subprocess
import tempfile


WIDE_FILTER = (
    '[0:v]split=3[overview][robots][step];'
    '[overview]crop=256:276:128:0,scale=512:552:flags=lanczos,setsar=1[left];'
    '[step]crop=100:20:0:0,scale=200:40:flags=lanczos,setsar=1[label];'
    '[left][label]overlay=312:0:shortest=1[captioned];'
    '[robots]crop=512:552:0:276,setsar=1[right];'
    '[captioned][right]hstack=shortest=1'
)


def wide_panel(source):
    from PIL import Image

    if source.size != (512, 828):
        raise ValueError(f'Unexpected review panel dimensions: {source.size}')
    panel = Image.new('RGB', (1024, 552))
    panel.paste(source.crop((128, 0, 384, 276)).resize((512, 552), Image.Resampling.LANCZOS))
    panel.paste(source.crop((0, 0, 100, 20)).resize((200, 40), Image.Resampling.LANCZOS), (312, 0))
    panel.paste(source.crop((0, 276, 512, 828)), (512, 0))
    return panel


def wide_clip(source: Path, cache: Path):
    with source.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    cache.mkdir(mode=0o700, parents=True, exist_ok=True)
    target = cache / (source.stem + '-' + digest + '.mp4')
    if not target.is_file():
        with tempfile.TemporaryDirectory(dir=cache) as tmp:
            output = Path(tmp) / 'review.mp4'
            subprocess.run(['ffmpeg', '-v', 'error', '-nostdin', '-threads', '1', '-i', str(source),
                            '-filter_complex_threads', '1', '-filter_complex', WIDE_FILTER,
                            '-an', '-c:v', 'libx264', '-threads', '1', '-preset', 'veryfast',
                            '-crf', '22', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(output)],
                           check=True, timeout=45)
            output.replace(target)
    return target
