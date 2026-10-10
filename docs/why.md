# 왜 만들었나 · 상세 사용법

**한국어** · [English](#english)

README에서 덜어낸 배경과 사용 시나리오를 여기 둡니다.

---

## 왜 만들었나

원고를 넘기기 전에 문장을 마지막으로 한 번 훑는 일은 늘 사람 몫이었습니다. 그런데 이 작업은 도구들 사이의 틈에 떨어져 있습니다.

한국어 학술 문장에는 고유한 실패 유형이 있습니다.

- **이중피동** — "분석되어지고 있다". '되다'로 이미 피동인데 '-어지다'를 한 번 더 붙였습니다. 규범 위반인데도 학술 문장에 워낙 흔해서, 읽으면서 걸리지 않습니다.
- **번역투** — "연구에 있어서", "~하는 것이 가능하다", "~로 사료된다", "~가 행해졌다". 문법적으로 틀린 데가 없으니 맞춤법 검사기는 그냥 통과시킵니다. 다만 문장이 길어지고 주장이 흐려집니다.
- **주술 불일치** — 한국어는 서술어가 맨 뒤에 오고, 그 앞에 수식절을 얼마든지 쌓을 수 있습니다. 명사구를 겹겹이 얹다 보면 주어와 서술어가 멀어져 호응이 깨지는데, 무슨 말을 하려 했는지 아는 저자 본인이 가장 못 봅니다.
- **띄어쓰기의 회색지대** — "읽어 보다"와 "읽어보다"는 둘 다 맞습니다. 여기서 정답은 둘 중 하나가 아니라 "원고 안에서 하나로 통일되어 있는가"입니다. 한쪽을 틀렸다고 표시하는 검사기는 도움이 안 됩니다.

영어권 교정 도구는 이 유형들을 개념 자체로 갖고 있지 않습니다. 자기 언어에 없는 범주이기 때문입니다. 국내 맞춤법 검사기는 표기 층위를 잘 잡지만, 그 위층 — 문장 문법, 문단 논리, 긴 원고에서 갈라지는 용어, 본문 인용과 참고문헌 목록의 정합 — 은 보지 않습니다. 결국 남는 건 사람이 처음부터 끝까지 다시 읽는 방법뿐입니다.

그런데 사람이 긴 원고를 한 번에 훑으면 어떻게 되는지는 다들 압니다. **뒤로 갈수록 점검이 성겨집니다.** 서론에서는 문장마다 붙잡고 늘어지다가 결론쯤 가면 눈이 미끄러집니다. 게다가 20쪽 앞에서 어떤 표기를 골랐는지 기억나지 않아, 같은 용어가 원고 안에서 갈라진 채 남습니다.

그래서 이 스킬은 원고를 한 번에 처리하지 않습니다. 약 2,000자 단위로 잘라 **한 조각씩 순차 점검**합니다. 분량이 늘어도 조각 하나에 쏟는 밀도는 그대로입니다. 대신 조각을 넘어갈 때 약어 정의·용어 표기·표 번호·인용 목록을 들고 다니며, 앞에서 정한 방식을 뒤에도 똑같이 적용합니다.

여기까지가 1.0이었습니다. 그다음에 새로운 문제가 생겼습니다.

**AI가 초안이나 문헌 정리에 관여한 원고**가 늘면서, 예전에는 드물던 실패가 흔해졌습니다. 그럴듯하지만 **존재하지 않는 문헌**이 참고문헌 목록에 앉아 있는 경우입니다. 저자명도 학술지명도 연도도 자연스럽고, 서지 형식은 오히려 사람이 손으로 적은 것보다 깔끔합니다. 그래서 눈으로는 걸러지지 않습니다. 본문 인용과 목록이 어긋난 것 — 본문에서 인용했는데 목록에 없거나, 목록에만 있고 본문에서 한 번도 부르지 않은 문헌 — 도 같은 이유로 늘었습니다.

이건 문장을 다듬어서 해결되는 종류가 아닙니다. **DOI와 URL을 실제로 열어보는 수밖에 없습니다.** v1.1에서 서지 실재 검증(`verify_references`)을 넣은 이유입니다. 투고 전 마지막 점검에서 이 축이 가장 값집니다. 오탈자는 교정 사항이지만, 존재하지 않는 인용은 그보다 훨씬 무거운 문제이기 때문입니다.

자매 스킬 [fact-verify](https://github.com/parkjui92/fact-verify)와는 담당 구간이 다릅니다. fact-verify는 **조사 단계**에서, 아직 원고에 들어가지 않은 출처를 거릅니다. paper-proofread는 **원고 단계**에서, 이미 문장에 박힌 인용과 목록의 정합을 봅니다. 앞에서 한 번 거르고 뒤에서 한 번 더 대조하는 셈입니다.

---

## 점검 축 — 전체 표

| 축 | 보는 것 | 예 |
|---|---|---|
| **표기 교정** | 맞춤법, 띄어쓰기, 외래어 표기, 문장부호, 숫자·단위 통일, 약어 첫 등장 시 풀어쓰기 | 데이타 → 데이터 · 갯수 → 개수 · 할수있다 → 할 수 있다 |
| **문장 교열** | 주술 호응, 조사 오용, 이중피동, 번역투, 문장 길이, 중복 표현, 피동태 연속, 접속사 과다 | 분석되어지고 → 분석되고 · ~에 있어서 → ~에서 |
| **논리·구조** | 문단의 주장→근거→정리 구조, 청크(chunk)[^chunk] 간 전환의 자연스러움, 용어 일관성, 표·그림 번호 순서와 본문 참조 여부 | 앞 절 '기술이전' ↔ 뒤 절 '기술 이전' |
| **인용·참고문헌** | 본문 인용 ↔ 목록 대조, 서지정보 완결성, 인용 형식 일관성, 정렬 순서, 연도 일치 | 본문 (김철수, 2021)이 목록에 없음 |
| **서지 실재 검증** (선택) | DOI·URL 실제 조회, 식별자 형식 검사, 조회된 메타데이터와 제목·저자·연도 대조 | DOI 조회 실패 → 🔴 환각 출처 의심 |

모든 지적에는 **심각도**가 붙습니다. 🔴 error(반드시 수정) / 🟡 suggest(수정 권고) / 🔵 style(선택). 출력 범위는 `strictness` 옵션으로 조절합니다.

---

## 작동 방식

```
문서 읽기 (.docx / .pdf / .md / .hwp → 텍스트 추출)
  → 구조 파악 · 청크 분할 (약 2,000자, 문단 경계에서 끊음)
  → [청크 N 점검 → 교정교열표 누적 → 중간 보고] × 반복
  → 참고문헌 점검 (본문 인용 ↔ 목록 대조)
  → ⚙ 선택: 서지 실재 검증 (DOI·URL 실제 조회)
  → 통합 출력 (교정교열표 · 수정 원고 · 요약 리포트)
```

**왜 청크로 나누나.** 원고 전체를 한 번에 처리하면 두 가지가 무너집니다. 세밀한 오류를 놓치고, 긴 문서는 컨텍스트 한계에 걸립니다. 잘라서 보면 분량이 늘어도 조각당 점검 밀도가 유지됩니다.

**그러면 문서 전체의 일관성은 어떻게 지키나.** 청크를 넘어갈 때 아래 정보를 들고 다닙니다.

- **약어 정의 목록** — 어느 청크에서 처음 풀어썼는지 (두 번째 등장부터는 약어만)
- **용어 표기 목록** — 핵심 용어의 띄어쓰기·한자 병기 방식
- **보조용언 표기 방식** — 첫 등장 때 확인한 방식으로 이후 통일
- **표·그림 번호 카운터** — 번호 누락, 본문에서 한 번도 부르지 않은 표
- **인용 목록** — 본문에 나온 (저자, 연도)를 모아 두었다가 마지막에 참고문헌 목록과 대조

청크마다 결과를 그때그때 보고하므로, 중간에 끼어들 수 있습니다. "3장은 그냥 넘어가도 돼", "이 표기는 학회 규정이라 두자" 같은 지시를 그 자리에서 반영합니다.

---

## 상세 사용법

명령어를 외울 필요는 없습니다. 자연어로 요청하면 다음 키워드 중 하나라도 걸릴 때 스킬이 자동으로 활성화됩니다.

> 교정 · 교열 · 교정교열 · proofreading · 논문 검토 · 논문 수정 · 원고 다듬기 · 맞춤법 검사 · 투고 전 검토 · 문장 교열 · 학술 글쓰기 점검

### 시나리오 1 — 투고 전 전체 점검

```
이 논문 투고 전에 교정교열해줘. 첨부한 .docx야.
```

네 축을 모두 돕니다. 원고를 청크로 나눈 뒤 조각마다 점검 결과를 보여주고, 마지막에 전체를 통합한 교정교열표와 수정 원고를 냅니다. 중간중간 멈춰 보고하므로 그때그때 방향을 잡아줄 수 있습니다.

### 시나리오 2 — AI가 관여한 원고, 투고 직전

```
참고문헌 실재 여부까지 검증해줘
```

`verify_references: on`이 켜집니다. 문장 교정을 다 마친 뒤 참고문헌 목록의 DOI·URL을 하나씩 실제로 열어봅니다. 조회가 안 되거나 메타데이터가 목록과 어긋나는 문헌은 🔴 + "환각 출처 의심"으로 표시됩니다.

### 시나리오 3 — 급할 때, 축을 골라서

```
맞춤법이랑 띄어쓰기만 빠르게 봐줘        → focus: surface
문장만 다듬어줘, 인용은 건드리지 말고     → focus: sentence
참고문헌만 점검해줘                      → focus: reference
```

전체를 다 돌릴 시간이 없거나, 이미 한 번 교정한 원고에서 특정 층위만 다시 보고 싶을 때 씁니다.

### 시나리오 4 — 논문이 아닌 문서

```
이 정책보고서 초안 교열해줘 (보수적으로)
```

논문 전용이 아닙니다. 보고서·제안서 같은 일반 문서에도 씁니다. 인용·참고문헌 축은 해당 문서에 인용이 있을 때만 의미가 있으니, 없으면 `focus`로 빼면 됩니다.

### strictness — 얼마나 엄격하게 볼 것인가

| 상황 | 이렇게 말하면 | 결과 |
|---|---|---|
| 공저자의 원고를 손볼 때. 남의 문체를 함부로 바꾸기 곤란한 경우 | "보수적으로 교정해줘" | `conservative` · 🔴만 |
| 보통의 투고 전 점검 | (지정하지 않음) | `moderate` · 🔴 + 🟡 |
| 내 원고를 문체까지 갈아엎을 때 | "스타일까지 다 봐줘" | `aggressive` · 🔴 + 🟡 + 🔵 |

**2패스를 권합니다.** 먼저 `conservative`로 돌려 🔴만 정리해 원고를 규범적으로 깨끗하게 만든 다음, `aggressive`로 다시 돌려 문체를 다듬는 순서입니다. 한 번에 수십 건을 받아 들면 어느 것이 반드시 고쳐야 할 항목인지 분간이 안 되는데, 나눠 받으면 판단이 쉬워집니다.

### 🔴 🟡 🔵 를 받았을 때 어떻게 처리하나

| 심각도 | 뜻 | 처리 |
|---|---|---|
| 🔴 **error** | 규범 위반·인용 불일치. 판단의 여지가 없는 것 | **전부 반영합니다.** 만약 반영하면 안 될 것 같은 항목이 있다면 대개 스킬이 문맥을 잘못 읽은 경우이니, 그 자리를 짚어 되물으면 됩니다 |
| 🟡 **suggest** | 고치면 읽기 좋아지지만 틀린 건 아닌 것 | **골라 씁니다.** 번역투는 대체로 고치는 편이 낫지만, 해당 분야에서 굳어진 표현이거나 원저자 문체상 유지할 이유가 있으면 남깁니다 |
| 🔵 **style** | 취향 차이 | **유형 단위로 처리합니다.** 하나씩 판단하지 말고 "60자 넘는 문장 분리만 반영해줘"처럼 유형을 골라 일괄 적용하는 편이 빠릅니다 |

한 가지 짚어둘 원칙이 있습니다. 둘 다 맞는 표기(예: "읽어 보다 / 읽어보다")는 원고 안에서 통일되어 있으면 **수정 대상이 아닙니다.** 혼용된 경우에만 다수 용례 쪽으로 통일을 권고합니다. 표기 취향을 바꾸는 도구가 아니라, 원고를 일관되게 만드는 도구입니다.

학술적 내용과 주장 자체도 건드리지 않습니다. 표현과 형식만 다듬습니다.

### 서지 실재 검증은 언제 켜나

기본값은 off입니다. 네트워크를 쓰는 유일한 단계이기 때문입니다.

**켜는 게 좋을 때**

- **투고·제출 직전** — 마지막 한 번은 실제로 열어보는 편이 낫습니다
- **AI가 초안이나 문헌 정리에 관여한 원고** — 환각 출처가 실제로 생기는 구간입니다
- **공저·인수인계 원고** — 내가 직접 읽지 않은 문헌이 목록에 섞여 있을 때
- **오래 묵힌 원고** — 걸어둔 링크가 죽어 있을 수 있습니다

**굳이 켤 필요 없을 때**

- 네트워크가 없거나 막힌 환경
- 문장만 빠르게 다듬으려는 경우 — 목록에 있는 문헌 수만큼 조회가 붙습니다

확인이 안 되는 문헌(페이월, 오프라인 단행본 등)은 **오류로 단정하지 않고 "미확인"으로 따로 셉니다.** 확인에 실패한 것과 실존하지 않는 것을 구분해 표시하는 게 이 단계의 핵심입니다.

---

## 무엇이 나오나

세 가지가 함께 나옵니다.

| 산출물 | 내용 |
|---|---|
| **교정교열표** | 청크별 지적을 하나로 통합한 표. 위치·심각도·유형·원문·수정안·사유. 20건 이상이면 별도 `.md` 파일로 |
| **수정 원고** | 모든 청크의 반영본을 순서대로 합친 전문. 기본 마크다운, 요청하면 `.docx` |
| **요약 리포트** | 총 건수와 심각도 분포, 반복 출현한 오류 패턴, 불일치가 발견된 용어 목록, 인용 점검 결과, 구조적 개선 권고 |

요약 리포트의 "반복 패턴" 항목을 눈여겨보면 좋습니다. 개별 수정 사항을 하나씩 반영하는 것은 이번 원고를 고치는 일이지만, "이 원고에서 특정 번역투가 반복해서 나온다"는 한 줄은 다음 원고를 바꿉니다.

---

## 요구 환경 · 원고 보호

- **Claude Code(로컬) 또는 claude.ai** — 양쪽 경로를 모두 지원합니다 (v1.1).
- 선택 의존성 (없으면 자동으로 다음 경로로 폴백합니다):

| 형식 | 1차 | 2차 | 3차 |
|---|---|---|---|
| `.docx` | `pandoc` | `python-docx` | docx 스킬 |
| `.pdf` | pdf 스킬 | `pypdf` / `pdfminer.six` | — |
| `.hwp` · `.hwpx` | [kordoc](https://github.com/chrisryugj/kordoc) MCP | kordoc CLI | LibreOffice 변환 |
| `.md` · `.txt` | 직접 읽기 | — | — |

어떤 경로를 썼는지 결과에 함께 알립니다.

> ⚠️ **`.hwp` 입력 시 주의.** LibreOffice 폴백 경로는 표·그림이 텍스트로 평탄화될 수 있습니다. 표가 많은 원고는 kordoc 경로를 우선하고, 추출본에서 표가 사라진 것으로 보이면 결과에 "원본 대조 필요"를 명시합니다.

원고 본문은 외부로 전송되지 않습니다. 네트워크를 쓰는 것은 사용자가 켠 경우의 서지 실재 검증뿐이며, 그때도 조회하는 것은 서지정보(제목·저자·DOI)뿐입니다.

---
---

<a name="english"></a>

# Why I built this · Detailed usage

[한국어](#왜-만들었나--상세-사용법) · **English**

Background and usage scenarios trimmed out of the README.

---

## Why I built this

The last pass over a manuscript before you hand it in has always been human work. The problem is that this particular job falls into a gap between the available tools.

Korean academic prose has failure modes of its own. Four that show up constantly:

**1. 이중피동 — the double passive.**
"분석되어지고 있다" (*"is being analyzed"*). The verb stem already takes `-되다`, which makes it passive; then `-어지다` is added, making it passive a second time. It's a norm violation, but it has become so common in Korean academic writing that it reads as perfectly fluent. Nothing snags when you read past it.

**2. 번역투 — translationese.**
"연구에 **있어서**" where plain "연구**에서**" ("in this study") says exactly the same thing in half the space. It's a calque — Japanese *~において*, English "with regard to" — that settled into Korean academic register and never left. Others in the same family: "~하는 것이 가능하다" (a literal rendering of "it is possible to," where Korean has a one-word form), "~로 사료된다" (an ornate hedge for "appears to be"), "~가 행해졌다" (a Japanese-shaped passive for "was carried out"). None of these are ungrammatical, so a spell checker passes every one. They just make sentences longer and claims vaguer.

**3. 주술 불일치 — subject–predicate mismatch.**
Korean is verb-final and lets you stack modifying clauses in front of the predicate without any structural limit. Subjects can also be dropped freely. Put those two together and a subject can end up far enough from its verb that agreement quietly breaks — and the author, who knows what the sentence was supposed to mean, is the last person who will notice.

**4. 띄어쓰기 — the spacing gray zone.**
Korean spacing has cases where two spellings are *both* standard. "읽어 보다" and "읽어보다" ("to try reading") are both correct. So the right answer isn't one of them — it's *whichever one you already used elsewhere in this manuscript*. A checker that flags one as wrong is worse than no checker at all. What you actually need is consistency detection across the whole document.

English-language proofreading tools don't model any of this. Not because they're weak, but because these categories don't exist in the language they were built for. Korean spell checkers do exist and handle the orthography layer well. What neither covers is the layer above it: sentence grammar, paragraph logic, terminology that drifts across a long document, and whether the citations in the body actually match the reference list. Which leaves reading the whole thing again, by hand.

And everyone knows what happens when a person reads a long manuscript in one pass. **The checking thins out toward the end.** You wrestle with every sentence in the introduction; by the conclusion your eyes are skating. Worse, you can't remember which of two legal spellings you picked twenty pages ago, so the same term ends up split across the document.

So this skill doesn't process a manuscript in one pass. It cuts it into roughly 2,000-character chunks and **checks them one at a time, in sequence.** Length goes up; the density of attention per chunk doesn't. What crosses the chunk boundary is a carried-forward record — abbreviation definitions, term spellings, table numbers, the running citation list — so a decision made early is applied consistently later.

That was version 1.0. Then a new problem showed up.

As **AI-assisted manuscripts** became common, a failure that used to be rare became ordinary: a plausible but **nonexistent work sitting in the reference list.** The author name reads naturally, so does the journal, so does the year, and the bibliographic formatting is often *cleaner* than what a human types by hand. Which is exactly why the eye doesn't catch it. Mismatches between body and list — a work cited in the text but missing from the list, or a work in the list that the text never actually calls — became more common for the same reason.

This isn't the kind of thing you fix by improving sentences. **You have to actually open the DOI and the URL.** That's why v1.1 added optional reference-existence verification (`verify_references`). It's the most valuable axis in a final pre-submission pass: a typo is a correction, but a citation to something that doesn't exist is a much heavier problem.

The sister skill [fact-verify](https://github.com/parkjui92/fact-verify) covers a different stretch of the same road. fact-verify screens sources at the **research stage**, before they ever reach the manuscript. paper-proofread checks, at the **manuscript stage**, the citations already embedded in sentences and whether they reconcile with the list. Filter once going in, cross-check once coming out.

---

## What it checks — full table

| Axis | What it looks at | Example |
|---|---|---|
| **Orthography** | Spelling, spacing, loanword transliteration, punctuation, number/unit consistency, abbreviations spelled out on first use | 데이타 → 데이터 (*data*) · 갯수 → 개수 (*count*) · 할수있다 → 할 수 있다 (*can do*, bound-noun spacing) |
| **Sentence editing** | Subject–predicate agreement, particle misuse, double passives, translationese, sentence length, redundancy, passive-voice runs, conjunction overuse | 분석되어지고 → 분석되고 (double passive removed) · ~에 있어서 → ~에서 |
| **Logic & structure** | Claim→evidence→wrap-up structure within paragraphs, transitions across chunks, terminology consistency, table/figure numbering and whether the body actually references them | 기술이전 in one section vs. 기술 이전 in another (same term, split spelling) |
| **Citations & references** | In-text citations vs. reference list, bibliographic completeness, format consistency, sort order, year agreement | (김철수, 2021) cited in the body but absent from the list |
| **Reference existence** (optional) | Resolves DOIs and URLs for real, checks identifier format, compares retrieved metadata against the listed title / authors / year | DOI fails to resolve → 🔴 suspected hallucinated citation |

Every finding carries a **severity**: 🔴 error (must fix) / 🟡 suggest (recommended) / 🔵 style (optional). The `strictness` option controls how much of that you see.

---

## How it works

```
Read document (.docx / .pdf / .md / .hwp → text extraction)
  → Map structure · split into chunks (~2,000 chars, cut at paragraph boundaries)
  → [check chunk N → append to correction table → report back] × repeat
  → Reference check (in-text citations ↔ reference list)
  → ⚙ optional: reference-existence verification (resolve DOIs / URLs)
  → Consolidated output (correction table · corrected manuscript · summary report)
```

**Why chunks.** Processing a whole manuscript at once breaks two things: fine-grained errors get missed, and long documents run into context limits. Splitting keeps per-chunk scrutiny constant no matter how long the document gets.

**Then how does document-wide consistency survive?** State is carried across chunk boundaries:

- **Abbreviation definitions** — which chunk first spelled a term out (so later chunks use the short form)
- **Term spellings** — spacing and Hanja-gloss decisions for key terms
- **Auxiliary-verb spacing** — the convention observed at first occurrence, then applied throughout
- **Table/figure counters** — gaps in numbering, tables the body never references
- **Citation list** — every (author, year) seen in the body, collected for the final reconciliation against the reference list

Results are reported chunk by chunk as it goes, so you can intervene mid-run: "skip chapter 3," "leave that spelling, it's the journal's house style."

---

## Detailed usage

There are no commands to memorize — ask in natural language and the skill activates on any of these keywords:

> 교정 · 교열 · 교정교열 · **proofreading** · 논문 검토 · 논문 수정 · 원고 다듬기 · 맞춤법 검사 · 투고 전 검토 · 문장 교열 · 학술 글쓰기 점검

The trigger list is Korean apart from `proofreading`, so an English request should include that word. If it doesn't fire, invoke the skill by name.

> **Note on languages.** The manuscripts this skill checks are Korean — the rule reference (`references/rules_ko.md`) and the report templates in `SKILL.md` are written in Korean. You can direct it in English; the material it works on is not.

### Scenario 1 — Full pre-submission pass

```
Proofread this paper before I submit it. The .docx is attached.
```

Runs all four axes. Splits the manuscript into chunks, shows findings for each, then consolidates into one correction table plus the corrected manuscript. It pauses to report along the way, so you can steer as it runs.

### Scenario 2 — AI-assisted manuscript, right before submission

```
Also verify that the references actually exist
```

Turns on `verify_references: on`. After sentence-level editing finishes, it opens each DOI and URL in the reference list for real. Anything that fails to resolve, or whose retrieved metadata disagrees with the listed entry, is flagged 🔴 with "suspected hallucinated citation."

### Scenario 3 — In a hurry, pick an axis

```
Just spelling and spacing, quickly            → focus: surface
Sentences only — don't touch the citations    → focus: sentence
Check the references only                     → focus: reference
```

For when there's no time for a full pass, or when you've already corrected once and want to re-examine a single layer.

### Scenario 4 — Documents that aren't papers

```
Copyedit this policy report draft, conservatively
```

Not restricted to academic papers. Reports and proposals work too. The citation axis only means something if the document has citations — if it doesn't, exclude it with `focus`.

### strictness — how hard to push

| Situation | Say this | Result |
|---|---|---|
| Editing a co-author's manuscript, where rewriting someone else's voice is awkward | "conservatively" / "보수적으로 교정해줘" | `conservative` · 🔴 only |
| Ordinary pre-submission check | (don't specify) | `moderate` · 🔴 + 🟡 |
| Your own manuscript, style included | "go over the style too" | `aggressive` · 🔴 + 🟡 + 🔵 |

**Two passes work better than one.** Run `conservative` first and clear the 🔴s, which gets the manuscript normatively clean. Then run `aggressive` and work on style. Handed dozens of findings at once, you can't tell which ones are non-negotiable; split across two passes, the judgment is easy.

### What to do with 🔴 🟡 🔵

| Severity | Meaning | How to handle it |
|---|---|---|
| 🔴 **error** | Norm violation or citation mismatch — no judgment call involved | **Apply all of them.** If one looks wrong to you, it's usually the skill misreading context — point at that spot and ask |
| 🟡 **suggest** | Better if changed, but not incorrect as written | **Pick and choose.** Translationese is usually worth fixing, but keep it where a phrase is entrenched in your field or the author's voice depends on it |
| 🔵 **style** | Preference | **Handle by type, not item.** Rather than adjudicating each one, select a category: "just apply the sentence splits for anything over 60 characters" |

One principle worth stating outright: where two spellings are both correct (that "읽어 보다 / 읽어보다" case), a manuscript that is already internally consistent **is not flagged.** A recommendation is issued only when the two are mixed, and it points toward whichever form you used more. This is a tool for making a manuscript consistent, not for imposing a spelling preference.

It also leaves scholarly content and claims alone. Expression and formatting only.

### When to switch on reference-existence verification

Off by default — it's the only step that touches the network.

**Worth turning on**

- **Right before submission** — one pass where the sources actually get opened
- **Manuscripts where AI helped with the draft or the reference list** — this is where hallucinated citations actually appear
- **Co-authored or handed-over manuscripts** — when the list includes works you didn't read yourself
- **Manuscripts that sat for a while** — links go dead

**Not worth it**

- Environments with no network access
- When you only want a fast sentence pass — you're adding one lookup per entry in the list

Entries that can't be confirmed (paywalled, offline books) are **counted separately as "unverified" rather than declared wrong.** Keeping *failed to confirm* distinct from *does not exist* is the whole point of the step.

---

## What you get

Three artifacts.

| Output | Contents |
|---|---|
| **Correction table** | All chunk-level findings consolidated: location, severity, type, original, suggestion, reason. Written to a separate `.md` file at 20 or more items |
| **Corrected manuscript** | Every chunk's corrected text stitched back in order. Markdown by default, `.docx` on request |
| **Summary report** | Total count and severity split, recurring error patterns, terms found to be inconsistent, citation-check results, structural recommendations |

The "recurring patterns" line in the summary is worth reading closely. Applying individual corrections fixes *this* manuscript; a line telling you that one particular calque keeps reappearing changes the next one.

---

## Requirements · manuscript privacy

- **Claude Code (local) or claude.ai** — both paths supported as of v1.1.
- Optional dependencies, with automatic fallback down the chain:

| Format | 1st | 2nd | 3rd |
|---|---|---|---|
| `.docx` | `pandoc` | `python-docx` | docx skill |
| `.pdf` | pdf skill | `pypdf` / `pdfminer.six` | — |
| `.hwp` · `.hwpx` | [kordoc](https://github.com/chrisryugj/kordoc) MCP | kordoc CLI | LibreOffice conversion |
| `.md` · `.txt` | read directly | — | — |

Whichever path was used is reported with the results.

> **`.hwp` / `.hwpx`** is Hangul Word Processor format — the de facto standard for Korean academic and government documents, and the reason a Korean-facing tool needs its own extraction chain.

> ⚠️ **Caveat on `.hwp` input.** The LibreOffice fallback can flatten tables and figures into plain text. Prefer the kordoc path for table-heavy manuscripts; if tables appear to have vanished from the extraction, the results will say so explicitly ("original comparison required").

Manuscript text is never sent anywhere. The only step that uses the network is reference-existence verification, and only if you turn it on — and even then, the only thing queried is bibliographic data (title, authors, DOI).

[^chunk]: 청크(chunk): 긴 원고를 한 번에 점검하지 않고 약 2,000자(`chunk_size`)씩 문단 경계에서 나눈 조각. 조각마다 차례로 점검해야 긴 원고에서도 세밀한 오류를 놓치지 않는다.
