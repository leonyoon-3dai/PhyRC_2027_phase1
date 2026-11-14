# 별도 세션 실행기 · 미적용 인계 artifact

사용자가 시연을 중지하고 나중에 클린 서버에서 다시 시작하도록 요청해, 이미 검토·합성 CPU 검사한 로컬 후보를 그대로 보존한다. **현재 실행하지 않으며 실제 GPU/모델 수집에는 아직 적용하지 않았다.** 게시가 actor/simulator 통합이나 재개 승인을 뜻하지 않는다.

- [실행기 원본](detached_collection_launcher.py.txt)
- [9개 합성 CPU 검사 원본](test_detached_collection_launcher.py.txt)
- [당시 로컬 사용 설명 원본](detached_collection_launcher.ko.md)
- [당시 준비 검증 receipt](detached_collection_launcher.preparation.json)

4개 파일은 무시된 로컬 원본과 byte-identical이다. Python source/test 사본만 `.py.txt` 확장자로 게시해 자동 테스트 탐색·import를 막는다. 원래 이름은 해당 파일명에서 마지막 `.txt`를 뺀 이름이다. 명시적 재개 뒤 무시된 로컬 output 경로에 원래 `.py` 이름으로 복사하기 전에는 실행용으로 취급하지 않는다. 아래 SHA는 원본 복사 일치를 확인한 기록이며 새 서버 실행·실제 수집 성공의 검증이 아니다. 사용 설명의 output 경로는 당시 로컬 배치다. 새 서버에서 명시적으로 재개한 뒤 원래 `output/sessions/20261113-setup/` 경로로 복사하고 인접한 테스트 파일과 실행기 이름을 유지해 검토한다. 실행기의 기본 root 계산은 원래 깊이에 의존하므로 docs artifact 위치에서 직접 실행하지 않는다. 다른 위치를 쓰려면 `--root`에 저장소 절대 경로를 명시하고 검토한다. 새 서버에 맞는 명령 파일과 고유 job을 새로 준비해야 한다. 기존 run/job/명령을 덮어쓰거나 자동 실행하지 않는다.

```json
{
  "detached_collection_launcher.py.txt": "3ce0a697d6187de0e4eef83cb37e375f00170f738f297175b898d7c3cb5280f3",
  "test_detached_collection_launcher.py.txt": "12b21fd564ec5b6d84497334052249442b4be63566d95d94002a038974e5b25f",
  "detached_collection_launcher.ko.md": "2108526058797dcc7dff7d7e061eb9f5f93197d2c603c39524dcba321e6fe6a3",
  "detached_collection_launcher.preparation.json": "52044279636d0d1d4ae69496f2bd8daf7b9ef0fffbb7c53a080dcc77401d0be9"
}
```

실행기 기본값은 dry-run이고 실제 실행에는 별도 명시적 인수가 필요하다. 검증 범위는 POSIX process-group 분리이며 host/cgroup 종료 생존과 이전143 원인을 해결했다고 주장하지 않는다. capture 완료·전수 QC·백업은 별도로 확인한다. 원시 실행 로그·PID·환경·인증 자료는 이 artifact에 없다.
