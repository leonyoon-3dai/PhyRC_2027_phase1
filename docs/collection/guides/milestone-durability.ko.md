# 점수 구간의 저장 내구성

2026-11-06 기준입니다. **서버 장애 후 복구는 미검증**이며 아래 확장은 후속 계획입니다. 실행 코드는 변경하지 않았습니다.

| 구분 | 지원 범위 |
|---|---|
| 현재 구현 | HDF5 flush·점수 색인. 정상 마감·전수 QC 후 행동 prefix 재실행 |
| 미검증 | 강제 종료·서버 장애 뒤 마지막 milestone과 파일 간 일관성 복구 |
| 후속 계획 | 참가자 wrapper의 불변 segment·해시·fsync·복구 시험 |

<details>
<summary>기술 근거와 최소 확장 계획</summary>

현재 [DatasetWriter](../../../src/PhyRC_Sim/Policy/training_dataset.py)는 여러 dataset·파일을 순차 갱신 후 flush하며, [점수 JSONL](../../../participant/collection/evaluation.py)도 flush만 합니다. fsync나 파일 간 원자적 commit은 없습니다. [구간 색인](../../../participant/collection/milestones.py)은 HDF5 참조이고, [loader](../../../participant/collection/continuation.py)는 완료·전수 QC·해시 일치를 요구합니다. 따라서 색인이 있어도 장애로 미완료된 원본을 바로 재개할 수 없습니다.

공식 물리·센서·DatasetWriter를 바꾸지 않고 **참가자 측 wrapper**에서 다음을 검토합니다.

1. 확인된 전이 경계에서 공개 관측·행동·다음 관측을 닫힌 불변 segment로 저장하고, 마지막 완전 전이·부모 관계·점수 경계·해시를 연결합니다. 평가는 actor와 분리합니다.
2. segment fsync → 임시 manifest 쓰기·fsync → rename → 상위 디렉터리 fsync 순서를 검토하고, 저장장치의 영속 범위와 추가 지연을 측정합니다.
3. 강제 종료·재시작 시험으로 해시·전이 연속성·평가 대응을 확인합니다. 미완성 꼬리는 별도 보존하고 검증된 경계까지만 복구합니다.

</details>

이는 기록 복구 계획이며 **정확한 물리 checkpoint 복원은 별도 과제**입니다. variation은 새 run으로 재평가하고 반복 prefix와 신규 suffix를 구분합니다.
