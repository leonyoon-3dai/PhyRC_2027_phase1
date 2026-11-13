# 2026-11-13 클린 서버 준비와 수집 재개 검사

사용자가 HF CLI 설치와 수집 재개를 요청했습니다. **고정 자산 복원, 환경 준비, CPU 335개 검사와 실제 GPU smoke를 통과했습니다.** 작은 연결 시험 `20261113-codex-wiring-001`도 정상 종료했고, **3/3전이 전수 QC를 통과**했습니다. E28 착의 시연이나 추가 득점의 완료 기록이 아닙니다. [검증 receipt](20261113-environment-setup.json).

## 확인한 환경

- L40S 46,068 MiB, NVIDIA 드라이버 580.126.09, Docker 29.1.5, NVIDIA Container Toolkit 1.20.1. 기본 Docker 실행과 컨테이너 GPU 인식, `run.sh doctor`를 확인했습니다.
- Python 3.12.16, numpy 1.26.4, h5py 3.12.1, Pillow 11.0.0, psutil 6.1.1. HF CLI 2.4.0을 설치하고 사용자의 HF 로그인을 확인했습니다.
- Node 20.20.2/npm 10.8.2를 유지하고 Codex CLI 0.166.0을 별도 로컬 경로에 설치했습니다. ChatGPT 로그인과 native 실행 파일·버전 검사를 확인했습니다. `exec / gpt-6-astra / ultra` 경로를 유지합니다.
- 실제 actor 격리 Docker·네트워크 준비 검사에는 모델 호출이 없었습니다. 검사 후 전용 인증 사본과 임시 컨테이너·네트워크를 정리했습니다. 로그인·준비 검사와 실제 모델 접근·행동 성능을 구분합니다.

초기 clone은 `df1e3da2b34f035d982d8381b397a46c40c0dda5`, 이 기록 작성 시 HEAD는 `6730e07f892ff0c227154d93e704b5428d596b4f`입니다. 이 HEAD를 별도 보존되지 않은 검사 시점 소스 스냅샷으로 주장하지 않습니다.

## 복원과 실제 검사

[초기 비공개 백업 receipt](20261106-remote-backup-verification.json)의 고정 revision `e1d32f9f9ea82438f90bc379452abf83a150999b`에서 **11,779,782,360 bytes** archive를 받았습니다. 크기·SHA256·내부 manifest를 검사하고 `assets/`·`output/`의 **5,166개 파일**을 검증했습니다. 기존 파일과 충돌하면 중단하며 누락 파일만 추가했습니다. 핵심 custom 자산은 이미 Git에 포함되어 있었고, 최종 asset lock의 8개 항목을 모두 확인했습니다. 이 복원 자체는 물리 replay나 천 상태 checkpoint 복원이 아닙니다.

고정 Isaac Sim 6.0.1 digest로 `build`를 완료했고, `prepare` 종료 코드 0을 확인했습니다. `smoke`는 **종료 코드 0과 `PHYRC-SMOKE-PASS`를 모두 확인**했습니다. CPU 전체 unittest는 **335개, 45.829초, OK**입니다. 이미지·자산 잠금·검사 로그의 해시는 receipt에 남기고 원시 simulator 로그와 내부 장면 값은 공개 문서에 복사하지 않습니다.

## 연결 시험과 다음 수집

연결 시험은 host·simulator 종료 코드 0, `completed`·`closed`·`finished=true`로 마감했습니다. 모델 호출 3회, 결정 3개, 기록 3전이이며 전수 QC는 오류 0·`quality_passed=true`입니다. client 전체 경과는 61.701초, actor 호출 합계는 18.009초입니다. 연결 시험의 로컬 평가기는 0점·착의 성공 false이며 학습 승인은 `unreviewed`입니다. 이 검사는 실제 모델·시뮬레이터 연결을 확인한 것이며 옷입히기 시연은 아닙니다.

닫힌 wiring 원본은 비공개 백업의 고정 revision `7edc9d787c923e60eaea95e9ee02f3100ea1d238`에서 재다운로드하여 archive 크기·SHA256과 **62개 member**를 검증했습니다. [Wiring 백업 receipt](20261113-wiring-backup-verification.json).

현재 구현한 측면 파지·밑단 펼침·첫 손목 유지 전략과 분기 기준은 [수집 계획](../../COLLECTION_PLAN.md)에 둡니다. 연결 검사 후 E28 `20261113-astra-side-hem-fresh-001`을 소스 `9f79772`의 새 reset에서 시작했으며, 현재 수집 중이고 최종 결과는 미확정입니다. 기존 prefix 재실행과 새 행동·정착·종료 구간을 분리하고, 마감 원본과 실패 근거를 보존합니다.

검증된 과거 최고 기록은 **5/50점, 착의 득점 0, success=false**입니다. 환경 준비·CPU 검사·GPU smoke 통과는 착의 성공이나 추가 점수 획득을 뜻하지 않습니다. 장비 비교 질문은 [GPU 비용 분석](../../collection/research/2026-11-13-gpu-rollout-cost.ko.md)에 별도로 기록했으며, 그 분석을 위한 인스턴스 변경·비교 벤치마크는 수행하지 않았습니다.
