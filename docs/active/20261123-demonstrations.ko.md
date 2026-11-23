# 11월 22–23일 착의 시연 기록

세 회차는 같은 시드 43, 테이블 인덱스 2, 셔츠–마네킹 마찰 0.35에서 각각 새로 시작했다. 같은 초기 배치를 다시 사용한 비교이며, 원점수는 회차별 로컬 공식 평가기의 누적값이다. 새 회차의 실제 진척은 [비공개 갤러리](https://jupyter-fjy7731zk.gobrev.dev/view/PhyRC-review.html)에서 확인할 수 있다.

| 시연 | 실행 ID | 기록 |
|---|---|---|
| 1 · 사용자 피드백 | `20261122T231754Z-astra62-dressing` | 1655전이 · 77구간 · **5/50**, 착의 성공 false. [마지막 구간](https://jupyter-fjy7731zk.gobrev.dev/view/PhyRC-gallery/20261122T231754Z-astra62-dressing/hold-0077.html) |
| 2 · GPT 단독, 한 팔과 얼굴 먼저 | `20261123T032900Z-astra62-autonomous` | 2195전이 · 110구간 · **20/50**, 착의 성공 false. 사용자 개입 1회는 종료 요청이었다. [종료 구간](https://jupyter-fjy7731zk.gobrev.dev/view/PhyRC-gallery/20261123T032900Z-astra62-autonomous/hold-0110.html) |
| 3 · GPT 단독, 양팔 먼저 | `20261123T061400Z-astra62-both-arms-first` | 부모·재생 행동 없이 0전이에서 출발. 양팔 걸침 → 목둘레 넘기기 → 양쪽 소매 재정렬 → 몸통 안착. [첫 관측](https://jupyter-fjy7731zk.gobrev.dev/view/PhyRC-gallery/20261123T061400Z-astra62-both-arms-first/hold-0001.html) |

## 1 · 양끝을 잡고 손 앞에 접근

630전이에 픽업 5점을 얻었다. 양 집게가 천을 들고 손 앞까지 갔지만 손목을 돌려도 노란 테두리 두 겹이 충분히 벌어지는 모습을 확인하기 어려웠다. 이후 시연에서는 테이블이 천을 받치고 있을 때 각 파지를 따로 시험하고, 운반 전 두 테두리 사이의 공간을 측면과 손목 깊이 영상으로 확인한다. [구간별 원인 분석과 공식 영상 비교](guided-retrospective.json)

## 2 · 한 팔과 얼굴까지 올라간 구간의 점수

| 전이 | 이번에 인정된 항목 | 누적 | 검토 구간 |
|---:|---|---:|---|
| 161 | 픽업 +5 | 5/50 | [픽업](https://jupyter-fjy7731zk.gobrev.dev/view/PhyRC-gallery/20261123T032900Z-astra62-autonomous/hold-0007.html) |
| 661 | 마네킹 왼손이 첫 소매를 통과 +5, 반대쪽 어깨 +5 | 15/50 | [632–664전이](https://jupyter-fjy7731zk.gobrev.dev/view/PhyRC-gallery/20261123T032900Z-astra62-autonomous/hold-0026.html) |
| 698 | 왼쪽 위팔에 소매가 걸림 +5 | **20/50** | [676–710전이 · 정수리가 보이는 장면](https://jupyter-fjy7731zk.gobrev.dev/view/PhyRC-gallery/20261123T032900Z-astra62-autonomous/hold-0028.html) |
| 2195 · 종료 | 이후 추가 득점 없음 | **20/50** | [마지막 관측](https://jupyter-fjy7731zk.gobrev.dev/view/PhyRC-gallery/20261123T032900Z-astra62-autonomous/hold-0110.html) |

**목 0/10, 두 번째 소매 0/5, 오른쪽 위팔 0/5, 앞면 방향 0/10.** 천이 얼굴과 정수리를 덮는 장면이 있었으나 공식 평가기는 목둘레를 통한 머리·목 통과를 인정하지 않았다. 왼쪽 위팔 점수는 698전이에 얻었고 최종 프레임에서는 왼쪽 위팔이 해당 소매 안에 자리잡은 상태가 풀렸다. 속도 점수 0.8753점/초는 픽업을 제외한 15점을 공식 접촉–마지막 득점 시간 17.1375초로 나눈 값이다.

| 구간에서 확인한 현상 | 3회차에 반영한 조작 |
|---|---|
| 1747–1773전이에 파란 소매 가장자리가 반대 손 옆에 남았고 손끝은 가려졌다. 1922–1943전이에는 파란 천이 그 손을 덮었지만 해당 소매로 손끝이 빠져나온 장면은 확인하기 어려웠다. [두 번째 손과 입구](https://jupyter-fjy7731zk.gobrev.dev/view/PhyRC-gallery/20261123T032900Z-astra62-autonomous/hold-0090.html) · [소매 재시도](https://jupyter-fjy7731zk.gobrev.dev/view/PhyRC-gallery/20261123T032900Z-astra62-autonomous/hold-0100.html) | 양팔에 한쪽씩 먼저 걸친 뒤 두 지점이 함께 유지되는지 본다. 머리가 나온 뒤 각 손목과 손끝이 올바른 소매 출구 밖에 드러나는지 다시 확인한다. |
| 2111–2138전이에 R1 집게가 약 5.3cm 올라갔지만 주로 파란 모서리가 움직였고 정수리 쪽 트임은 거의 움직이지 않았다. [목둘레와 주름의 움직임](https://jupyter-fjy7731zk.gobrev.dev/view/PhyRC-gallery/20261123T032900Z-astra62-autonomous/hold-0108.html) | 목둘레의 테두리가 실제로 이동하는지 확인한다. 얼굴이 가려지거나 가장자리만 움직이면 한쪽 지지를 유지하고 장력 또는 파지 위치를 바꾼다. |

## 3 · 공식 영상의 흐름을 따르는 새 시연

공식 전후면 영상에서 약 19.5–24초에는 열린 옷이 양손 앞으로 이동하고, 약 26–30초에는 머리 쪽으로 올라간다. 약 32–34초에는 양팔이 서로 다른 소매 너머에 보이고, 마지막 35.7초에는 얼굴이 드러나며 밑단이 몸통 아래로 내려온다. 천이 손·머리를 가리는 동안의 정확한 통과 시점은 판별하기 어렵다. 이번 회차는 이 장면을 바탕으로 사용자가 지정한 순서를 시험한다. [공식 전체 영상](https://emprise.cs.cornell.edu/phyrc/assets/c27/media/teleop-overhead.mp4) · [공식 전후면 영상](https://github.com/rirolab/PhyRC_2027_Challenge/blob/9afd513e926a82f1866a4b870135e33faba1358e/docs/videos/Front_Back_8x.mp4)

같은 시점에 양팔이 옷을 지지했는지, 머리를 넘길 때 첫 팔이 빠졌는지, 마지막에 마네킹의 어느 쪽 손이 어느 소매 밖으로 나왔는지를 각 구간에서 구별한다. GPT는 지정 RGB-D와 실제 움직임을 비교해 다음 동작을 선택한다. 운영 측은 별도로 평가 이벤트와 최종 시점의 유지 여부를 대조한다. [실행 지침](autonomous.md) · [3회차에 사용한 프롬프트](../../participant/collection/prompts/autonomous_full_dressing.txt)

## 로컬 검증과 비공개 보관

첫 두 시연은 각 HDF5의 1655/1655, 2195/2195전이가 기술 검증을 통과했고, 각 최종 `result.json`의 `valid`는 true다. 모두 학습용 승인 상태는 `unreviewed`이다. 두 번째 시연의 원본은 110개 구간의 행동 묶음 220건을 HDF5와 대조했고, 판단 시점의 RGB-D 관측 221세트를 확인했다. 운영 서버에서 확인할 상대 경로는 다음과 같다.

| 자료 | 위치 |
|---|---|
| 항목별 최초 득점과 최종 결과 | `output/collections/RUN/evaluation/<episode>/score_events.jsonl`, `result.json` |
| 전수 검증과 훈련 승인 상태 | `output/collections/RUN/validation.json` |
| 행동·관측과 검증된 보존 파일 목록 | `output/preservation/RUN-final.receipt.json` |
| 구간 영상·분석·종료 기록 | `output/review-exports/RUN.zip` |
