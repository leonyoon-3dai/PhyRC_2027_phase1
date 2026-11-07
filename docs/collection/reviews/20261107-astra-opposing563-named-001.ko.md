# E25 · 실제 재파지와 국소 동행, 반대 입구 경계 미확인으로 자율 종료

**원점수5/50(픽업5·모든 착의0), success=false다. 최고5점·중간 목표10점 미달성이다.** R0를 지지측 후보로 유지하고 R1 release→낮은 경계 초기 placement→보정1회→reclose1회를 실제 수행했다. 단독 lift에서 새 국소 천 동행의 잠정 근거가 있었지만, 반대 자유 lip 정체·독립 하중 지지·차등 개방은 미확인이다. D13에서 모델이 자율 finish했으며30판단 중16개가 남았다. 운반·착의 진입은 수행하지 않았다.

| 항목 | 마감 기록 |
|---|---|
| 실행 / 소스 | `20261107-astra-opposing563-named-001` / `68658c9d9bb7e47591fb330f08f4f996ec4fcbfb`, 시작 clean |
| UTC / 직접 부모 | 2026-11-07 05:18:00–05:38:26 / E18 `20261106-astra-guide470-depth-001`·563행동 재실행·이번510/542경계 과거 RGB |
| 전략·모델 | `coordinated-opposing-rim`·Astra/ultra·CLI0.166.0/exec·named/query/wrist-depth-panel |
| 예산·종료 | 30판단/max1400/timeout180/settle6/review10. 모델 자율 finish·예산16개 잔여·감독 중단0 |
| 호출·결정 | **15호출·14최종 결정 = 13act + 1finish** |
| 질의 | index3 R1 head6점·1회·6/6valid·물리0 |
| 기록 | **698 = 563재실행 + 93모델 행동 + 42제어기 정착**. 종료 추가중립0 |
| 시뮬레이션 / 실제 | 전체34.9초·새135전이6.75초 /1225.593759초(20분25.594초) |
| 호출·환경 시간 | 모델 호출 경로568.194194초·환경609.287344초. 내부 추론시간 미제공 |
| 별도 평가 | raw5/50·pickup5·모든 착의0·success=false·no_contact / final_score=null |
| 마감·검사 | completed/errornull·host/Python0·simulator0. 전수 QC698/698 통과·오류0 |
| 재파지·진전 | release1·초기 placement1·보정1·reclose1. 새 R1 국소 동행 잠정 근거, 반대 경계 정체 미확인. 운반/진입0 |
| 학습 승인 | unreviewed. 같은 prefix·인접 프레임을 독립 성공 표본으로 세지 않음 |

점수·종료·실제 시간은 별도 실행 검수자가 제공했다. 점수에서 파지 정체·실패 원인을 역추론하거나 배우 입력·교사 행동 라벨에 평가 항목을 넣지 않는다.

근거는 지정 공개 RGB, 공개 로봇 상태, 최종 결정의 짧은 설명·적용 행동, 실제 공개 depth 질의에 한정한다. 활성 H5·평가·audit·내부 기하·seed·원시 CLI 이벤트·내부 추론은 읽지 않았다. 실행 중 다음 행동을 지시하거나 물리 제어에 개입하지 않았다. D/obs는0부터 시작하며 obsN은 DN 직전 입력이다. 같은 prefix는 정확한 천 checkpoint가 아니므로 과거 E18의 지지·파지 정체를 이번 시작 상태에 대입하지 않는다.

## 이번563 시작 관측

obs0의 지정5뷰를 직접 확인했다. 양 wrist의 jaw 부근에 노란 띠와 파란 천이 남고 양 head에서 길게 벌어진 어두운 영역과 아래 파란 flap이 보인다. 테이블이 아래에 보이지만 몸판 전체가 충분히 받쳐졌는지는 아직 확정할 수 없었다. 자유로운 반대 lip·독립 하중 지지·서로 다른 층의 파지 정체도 미확인이다.

공개 상태의 close intent는 양측 true였으나 fingertip 원점 간격은 R0 약40.61mm/R1 약52.58mm이고 관절 잔류 속도가 있었다. 닫힘 명령만으로 실제 attachment나 안정 지지를 인증하지 않는다. 해당 간격은 공개 기준점 사이 거리이며 천 압착력 센서가 아니다.

## 실제 행동·관측

| 판단·경계 | 실제 행동 | 직접 관측과 한계 |
|---|---|---|
| D0 /563–577 | 양 lift−0.25·8모델+6정착, 기존 close intent 유지. R0 anchor/R1 changed측 후보 선택 | obs1 R0 head/R1 wrist에서 jaw 천이 남고 전체가 테이블에 가까워짐. 몸판의 넓은 지지는 아직 불명확. 양 lift 실측 약−139.9mm이며 동시 운동이라 독립 anchor 시험이 아님 |
| D1 /577–591 | 양 lift−0.20·8모델+6정착, 테이블에 몸판을 놓기 위한 추가하강 | obs2 overview·양 head·R1 wrist에서 파란 몸판이 테이블 위에 더 넓게 놓이고 이전 큰 어두운 틈이 납작해짐. 양 jaw 천 유지. lift 실측 약−125.6mm, 마지막 속도 약−48mm/s로 잔류 운동 존재. 실제 release/regrasp는 없음 |
| D2 /591–599 | R1 gripper−1(open)8모델 전이·추가 정착0, R0 명령0 | obs3 양 head/양 wrist에서 R1 손가락이 벌어지고 파란 몸판/노란 경계가 대각으로 접힘. R1 fingertip 간격47.05→129.30mm·close false, 손가락 속도+0.80/+0.83rad/s로 아직 열리는 중. R0 close true·간격39.96mm·jaw 천 유지. 반대 자유 lip와 독립 anchor 지지는 미확인 |
| D3 /599–613 | query 뒤 R1 lower/retract/wrist-yaw·8모델+6정착, R0 명령0. 초기 placement1회이며 보정 횟수와 구분 | obs4 양 head/양 wrist에서 열린 R1 jaw가 이전 상단 파지 위치에서 낮은 곡선 노란 경계 쪽으로 이동. R1 wrist에 파란 면과 노란 경계가 두 손가락 사이/옆에 보임. R0 jaw 천 유지이나 actual 기준점·속도는0이 아님. 다른 경계 접근은 실제 수행했으며 반대 자유 lip 정체·잡힘은 미확인 |
| D4 /613–619 | all-zero 모델 중립6전이·추가 정착0, placement 전에 잔류 운동을 기다림 | obs5 양 head/R1 wrist의 천 모양은 거의 같지만 R1 lift target 오차−14.41→−1.16mm/yaw−0.0604→−0.0133rad로 감소. lift 속도−75.9→−7.76mm/s. 새 경계 발견보다 잔류 목표 추종을 분리하는 정보가 생김 |
| D5 /619–633 | R1 lower−0.26/extension+0.08/yaw−0.11·8모델+6정착, placement correction1 | obs6 R0/R1 head·R1 wrist에서 낮은 노란 경계 끝이 열린 jaw 중앙 가까이 이동. R0 jaw 천/형상 유지. R1 lift error−12.22mm·하강속도−63.10mm/s로 아직 정착 중 |
| D6 /633–639 | all-zero 모델 중립6전이·추가 정착0, 첫 보정 뒤 정착 확인 | obs7 R1 head/wrist의 경계 위치는 대체로 유지. R1 lift error−0.69mm/yaw−0.0052rad·lift 속도−5.65mm/s로 잔류 감소. 열린 간격188.50mm |
| D7 /639–649 | R1 gripper+1(close)10모델 전이·추가 정착0, 한 번의 reclose | obs8 양 head/양 wrist에서 노란 경계 끝이 모인 R1 손가락 중앙에 보임. 간격188.50→80.67mm·close true. 하지만 실제 finger .212/.207rad 대 target .103rad, 속도−.552/−.493rad/s로 여전히 닫히는 중. R0 jaw 천 유지. 국소 동행·하중 지지·반대 자유 lip 정체 검증 전 |
| D8 /649–657 | all-zero 모델 중립8전이·추가 정착0, R1 닫힘 추종을 기다림 | obs9 양 head/R1 wrist에서 선택한 노란 끝은 jaw 중앙에 남음. R1 간격80.67→46.61mm, actual finger .118/.124rad·target .103rad. 닫힘 속도−.031/−.106rad/s가 남아 attachment 확정은 아님 |
| D9 /657–667 | R1만 lift+0.10·4모델+6정착, 근처 테이블 지지를 남긴 국소 동행 시험 | obs10 양 head/R1 wrist에서 jaw 부근 노란 끝이 함께 위로 이동하고 몸판 아래 윤곽도 변함. R1 lift+26.62mm·grasp_base 이동26.62mm, R0 기준점0.143mm. 간격46.61→40.68mm로 추가닫힘 혼재. 새 국소 파지의 잠정 동행 근거이며 독립 하중/반대 lip 인증은 아님 |
| D10 /667–678 | R1 retract−0.10/roll+0.12·5모델+6정착, 차등 경계 변화 시험 | obs11 양 head/양 wrist에서 jaw 천 유지·경계 기울기/아래 윤곽 변화. 실측 extension−27.43mm/roll+0.1459rad와 잔류lift+3.88mm. R0 기준점0.224mm. 아직 큰 한 면과 한 노란 경계가 주로 보여 자유로운 두 lip의 독립 개방은 미확인. roll은 최종 설명에 명시된 의도적 명령 |
| D11 /678–690 | R1 lift+0.12/ext+0.09/pitch+0.15·6모델+6정착, 같은 파지의 시점/자세 변경 | obs12 양 head/R1 wrist에서 한 노란 경계·큰 파란 면 관계 유지. R1 grasp_base ΔZ+0.018mm이나 ΔY+32.67mm(norm32.76mm)로 높이 보존은 근사적으로 됐지만 위치고정은 아님. 두 자유 lip 개방 새 근거 없음 |
| D12 /690–698 | all-zero 모델 중립8전이·추가 정착0, 자세 목표 정착 뒤 실험 판정 | obs13 양 head/R1 wrist에서 jaw 천 유지·경계 배치 대체로 같음. R1 pitch 오차+0.00023rad/arm−0.048mm로 감소하나 lift오차+3.39mm·속도+14.84mm/s 잔류. 반대 두 경계의 정체/독립 개방 미해결 |
| D13 /698·물리0 | finish_episode, 최종 설명은 국소 동행을 잠정 인정하되 반대 입구 경계 미해결로 마감 | 이번 관측에서 양 파지·테이블 근처 상태를 보존하며 종료. finish의 steps1을 실제 전이로 세지 않음. 감독 중단·예산 소진 아님 |

index3에서 당시 현재 관측의 R1 head6점 depth query가 실제 완료됐다(6/6valid·물리0). 그 뒤 초기 placement 행동 D3를 실제 수행했다. 깊이는 현재 보이는 표면의 optical Z이며 다른 층/자유 lip의 정답이나 접촉 센서가 아니다.

D3에서 R1 실측 lift−169.37mm/arm−20.70mm/wrist-yaw−0.600rad였다. obs4의 target−actual은 lift−14.41mm/arm+2.02mm/yaw−0.0604rad, 실제 속도는 lift−75.9mm/s/yaw−0.348rad/s로 잔류 운동이 남는다. R0에도 lift+10.6mm/s가 남고 grasp_base 기준점 endpoint가 약1.57mm 변했다(R1 약238mm). 이는 robot base frame의 기준점이며 천 재료점·고정 파지점이 아니다. R0 명령0을 stationary 증명으로 쓰지 않는다. 몸판은 양 head에서 테이블 윗면 영역과 겹치지만 지지 면적·하중·전체 받침을 인증하지 않는다.

D5의 첫 보정과 D7 reclose까지 실제 적용됐다. 초기 placement는 보정 횟수에 넣지 않으며 추가 위치 보정은1회만 사용했다. release와 reclose는 각각1회다. 서로 다른 낮은 경계로 실제 이동했지만 시각적으로 선택한 경계가 자유로운 반대 lip인지 같은 층의 다른 지점인지는 아직 미확인이다.

release→다른 낮은 경계로 reposition→reclose는 수행했고, 이후 실제 손가락·타깃·속도 변화와 시험측 국소 천 동행/상대 anchor 움직임을 분리했다. 테이블 지지가 남아 있다는 이유만으로 국소 동행 근거를 무효화하지 않되 이것을 독립 하중·attachment 센서 확정으로 확대하지 않는다. 화면의 노란 띠를 반대 자유 lip로 자동 인정하지 않는다. 허용된 최대2회 placement 보정 중1회, 재파지 cycle1회를 실제 사용했다. 남은 예산16개에서 자율 종료했으며 반복된 현재 파지의 의미 확인과 다른 구조적 조작의 가능성을 구분한다.

D9의 새 국소 동행 근거는 유지한다. D10 차등시험→D11 시점 변경→D12 정착에서 반대 경계 정체에 관한 추가 정보가 작다는 것은 현재 배치의 의미 확인이 포화되는 근거이지 모든 입구 조작의 물리 불가능이나 새 파지 실패의 확정은 아니다.

자료는 `unreviewed`이며 같은 계보·재실행 prefix·인접 프레임을 독립 성공 표본으로 세지 않는다.

## 기록과 다음 비교

13개 act의 named→공식 배열→적용 float32는 일치했다. 비영 roll은 D10에만 있으며 최종 설명에서 명시한 의도적 차등시험이다. 이전 E18의 의도와 다른 roll 명령과 구분한다. D2 open·D7 close를 실제 finger/velocity/target과 함께 확인했으며 close intent만을 파지 성공으로 라벨링하지 않았다.

[학습 검토 JSON](20261107-astra-opposing563-named-001-learning-segments.json)은 새135전이를12개 연속 구간으로 나누고 질의·자율 finish는 물리0 사건으로 보존한다. D4/D6 추가 중립은 새로운 입구 발견보다 잔류 목표 추종을 분리하는 정보였고, D8 중립은 실제 닫힘 추종을 확인했다. 실패·부분 복구도 원본 그대로 유지하며 자동 모방학습 승인은 하지 않는다.

다음 E26는 **M2 별도 방법, E18/787·과거719/771·22판단/max1400/settle6**으로 채택했고 후보 코드를 main에 통합했다. 실제 미실행이며 E25의 국소 동행을 반대 입구의 확정이나 인증된 착의 출발점으로 승격하지 않는다. 구체적 현재 상태는 [STATUS](../../project/STATUS.md)를 따른다.

[재파지 영상591–698](../../gallery/assets/20261107-e25-rim-regrasp/event.mp4)·108프레임/21.6초, [국소 동행657–698](../../gallery/assets/20261107-e25-local-follow/event.mp4)·42프레임/8.4초를 공개했다. 두 번째는 첫 영상에 포함되는 같은 구간이며 독립 시연이 아니다. 모두5fps·4배 느리게이고 모델 응답 대기·구간 내 생략·보간이 없다. [갤러리 상세](../../gallery/20261107-astra-opposing563-named-001.ko.md) · [전체 공개 기록](../attempts/20261107-astra-opposing563-named-001/README.ko.md).

최종698경계의 지정5뷰를 직접 확인했다. [R1 wrist](../attempts/20261107-astra-opposing563-named-001/images/final-robot_1_wrist.png)의 모인 손가락 중앙에는 노란 경계 끝이 남고 [양 head 중 R1](../attempts/20261107-astra-opposing563-named-001/images/final-robot_1_head.png)은 테이블 위 큰 삼각형 몸판과 이어진 한 경계를 보여준다. R0 wrist에도 jaw 부근 천이 남는다. 이 최종 모습은 국소 유지와 양립하지만 반대 자유 입구·독립 지지의 인증은 아니다. overview에서는 로봇과 옷이 여전히 테이블 쪽에 있어 운반·사람에게 진입한 장면은 없다.

[D3–D6 중립·정착 독립 검토](20261107-astra-opposing563-named-001-settle.ko.md) · [선별 수치 JSON](20261107-astra-opposing563-named-001-settle.json). 추가 중립6전이에서 잔류 목표 추종은 개선됐고 새 천 관계는 거의 변하지 않았다. 이 분석은 E26에 정착12를 적용한 실행 검증이 아니며 다음 비교는 기존 settle6을 유지한다.

[비공개 원본 백업](../../project/sessions/20261107-e25-backup-verification.json)은 고정 revision`79e74c3dda23a676a59754005a22d55e89c6034f`·1,624,331,388bytes·SHA`1d44bf676d162944907f33d090fa85f8516fafd22a7ef5f9190c57c13dfd8150`다. 05:43:45UTC 강제 재다운로드와182개 member 해시 검증을 완료했다. 학습 승인은unreviewed이며 실제 재파지·부분 동행·가설 미해결·자율 종료를 함께 보존했다.

후속실행갱신: E26 `20261107-astra-hand-swap787-named-001`은2026-11-07T05:51:36Z·source`53a58bb4e9fa4ff5366b66485c8690b0784ad71f` clean으로실제시작했습니다. 위미실행표기는E25마감당시이며현재재실행중·새성과미확인입니다.
