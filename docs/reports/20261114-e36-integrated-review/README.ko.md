# E00–E36 통합 분석 보고서

**[18장 슬라이드 PDF 열기](phyrc-e36-integrated-review.ko.pdf)** · [텍스트 동반본](report.ko.md) · [최신 E36 GIF](../../gallery/20261114-e36-overview/README.ko.md)

2026-11-14 E36 마감 기준. 사용자 관찰과 제안, Codex가 검토한 실행·관측·데이터 근거, 관련 연구의 주장과 적용 후보를 구분해 통합했다. E36으로 수집을 종료했으며 E37 이후는 실행하지 않았다. 새 키보드 연결·텍스트 개입·직접 제어권 전환·학습을 완료한 보고서가 아니다.

## 검토 범위

- E00–E34는 보존된 리뷰·계보·코드를 종합했다. 모든 과거 원본 영상을 이번에 전수 재시청한 것은 아니다.
- E35/E36은 지정 공개 관측·실제 적용 행동·로봇 상태, 별도 공식 평가·전수 QC·고정 백업 결과를 확인했다. 평가·내부 기하를 actor 입력이나 교사 정답에 넣지 않았다.
- 연구 4편의 고정 버전 초록·관련 본문을 확인했다. 코드·실험 재현이나 PhyRC 성능 개선을 검증한 것은 아니다. [원문과 확인 범위](research-sources.json).
- 7쪽 시작 이미지는 환경 reset 사진이 아니라 **E36의 새 replay 경계835, 공개 `next_obs[834]`**다. 원본 픽셀과 추출 출처는 [이미지 provenance](assets/provenance.json)에 있다. 로봇별 표시는 왼쪽 robot_1, 오른쪽 robot_0이며 픽셀 반전은 없다.
- raw5/50과 공식 rate `final_score=0`은 다른 값이다. E35/E36의 pickup5는 각 replay 구간에서 얻었고 새 착의점은0이다. 기술 QC는 학습 승인이 아니며 현재 `unreviewed`다.

## 파일과 검증

[수치·출처 입력](report-data.json), [PDF·소스 해시](provenance.json), [자동 검증 결과](validation.json)를 함께 보존한다. 18개 페이지를 모두 렌더링하고 한글 추출, 폰트 glyph, 페이지 밖 텍스트, 음수 측정값, 링크와 근거 파일 해시를 검사한다. 코드 검사만으로 시각 내용의 정확성이나 천의 통과를 인증하지 않는다.

제작 중 독립 검토에서 초기 이미지의 시간 경계와 음수 glyph 문제를 찾아 고쳤다. 최종 내용은 실제835 이미지, ASCII 음수 부호, base yaw 명령0의 수행 한계, 미구현 기능과 조건부 시간 추정을 포함한다. 렌더 이미지는 ignored `output/report-validation/20261114-e36/`에 둔다.

## 재생성

보고서 전용 환경을 사용한다. 수집용 `.venv`의 고정 라이브러리를 바꾸지 않는다.

```bash
sudo apt-get install -y fonts-nanum
python3 -m venv .runtime/report-venv
.runtime/report-venv/bin/pip install -r docs/reports/20261114-e36-integrated-review/requirements.txt
.runtime/report-venv/bin/python docs/reports/20261114-e36-integrated-review/build_report.py
.runtime/report-venv/bin/python docs/reports/20261114-e36-integrated-review/validate_report.py
```

필요한 이미지는 공개 저장소에 포함돼 있어 비공개 HDF5 없이 PDF를 재생성할 수 있다. 이미지를 다시 추출하려면 별도 권한이 있는 원본과 검증된 SHA가 필요하다. 생성기는 simulator·actor를 실행하거나 원본 manifest/MP4/HDF5를 수정하지 않는다. NanumGothic/NanumGothicBold는 NAVER의 SIL Open Font License 글꼴이며 PDF에 사용 glyph subset을 포함했다.
