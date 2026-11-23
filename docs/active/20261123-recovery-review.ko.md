# 11월 23일 착의 실험 회고와 복구 사례

세 번째 시연에서 옷이 처음 양팔 위를 지난 것처럼 보인 시점은 **281–301전이**였다. 몸판이 양쪽 전완에 겹쳤지만 먼 쪽 손목은 로봇 팔 뒤에 가려졌다. 바로 다음 12전이 동안 양 집게가 어깨 쪽으로 17–18cm 이동하자 맨손과 줄무늬 팔뚝이 천 위로 드러났다. 양팔이 밑단 안에 들어갔다가 빠졌는지, 처음부터 한 팔이 바깥에 있었는지는 이 영상만으로 가릴 수 없다. 어느 해석에서든 다음 행동을 결정할 때 빠졌던 증거는 **각 손목에서 몸판 안팎을 구별해 주는 자유 가장자리의 위치**였다. [281–301전이](https://jupyter-fjy7731zk.gobrev.dev/view/PhyRC-gallery/20261123T061400Z-astra62-both-arms-first/hold-0013.html) · [301–313전이](https://jupyter-fjy7731zk.gobrev.dev/view/PhyRC-gallery/20261123T061400Z-astra62-both-arms-first/hold-0014.html)

## 세 시연에서 실제로 얻은 것

| 시연 | 전이·구간 | 최종 원점수 | 다음 실행에 남길 경험 |
|---|---:|---:|---|
| 1 · 사용자 피드백 | 1,655 · 77 | **5/50** | 양끝 파지·운반은 가능했다. 손 앞에서 노란 밑단 두 겹이 함께 움직이면 손목 회전만 반복해도 통로가 납작하게 남을 수 있다. [마지막 손목 교정](https://jupyter-fjy7731zk.gobrev.dev/view/PhyRC-gallery/20261122T231754Z-astra62-dressing/hold-0077.html) |
| 2 · 한 팔 먼저 | 2,195 · 110 | **20/50** | 픽업 후 661전이에 왼쪽 첫 소매와 반대 어깨를 함께 얻었고, 698전이에 왼쪽 위팔까지 얻었다. 최종 상태에서는 왼쪽 위팔이 해당 소매에서 빠졌다. 정수리가 보였던 구간에도 목은 0점이었다. [첫 소매](https://jupyter-fjy7731zk.gobrev.dev/view/PhyRC-gallery/20261123T032900Z-astra62-autonomous/hold-0026.html) · [정수리와 위팔](https://jupyter-fjy7731zk.gobrev.dev/view/PhyRC-gallery/20261123T032900Z-astra62-autonomous/hold-0028.html) |
| 3 · 양팔 먼저 | 608 · 30 | **5/50** | 탁자에서 한쪽 테두리를 들고 다른 쪽 파지를 시험해 손 앞까지 열린 밑단을 운반했다. 가까운 손목 쪽 천을 유지한 채 먼 손을 다시 넣으려 했으나, 양손의 개별 지지를 확인하기 전에 종료했다. [테이블의 두 테두리](https://jupyter-fjy7731zk.gobrev.dev/view/PhyRC-gallery/20261123T061400Z-astra62-both-arms-first/hold-0007.html) · [종료 장면](https://jupyter-fjy7731zk.gobrev.dev/view/PhyRC-gallery/20261123T061400Z-astra62-both-arms-first/hold-0030.html) |

시연 3의 유일한 득점은 **202전이의 픽업 5점**이었다. 첫 소매, 반대 어깨, 두 번째 소매, 양쪽 위팔, 목, 앞면 방향은 모두 0점이다. 세 실행 모두 같은 연습 배치에서 독립적으로 시작했고 평가가 유효했으며 최종 착의 성공은 모두 false였다. 전체 **4,458전이, 217구간**을 수집했다. 세 원본의 전이 검증은 모두 통과했고 학습 승인 상태는 각각 `unreviewed`다. 시연 3의 사용자 개입 1회는 종료 요청이었다. [세 시연의 전체 GIF](../../README.md) · [점수 항목과 시연별 실행 ID](20261123-demonstrations.ko.md)

## 시연 3의 복구가 반복된 과정

아래의 가까운 손·먼 손은 해당 로봇 머리 카메라 기준이다. 좌우 팔이 확인되지 않은 구간은 마네킹의 해부학적 좌우로 단정하지 않았다. 거리 수치는 공개 로봇 상태에서 계산한 집게 기준점의 실제 이동이다. 천이나 손이 같은 거리만큼 움직였는지는 영상에서 따로 확인했다.

| 전이 | 보이는 변화와 판정 | 다음번에 확인할 것 |
|---|---|---|
| 50–70, 125–157 | R1이 윗단을 약 2.8cm 들자 아랫단은 상판 가까이에 남았다. R0을 당겼을 때 인접한 노란 테두리와 파란 천이 따라왔고, 양쪽을 들어도 R1 손목에 두 테두리 사이의 파란 면이 보였다. **입구를 만든 조작**을 확인할 수 있는 구간이다. [한 겹 들기](https://jupyter-fjy7731zk.gobrev.dev/view/PhyRC-gallery/20261123T061400Z-astra62-both-arms-first/hold-0003.html) · [들어 올리기](https://jupyter-fjy7731zk.gobrev.dev/view/PhyRC-gallery/20261123T061400Z-astra62-both-arms-first/hold-0008.html) | 테이블 지지가 남아 있을 때 한쪽씩 시험하고, 공중에서도 두 테두리가 벌어져 있는지 확인한다. |
| 281–313 | 301전이에는 파란 천이 양 전완을 가로질렀다. 이어진 한 행동에서 R0·R1이 어깨 쪽으로 18.2·17.0cm, 위로 각각 약 2.9cm 이동했다. 313전이에 한쪽 맨손이 천 위에 드러났고 반대 손목은 가려졌다. [전환 직전](https://jupyter-fjy7731zk.gobrev.dev/view/PhyRC-gallery/20261123T061400Z-astra62-both-arms-first/hold-0013.html) · [직후](https://jupyter-fjy7731zk.gobrev.dev/view/PhyRC-gallery/20261123T061400Z-astra62-both-arms-first/hold-0014.html) | 먼 손의 손끝→손목과 밑단의 앞뒤 경계를 다른 시점에서 연결한다. 한쪽만 판별되면 그쪽을 받치고 반대쪽에만 여유를 준다. |
| 363–382, 503–521, 558–576 | 팔꿈치 쪽으로 천을 보낼 때마다 가까운 손목 위의 천은 남고 먼 주먹이 몸판 위에 다시 보였다. 576전이에는 집게 높이 차를 바꾼 뒤에도 양쪽 손목 카메라를 로봇 하우징이 가렸다. **다른 명령 뒤 같은 장면이 반복된** 사례다. [첫 재출현](https://jupyter-fjy7731zk.gobrev.dev/view/PhyRC-gallery/20261123T061400Z-astra62-both-arms-first/hold-0017.html) · [두 번째](https://jupyter-fjy7731zk.gobrev.dev/view/PhyRC-gallery/20261123T061400Z-astra62-both-arms-first/hold-0025.html) · [세 번째](https://jupyter-fjy7731zk.gobrev.dev/view/PhyRC-gallery/20261123T061400Z-astra62-both-arms-first/hold-0028.html) | 같은 주먹이 같은 바깥쪽에 다시 나타나면 전진을 멈춘다. 한쪽 파지를 유지하고 입구를 손끝 앞으로 돌려, 먼 손을 옆에서 볼 수 있는 자리에서 짧게 다시 건다. |
| 487–495, 542–550 | R1은 베이스의 기울기를 줄였으나 올리려던 집게가 2.93cm 내려갔다. 다른 시도에서 R0은 바깥으로 뻗으려 했으나 집게가 안쪽으로 4.15cm 움직였다. 가려진 원단을 해석하기 전부터 **의도와 실측의 방향이 달랐다.** [R1 높이](https://jupyter-fjy7731zk.gobrev.dev/view/PhyRC-gallery/20261123T061400Z-astra62-both-arms-first/hold-0023.html) · [R0 옆 이동](https://jupyter-fjy7731zk.gobrev.dev/view/PhyRC-gallery/20261123T061400Z-astra62-both-arms-first/hold-0026.html) | 반대쪽에서 지지하면서 베이스 자세·팔 뻗기를 조정한다. 짧은 한 번의 이동으로 집게와 자유 테두리가 원하는 방향으로 함께 움직이는지 본다. |
| 576–603, 603–608 | R0이 손목을 돌려도 파란 주름이 집게 옆에 겹쳤다. 다음 행동에서 R1이 반대 밑단을 받친 채 R0을 열자 주름이 떨어지고 두 집게 끝과 옆의 노란 밑단이 다시 보였다. **시야와 접근을 일부 회복한 장면**이다. 다음 재파지나 먼 손 진입은 검증하지 않았다. [접힌 상태](https://jupyter-fjy7731zk.gobrev.dev/view/PhyRC-gallery/20261123T061400Z-astra62-both-arms-first/hold-0029.html) · [한쪽을 열고 종료](https://jupyter-fjy7731zk.gobrev.dev/view/PhyRC-gallery/20261123T061400Z-astra62-both-arms-first/hold-0030.html) | 노란 자유 끝을 다시 잡은 뒤 그 부위가 따로 따라오는지 시험한다. 먼 손을 확인할 시야가 확보되면 그쪽만 다시 걸친다. |

## 다음 시연에서 비교할 세 장면

1. **양팔 걸침.** 각 손끝을 손목까지 따로 추적하고 밑단의 가까운 테두리와 먼 테두리가 어느 쪽에 있는지 확인한다. 손목 하우징이 결합부를 가리면 머리·전체 카메라를 쓰고, 표면이 보일 때 손목 깊이로 간격을 확인한다. 양팔의 지지가 작은 이동 뒤에도 유지되면 목둘레 쪽으로 진행한다.
2. **목둘레 통과.** 파란 몸판의 주름, 노란 밑단, 실제 목둘레를 구별한다. 양쪽 팔을 받치는 동안 목둘레가 정수리를 넘어 목 주변으로 내려가 얼굴이 드러나는지 본다. 시연 2의 2111–2138전이에는 R1이 올라가면서 몸판 모서리만 넓게 펴지고 정수리 쪽 트임은 거의 움직이지 않았다. 이런 변화라면 지지 쪽을 유지하며 다른 자유 가장자리를 찾는다. [실패 비교](https://jupyter-fjy7731zk.gobrev.dev/view/PhyRC-gallery/20261123T032900Z-astra62-autonomous/hold-0108.html)
3. **두 소매와 몸통 안착.** 한 팔을 조정할 때마다 반대 손과 목둘레가 유지되는지 확인한다. 각 손끝·손목이 서로 다른 소매 밖으로 나왔는지, 양 위팔이 덮였는지, 앞면이 바르게 놓였는지 순서대로 기록한다. 두 손과 목이 통과한 뒤에도 위팔과 앞면이 남을 수 있다. **50/50점과 최종 자세의 실제 유지 여부**는 각각 검증할 항목이다. [항목별 채점 기준](experiment.md) · [공식 시연 관찰](autonomous.md)

## 실패 데이터를 다시 찾는 법

[복구 사례 색인 16건](20261123-recovery-cases.jsonl)에는 각 구간의 실행 ID, HOLD ID, 전이 시작·끝, 관찰 메모, 구간 전후의 누적 점수가 있다. `compare_with`는 비교할 다른 사례의 ID다. 시연 1의 좁은 입구와 시연 3의 테이블 위 가장자리 분리, 시연 3의 주름이 고정된 장면과 직후 한쪽 집게를 연 장면처럼 조건이 달라진 쌍을 함께 볼 수 있다.

색인의 `failure`는 **그 구간에서 의도한 국소 변화가 확인되지 않거나 역방향 변화가 관측된 경우**다. `uncertain`은 관계가 가려진 경우, `partial_recovery`는 다음 조작이 가능해진 범위까지만 확인한 경우다. `credited_progress`에는 평가에서 검증한 득점이 있다. `raw_points_before/after`는 감독용이다. 다음 시연의 actor는 현재 실행의 지정 카메라와 공개 로봇 상태를 사용한다.

서버가 바뀌어도 실행 ID와 HOLD ID는 동일하다. 비공개 검토 번들의 `segments.jsonl`에서 두 ID를 찾으면 `media/<run_id>/<segment_id>.mp4`로 해당 영상에 접근할 수 있다. 보존된 수집 데이터에서 `data/demo_0/actions[start_step:end_step]`는 이 구간의 실제 행동이다. 같은 실행의 전후 구간은 같은 데이터 분할에 둔다. 전체 GIF와 이 색인은 저장소에서 바로 볼 수 있다.
