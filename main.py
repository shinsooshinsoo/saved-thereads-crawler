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


# ─────────────────────────────────────────────────────────────
# 유틸
# ─────────────────────────────────────────────────────────────

def _safe_filename(text: str, max_len: int = 60) -> str:
    """텍스트를 안전한 파일명으로 변환."""
    name = re.sub(r'[\\/*?:"<>|\n\r\t]', "", text).strip()
    name = re.sub(r"\s+", "_", name)
    return name[:max_len] if name else "untitled"





# ─────────────────────────────────────────────────────────────
# Markdown 파일 생성
# ─────────────────────────────────────────────────────────────

def _create_post_markdown(post: dict[str, Any], post_num: int) -> str:
    """단일 글 → Markdown 문자열 변환."""

    title = post["text"][:50].replace("\n", " ").strip() or "제목 없음"
    author = post.get("author", "알 수 없음")
    timestamp = post.get("timestamp", "알 수 없음")
    url = post.get("url", "")

    lines = [
        f"# {title}",
        "",
        f"- **작성자:** {author}",
        f"- **작성일:** {timestamp}",
        f"- **원본:** [{url}]({url})" if url else "",
        "",
        "---",
        "",
        post.get("text", ""),
        "",
    ]

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

    for p in posts:
        title = p["text"][:50].replace("\n", " ").strip() or "제목 없음"
        fname = p.get("filename", "")
        author = p.get("author", "알 수 없음")
        lines.append(f"- [{title}](./{fname}) — @{author}")

    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────
# 파일 저장
# ─────────────────────────────────────────────────────────────

def save_posts(posts: list[dict[str, Any]]) -> None:
    """글들을 Markdown 파일로 저장."""
    output_dir = config.OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n💾 {len(posts)}개 글을 Markdown으로 저장합니다...")

    for i, post in enumerate(posts, 1):
        # MD 파일 생성
        title_text = post["text"][:50].replace("\n", " ").strip() or "untitled"
        filename = f"post_{i:03d}_{_safe_filename(title_text)}.md"
        post["filename"] = filename

        md_content = _create_post_markdown(post, i)
        md_path = output_dir / filename
        md_path.write_text(md_content, encoding="utf-8")
        print(f"  [{i}/{len(posts)}] {filename}")

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
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    print("=" * 60)
    print("[*] Threads 저장글 -> Markdown 추출 파이프라인")
    print("=" * 60)

    # 1) Threads 스크래핑
    print("\n── Step 1: Threads 저장글 스크래핑 ──")
    posts = scrape_saved_posts()

    if not posts:
        print("\n⚠ 스크래핑된 글이 없습니다. 종료합니다.")
        sys.exit(0)

    # 2) Markdown 저장
    print("\n── Step 2: Markdown 파일 저장 ──")
    save_posts(posts)

    # 3) 요약
    print("\n" + "=" * 60)
    print("🎉 완료!")
    print(f"   📁 결과 위치: {config.OUTPUT_DIR}")
    print(f"   📋 총 {len(posts)}개 글 처리됨")
    print("=" * 60)


if __name__ == "__main__":
    main()
