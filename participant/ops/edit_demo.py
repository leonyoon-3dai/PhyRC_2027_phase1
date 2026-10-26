#!/usr/bin/env python3
"""Build a captioned presentation edit and contact sheet from recorded renders."""
import argparse,bisect,json,subprocess
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--renders',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
a.output.mkdir(parents=True,exist_ok=True)
report=json.loads((a.renders/'render-report.json').read_text());plan=report['plan']
font='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc';bold='/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'
f=lambda size,heavy=False:ImageFont.truetype(bold if heavy else font,size)
images={};fps=25;intro=40;outro=65;last=plan[-1]['video_frame'];slots=[r['video_frame'] for r in plan]
labels=['접근과 그리퍼 정렬','양팔 파지와 옷 들어 올리기','사람 쪽으로 옷 옮기기']
def compose(index,opening=False,ending=False):
 row=plan[index];t=row['time_s'];phase=0 if t<71.15 else 1 if t<94 else 2
 if index not in images:images[index]=Image.open(a.renders/f'{index:05d}.png').convert('RGB')
 image=images[index]
 canvas=Image.new('RGB',(960,680),'#0b1726');canvas.paste(image,(0,60));d=ImageDraw.Draw(canvas)
 d.text((20,10),'PhyRC 2027 · Cooperative Robot Dressing',font=f(23,True),fill='#f0f5fb')
 d.text((20,40),'Leonard Yoon · Human teleoperation · 2026.10.26',font=f(11),fill='#adc0d4')
 d.rounded_rectangle((795,14,940,45),8,fill='#1c4c51');d.text((810,18),'실제 사람 시연',font=f(15,True),fill='#8ce8dc')
 for j,title in enumerate(labels):
  x=20+j*310;active=j==phase
  d.rounded_rectangle((x,610,x+300,638),6,fill='#24676b' if active else '#1b2d40')
  d.text((x+10,613),f'{j+1}  {title}',font=f(14,active),fill='#e9f9f5' if active else '#a8b8ca')
 speed=12 if phase==0 else 2 if phase==1 else 1.5
 d.text((20,645),f'SIM {t:05.1f} / 111.25 s  ·  시뮬레이션 기준 {speed:g}배속',font=f(13),fill='#a3c7dc')
 d.text((570,645),'원본 상태 재생 · 파지/운반 시연',font=f(13),fill='#b9cbda')
 d.rectangle((0,675,960,679),fill='#24384a');d.rectangle((0,675,round(960*t/111.25),679),fill='#53d6c3')
 if opening or ending:
  overlay=Image.new('RGBA',canvas.size);od=ImageDraw.Draw(overlay)
  od.rounded_rectangle((35,115,610,275 if opening else 260),18,fill=(11,23,38,230))
  od.text((60,135),'두 로봇으로 옷을 잡고' if opening else '파지 · 들어 올리기 · 운반',font=f(29,True),fill='#f0f5fb')
  od.text((60,181),'사람 쪽으로 옮기기' if opening else '다음 목표: 소매 진입과 착의',font=f(29,True),fill='#7de7d4')
  od.text((60,230 if opening else 227),'19분 28초의 키보드 조작 → 단계별 배속 편집' if opening else '전체 착의 성공이나 공식 평가 점수는 아직 아님',font=f(15),fill='#c5d2df')
  canvas=Image.alpha_composite(canvas.convert('RGBA'),overlay).convert('RGB')
 return canvas
out=a.output/'20261026-human-pickup-transport.mp4'
cmd=['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s','960x680','-r',str(fps),'-i','-','-an','-c:v','libx264','-preset','fast','-crf','21','-pix_fmt','yuv420p','-movflags','+faststart',str(out)]
with subprocess.Popen(cmd,stdin=subprocess.PIPE) as proc:
 for _ in range(intro):proc.stdin.write(compose(10,opening=True).tobytes())
 for slot in range(last+1):
  i=max(0,bisect.bisect_right(slots,slot)-1);proc.stdin.write(compose(i).tobytes())
 for _ in range(outro):proc.stdin.write(compose(len(plan)-1,ending=True).tobytes())
 proc.stdin.close();assert proc.wait()==0
canvas=Image.new('RGB',(1440,390),'#0b1726');d=ImageDraw.Draw(canvas)
for j,(time_s,title,sub) in enumerate([(69,'01 · 접근과 정렬','옷 양옆에서 팔과 그리퍼 조정'),(97,'02 · 양팔 파지·들기','두 로봇이 잡은 옷을 테이블 위로 올림'),(110,'03 · 사람 쪽 운반','옷을 유지하며 마네킹 쪽으로 이동')]):
 index=min(range(len(plan)),key=lambda i:abs(plan[i]['time_s']-time_s));image=Image.open(a.renders/f'{index:05d}.png').convert('RGB').resize((480,270),Image.Resampling.LANCZOS)
 canvas.paste(image,(j*480,70));d.text((j*480+18,16),title,font=f(25,True),fill='#80e1d2');d.text((j*480+18,348),sub,font=f(17),fill='#d1deeb')
canvas.save(a.output/'20261026-human-demo-stages.jpg',quality=94)
compose(len(plan)-1).save(a.output/'20261026-human-demo-poster.jpg',quality=94)
# A short, clearly edited looping teaser links to the complete captioned video.
subprocess.run(['ffmpeg','-y','-loglevel','error','-i',str(out),'-filter_complex','[0:v]fps=6,scale=560:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=96[p];[b][p]paletteuse=dither=bayer:bayer_scale=3','-loop','0',str(a.output/'20261026-human-demo.gif')],check=True)
edit={'source_run':report['source_run'],'source_manifest_sha256':report['source_manifest_sha256'],'video_duration_s':(intro+last+1+outro)/fps,'source_simulation_s':111.25,'collection_wall_s':1168.119,'speed_segments':report['speed_segments'],'physics_resimulated':False,'presentation_only':True,'full_dressing_success':False,'notes':['Captioned edit; original archive preserved','5Hz recorded-state sampling; repeated frames on 25fps output; no generated in-between states','Intro/outro holds and stage-dependent playback speed; not real-time robot speed']}
(a.output/'20261026-human-demo-edit.json').write_text(json.dumps(edit,indent=2)+'\n');print(json.dumps(edit),flush=True)
