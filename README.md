# PhyRC 2027

두 대의 **Stretch 4**로 마네킹에 티셔츠를 입히는 시뮬레이션 연구. 사람의 직접 조작과 **GPT Astra**로 시연을 수집하고, 관측과 행동을 검토해 다음 조작을 개선합니다.

| [**시연 영상**](docs/EPISODES.md) | [**E28 이후 계획**](docs/COLLECTION_PLAN.md) | [**Astra 코드·Hz**](docs/ASTRA.md) | [**클린 서버 시작**](docs/OPERATIONS.md) |
|:---:|:---:|:---:|:---:|
| E00–E27 전체 자료 | 옆에서 파지하고 입구 펼치기 | 관측부터 HDF5까지 | 설치·복원·검증·Codex CLI |

**현재:** E27까지 수집 완료, 새 수집은 중지 상태입니다. 최고 로컬 공식 평가기 **5/50점**, 착의 득점 **0**, 전체 성공은 미달입니다. E28 이후는 아래의 **새 계획**입니다.

## 최근 시연

<a href="docs/gallery/assets/20261107-e27-arm-approach/event.mp4"><img src="docs/gallery/assets/20261107-e27-arm-approach/preview.gif" width="960" alt="E27 실제 관측: 새 파지로 옷을 운반해 팔에 접근. 위는 머리, 아래는 손목 카메라. 각 행의 왼쪽 robot_1, 오른쪽 robot_0."></a>

**E27 — 새 파지로 운반하고 팔에 접근.** 소매 통과는 아직 확인되지 않았습니다.

[MP4 보기](docs/gallery/assets/20261107-e27-arm-approach/event.mp4) / [전체 overview](docs/collection/attempts/20261107-astra-regrasp698-progress-named-001/overview.mp4) / [장면 분석](docs/collection/reviews/20261107-astra-regrasp698-progress-named-001.ko.md) / [피드백](https://github.com/leonyoon-3dai/PhyRC_2027_phase1/issues/new?title=E27%20review)

<sub>분할 화면은 왼쪽 robot_1, 오른쪽 robot_0. 위 영상은 20 Hz 기록을 5 fps로 재생해 4배 느리며 모델 대기는 제외합니다. <a href="docs/gallery/assets/20261107-e27-arm-approach/provenance.json">영상 출처</a></sub>

## 다음 수집

![E28 이후 계획: 옷 양옆에서 파지, 아래 입구 펼치기, 한쪽 손목, 반대쪽 손목. 실제 시연이 아닌 개념도.](docs/assets/collection-plan.svg)

**정면 접근에서 측면 파지로 바꿉니다.** 옷 아래쪽을 충분히 펼쳐 한쪽 손목에 먼저 걸친 뒤, 이를 유지하며 반대쪽 손목으로 이어갑니다. 이전 `E27/928 same-arm` 후보는 과거 계획으로 보존합니다.

[단계별 관측 기준과 새 시작점 선택](docs/COLLECTION_PLAN.md)

## 수집한 과정

<table>
<tr>
<td width="33%" valign="top"><strong>사람 직접 조작</strong><br><a href="docs/videos/20261026-human-pickup-transport.mp4"><img src="docs/project/assets/visual-20261027/human-demo-t20.jpg" width="300" alt="키보드로 수집한 사람의 부분 시연"></a><br>집기·들기·운반의 부분 시연</td>
<td width="33%" valign="top"><strong>E07 협력 운반</strong><br><a href="docs/gallery/assets/20261106-astra-coordinated-fresh-001-multiview/event.mp4"><img src="docs/collection/milestones/20261106-astra-coordinated-fresh-001/images/approach-step-000700-overview.png" width="300" alt="E07 두 로봇이 옷을 함께 운반하는 실제 관측"></a><br>Astra 공동 조작과 후속 분기의 원본</td>
<td width="33%" valign="top"><strong>E25 새 파지</strong><br><a href="docs/gallery/assets/20261107-e25-rim-regrasp/event.mp4"><img src="docs/gallery/assets/20261107-e25-rim-regrasp/preview.gif" width="300" alt="E25 실제 열기, 위치 변경, 다시 잡기"></a><br>파지 위치를 바꾸고 천의 동행 확인</td>
</tr>
</table>

각 이미지를 누르면 영상이 열립니다. **[전체 시연 목록](docs/EPISODES.md)**에서 E00–E27 영상, 관측 이미지, 원본 manifest와 직접 부모를 한 번에 찾을 수 있습니다.

## 코드와 재현

| 확인할 것 | 바로 가기 |
|---|---|
| 공개 RGB-D → Astra JSON → 두 로봇 명령 → 데이터 | [실제 함수와 행동 예제](docs/ASTRA.md) |
| 20 Hz 기록 / 60 Hz 제어 / 240 Hz 물리 | [주기와 실행 길이](docs/ASTRA.md#4-시간과-실행-길이) |
| 새 서버에서 저장소만 읽고 시작 | [준비물부터 복원·검증까지](docs/OPERATIONS.md), [Codex 작업 지침](AGENTS.md) |

GitHub에는 코드와 선별 영상이 있습니다. 전체 시연 HDF5와 필수 자산 복원에는 **접근 권한이 있는 비공개 백업**이 필요합니다. 새 서버 가이드에 고정 revision과 해시 검증 절차를 함께 남깁니다.

[공식 챌린지](https://emprise.cs.cornell.edu/phyrc/challenge-2027/) / [점수·규칙](docs/project/CHALLENGE_GUIDE.ko.md) / [현재 상태](docs/project/STATUS.md) / [기록 보관함](docs/ARCHIVE.md) / [주최 측 README](README.upstream.md) / [LICENSE](LICENSE) / [NOTICE](NOTICE) / [THIRD_PARTY](THIRD_PARTY.md)
