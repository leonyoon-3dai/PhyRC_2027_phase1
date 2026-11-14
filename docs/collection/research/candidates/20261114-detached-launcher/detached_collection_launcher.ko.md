# 별도 세션 실행기 후보 — 로컬 전용

`detached_collection_launcher.py`는 검토된 기존 수집 명령 `.sh`를 별도 supervisor와 client 세션에서 실행하고 실제 PID/PGID/SID·시작·종료 코드를 저장한다. 현재 기본값은 dry-run이다. 배우·collector·물리 코드, 모델, 예산과 원래 명령 파일 내용은 바꾸지 않는다.

저장소 루트에서 준비된 새 명령 파일을 지정한다.

```bash
.venv/bin/python output/sessions/20261113-setup/detached_collection_launcher.py \
  --run-id NEW_RUN --job-id UNIQUE_JOB \
  --script output/sessions/20261113-setup/NEXT-command.sh
```

실제 실행은 같은 인수에 `--execute`를 붙인다. 이 문서 작성 시 실제 수집은 실행하지 않았다. parent가 명령 파일과 run ID를 대조하고 이전 GPU/collector가 끝났는지 확인한 뒤 사용하는 로컬 도우미다.

출력은 `output/sessions/20261113-setup/detached-UNIQUE_JOB/`에 생긴다. 폴더0700·파일0600으로 만들고 환경 변수 값이나 인증 내용을 JSON에 저장하지 않는다.

- `launch.json`: 검토 대상 명령 파일과 실행기 SHA256, 요청된 run/job, 고정 stdin/출력 설정.
- `launcher-receipt.json`: supervisor 생성 접수. **이 단계는 client 시작·수집 완료의 확인이 아니다.**
- `status.json`: supervisor와 실제 client PID/PGID/SID, `running` 또는 `exited`, 실제 `client_returncode`와 관측 종료 시각. 음수 코드는 직접 관측한 signal 종료이며 별도 shell-style 숫자도 보존한다.
- `client.log`, `supervisor.log`: 비공개 진단 출력. 자동 게시·수집 archive 포함 대상으로 추가하지 않는다.
- `worker.claim`: 동일 supervisor를 중복 실행해 이전 종료 receipt를 덮어쓰지 않도록 하는 일회성 표식.

부모 도구 호출에서 supervisor를 `Popen(start_new_session=True, stdin=DEVNULL)`로 만들고, supervisor도 동일 설정으로 실제 bash/client를 시작한다. stdout은 위 비공개 파일, stderr는 stdout으로 합친다. client가 자체적으로 여는 collector stdin pipe는 기존 코드대로 유지된다. supervisor는 실제 client 종료를 기다려 기록하며 수집 프로세스에 signal을 전달하지 않는다.

기존 job이나 동일 run의 trace/collection/actor 경로가 있으면 자동 재실행하지 않는다. 명령 파일이 접수 뒤 바뀌면 client 시작을 거부한다. 실행기/명령 파일을 실행 중 교체하지 않는다. `status.json`이 running이어도 supervisor가 사라졌을 수 있으므로 실제 프로세스와 capture 상태를 따로 확인한다. `exited` 또는 exit0만으로 capture complete/QC를 주장하지 않는다.

CPU 합성 검사9개가 통과했다. 새로운 합성 부모 process group만 SIGTERM으로 종료한 뒤 별도 세션의 합성 자식이 완료되고 실제 exit7이 기록되는 것을 확인했다. 기본 dry-run 무실행, 기존 job/run 거부, 중복 worker의 receipt 보존, 접수 뒤 바뀐 명령 파일의 hash 불일치로 child 생성 전 거부도 확인했다. `test_detached_collection_launcher.py`와 `detached_collection_launcher.preparation.json`에 근거를 남겼다.

**이 검사는 POSIX process-group 분리만 확인한다.** host·cgroup·도구의 전체 작업 정리에서도 살아남는다는 보장은 없고, 이전143의 원인은 미확정이다. 실제 GPU·모델 수집으로 검증하지 않았다. E32 원본의 incomplete 표시와 정상 보존/재실행 gate는 그대로 유지한다.
