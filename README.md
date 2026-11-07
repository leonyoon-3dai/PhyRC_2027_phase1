# PhyRC 2027 · 두 로봇의 협력 착의

**최신 E23 · 방향 반전 뒤 팔 노출, 머리 접근까지 진행**

<a href="docs/gallery/assets/20261107-e23-arm-head-progress/event.mp4"><img src="docs/gallery/assets/20261107-e23-arm-head-progress/preview.gif" width="960" alt="E23 공개 네 카메라. 손과 전완이 드러나는 변화 뒤 머리 높이로 옷을 올리고 내려보는 과정"></a>

[**MP4 크게 보기**](docs/gallery/assets/20261107-e23-arm-head-progress/event.mp4) · [**방향 반전·전체 갤러리**](docs/gallery/20261107-astra-progress787-named-001.ko.md) · [**분석**](docs/collection/reviews/20261107-astra-progress787-named-001.ko.md) · [**피드백 남기기**](https://github.com/leonyoon-3dai/PhyRC_2027_phase1/issues/new?title=%5BE23+%ED%94%BC%EB%93%9C%EB%B0%B1%5D+%ED%8C%94+%EB%85%B8%EC%B6%9C%EA%B3%BC+%EB%A8%B8%EB%A6%AC+%EC%A0%91%EA%B7%BC&body=%EC%8B%9C%EB%8F%84%3A+E23+%2F+20261107-astra-progress787-named-001%0A%EC%98%81%EC%83%81+%EC%8B%9C%EA%B0%81+%EB%98%90%EB%8A%94+%EA%B2%BD%EA%B3%84%3A%0A%EC%B9%B4%EB%A9%94%EB%9D%BC%3A%0A%0A%EB%B3%B4%EC%9D%B4%EB%8A%94+%EC%82%AC%EC%8B%A4%3A%0A%0A%ED%95%B4%EC%84%9D%C2%B7%EC%A7%88%EB%AC%B8%3A%0A%0A%EB%8B%A4%EC%9D%8C%EC%97%90+%EB%B9%84%EA%B5%90%ED%95%A0+%EB%B0%A9%EB%B2%95%3A%0A) · [이전 E22 짧은 탐색](docs/gallery/20261107-astra-probe787-named-001.ko.md)

**공식 원점수 5/50 · 픽업5 · 착의0 · `success=false` · 1,180/1,180기록 검사 통과.** 경계의 전후 방향을 바꾸고 측면으로 이동한 뒤, 한쪽 경계를 올리면서 손·전완이 천 옆으로 더 드러났습니다. 이어 머리 높이로 올렸다 내렸지만 머리 통과는 확인되지 않았습니다. **시각적 팔 노출은 공식 소매 통과와 다르며, 착의 득점은 아직 없습니다.** 18판단 예산을 모두 사용해 종료했습니다. 최고5점, 중간 목표10점은 아직 미달성입니다.

1011–1180경계 · 170프레임 · 34초 · 4배 느리게입니다. 위는 로봇0/1 머리, 아래는 로봇0/1 손목이며 모델 대기는 제외했습니다. [영상 출처](docs/gallery/assets/20261107-e23-arm-head-progress/provenance.json) · [학습 검토 구간](docs/collection/reviews/20261107-astra-progress787-named-001-learning-segments.json)

전체 **1,180전이·시뮬레이션59초**, 새 구간은 **393전이·19.65초**입니다. 실제31분46초, 787재실행+284모델 행동+108정착+1예산 마감이며 18호출/18행동, 실제 depth 질의0회입니다. 전이1개는 관측→행동→다음 관측의0.05초 기록입니다.

**다음 E24 준비:** 마지막 지지·팔 노출 관계가 유지된 E23/1179에서 같은 `coordinated-task-progress`를 이어가도록 출발점을 채택했습니다. 30판단으로 미완료 머리·몸판 관계를 더 확인하는 연속 분기이며, 새 파지 방법이나 성공으로 세지 않습니다. 아직 실행하지 않았습니다. [현재 상태·검증·명령](docs/project/STATUS.md)

[**출발점 화면 5개 비교·피드백**](docs/gallery/20261107-support-startpoints.ko.md) · [**출발점·방법 데이터베이스**](docs/collection/catalog/README.ko.md) · [**0→5→10 구간 조합 장기계획**](docs/collection/research/2026-11-07-composable-scoring-data-plan.ko.md)

[더 이른5점 출발 후보](docs/collection/research/2026-11-07-earlier-support-startpoints.ko.md) · [의복 방향·경계의 경쟁 가설](docs/collection/research/2026-11-07-garment-direction-hypotheses.ko.md) · [다른 조작 대안](docs/collection/research/2026-11-07-post-overhead-method-options.ko.md) · [전체 갤러리](docs/gallery/README.ko.md)

**10점은 중간 목표이며 공식 확인 후 다음 득점 항목으로 계속 진행합니다.** 실패·복구와 원본을 보존하고, 합성 자료 확대는 장기 계획으로 구분합니다.

## 무엇을 만드는가

두 대의 Stretch 4가 공개 RGB-D 카메라와 로봇 상태를 이용해 앉은 마네킹에 티셔츠를 입히는 정책을 개발합니다. 라이브 화면 대신 실제 시도별 영상과 실패 분석을 보존하고, 조작 방법이 달라졌을 때 관측과 점수가 어떻게 달라지는지 비교합니다.

| 평가 항목 | 점수 |
|---|---:|
| 같은 그리퍼로 잡은 영역을5cm 올려 시뮬레이션3초 유지 | 5 |
| 첫 손이 소매를 통과해 밖으로 나옴 | 5 |
| 반대 어깨 / 두 번째 소매 / 왼쪽 위팔 / 오른쪽 위팔 | 각각5 |
| 목 / 앞면 방향 | 각각10 |

목표는 **공식 원점수10점을 거쳐 다음 득점 항목과 반복 가능한 착의 진전으로 나아가는 것**입니다. 목 우선 준비와 상방·하강을 비교했고, 짧은 진입 탐색 뒤 목적 있는 이동에서 새 팔–옷 관계가 나타났으나 착의 득점은 아직 없습니다. 이 관계를 보존한 연속 분기를 준비합니다. 어떤 경로든 실행·관측·공식 평가로 확인하며 모든 방법의 첫 단계를 소매로 고정하지 않습니다. 점수율은 픽업을 제외한 착의 점수를 첫 접촉부터 마지막 착의 득점까지의 시뮬레이션 시간으로 나눕니다. 픽업5점만으로는 양의 순위 점수가 생기지 않으며, 원점수10점도 전체 착의 성공과 다릅니다.

[점수 지도와 과제 설명](docs/project/CHALLENGE_GUIDE.ko.md) · [공식 평가 정의](docs/competition/EVALUATION.md) · [공식 대회](https://emprise.cs.cornell.edu/phyrc/challenge-2027/) · [원본 README](README.upstream.md)

## 시연 데이터와 검수

공개 관측 → 모델의 짧은 행동 → 실행·다음 관측 저장 → 별도 공식 평가 → 전수 기술 검사 → 시각 검수 순서입니다. **기술 검사 통과, 과제 성공, 학습 승인은 별도**이며 시도별 승인 상태를 보존합니다.

| 자료 | 내용 | 위치 |
|---|---|---|
| `policy.hdf5` | 20Hz 공개 관측·실제 행동·다음 관측 | 원본 collection, 비공개 HF 백업 |
| audit·평가·검사 | 전이·파일 정합성과 공식 점수 | actor 입력 밖의 비공개 검수 자료 |
| 실행 기록 | 프롬프트·최종 행동·구간·시간·소스 | [시도별 패키지](docs/collection/attempts/) |
| 영상·분석 | 실제 사건과 확인되지 않은 가설 | [갤러리](docs/gallery/README.ko.md) |

재실행 prefix, 새 모델 행동, 제어기 중립을 구분하며 같은 원본의 분기를 독립 시연이나 별도 검증 출처로 세지 않습니다. E07 행동 재실행은 정확한 천 상태 checkpoint 복원이 아닙니다.

[수집·검수 안내](docs/collection/README.ko.md) · [백업·복원 명령](docs/project/START_HERE.ko.md) · [재실행·분기](docs/collection/guides/continuation-and-branches.ko.md) · [사람 부분 시연](docs/gallery/20261026-human-pickup-transport.ko.md)

## 현재 구현과 다음 비교

| 구분 | 확인된 상태 |
|---|---|
| 최신 과제 시도 | E23 `20261107-astra-progress787-named-001` · 1,180/1,180검사 통과 · 5/50 · 18판단 예산 종료 |
| 모델·환경 | Astra/ultra · CLI0.166.0/exec · 고정 Isaac Sim6.0.1 · Chrome/WebRTC OFF |
| 실제 비교 | 목적 있는 접근·경계 방향 반전·측면 이동·한쪽 들기 뒤 팔 노출, 이어 머리 접근. 새 파지0회 |
| 관찰된 한계 | 손·전완 노출은 보이나 공식 착의0. 머리–입구 연결은 마지막에도 가려짐 |
| 다음 E24 준비 | E23 마지막1179경계·history1077/1161·같은 방법30판단 연속 분기 검수. 아직 미실행 |
| 검증 범위 | 실행 소스 전체302CPU 통과. 후속 코드 변경 없음. 기술 QC와 과제 성과는 별도 |
| 마감·원본 | E23 source952ec8d·시작clean·capture완료·host0·shell 관측 Python0·simulator0. [고정 원본 백업·재다운로드 검증 완료](docs/project/sessions/20261107-e23-backup-verification.json) |

[현재 상태·다음 명령](docs/project/STATUS.md) · [이번 세션 원문](docs/project/sessions/20261106-evening-resume.ko.md) · [방법 전환 기준](docs/project/sessions/20261106-method-switch-matrix.ko.md)

E16의 순차 지지 진단, E17의 다른 경계 재파지, E18의 운반·접근 변경을 실제 행동으로 구분합니다. E18의 추가 roll과 복구도 [학습 검토 구간](docs/collection/reviews/20261106-astra-guide470-depth-001-learning-segments.json)으로 보존했습니다. 실패·복구 자료의 가치와 좋은 행동 모방 승인 여부는 별개이며 현재 unreviewed입니다. 같은 재실행 출처를 독립 표본으로 세거나 점수에서 파지 정답을 만들지 않습니다.

[5점에서10점으로 가는 진단](docs/project/FIVE_TO_TEN.ko.md) · [시각적 가이드 PDF](docs/guide/PhyRC_2027_Repository_Guide_KR.pdf) · [연구 로드맵](docs/project/RESEARCH_ROADMAP.ko.md)

π₀.₅의 과거63전이·30회 갱신은 학습 경로 시험이었습니다. 이번 세션에서 새 정책 학습은 실행하지 않았습니다. VLA·RL 후속 비교는 승인된 자료와 공통 평가 조건을 갖춘 뒤 구분해서 기록합니다.

<details>
<summary>성능 메모 · 측정값과 속도 개선 근거 보존</summary>

E13의 4분·121표본에서 CPU 평균은 모델 대기2.08% / 동작19.14%, GPU 평균은0% /49.63%였습니다. RAM은70.76GiB 중 약16%, VRAM은9.06/44.99GiB입니다. E12의 모델 대기 포함 처리량은0.395전이/초, 동작 요청·기록 중에는1.15전이/초였습니다. 렌더 FPS와 다릅니다.

E15 전체28분29.785초 중 모델 호출 경로18분25.822초, 환경9분08.946초였습니다. 순수 모델 추론시간은 제공되지 않습니다. 메모리 부족이나 지속적인 전체 자원 포화 증거는 없지만 짧은 병목을 배제하지는 않습니다.

[원문·표본·측정 한계](docs/project/performance/20261106-performance-review.ko.md) · [단계 계측과 속도 후보](docs/project/performance/20261106-speedup-plan.ko.md) · [개편 전 성능 메모 전체](README.before-reorganization-20261106.ko.md)

</details>

## 코드와 이전 기록

[코드 길잡이](docs/project/CODE_MAP.ko.md) · [전체 문서 지도](docs/README.ko.md) · [개발 이력](docs/project/HISTORY.ko.md) · [E10~E15 일지](docs/project/sessions/20261106-resume10.ko.md) · [E15 마감 분석](docs/project/SESSION_WRAPUP_20261106.ko.md)

이전 시점의 상태와 계획은 이력으로 남깁니다. 현재 실행 여부와 적용된 기능은 위 표 및 [STATUS](docs/project/STATUS.md)를 기준으로 확인합니다. [개편 전 README](README.before-reorganization-20261106.ko.md) · [LICENSE](LICENSE) · [NOTICE](NOTICE) · [THIRD_PARTY](THIRD_PARTY.md)
