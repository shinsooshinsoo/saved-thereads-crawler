"""LLM 기반 주제 분류."""

from __future__ import annotations

import time

import config


def _build_prompt(text: str) -> str:
    """분류 프롬프트 생성."""
    categories = ", ".join(config.CATEGORIES)
    return (
        f"다음 글을 [{categories}] 중 **정확히 하나**로 분류해줘.\n"
        f"카테고리 이름만 한 단어로 답해. 다른 말은 하지 마.\n\n"
        f"글:\n{text[:2000]}"  # 토큰 절약을 위해 2000자 제한
    )


def classify_post(text: str) -> str:
    """단일 글 분류 → 카테고리 문자열 반환.

    Args:
        text: 글 본문

    Returns:
        카테고리 이름 (정보/지혜/기술/뉴스/인생)
    """
    if not text or text == "(본문 없음)":
        return "정보"  # 기본값

    prompt = _build_prompt(text)

    for attempt in range(3):
        try:
            response_text = config.generate_content(prompt)
            result = response_text.strip()

            # 응답에서 카테고리 추출 (정확히 일치하는 것만)
            for cat in config.CATEGORIES:
                if cat in result:
                    return cat

            # 일치하는 게 없으면 기본값
            print(f"  ⚠ 예상 외 분류 결과: '{result}' → '정보' 사용")
            return "정보"

        except Exception as e:
            err_msg = str(e)
            if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg:
                if attempt < 2:
                    print(f"  ⚠ Rate Limit 초과. 30초 대기 후 재시도... ({attempt+1}/3)")
                    time.sleep(30)
                    continue
            print(f"  ⚠ LLM 호출 오류: {e} → '정보' 사용")
            return "정보"
            
    return "정보"


def classify_posts(posts: list[dict]) -> list[dict]:
    """여러 글 일괄 분류. 각 post dict에 'category' 키 추가.

    Args:
        posts: scraper에서 반환된 글 리스트

    Returns:
        category가 추가된 글 리스트
    """
    if not config.USE_OLLAMA and not config.GEMINI_API_KEY:
        raise ValueError(
            "GEMINI_API_KEY가 설정되지 않았습니다.\n"
            ".env 파일에 GEMINI_API_KEY=your_key 를 추가하거나, "
            "config.py에서 USE_OLLAMA = True 로 설정해주세요."
        )

    print(f"\n[*] LLM으로 {len(posts)}개 글 분류 시작...")
    for i, post in enumerate(posts, 1):
        category = classify_post(post["text"])
        post["category"] = category
        print(f"  [{i}/{len(posts)}] {category} ← {post['text'][:40]}...")
        time.sleep(config.CLASSIFY_DELAY_SEC)

    # 결과 요약
    summary: dict[str, int] = {}
    for p in posts:
        cat = p["category"]
        summary[cat] = summary.get(cat, 0) + 1
    print(f"\n[*] 분류 결과: {summary}")

    return posts


if __name__ == "__main__":
    # 단독 테스트
    test_posts = [
        {"text": "Python 3.13에서 GIL이 제거될 예정입니다.", "author": "dev", "url": ""},
        {"text": "주식 시장이 하락세를 보이고 있습니다.", "author": "news", "url": ""},
        {"text": "인생에서 가장 중요한 건 건강입니다.", "author": "life", "url": ""},
    ]
    result = classify_posts(test_posts)
    for r in result:
        print(f"  {r['category']}: {r['text'][:50]}")
