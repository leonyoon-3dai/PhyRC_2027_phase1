# B1: 공개 depth의 카메라 좌표 변환 연결 검사

종료된 E06의 공개 RGB-D를 이용해 **광축 Z depth → 카메라 XYZ** 연결을 CPU에서 확인했습니다. 기준선 이름은 B1이며 현재 actor 입력인 B0, 후속 pose+depth B2와 구분합니다. 사람 관절·의복 키포인트를 검출하지 않았고 실제 자세 추정 정확도를 평가하지 않았습니다. 현재 실행 중인 수집 코드와 모델 입력은 바꾸지 않았습니다.

[결과 JSON·원본 해시·불확실성](../assets/20261106-b1-depth-sanity/result.json) · [독립 offline 모듈](../../../participant/research/depth_backprojection.py) · [CPU 테스트](../../../tests/test_depth_backprojection.py) · [같은 관측의 시각 검토](2026-11-06-continuation-public-review.ko.md)

## 입력과 좌표의 의미

`20261106-astra-dressing-continue-001`의 저장 관측 0·2에서 지정 카메라 5개씩, 총 10표본을 사용했습니다. 입력은 해당 `public_depth.npz`의 `depth`, `depth_valid`, 원본 RGB PNG, 공개 관측 시계와 저장된 `run_metadata.json.public_interface`의 내부행렬·해상도입니다. 같은 JSON 안의 다른 metadata를 모델 입력이나 결과로 복사하지 않습니다. HDF5·audit·평가·seed·내부 장면 기하·world extrinsic은 사용하지 않았습니다.

실제 관절점을 별도로 선택하지 않았으므로 픽셀은 모두 **화면 중심 `(u,v)=(128,128)`의 calibration probe**입니다. 이것은 사람·옷·그리퍼에 대한 의미 라벨이 아닙니다. 좌표는 0부터 시작하는 `(열, 행)`이며 임의의 half-pixel 보정을 추가하지 않았습니다. RGB와 depth가 모두 256×256인지 확인했고, 저장된 내부행렬 두 공개 출처가 일치하는지도 검사했습니다.

계약의 depth는 카메라에서 점까지의 유클리드 거리가 아니라 **광축 방향 Z의 미터 값**입니다. 카메라 좌표는 X 오른쪽·Y 아래·Z 앞이며 다음 식을 사용합니다.

`[X, Y, Z]ᵀ = Z · K⁻¹ · [u, v, 1]ᵀ`

출처는 저장된 공개 내부행렬이며, 센서 의미는 [공개 계약](../../../config/policy_interface.json)과 [`distance_to_image_plane`를 사용하는 센서 코드](../../../src/PhyRC_Sim/Policy/sensors.py)에서 확인했습니다. 현재 pilot은 내부행렬의 주점 `(128,128)`과 표본이 같아 계산된 X·Y가 모두 0입니다. 비중심 픽셀, 서로 다른 fx·fy와 skew가 있는 내부행렬은 합성 테스트에서 별도로 검증했습니다. world 좌표나 여러 카메라를 합친 3D skeleton은 생성하지 않습니다.

## invalid와 불확실성 보존

중심 픽셀의 mask가 거짓이거나 depth가 비유한·0 이하이면 XYZ를 `null`로 남깁니다. 주변에 유효 값이 있어도 중심 depth를 몰래 대체하지 않습니다. 각 표본에는 중심 RGB·depth와 5×5 patch의 유효 비율, 중앙값, MAD, 최솟값·최댓값과 범위를 기록합니다. MAD는 `median(|Z−median(Z)|)`이며 위치 정확도의 표준편차나 관절 검출 confidence가 아닙니다.

기본 주의 플래그는 유효 비율 0.8 미만, mask와 숫자의 불일치, 영상 경계에서 잘린 patch, depth 범위 또는 중심−중앙값 차이가 `max(0.05m, 0.05×patch 중앙값)`보다 큰 경우입니다. 이는 분리된 휴리스틱 기준이며 실제 접촉 경계나 정확도를 검증한 임계값이 아닙니다. 플래그가 없다는 사실만으로 그 픽셀이 옳은 관절점이거나 장애물이 없다고 판단하지 않습니다.

## 실제 중심 표본 결과

| 카메라 | 관측 0의 중심 Z | 관측 2의 중심 Z | 관측 2 patch MAD | 처리 |
|---|---:|---:|---:|---|
| overview | 2.565314m | 2.565314m | 0.007429m | 유효 depth 표본 |
| robot_0_wrist | 0.201167m | 0.201614m | 0.000275m | 유효 depth 표본 |
| robot_1_wrist | invalid | invalid | null | XYZ=null, 보간 없음 |
| robot_0_head | 2.730727m | 2.730735m | 0.021694m | 유효 depth 표본 |
| robot_1_head | 1.732296m | 1.732299m | 0.013763m | 유효 depth 표본 |

8개 표본에 유효 depth가 있었고 로봇 1 손목 카메라의 중심 2개 표본은 mask=false·depth=0이었습니다. 이 개수를 pose 검출 성공률이나 정확도로 해석하지 않습니다. 이번 유효 표본의 5×5 patch는 모두 유효 비율 1.0이고 설정한 깊이 차이 주의 기준을 넘지 않았습니다. 서로 다른 시점의 중심 픽셀은 같은 표면점을 추적한 것이 아니므로 두 Z의 차이를 옷·그리퍼의 실제 이동으로 해석하지 않습니다.

입력 읽기·해시·10표본 계산의 실제 CPU 경과는 **0.0648초**였습니다. 모델 호출·GPU 작업은 없으며, 이 작은 offline 비용을 전체 로보틱스 지각·행동 지연으로 일반화하지 않습니다. 유효 표본의 재투영 roundtrip은 수식 연결 점검일 뿐 독립적인 정확도 검증이 아닙니다.

## 재현과 다음 경계

CPU 회귀 11개가 통과했습니다. 광축 Z와 ray 거리의 구분, 비중심 좌표·skew, invalid 중심 무보간, depth 불연속, patch MAD·유효 비율, 비유한 값, 좌표·영상 경계, calibration 불일치, 닫히지 않은 source 거부와 출력 덮어쓰기 거부를 확인합니다. metadata canary도 결과에 포함되지 않았습니다.

```bash
PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -p test_depth_backprojection.py -v
PYTHONPATH=. .venv/bin/python -m participant.research.depth_backprojection \
  --run-id 20261106-astra-dressing-continue-001 \
  --observations 0 2 --patch-radius 2 \
  --output /tmp/phyrc-b1-depth-sanity-new.json
```

출력은 새 파일만 허용합니다. 결과 JSON은 내부행렬의 정확한 공개 출처, RGB·depth·관측 JSON의 SHA256과 모듈 해시를 기록합니다. 원본 PNG나 depth는 수정하지 않았습니다.

다음 단계는 별도 검토한 실제 RGB 픽셀 선택 또는 pose detector의 2D 출력에 같은 역투영·invalid 처리를 연결하고, 가림·표면 depth와 해부학적 관절 중심의 차이를 평가하는 것입니다. 현재는 그 단계의 키포인트나 정확도 기준이 정해지지 않았으며, B1 결과를 실시간 actor에 주입하지 않습니다.
