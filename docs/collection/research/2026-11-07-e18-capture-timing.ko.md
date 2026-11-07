# E18 수집 경계 비용 재검토

**이번 검토에서 새로 채택할 수집 최적화는 확인하지 못했다.** 공식 물리·20Hz 기록·카메라 정합성과 렌더 경로를 유지했다. 닫힌 E18의 숫자 타이밍과 소스를 읽는 CPU 분석만 수행했으며 코드 변경, 새 수집·모델·GPU 실행은 없다.

범위는 `20261106-astra-guide470-depth-001`의 `step_timings.jsonl` 전체 **928행, step_index0–927**이다. 470개 재실행+457개 새 행동/정착+마지막 감독 중립1개이며, 기록된 simulation 구간은46.4초다. 원본 경로는 `output/collections/<run-id>/step_timings.jsonl`, 파일 SHA256은 다음과 같다.

```text
2d32792712fd1c24a88996d6628b567c8f5a6029f8b396f4188ef602d63afcfb
```

## 경계별 실제 비용

| 구간 | 928전이 합계 | 전이당 평균 | 전이당95백분위 |
|---|---:|---:|---:|
| environment step 전체 | 696.861초 | 750.927ms | 831.496ms |
| 그 안의 camera capture | 149.554초 | 161.157ms | 208.905ms |
| capture를 뺀 observe | 8.978초 | 9.674ms | 11.878ms |
| observe 바깥 step | 538.329초 | 580.096ms | 625.248ms |
| 별도 dataset writer | 44.784초 | 48.259ms | 56.614ms |

각 행에서 `environment step = capture + 나머지 observe + observe 바깥 step`이 정확히 성립했다. 이는 기존 호출 지점의 host wall 시간이며 GPU kernel 분해가 아니다. observe 바깥에는 제어·물리·callback·평가·대기가 섞인다. writer는 environment step 밖의 별도 시간이다. 재실행470행과 새457행의 environment 평균도 각각751.200/750.749ms로 비슷했다.

**928개 경계 모두 `_observe` 1회, `capture` 1회, observe 밖 capture 0회**였다. `capture.json`의 idle render도 호출0·시간0이다. 조사한 호출 계층에서 제거할 중복 관측은 발견하지 못했다. capture 내부의 `world.render()`와 Replicator `rt_subframes=4, delta_time=0, wait_for_render=True`는 기존 동기화 경로다. 내부 단계별 시간과 프레임 신선도 비교가 없으므로 두 호출이 불필요한 중복이라고 판단하지 않는다.

## 전체 경과와 제거 상한의 구분

| 범위 | 실제 시간 |
|---|---:|
| client 전체 wall | 1862.366초 |
| 모델 호출 경로 | 1000.803초 |
| client가 측정한 환경 dispatch 왕복 | 806.244초 |
| collector 내부 request 실행 합계 | 742.592초 |
| 내부 실행 − environment step − writer | **0.947523초** |
| 외부 dispatch − 내부 실행 | 63.652초 |

내부 합계는 `operator.jsonl`의 완료 request102개(act100·stop1·finish1), 실행928전이를 대상으로 했다. 전체 wall에는 모델 경로·환경 왕복 외에 초기화·정리 등의 시간도 포함된다. dispatch와 내부 실행의 차이를 전부 JSON 직렬화 시간으로 단정하지 않는다.

현재 collector는 요청 시작 때 `Operator.observe()`로 공개 배열을 복사하고, 각 전이의 `Operator.act()` 반환에서도 공개 배열을 복사한다. 이 복사와 검증·기록 타이밍 출력·요청 처리 등을 모두 포함한 **내부 실행의 environment/writer 밖 잔여가0.947523초**다. 이를 전부 없앤다는 **불가능한 제거 상한조차 전체 wall의 약0.051%**이며, 실제 특정 복사의 비용이나 가능한 절감량을 측정한 수치가 아니다. 새 wrapper 최적화를 우선할 근거로 삼지 않는다.

63.652초의 외부/내부 차이는 이미 문서화한 전송 경로 분리 계측 후보와 같은 범주다. capture 내부 render·Replicator·readback 분해와 같은 capture 내 link transform 재사용도 [기존 속도 연구](../../project/performance/20261106-speedup-plan.ko.md)의 범위다. 미적용 phase2 profiler를 새로 적용하거나 기존 후보를 새로운 개선으로 다시 제안하지 않았다.

해석에 사용한 현재 `collect_operator.py`, `boundary.py`, `evaluation.py`, `step_profile.py`는 E18 source snapshot과 파일 SHA가 같음을 확인했다. 이 검토는 기존 필수 동기화·기록을 생략할 근거를 찾지 못했으며, 진행 중 실행 안정성을 우선해 **신규 최적화를 채택하지 않는다.**
