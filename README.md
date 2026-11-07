# PhyRC 2027 · 두 로봇의 협력 착의

**최신 E25 · 한쪽 가장자리 재파지와 국소 천 동행 검사**

<a href="docs/gallery/assets/20261107-e25-rim-regrasp/event.mp4"><img src="docs/gallery/assets/20261107-e25-rim-regrasp/preview.gif" width="960" alt="E25 공개 네 카메라. 로봇0 지지를 유지하며 로봇1을 열고 다른 낮은 경계로 옮겨 다시 닫은 뒤 천 동행과 경계 반응을 확인하는 과정"></a>

[**MP4 크게 보기**](docs/gallery/assets/20261107-e25-rim-regrasp/event.mp4) · [**전체·지지 검사 영상**](docs/gallery/20261107-astra-opposing563-named-001.ko.md) · [**분석**](docs/collection/reviews/20261107-astra-opposing563-named-001.ko.md) · [**피드백 남기기**](https://github.com/leonyoon-3dai/PhyRC_2027_phase1/issues/new?title=%5BE25+%ED%94%BC%EB%93%9C%EB%B0%B1%5D+%ED%95%9C%EC%AA%BD+%EC%9E%AC%ED%8C%8C%EC%A7%80%EC%99%80+%EC%A7%80%EC%A7%80+%EA%B2%80%EC%82%AC&body=%EC%8B%9C%EB%8F%84%3A+E25+%2F+20261107-astra-opposing563-named-001%0A%EC%98%81%EC%83%81+%EC%8B%9C%EA%B0%81+%EB%98%90%EB%8A%94+%EA%B2%BD%EA%B3%84%3A%0A%EC%B9%B4%EB%A9%94%EB%9D%BC%3A%0A%0A%EB%B3%B4%EC%9D%B4%EB%8A%94+%EC%82%AC%EC%8B%A4%3A%0A%0A%ED%95%B4%EC%84%9D%C2%B7%EC%A7%88%EB%AC%B8%3A%0A%0A%EB%8B%A4%EC%9D%8C%EC%97%90+%EB%B9%84%EA%B5%90%ED%95%A0+%EB%B0%A9%EB%B2%95%3A%0A) · [이전 E24 진입·복구](docs/gallery/20261107-astra-progress1179-named-001.ko.md)

**공식 원점수 5/50 · 픽업5 · 착의0 · `success=false` · 698/698기록 검사 통과.** 테이블 위에서 로봇0 쪽 지지를 유지하고 로봇1을 열어 낮은 곡선 경계로 옮겼습니다. 한 번 위치를 보정해 다시 닫은 뒤, 약2.7cm 상승에 새 파지 부근 천이 따라오는 모습을 확인했습니다. **국소 동행의 잠정 근거는 있지만, 반대인 두 입구 경계의 개방은 미확인입니다.** 차등 움직임·시점 복구 뒤 모델이 자율 종료했으며 운반·진입은 실행하지 않았습니다. 최고5점, 중간 목표10점은 아직 미달성입니다.

591–698경계 · 108프레임 · 21.6초 · 4배 느리게입니다. 위는 로봇0/1 머리, 아래는 로봇0/1 손목이며 모델 대기는 제외했습니다. [영상 출처](docs/gallery/assets/20261107-e25-rim-regrasp/provenance.json) · [학습 검토 구간](docs/collection/reviews/20261107-astra-opposing563-named-001-learning-segments.json)

전체 **698전이·시뮬레이션34.9초**, 새 구간은 **135전이·6.75초**입니다. 실제20분26초, 563재실행+93모델 행동+42정착이며 15호출·13행동+자율종료1판단입니다. 깊이 질의1회6유효점·질의 중 물리0, 추가 마감 전이0입니다. 전이1개는 관측→행동→다음 관측의0.05초 기록입니다.

**다음 E26 준비:** E18/787·history719/771에서 기존 파지를 유지하고, 먼저 안내할 손·지지/안내 역할·몸통 입구의 접근면을 바꾸는 `coordinated-leading-hand-swap`을 선택했습니다. 실제 손·역할 교환은 현재 관측으로 구분해 기록하며, 단순 비대칭 움직임이나 이름 변경으로 대신하지 않습니다. 22판단/max1400·정착6을 유지합니다. 아직 실행 전입니다. [현재 상태·명령](docs/project/STATUS.md) · [방법 설명](docs/collection/research/2026-11-07-leading-hand-candidate.ko.md)

[**출발점 화면 5개 비교·피드백**](docs/gallery/20261107-support-startpoints.ko.md) · [**출발점·방법 데이터베이스**](docs/collection/catalog/README.ko.md) · [**0→5→10 구간 조합 장기계획**](docs/collection/research/2026-11-07-composable-scoring-data-plan.ko.md)

**10점은 중간 목표이며 공식 확인 후 다음 득점 항목으로 계속 진행합니다.** 실패·복구와 원본을 보존하고, 합성 자료 확대는 장기 계획으로 구분합니다.

## 무엇을 만드는가

두 대의 Stretch 4가 공개 RGB-D 카메라와 로봇 상태를 이용해 앉은 마네킹에 티셔츠를 입히는 정책을 개발합니다. 라이브 화면 대신 실제 시도별 영상과 실패 분석을 보존하고, 조작 방법이 달라졌을 때 관측과 점수가 어떻게 달라지는지 비교합니다.

| 평가 항목 | 점수 |
|---|---:|
| 같은 그리퍼로 잡은 영역을5cm 올려 시뮬레이션3초 유지 | 5 |
| 첫 손이 소매를 통과해 밖으로 나옴 | 5 |
| 반대 어깨 / 두 번째 소매 / 왼쪽 위팔 / 오른쪽 위팔 | 각각5 |
| 목 / 앞면 방향 | 각각10 |

목표는 **공식 원점수10점을 거쳐 다음 득점 항목과 반복 가능한 착의 진전으로 나아가는 것**입니다. 목 우선 준비와 상방·하강을 비교했고, 짧은 진입 탐색 뒤 목적 있는 이동에서 새 팔–옷 관계가 나타났으나 착의 득점은 아직 없습니다. E25에서는 실제 한쪽 재파지와 국소 동행을 확인했지만 입구 관계는 미해결이었습니다. 다음에는 안내할 손·역할·접근면 변경을 비교합니다. 어떤 경로든 실행·관측·공식 평가로 확인하며 모든 방법의 첫 단계를 소매로 고정하지 않습니다. 점수율은 픽업을 제외한 착의 점수를 첫 접촉부터 마지막 착의 득점까지의 시뮬레이션 시간으로 나눕니다. 픽업5점만으로는 양의 순위 점수가 생기지 않으며, 원점수10점도 전체 착의 성공과 다릅니다.

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
| 최신 과제 시도 | E25 `20261107-astra-opposing563-named-001` · 698/698검사 통과 · 5/50 · 모델 자율 종료 |
| 모델·환경 | Astra/ultra · CLI0.166.0/exec · 고정 Isaac Sim6.0.1 · Chrome/WebRTC OFF |
| 실제 비교 | R0 지지 유지·R1 release→다른 경계 placement→보정1→reclose1, 국소 동행·차등 반응 검사 |
| 관찰된 한계 | 새 파지 국소 동행은 잠정 긍정, 반대 두 lip의 개방은 미확인. 운반/진입0·착의0 |
| 다음 E26 준비 | E18/787·history719/771·다른 leading hand/역할/접근면 비교·22판단/max1400/settle6. 아직 미실행 |
| 검증 범위 | M2 선택 분기 통합·전체 CPU317개 통과(31.785초). [검증 기록](docs/project/sessions/20261107-leading-hand-validation.json). 실제 조작 효과는 별도 |
| 마감·원본 | E25 source68658c9·시작clean·capture완료·host0·shell Python0·simulator0. [고정 원본 백업·재다운로드 검증 완료](docs/project/sessions/20261107-e25-backup-verification.json) |

[현재 상태·다음 명령](docs/project/STATUS.md) · [이번 세션 원문](docs/project/sessions/20261106-evening-resume.ko.md) · [방법 전환 기준](docs/project/sessions/20261106-method-switch-matrix.ko.md)

E16의 순차 지지 진단, E17의 다른 경계 재파지, E18의 운반·접근 변경을 실제 행동으로 구분합니다. E18의 추가 roll과 복구도 [학습 검토 구간](docs/collection/reviews/20261106-astra-guide470-depth-001-learning-segments.json)으로 보존했습니다. 실패·복구 자료의 가치와 좋은 행동 모방 승인 여부는 별개이며 현재 unreviewed입니다. 같은 재실행 출처를 독립 표본으로 세거나 점수에서 파지 정답을 만들지 않습니다.

[5점에서10점으로 가는 진단](docs/project/FIVE_TO_TEN.ko.md) · [시각적 가이드 PDF](docs/guide/PhyRC_2027_Repository_Guide_KR.pdf) · [연구 로드맵](docs/project/RESEARCH_ROADMAP.ko.md)

π₀.₅의 과거63전이·30회 갱신은 학습 경로 시험이었습니다. 이번 세션에서 새 정책 학습은 실행하지 않았습니다. VLA·RL 후속 비교는 승인된 자료와 공통 평가 조건을 갖춘 뒤 구분해서 기록합니다.

<details>
<summary>성능 메모 · 측정값과 속도 개선 근거 보존</summary>

E13의 4분·121표본에서 CPU 평균은 모델 대기2.08% / 동작19.14%, GPU 평균은0% /49.63%였습니다. RAM은70.76GiB 중 약16%, VRAM은9.06/44.99GiB입니다. E12의 모델 대기 포함 처리량은0.395전이/초, 동작 요청·기록 중에는1.15전이/초였습니다. 렌더 FPS와 다릅니다.

E15 전체28분29.785초 중 모델 호출 경로18분25.822초, 환경9분08.946초였습니다. 순수 모델 추론시간은 제공되지 않습니다. 메모리 부족이나 지속적인 전체 자원 포화 증거는 없지만 짧은 병목을 배제하지는 않습니다.

E23에서는 모델 호출 경로821.40초(43.09%)·환경 요청1031.87초(54.13%)가 들었습니다. 실제0→563 재실행 요청은484.94초였지만, 짧은 출발점의 이후 조작 비용까지 줄어든다는 뜻은 아닙니다. [E23 구간별 시간 분석](docs/project/performance/20261107-e23-stage-timing.ko.md)

E24의 실제 준비 재실행에서563→1179 구간은616전이·54요청·551.558초(9분12초)였습니다. 짧은 출발점이 이후 재파지·전체 시도 시간을 얼마나 바꾸는지는 별도 비교합니다. [E24 실제 재실행·질의 비용](docs/project/performance/20261107-e24-stage-timing.ko.md)

[원문·표본·측정 한계](docs/project/performance/20261106-performance-review.ko.md) · [단계 계측과 속도 후보](docs/project/performance/20261106-speedup-plan.ko.md) · [개편 전 성능 메모 전체](README.before-reorganization-20261106.ko.md)

</details>

## 코드와 이전 기록

[코드 길잡이](docs/project/CODE_MAP.ko.md) · [전체 문서 지도](docs/README.ko.md) · [개발 이력](docs/project/HISTORY.ko.md) · [E10~E15 일지](docs/project/sessions/20261106-resume10.ko.md) · [E15 마감 분석](docs/project/SESSION_WRAPUP_20261106.ko.md)

이전 시점의 상태와 계획은 이력으로 남깁니다. 현재 실행 여부와 적용된 기능은 위 표 및 [STATUS](docs/project/STATUS.md)를 기준으로 확인합니다. [개편 전 README](README.before-reorganization-20261106.ko.md) · [LICENSE](LICENSE) · [NOTICE](NOTICE) · [THIRD_PARTY](THIRD_PARTY.md)
