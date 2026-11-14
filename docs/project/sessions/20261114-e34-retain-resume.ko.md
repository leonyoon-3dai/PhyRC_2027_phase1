# E34: E33의 마지막 새 파지를 유지하며 후속 시험

사용자의 기존 방식 추가 수집 요청에 따른 두 번째 시도다. [E33 리뷰](../../collection/reviews/20261114-astra-middle-grip264-001.ko.md)와 [고정 백업](20261114-e33-backup-verification.json)을 확인했다. E33은0/50·20결정·471전이·QC통과였으며 마지막 robot1 닫기 뒤 들기 시험이 남았다.

- run: `20261114-astra-middle-grip470-retain-001`
- 직접 parent: E33 `20261114-astra-middle-grip264-001`; source group: E28 `20261113-astra-side-hem-fresh-001`
- prefix470 / 새 replay history434·454; 정확한 천 checkpoint가 아니다.
- `coordinated-middle-grip-drape-retain`, 새20결정/총1400/review10, Codex0.166.0/exec/gpt-6-astra/ultra, named·pixel query·wrist panel·plan1, motion-only settle6·timeout180·시간계측.
- 이전 파지 위치 변경 목표와 위에서 내려 걸치기를 유지하면서 추가 재파지0을 지시한다. 정적 프롬프트 제약이며 런타임 자동 차단·누적 상태기계 구현이 아니다. 공개 관측·스키마·물리·평가기는 유지한다.
- 정상 close·전수 QC·별도 평가·영상·고정 백업 후 추가 결정의 효용을 판단했다. 실제 결과는 아래 마감 기록을 따른다.

실행 조건 정본은 [COLLECTION_PLAN](../../COLLECTION_PLAN.md#다음-e34-실행-조건)이며 [CPU 분기 계획](../../collection/retry-plans/20261114-e34-e33-470-retain.json)을 보존한다.

변경 후 전체 CPU356개 검사가41.562초에 통과했다. 기존 전략의 동작 동등성, 새 선택지의 프롬프트/hash, exec/plan1 제한, 질의·정착 경로를 확인했다. 합성 open 응답이 기존 스키마를 통과하는 검사도 있어 이 제약이 hard gate가 아님을 명시적으로 유지한다.

## 진행 중 사용자 범위 변경

현재 E34까지만 진행한 뒤 수집을 중지하도록 요청했다. E35 계획은 취소한다. E34 마감·QC·보존·분석 후 전체 시연 경험과 agentic robotics 연구에 근거한 수집 시스템 재정비 계획을 작성한다. 새 수집이나 시스템 개편 구현은 시작하지 않는다.

## 실행·마감 검증

- source `0a5121cde33a32db5e4888255de150e846d52c15`, 시작 시 clean. 실행 중 코드·프롬프트는 변경하지 않았다.
- client 시작 `2026-11-14T08:41:36Z`, 종료 `2026-11-14T09:14:16Z`. detached supervisor/client는 별도 session이고 client와 simulator 반환값은 모두0이다.
-20 act·24모델 호출.836전이=470 replay+245 model+120 settle+1 budget cleanup.20결정 예산으로 정상 종료했고 `completed/closed/finished=true`, capture complete=true다.
- 전수 QC836/836·오류0. 로컬 공식 평가기 valid=true, **5/50·픽업5·착의0·success=false**. pickup은 replay prefix 이후 부여됐지만 입구·첫 소매 통과를 뜻하지 않는다. 학습 승인은 `unreviewed`다.
- client 내부 wall1959.323초(32.66분), actor1170.153초, 환경737.509초. 환경 중 replay418.908초, 새 model209.558초+settle109.043초다. actor+새 환경은1488.754초(24.81분)이며 전체 경과와 구분한다. 별도 launcher wall1960.331초다.
- 공개 usage는24호출의 thread cumulative를 증분 정산한 합이다: input3,103,736, 그중 cached2,510,080; output34,065, 그중 reasoning28,291. 부분집합을 다시 더하거나 각 호출의 누적 수치를 모두 합산하지 않는다. 금액·모델 내부 추론 시간은 이 값에서 추정하지 않는다.
- [전체836프레임 영상](../../collection/attempts/20261114-astra-middle-grip470-retain-001/overview.mp4), [공개 manifest](../../collection/attempts/20261114-astra-middle-grip470-retain-001/manifest.json), [시각 리뷰](../../collection/reviews/20261114-astra-middle-grip470-retain-001.ko.md), [고정 백업 receipt](20261114-e34-backup-verification.json).
- 고정 private HF revision `ba71dd6a07e2b05202c3dcaa5b0c9a3c17997b1d`, archive1,910,237,869bytes, SHA `ccd01e7a41b72dcb03b055e834c7f2e4404dc7b50d8a84647b2e6d956bd0620b`. 강제 재다운로드·236개 manifest 항목·원본234파일 불변 검증을09:18:02 UTC에 완료했다. 실행 중 Docker 컨테이너는 없으며 후속 수집을 시작하지 않았다.

E33의 마지막 파지를 유지한 후 천을 들고 운반해 같은 손 부근에서 정렬·짧은 하강까지 시도했다. D18의815→825(정착 포함)에서 양쪽 lift는 약16mm 낮아졌고, D19의825→835는 약36–37mm의 base 측면 이동이다.20개 새 행동의 gripper는 모두+1이고 HDF5 새 구간에는0/+1만 있어 open 명령은 없었다. 이는 지시 준수이며 천 부착의 인증은 아니다. E33 준비가 전부 무용했다고 해석할 수 없지만, 유효 입구·손목 걸침·전완 진행은 확인되지 않았다. E33→E34를 파지 유지 기능의 통제된 성능 비교로 해석하지 않는다. 새 replay·출발 경계·이전 준비 누적의 차이가 있다.

현재 후속 수집은 중지다. E35·추가 GPU 실행·학습·연구 기능 통합은 수행하지 않는다. [전체 경험 기반 재정비 계획](../../collection/research/2026-11-14-collection-system-redesign.ko.md)을 다음 개발 판단의 기준으로 보존한다.
