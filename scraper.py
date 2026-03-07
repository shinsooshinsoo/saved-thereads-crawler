"""Playwright 기반 Threads 저장글 스크래핑."""

from __future__ import annotations

import json
import re
import time
import urllib.request
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, sync_playwright

import config

# 쿠키/세션 저장 경로 (한번 로그인하면 다음엔 자동)
STORAGE_PATH = config.BASE_DIR / ".auth_state.json"
# 이미 크롤링한 URL을 기록해두는 파일
CRAWLED_PATH = config.BASE_DIR / ".crawled_urls.txt"


# ─────────────────────────────────────────────────────────────
# 유틸
# ─────────────────────────────────────────────────────────────

def _download_image(url: str, dest: Path) -> str | None:
    """이미지 다운로드 후 로컬 경로 반환. 실패 시 None."""
    try:
        dest.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(url, str(dest))
        return str(dest)
    except Exception as e:
        print(f"  [!] 이미지 다운로드 실패: {e}")
        return None


def _safe_filename(text: str, max_len: int = 50) -> str:
    """텍스트를 안전한 파일명으로 변환."""
    name = re.sub(r'[\\/*?:"<>|\n\r\t]', "", text).strip()
    name = re.sub(r"\s+", "_", name)
    return name[:max_len] if name else "untitled"


# ─────────────────────────────────────────────────────────────
# 로그인 대기
# ─────────────────────────────────────────────────────────────

def _wait_for_login(page: Page, context) -> None:
    """유저가 수동 로그인할 때까지 대기."""
    ready_file = config.BASE_DIR / ".ready"
    # 이전 시그널 파일 제거
    if ready_file.exists():
        ready_file.unlink()

    print("\n" + "=" * 60)
    print("[*] Threads에 로그인해주세요 (Instagram 계정)")
    print("    브라우저에서 로그인을 완료한 후,")
    print(f"    다음 파일을 생성해주세요: {ready_file}")
    print("    (또는 로그인 후 자동 감지를 기다려주세요)")
    print("=" * 60)

    page.goto("https://www.threads.net/login")
    time.sleep(2)

    # 최대 5분 대기: .ready 파일 생성 또는 URL이 login이 아닌 것으로 감지
    deadline = time.time() + config.LOGIN_TIMEOUT_SEC
    check_count = 0
    while time.time() < deadline:
        # 방법 1: .ready 파일 존재 확인
        if ready_file.exists():
            print("[OK] .ready 파일 감지! 진행합니다.")
            ready_file.unlink()
            break

        # 방법 2: URL이 더이상 login 페이지가 아닌지 확인
        check_count += 1
        try:
            current_url = page.url
            if "login" not in current_url and "threads.net" in current_url:
                # 로그인 후 홈으로 리다이렉트됨
                print(f"[OK] 로그인 감지됨! (URL: {current_url})")
                break
        except Exception:
            pass

        if check_count % 10 == 0:
            elapsed = int(time.time() - (deadline - config.LOGIN_TIMEOUT_SEC))
            print(f"  ... 로그인 대기 중 ({elapsed}초 경과)")

        time.sleep(3)
    else:
        raise TimeoutError("로그인 시간 초과! 다시 실행해주세요.")

    time.sleep(2)
    # 로그인 상태 저장 (다음 실행 시 자동 로그인)
    context.storage_state(path=str(STORAGE_PATH))
    print("[OK] 로그인 상태가 저장되었습니다!")


# ─────────────────────────────────────────────────────────────
# 저장글 목록 수집 (무한 스크롤)
# ─────────────────────────────────────────────────────────────

def _collect_saved_post_links(page: Page) -> list[str]:
    """저장글 페이지에서 개별 글 링크 수집."""
    print("\n[*] 저장글 목록을 수집합니다...")
    page.goto(config.THREADS_SAVED_URL)
    page.wait_for_load_state("networkidle")
    time.sleep(5)  # 충분히 대기

    collected_links: set[str] = set()
    prev_count = 0
    no_change_count = 0

    for attempt in range(config.MAX_SCROLL_ATTEMPTS):
        # 모든 앵커 태그에서 글 링크 패턴을 찾음
        # Threads 글 URL 패턴: /@username/post/xxx 또는 /t/xxx
        all_anchors = page.locator("a[href]").all()
        for a in all_anchors:
            try:
                href = a.get_attribute("href")
                if not href:
                    continue
                # /post/ 패턴 또는 /@user/post/ 패턴
                if "/post/" in href:
                    if href.startswith("/"):
                        href = config.THREADS_BASE_URL + href
                        
                    # URL 정규화: 쿼리스트링 제거 및 /media 제거
                    if "?" in href:
                        href = href.split("?")[0]
                    if "/media" in href:
                        href = href.replace("/media", "")
                    if href.endswith("/"):
                        href = href[:-1]
                        
                    collected_links.add(href)
            except Exception:
                continue

        current_count = len(collected_links)
        print(f"  스크롤 {attempt + 1}: {current_count}개 글 발견")

        if current_count == prev_count:
            no_change_count += 1
            if no_change_count >= 5:
                print("  더 이상 새로운 글이 없습니다.")
                break
        else:
            no_change_count = 0
        prev_count = current_count

        # 스크롤 다운
        page.evaluate("window.scrollBy(0, window.innerHeight * 2)")
        time.sleep(config.SCROLL_PAUSE_SEC)

    # /post/ 패턴이 없으면 다른 패턴 시도
    if not collected_links:
        print("  [*] /post/ 패턴으로 링크를 찾지 못했습니다. 다른 패턴 시도...")
        all_anchors = page.locator("a[href]").all()
        for a in all_anchors:
            try:
                href = a.get_attribute("href")
                if not href:
                    continue
                # /@username/ 패턴 (프로필 링크가 아닌 개별 글 링크)
                if re.match(r"/?@[\w.]+/\w+", href):
                    if href.startswith("/"):
                        href = config.THREADS_BASE_URL + href
                        
                    # URL 정규화: 쿼리스트링 제거 및 /media 제거
                    if "?" in href:
                        href = href.split("?")[0]
                    if "/media" in href:
                        href = href.replace("/media", "")
                    if href.endswith("/"):
                        href = href[:-1]
                        
                    collected_links.add(href)
            except Exception:
                continue
        print(f"  대체 패턴으로 {len(collected_links)}개 발견")

    # 디버그: 페이지에 있는 모든 링크 출력 (처음 20개)
    if not collected_links:
        print("\n  [DEBUG] 페이지의 링크 목록:")
        all_anchors = page.locator("a[href]").all()
        for i, a in enumerate(all_anchors[:30]):
            try:
                href = a.get_attribute("href")
                text = a.inner_text(timeout=1000)[:50]
                print(f"    {i+1}. href={href}  text={text}")
            except Exception:
                continue

    print(f"\n[*] 총 {len(collected_links)}개 저장글 링크 수집 완료")
    return list(collected_links)


# ─────────────────────────────────────────────────────────────
# 개별 글 상세 스크래핑
# ─────────────────────────────────────────────────────────────

def _scrape_single_post(page: Page, url: str, index: int) -> dict[str, Any] | None:
    """개별 글 방문 후 본문·작성자·댓글·이미지 추출."""
    try:
        page.goto(url, wait_until="networkidle", timeout=30000)
        time.sleep(3)
    except Exception as e:
        print(f"  [!] 글 로드 실패 ({url}): {e}")
        return None

    post_data: dict[str, Any] = {
        "url": url,
        "author": "",
        "text": "",
        "timestamp": "",
        "images": [],
        "comments": [],
    }

    try:
        # ── 작성자 추출 ──
        author_el = page.locator('a[href^="/@"] span').first
        if author_el.count() > 0:
            post_data["author"] = author_el.inner_text(timeout=3000)

        # ── 본문 추출 ──
        # 첫 번째 게시글 블록(원본 글) 내의 텍스트만 추출
        main_block = page.locator('div[data-pressable-container="true"]').first
        texts = []
        
        if main_block.count() > 0:
            text_blocks = main_block.locator('> div').all()
            for block in text_blocks:
                t = block.inner_text(timeout=3000).strip()
                if t and len(t) > 1:
                    texts.append(t)

        # 방법 2: 메인 콘텐츠 영역 (첫 번째 블록 실패 시)
        if not texts:
            main_el = page.locator('div[role="main"]')
            if main_el.count() > 0:
                all_text = main_el.first.inner_text(timeout=5000)
                # 너무 긴 전체 텍스트 대신 적당히 자름
                lines = [l.strip() for l in all_text.split("\n") if len(l.strip()) > 5]
                texts = lines[:20]

        # ── UI 쓰레기 값 제거 (인기순, 활동 보기 등) ──
        garbage_patterns = [
            re.compile(r'^인기순$'),
            re.compile(r'^활동 보기$'),
            re.compile(r'^더 보기$'),
            re.compile(r'^번역 보기$'),
            re.compile(r'^\d{4}-\d{2}-\d{2}.*$'), # 날짜 형태
            re.compile(r'^\d+$'), # 단순 숫자 (좋아요/댓글 수 등)
            re.compile(r'^/$'),
            re.compile(r'^답글 \d+개 보기$'),
            re.compile(r'^스레드$'),
        ]
        
        while texts:
            last_line = texts[-1].strip()
            if not last_line:
                texts.pop()
                continue
                
            is_garbage = False
            for p in garbage_patterns:
                if p.match(last_line):
                    is_garbage = True
                    break
                    
            if not is_garbage and post_data["author"] and last_line.lower() == post_data["author"].lower():
                is_garbage = True
                
            if is_garbage:
                texts.pop()
            else:
                break

        post_data["text"] = "\n".join(texts) if texts else "(본문 없음)"

        # ── 시간 추출 ──
        time_el = page.locator("time").first
        if time_el.count() > 0:
            post_data["timestamp"] = (
                time_el.get_attribute("datetime")
                or time_el.inner_text(timeout=3000)
            )

        # ── 이미지 추출 ──
        # Instagram CDN 이미지
        img_elements = page.locator('img[src*="cdninstagram"]').all()
        seen_srcs = set()
        for img in img_elements:
            src = img.get_attribute("src")
            if src and src not in seen_srcs:
                # 프로필 사진 제외 (보통 작은 크기)
                width = img.get_attribute("width")
                height = img.get_attribute("height")
                if width and int(width) < 50:
                    continue
                seen_srcs.add(src)
                post_data["images"].append(src)

        # ── 댓글 추출 ──
        reply_blocks = page.locator(
            'div[data-pressable-container="true"]'
        ).all()

        # 첫 번째는 원본 글, 나머지가 댓글
        for rb in reply_blocks[1:]:
            try:
                comment_author_el = rb.locator('a[href^="/@"] span').first
                comment_author = ""
                if comment_author_el.count() > 0:
                    comment_author = comment_author_el.inner_text(timeout=2000)

                comment_text = rb.inner_text(timeout=3000).strip()
                if comment_author and comment_text.startswith(comment_author):
                    comment_text = comment_text[len(comment_author):].strip()

                if comment_text and len(comment_text) > 1:
                    post_data["comments"].append({
                        "author": comment_author,
                        "text": comment_text,
                    })
            except Exception:
                continue

    except Exception as e:
        print(f"  [!] 글 파싱 오류 ({url}): {e}")

    return post_data


# ─────────────────────────────────────────────────────────────
# 공개 API
# ─────────────────────────────────────────────────────────────

def scrape_saved_posts() -> list[dict[str, Any]]:
    """Threads 저장글 전체 스크래핑. 메인 진입점."""
    posts: list[dict[str, Any]] = []

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False)

        # 저장된 로그인 상태가 있으면 사용
        if STORAGE_PATH.exists():
            print("[*] 저장된 로그인 상태를 불러옵니다...")
            context = browser.new_context(
                viewport={"width": 1280, "height": 900},
                locale="ko-KR",
                storage_state=str(STORAGE_PATH),
            )
        else:
            context = browser.new_context(
                viewport={"width": 1280, "height": 900},
                locale="ko-KR",
            )

        page = context.new_page()

        # 로그인 확인
        if STORAGE_PATH.exists():
            # 저장된 세션으로 접속 시도
            page.goto(config.THREADS_SAVED_URL)
            time.sleep(3)
            # 로그인 페이지로 리다이렉트되면 재로그인 필요
            if "login" in page.url:
                print("[!] 저장된 세션이 만료되었습니다. 다시 로그인해주세요.")
                _wait_for_login(page, context)
            else:
                print("[OK] 자동 로그인 성공!")
        else:
            _wait_for_login(page, context)

        # 저장글 링크 수집
        links = _collect_saved_post_links(page)

        if not links:
            print("[!] 저장된 글이 없습니다.")
            browser.close()
            return posts
            
        # ──────────────────────────────────────────────────
        # 중복 스크래핑 방지
        # ──────────────────────────────────────────────────
        crawled_urls = set()
        if CRAWLED_PATH.exists():
            content = CRAWLED_PATH.read_text(encoding="utf-8")
            crawled_urls = set(content.splitlines())
            
        new_links = [l for l in links if l not in crawled_urls]
        
        if not new_links:
            print(f"\n[*] 총 {len(links)}개의 저장글이 있지만, 모두 이미 크롤링되었습니다.")
            browser.close()
            return posts

        # 개별 글 스크래핑
        print(f"\n[*] {len(new_links)}개 글(새로운 글) 상세 스크래핑 시작...")
        for i, link in enumerate(new_links, 1):
            print(f"\n[{i}/{len(new_links)}] {link}")
            post = _scrape_single_post(page, link, i)
            if post:
                posts.append(post)
                print(f"  [OK] 작성자: {post['author']}, 본문: {post['text'][:50]}...")
                # 성공 시 파일에 기록하여 다음 번에 스킵되게 함
                with CRAWLED_PATH.open("a", encoding="utf-8") as f:
                    f.write(link + "\n")

        browser.close()

    print(f"\n[*] 총 {len(posts)}개 글(새로운 글) 스크래핑 완료!")
    return posts


if __name__ == "__main__":
    # 단독 실행 테스트
    results = scrape_saved_posts()
    print(json.dumps(results, ensure_ascii=False, indent=2))
