"""프로젝트 설정 및 카테고리 정의."""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# ── LLM 설정 (Gemini 또는 Ollama) ───────────────────────────
USE_OLLAMA = True             # True로 설정하면 로컬 Ollama 사용, False면 Gemini API 사용
OLLAMA_API_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "gemma4:e4b"   # 사용자 로컬 Ollama에 설치된 Gemma 4B 모델

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = "gemini-3.1-flash-lite"

_genai_client = None

def generate_content(prompt: str) -> str:
    """Gemini API 또는 Ollama를 사용하여 텍스트 생성."""
    if USE_OLLAMA:
        import json
        import urllib.request
        
        data = {
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False
        }
        req = urllib.request.Request(
            OLLAMA_API_URL,
            data=json.dumps(data).encode("utf-8"),
            headers={"Content-Type": "application/json; charset=utf-8"},
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as response:
                resp_data = json.loads(response.read().decode("utf-8"))
                return resp_data.get("response", "").strip()
        except Exception as e:
            if GEMINI_API_KEY:
                print(f"\n  [!] Ollama 호출 실패로 인해 Gemini API로 대체 시도합니다... (에러: {e})")
                return _generate_content_gemini(prompt)
            raise RuntimeError(f"Ollama API 호출 실패 (모델: {OLLAMA_MODEL}, URL: {OLLAMA_API_URL}): {e}")
    else:
        return _generate_content_gemini(prompt)

def _generate_content_gemini(prompt: str) -> str:
    from google import genai
    global _genai_client
    if _genai_client is None:
        if not GEMINI_API_KEY:
            raise ValueError(
                "GEMINI_API_KEY가 설정되지 않았습니다.\n"
                ".env 파일에 GEMINI_API_KEY=your_key 를 추가하거나, "
                "config.py에서 USE_OLLAMA = True 로 설정해주세요."
                )
        _genai_client = genai.Client(api_key=GEMINI_API_KEY)
    
    response = _genai_client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
    )
    return response.text.strip()


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
MAX_SCROLL_ATTEMPTS = 100      # 최대 스크롤 횟수
LOGIN_TIMEOUT_SEC = 300       # 로그인 대기 시간 (5분)

# ── Gemini 분류 설정 ────────────────────────────────────────
CLASSIFY_DELAY_SEC = 0.1      # API 호출 간 딜레이 (유료 티어 권장: 속도 대폭 향상)
