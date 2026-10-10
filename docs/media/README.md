# paper-proofread 소개영상

30초 한국어 사용 예시. 로고는 1920px 화면에서 너비 144px로 줄이고, 실제 사용하는 터미널·요청·결과 파일에 화면을 배분했습니다.

Claude Code의 요청·응답과 교정 결과를 공개 규칙에 맞춰 재구성한 30초 사용 예시입니다. 실제 실행 녹화는 아닙니다.

화면 속 응답·파일 내용은 사용법 설명을 위한 작성 예시입니다. Claude Code를 실행해 얻은 산출물이나 성능 측정 결과로 제시하지 않습니다. 터미널·파일 뷰어의 배치는 가독성을 위해 편집했으며 실제 제품의 별도 GUI가 아닙니다.

## 영상 구성

| 구간 | 화면 | 읽을 내용 |
|---|---|---|
| 0–7초 | 원고와 함께, 고칠 범위를 말로 지정합니다 | 맞춤법만, 문장까지, 보수적으로 — 요청으로 범위를 정합니다. |
| 7–14초 | 어색한 표현을 원문과 나란히 확인합니다 | 문장 표현을 다듬고, 원문에 없는 연구 결과를 덧붙이지 않습니다. |
| 14–23초 | 어디를 왜 고쳤는지, 표로 남깁니다 | 섹션명·문단 번호로 원고에서 해당 위치를 바로 찾습니다. |
| 23–30초 | 수정 원고·교정표·요약을 함께 받습니다 | 수정한 문장을 읽고, 교정표에서 바뀐 이유를 확인합니다. |

## 파일·근거

- [MP4](intro.mp4): 1920×1080, 30fps, 30초, 무음 H.264
- [README GIF](intro-preview.gif): 같은 30초 전체, 960×540, 8fps
- [포스터](intro-poster.png) · [4개 장면](intro-storyboard.png)
- [대본·화면 데이터](intro.json) · [렌더러](render_intro.py)

기준 소스 커밋: `e15199dce1c538b8b736071432918c04e21d316c`. 영상 길이는 실제 처리시간을 뜻하지 않습니다.

- [SKILL.md](../../SKILL.md)
- [references/rules_ko.md](../../references/rules_ko.md)
- [examples/intro-manuscript.md](../../examples/intro-manuscript.md)

## 다시 만들기

Python 3.9+, Pillow, FFmpeg, 한국어 글꼴이 필요합니다. 이 의존성은 영상 재생성에만 쓰입니다.

```bash
python3 -m pip install Pillow
python3 docs/media/render_intro.py
# 정지 이미지 먼저 확인
python3 docs/media/render_intro.py --stills
```

기본 글꼴은 Pretendard이며 Apple SD Gothic Neo 또는 Noto Sans CJK를 대체로 사용합니다. `INTRO_FONT`, `INTRO_FONT_BOLD` 환경변수로 글꼴 경로를 지정할 수 있습니다. `intro.json`의 화면 문구를 바꾼 뒤 다시 렌더링하면 MP4·GIF·포스터·스토리보드를 갱신합니다. 원본 로고 PNG는 수정하지 않으며 렌더링 전에 체크섬을 확인합니다.
