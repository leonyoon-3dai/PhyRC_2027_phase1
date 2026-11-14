# E32 불완전 수집: 원본 표식을 유지한 진단 보존

`20261113-astra-central380-001`은 clean source `0421f8b3c45fd0291455fb278144ce279682dd98`에서 2026-11-13 23:59:34 UTC에 시작했다. 직접 parent/source group E28, prefix380·새 history264/332, `coordinated-central-span-entry`, 최대20결정/1400전이/review10이다. 실행 중 actor 입력·프롬프트·소스를 변경하지 않았다. [시작 기록](20261113-e32-start.ko.md).

20개 결정은 모두 act이며21호출(물리0인 질의 후속1회)을 사용했고 `finish_episode` 요청은 없다. accepted trace는756전이=380 replay+256 model+120 settle까지 완료됐다. 마지막 D19는744→750 회전과750→756 정착이다. collector stop1전이와 stdin EOF cleanup1전이를 합쳐 실제 파일은758전이다. 행동이 모두 기록됐다는 사실과 정상 마감은 별개다.

host 반환값은143이며 발신 원인은 미확정이다. attempt는 `collecting/controller_settle`, `finished=false`, simulation_steps756, simulator_returncode null에 남았다. capture는758전이·`complete=false`·`input_closed`이고 두 HDF5 root도 complete=false다. episode의 complete=true를 root/capture 완료로 대체하지 않았다. 실행 프로세스·GPU 사용이 멈춘 뒤 고아 actor egress만 정리했으며 원본은 수정하지 않았다. 실제 client의 최종 정상 종료 시각·반환값을 임의 생성하지 않는다.

전수 검사758/758에서 전이 내용과 episode 검사는 통과했지만 전체 `quality_passed=false`다. 오류는 정확히 `capture manifest is incomplete`, `policy HDF5 file is incomplete`, `audit HDF5 file is incomplete` 세 개다. [검사 JSON](20261114-e32-capture-validation.json). 기록된 별도 평가의 valid=true·raw5/50·pickup5·착의0·success=false, 새 득점0은 불완전 capture를 정상 replay 또는 학습 출처로 승인하지 않는다.5점은 E28 재실행371에서 얻었다.

| 원본 | bytes | SHA256 |
|---|---:|---|
| policy.hdf5 |1915009775|`8a0e9902d2fb28f8af6c01c56e4a4ca41f4568f9f888b2e3d08a5a1c1acbccd3`|
| audit.hdf5 |167198|`5a9435be1507e07a954f189beed14ae2c3d749a0359347784247bd937cc9bd4d`|

두 실제 해시는 capture 기록과 일치한다. 정상 `preserve_collection`/replay gate는 완화하지 않았다. 검토된 별도 로컬 helper는 허용된 원본·평가·accepted trace/prompt·기록된 소스·공개 관측233파일과 진단 scope1파일을 새 비공개 archive로 보존한다. 원시 CLI reasoning/events·인증·세션 DB·actor runtime·simulator.log는 공개/백업에서 제외한다. helper는 원격 기능이 없고 준비 단계의11개 합성 CPU 검사 및 독립 검토를 통과했다. archive 무결성과 원래 수집 QC는 별개다.

진단 archive의 로컬 pack은 완료했다.1,665,375,739bytes, SHA256 `eadd08aff5ab09a93828bf3f2177d28efcedde8d3a7f4d9d927cb62202a1889d`, manifest234members이며 원본 바이트·플래그를 재검사했다. private HF 고정 revision `91f91b06e39bb8257b8c888675b74d747261edd4`에서 강제 재다운로드·archive 크기/SHA·manifest SHA·234members·원본233파일 불변성을 검증했다. [진단 백업 receipt](20261114-e32-backup-verification.json). 검증된 것은 진단 archive의 무결성이며 capture 전체 QC는 여전히 실패다. 어떤 E32 경계도 정상 replay 후보로 승격하지 않는다.

[공개 리뷰](../../collection/reviews/20261113-astra-central380-001.ko.md)는 넓어진 후보402/414·운반 유지456–694·손 근처 접촉694–732·복구744를 구분한다. 실제 actor 마지막 관측은744이고, 정지한 파일의 지정 공개 RGB에서756/758도 진단 목적으로 검토했다. 첫 손 통과·연결 전완 진행은 확인하지 못했다. 정상 QC를 요구하는 결과 exporter를 우회해 정상 시연 영상으로 게시하지 않는다.

[결정·시간 분석](../../collection/reviews/20261113-decision-budget/E32/README.ko.md)은 actor1220.871470초·환경646.736852초(replay324.026041+새322.710811)를 분리한다. 최종 client 전체 경과는 미기록이며 collector wall1915.873023초로 대체하지 않는다. 마지막5개 판단은 접촉·좁아짐·복구 비교를 추가했지만 새 점수나 확인된 전완 진행은 없었다. 같은 마지막 상태의 예산 증액보다 유효한 접근 전 경계로 옮겨 판단을 정렬에 쓰는 계획을 우선한다.

다음 [E33 계획](20261114-e33-plan.ko.md)은 검증된 E28/632와 새 replay history588/614, 같은 중앙 전략·최대20결정이다. E32의 실패 자료를 보존하고 긴 운반보다 접촉 전 형상·같은 손 정렬에 예산을 쓸 계획이다. 아직 실행 결과가 아니다. [별도 process session launcher의 CPU 격리 검사](20261114-detached-launch-preparation.ko.md)는 실제 수집의 정상 종료 보장이 아니며 client/actor/simulator 정책·채점은 바꾸지 않는다. 이후 사용자 중지 요청을 받아 자동 반복을 중단했다. E33은 시작하지 않고 [클린 서버 인계](20261114-paused-clean-server-handoff.ko.md)를 보존하며 명시적 재개를 기다린다.
