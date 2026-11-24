# 11월 22–23일 착의 시연 기록

세 회차는 같은 시드 43, 테이블 인덱스 2, 셔츠–마네킹 마찰 0.35에서 각각 새로 시작했다. 같은 초기 배치를 다시 사용한 비교이며, 원점수는 회차별 로컬 공식 평가기의 누적값이다. 이 문서의 영상 링크는 당시 운영 서버 주소다. 새 서버에서는 갤러리를 복원하고 링크 끝의 실행 ID와 구간 번호로 같은 영상을 연다. [여섯 회차 갤러리 복원](start.md)

| 시연 | 실행 ID | 기록 |
|---|---|---|
| 1 · 사용자 피드백 | `20261122T231754Z-astra62-dressing` | 1655전이 · 77구간 · **5/50**, 착의 성공 false. [마지막 구간](https://jupyter-fjy7731zk.gobrev.dev/view/PhyRC-gallery/20261122T231754Z-astra62-dressing/hold-0077.html) |
| 2 · GPT 단독, 한 팔과 얼굴 먼저 | `20261123T032900Z-astra62-autonomous` | 2195전이 · 110구간 · **20/50**, 착의 성공 false. 사용자 개입 1회는 종료 요청이었다. [종료 구간](https://jupyter-fjy7731zk.gobrev.dev/view/PhyRC-gallery/20261123T032900Z-astra62-autonomous/hold-0110.html) |
| 3 · GPT 단독, 양팔 먼저 | `20261123T061400Z-astra62-both-arms-first` | 608전이 · 30구간 · **5/50**, 착의 성공 false. 202전이에 픽업. 이후 양팔 걸침을 재시도했고, 종료 요청에서만 사용자가 개입했다. [첫 관측](https://jupyter-fjy7731zk.gobrev.dev/view/PhyRC-gallery/20261123T061400Z-astra62-both-arms-first/hold-0001.html) |

**세 회차 합계**는 4,458전이(물리 시간 222.9초), 217구간, 모델 판단 499회다. 클립은 HOLD 경계에서 나눈 같은 회차의 연속 구간이다. 수집기 벽시계 시간은 회차별 약 3시간 58분, 2시간 46분, 49분이며 합계 약 7시간 33분이다. 앞선 3전이 연결 점검은 기술 확인용으로 따로 기록했다. [전체 GIF 3편](../../README.md) · [복구 사례](20261123-recovery-review.ko.md) · [다음 클린 서버 인계](20261124-handoff.ko.md)

## 1 · 양끝을 잡고 손 앞에 접근

630전이에 픽업 5점을 얻었다. 양 집게가 천을 들고 손 앞까지 갔지만 손목을 돌려도 노란 테두리 두 겹이 충분히 벌어지는 모습을 확인하기 어려웠다. 이후 시연에서는 테이블이 천을 받치고 있을 때 각 파지를 따로 시험하고, 운반 전 두 테두리 사이의 공간을 측면과 손목 깊이 영상으로 확인한다. [구간별 원인 분석과 공식 영상 비교](guided-retrospective.json)

## 2 · 한 팔과 얼굴까지 올라간 구간의 점수

| 전이 | 이번에 인정된 항목 | 누적 | 검토 구간 |
|---:|---|---:|---|
| 161 | 픽업 +5 | 5/50 | [픽업](https://jupyter-fjy7731zk.gobrev.dev/view/PhyRC-gallery/20261123T032900Z-astra62-autonomous/hold-0007.html) |
| 661 | 마네킹 왼손이 첫 소매를 통과 +5, 반대쪽 어깨 +5 | 15/50 | [632–664전이](https://jupyter-fjy7731zk.gobrev.dev/view/PhyRC-gallery/20261123T032900Z-astra62-autonomous/hold-0026.html) |
| 698 | 왼쪽 위팔에 소매가 걸림 +5 | **20/50** | [676–710전이 · 정수리가 보이는 장면](https://jupyter-fjy7731zk.gobrev.dev/view/PhyRC-gallery/20261123T032900Z-astra62-autonomous/hold-0028.html) |
| 2195 · 종료 | 이후 추가 득점 없음 | **20/50** | [마지막 관측](https://jupyter-fjy7731zk.gobrev.dev/view/PhyRC-gallery/20261123T032900Z-astra62-autonomous/hold-0110.html) |

**목 0/10, 두 번째 소매 0/5, 오른쪽 위팔 0/5, 앞면 방향 0/10.** 천이 얼굴과 정수리를 덮는 장면이 있었으나 공식 평가기는 목둘레를 통한 머리·목 통과를 인정하지 않았다. 왼쪽 위팔 점수는 698전이에 얻었고 최종 프레임에서는 왼쪽 위팔이 해당 소매 안에 자리잡은 상태가 풀렸다. 속도 점수 0.8753점/초는 픽업을 제외한 15점을 공식 접촉–마지막 득점 시간 17.1375초로 나눈 값이다.

| 구간에서 확인한 현상 | 3회차에 반영한 조작 |
|---|---|
| 1747–1773전이에 파란 소매 가장자리가 반대 손 옆에 남았고 손끝은 가려졌다. 1922–1943전이에는 파란 천이 그 손을 덮었지만 해당 소매로 손끝이 빠져나온 장면은 확인하기 어려웠다. [두 번째 손과 입구](https://jupyter-fjy7731zk.gobrev.dev/view/PhyRC-gallery/20261123T032900Z-astra62-autonomous/hold-0090.html) · [소매 재시도](https://jupyter-fjy7731zk.gobrev.dev/view/PhyRC-gallery/20261123T032900Z-astra62-autonomous/hold-0100.html) | 양팔에 한쪽씩 먼저 걸친 뒤 두 지점이 함께 유지되는지 본다. 머리가 나온 뒤 각 손목과 손끝이 올바른 소매 출구 밖에 드러나는지 다시 확인한다. |
| 2111–2138전이에 R1 집게가 약 5.3cm 올라갔지만 주로 파란 모서리가 움직였고 정수리 쪽 트임은 거의 움직이지 않았다. [목둘레와 주름의 움직임](https://jupyter-fjy7731zk.gobrev.dev/view/PhyRC-gallery/20261123T032900Z-astra62-autonomous/hold-0108.html) | 목둘레의 테두리가 실제로 이동하는지 확인한다. 얼굴이 가려지거나 가장자리만 움직이면 한쪽 지지를 유지하고 장력 또는 파지 위치를 바꾼다. |

## 3 · 양팔에 먼저 걸친 시도

공식 전후면 영상에서 약 19.5–24초에는 열린 옷이 양손 앞으로 이동하고, 약 26–30초에는 머리 쪽으로 올라간다. 약 32–34초에는 양팔이 서로 다른 소매 너머에 보이고, 마지막 35.7초에는 얼굴이 드러나며 밑단이 몸통 아래로 내려온다. 천이 손·머리를 가리는 동안의 정확한 통과 시점은 판별하기 어렵다. 세 번째 시연에서 이 순서를 시험했다. [공식 전체 영상](https://emprise.cs.cornell.edu/phyrc/assets/c27/media/teleop-overhead.mp4) · [공식 전후면 영상](https://github.com/rirolab/PhyRC_2027_Challenge/blob/9afd513e926a82f1866a4b870135e33faba1358e/docs/videos/Front_Back_8x.mp4)

281–301전이에는 천이 양쪽 전완에 걸쳐 보였지만 한쪽 손목이 가려졌다. 301–313전이에 양 집게가 어깨 쪽으로 각각 약 18·17cm 움직인 뒤 노출된 손목이 천 위에 다시 보였다. 503–521전이와 558–576전이에도 한쪽 손이 몸판 위에 남았다. 종료 직전에는 R1이 지지한 채 R0이 파란 주름을 놓아 노란 가장자리가 보였다. 재파지는 후속 가설로 남았다. 202전이의 픽업 외에 추가 점수는 없었다. [구간별 실패 사례](20261123-recovery-review.ko.md) · [시연 3 당시 프롬프트](https://github.com/leonyoon-3dai/PhyRC_2027_phase1/blob/4741c844839845e5237016a420828747a9bad5b5/participant/collection/prompts/autonomous_full_dressing.txt)

## 검증과 비공개 보관

세 시연은 각 HDF5의 1655/1655, 2195/2195, 608/608전이가 기술 검증을 통과했고, 각 최종 `result.json`의 `valid`는 true다. 모두 학습용 승인 상태는 `unreviewed`이다. 두 번째 시연의 원본은 110개 구간의 행동 묶음 220건을 HDF5와 대조했고, 판단 시점의 RGB-D 관측 221세트를 확인했다. 운영 서버에서 확인할 상대 경로는 다음과 같다.

| 자료 | 위치 |
|---|---|
| 항목별 최초 득점과 최종 결과 | `output/collections/RUN/evaluation/<episode>/score_events.jsonl`, `result.json` |
| 전수 검증과 훈련 승인 상태 | `output/collections/RUN/validation.json` |
| 행동·관측과 검증된 보존 파일 목록 | `output/preservation/RUN-final.receipt.json` |
| 구간 영상·분석·종료 기록 | `output/review-exports/RUN.zip` |

## 지난 구간을 새 서버에서 열기

[비공개 백업 확인서](20261123-private-backup.json)의 고정 revision에 회차별 HDF5 원본, 공개 카메라 프레임, 구간별 MP4·분석 ZIP, 갤러리 저널이 있다. 백업에 접근할 수 있는 Hugging Face 계정으로 인증한 **운영자가 새 서버의 첫 수집을 시작하기 전** 아래 한 줄을 실행하면, 3개 구간 ZIP과 저널만 받아 217개 MP4를 복원한다. 사용자 브라우저에는 새 서버의 Brev 주소만 필요하다. 이번 백업 복원에 사용한 CLI는 huggingface-hub 2.4.0이다. 새 서버에 CLI가 없으면 운영자가 `uv tool install huggingface-hub==2.4.0`으로 준비하고, 필요한 경우 `hf auth login`으로 해당 비공개 데이터셋 접근 권한을 연결한다.

```bash
.venv/bin/python scripts/restore_review_gallery.py --receipt docs/active/20261123-private-backup.json
```

복원기는 백업 파일과 각 클립의 SHA-256을 대조한다. 기본 대상은 새 `output/segment-review`이다. 이미 수집한 저널이 있으면 다른 빈 경로를 `--destination`으로 지정하고 그 경로로 별도의 검토 갤러리를 연다. 내려받은 고정 스냅샷은 `--download-root`로 사용할 수 있다. 새 서버에서 이 문서의 Brev 구간 링크를 열 때는 호스트를 새 인스턴스로 바꾸면 `/view/PhyRC-gallery/<run>/<hold>.html` 경로가 그대로 연결된다.

원본 분석에 필요한 HDF5·행동 로그·평가 결과는 확인서에서 해당 회차의 `archive.path`를 골라 같은 revision에서 받는다. SHA-256을 확인한 다음 `.venv/bin/python -m participant.ops.artifacts restore 새_복원_디렉터리 --archive 받은_파일.tar.gz`를 실행하면 내부 파일 목록과 해시까지 검증한다. 원본 아카이브 세 개 모두 별도 디렉터리에 복원해 검증했다. 전체 백업은 10개 파일, 11.11 GB이며, 새 서버의 갤러리에는 이 중 저널 1개와 구간 ZIP 3개만 필요하다.
