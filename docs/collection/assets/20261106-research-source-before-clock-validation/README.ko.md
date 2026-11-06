# 공개 관측 시각 검사 추가 전 연구 소스

[B1b 결과](../20261106-b1b-color-depth-roi/result.json)와 [B1c 결과](../20261106-b1c-color-pair-comparison/result.json)에 기록된 소스 SHA를 재현할 수 있도록 변경 전 파일을 원본 바이트 그대로 보존했습니다.

| 파일 | 변경 전 SHA256 |
|---|---|
| [color_depth_roi.py](color_depth_roi.py) | `a9ffaa4c793cfb223689db8d5f41a3b8328035ca0418d9e4b62df845441c485d` |
| [color_pair_comparison.py](color_pair_comparison.py) | `a38877f47fe435a4dfca9df764e89cf72ac69ea413123a2d87f3b5279d2e9103` |

독립 CPU 검토에서 B1b·B1c가 잘못된 형식의 `simulation_time_s`를 결과로 복사할 수 있음을 합성 입력으로 확인했습니다. 현재 연구 모듈에는 B1과 동일하게 **bool을 제외한 유한 int/float만 허용하는 검사**와 잘못된 시각을 거부하는 회귀 테스트를 추가했습니다. dict·list·문자열·bool·null·NaN·Infinity 입력은 출력 폴더 생성 전에 거부합니다.

실제 사용한 고정 5프레임의 시각은 정상 숫자이며 기존 후보·depth·보류 결과의 오류나 정보 유출을 발견한 것은 아닙니다. 기존 결과 JSON·PNG·SVG는 변경하지 않았습니다. 변경 범위는 별도 offline 연구 코드와 테스트이며 현재 수집 runtime·모델 입력과 관계없습니다. 이 폴더는 과거 결과 재현용이며, 새 분석 실행에는 현재 `participant/research` 모듈을 사용합니다.

수정 후 2026-11-06 05:14 UTC의 전체 CPU 검사는 **141개 통과·오류/실패 없음·3.103초**였습니다. 연구 검사 31개(B1 11·B1b 11·B1c 9)와 기존 수집·기타 검사 110개입니다. B1b 3프레임·B1c 5프레임을 새 로컬 출력으로 다시 계산해 후보·depth·보류·입력 해시·PNG/SVG 해시가 기존 결과와 정확히 같음을 확인했습니다. A/B는 5쌍, C는 2쌍 출력·3건 보류로 유지됐으며 이는 정확도 검증이 아닙니다.

```bash
PYTHONPATH=.:src/PhyRC_Sim .venv/bin/python -m unittest discover -s tests -p 'test_*.py' -v
```

첫 독립 검사에서는 `PYTHONPATH=.`만 지정해 공식 `Policy` 모듈 import 오류 6개가 발생했습니다. 실행 경로를 수정한 뒤 변경 전 139개, 두 회귀 테스트 추가 후 141개가 통과했습니다. 이 실행 설정 실패와 각 검사 원본 로그는 로컬 `output/verification/20261106-research-cpu-review-001`~`003`에 따로 보존했습니다.

[전체 CPU 검사와 소스 SHA](verification.json) · [기존 프레임·산출물 일치 검사](actual-frame-compatibility.json)
