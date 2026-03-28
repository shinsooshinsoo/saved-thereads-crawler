"""프로젝트 설정 및 카테고리 정의."""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# ── Gemini API ──────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = "gemini-2.5-flash-lite"

# ── 카테고리 ────────────────────────────────────────────────
CATEGORIES = ["정보", "지혜", "기술", "뉴스", "인생"]

# ── 경로 ────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"

# ── Threads ─────────────────────────────────────────────────
THREADS_SAVED_URL = "https://www.threads.com/saved"
THREADS_BASE_URL = "https://www.threads.com"

# ── 스크래핑 설정 ───────────────────────────────────────────
SCROLL_PAUSE_SEC = 2.0        # 스크롤 간 대기 시간
MAX_SCROLL_ATTEMPTS = 50      # 최대 스크롤 횟수
LOGIN_TIMEOUT_SEC = 300       # 로그인 대기 시간 (5분)

# ── Gemini 분류 설정 ────────────────────────────────────────
CLASSIFY_DELAY_SEC = 0.1      # API 호출 간 딜레이 (유료 티어 권장: 속도 대폭 향상)
