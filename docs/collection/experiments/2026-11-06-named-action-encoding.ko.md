# 명명된 행동 채널과 공식 배열의 변환 시험

**후속 연결 검사:** [실제 Astra ABBA 4호출](2026-11-06-action-encoding-cli-probe.ko.md)에서 명시한 단순 명령의 형식 연결을 확인했습니다. 아래 prototype과 별도 시험이며 현재 수집 정책에는 적용하지 않았습니다.

**E07 decision 27의 robot 1 행동에는 7번 열 `wrist_roll=+1`이 들어 있습니다.** 이를 이름으로 분명하게 표시하는 별도 offline prototype을 만들었습니다. 기존 원본 행동을 수정하거나 현재 actor의 출력 형식·runtime을 바꾸지 않았습니다. 설명과 행동의 의미가 일치하는지 자동 판정한 것도 아닙니다.

[순수 변환 모듈](../../../participant/research/action_encoding.py) · [회귀 테스트](../../../tests/test_action_encoding.py) · [실제 decision 27과 표현 길이 비교 JSON](../assets/20261106-action-encoding/representation-comparison.json)

| 공식 열 | prototype의 이름 | 공식 공개 계약의 field |
|---:|---|---|
| 0 | `base_forward` | `base_forward_velocity` |
| 1 | `base_left` | `base_left_velocity` |
| 2 | `base_CCW_yaw` | `base_yaw_velocity` |
| 3 | `lift` | `lift_velocity` |
| 4 | `arm_extension` | `arm_extension_velocity` |
| 5 | `wrist_yaw` | `wrist_yaw_velocity` |
| 6 | `wrist_pitch` | `wrist_pitch_velocity` |
| 7 | `wrist_roll` | `wrist_roll_velocity` |
| 8 | `gripper` | `gripper_command` |

이 이름들은 `[-1,1]` 정규화 명령을 나타냅니다. 각도·실측 속도·미터 좌표가 아니며 변환기는 scale을 곱하거나 부호를 바꾸지 않습니다. `base_left` 양수는 공식 행동의 왼쪽 방향을 유지합니다. `gripper=0`은 이전 의도 유지이며 실제 천 파지를 보장하지 않습니다. [공식 공개 행동 계약](../../../config/policy_interface.json) · [행동·단위 설명](../../competition/DATA.md)

<details>
<summary>명명 JSON의 구조와 decision 27을 그대로 표시한 예</summary>

최상위 키는 `robots` 하나입니다. 목록에 `robot_id`와 `action`을 가진 객체 두 개를 넣고, ID 순서는 반드시 `robot_0`, `robot_1`입니다. 각 `action`에는 위의 9개 이름을 모두 써야 합니다. 채널 객체의 키 순서는 바꿔도 이름으로 정확한 열에 대응하지만 로봇 목록의 순서는 바꾸면 거부합니다. 누락·여분 키·다른 대소문자·중복 로봇·범위 밖 값·비유한 수·bool·문자열 숫자를 거부합니다. 원시 JSON은 `named_json_to_array`로 읽으면 중복 키와 비표준 NaN/Infinity도 거부합니다.

```python
from participant.research.action_encoding import array_to_named, named_to_array

original = [
    [-0.65, 0, 0, 0, 0, 0, 0, 0, 1],  # robot_0
    [-0.65, 0, 0, 0, 0, 0, 0, 1, 0],  # robot_1
]
named = array_to_named(original)
official_action = named_to_array(named)  # 새 float32 (2,9) 배열
```

robot 0은 `base_forward=-0.65`, `gripper=1`이고, robot 1은 `base_forward=-0.65`, **`wrist_roll=1`, `gripper=0`**으로 표시됩니다. 원본에서 두 로봇의 마지막 두 열이 다른 점이 이름으로 드러납니다. 변환기는 이 차이를 오류로 선언하거나 `wrist_roll`을 0으로 고치지 않습니다. 원본 행동의 compact JSON SHA는 비교 JSON에 기록했습니다.

왕복 검사는 공식 float32 배열의 수치를 보존합니다. 일반적인 float32 반올림으로 `-0.65`의 표시 자릿수가 늘어날 수 있으며, 원래 JSON 문자열까지 동일하게 복원한다는 뜻은 아닙니다. 원본 기록은 별도로 유지합니다.

</details>

<details>
<summary>실제 표현 크기·검사 결과·적용 전 한계</summary>

동일한 decision 27 수치를 **양쪽 모두 Python float로 통일**하고, `json.dumps(..., ensure_ascii=False, separators=(',', ':'), allow_nan=False)`로 공백 없이 직렬화했습니다. 따라서 양쪽 모두 0은 `0.0`이며 float32 변환 전의 같은 수치 표기를 비교합니다. 측정 대상은 행동 payload뿐이며 실제 모델 응답 전체가 아닙니다.

| 표현 | 문자 수 | UTF-8 바이트 |
|---|---:|---:|
| `(2,9)` 배열 | 81 | 81 |
| 명명 채널·명시적 robot ID | 384 | 384 |
| 증가 | +303 | +303 |

이 예에서는 바이트가 약 4.74배입니다. 추가 응답 토큰이 생길 가능성이 있지만 **실제 토큰 수·모델 지연·호출 수·오류 감소·과제 성능은 미측정**입니다. tokenizer를 설치하거나 모델을 호출하지 않았습니다. 이름을 쓰더라도 모델이 잘못된 채널을 선택하거나 설명과 다른 값을 낼 수 있습니다. 변환기는 설명 문자열을 읽지 않으므로 의미 일치·안전성·접촉·파지 판정을 대신하지 않습니다.

새 테스트 10개는 공식 field 순서·로봇별 열 배치·왕복·키 순서 독립성·decision 27·부호/단위 무변경·잘못된 ID/키/수치/배열·중복 JSON 키를 검사했습니다. 기존 141개와 합쳐 **전체 151개 CPU 테스트가 3.069초에 통과**했습니다. 모델·GPU 실행은 없으며 검사 중 소스 변경도 없었습니다. 기존 139→141 검사 기록은 그대로 보존합니다.

```bash
PYTHONPATH=.:src/PhyRC_Sim .venv/bin/python -m unittest discover -s tests -p 'test_*.py' -v
```

후속 비교에서는 고정된 공개 관측을 이용해 배열·명명 표현의 형식 오류와 채널 선택을 별도 검수하고 응답 토큰·wall time을 함께 측정해야 합니다. 현재 정책에 적용됐거나 실제 성능이 개선됐다는 결과는 없습니다.

</details>

[전체 151개 검사·소스 SHA](../assets/20261106-action-encoding/verification.json)
