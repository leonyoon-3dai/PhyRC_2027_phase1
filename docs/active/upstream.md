# 공식 업데이트와 새 실험의 비교 기준

2026-11-23 KST 확인. 이번 연습 시연은 매회 **t=0의 새 reset, 셔츠–마네킹 마찰 0.35, 가장 가까운 테이블 한 곳**에서 시작한다. 같은 회차의 픽업부터 최종 착의까지 50점을 목표로 한다. 이전 경험은 보관 자료다.

## 11월 19일 공식 변경

| 변경 | 새 서버에서 확인할 것 |
|---|---|
| 12월 1일 leaderboard checkpoint 2부터 shirt–manikin 마찰 0.35. 공식 코드의 새 기본값은 이미 0.35다. 천 자체 접촉에도 적용되며 그리퍼·테이블은 0.5다. | 공식 기본값을 사용해 새 장면을 시작한다. 시작 로그의 `[Cloth/human friction] static=dynamic=0.35`와 소스 revision을 run 기록에 남긴다. |
| 순위의 1차 지표는 평가 레이아웃 전체의 평균 `result.raw_points`(픽업 포함, 최대 50), 동점 기준은 points/s다. | 새 동작은 추가 획득 항목과 반복 가능성부터 비교한다. 마지막 착의 득점까지의 속도는 그다음에 본다. |
| 판단 근거는 공식 evaluator의 유효한 결과다. 평가식은 `pickup-excluded-last-award-v9`이다. | `valid`, `raw_points`, `score_items`, `success`와 속도를 분리해 기록한다. 손목 근접, 영상상 통과 추정, 구간 종료는 각자 별도 라벨로 남긴다. |

[공식 마찰 변경](https://github.com/rirolab/PhyRC_2027_Challenge/commit/9afd513e926a82f1866a4b870135e33faba1358e) · [최종 순위 공지 변경](https://github.com/rirolab/PhyRC_2027_Challenge/commit/30c005e52b04b126d67f4eb2e601122c75843d0b) · [공식 평가 가이드](../competition/EVALUATION.md)

## 5점에서 50점까지 판정 읽기

| 항목 | 배점 | 공식 확인 조건 |
|---|---:|---|
| pickup | 5 | 같은 그리퍼가 잡은 영역을 최초 파지 위치보다 5 cm 이상 들어 3초 유지 |
| first_sleeve | 5 | 한 손의 손목과 손끝이 소매 구멍을 통과해 나옴 |
| opposite_shoulder | 5 | 옷 일부가 반대쪽 어깨 관절을 넘어감 |
| second_sleeve | 5 | 반대 손의 손목과 손끝이 다른 소매를 통과해 나옴 |
| left_upper_arm / right_upper_arm | 5 + 5 | 각 소매가 해당 위팔 일부를 덮음 |
| neck | 10 | 가슴이 셔츠 안쪽에 있고 머리·목이 목 구멍을 통해 나온 것이 확인됨 |
| front_orientation | 10 | 머리가 나온 상태에서 V넥 앞면 방향이 정면 45° 이내, 투영 방향 길이 2 cm 이상으로 0.5초 유지 |

누적 득점은 이후 자세가 변해도 보존된다. `success`는 서로 다른 소매 밖의 양손, 목 구멍 밖의 머리·목, 올바른 앞뒤 방향이 **동시에 0.5초** 확인됐는지를 따로 나타낸다. 점수 확인과 정책 입력의 경계를 지킨다. 점수·성공·audit·seed·내부 기하로 다음 행동이나 행동 정답을 만들지 않는다. [공식 규칙](../competition/RULES.md) · [판정·유효성·시간 정의](../competition/EVALUATION.md)

## 새 서버에서 물리 조건 확인

정상적인 전체 clone에는 옷·마네킹·텍스처·로봇의 원본 4개가 Git 파일로 들어 있다. `./run.sh prepare`가 나머지 잠긴 자산을 받아 검사하고 최신 물리 코드를 `.runtime/PhyRC_Sim/`에 복사한다. 기존 서버를 재사용할 때도 코드 업데이트 후 prepare를 다시 실행한다. `python3 scripts/fetch_assets.py --check`로 8개 파일을 확인한다. [설치](../competition/SETUP.md) · [자산 잠금](../../config/assets.lock.json) · [준비 스크립트](../../run.sh)

`run.sh`는 호스트의 `STRETCH4_*`를 컨테이너에 전달한다. 새 공식 조건에서는 예전 수동 마찰 override를 해제하고 첫 simulator 로그의 실제 적용값을 확인한다.

## 연습 테이블 선정과 공식 평가

기본 장면에서 두 로봇이 함께 접근하기 쉬운 테이블을 **두 초기 로봇 베이스에서 각 테이블 중심까지 수평 거리의 평균**으로 정했다. 인덱스 0, 1, 2, 3의 거리는 각각 약 3.492, 1.923, 1.923, 3.492 m다. 중앙 두 곳이 공동 최단이므로 기존 연습 시드 43이 실제로 선택하는 **인덱스 2(4개 중 세 번째, 월드 +X)** 한 곳으로 동률을 정한다. 이 수치는 기본 배치 정의를 계산한 감독용 근거다. 시연 모델은 공개 카메라에서 옷을 찾는다. [공식 장면의 테이블·로봇 배치](../../src/PhyRC_Sim/Env_StandAlone/Teleop_TShirt_Stretch4_Env.py) · [공식 의류 표본 추출](../../src/PhyRC_Sim/Env_Config/Garment/RandomSpawn.py)

연습 회차마다 reset 안정화 뒤 첫 관측부터 새 전이를 기록한다. 이 연습 결과는 한 테이블의 로컬 점수로 표기한다. 공식 제출은 주최 측 초기화와 평가 레이아웃 전체의 평균 원점수로 비교하고 동점이면 points/s를 적용한다. 웹에 입력하는 다음 동작 지시는 지정 카메라·공개 로봇 상태만으로 설명한다. [공식 데이터·행동 규격](../competition/POLICY.md)

## 반영 범위와 재확인

대조한 포크는 `777e5fab3cd038c181000dd2eb106e58945fc554`, 공통 조상은 `4dbbebcf93a06c1bfe12136eadc2e580f30125d6`, 공식 기준은 `9afd513e926a82f1866a4b870135e33faba1358e`다. 공통 조상 이후 공식 커밋 4개의 최종 차이는 5개 경로다. 아래 네 파일은 공식 버전과 바이트 단위로 같다. [저장소 안의 참가 안내서](../../README.upstream.md)에는 공식 변경을 모두 반영했다. 포크의 RGB·depth 미리보기는 왼쪽에 R1을 두므로 해당 캡션 한 줄만 포크의 기존 배치 설명을 유지했다. [수정 없는 공식 README](https://github.com/rirolab/PhyRC_2027_Challenge/blob/9afd513e926a82f1866a4b870135e33faba1358e/README.md)에서 원래 배치도 볼 수 있다. [실행 잠금](../../config/execution_lock.json)의 공식 소스 revision도 함께 갱신했다. 자산 잠금 파일의 SHA-256과 Isaac Sim 이미지는 이전과 같다. 중간에 도입했다 되돌린 복합 순위값을 사용하지 않는다.

- [물리 기본값](../../src/PhyRC_Sim/Env_Config/Garment/ZeroSceneFriction.py)
- [평가](../competition/EVALUATION.md) · [정책 실행](../competition/POLICY.md) · [용어](../competition/GLOSSARY.md)

다음 서버에서 수정 여부를 확인할 때만 아래 명령을 쓴다. 이번 정리의 GPU 검증은 사용자 리뷰 후 첫 실행에 남아 있다.

```bash
git fetch https://github.com/rirolab/PhyRC_2027_Challenge.git main
git diff --exit-code 9afd513e926a82f1866a4b870135e33faba1358e HEAD -- \
  src/PhyRC_Sim/Env_Config/Garment/ZeroSceneFriction.py \
  docs/competition/EVALUATION.md docs/competition/POLICY.md docs/competition/GLOSSARY.md
```
