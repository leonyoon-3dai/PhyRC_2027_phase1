# 별도 세션 실행기 준비 검토

기존 수집 명령을 별도 supervisor/client 세션에서 실행하고 실제 시작·종료 상태를 남기는 **로컬 실행기 후보**를 준비했다. Root가 전체 소스를 읽어 차단 이슈가 없음을 확인했고, CPU 합성 검사9개를 통과했다. 준비 검증 당시 실제 GPU·모델 수집은 시작하지 않았다. [검증 receipt](20261114-detached-launch-preparation.json)

로컬 파일은 `output/sessions/20261113-setup/detached_collection_launcher.py`다. 정확한 SHA256은 `3ce0a697d6187de0e4eef83cb37e375f00170f738f297175b898d7c3cb5280f3`이다. 배우·모델·collector·시뮬레이터·물리·평가 코드와 기존 capture/attempt는 바꾸지 않았다.

기본 실행은 dry-run이며 파일이나 프로세스를 만들지 않는다. 실행 담당자는 검토된 명령 파일과 새 run ID를 대조하고 이전 수집 프로세스가 종료됐는지 확인한 뒤 `--execute`를 사용한다. 접수 뒤 명령 파일 해시가 바뀌거나 동일 job/run의 자료가 있으면 재실행을 거부한다. 자동 재시도나 기존 자료 덮어쓰기는 하지 않는다.

Supervisor와 실제 client를 각각 `start_new_session=True`, stdin `DEVNULL`, 비공개 stdout/stderr 파일로 시작한다. 기존 client가 collector와 통신할 때 사용하는 별도 stdin pipe는 유지된다. 접수 receipt는 client 시작이나 수집 완료의 확인이 아니다. 별도 상태 기록에서 실제 client PID/PGID/SID와 종료 코드를 확인하고, 그 뒤 capture 완료·전수QC·보존 검증을 따로 수행한다. 원시 로그·환경 값·인증 내용·실제 프로세스 식별자는 공개 receipt에 넣지 않았다.

CPU 검사에서는 새로 만든 합성 부모 process group에만 SIGTERM을 보내고, 분리된 합성 작업이 완료되어 실제 exit7을 남기는 것을 확인했다. 기본 dry-run 무실행, 기존 job/run 거부, 중복 worker의 종료 receipt 보존, 명령 파일 변경 시 child 생성 전 거부도 통과했다.

**검증 범위는 POSIX process-group 분리다.** Host·cgroup·실행 도구가 전체 작업을 정리하는 경우의 생존을 보장하지 않으며, 이전143의 원인도 아직 미확정이다. Supervisor가 사라지면 running 상태 기록이 오래 남을 수 있으므로 실제 프로세스를 별도로 확인해야 한다. Exit0만으로 정상 캡처를 인증하거나 E32의 incomplete 표시를 변경하지 않는다. 실제 적용과 결과는 후속 실행 기록에 남긴다.

사용자 중지 후 [원본·검사·사용 설명을 미적용 인계 artifact](../../collection/research/candidates/20261114-detached-launcher/README.ko.md)로 보존했다. 원본 해시는 동일하며 게시 후에도 실제 수집을 실행하지 않았다.
