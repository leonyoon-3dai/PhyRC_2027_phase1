# E26 · 대안 손 접근·보상 관측, 착의0으로 자율 종료

**원점수5/50(픽업5·모든 착의0), success=false다. 최고5점·중간 목표10점 미달성이다.** E23 초기와 다른 화면상 위쪽 손 H_B를 선택하고 상대 파지 방향·측면 접근·보상 관측을 실제 수행했다. R1 guide/R0 support는 유지돼 역할 교환은 확인되지 않았다.953경계의 두손 재노출과 후반 관측 orbit의 손/손목 노출은 유용한 변화지만 H_B 정체의 연속 추적·소매 통과는 미확인이다. 마지막22번째 판단에서 모델이 자율 finish했으며 감독 중단이나 제어기 예산 강제종료가 아니다.

| 항목 | 마감 기록 |
|---|---|
| 실행 / 소스 | `20261107-astra-hand-swap787-named-001` / `53a58bb4e9fa4ff5366b66485c8690b0784ad71f`, 시작 clean |
| UTC / 직접 부모 | 2026-11-07 05:51:36–06:42:28 / E18 `20261106-astra-guide470-depth-001`·787행동 재실행·이번719/771경계 과거 RGB |
| 설정 | M2 leading-hand swap 후보·Astra/ultra·named/query/wrist-depth-panel·22판단/max1400/timeout180/settle6/review10 |
| 호출·판단 | **25모델 호출·22최종 결정 = 21act + 1finish**. 마지막 요청 슬롯에서 자율 종료 |
| 질의 | index2/10/19·6/8/8점·3회·22/22valid·물리0 |
| 기록 | **1139 = 787재실행 + 232모델 행동 + 120자동 정착**, 종료 추가중립0 |
| 시뮬레이션 / 실제 | 전체56.95초·새352전이17.6초 /3051.140932초(50분51.141초) |
| 호출·환경 시간 | 모델 호출 경로2022.295263초·환경977.668086초. 내부 추론시간 미제공 |
| 별도 평가 | raw5/50·pickup5·모든 착의0·success=false·no_dressing_points / final_score=0.0 |
| 마감·검사 | completed/errornull·host/Python0·simulator0·감독 신호0. 전수 QC1139/1139 통과(공개 provenance quality=true) |
| 자료 승인 | unreviewed. 역할/입구 의미·부분 동행을 공식 성공 교사 라벨로 쓰지 않음 |

점수·마감·시간 수치는 별도 실행 검수자가 제공했다. 아래 시각·행동 분석의 원인을 점수에서 역추론하지 않는다.

근거는 지정 공개 RGB·공개 로봇 상태·최종 결정과 짧은 최종 설명·실제 공개 depth 질의다. 활성 H5/eval/audit/seed/숨은 기하/원시 CLI 이벤트/내부 추론은 읽지 않았다. 실행 코드·물리 제어에 개입하지 않았다. D/obs는0부터 시작하며 obsN은 DN 직전 입력이다. 현재 상태를 과거 출발점 이미지로 대체하지 않고 새 재실행의 천·지지를 다시 확인한다.

## 이번787 시작 관측

obs0의 지정5뷰를 직접 확인했다. R0 wrist에서 위쪽·먼손과 아래쪽·가까운손을 서로 다른 줄무늬 전완으로 구별할 수 있고 R1 wrist에도 두 손이 위아래로 드러난다. actor의 H_B/H_A 구분과 관측이 양립하지만 해부학 좌/우나 과거 실제 목표 손은 이 화면만으로 확정하지 않는다.

양 jaw 부근에 노란 띠·천이 남고 두 띠 사이 어두운 영역이 보인다. 입구 정체·독립 하중 지지는 미확인이다. 몸판은 사람 앞에서 매달려 보이며 이번 obs0에서 테이블 몸판 지지 근거는 없다. 양 close intent는 true지만 R0 fingertip 간격40.11mm/R1 24.71mm, R1 finger 관절 .128/약0rad로 비대칭이다. lift 잔류 속도는 양 약+10.8mm/s, arm target−actual은 약−6.7mm다. 닫힘 명령·과거 점수·같은 prefix를 현재 파지 확정으로 쓰지 않는다.

## M2 세 축의 마감 판정

| 축 | 실제 근거 | 한계 |
|---|---|---|
| 대상 손 | 초기 E23 H_A 대비 E26 H_B 선택 차이는 별도 공개 비교로 지지됨. 초기 두 전완과953의 재노출을 추적 | 전 이력 최초의 다른손 접근이나 지속된 교체 완료를 뜻하지 않음. 후반 노출 손을 H_B로 인증하지 못함 |
| guide/support | R1 guide/R0 support 배정과 비대칭 extension·한쪽 guide 이동을 실제 수행 | 기존 E24에도 같은 역할이 있었고 이번에도 서로 바뀌지 않음. 역할 분담과 역할 교환은 다름 |
| 접근면 | D5 반대 base 이동·wrist yaw로 상대 방향을 바꾸고 D6 측면 접근, 이후 높이·정렬·body-entry 가설 시험을 실제 수행 | 실제 방법 요소는 있으나 입구 정체·연속 통과·M2 전체 성공을 확정하지 않음. 일반 task-progress 수행을 손/역할 교환으로 대신하지 않음 |

| 판단·경계 | 최종 의도·선택 | 실제 관측/한계 |
|---|---|---|
| D0 /787–809 | 양 base_forward+0.15/base_left+0.22, R1 extension+0.09·16step 선택. H_B를 guide하려는 비스듬한 배치 | obs1 양 head/양 wrist 직접 확인. 양 base worldΔ약(−69,−111)mm, R1arm+79.32mm/R0arm−4.83mm로 실제 공동 대각이동+비대칭 extension 수행. 양 jaw 천 유지·span/몸판 형상 변화. R0 wrist에서 H_A가 rim에 더 가까이 보이고 H_B는 위에 남아 H_B 진입 관계는 없음. finalreason의 hand swap 미확정을 보존 |
| D1 /809–827 | 양pitch−0.13/R1extension+0.06·12모델+6정착, H_B 쪽 입구 정렬을 위한 자세 변화 | obs2 양 head/양 wrist에서 노란경계·큰몸판이 head뷰 위로 올라오고 wrist 시점이 크게 변함. 이전 두 손의 분리 추적이 어려워지고 R0 wrist에 얼굴/팔 일부, R1 wrist에 주로 천이 보임. 가림/시야변화는 진입 증거가 아님. finalreason은 hand swap·prior role exchange 미확정/no entry를 유지 |
| D2 /827–845 | R0 wrist6점 query 뒤 양forward+0.26/pitch−0.04·12모델+6정착. 손 후보가 lip보다 멀어 투영 겹침≠진입으로 해석 | obs3 양 head/양 wrist에서 큰 파란 면이 사람 앞을 더 가리고 노란 띠가 head뷰 상단에 올라옴. H_B 손/전완 연속 추적은 복원되지 않음. R0 wrist 얼굴/어깨는 아래, R1 wrist는 주로 천. 진입/실패 모두 미확정 |
| D3 /845–863 | 양backward−0.10/pitch+0.085·12모델+6정착, 좁아진 mouth 후보와 H_B 가시성을 복구 | obs4 양 head/양 wrist에서 노란띠 사이 어두운 영역이 다시 넓어 보이고 R0 wrist 상단왼쪽 손/줄무늬전완이 재노출. R1 wrist에도 상단오른쪽 손/전완 일부. 실제 관측 복구 정보이며 D1/D2와 동일 가림으로 묶지 않음. H_A 부분가림·연속 진입 미확인 |
| D4 /863–885 | 복구 pitch 유지·양forward+0.25·16모델+6정착, upward tilt를 추가하지 않고 H_B 접근 | obs5 양 head/양 wrist에서 H_B가 다시 가려지고 노란띠 사이 어두운 영역이 좁아짐. R0 wrist 얼굴/팔은 가까워보이나 손–rim 연결 미확인, R1 wrist는 큰 천 면. forward-only에서도 가림이 재발하므로 이전 tilt만을 원인으로 단정하지 않음 |
| D5 /885–903 | R0 backward/left+,R1 forward/left−,양wristyaw−0.08·12모델+6정착. 같은 공동전진 대신 상대 파지 배치/입구방향 전환 | obs6 양 head/양 wrist에서 노란띠/몸판 기울기·가로배치 변화. H_B 손추적 복구 없이 큰면 가림 유지. grip간격 보존은 의도이며 실측 인증 아님. 실제 방향 전환 시도와 body-entry 성립을 구분. R1guide/R0support 유지라 역할 교환 아님 |
| D6 /903–921 | 바꾼 방향 유지·양forward+0.12/left+0.20·12모델+6정착, 측면 body-opening 접근 시험 | obs7 양 head/양 wrist에서 방향 변화 뒤 대각 접근은 실제 수행됐으나 H_B 가림/큰면 관계가 유지. 입구/손 진전 확정은 없음 |
| D7 /921–937 | 양lift−0.14·10모델+6정착, 손과 입구 후보의 가시성 회복 | obs8 양 head/양 wrist에서 손/줄무늬전완이 노란 경계 바로 위에 재노출. R0 wrist 왼쪽손과 긴 전완·R1 wrist 상단손이 보이고 두 head도 팔–경계 관계가 더 드러남. 실제 관측 복구이며 D5/D6와 같은 가림으로 묶지 않음. 연속 통과·손/역할 교환 완료는 미확인 |
| D8 /937–953 | 회복한 높이/방향 유지·양forward+0.20·10모델+6정착 | obs9 양 head/양 wrist에서 H_B가 R0 wrist상단왼쪽/R1 wrist상단오른쪽에 유지되고 R0 wrist그리퍼아래왼쪽에 가까운 다른손 H_A가 새로 크게 드러남. 두손 관계 재구별·정보 진전이며 이전 D2/D4의 즉시가림과 다름. H_B–rim 접근/투영 겹침이나 H_A재노출을 소매/경계 통과로 라벨링하지 않음 |
| D9 /953–967 | R0retract−0.04/R1extension+0.08·8모델+6정착, H_A 여유와 H_B 접근을 함께 조정 | 실측 arm R0−18.23mm/R1+31.88mm. obs10 양 head/양 wrist에서953의 두손 가시성 유지. H_A는 R0 outer finger 가까이에 남아 여유 증가 확정X, H_B는 상단노란경계에 가깝지만 통과미확인. R1 arm잔차+5.86mm. R1guide/R0clearance 수행은 보이되 과거 대비 역할교환 아님 |
| D10 /967–981 | R1 wrist8점 query 뒤 R0targets유지/R1 inward base−0.04·extension+0.07·8모델+6정착, guide만 접근 | obs11 양 head/양 wrist에서953이후 두손관계 유지. H_B–상단rim 근접의 미소변화는 있으나 연속진입/새전완통과 없음. H_A도 R0 finger 가까이 남음. 실제 역할분담이지만 역할교환은 아님. D9/D10은 현 배치의 미세접근으로 구분 |
| D11 /981–995 | R0targets유지/R1base forward+0.12·left−0.04·8모델+6정착, 남은 extension 추종과 함께 유한 접근 | obs12 양 head/양 wrist에서 H_A는R0finger아래에 남고 H_B는R1상단rim뒤로 더 가려짐. 실제 접근 뒤 가림 증가이지 이동무효/간격불변 증거는 아님. 현재 선택뷰에서는 남은 거리·연속통과를 더 확정하기 어려움 |
| D12 /995–1009 | R0forward+0.24/lift+0.08,R1forward+0.12·8모델+6정착, fore-aft skew를 줄이는 body-entry 시험 | obs13 양 head/양 wrist에서953–995에 유지됐던 H_A 아래손 재노출도 사라져 두손 관계가 다시 추적 불가. R0 wrist 얼굴/팔·노란띠, R1 wrist 큰 천면은 남음. 실제 접근 후 관계 상실이며 연속통과/실패 확정 아님.953의 이전 유용한 관계를 소급 부정하지 않음 |
| D13 /1009–1027 | 양pitch−0.15/lift−0.158/retract−0.012·12모델+6정착, held-edge 위치를 대략 유지하며 더 세운 입구 자세를 시험 | obs14 양 head/양 wrist에서 R0 head의 가까운손/전완 일부 재노출, H_B 연속추적/진입은 미확인. actualpitch−0.460/−0.461rad·lift−131.6/−136.1mm, 로봇별 base frame의 grasp 기준점 endpoint변화4.62/3.10mm로 근사유지. base world 이동도0.95/1.12mm 남아 world정지·천 재료점 고정/입구 upright 인증은 아님. pitch잔차약−.039rad/lift−7.3mm |
| D14 /1027–1033 | 모델 all-zero6전이·추가 자동정착0, D13 잔류 pitch/lift 목표 추종을 확인 | obs15 양 head/R1 wrist에서 D13 corners·가까운손 일부 관계 거의 유지. lift잔차−7.29/−7.36→+0.28/+0.25mm, pitch잔차약−.039→−.013rad·lift속도약−39→−0.5mm/s로 수렴 확인. 새 통과 증거 없음. 실행 설정settle6 유지이고 별도 모델 중립을 자동settle12 변경으로 세지 않음 |
| D15 /1033–1049 | 양forward+0.12/lift+0.08·10모델+6정착, 바꾼 orientation에서 body-entry 시험 | obs16 양 head/양 wrist에서 천이 더 올라가 상단노란띠/파란면 형상 변화. H_B 새출현/연속 전완통과는 보이지 않음. R0 head 가까운손/팔 일부는 천 옆에 남고 wrist들은 천가림·아래얼굴 위주. 실제 진입 시험과 미확인 결과를 분리 |
| D16 /1049–1065 | 양local-right(base_left−0.16)/lift+0.10·10모델+6정착, guide측 sleeve후보를 H_B쪽으로 옮기는 body-entry 가설 시험 | obs17 양 head/양 wrist에서 큰면이 더 올라가 wrist 사람가시성 감소. R1 head 오른쪽 화면끝에 작은 피부색 손 일부처럼 보이는 돌출 후보가 있음. 잘린 경계라 어느손·전완연결·통과 여부는 미확정이며 후속 비교 대상으로 보존. H_B 연속추적 미확인 |
| D17 /1065–1081 | R0targets유지/R1base-left+0.296·base-yaw−0.10·wrist-yaw+0.052·10모델+6정착, held-edge 근사유지를 목표로 head 시점을 회전 | obs18 양 head/양 wrist에서 R1 head 오른쪽 손조각이 조금 더 보이나 연결 전완·손 정체·소매 통과는 미확인. R0 관계 대략 유지. 실제 로봇을 움직인 관측 행동으로 물리0 query와 다름. 독립 공개pose 대조: R0/R1 world grasp XY변화1.686/1.667mm, Z약+6mm·3Dnorm6.272/6.221mm, R1baseyaw−.142978rad. 수평endpoint 근사유지와 완전고정은 구분 |
| D18 /1081–1107 | R1base-left+0.37/base-yaw−0.125/wrist-yaw+0.065·20모델+6정착, 같은 보상 관측을 확대 | obs19 양 head/양 wrist에서 R1 head의 손/짧은 손목이 천 오른쪽 경계 밖에 더 분명히 노출. 연결전완 대부분 가림이라 H_B정체/소매통과 미확정. 공개world grasp R1Δ[−3.497,−.736,−.140]mm·norm3.576mm, baseyaw−.357114rad(~20.46°). R0norm.696mm. 큰시점변경+작은endpoint변화로 얻은 유용한 정보. 경로최대이탈·천재료점고정은 검증안함 |
| D19 /1107–1121 | R1 head8점 query 뒤 R0targets유지/R1lower−0.15/retract−0.06·8모델+6정착, 접힌 guide측 경계를 풀고 손 연결을 보려는 복구 | obs20 양 head/양 wrist에서 R1corner가 낮아져span기울기 변화. R1 head의 기존 손/짧은손목 노출 유지, 연결전완/H_B정체 새확인 없음. 질의의 손후보 opticalZ.726/.763m와 주변표면.907–1.024m 차이는 소매 안팎 정답이 아님 |
| D20 /1121–1139 | R1roll+0.10·12모델+6정착, 올라접힌 노란lip를 펴려는 명시적 회전 | obs21 양 head/양 wrist에서 손목시점/노란lip각도 크게 변하나 두head의 큰면/손 관계 대체로 유지. 추가 정보 이득은 작지만 실제 회전 수행은 구분. 기존 손노출은 유지되고 H_B 정체·연속통과는 미확인. 의도와 roll명령 일치 |
| D21 /1139·물리0 | finish_episode. 손 정체·소매통과 미해결로 사람 앞의 파지를 유지하며 자율 마감 | 선언steps1에 대해 applied_segment1139→1139·actual_steps0. 마지막22번째 요청 슬롯의 모델 finish이며 제어기 budgetstop/감독 중단 아님 |

공개 질의는 index2 R0 wrist6점, index10 R1 wrist8점, index19 R1 head8점의 총3회·22/22valid·물리0이다. 첫 질의는 손후보 opticalZ약0.77–0.79m와 lip후보0.23–0.27m, 두 번째는0.339–0.357m와0.210–0.224m를 구별했다. 세 번째는 후반 노출손과 인접 천 표면을 구별했다. D8 설명의 depth 수치를 별도 query로 더 세지 않는다. 질의는 현재 보이는 표면 정보이며 픽셀 의미·입구 평면·손 정체·소매 안팎 정답을 제공하지 않는다.

일반 task-progress 동작으로 fallback하더라도 그 자체를 M2의 손·역할 교환 수행으로 세지 않는다. 새 천–손 관계뿐 아니라, 대응하는 손/경계 표면의 유효한 측정 간격 감소와 예측한 유한 접근의 실현도 진전으로 기록한다. D9/D10의 미세접근 분류는 포화 판정이 아니다.953의 두손 관계는995까지 일부 유지됐고1009에서 상실됐다. 이 후속 상실을 앞선 진전이 없었다는 뜻으로 소급하지 않는다. 같은 가림/접힘이2–3회 지속되고 유용한 간격 감소·목표 관계 변화도 없을 때 현재 조작의 포화와 다른 방법 필요성을 검토한다. 이는 자동 종료 규칙이 아니다. 카메라가 움직이므로 서로 다른 프레임의 opticalZ 단독 감소를 같은 손–rim 거리 감소로 대신하지 않는다. 자료는 `unreviewed`다.

## 별도 오프라인 비교의 범위

실행 담당자가 검수한 [초기 손 정체 비교](../research/2026-11-07-e26-initial-hand-comparison.ko.md)·[47개 공개 파일 SHA](../research/2026-11-07-e26-initial-hand-comparison.json)는 E26 obs0/1·809경계까지만 비교하며 이후 E26 결과를 판정하지 않는다. [E23](20261107-astra-progress787-named-001.ko.md)의 초기 D0–2는 낮은 H_A를, 이번 E26 초기 D0는 높은 H_B를 선택했다는 **초기 목표 대비**는 지지된다. 다만 E23 후반에는 다른 전완/높은 R1 경계가 관여했고 [E24](20261107-astra-progress1179-named-001.ko.md)에도 R1 guide/R0 anchor가 있었다. 따라서 모든 과거 시도 대비 첫 H_B 선택·완전한 역할 교환·M2 전체 수행으로 확대하지 않는다. 배우가 유지한 불확실성과 이 외부 비교를 분리하며 이 결과를 실행 중 actor에게 전달하지 않았다.

## 보존할 결과와 한계

D13의 큰 pitch 변화와 작은 그리퍼 기준점 endpoint 차이, D14의 잔류 목표 수렴, D17/D18의 보상 관측은 득점 여부와 별개로 통제된 부분 기능의 근거다. D17에서는 world XY endpoint 변화가 양측 약1.7mm였지만 Z가 약+6mm였다. D18은 R1base yaw 약20.46°와 world endpoint norm3.58mm가 함께 나타나 잘린 손조각을 화면 안의 손/짧은 손목으로 더 드러냈다. 두 endpoint만으로 경로 중 최대 이탈·완전 world 정지·천 재료점 고정은 인증하지 않는다.

19번째 관측의 손은 천 오른쪽 경계 밖에 보이지만 연결 전완 대부분이 가렸다. D19 lower/retract와 D20 명시적 roll 뒤에도 그 노출은 유지됐으나 H_B 정체·소매 안팎·연속 통과는 더 확인되지 않았다. 이는 후반 보정의 정보 이득 한계이며 전체 방법의 물리적 불가능이나 모든 이전 진전의 부정은 아니다.

[학습 검토 JSON](20261107-astra-hand-swap787-named-001-learning-segments.json)은 새352전이를21개 연속 구간으로 보존한다.953의 유용한 공개 관계, 이후 상실, D13 자세 보상/D14 중립, D17/D18 관측 보상, 세 질의와 마지막 물리0 finish를 각각 기록한다.21개 act의 named→공식 배열→적용 float32는 일치했고 비영 roll은 D20의 명시적 회전뿐이다. 실제 release/regrasp는0이다. 같은 출처·재실행 prefix·인접 관측·중첩 영상은 독립 성공 표본이 아니다. 학습 승인은 `unreviewed`다.

[후반 접근·보상 관측·복구1033–1139](../../gallery/assets/20261107-e26-view-orbit/event.mp4)·107프레임/21.4초, [방향 변경·낮춘 접근885–981](../../gallery/assets/20261107-e26-lower-approach/event.mp4)·97프레임/19.4초, [자세 보상1009–1033](../../gallery/assets/20261107-e26-compensated-posture/event.mp4)·25프레임/5초를 공개했다. 모두5fps·4배 느리게이며 구간 내 생략·보간·모델 응답 대기는 없다. [전체 공개 기록](../attempts/20261107-astra-hand-swap787-named-001/README.ko.md)과 [overview](../attempts/20261107-astra-hand-swap787-named-001/overview.mp4)에서 앞선 준비·접근도 확인할 수 있다.

최종1139경계 지정5뷰를 직접 확인했다. [R1 head](../attempts/20261107-astra-hand-swap787-named-001/images/final-robot_1_head.png)의 손/짧은손목은 천 옆에 남고, R0 head에는 사람 얼굴과 팔 일부가 보이지만 두 wrist는 주로 천을 보여준다. overview에서도 옷은 사람 앞에 매달려 있다. 이 모습은 손노출 유지와 양립하나 연결전완·H_B 정체·소매 통과를 확정하지 않는다. 마감 finish는 추가 전이를 만들지 않았다.

원본 백업은 별도 담당자가 검증 중이며 고정 revision·재다운로드 receipt 도착 뒤 반영한다. 다음 실행 선택은 [STATUS](../../project/STATUS.md)를 따른다.


백업 마감 갱신: [고정 원본 검증](../../project/sessions/20261107-e26-backup-verification.json)은revision`41c78439105eb3a6e1f5fd9c0943cee6039d041b`·2,544,928,271bytes·SHA`82f7f3fb3b0b255c7549499078ef86e90352257f12cb728ccbd88221e5127d44`다. 2026-11-07T06:49:13.774600+00:00에강제재다운로드·254member SHA·private검증을마쳤다. 위 백업 진행중 문구는 작성 당시 상태다.
