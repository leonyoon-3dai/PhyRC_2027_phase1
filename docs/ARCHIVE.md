# 기록 보관함

[메인](../README.md) | [시연 목록](EPISODES.md) | [다음 수집](COLLECTION_PLAN.md) | [Astra 코드](ASTRA.md) | [클린 서버](OPERATIONS.md)

현재 안내는 네 개의 주요 문서에서 관리합니다. 아래 자료는 실행 근거와 당시 연구 기록입니다. 과거 문서의 “다음 실행”을 현재 지시로 사용하지 않습니다.

## 실행과 자료

| 찾을 것 | 자료 |
|---|---|
| 영상·관측·manifest | [시연 목록](EPISODES.md) |
| 실행·출발점·방법 정본 | [catalog.v1.json](collection/catalog/catalog.v1.json), [색인 설명](collection/catalog/README.ko.md) |
| 시도별 검수 | [reviews](collection/reviews/), [attempts](collection/attempts/) |
| 날짜별 진행 | [HISTORY](project/HISTORY.ko.md), [project sessions](project/sessions/), [collection sessions](collection/sessions/) |
| E27 마감 | [마감 기록](project/SESSION_WRAPUP_20261107.ko.md), [현재 상태](project/STATUS.md) |
| 화면 표시·원본 출처 | [robot_1 왼쪽 / robot_0 오른쪽](gallery/ROBOT_LAYOUT.ko.md) |
| 성능 계측과 한계 | [performance](project/performance/) |

## 고정 백업

다운로드·SHA·누락 파일 병합 명령은 [OPERATIONS](OPERATIONS.md)에 있습니다. 각 receipt는 해당 묶음의 고정 revision과 archive hash를 지정합니다. 한 archive를 전체 데이터 백업으로 해석하지 않습니다.

| 복원 대상 | 검증 receipt |
|---|---|
| `20261106-depth-query-wiring-backup-verification` | [JSON](project/sessions/20261106-depth-query-wiring-backup-verification.json) |
| `20261106-e10-backup-verification` | [JSON](project/sessions/20261106-e10-backup-verification.json) |
| `20261106-e11-backup-verification` | [JSON](project/sessions/20261106-e11-backup-verification.json) |
| `20261106-e12-backup-verification` | [JSON](project/sessions/20261106-e12-backup-verification.json) |
| `20261106-e13-backup-verification` | [JSON](project/sessions/20261106-e13-backup-verification.json) |
| `20261106-e14-backup-verification` | [JSON](project/sessions/20261106-e14-backup-verification.json) |
| `20261106-e15-backup-verification` | [JSON](project/sessions/20261106-e15-backup-verification.json) |
| `20261106-e16-backup-verification` | [JSON](project/sessions/20261106-e16-backup-verification.json) |
| `20261106-e17-backup-verification` | [JSON](project/sessions/20261106-e17-backup-verification.json) |
| `20261106-evening-wiring-backup-verification` | [JSON](project/sessions/20261106-evening-wiring-backup-verification.json) |
| `20261106-private-research-backup-verification` | [JSON](project/sessions/20261106-private-research-backup-verification.json) |
| `20261106-remote-backup-verification` | [JSON](project/sessions/20261106-remote-backup-verification.json) |
| `20261107-champion-reference-backup-verification` | [JSON](project/sessions/20261107-champion-reference-backup-verification.json) |
| `20261107-e18-backup-verification` | [JSON](project/sessions/20261107-e18-backup-verification.json) |
| `20261107-e19-backup-verification` | [JSON](project/sessions/20261107-e19-backup-verification.json) |
| `20261107-e20-backup-verification` | [JSON](project/sessions/20261107-e20-backup-verification.json) |
| `20261107-e21-backup-verification` | [JSON](project/sessions/20261107-e21-backup-verification.json) |
| `20261107-e22-backup-verification` | [JSON](project/sessions/20261107-e22-backup-verification.json) |
| `20261107-e23-backup-verification` | [JSON](project/sessions/20261107-e23-backup-verification.json) |
| `20261107-e24-backup-verification` | [JSON](project/sessions/20261107-e24-backup-verification.json) |
| `20261107-e25-backup-verification` | [JSON](project/sessions/20261107-e25-backup-verification.json) |
| `20261107-e26-backup-verification` | [JSON](project/sessions/20261107-e26-backup-verification.json) |
| `20261107-e27-backup-verification` | [JSON](project/sessions/20261107-e27-backup-verification.json) |
| `20261107-m2-candidate-backup-verification` | [JSON](project/sessions/20261107-m2-candidate-backup-verification.json) |
| `20261107-named-depth-wiring-backup-verification` | [JSON](project/sessions/20261107-named-depth-wiring-backup-verification.json) |
| `20261107-single-arm-offline-backup-verification` | [JSON](project/sessions/20261107-single-arm-offline-backup-verification.json) |
| `20261107-wrist-translation-candidate-backup-verification` | [JSON](project/sessions/20261107-wrist-translation-candidate-backup-verification.json) |

## 공식 자료와 보존 연구

[주최 측 README](../README.upstream.md) / [공식 문서](competition/) / [챌린지·점수 설명](project/CHALLENGE_GUIDE.ko.md) / [초기 계획](project/PLAN.ko.md) / [연구 검토](collection/research/)

## 통합 전 설명

아래는 개편 직전 commit에 고정한 원문입니다. Git 이력에서 그대로 보존하며 현재 checkout에 같은 설명을 중복 관리하지 않습니다. 실행 원본·영상·manifest·provenance는 기존 경로를 유지합니다.

| 이전 문서 | 원문 |
|---|---|
| `README.md` | [고정 원문](https://github.com/leonyoon-3dai/PhyRC_2027_phase1/blob/f17f5495259468ce2c9fc625b4eff145a28d27cf/README.md) |
| `AGENTS.md` | [고정 원문](https://github.com/leonyoon-3dai/PhyRC_2027_phase1/blob/f17f5495259468ce2c9fc625b4eff145a28d27cf/AGENTS.md) |
| `docs/project/STATUS.md` | [고정 원문](https://github.com/leonyoon-3dai/PhyRC_2027_phase1/blob/f17f5495259468ce2c9fc625b4eff145a28d27cf/docs/project/STATUS.md) |
| `README.ko.md` | [고정 원문](https://github.com/leonyoon-3dai/PhyRC_2027_phase1/blob/f17f5495259468ce2c9fc625b4eff145a28d27cf/README.ko.md) |
| `README.before-reorganization-20261106.ko.md` | [고정 원문](https://github.com/leonyoon-3dai/PhyRC_2027_phase1/blob/f17f5495259468ce2c9fc625b4eff145a28d27cf/README.before-reorganization-20261106.ko.md) |
| `README.history.en.md` | [고정 원문](https://github.com/leonyoon-3dai/PhyRC_2027_phase1/blob/f17f5495259468ce2c9fc625b4eff145a28d27cf/README.history.en.md) |
| `README.history.ko.md` | [고정 원문](https://github.com/leonyoon-3dai/PhyRC_2027_phase1/blob/f17f5495259468ce2c9fc625b4eff145a28d27cf/README.history.ko.md) |
| `docs/gallery/README.ko.md` | [고정 원문](https://github.com/leonyoon-3dai/PhyRC_2027_phase1/blob/f17f5495259468ce2c9fc625b4eff145a28d27cf/docs/gallery/README.ko.md) |
| `docs/collection/README.ko.md` | [고정 원문](https://github.com/leonyoon-3dai/PhyRC_2027_phase1/blob/f17f5495259468ce2c9fc625b4eff145a28d27cf/docs/collection/README.ko.md) |
| `docs/collection/guides/astra-end-to-end.ko.md` | [고정 원문](https://github.com/leonyoon-3dai/PhyRC_2027_phase1/blob/f17f5495259468ce2c9fc625b4eff145a28d27cf/docs/collection/guides/astra-end-to-end.ko.md) |
| `docs/project/START_HERE.ko.md` | [고정 원문](https://github.com/leonyoon-3dai/PhyRC_2027_phase1/blob/f17f5495259468ce2c9fc625b4eff145a28d27cf/docs/project/START_HERE.ko.md) |
| `docs/project/CODE_MAP.ko.md` | [고정 원문](https://github.com/leonyoon-3dai/PhyRC_2027_phase1/blob/f17f5495259468ce2c9fc625b4eff145a28d27cf/docs/project/CODE_MAP.ko.md) |
| `docs/project/CODEX_CONTEXT.ko.md` | [고정 원문](https://github.com/leonyoon-3dai/PhyRC_2027_phase1/blob/f17f5495259468ce2c9fc625b4eff145a28d27cf/docs/project/CODEX_CONTEXT.ko.md) |
| `docs/project/PRESENTATION.ko.md` | [고정 원문](https://github.com/leonyoon-3dai/PhyRC_2027_phase1/blob/f17f5495259468ce2c9fc625b4eff145a28d27cf/docs/project/PRESENTATION.ko.md) |
| `docs/project/RESEARCH_ROADMAP.ko.md` | [고정 원문](https://github.com/leonyoon-3dai/PhyRC_2027_phase1/blob/f17f5495259468ce2c9fc625b4eff145a28d27cf/docs/project/RESEARCH_ROADMAP.ko.md) |
| `docs/project/TODO.ko.md` | [고정 원문](https://github.com/leonyoon-3dai/PhyRC_2027_phase1/blob/f17f5495259468ce2c9fc625b4eff145a28d27cf/docs/project/TODO.ko.md) |
