# 분할 화면은 왼쪽 robot_1, 오른쪽 robot_0

[메인 화면](../../README.md) · [시간순 갤러리](README.ko.md) · [변환 출처와 검사](assets/robot-layout-20261110/provenance.json)

실제 조작에서 로봇 위치를 쉽게 따라가도록 **화면의 왼쪽에는 robot_1, 오른쪽에는 robot_0**을 배치합니다. 카메라 이름과 픽셀을 함께 옮깁니다. 카메라 영상을 거울처럼 좌우 반전하거나 로봇 ID를 바꾸지 않습니다.

## 표시 규칙

| 자료 | 왼쪽 | 오른쪽 |
|---|---|---|
| 4분할 윗행 | robot_1_head | robot_0_head |
| 4분할 아랫행 | robot_1_wrist | robot_0_wrist |
| 현재 손목 depth 패널 | robot_1_wrist | robot_0_wrist |
| E11 분석 그림의 각 행 | robot_1의 RGB /depth /격자 | robot_0의 RGB /depth /격자 |
| 문서에서 두 로봇 카메라를 비교하는 표 | robot_1 | robot_0 |

5카메라 예시는 전체 화면을 첫 칸에 유지하고 `overview → robot_1_wrist → robot_0_wrist → robot_1_head → robot_0_head` 순으로 표시합니다. 단일 카메라, 같은 카메라의 시간순 비교, 앞/뒤 시점 비교에는 이 로봇별 열 교환을 적용하지 않습니다.

## 원본과 표시용 자료

2026-11-10에 이미 공개된 사건 MP4·GIF,5카메라 샘플,문서의 카메라 비교 표를 재배치했습니다. 사건 영상은 시간 footer를 유지하고 카메라 타일과 이름만 옮깁니다. 프레임 수·시각·재생 속도·원본 로봇 행동·점수는 바꾸지 않습니다. MP4는 브라우저 재생을 위해 H.264 High·yuv420p·CRF18로 재인코딩하며, 모든 프레임을 원본 타일 재배치 결과와 비교해 PSNR38dB 이상을 확인합니다. 압축에 따른 작은 픽셀 차이는 원본 관측의 변경과 구분합니다. GIF는 프레임마다 원래 색을 정확히 담는 팔레트를 사용하며, 모든 프레임의 RGB 픽셀과 재생 시간을 검사합니다. 정확한 파일별 크기·해시·시간·변환 검사는 provenance에서 확인합니다.

당시 모델에 실제 전달한 `first-call/*current_wrist_depth.png`, 분석용 원본 PNG와 evidence, source snapshot,학습 HDF5·평가·audit는 수정하지 않습니다. E11·E13–E15의 웹 그림은 [표시용 파생 폴더](assets/robot-layout-20261110/)를 사용하고 과거 입력 원본은 별도 링크로 남깁니다. 원본의 해시와 새 표시용 이미지의 해시는 다르므로 출처를 구분합니다.

기존26쪽 가이드 PDF의11·12쪽에도 같은 표시 배치를 적용합니다. 보고서의 E15 시점·결과·수치와 다른 시간순 이미지는 그대로 보존합니다.

## 데이터 순서는 그대로 유지

| 계약 | 유지하는 순서 |
|---|---|
| 공개 RGB-D 카메라 배열 | overview, robot_0_wrist, robot_1_wrist, robot_0_head, robot_1_head |
| 정책 행동 `(2,9)` | 행0=robot_0, 행1=robot_1 |
| 로봇·카메라 이름·좌표계 | 원래 의미 그대로 |

표시 순서를 데이터 배열 순서로 오해하지 않습니다. 향후 [`export_gallery_event.py`](../../scripts/export_gallery_event.py)와 [`wrist_depth.py`](../../participant/collection/wrist_depth.py)도 새 배치로 생성합니다. 과거 actor의 입력을 소급해서 바꿨다고 설명하지 않습니다.

## 재현

[`reorder_display_media.py`](../../scripts/reorder_display_media.py)는 변환 전 commit `3a255108a1c8e65428f19fa7caebb4b4684bc50f`에서 공개 파일만 읽습니다. 이미 변경된 영상에서 다시 좌우를 교환하지 않습니다. 원본 commit을 포함한 Git 이력과 Python의 NumPy·Pillow, FFmpeg가 필요합니다. 시뮬레이터와 모델은 실행하지 않습니다.

```bash
python scripts/reorder_display_media.py
```

변환 출처에는 78개 표시용 미디어의 원본·산출물 SHA256과 검사 범위를 기록했습니다. 모든 GIF·PNG의 RGB 픽셀은 타일 재배치 결과와 정확히 비교하고, MP4는 매 프레임의 PSNR을 비교했습니다. 해상도·프레임 수·재생 시간도 확인했습니다. PDF 11·12쪽의 변경은 [별도 검사 기록](../project/sessions/20261110-display-layout.json)에 연결합니다.

PDF는 PyMuPDF·fontTools와 한국어 글꼴이 있는 환경에서 `python scripts/reorder_display_guide.py --font /path/to/NotoSansCJK-Regular.ttc`로 다시 만들 수 있습니다. 원본26쪽 중11·12쪽의 비교 그림과 표시용 파생본 안내만 수정합니다.
