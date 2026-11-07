# 공개 손목 좌표의 이동 방향 보조 · 미채택 후보

**현재 E27에는 적용하지 않았다.** 기존 새 파지 task-progress를 그대로 실행하며, 선택형 계산 보조는 별도 worktree에서 준비·검증했다. 새 센서나 새 파지 방법이 아니고 착의 점수 향상을 확인한 것도 아니다.

[고정 후보·정적 근거 백업](../../project/sessions/20261107-wrist-translation-candidate-backup-verification.json) · [격리 전체 CPU 결과](../../project/sessions/20261107-wrist-translation-full-suite.json) · [현재 실제 실행](../../project/STATUS.md)

| 구분 | 이미 제공되던 정보 | 이번 미채택 후보 |
|---|---|---|
| 깊이 질의 | 같은 현재 카메라의 optical Z와 선택형 camera XYZ/range, K·정적 mount | 새 표면·센서·질의점을 추가하지 않음 |
| 로봇 상태 | 공개 base/grasp pose, 관절·행동 척도 | 공개 pose와 고정 mount를 합성해 손목 camera frame에서 양의 base-forward/left·lift·arm-extension 방향 계산 |
| 선택점 해석 | actor가 고른 최대8개 가시 픽셀 | 고정 grasp reference에 대한 좌표차·각 방향에 대한 dot product. 점의 정체는 여전히 시각 가설 |
| 제어 효과 | 실제 다음 관측에서 확인 | 명령·IK·여유 공간·접촉·천 운동·입구 통과를 추론하지 않음 |

공개 robot USD에서 grasp-center와 손목 camera mount 사이가 fixed joint4개로 연결되고 finger hinge는 별도 분기임을 확인했다. GPU 장치와 network가 없는 읽기 전용 컨테이너에서 pxr만 사용해 정적 파일을 읽었다. joint-frame 합성과 authored rest transform의 최대 차이는9.31e−9였고, 정적 재현 결과는 두 실행에서 byte동일했다. 실제 sensor pose나 장면 상태를 조회한 검증은 아니다. [작업 규칙](../../competition/RULES.md)은 정적 calibration과 공개 관절 상태에 결합한 로봇 자신의 공개 geometry를 허용한다.

계산은 정규화된wxyz와 optical X오른쪽/Y아래/Z전방을 사용한다. base의 forward/left는 실제 제어기와 같은 world 수평 투영을 따르고, lift/arm은 검증된 base+Z/+X를 변환한다. 수평 heading이 퇴화하면 해당 축을 unavailable로 남긴다. **양의 로봇 이동 방향과 정지 장면의 상대 이동 부호는 반대**이며, 현재 unit axis는 실제 이동량·이미지 흐름·잔류 운동을 예측하지 않는다.

**grasp reference는 원하는 손 위치나 접촉점이 아니다.** 손을 그리퍼 중심에 맞추라는 처방으로 쓰지 않고, 필요한 경우 actor가 식별한 손–rim 두점의 차이를 해석한다. 축들은 중복·비직교일 수 있어 개별 투영의 합은 역제어 해가 아니다. 손목 camera·geometry=true에서만 제공하는 `--wrist-translation-aid`가 기본OFF이며 기존query가 필요하다. 관측당1질의·최대8점·질의물리0·기존action후속1회·공식행동범위는 유지한다.

격리 후보는 로컬commit`b1f30dd6962a8179070f8fe68a7448d8a7250acc`,branch`experiments/wrist-translation-aid`,base공개`5ed549a7fe3b5b84a8ecc3201297e78f77ef7416`이다. client/exporter/helper/test/선택공개pose fixture/후보설명6개 파일이다. runtime의 새로운 의존성은 collection Python 모듈1개로 기존snapshot/preserve허용범위에 포함됨을 검사했다. 정적robot·계약 pin 불일치는 시작 전에 거부하고, 매 관측에서 공개 mount 일치를 다시 검사한다. 후보 코드는 아직main에 통합하지 않았다.

집중82검사9.072초와 기존14전략×named/query 56하위조합의OFF불변을 확인했다. 뒤이어 **전체335검사40.913초 PASS**(외부wall41.279초,실제model/GPU0)를 격리commit에서 실행했다. 56조합은 별도 unittest56개로 더하지 않는다. root는 helper 전체와 client/exporter 변경을 읽고, 전체검사log SHA 및168개소스·설정의현재SHA/전후동일을 대조했다. 이 재검토를 root에서 전체suite를 다시 실행한 것으로 설명하지 않는다.

private 연구백업은revision`f1264b24386d5b993d9f313416bd416e7676c8e0`,89,000bytes·15member·SHA`1539d06f64302fd692d476eb76a7de80ef7fb2a11423f2032b25226a5b58963e`이며07:01:25UTC고정재다운로드 검증을 마쳤다. 고정6파일·정적근거7·scope·manifest를 담았으며 raw로그·인증·USD실물·전체worktree는 넣지 않았다. **335전체CPU영수증은 그 archive에 포함되지 않은 별도 근거**다.

실제 카메라 투영·정책의 방향 오류 감소·호출 시간·착의 성능은 아직 미검증이다. E27의 새로운 파지 효과와 동시에 섞지 않고, 필요 시 닫힌 실행 뒤 별도 선택·소스 기록으로 비교한다. 현재 학습·합성 성공자료 생성은 없다.
