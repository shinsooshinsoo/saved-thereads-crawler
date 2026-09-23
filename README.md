# Threads Saved to Markdown Pipeline 🧵➡️📝

Threads(스레드)에서 **'저장됨'** 폴더에 보관한 소중한 글들을 자동으로 수집하여, AI(로컬 Ollama 또는 Google Gemini)가 분석하고 깔끔한 마크다운(Markdown) 문서로 변환해주는 파이썬 프로그램입니다.

---

## ✨ 주요 기능

- **자동 스크래핑 & 세션 유지**: Playwright를 이용해 로그인 세션을 유지하며 저장된 글 목록(`/saved`)을 끝까지 스크롤하여 수집합니다.
- **스마트 리다이렉트 방지 아키텍처**:
  - 저장글 목록은 로그인 세션으로 안전하게 수집하고, 개별 글 상세 페이지는 클린 비인증 세션으로 접속하여 Threads 웹 특유의 **홈 피드(302) 튕김 현상을 원천 방지**합니다.
- **관련 스레드(추천 피드) 차단 & 정품 댓글 선별**:
  - 글 하단에 무한으로 붙는 무관한 추천 피드(야구, 사주, 광고 등)를 구분선(Divider)으로 완벽 감지 및 차단합니다.
  - 원글 작성자의 **스레드 이어쓰기(본문 연장)** 및 독자들의 **진짜 댓글**만 정확하게 선별 수집합니다.
- **정확한 메타데이터 & 텍스트 정제**:
  - 글 URL에서 정확한 `@아이디`를 추출하여 작성자명이 `"스레드"`나 `"프로필"`로 잡히는 문제를 해결했습니다.
  - 본문 앞머리의 시간/태그(예: `22시간`, `사주 1일`) 및 UI 찌꺼기 텍스트를 자동 정제합니다.
- **Ollama(로컬 AI) & Gemini API 지원**:
  - `config.py` 설정을 통해 로컬 Ollama 모델(Gemma, Llama 등) 또는 Google Gemini 모델을 자유롭게 선택하여 사용할 수 있습니다.
- **AI 스마트 리네임 (`clean_rename.py`)**:
  - AI가 본문 핵심을 파악하여 간결하고 직관적인 한국어 파일명으로 자동 변경합니다.
- **텍스트 정밀 청소 도구 (`clean_garbage.py`, `deep_clean.py`)**:
  - UI 찌꺼기 제거 및 예외적인 중복 텍스트 블록 제거 도구를 제공합니다.
- **자동 인덱스 생성 (`update_index.py`)**:
  - 수집된 모든 마크다운 파일의 목록을 한눈에 볼 수 있는 `output/index.md`를 자동 생성 및 갱신합니다.

---

## 🚀 시작하기

### 1. 요구 사항
- Python 3.9 이상
- Google Gemini API Key (Gemini 사용 시) 또는 로컬 [Ollama](https://ollama.com/) 실행 환경

### 2. 설치

```bash
# 저장소 클론 (또는 다운로드)
git clone https://github.com/shinsooshinsoo/saved-thereads-crawler.git
cd saved-thereads-crawler

# 필수 라이브러리 설치
pip install -r requirements.txt

# Playwright 브라우저 설치
playwright install chromium
```

### 3. 설정 (`.env` 파일 생성)

프로젝트 루트 디렉토리에 `.env` 파일을 생성하고 발급받은 API 키를 입력합니다 (Gemini 사용 시).
```env
GEMINI_API_KEY=your_actual_api_key_here
```

`config.py`에서 AI 엔진을 선택할 수 있습니다:
```python
# config.py
USE_OLLAMA = True             # True: 로컬 Ollama 사용 / False: Gemini API 사용
OLLAMA_MODEL = "gemma4:e4b"   # 로컬에 설치된 모델명 (예: gemma, llama3 등)
GEMINI_MODEL = "gemini-3.1-flash-lite"
```

---

## 🛠️ 사용 방법

### 1. 기본 실행 (저장글 스크래핑 및 마크다운 변환)
```bash
python main.py
```
- **최초 실행 시 1회 로그인**: 브라우저 창이 열리면 Threads 로그인을 완료하고 터미널에서 `Enter`를 누릅니다. 세션이 `.auth_state.json`에 저장되어 이후에는 자동 로그인됩니다.
- 수집된 글은 `output/` 폴더에 마크다운 파일로 저장됩니다.

### 2. 추가 관리 스크립트
- `python clean_rename.py`: AI를 이용해 파일명을 읽기 쉬운 간결한 제목으로 일괄 변경합니다.
- `python clean_garbage.py`: 본문에 섞여 들어간 불필요한 UI 문구(좋아요 수, 버튼 등)를 일괄 제거합니다.
- `python update_index.py`: `output/` 내의 전체 마크다운 글 목록을 담은 `index.md`를 최신 상태로 갱신합니다.
- `python deep_clean.py`: 원문-댓글 중복 블록 사후 치료 도구.

---

## ⚠️ 주의 사항 및 팁

- **로그인 보안**: `.auth_state.json` 파일에는 본인의 Threads 로그인 쿠키가 저장되어 있습니다. **절대 외부에 공유하거나 깃허브에 올리지 마세요.** (이미 `.gitignore`에 등록되어 있습니다)
- **API 요율 제한**: Gemini API 사용 시 안정적인 속도를 위해 유료 결제(Pay-as-you-go) 연동 키 사용을 권장합니다. 로컬 무료 사용을 원하시면 Ollama를 활성화(`USE_OLLAMA = True`)하세요.
- **스크래핑 정책**: 본 프로그램은 개인적인 보존 및 학습 용도로만 사용하시길 권장합니다.

---

## 📁 프로젝트 구조

```
├── main.py              # 전체 파이프라인 조율 메인 스크립트
├── scraper.py           # Playwright 기반 스크래퍼 (리다이렉트 방지, 추천피드 차단)
├── config.py            # LLM 설정, 딜레이, URL 등 주요 설정값
├── update_index.py      # output/ 내 마크다운 파일 통합 인덱스(index.md) 생성
├── clean_rename.py      # AI 기반 간결한 파일명 일괄 변경
├── clean_garbage.py     # 본문/댓글 내 UI 찌꺼기 텍스트 청소
├── deep_clean.py        # 원문-댓글 중복 텍스트 정제
├── add_tags.py          # AI 기반 해시태그 추가
├── classifier.py        # 텍스트 카테고리 분류
├── requirements.txt     # 파이썬 의존성 패키지 목록
├── .env.example         # 환경변수 예시 파일
└── README.md            # 프로젝트 안내 문서
```

---
이 도구가 여러분의 지식 보관소 구축에 도움이 되길 바랍니다! 🌟
