# 배열·명명 행동의 실제 CLI 연결 검사

**2026-11-06 05:32:22~05:32:48 UTC에 새 thread 4개로 ABBA 연결 검사를 마쳤고, 4개 응답 모두 지정한 행동과 정확히 일치했습니다.** `gpt-6-astra`·`ultra`, CLI 0.166.0, 호출별 timeout 90초를 유지했습니다. 이는 명시된 숫자를 두 JSON 형식으로 표현하는 검사이며 실제 착의 판단·오류 감소·수집 속도 개선을 검증한 결과는 아닙니다.

[선별 결과·시간·usage·소스 SHA](../assets/20261106-action-encoding-probe-001/summary.json) · [입력 동일성·정리 후 검사](../assets/20261106-action-encoding-probe-001/cleanup-and-input-checks.json) · [파일 manifest](../assets/20261106-action-encoding-probe-001/manifest.json) · [probe 스크립트](../../../scripts/probe_action_encoding.py) · [명명 변환 prototype](2026-11-06-named-action-encoding.ko.md)

## 동일한 명령과 실제 결과

두 로봇 모두 **`base_forward=-0.65`, 나머지 움직임 채널 0, `gripper=1`**을 표현하도록 명시했습니다. 현장에서 행동을 선택하거나 E07 decision 27을 수정하는 요청이 아닙니다. 시뮬레이터를 실행하거나 행동을 전송하지 않았고 서버 GPU 작업도 없었습니다.

| 순서 | 형식 | actor wall | CLI input tokens | CLI output tokens | 검증·최종 응답 |
|---:|---|---:|---:|---:|---|
| 1 | A · 배열 | 4.526초 | 7,410 | 56 | [정확히 일치](../assets/20261106-action-encoding-probe-001/response-00-array.json) |
| 2 | B · 명명 채널 | 6.227초 | 7,498 | 142 | [정확히 일치](../assets/20261106-action-encoding-probe-001/response-01-named.json) |
| 3 | B · 명명 채널 | 6.527초 | 7,498 | 142 | [정확히 일치](../assets/20261106-action-encoding-probe-001/response-02-named.json) |
| 4 | A · 배열 | 5.325초 | 7,410 | 56 | [정확히 일치](../assets/20261106-action-encoding-probe-001/response-03-array.json) |

`actor wall`에는 입력 준비·Docker/CLI 실행·네트워크·서비스 대기·생성·결과 해석이 포함됩니다. 격리 환경 준비와 정리 시간은 별도 필드로 보존했습니다. 모델 내부 추론 시간으로 표시하지 않습니다. usage는 **각각 한 턴인 새 thread의 CLI 보고값**이며 네 호출 모두 cached input과 reasoning output은 0으로 보고됐습니다. 별도 tokenizer로 재계산한 값은 아닙니다.

이 간단한 목표에서 명명 응답은 출력 토큰이 142개로 배열의 56개보다 많았습니다. 각 조건 2회뿐이고 **E07 수집의 모델 요청과 겹칠 수 있는 서비스 부하를 분리·계측하지 않았으므로** 표의 시간을 형식 변경의 일반적인 지연 효과로 해석하지 않습니다. 초단순 명령의 4/4 일치를 실제 과제 성공률이나 불필요한 손목 회전 감소로 확대하지도 않습니다.

<details>
<summary>프롬프트·엄격한 스키마·이미지 조건</summary>

실제로 Actor에 전달한 [배열 프롬프트](../assets/20261106-action-encoding-probe-001/prompt-array.txt)·[배열 스키마](../assets/20261106-action-encoding-probe-001/schema-array.json), [명명 프롬프트](../assets/20261106-action-encoding-probe-001/prompt-named.txt)·[명명 스키마](../assets/20261106-action-encoding-probe-001/schema-named.json)를 보존했습니다. 같은 형식의 두 호출은 각각 동일한 입력 바이트를 사용했습니다. 스키마는 필수 키·여분 키 금지·정확한 배열 길이·수치 범위를 지정하며, 반환 후 기존 공식 행동 검사와 명명 변환기로 로봇 순서·채널·bool 거부·float32 예상값 일치를 다시 확인했습니다.

기존 Actor가 이미지 1~16개를 요구하므로 네 호출 모두 **같은 16×16 회색 PNG 한 장**을 넣었습니다. [원본 fixture](../assets/20261106-action-encoding-probe-001/constant-gray.png)는 장면 정보가 없으며 프롬프트에 무정보 transport fixture라고 명시했습니다. Actor가 재인코딩해 실제 전송한 네 이미지도 원본과 바이트 SHA가 같음을 확인했습니다. 지정 카메라·평가·기하·점수·저장소 문맥을 입력하지 않았습니다.

`--output-schema`로 최종 JSON 형식을 지정하는 경로는 [공식 Codex 비대화형 문서](https://learn.chatgpt.com/docs/non-interactive-mode#create-structured-outputs-with-a-schema)를 참고했고, 실제 동작은 저장소의 기존 Actor 0.166.0 경로로 검사했습니다. 소스가 기록한 `schema_sha256`은 사람이 읽기 위한 들여쓰기 버전의 해시이며, 공개한 `actual_staged_schema_sha256`은 Actor가 실제 입력한 동등한 스키마 바이트의 해시입니다. 두 표현의 JSON 내용이 같음을 확인했습니다.

</details>

<details>
<summary>격리·실패 처리·재현 범위</summary>

호출마다 전용 Actor root·CODEX_HOME 사본·내부 Docker 네트워크·proxy와 새 thread를 사용했습니다. 기존 E07 session·인증·설정은 변경하지 않았습니다. 네 호출은 모두 완료됐고 추가 재시도는 0회입니다. 반환 이벤트에서 tool/unsupported item 0개, malformed line 0개를 확인했습니다. 이것을 모델에 등록된 도구 자체가 0개였다는 의미로 해석하지 않습니다.

정리 후 인증 사본 0개, 이 probe 디렉터리를 mount한 잔여 actor 컨테이너 0개를 확인했습니다. 각 Actor의 네트워크 제거가 성공했고 후검사에서 빈 actor 네트워크도 없었습니다. thread 4개의 서로 다름을 확인했지만 UUID·인증·원시 reasoning·비공개 stderr·host 경로는 공개 자료에 넣지 않았습니다. 로컬 원본은 `output/sessions/20261106-action-encoding-probe-001`에 보존했습니다.

실행 전 CPU 테스트 **4개**는 고정된 ABBA 순서·model/timeout·스키마·정답과 잘못된 roll의 구분·각기 다른 Actor root·호출당 한 번·정리를 확인했습니다. 실제 모델 4호출과 CPU mock 테스트를 따로 집계합니다.

```bash
# 기본 실행은 계획만 출력하며 모델을 호출하지 않음
PYTHONPATH=.:src/PhyRC_Sim .venv/bin/python scripts/probe_action_encoding.py

# 이번에 실제 실행한 명령; 재실행은 새로운 출력 폴더가 필요함
PYTHONPATH=.:src/PhyRC_Sim .venv/bin/python scripts/probe_action_encoding.py \
  --execute --output output/sessions/20261106-action-encoding-probe-001
```

기존 폴더 덮어쓰기를 거부합니다. 잘못된 응답은 같은 슬롯에서 재요청하지 않고 보존하며, 자원 정리가 불확실하면 후속 요청을 중단하도록 설계했습니다. 현재 결과는 표현 연결을 확인한 기록이며 수집 runtime에 적용한 변경은 없습니다.

</details>
