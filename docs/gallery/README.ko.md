# 시연 갤러리

[저장소 소개](../../README.md) · [현재 상태](../project/STATUS.md) · [이번 세션 기록](../project/sessions/20261106-evening-resume.ko.md)

## 최신 E17 · 다른 경계 재파지와 미확인으로 남은 입구

**다른 lower-rim 후보를 겨냥한 재파지는 실행했지만 실제 반대층 파지와 양측 지지는 확인하지 못했습니다. E17은5/50이며 최고5/50·목표10점 미달성 상태입니다.**

<a href="assets/20261106-e17-regrasp/event.mp4"><img src="assets/20261106-e17-regrasp/preview.gif" width="960" alt="E17 실제 공개 관측 네 카메라. 경계392~452의 다른 입구 경계 후보 재파지와 재시험"></a>

[**MP4 크게 열기 · 재생 위치를 옮기며 보기**](assets/20261106-e17-regrasp/event.mp4) · [전체 시도·행동 분석](20261106-astra-layer352-001.ko.md) · [원본 경계·영상 출처](assets/20261106-e17-regrasp/provenance.json)

392~452경계 · 61프레임 · 12.2초 재생 · 4배 느리게 · 모델 응답 대기 제외. 위는 로봇0·1 머리, 아래는 로봇0·1 손목입니다. 원본은 카메라당256×256이며 확대해도 세부 정보가 늘어나지는 않습니다.

**결과:** 5/50 · 픽업5 · 첫 소매0 · `success=false` · 전수검사452/452. [공식 결과와 공개 분석](../collection/reviews/20261106-astra-layer352-001.ko.md). [E17 고정 HF 백업·재다운로드 SHA 검증](../project/sessions/20261106-e17-backup-verification.json)을 완료했습니다.

| 구분 | 이 영상에서 확인할 내용 |
|---|---|
| 관측·행동 | 로봇0만 열고 lower-rim 후보에 맞춰 하강·손목 회전·팔 당기기를 한 뒤 다시 닫았습니다. 이후 양측 짧은 lift와 복귀를 실행했습니다. |
| 해석 | 다른 후보를 겨냥한 조작은 실제 실행했습니다. 실제 반대 입구 층인지와 새 파지의 지지는 미확인입니다. 픽업5점을 파지 정답으로 사용하지 않습니다. |
| 다음 | E18 B는 E16의470경계에서 지지/가이드 역할 분담과 소매 쪽 가장자리 재파지를 비교할 계획입니다. 픽셀 depth 질의를 켤 예정이며 아직 실행하지 않았습니다. 목부터 접근하는 별도 후보도 준비 중입니다. |

[**이 영상에 피드백 남기기**](https://github.com/leonyoon-3dai/PhyRC_2027_phase1/issues/new?title=%5BE17+%ED%94%BC%EB%93%9C%EB%B0%B1%5D+%EC%98%81%EC%83%81+%EA%B5%AC%EA%B0%84%EA%B3%BC+%EA%B4%80%EC%B8%A1&body=%EC%8B%9C%EB%8F%84%3A+E17+%2F+20261106-astra-layer352-001%0A%EC%98%81%EC%83%81+%EC%8B%9C%EA%B0%81+%EB%98%90%EB%8A%94+%EA%B2%BD%EA%B3%84%3A+%0A%EC%B9%B4%EB%A9%94%EB%9D%BC%3A+%EB%A1%9C%EB%B4%870+%EB%A8%B8%EB%A6%AC+%2F+%EB%A1%9C%EB%B4%871+%EB%A8%B8%EB%A6%AC+%2F+%EB%A1%9C%EB%B4%870+%EC%86%90%EB%AA%A9+%2F+%EB%A1%9C%EB%B4%871+%EC%86%90%EB%AA%A9%0A%0A%EA%B4%80%EC%B8%A1%ED%95%9C+%EC%9E%A5%EB%A9%B4%3A%0A%0A%EC%A0%9C+%ED%95%B4%EC%84%9D+%EB%98%90%EB%8A%94+%EC%A7%88%EB%AC%B8%3A%0A%0A%EB%8B%A4%EC%9D%8C%EC%97%90+%EB%B9%84%EA%B5%90%ED%95%98%EB%A9%B4+%EC%A2%8B%EC%9D%84+%EB%8F%99%EC%9E%91%3A%0A%0A%EA%B0%A4%EB%9F%AC%EB%A6%AC%3A+https%3A%2F%2Fgithub.com%2Fleonyoon-3dai%2FPhyRC_2027_phase1%2Fblob%2Fmain%2Fdocs%2Fgallery%2FREADME.ko.md%0A)

영상의 **시각 또는 경계와 카메라**를 적으면 같은 장면을 비교할 수 있습니다. 위 링크는 GitHub 작성 화면을 열며 제출은 사용자가 합니다. 아래 양식으로 이 대화에 남겨도 됩니다.

```text
E17 / 영상 시각 또는 경계:
카메라:
관측한 장면:
해석·질문 또는 다음에 바꿔볼 동작:
```

전이1개는 **관측 → 행동 → 다음 관측**의0.05초 기록입니다. E17은452전이·시뮬레이션22.6초,12번의 모델 판단·실제 약13분44초입니다. 12판단은11개 act와 종료 판단1개이며 종료 판단 자체는 물리를 진행하지 않았습니다. 정지 명령도 물리 기록에 포함되므로 모델 판단 수와 전이 수를 같게 세지 않습니다.

## 최근 비교

| 시도 | 실제 바꾼 접근 | 결과·한계 |
|---|---|---|
| [E17](20261106-astra-layer352-001.ko.md) | 다른 lower-rim 후보를 겨냥한 한쪽 재파지 | 5/50. 반대층·양측 지지 미확인, 운반 없이 종료 |
| [E16](20261106-astra-support264-002.ko.md) | 순차 지지 진단·같은 오른쪽 가장자리 재파지 | 0/50. 국소 천 동행 근거, 입구 미확인 |
| [E15](20261106-astra-opening264-001.ko.md) | 초기264경계 입구 준비 후 운반 | 5/50. 손 근처 가림·입구 통과 미확인 |

시작 경계·입력·후속 행동·예산이 달라 통제된 성공률 비교는 아닙니다. 같은 원본의 재실행을 독립 시연으로 세지 않으며, 기술 검사·시각 판단·공식 점수·학습 승인은 별도입니다.

<details>
<summary>E16 및 이전 시도 전체 · 당시 상태와 영상 보존</summary>

> 아래는 E16 정리 시점의 원문입니다. 당시의 최신·다음 계획·진행 상태는 현재 실행 지시가 아닙니다.

# 시연 갤러리

[저장소 소개](../../README.md) · [현재 상태](../project/STATUS.md) · [이번 세션 기록](../project/sessions/20261106-evening-resume.ko.md)

## 최신 E16 · 각 파지를 따로 확인한 뒤 입구 접근

**로봇0 재파지 뒤 국소 천 동행을 관측했지만 입구를 확인하지 못해 운반 없이 종료했습니다. E16은0/50이며 최고 기록5/50과10점 미달성 상태는 그대로입니다.**

<a href="assets/20261106-e16-regrasp/event.mp4"><img src="assets/20261106-e16-regrasp/preview.gif" width="960" alt="E16 실제 공개 관측 네 카메라. 경계352~440의 재파지 시도"></a>

[**MP4 크게 열기 · 재생 위치를 옮기며 보기**](assets/20261106-e16-regrasp/event.mp4) · [전체 시도·행동 분석](20261106-astra-support264-002.ko.md) · [원본 경계·영상 출처](assets/20261106-e16-regrasp/provenance.json)

352~440경계 · 89프레임 · 17.8초 재생 · 4배 느리게 · 모델 응답 대기 제외. 위는 로봇0·1 머리, 아래는 로봇0·1 손목입니다. 원본은 카메라당256×256이며 확대해도 세부 정보가 늘어나지는 않습니다.

**결과:** 0/50 · 첫 소매 0 · `success=false` · 전수검사 516/516. [공식 평가와 검수](../collection/reviews/20261106-astra-support264-002.ko.md) · [원본 보존·재다운로드 SHA 검증 완료](../project/sessions/20261106-e16-backup-verification.json)

| 구분 | 이 영상에서 확인할 내용 |
|---|---|
| 관측 | 위352~440경계는 로봇0만 열고 다시 잡은 뒤 따로 들어 확인한 구간입니다. 후반의 국소 천 접힘이 이동·유지·복귀하는 모습을 관측했습니다. |
| 해석 | 국소 지지의 시각적 근거를 얻었지만 두 지지점 사이의 연속 입구는 미확인입니다. 0점만으로 파지 실패를 단정하지 않으며, 국소 동행을 접촉 센서 판정으로 취급하지 않습니다. |
| 다음 | E16의352경계부터 다른 가시 입구 경계·층에서 한쪽 재파지를 비교하는 E17을 준비합니다. 기존 오른쪽 가장자리 회복과 구분하며 아직 실행하지 않았습니다. |

[**이 영상에 피드백 남기기**](https://github.com/leonyoon-3dai/PhyRC_2027_phase1/issues/new?title=%5BE16+%ED%94%BC%EB%93%9C%EB%B0%B1%5D+%EC%98%81%EC%83%81+%EA%B5%AC%EA%B0%84%EA%B3%BC+%EA%B4%80%EC%B8%A1&body=%EC%8B%9C%EB%8F%84%3A+E16+%2F+20261106-astra-support264-002%0A%EC%98%81%EC%83%81+%EC%8B%9C%EA%B0%81+%EB%98%90%EB%8A%94+%EA%B2%BD%EA%B3%84%3A+%0A%EC%B9%B4%EB%A9%94%EB%9D%BC%3A+%EB%A1%9C%EB%B4%870+%EB%A8%B8%EB%A6%AC+%2F+%EB%A1%9C%EB%B4%871+%EB%A8%B8%EB%A6%AC+%2F+%EB%A1%9C%EB%B4%870+%EC%86%90%EB%AA%A9+%2F+%EB%A1%9C%EB%B4%871+%EC%86%90%EB%AA%A9%0A%0A%EA%B4%80%EC%B8%A1%ED%95%9C+%EC%9E%A5%EB%A9%B4%3A%0A%0A%EC%A0%9C+%ED%95%B4%EC%84%9D+%EB%98%90%EB%8A%94+%EC%A7%88%EB%AC%B8%3A%0A%0A%EB%8B%A4%EC%9D%8C%EC%97%90+%EB%B9%84%EA%B5%90%ED%95%98%EB%A9%B4+%EC%A2%8B%EC%9D%84+%EB%8F%99%EC%9E%91%3A%0A%0A%EA%B0%A4%EB%9F%AC%EB%A6%AC%3A+https%3A%2F%2Fgithub.com%2Fleonyoon-3dai%2FPhyRC_2027_phase1%2Fblob%2Fmain%2Fdocs%2Fgallery%2FREADME.ko.md%0A)

영상의 **시각 또는 경계와 카메라**를 적으면 같은 장면을 바로 비교할 수 있습니다. 위 링크는 GitHub 작성 화면을 열며 제출은 사용자가 합니다. 아래 양식으로 이 대화에 남겨도 됩니다.

```text
E16 / 영상 시각 또는 경계:
카메라:
관측한 장면:
해석·질문 또는 다음에 바꿔볼 동작:
```

## 이전 시도와 비교

| 시도 | 바꾼 접근 | 확인된 결과 | 영상·근거 |
|---|---|---|---|
| E16 | 각 그리퍼 순차 지지 확인 | 0/50 · 첫 소매0 · 운반 없이 모델 종료 | [이번 분석](20261106-astra-support264-002.ko.md) |
| E15 | 초기264경계에서 입구 준비 후 운반 | 5/50 · 첫 소매0 · 착의 실패 | [준비·운반·복구](20261106-astra-opening264-001.ko.md) |
| E14 | 두 이동 뒤 중립 대기 경로 진단 | 5/50 · 감독 중단 · 정착 효과 미확인 | [짧은 진단](20261106-astra-hem-settle-001.ko.md) |
| E13 | 현재 손목 depth 패널 추가 | 5/50 · 입구와 손의 관계 불명확 | [진입·복구](20261106-astra-hem-depth-001.ko.md) |
| E12 | 밑단 진입→소매 출구 경로 | 5/50 · 테두리 통과 미확인 | [두 차례 시도](20261106-astra-hem-route-001.ko.md) |
| E11 | 같은 시도의 과거 RGB 추가 | 5/50 · 소매 통과 미확인 | [가장자리 비교](20261106-astra-sleeve-history-001.ko.md) |
| E10 | 700경계에서 소매 식별·시야 조정 | 5/50 · 손과 소매 관계 미확인 | [자세·시야 조정](20261106-astra-sleeve-branch700-003.ko.md) |

시작 경계·입력·후속 행동·예산이 달라 통제된 성능 비교는 아닙니다. 같은 실행의 여러 영상이나 같은 원본의 재실행 구간을 독립 시연으로 세지 않습니다. 기술 검사·시각 판단·공식 점수·학습 승인은 별도입니다.

전이1개는 **관측 → 행동 → 다음 관측**을 묶은0.05초 기록입니다. E16의516개 기록은 **시뮬레이션25.8초**이며,34번의 모델 판단·실제32분40초 실행과 구분합니다. 정지·기다림 명령도 기록에 포함됩니다.


<details>
<summary>이전 영상 전체 · E10~E15, E07, E05, 사람 시연과 연결 시험</summary>

> 아래는 E15 마감 시점의 영상·분석 원문입니다. 당시의 종료·다음 계획 문구는 현재 실행 지시가 아닙니다.

# 시연 갤러리 · 같은 네 카메라로 비교하기

[저장소 소개](../../README.md) · [E15 세 구간 전체 보기](20261106-astra-opening264-001.ko.md) · [현재 상태·재개 안내](../project/STATUS.md)

**아래로 스크롤하며 실제 영상을 비교하세요.** 위쪽은 robot0·1 머리, 아래쪽은 robot0·1 손목입니다. GIF는 자동 반복하며 MP4에서 재생 위치를 옮길 수 있습니다. 원본 카메라는 각각256×256이며 확대해도 세부 정보가 늘어나지는 않습니다.

**아래 E10~E15는 모두 원점수5/50·첫 소매0·착의 `success=false`입니다.** E15까지 종료했으며, 같은 실행의 여러 구간은 별도 시연이나 새 득점으로 세지 않습니다.

| 시도 | 바꾼 접근 | 최종 점수율 상태 |
|---|---|---|
| E15 | 초기264경계에서 입구 준비 후 운반 | `no_dressing_points / 0` |
| E13 | 현재 손목 depth 패널 추가 | `no_dressing_points / 0` |
| E12 | 밑단 진입→소매 출구 경로 | `no_dressing_points / 0` |
| E11 | 같은 시도의 과거 RGB 추가 | `no_contact / null` |
| E10 | 700경계 분기에서 소매 식별 | `no_contact / null` |

점수율 단위는 points/s이며 `null`은0과 다릅니다. 시작 조건·후속 행동·예산이 달라 통제된 성능 비교는 아닙니다.

## E15 · 손 근처 진입 시도→후퇴→한쪽 열기

**손의 입구 통과는 확인되지 않았고, 로봇0을 연 뒤 철수하면서 로봇1 쪽에 천이 남았습니다.**

<img src="assets/20261106-e15-hand-recovery/preview.gif" width="960" alt="E15 실제 경계509~611 네 카메라: 손 근처 가림, 후퇴, 로봇0 열기와 철수, 모델 종료">

509~611경계 · 103프레임 · 20.6초 반복 · 4배 느리게 · GIF6.20MB. [MP4](assets/20261106-e15-hand-recovery/event.mp4) · [준비·운반·복구 세 구간](20261106-astra-opening264-001.ko.md) · [최종 원인 검토](../collection/reviews/20261106-astra-opening264-001.ko.md) · [출처](assets/20261106-e15-hand-recovery/provenance.json)

## E13 · 손목 depth를 보며 진입·복구 반복

**입구와 손의 관계가 끝내 불명확했고 모델이 종료했습니다. depth 추가의 과제 개선 효과는 확인되지 않았습니다.**

<img src="assets/20261106-astra-hem-depth-001/preview.gif" width="960" alt="E13 새 구간700~810 네 카메라: depth 입력 뒤 정렬, 진입 시도, 복구와 모델 종료">

700~810경계 · 111프레임 · 22.2초 반복 · 4배 느리게 · GIF5.95MB. [MP4](assets/20261106-astra-hem-depth-001/event.mp4) · [입력·결과 비교](20261106-astra-hem-depth-001.ko.md) · [실제 첫16이미지](../collection/attempts/20261106-astra-hem-depth-001/first-call-images.json) · [출처](assets/20261106-astra-hem-depth-001/provenance.json)

## E12 · 밑단 진입 경로의 두 차례 시도

**평가기의 접촉 범위 조건은 기록됐지만, 손이 테두리를 통과했다는 증거는 확인하지 못했습니다.**

<img src="assets/20261106-astra-hem-route-001/preview.gif" width="960" alt="E12 새 구간700~781 네 카메라: 밑단 정렬, 진입 시도, 가림 복구와 재시도">

700~781경계 · 82프레임 · 16.4초 반복 · 4배 느리게 · GIF4.69MB. [MP4](assets/20261106-astra-hem-route-001/event.mp4) · [접촉 판정과 진입의 구분](20261106-astra-hem-route-001.ko.md) · [출처](assets/20261106-astra-hem-route-001/provenance.json)

## E11 · 과거 사진으로 가장자리 후보 비교

**모델의 가장자리 설명은 구체화됐지만, 검증된 소매 통과나 추가 득점으로 이어지지는 않았습니다.**

<img src="assets/20261106-astra-sleeve-history-001/preview.gif" width="960" alt="E11 새 구간700~777 네 카메라: 과거 RGB 입력 뒤 자세 조정, 후보 정렬과 복구">

700~777경계 · 78프레임 · 15.6초 반복 · 4배 느리게 · GIF3.96MB. [MP4](assets/20261106-astra-sleeve-history-001/event.mp4) · [E10과 비교](20261106-astra-sleeve-history-001.ko.md) · [출처](assets/20261106-astra-sleeve-history-001/provenance.json)

## E10 · 소매를 찾기 위한 자세·시야 조정

**들기·펼치기·기울이기를 바꿨지만 소매와 손의 관계를 확인하지 못하고 종료했습니다.**

<img src="assets/20261106-astra-sleeve-branch700-003/preview.gif" width="960" alt="E10 새 구간700~750 네 카메라: 들기, 펼치기, 기울이기와 시야 조정">

700~750경계 · 51프레임 · 10.2초 반복 · 4배 느리게 · GIF2.54MB. [MP4](assets/20261106-astra-sleeve-branch700-003/event.mp4) · [결과·실패 원인](20261106-astra-sleeve-branch700-003.ko.md) · [출처](assets/20261106-astra-sleeve-branch700-003/provenance.json)

선택 구간 안에서는 프레임을 생략하거나 시간 보간하지 않았습니다. 20Hz 관측을5fps로 재생하며 모델 응답 대기는 포함하지 않습니다. [영상 내보내기·정확한 경계 매핑](EVENT_EXPORT.ko.md)

<details>
<summary>E14 · 두 번의 이동 뒤 추가 중립 경로를 확인한 짧은 진단</summary>

## E14 · 두 번의 이동 뒤 추가 중립, 새 준비 방향으로 전환

**짧은 제어 진단 · 5/50 · 첫 소매 0 · 착의 `success=false` · 721/721전이 검사 통과.** 두 모델 이동 뒤 제어기가 중립 대기를 추가하는 경로를 확인하고, 더 이른 입구 준비를 시도하기 위해 감독 프로세스가 중단했습니다. 완주한 과제 성능 비교나 정착 효과 검증 결과로 해석하지 않습니다.

<img src="assets/20261106-astra-hem-settle-001/preview.gif" width="960" alt="E14 실제 새 구간 전체700~721경계: 두 모델 이동과 각각의 제어기 중립 대기, 종료 정리를 담은 네 공개 카메라 반복 영상">

**새 구간 전체 700~721경계 · 22프레임 · 4.4초 반복 · 4배 느리게 · GIF 1.07MB.** 새 물리 진행 1.05초는 모델 이동 8전이, 제어기 중립 12전이, 종료 정리 1전이입니다. 3회 모델 호출 중 2개 결정만 적용했고, 중단 뒤 마지막 반환 행동은 폐기했습니다. 적용된 두 행동은 이동 베이스만 사용해 리프트·손목 목표 추종 개선은 시험하지 않았습니다. 공식 점수율 상태는 `no_contact / null`입니다.

[**정확한 행동 출처·중단 이유·E13 비교·다음 E15 계획**](20261106-astra-hem-settle-001.ko.md) · [새 구간 MP4](assets/20261106-astra-hem-settle-001/event.mp4) · [전체 기록](../collection/attempts/20261106-astra-hem-settle-001/README.ko.md) · [영상 출처](assets/20261106-astra-hem-settle-001/provenance.json)

</details>

<details>
<summary>이전 기록 · E07 공동 운반, E05 픽업, 사람 조작과 연결 시험</summary>

## 참고 영상 · E07의 평평한 옷에서 초기 들기까지

아래는 **이전 E07의 참고 영상**이며 E11의 새 행동이나 새 득점이 아닙니다. 테이블 위 옷의 전체 외곽과 들어 올린 가장자리의 연결을 비교합니다. E11 actor에는 이 원본 영상을 복사하지 않았으며, E11의 새 재실행 264·320경계에서 직접 얻은 카메라 사진을 제공했습니다.

<img src="assets/20261106-e07-flat-to-lift/preview.gif" width="960" alt="이전 E07 참고: 평평한 티셔츠와 초기 공동 들기의 네 카메라 연속 영상, 경계264~320">

**원본 E07 264~320경계 · 57프레임 · 11.4초 반복 · 4배 느리게 · GIF 3.08MB.** V형 무늬가 있는 쪽과 넓은 반대편 가장자리의 위치를 추적할 수 있습니다. 잡은 구멍이 소매인지 밑단인지에 대한 판단은 영상에서 추론하며 내부 기하로 확인한 정답 라벨이 아닙니다.

[참고 구간 MP4](assets/20261106-e07-flat-to-lift/event.mp4) · [출처·변환 근거](assets/20261106-e07-flat-to-lift/provenance.json) · [E11 입력 비교와 실행 조건](../project/sessions/20261106-resume10.ko.md)

## E07 · 양쪽 머리·손목으로 보는 손 근처 접근

**같은 시각의 네 카메라를 함께 봅니다.** 위쪽은 로봇 0·1의 머리, 아래쪽은 로봇 0·1의 손목입니다. 옷과 각 그리퍼, 마네킹 손의 관계를 overview보다 가까이 확인할 수 있습니다.

<img src="assets/20261106-astra-coordinated-fresh-001-multiview/preview.gif" width="960" alt="E07 경계620부터700까지 양쪽 머리·손목 공개 카메라 4개를 함께 표시한 실제 접근 구간, 4배 느리게 자동 반복">

**자동 반복 16.2초 · 경계 620~700 · 81프레임 · 5fps · 4배 느리게 · 약 4.58MB.** 선택 구간의 모든 원본 프레임을 유지했습니다. 카메라당 원본 256×256, 합성 화면 512×588이며 이름·전이 경계·상대 시간은 영상 바깥 띠에 표시합니다.

[**네 카메라 16.2초 MP4 열기**](assets/20261106-astra-coordinated-fresh-001-multiview/event.mp4) · [원본 SHA·정확한 경계·변환 조건](assets/20261106-astra-coordinated-fresh-001-multiview/provenance.json) · [사건 영상 내보내기](EVENT_EXPORT.ko.md)

**이 영상은 기존 E07의 접근 구간입니다. 새 시도나 소매 성공 영상이 아닙니다.** 아래의 더 긴 overview는 경계 356~700, 전체 원본 MP4는 1,067프레임을 보여 줍니다. 같은 실행의 다른 보기이므로 독립 시연으로 추가 집계하지 않습니다.

## E07 · 공동 운반과 손 근처 접근

**관측한 사건:** 픽업 첫 5점 경계 → 손목 회전·천 감김 → 반대 회전 복구 → 함께 회전·전진 → 마네킹 손 근처 접근.

<img src="assets/20261106-astra-coordinated-fresh-001/preview.gif" width="960" alt="E07 실제 선택 구간 자동 반복: 첫 5점 경계356부터 손목 감김·복구와 공동 회전·운반을 거쳐 손 근처 경계700까지">

**자동 반복 69.0초 · 경계 356~700 · 345프레임 · 5fps · 4배 느리게.** 약 6.25MB. 전체 1,067프레임 중 일부이며 선택 구간 내부의 프레임 생략은 없습니다. 이 GIF에는 이후 소매 진입 시도가 포함되지 않습니다.

[**전체 213.4초 MP4 열기**](../collection/attempts/20261106-astra-coordinated-fresh-001/overview.mp4) · [구간·행동·원본 관측](20261106-astra-coordinated-fresh-001.ko.md) · [정확한 득점·접근 프레임](../collection/milestones/20261106-astra-coordinated-fresh-001/README.ko.md) · [GIF 변환 출처](assets/20261106-astra-coordinated-fresh-001/provenance.json)

**결과:** 공식 원점수 5/50, 착의 `success=false`, 최종 점수율 0 points/s. 양쪽 손끝 가까이에 옷을 유지하며 이동하는 모습은 확인했지만, 이 점수나 영상이 지속적인 양쪽 파지·소매 통과를 인증하지는 않습니다. 이후 소매 의도 24개 구간·254전이의 모델 판단은 모두 `uncertain`이었습니다. [종료 검토](../collection/reviews/20261106-astra-coordinated-fresh-001.ko.md)

## E05 · 파지 실패에서 재파지·픽업 5점까지

**관측한 사건:** 로봇 0 접근 → 첫 파지 실패 → 재접근·닫기 → 들기·유지 → 픽업 5점 확인 후 종료.

<img src="assets/20261106-astra-pickup-hold5-001/preview.gif" width="960" alt="E05 실제 전체 구간 자동 반복: 로봇0의 첫 파지 실패와 재파지, 들기·유지, 픽업 5점">

**자동 반복 50.6초 · 전체 253프레임 · 5fps · 4배 느리게.** 약 4.08MB. 원본 물리 진행은 12.65초입니다.

[**전체 50.6초 MP4 열기**](../collection/attempts/20261106-astra-pickup-hold5-001/overview.mp4) · [시간대별 행동·원본 관측](20261106-astra-pickup-hold5-001.ko.md) · [첫 5점 경계 246](../collection/milestones/20261106-astra-pickup-hold5-001/README.ko.md) · [GIF 변환 출처](assets/20261106-astra-pickup-hold5-001/provenance.json)

**결과:** 공식 원점수 5/50, 착의 `success=false`. 로봇 0만 옷자락을 들었으며 두 로봇의 협력 들기 시연은 아닙니다. 공식 유지 시간은 3.35초이며 프롬프트의 5초 목표와 구분합니다. [종료 검토](../collection/reviews/20261106-astra-pickup-hold5-001.ko.md)

## 사람 시연 · 양쪽 파지와 운반

**관측한 사건:** 두 로봇 접근 → 양쪽 파지·들기 → 마네킹 방향 운반. 사람이 조작한 고정 연습 배치의 부분 시연입니다.

<img src="assets/20261026-human-pickup-transport/preview.gif" width="960" alt="사람이 두 로봇을 조작한 접근·양쪽 파지·들기·운반 실제 편집 구간 자동 반복">

**자동 반복 33.0초 · 640×453 · 4fps.** 약 4.82MB. 원본 기록을 재생해 렌더링한 편집 영상이며 구간별 배속이 다릅니다.

[**33.08초 MP4 열기**](../videos/20261026-human-pickup-transport.mp4) · [장면·제어 출처](20261026-human-pickup-transport.ko.md) · [GIF 변환 출처](assets/20261026-human-pickup-transport/provenance.json)

**결과:** 공식 점수·전체 착의 성공 미확인. E05·E07과 동일한 평가 조건의 비교 표본으로 집계하지 않습니다.

## 첫 착의 시도 · 접근과 파지 미확인

**관측한 사건:** 접근 → 그리퍼 닫기 → 작은 시험 들기 → 재정렬. 실패 과정도 함께 보존합니다.

<img src="assets/20261106-astra-dressing-001/preview.gif" width="960" alt="첫 Astra 착의 시도의 실제 167프레임 자동 반복: 접근·닫기·시험 들기·재정렬, 파지 성공 미확인">

**자동 반복 33.4초 · 전체 167프레임 · 5fps · 4배 느리게.** 물리 진행 8.35초, 완료 판단 15개입니다.

[**전체 33.4초 MP4 열기**](../collection/attempts/20261106-astra-dressing-001/overview.mp4) · [관측·최종 행동](20261106-astra-dressing-001.ko.md) · [GIF 변환 출처](assets/20261106-astra-dressing-001/provenance.json)

**결과:** 공식 0/50점, 착의 `success=false`. 파지 성공은 확인하지 못했습니다.

## 연결 시험 · 작은 움직임·정지·종료

다음 두 영상은 과제 시연과 구분한 연결 시험입니다. 물리 진행은 각각 3전이·0.15초이며 20배 느리게 표시합니다. 파지·착의를 시도한 자료가 아닙니다.

| 비교 | r5 · 세 번 판단 | plan3 · 한 번 판단 |
|---|---|---|
| 모델 호출 | 3회 | 1회 |
| 적용 구간 | 작은 리프트 → 정지 → 종료 | 한 응답에서 미리 계획한 작은 리프트 → 정지 → 종료 |
| 공식 결과 | 0/50 · `success=false` | 0/50 · `success=false` |

**r5 · 세 번 판단한 연결 시험**

<img src="assets/20261106-codex-robot-wiring-r5/preview.gif" width="960" alt="r5 실제 3프레임 자동 반복: 작은 리프트·정지·종료, 20배 느리게">

자동 반복 3초 · 1fps. [MP4 열기](../collection/attempts/20261106-codex-robot-wiring-r5/overview.mp4) · [세 응답·시작과 종료](20261106-codex-robot-wiring-r5.ko.md) · [GIF 출처](assets/20261106-codex-robot-wiring-r5/provenance.json)

**plan3 · 한 응답에 담은 세 행동**

<img src="assets/20261106-exec-plan3-wiring-001/preview.gif" width="960" alt="plan3 실제 3프레임 자동 반복: 한 응답의 작은 리프트·정지·종료, 20배 느리게">

자동 반복 3초 · 1fps. [MP4 열기](../collection/attempts/20261106-exec-plan3-wiring-001/overview.mp4) · [실제 행동 목록](20261106-exec-plan3-wiring-001.ko.md) · [GIF 출처](assets/20261106-exec-plan3-wiring-001/provenance.json)

plan3는 중간 관측으로 다시 판단하는 조건부 계획이 아닙니다. 이 두 연결 시험만으로 착의 성능이나 일반적인 호출 효율 향상을 주장하지 않습니다.

</details>

</details>

</details>
