# PhyRC 2027 · 두 로봇의 협력 착의

**최신 E17 · 다른 입구 경계를 겨냥해 재파지했지만 지지·입구 미확인**

<a href="docs/gallery/assets/20261106-e17-regrasp/event.mp4"><img src="docs/gallery/assets/20261106-e17-regrasp/preview.gif" width="960" alt="E17 실제 공개 관측 네 카메라. 392~452경계의 다른 lower-rim 후보 재파지와 재시험"></a>

[**MP4 크게 보기**](docs/gallery/assets/20261106-e17-regrasp/event.mp4) · [**전체 갤러리**](docs/gallery/README.ko.md) · [**E17 분석**](docs/collection/reviews/20261106-astra-layer352-001.ko.md) · [**영상 피드백 남기기**](https://github.com/leonyoon-3dai/PhyRC_2027_phase1/issues/new?title=%5BE17+%ED%94%BC%EB%93%9C%EB%B0%B1%5D+%EC%98%81%EC%83%81+%EA%B5%AC%EA%B0%84%EA%B3%BC+%EA%B4%80%EC%B8%A1&body=%EC%8B%9C%EB%8F%84%3A+E17+%2F+20261106-astra-layer352-001%0A%EC%98%81%EC%83%81+%EC%8B%9C%EA%B0%81+%EB%98%90%EB%8A%94+%EA%B2%BD%EA%B3%84%3A+%0A%EC%B9%B4%EB%A9%94%EB%9D%BC%3A+%EB%A1%9C%EB%B4%870+%EB%A8%B8%EB%A6%AC+%2F+%EB%A1%9C%EB%B4%871+%EB%A8%B8%EB%A6%AC+%2F+%EB%A1%9C%EB%B4%870+%EC%86%90%EB%AA%A9+%2F+%EB%A1%9C%EB%B4%871+%EC%86%90%EB%AA%A9%0A%0A%EA%B4%80%EC%B8%A1%ED%95%9C+%EC%9E%A5%EB%A9%B4%3A%0A%0A%EC%A0%9C+%ED%95%B4%EC%84%9D+%EB%98%90%EB%8A%94+%EC%A7%88%EB%AC%B8%3A%0A%0A%EB%8B%A4%EC%9D%8C%EC%97%90+%EB%B9%84%EA%B5%90%ED%95%98%EB%A9%B4+%EC%A2%8B%EC%9D%84+%EB%8F%99%EC%9E%91%3A%0A%0A%EA%B0%A4%EB%9F%AC%EB%A6%AC%3A+https%3A%2F%2Fgithub.com%2Fleonyoon-3dai%2FPhyRC_2027_phase1%2Fblob%2Fmain%2Fdocs%2Fgallery%2FREADME.ko.md%0A)

**공식 원점수5/50 · 픽업5 · 첫 소매0 · `success=false`.** 로봇0을 열고 별도로 보이는 아래쪽 입구 경계 후보에 맞춰 다시 닫는 동작은 실행했습니다. 실제 반대층 파지와 양측 지지는 확인하지 못했고, 운반 없이 종료했습니다. 한 번의 제한된 재파지로 이 방법 전체가 실패했다고 단정하지 않습니다.

392~452경계 · 61프레임 · 12.2초 재생 · 4배 느리게 · 모델 응답 대기 제외. 위는 로봇0·1 머리, 아래는 로봇0·1 손목입니다. 피드백에는 **영상 시각 또는 경계와 카메라**를 적어 주세요. [영상 출처](docs/gallery/assets/20261106-e17-regrasp/provenance.json) · [현재 상태](docs/project/STATUS.md)

전이1개는 **관측 → 행동 → 다음 관측**을 묶은0.05초 기록입니다. E17의452개 기록은 **시뮬레이션22.6초**이며,12번의 모델 판단·실제 약13분44초 실행과 구분합니다. 모델 판단 한 번이 여러 전이에 적용될 수 있고, 정지·기다림 명령도 기록에 포함됩니다.

## 무엇을 만드는가

두 대의 Stretch 4가 공개 RGB-D 카메라와 로봇 상태를 이용해 앉은 마네킹에 티셔츠를 입히는 정책을 개발합니다. 라이브 화면 대신 실제 시도별 영상과 실패 분석을 보존하고, 조작 방법이 달라졌을 때 관측과 점수가 어떻게 달라지는지 비교합니다.

| 평가 항목 | 점수 |
|---|---:|
| 같은 그리퍼로 잡은 영역을5cm 올려 시뮬레이션3초 유지 | 5 |
| 첫 손이 소매를 통과해 밖으로 나옴 | 5 |
| 반대 어깨 / 두 번째 소매 / 왼쪽 위팔 / 오른쪽 위팔 | 각각5 |
| 목 / 앞면 방향 | 각각10 |

목표는 **공식 원점수10점 이상과 반복 가능한 실제 착의 진전**입니다. 첫 소매 통과는 현재 비교하는 경로이며, 목부터 접근하는 대안도 준비 중입니다. 어떤 경로든 실행·관측·공식 평가로 확인하며 모든 방법의 첫 단계를 소매로 고정하지 않습니다. 점수율은 픽업을 제외한 착의 점수를 첫 접촉부터 마지막 착의 득점까지의 시뮬레이션 시간으로 나눕니다. 픽업5점만으로는 양의 순위 점수가 생기지 않으며, 원점수10점도 전체 착의 성공과 다릅니다.

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
| 최신 과제 시도 | E17 `20261106-astra-layer352-001` · 모델 자율 종료 · 452/452전이 통과 |
| 모델·환경 | Astra/ultra · Codex CLI0.166.0/exec · 고정 Isaac Sim6.0.1 · Chrome/WebRTC OFF |
| 이번에 바꾼 접근 | E16의352전이 재실행 뒤 다른 lower-rim 후보를 겨냥한 재파지. 새52개 모델 전이와48개 제어기 중립 전이를 기록했습니다. |
| 다음 비교 | **E18 B: 지지/가이드 역할을 나눠 소매 쪽 가시 가장자리로 재파지**를 준비합니다. E16의470경계에서 분기하며 픽셀 depth 질의를 켤 계획입니다. 아직 실행하지 않았습니다. |
| 다른 경로 | 목 우선 전략 코드를 통합하고 CPU 검사를 마쳤으며 실제 과제는 아직 실행하지 않았습니다. |
| 후보 기능 | 픽셀 depth 질의는 CPU·합성 이미지 실제 CLI2턴 및 모델 없는 GPU3전이 연결 검사를 통과했습니다. GPU 연결 시험은 실제 모델0회·fixture 질의1회였습니다. **E16·E17에는 사용하지 않았으며 실제 과제 적용 효과는 미검증**입니다. |
| 소스·원본 | E17 실행 소스는98bb41f(작업 트리 clean). 공개 기록과 [E17 고정 HF 백업·재다운로드 SHA 검증](docs/project/sessions/20261106-e17-backup-verification.json)을 완료했습니다. [E16 고정 백업](docs/project/sessions/20261106-e16-backup-verification.json)도 보존했습니다. |

[현재 상태·다음 명령](docs/project/STATUS.md) · [이번 세션 원문](docs/project/sessions/20261106-evening-resume.ko.md) · [방법 전환 기준](docs/project/sessions/20261106-method-switch-matrix.ko.md)

E16에서는 순차 진단과 로봇0 재파지 뒤 국소 천 동행을 관측했고, E17은 다른 가시 경계를 목표로 재파지했지만 반대층·양측 지지를 확인하지 못했습니다. 실제 동작 변화, 시각적 근거, 공식 점수를 따로 기록합니다. 픽업5점에서 어느 파지가 성공했는지나 입구가 열렸는지를 역추론하지 않습니다.

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
