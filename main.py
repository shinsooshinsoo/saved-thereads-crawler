"""Threads 저장글 -> Markdown 파이프라인 메인 스크립트."""

from __future__ import annotations

import re
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any

import config
from scraper import scrape_saved_posts
from classifier import classify_posts


# ─────────────────────────────────────────────────────────────
# 유틸
# ─────────────────────────────────────────────────────────────

def _safe_filename(text: str, max_len: int = 60) -> str:
    """텍스트를 안전한 파일명으로 변환."""
    name = re.sub(r'[\\/*?:"<>|\n\r\t]', "", text).strip()
    name = re.sub(r"\s+", "_", name)
    return name[:max_len] if name else "untitled"


def _download_image(url: str, dest: Path) -> bool:
    """이미지 다운로드. 성공 시 True."""
    try:
        dest.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(url, str(dest))
        return True
    except Exception as e:
        print(f"    [!] 이미지 다운로드 실패: {e}")
        return False


# ─────────────────────────────────────────────────────────────
# Markdown 파일 생성
# ─────────────────────────────────────────────────────────────

def _create_post_markdown(post: dict[str, Any], post_num: int) -> str:
    """단일 글 → Markdown 문자열 변환."""

    title = post["text"][:50].replace("\n", " ").strip() or "제목 없음"
    author = post.get("author", "알 수 없음")
    timestamp = post.get("timestamp", "알 수 없음")
    category = post.get("category", "정보")
    url = post.get("url", "")

    lines = [
        f"# {title}",
        "",
        f"- **작성자:** {author}",
        f"- **작성일:** {timestamp}",
        f"- **원본:** [{url}]({url})" if url else "",
        f"- **주제:** {category}",
        "",
        "---",
        "",
        post.get("text", ""),
        "",
    ]

    # 이미지 추가
    local_images = post.get("local_images", [])
    if local_images:
        lines.append("")
        for img_path in local_images:
            lines.append(f"![이미지]({img_path})")
            lines.append("")

    # 댓글 추가
    comments = post.get("comments", [])
    if comments:
        lines.append("---")
        lines.append("")
        lines.append("## 댓글")
        lines.append("")
        for c in comments:
            c_author = c.get("author", "익명")
            c_text = c.get("text", "")
            lines.append(f"> **{c_author}:** {c_text}")
            lines.append("")

    return "\n".join(lines)


def _create_index_markdown(posts: list[dict[str, Any]]) -> str:
    """전체 목록 index.md 생성."""
    lines = [
        "# 📚 Threads 저장글 모음",
        "",
        f"총 **{len(posts)}** 개의 글",
        "",
        f"생성일: {time.strftime('%Y-%m-%d %H:%M')}",
        "",
        "---",
        "",
    ]

    # 카테고리별 그룹핑
    by_category: dict[str, list] = {}
    for p in posts:
        cat = p.get("category", "정보")
        by_category.setdefault(cat, []).append(p)

    for cat in config.CATEGORIES:
        cat_posts = by_category.get(cat, [])
        if not cat_posts:
            continue
        lines.append(f"## {cat} ({len(cat_posts)}개)")
        lines.append("")
        for p in cat_posts:
            title = p["text"][:50].replace("\n", " ").strip() or "제목 없음"
            fname = p.get("filename", "")
            author = p.get("author", "알 수 없음")
            lines.append(f"- [{title}](./{cat}/{fname}) — @{author}")
        lines.append("")

    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────
# 파일 저장
# ─────────────────────────────────────────────────────────────

def save_posts(posts: list[dict[str, Any]]) -> None:
    """분류된 글들을 Markdown 파일로 저장."""
    output_dir = config.OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    # 카테고리별 폴더 생성
    for cat in config.CATEGORIES:
        (output_dir / cat).mkdir(exist_ok=True)
        (output_dir / cat / "images").mkdir(exist_ok=True)

    print(f"\n💾 {len(posts)}개 글을 Markdown으로 저장합니다...")

    for i, post in enumerate(posts, 1):
        category = post.get("category", "정보")
        cat_dir = output_dir / category

        # 이미지 다운로드
        local_images = []
        for j, img_url in enumerate(post.get("images", [])):
            ext = ".jpg"
            if ".png" in img_url:
                ext = ".png"
            elif ".webp" in img_url:
                ext = ".webp"
            img_name = f"post_{i:03d}_img{j + 1}{ext}"
            img_dest = cat_dir / "images" / img_name
            if _download_image(img_url, img_dest):
                # MD에서 상대 경로로 참조
                local_images.append(f"./images/{img_name}")
        post["local_images"] = local_images

        # MD 파일 생성
        title_text = post["text"][:50].replace("\n", " ").strip() or "untitled"
        filename = f"post_{i:03d}_{_safe_filename(title_text)}.md"
        post["filename"] = filename

        md_content = _create_post_markdown(post, i)
        md_path = cat_dir / filename
        md_path.write_text(md_content, encoding="utf-8")
        print(f"  [{i}/{len(posts)}] {category}/{filename}")

    # index.md 생성
    index_content = _create_index_markdown(posts)
    index_path = output_dir / "index.md"
    index_path.write_text(index_content, encoding="utf-8")
    print(f"\n📄 index.md 생성 완료: {index_path}")


# ─────────────────────────────────────────────────────────────
# 메인
# ─────────────────────────────────────────────────────────────

def main() -> None:
    """파이프라인 실행."""
    print("=" * 60)
    print("🧵 Threads 저장글 → Markdown 분류 파이프라인")
    print("=" * 60)

    # 1) API 키 확인
    if not config.GEMINI_API_KEY or config.GEMINI_API_KEY == "your_key_here":
        print("\n❌ GEMINI_API_KEY를 .env 파일에 설정해주세요!")
        print("   Google AI Studio에서 발급: https://aistudio.google.com")
        sys.exit(1)

    # 2) Threads 스크래핑
    print("\n── Step 1: Threads 저장글 스크래핑 ──")
    posts = scrape_saved_posts()

    if not posts:
        print("\n⚠ 스크래핑된 글이 없습니다. 종료합니다.")
        sys.exit(0)

    # 3) Gemini 분류
    print("\n── Step 2: Gemini 주제 분류 ──")
    posts = classify_posts(posts)

    # 4) Markdown 저장
    print("\n── Step 3: Markdown 파일 저장 ──")
    save_posts(posts)

    # 5) 요약
    print("\n" + "=" * 60)
    print("🎉 완료!")
    print(f"   📁 결과 위치: {config.OUTPUT_DIR}")
    print(f"   📋 총 {len(posts)}개 글 처리됨")
    summary: dict[str, int] = {}
    for p in posts:
        cat = p.get("category", "정보")
        summary[cat] = summary.get(cat, 0) + 1
    for cat, cnt in summary.items():
        print(f"      {cat}: {cnt}개")
    print("=" * 60)


if __name__ == "__main__":
    main()
