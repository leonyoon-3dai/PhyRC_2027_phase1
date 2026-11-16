#!/usr/bin/env python3
"""Export dense public-camera GIFs only from a verified, frozen HOLD file copy.

Never reads the live source file. A preceding supervisor HOLD and ordinary copy
must have recorded identical source-before/source-after/copy SHA256 values in
snapshot.json. The source may remain incomplete/open; this is a review export,
not capture validation or training approval.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re

import h5py
import numpy as np
from PIL import Image, ImageDraw, ImageFont

CAMERAS = ['overview', 'robot_1_head', 'robot_0_head', 'robot_1_wrist', 'robot_0_wrist']
TITLES = {'retreat': 'Retreat', 'lower-and-neutral': 'Lower, then neutral',
          'reapproach': 'Reapproach', 'full': 'All recorded movement',
          'right-hand-retreat': 'Retreat to inspect right hand and garment slack',
          'neutral-residual-motion': 'Neutral step / residual motion',
          'tiny-lowering': 'Tiny lowering',
          'neutral-and-tiny-lowering': 'Neutral step, then tiny lowering',
          'tiny-bodyward-approach': 'Tiny bodyward approach / lift command 0',
          'bodyward-15mm': 'Bodyward approach / requested target: 15 mm',
          'bodyward-30mm': 'Bodyward approach / additional target: 30 mm',
          'bodyward-30mm-slight-rise': '30 mm additional target / brief slight rise',
          'bodyward-50mm-slight-rise': '50 mm requested / ~17 mm moved / early HOLD',
          'bodyward-33mm-completion': '33 mm requested / about 32 mm moved',
          'third-stripe-approach': 'Third stripe unconfirmed / asymmetric HOLD'}


def sha(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def font(size):
    return ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', size)


def frame(data, boundary, title, origin):
    group, row = ('obs', 0) if boundary == 0 else ('next_obs', boundary - 1)
    time_s = float(np.asarray(data[group]['simulation_time_s'][row]).reshape(-1)[0])
    # Keep every original 256px camera pixel; browser zoom can enlarge the panel.
    tile, gap, top, label = 256, 8, 70, 20
    width, height = 2 * tile + 3 * gap, top + 3 * (tile + label + gap) + gap
    image = Image.new('RGB', (width, height), '#101a28')
    draw = ImageDraw.Draw(image)
    draw.text((gap, 7), title, font=font(14), fill='white')
    draw.text((gap, 29), f'STEP {boundary:03d}  |  episode {time_s-origin:.2f}s  |  sim {time_s:.3f}s',
              font=font(13), fill='#aadaff')
    draw.text((gap, 49), 'Recorded 20 Hz / 5 fps (4x slower) / endpoint pauses',
              font=font(12), fill='#d2dae6')
    places = [(int((width-tile)/2), top), (gap, top+tile+label+gap),
              (tile+2*gap, top+tile+label+gap), (gap, top+2*(tile+label+gap)),
              (tile+2*gap, top+2*(tile+label+gap))]
    for camera, (x, y) in zip(CAMERAS, places):
        rgb = np.asarray(data[group][camera+'_rgb'][row])
        if rgb.dtype != np.uint8 or rgb.shape != (256, 256, 3):
            raise ValueError('unexpected designated-camera dimensions or dtype')
        draw.text((x, y), camera, font=font(13), fill='white')
        image.paste(Image.fromarray(rgb), (x, y+label))
    return image, time_s


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--snapshot-dir', type=Path, required=True)
    p.add_argument('--output-dir', type=Path, required=True)
    p.add_argument('--segment', action='append', required=True, help='inclusive START:END:SLUG boundary range')
    args=p.parse_args()
    snapshot=json.loads((args.snapshot_dir/'snapshot.json').read_text())
    hold=snapshot['hold']
    if not hold['held'] or not hold['active']:
        raise ValueError('snapshot was not secured at a live HOLD')
    expected=snapshot['copy_sha256']
    if not expected == snapshot['source_sha256_before'] == snapshot['source_sha256_after'] == sha(args.snapshot_dir/'policy.hdf5'):
        raise ValueError('frozen file SHA verification failed')
    args.output_dir.mkdir(parents=True, exist_ok=True)
    receipt_name='source-'+hold['hold_id']+'.json'
    receipt_path=args.output_dir/receipt_name
    if receipt_path.exists():
        if json.loads(receipt_path.read_text())!=snapshot:raise ValueError('existing snapshot receipt differs')
    else:receipt_path.write_text(json.dumps(snapshot,indent=2)+'\n')
    reports=[]
    with h5py.File(args.snapshot_dir/'policy.hdf5','r') as stream:
        data=stream['data/demo_0']
        n=len(data['actions'])
        if n!=hold['observation_step']:raise ValueError('HOLD boundary differs from copied transitions')
        # Check each adjacent recorded RGB boundary; use every real boundary.
        for camera in CAMERAS:
            if not np.array_equal(data['obs'][camera+'_rgb'][1:],data['next_obs'][camera+'_rgb'][:-1]):
                raise ValueError('RGB transition continuity failed: '+camera)
        origin=float(np.asarray(data['obs/simulation_time_s'][0]).reshape(-1)[0])
        for segment in args.segment:
            start,end,slug=segment.split(':');start,end=int(start),int(end)
            if not 0<=start<end<=n or not re.fullmatch('[a-z0-9-]+',slug):raise ValueError('invalid segment')
            output=args.output_dir/(slug+'.gif')
            if output.exists():raise FileExistsError(output)
            frames,times=zip(*(frame(data,b,TITLES.get(slug,slug.replace('-',' ').title()),origin)
                               for b in range(start,end+1)))
            sample=Image.new('RGB',(128*len(frames),200))
            for i,img in enumerate(frames):sample.paste(img.resize((128,200)),(i*128,0))
            palette=sample.quantize(colors=256,method=Image.Quantize.MEDIANCUT)
            quantized=[img.quantize(palette=palette,dither=Image.Dither.NONE) for img in frames]
            durations=[200]*len(frames);durations[0]=800;durations[-1]=1000
            quantized[0].save(output,save_all=True,append_images=quantized[1:],duration=durations,
                              loop=0,optimize=True,disposal=1)
            with Image.open(output) as check:
                if check.n_frames!=len(frames):raise ValueError('GIF frame count mismatch')
                actual=[]
                for i in range(check.n_frames):
                    check.seek(i);actual.append(check.info['duration'])
                    if not np.array_equal(np.asarray(check.convert('RGB')), np.asarray(quantized[i].convert('RGB'))):
                        raise ValueError('GIF optimization changed decoded frame: '+str(i))
                if actual!=durations:raise ValueError('GIF duration mismatch')
            metadata={'schema':'phyrc-held-segment-gif-v1','source_run':snapshot['source_run'],
                'source_receipt':receipt_name,'source_capture_complete':False,
                'boundary_start':start,'boundary_end':end,'transition_count':end-start,
                'source_frames':len(frames),'source_simulation_duration_s':times[-1]-times[0],
                'all_boundaries_included':True,'interpolated_frames':False,'mirrored':False,
                'layout':{'top':'overview','left':['robot_1_head','robot_1_wrist'],
                    'right':['robot_0_head','robot_0_wrist']},
                'original_camera_size_px':[256,256],'display_scale':1,'resize':'none',
                'gif_palette_colors':256,'gif_dither':'none','delta_frame_optimization':True,
                'decoded_frames_match_palette_frames':True,'source_spacing_s':0.05,
                'interior_playback_spacing_ms':200,'endpoint_durations_ms':[800,1000],
                'playback_duration_ms':sum(durations),'gif_bytes':output.stat().st_size,'gif_sha256':sha(output)}
            (args.output_dir/(slug+'.json')).write_text(json.dumps(metadata,indent=2)+'\n')
            reports.append({'gif':str(output),'frames':len(frames),'bytes':output.stat().st_size})
    print(json.dumps(reports,indent=2))


if __name__=='__main__':main()
