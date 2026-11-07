# 출발점·방법 비교 카탈로그 도구 사용법

`catalog.v1.json`은 사람이 근거를 확인해 정리하는 버전 관리 원본이다. `scripts/startpoint_catalog.py`는 이를 **stdlib Python SQLite 검색 인덱스**로 재생성한다. 원본 수집, 시뮬레이터·모델 호출, 행동 생성이나 actor 프롬프트 수정은 하지 않는다. 기본 인덱스 `output/indices/startpoint-catalog.sqlite3`는 Git에서 제외하며, 지워도 JSON으로 다시 만든다.

점수·평가 근거는 **trusted 오프라인 분석·출발점 선택 전용**이다. 카탈로그나 검색 결과를 actor 입력·교사 행동 라벨로 전달하지 않는다. `validate`는 curated JSON의 형식과 관계를 검사한다. 링크된 원본·점수·백업 영수증을 열거나 진위를 재검증하는 명령이 아니다.

## 사용

저장소 루트에서 실행한다. 외부 패키지는 필요 없다.

```bash
python3 scripts/startpoint_catalog.py validate
python3 scripts/startpoint_catalog.py build
python3 scripts/startpoint_catalog.py validate --db output/indices/startpoint-catalog.sqlite3
python3 scripts/startpoint_catalog.py list startpoints --ready --support-status observed_bilateral --boundary-score 5
python3 scripts/startpoint_catalog.py list attempts --attempt-status failed
python3 scripts/startpoint_catalog.py list methods --method-status proposed
python3 scripts/startpoint_catalog.py matrix --attempt-status planned
python3 scripts/startpoint_catalog.py show startpoints 20261106-astra-guide470-depth-001-p563
```

- `build`/`validate`: `--source PATH`로 다른 JSON을 지정할 수 있다. `build`는 검증을 마친 뒤 임시 DB를 원자적으로 교체하며, 오류 시 기존 인덱스를 보존한다. JSON 자체를 DB로 덮어쓸 수 없다.
- `list`의 별칭은 `query`; 대상은 `runs`, `startpoints`(기본), `methods`, `attempts`다. 모든 출력은 JSON이며 `usage=trusted_offline_research_only`를 명시한다.
- `--source-group`, `--run-kind`, `--qc-status`, `--support-status`, `--method-id`, `--method-status`, `--attempt-status`로 찾는다. `runs` 목록에는 처음 세 조건만 적용한다. 다른 대상에서는 해당 대상에 연결된 attempt/startpoint/run으로 필터링한다. 따라서 출발점이 없는 실제 시도는 지지·출발점 점수 조건과 일치하지 않는다.
- `--boundary-score 5`는 출발점 점수, `--result-score 5`는 시도 결과 점수다. 각각 `--boundary-score-unknown`, `--result-score-unknown`으로 미확인을 찾는다. 미확인은 0점과 다르며, 연결된 출발점/결과가 없는 경우도 포함한다.
- `--ready`/`--not-ready`는 출발점 준비 조건을 적용한다. `--limit`은 출력 행 수를 제한하며(기본100), `total`은 일치한 전체 개수다. `--db PATH`로 인덱스를 선택한다.
- `matrix`는 **등록된 시도만** 출처 계보·출발점·방법별로 묶어 planned/in_progress/completed/failed 개수를 표시한다. `actual_startpoint_counts`는 실제 시도의 도달/reached·미도달/unreached·미확인/unknown·출발점 미지정/not_applicable을 별도로 센다(planned 제외). 출발점에 도달하지 못한 failed도 실행 상태 집계에는 포함되므로, 해당 방법의 실제 조작 실패로 해석하지 않는다. 가능한 모든 조합을 만들거나 실행하지 않는다. 방법만 등록하고 시도가 없는 조합은 표시하지 않으며 `list methods`에서 찾는다.
- JSON이 갱신되면 `build`를 다시 실행한다. `validate --db ...`는 JSON SHA256과 인덱스 메타데이터를 대조해 오래된 인덱스를 거부한다. 일반 조회는 기록된 인덱스를 읽으며 출력의 `index_source_sha256`으로 버전을 식별한다.

## 서로 다른 판단을 합치지 않기

`review_ready`는 출처 run의 `qc_status=passed`, `backup.status=verified`, 알려진 녹화 길이 안의 출발 경계라는 세 조건만 뜻한다. **양측 지지 관찰·5점·실제 실행 적합성·학습 승인과 동의어가 아니다.** `observed_bilateral`도 기재된 공개 시각 근거에 대한 관찰 분류이며, 독립 하중 지지·층 구분·입구 연결·진입을 자동으로 확정하지 않는다.

`support.window_start/end`는 검토 범위다. evidence에 선택 관측 시점과 연속 검수 여부를 적는다. 범위의 길이만으로 지속 지지 시간을 계산하지 않는다. 같은 source_group의 prefix/인접 관측/재실행 분기는 독립 시연이나 검증 표본이 아니다.

`replay_prefix_steps`는 **의도한** 길이, `replay_completed_steps`는 **실제로 완료한** 길이다. 예를 들어 목표700·실제120·녹화141인 실패는 유효한 기록이다. 선택 출발점700을 기록해도 조회의 `startpoint_reached=false`로 구분한다. 실행 전 planned의 run_id와 도달 여부는 null이다. parent는 직접 계보이며, fresh 재시도는 parent가 있어도 replay0일 수 있다. replay가 있으면 parent와 source_group이 같아야 한다.

`source_commit`과 `source_working_tree_modified`를 함께 보존한다. 커밋이 있다는 이유로 clean 또는 정확한 재현 상태를 뜻하지 않는다. 행동 재실행은 천의 physics checkpoint가 아니므로 `exact_checkpoint=false`, 학습 검수는 `training_approval=unreviewed`만 허용한다. 누락 시에도 이 값으로 기본화한다.

## v1 필드

최상위 필드는 `schema_version=1`, `catalog_id`, `runs`, `startpoints`, `methods`, `attempts`다. 아래 모든 필드는 필수이며, 위 두 기본 필드만 생략할 수 있다. 모르는 값은 허용된 위치에 명시적 null로 적는다. ID는 각 배열에서 유일해야 하고 미정의 필드·중첩 JSON 키 중복을 거부한다.

| 객체 | 필드와 범위 |
|---|---|
| run | `id`, `kind`(demonstration/integration_test/failed_start/unknown), `source_group`, `source_commit`(40자리 소문자hex 또는 null), `source_working_tree_modified`(bool/null), `parent_run_id`(run ID/null), `replay_prefix_steps`(0이상 정수), `replay_completed_steps`·`recorded_transitions`(0이상 정수/null), `qc_status`(unknown/pending/passed/failed), `backup` |
| backup | `status`(unknown/pending/verified/failed), `receipt`·`revision`(문자열/null), `sha256`(64자리 소문자hex/null). verified에는 세 근거 필드가 필요하며 revision은40자리 소문자hex 고정 커밋이어야 한다(main 등 가변 참조 거부). |
| startpoint | `id`, `source_run_id`, `boundary`, `history`(boundary보다 작은 중복 없는 오름차순 정수 배열), `support`, `score_at_boundary`, `exact_checkpoint=false`, `training_approval=unreviewed` |
| support | `status`(unknown/uncertain/observed_unilateral/observed_bilateral), `evidence`·`uncertainty`(문자열 배열), `window_start`·`window_end`(둘 다 null 또는 0≤start≤end≤boundary). observed 분류에는 공개 evidence가 필요하다. |
| score_at_boundary | `raw_points`(0..50 유한 숫자/null), `evidence`(문자열/null). 알려진 점수에는 trusted 오프라인 근거가 필요하다. |
| method | `id`, `name`, `status`(proposed/ready/tested/retired), `axes`, `description` |
| axes | `grasp_arrangement`, `entry_target`, `approach`, `order`, `view`, `action_encoding`; 각 문자열/null. 설정·의도이며 실제 행동 달성 여부는 시도 review/notes로 구분한다. |
| attempt | `id`, `status`(planned/in_progress/completed/failed), `run_id`(run ID/null), `startpoint_id`(startpoint ID/null), `method_id`, `result`, `notes`(문자열/null) |
| result | `raw_points`(0..50/null), `success`(bool/null), `review`(문자열/null), `videos`(문자열 배열) |

의도한 재생은 알려진 parent 녹화 길이를 넘지 못하고, 실제 완료 길이는 의도 길이 및 알려진 자체 녹화 길이를 넘지 못한다. 실제 시도가 출발점을 지정하면 해당 출발점의 source_run이 직접 parent이며 boundary가 의도한 replay 길이와 같아야 한다. 미도달 실패는 허용하되 notes에 경위를 남긴다. run은 선택된 출발점 없이도 등록할 수 있다.

planned에는 실제 run·관측 점수·success·결과 review·영상이 없다. 실제 시도에는 run_id가 필요하며 한 run을 여러 시도로 중복 세지 않는다. proposed 방법에는 실제 시도가 없어야 하고, tested에는 completed/failed 시도가 하나 이상 있어야 한다. tested는 **종료된 시도와 연결됨**을 뜻하며, 그 방법이 실제로 모두 수행되었거나 성공했다는 뜻이 아니다. 실패 시작/중단은 run.kind·notes·review로 구분한다.

## CPU 검증

```bash
python3 -m unittest discover -s tests -p test_startpoint_catalog.py -v
```

11개 검사는 JSON↔SQLite 보존, 실제/의도 재생과 미도달 실패, source_group·직접 parent, 지지/점수/준비 상태 분리, 미실행 조합 표시, null/0/bool/비유한값, 관측 범위, PK/FK, 원자적 실패 보존, 오래된 인덱스 검출과 CLI를 다룬다. 연결된 영상·백업·점수의 진실, 새로운 정책 행동 성능이나 학습 적합성은 이 검사 범위가 아니다.
