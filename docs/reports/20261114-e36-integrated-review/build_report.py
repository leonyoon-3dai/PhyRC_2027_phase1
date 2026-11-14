#!/usr/bin/env python3
"""Build the Korean, 16:9 review from public repo evidence; no simulator access.

Requires reportlab 5.1.0 and NanumGothic regular/bold TTF (Ubuntu fonts-nanum).
Run from any directory. Original captures, manifests and media are never edited.
"""
from pathlib import Path
from xml.sax.saxutils import escape
import hashlib
import json

from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph, Table, TableStyle

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
W, H = 960, 540
NAVY, INK, MUTED = '#142B45', '#172E47', '#526879'
TEAL, AMBER, BLUE, BG = '#008B8B', '#BC6B19', '#497DC1', '#F3F6F9'
FONT_DIR = Path('/usr/share/fonts/truetype/nanum')
for name, filename in [('NG', 'NanumGothic.ttf'), ('NGB', 'NanumGothicBold.ttf')]:
    pdfmetrics.registerFont(TTFont(name, str(FONT_DIR / filename)))
pdfmetrics.registerFontFamily('NG', normal='NG', bold='NGB')

DATA = json.loads((HERE / 'report-data.json').read_text())
PDF = HERE / 'phyrc-e36-integrated-review.ko.pdf'
C = canvas.Canvas(str(PDF), pagesize=(W, H), pageCompression=1)
C.setTitle('PhyRC E00–E36 통합 분석과 다음 사용자 개입 실험')
C.setAuthor('PhyRC · 사용자 관찰 / Codex 분석 / 연구 검토')
C.setSubject('E36 종료, 데이터 검증, 실제 조작과 미확인 통과, 키보드 및 사용자 개입 계획')
PAGE = 0
TEXT = []
SOURCES_USED = set()


def rect(x, top, w, h, color, radius=0):
    C.setFillColor(colors.HexColor(color))
    C.setStrokeColor(colors.HexColor(color))
    if radius:
        C.roundRect(x, H-top-h, w, h, radius, stroke=0, fill=1)
    else:
        C.rect(x, H-top-h, w, h, stroke=0, fill=1)


def p(text, x, top, w, size=16, color=INK, bold=False, leading=None, limit=494):
    style = ParagraphStyle('p', fontName='NGB' if bold else 'NG', fontSize=size,
                           leading=leading or size*1.43, textColor=colors.HexColor(color),
                           wordWrap='CJK', spaceAfter=0)
    para = Paragraph(text, style)
    _, height = para.wrap(w, H)
    if top + height > limit:
        raise ValueError(f'Page {PAGE} overflow at {top+height:.1f}: {text[:65]}')
    para.drawOn(C, x, H-top-height)
    return height


def footer(refs=(), dark=False):
    col = '#C7D5E1' if dark else MUTED
    C.setFillColor(colors.HexColor(col)); C.setFont('NG', 8.5)
    C.drawString(48, 20, 'PhyRC 2027  |  2026-11-14  |  공개 근거·제안·미확인 분리')
    C.drawRightString(912, 20, f'{PAGE:02d}')
    x = 48
    for key in refs:
        src = DATA['sources'][key]
        label = src['label']
        width = pdfmetrics.stringWidth(label, 'NG', 8.5)
        C.drawString(x, 36, label)
        C.linkURL(src['url'], (x, 34, x+width, 46), relative=0, thickness=0)
        x += width+22
        SOURCES_USED.add(key)


def start(title, subtitle='', section='ANALYSIS', refs=(), dark=False):
    global PAGE
    if PAGE: C.showPage()
    PAGE += 1
    rect(0, 0, W, H, NAVY if dark else '#FFFFFF')
    rect(0, 0, W, 6, TEAL)
    p(section, 48, 22, 864, 9, '#7CCBD0' if dark else TEAL, True)
    p(title, 48, 47, 864, 28, '#FFFFFF' if dark else INK, True)
    if subtitle: p(subtitle, 48, 92, 864, 12, '#D1DFE9' if dark else MUTED)
    footer(refs, dark)
    TEXT.append(f'\n## {PAGE:02d}. {title}\n\n{subtitle}\n')
    if refs:
        TEXT.append('근거: ' + ' · '.join(f"[{DATA['sources'][r]['label']}]({DATA['sources'][r]['url']})" for r in refs)+'\n')


def card(x, y, w, h, title, body, color=TEAL, size=16):
    rect(x, y, w, h, BG, 10); rect(x, y, 5, h, color)
    th = p(title, x+18, y+16, w-36, 18, color, True)
    p(body, x+18, y+27+th, w-36, size, leading=size*1.48, limit=min(y+h-14, 494))
    TEXT.append(f'**{title}** — {body.replace("<br/>", " ")}\n')


def table(headers, rows, widths, top=138, size=13):
    sty = ParagraphStyle('cell', fontName='NG', fontSize=size, leading=size*1.42,
                         textColor=colors.HexColor(INK), wordWrap='CJK')
    head = ParagraphStyle('head', parent=sty, fontName='NGB', textColor=colors.white)
    cells = [[Paragraph(escape(str(v)), head) for v in headers]]
    cells += [[Paragraph(escape(str(v)).replace('\n', '<br/>'), sty) for v in row] for row in rows]
    t = Table(cells, colWidths=widths, hAlign='LEFT')
    t.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),colors.HexColor(NAVY)),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.HexColor(BG),colors.white]),
        ('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),11),
        ('BOTTOMPADDING',(0,0),(-1,-1),11),('LEFTPADDING',(0,0),(-1,-1),12),
        ('RIGHTPADDING',(0,0),(-1,-1),12),
        ('LINEBELOW',(0,0),(-1,0),0.5,colors.HexColor(NAVY))]))
    _, h = t.wrap(864, 360)
    if top+h>489: raise ValueError(f'Page {PAGE} table overflow: {top+h}')
    t.drawOn(C, 48, H-top-h)
    TEXT.append('| '+' | '.join(headers)+' |\n| '+' | '.join(['---']*len(headers))+' |')
    TEXT.extend('| '+' | '.join(str(v).replace('\n',' / ') for v in row)+' |' for row in rows)
    TEXT.append('')
    return top+h


def img(relative, x, top, size):
    path = ROOT / relative
    if not path.is_file(): raise FileNotFoundError(path)
    C.drawImage(str(path), x, H-top-size, size, size, preserveAspectRatio=True, mask='auto')


def text_note(text, top=456, size=12):
    p(text, 48, top, 864, size, MUTED)
    TEXT.append(text+'\n')


# 01: Cover.
start('옷을 펼친 뒤, 손목을 통과시키기까지',
      'E00–E36 통합 분석 · 사용자 관찰 × Codex 실행 근거 × Agentic Robotics 연구',
      'FINAL COLLECTION REVIEW', ['status','e36','plan'], True)
p('E36에서 수집을 종료했습니다.', 48, 163, 864, 32, '#FFFFFF', True)
p('다음 목표는 사람의 짧은 조작으로 아직 모르는 관계를 구분하고,<br/>그 교정 과정을 재검토 가능한 데이터로 남기는 것입니다.',
  48, 225, 825, 19, '#D1DFE9')
for x, big, label in [(48,'5 / 50','E36 원점수 · 새 착의점 0'),(344,'933 / 933','E36 전체 전이 QC 통과'),(640,'E36 종료','E37 이후 추가 실행 없음')]:
    rect(x, 337, 272, 105, '#213E5C', 10)
    p(big,x+18,350,236,26,'#71D6CA',True)
    p(label,x+18,399,236,12,'#FFFFFF')
TEXT.append('E36 최종5/50·새 착의점0·QC933/933. E37 이후 실행 없음.\n')

# 02: Three perspectives and common conclusion.
start('세 관점이 만나는 결론', '관찰과 가설, 측정 결과, 연구의 적용 제안을 한 층으로 섞지 않는다.', refs=['e34','e35','e36','research'])
card(48,137,272,278,'사용자 관찰', '옷의 폭과 손목 근처 위치는 유용해 보인다.<br/><br/>정확히 방향을 맞추고 몸쪽으로 밀면 다음 단계에 도달할 수 있다는 가설.',TEAL)
card(344,137,272,278,'Codex 실행 분석','접근·하강과 상대 위치 변화는 실제로 있었다.<br/><br/>E36의 새 base yaw 명령은 모두 0. 정확한 베이스 방향 정렬까지 충분히 시험하지는 못했다.',BLUE,15)
card(640,137,272,278,'연구에서 가져올 것','사람 개입의 경계, 실제 행동, 전후 효과를 구분해 기록한다.<br/><br/>연구의 기능·성과가 현재 PhyRC에 구현되거나 재현된 것은 아니다.',AMBER,15)
text_note('공통 우선순위: 같은 실패 설명을 늘리기보다, 사람의 짧은 조작으로 구분 가능한 질문을 만든다.',446,14)

# 03: User request mapped to actual behavior.
start('사용자의 제안은 어디까지 시험됐는가', '“방향을 맞춰 서기”와 “몸쪽 이동”을 별개의 수행 항목으로 검토한다.',refs=['e35','e36','batch'])
table(['사용자 관찰·요청','실제 반영','현재 판단'],[
 ['옷 아래를 넓게 펼쳐 약간 위·옆에서 접근','E35: 형상 조절·방향 변경 후 같은 손에 측면 접근','새 근접 관계 관측. 통과 미확인'],
 ['E34 형상이 이미 유용하므로 보존','E36: E34/835에서 시작, 재파지·운반 준비 반복 없음','기존 형상 활용은 반영'],
 ['정확히 손목 방향에 맞춰 서기','E36: wrist yaw 2회, 새 base yaw 명령 0','베이스 방향 정렬의 충분한 시험은 아님'],
 ['몸쪽으로 밀어 넣기','E36: 몸쪽·하강 시험 5회, 매번 후속 관측','실제 운동 있음. 연속 전완 진행·소매 출구 미확인'],
 ],[230,354,280],size=13)
text_note('“추가 5점 가능”은 사용자 가설이다. 다음 5점인 첫 소매 통과는 별도 평가에서 충족되지 않았다.',464,11)

# 04: Prior evidence.
start('축적된 경험: 이미 되는 부분과 남은 문제', '전체 경험은 보존된 리뷰·계보·코드를 종합했다. 모든 과거 영상을 이번에 전수 재시청한 것은 아니다.',refs=['episodes','redesign'])
items=[('사람·E00–E07','사람 부분 시연 2,225전이. 초기 픽업과 두 로봇 공동 운반을 관측.'),
       ('E10–E19','관측·depth·지지 검사·재파지·정착을 이미 비교. 중립에서도 실제 운동이 남음.'),
       ('E20–E27','새 경계 파지와 운반, 첫 팔 접근을 시험. 손 선택 전환·통과 미확인이 남음.'),
       ('E28–E32','같은 손 유지·대각선/중앙 접근 비교. E32는 불완전 원본이며 정상 replay에서 제외.'),
       ('E33–E34','새 파지 준비 뒤 들기·운반·하강까지 확인. 준비가 끝난 것과 진입 성공은 다름.'),
       ('E35–E36','넓은 형상과 즉시 몸쪽 접근을 비교. 사용자 피드백을 반영했으나 새 착의점 0.')]
for i,(title,body) in enumerate(items):
    card(48+(i%2)*444,132+(i//2)*113,420,108,title,body,TEAL if i<4 else BLUE,13)

# 05: Matched quantities.
start('최근 네 시연: 무엇을 새로 수집했는가', '결정 수와 모델 호출, 재생 전이와 새 전이를 구분한다.',refs=['e33','e34','e35','e36'])
table(['시연 / 직접 출발','결정 / 호출','전체 = 재생 + 새 전이','최종 raw / 새 착의점','수집 경과'],[
 ['E33 · E28/264','20 / 21','471 = 264 + 207','0 / 0','22.52분'],
 ['E34 · E33/470','20 / 24','836 = 470 + 366','5 / 0','32.66분'],
 ['E35 · E34/723','19 / 21','983 = 723 + 260','5 / 0','40.17분'],
 ['E36 · E34/835','11 / 12','933 = 835 + 98','5 / 0','28.12분'],
 ],[206,118,250,145,145],size=13)
text_note('새 전이는 model·settle·종료 정리를 포함한다. E35/E36의 픽업5는 각 replay에서 얻었다.',405,13)
text_note('E34/723 이후는 7act, E35는 18act다. 다른 출발점·예산·재생 편차를 전략 하나의 인과 효과로 해석하지 않는다.',446,12)

# 06: Three observations, clearly same camera identity but no pixel geometry comparison.
start('최근 공개 영상: 근접은 보이지만 통과는 미확인', '각 시연의 마지막 robot_1 head. 카메라·로봇 자세가 달라 픽셀 폭을 물리 개방률로 비교하지 않는다.',refs=['e34','e35','e36'])
for i,(key,label,cap) in enumerate([
    ('e34','E34 · 836','운반 후 손목 근처 형상'),
    ('e35','E35 · 983','더 넓은 외관과 새 근접 관계'),
    ('e36','E36 · 933','몸쪽 시험 뒤에도 파지부 곁에 손')]):
    x=60+i*296
    p(label,x,132,260,17,TEAL,True)
    img(DATA['runs'][key]['images']+'/final-robot_1_head.png',x,168,248)
    p(cap,x,430,260,13)
    TEXT.append(f'{label}: {cap}\n')

# 07: E36 initial/final mosaic.
start('E36: 같은 손·전완은 보였고, 진입은 남았다', '각 묶음은 왼쪽 robot_1 / 오른쪽 robot_0, 위 head / 아래 wrist. 원본 픽셀을 반전하지 않았다.',refs=['e36','e36manifest'])
base=DATA['runs']['e36']['images']
for x,phase,title in [(70,'initial','새 replay / 835'),(554,'final','최종 / 933')]:
    p(title,x,126,330,17,TEAL,True)
    for j,cam in enumerate(['robot_1_head','robot_0_head','robot_1_wrist','robot_0_wrist']):
        rel = ('docs/reports/20261114-e36-integrated-review/assets/e36-0835-'+cam+'.png' if phase=='initial' else base+f'/final-{cam}.png')
        img(rel,x+(j%2)*164,156+(j//2)*164,160)
TEXT.append('초기와 최종 공개 head/wrist를 비교. 손·연결 전완은 유지됐지만 자유 경계 통과와 소매 출구는 확인하지 못했다.\n')

# 08: Movement mismatch.
start('E36에서 새로 분명해진 실행 차이', '명령값·관절 변위·그리퍼 실제 이동·천의 진행은 같은 양이 아니다.',refs=['e36'])
card(48,136,272,290,'5회 진입 시험','10act 중 몸쪽/하강 5회, wrist 방향 2회, 팔 수축 1회, 중립 관찰 2회.<br/><br/>처음부터 진입을 시도했다.',TEAL,15)
card(344,136,272,290,'-17mm ≠ -1mm','D5 robot_1 lift 약 -16.97mm.<br/>base 기준 grasp Z는 약 -0.97mm.<br/><br/>손목 pitch 편차가 함께 나타났다.',BLUE,15)
card(640,136,272,290,'정착 중 일부 되돌림','D5 base Y: 명령 +10.97mm → settle -2.78mm.<br/>D9: +11.44mm → -1.23mm.<br/><br/>world Y는 몸쪽 거리가 아니다.',AMBER,14)
text_note('같은 손이 파지 모서리/housing 가까이에 남았다는 관측은 있으나, 정확한 접촉 원인은 확정하지 않았다.',451,12)

# 09: Evidence ladder.
start('관측 판정 기준: 확인할 수 있는 만큼만', 'unknown을 허용한다. 아래 단계의 증거가 위 단계의 성공을 대신하지 않는다.',refs=['e36','redesign'])
table(['층','이번에 확인한 근거','남겨야 할 한계'],[
 ['1. 명령·실행','실제 적용 action, 로봇 pose, 동작/정착 경계','속도 명령만으로 이동 거리·천 효과를 확정하지 않음'],
 ['2. 국소 천 변화','jaw 근처 천 동행, 주름·윤곽과 상대 위치 변화','열기0이나 국소 동행은 독립 지지·부착의 인증이 아님'],
 ['3. 유효 자유 구간','손·경계·housing을 여러 공개 시점에서 비교','색 띠·파란 면·가림만으로 통로 정체/깊이를 확정하지 않음'],
 ['4. 손목·전완 진행','같은 손 식별과 경계의 전후 관계','가림은 통과도 이탈도 아님. 이번 진행 판정은 미확인'],
 ['5. 별도 과제 결과','공식 raw5/50, 착의0, success=false','평가 정답을 actor 입력이나 시각 라벨로 역주입하지 않음'],
 ],[156,330,378],size=12)

# 10: Timing plot in vector graphics.
start('비용을 해석하려면 재생부터 분리해야 한다', '수집 클라이언트 wall 시간. 후속 QC·검토·백업·게시 시간은 이 그래프에 포함하지 않는다.',refs=['e34','e35','e36'])
legend=[('모델 호출 경로',TEAL),('기존 행동 재생',BLUE),('새 환경 요청·응답',AMBER),('기타 경과','#CED7DE')]
for i,(label,col) in enumerate(legend):
    x=48+i*218;rect(x,129,12,12,col);p(label,x+20,126,188,11)
scale=650/42
for i,key in enumerate(['e34','e35','e36']):
    run=DATA['runs'][key];y=180+i*87
    p(key.upper(),48,y,120,20,INK,True)
    vals=[run['actor_s'],run['replay_s'],run['new_env_s']]
    vals.append(run['wall_s']-sum(vals))
    x=170
    for value,(_,col) in zip(vals,legend):
        width=value/60*scale;rect(x,y, width,34,col)
        if width>48:p(f'{value/60:.1f}분',x+4,y+8,width-8,11,'#FFFFFF' if col!='#CED7DE' else INK)
        x+=width
    p(f"{run['wall_s']/60:.2f}분",x+10,y+5,90,14,INK,True)
    TEXT.append(f"{key.upper()}: 전체 {run['wall_s']:.3f}s / actor {run['actor_s']:.3f}s / replay {run['replay_s']:.3f}s / 새 환경 {run['new_env_s']:.3f}s\n")
text_note('모델 대기 중 물리는 정지한다. actor 시간은 CLI·통신·대기 등을 포함하며 순수 추론시간이 아니다.',455,12)

# 11: Dataset accounting.
start('데이터 수량과 독립적인 시연 가치는 다르다', '카탈로그의 demonstration만 집계. 연결 시험·실행 실패·미실행 계획과 사람 부분 시연은 이 수량에서 제외.',refs=['catalog','e35','e36'])
card(48,134,272,105,'33개 시연 기록','QC 통과 31 / 실패 2',TEAL,16)
card(344,134,272,105,'24,296개 전이','QC 통과 기록의 합계',BLUE,16)
card(640,134,272,105,'16,095개 replay','명시된 재생 완료 합계',AMBER,16)
rect(48,273,864,51,'#DCE4EB',8);rect(48,273,864*(16095/24296),51,BLUE)
p('알려진 replay 66.25%',66,287,500,17,'#FFFFFF',True)
p('나머지 8,201',645,287,245,17,INK,True)
p('나머지도 새 모델 행동만은 아니다. 정착·정리 등이 포함되며 초기 3개 기록은 replay 메타데이터가 null이다.',48,347,864,16)
p('4개 source-group 라벨 ≠ 독립적인 초기 조건 4개. 같은 prefix 분기를 독립 성공 표본으로 세지 않는다.',48,405,864,16)
TEXT.append('demonstration33 / QCpassed31 / QCfailed2 / transitions24296 / known replay16095 / remainder8201 / replay null3 / source-group labels4.\n')

# 12: Hypotheses, not diagnoses asserted as truth.
start('Codex 진단: 단일 실패 원인으로 단정하지 않는다', '직접 조작은 답을 대신하는 수단이 아니라, 경쟁하는 설명을 나눌 실험이다.',refs=['e36','redesign'])
table(['설명 후보','이미 있는 반증·제약','다음에 구분할 질문'],[
 ['명령이 전혀 실행되지 않는다','E19/E34/E36에서 실제 이동·하강과 settle 운동 확인','원하는 grasp 방향이 실제로 얼마나 만들어지는가?'],
 ['같은 손을 기억하면 해결된다','E31/E36은 같은 손을 유지해도 통과 미확인','손 identity와 유효 통로 정렬을 별개로 판정할 수 있는가?'],
 ['현재 형상·접근이 유효한 통로를 만든다','폭·주름·손 가림은 통로의 확정 증거가 아님','사람의 짧은 방향 교정으로 손–자유 경계 관계가 바뀌는가?'],
 ['더 많은 결정을 주면 해결된다','E35 18act, E36 10act 뒤 자발적 마감','무엇을 바꾸면 같은 정체를 벗어나는지 관측으로 명시할 수 있는가?'],
 ],[195,323,346],size=13)

# 13: Research matrix.
start('연구에서 가져올 것은 작고 검증 가능한 원칙', '네 논문의 고정 버전 초록·관련 본문을 확인했다. 코드·실험 재현은 수행하지 않았다.',refs=['encore','help','phil','feijoa'])
table(['연구','논문에서 확인한 내용','우리에게 적용할 후보','바로 옮기지 않을 것'],[
 ['ENCORE v1','시연 근거로 정책 프로그램 개발 후 동결 평가','개발자용 전후 근거 묶음','배포는 모델 호출 없음. 온라인 Astra와 동일 구조 아님'],
 ['HELP v2','사람 복구와 진행·복구 구간을 학습 후보로 선별','개입 구간·유용한 수정·정체를 분리 기록','PhyRC 자동 구간분류·학습 효과는 미구현/미검증'],
 ['PHIL v1','같은 query 상태·길이의 거절 예측/실제 실행 쌍','관측·요청·실제 행동·개입 경계 연결','다른 replay 상태를 동일 상태의 선호쌍으로 만들지 않음'],
 ['FEIJOA v1','실행 전후 효과 검증과 uncertain 판정','명령·운동·천 관계·통과의 분리 검수','시각 judge는 착의 참값이 아니며 타 로봇 통계 전용 불가'],
 ],[108,243,239,274],size=12)
text_note('이 원칙들은 설계 제안이다. 다른 과제의 성공률·비용 감소를 PhyRC 예상 개선율로 제시하지 않는다.',465,11)

# 14: Current readiness.
start('직접 조작과 사용자 개입은 세 가지 다른 기능', '현재 되는 구성요소, 연결 검증이 필요한 경로, 아직 없는 제어권 전환을 구분한다.',refs=['plan','teleop','feedback'])
table(['경로','현재 준비 수준','다음 검증'],[
 ['사람 단독 키보드','GUI 경로·키 입력 구성요소·과거 사람 기록 있음. 현재 브라우저 화면은 spectator','사용자 접속 → 실제 키 입력/해제 → 공개 pose 변화 → 기록/QC'],
 ['decision 경계 텍스트','CPU 검사를 거친 후보 patch. 미적용이며 실제 모델 전달 미검증','최신 소스 회귀 검토 → 한 번 전달/응답 확인 → 실제 행동 비교'],
 ['Astra ↔ 사람 직접 handoff','완성된 제어권 전환 경로 미구현','현재 행동/정착 완료, 한 제어원, 큐 처리, 인간 구간·재개 관측 기록'],
 ],[190,354,320],size=14)
text_note('사람 조작이 됐다고 직접 handoff까지 완료된 것은 아니다. 새 기능·시연은 이번 마감 이후의 별도 작업이다.',463,11)

# 15: Practical next work.
start('다음 작업: 전체 개편 대신 조건부 4–8시간', '사용자 접속·GUI/브라우저 연결이 준비된 경우의 추정. 연결 장애나 착의 성공을 보장하는 일정은 아니다.',refs=['plan'])
card(48,135,272,270,'1–1.5시간 · 근거 표','E34–E36 전후 관측, 적용 action, 실제 운동, 손·천 관계, unknown을 한 표로 연결.<br/><br/>기존 export 재사용. 원본 수정 없음.',TEAL,15)
card(344,135,272,270,'2–4시간 · 키보드 시험','새 run에서 사람 단독 연결·키 해제·포커스·두 로봇 매핑·짧은 실제 움직임 확인.<br/><br/>중간 상태 재생 후 사람 입력 연결은 별도 확인.',BLUE,15)
card(640,135,272,270,'0.5–1시간 · 시험 카드','유지할 관계, 바꿀 한 요소, 관측 근거, 중지 조건, 총시간을 기록.<br/><br/>운영 규칙으로 무검토 재시도와 예산 이월을 막음.',AMBER,15)
text_note('검사·실제 입력 확인·마감·정리에 0.5–1.5시간 확보. 연결이 막히면 그날은 재현 가능한 장애 진단까지.',438,13)

# 16: Next experiment protocol.
start('사람의 교정이 어떤 가설을 구분해야 하는가', '새 시연의 첫 목표는 완전 착의 성공이 아니라 입력·운동·관계 변화의 확인이다.',refs=['e36','plan','phil','rules'])
table(['질문','짧은 비교의 설계','남길 증거'],[
 ['자유 구간과 같은 손을 식별할 수 있는가?','같은 공개 시점에서 사람·모델의 경계/손 해석 비교','관측 ID·카메라·판정·대안 설명·unknown'],
 ['베이스 방향·housing 여유가 핵심인가?','연결 확인 후 한 요소의 짧은 사람 교정과 결과 관찰','요청/실제 action, 전후 pose, 정착, 천·손 관계'],
 ['기존 파지에서 유효한 진입이 가능한가?','허용할 파지 조건과 중지 기준을 사전에 고정','진행/복구/실패 구간·제어원·source group'],
 ],[254,324,286],size=14)
text_note('본 비교는 지정5RGB-D를 사용한다. 자유 viewport 진단 영상은 별도 보관하고 actor·학습 입력·자동 라벨·교사 정보로 쓰지 않는다.',449,12)

# 17: Closure and priorities.
start('이번 마감과 다음 개발의 경계', '좋은 부분 동작을 보존하면서, 아직 확인하지 못한 통과를 성공 데이터로 바꾸지 않는다.',refs=['backup35','backup36','plan','redesign'])
card(48,135,272,287,'완료','E35·E36 정상 종료<br/>전수 QC·공개 리뷰<br/>고정 백업 재다운로드 검증<br/>원본·GIF·근거 연결<br/>E37 이후 실행 없음',TEAL,16)
card(344,135,272,287,'다음 작은 작업','사람 단독 입력 경로 확인<br/>전후 근거와 unknown 정리<br/>같은 실패의 시험 조건 명시<br/><br/>개입은 단계별로 넓힘',BLUE,16)
card(640,135,272,287,'뒤로 미룰 것','직접 handoff 구현·검증<br/>검수 전 자동 학습<br/>새 VLA·critic·world model의 동시 도입<br/><br/>현재 학습 승인: unreviewed',AMBER,15)
text_note('채택 기준: 설명이 그럴듯한가보다, 어떤 관계가 바뀌었고 어떤 증거로 다시 확인할 수 있는가.',448,14)

# 18: Sources and scope.
start('원문과 재검토 경로', '슬라이드 하단의 근거 링크와 아래 원문을 클릭해 확인할 수 있다.',refs=['episodes','catalog','research'])
y=132
for key in ['encore','help','phil','feijoa']:
    item=DATA['sources'][key]
    title=escape(item['title'])
    p(f'<b>{item["label"]}</b> · {title}',48,y,864,13)
    p(f'<link href="{item["url"]}" color="{TEAL}">{item["url"]}</link>',48,y+39,864,10)
    y+=76
    TEXT.append(f'[{item["title"]}]({item["url"]})\n')
p('검토 범위: 기존 E00–E34 리뷰·코드 + E35/E36 공개 관측·실행·평가·QC·백업. 논문은 지정 절 확인이며 실험 재현 아님.',48,446,864,11,MUTED)
TEXT.append('과거 전 영상의 신규 전수 재시청·연구 재현은 하지 않았다. 분석용 개발자와 실행 actor의 접근 범위를 분리했다.\n')

C.save()
md = '# PhyRC E00–E36 통합 분석과 다음 사용자 개입 실험\n\n'
md += '[슬라이드 PDF](phyrc-e36-integrated-review.ko.pdf) · [재현·출처](README.ko.md)\n\n'
md += '\n'.join(TEXT)
(HERE/'report.ko.md').write_text(md)
used={}
for key,run in DATA['runs'].items():
    for name in ['manifest']:
        path=ROOT/run[name];used[run[name]]=hashlib.sha256(path.read_bytes()).hexdigest()
for key in ['e34','e35','e36']:
    phase=['initial','final'] if key=='e36' else ['final']
    cams=['robot_1_head','robot_0_head','robot_1_wrist','robot_0_wrist'] if key=='e36' else ['robot_1_head']
    for ph in phase:
        for cam in cams:
            rel=('docs/reports/20261114-e36-integrated-review/assets/e36-0835-'+cam+'.png' if key=='e36' and ph=='initial' else DATA['runs'][key]['images']+f'/{ph}-{cam}.png');used[rel]=hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()
provenance={'schema':'phyrc-public-review-slides-v1','pages':PAGE,'page_size_points':[W,H],
    'source_scope':'public exports, reviewed measurements, catalog, fixed backup receipts and primary research',
    'pdf_sha256':hashlib.sha256(PDF.read_bytes()).hexdigest(),'pdf_bytes':PDF.stat().st_size,
    'source_file_sha256':used,'renderer':'ReportLab 5.1.0','font':'NanumGothic / NanumGothicBold (embedded subsets)',
    'no_simulator_or_actor_execution':True,'no_original_media_mutation':True,
    'image_layout':'left robot_1, right robot_0; head above wrist; no pixel reflection',
    'data_sha256':hashlib.sha256((HERE/'report-data.json').read_bytes()).hexdigest(),
    'builder_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
(HERE/'provenance.json').write_text(json.dumps(provenance,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'pdf':str(PDF.relative_to(ROOT)),'pages':PAGE,'bytes':PDF.stat().st_size}))
