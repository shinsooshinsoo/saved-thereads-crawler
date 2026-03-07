import re
import config
from pathlib import Path

def seed_crawled_urls():
    out_dir = config.OUTPUT_DIR
    crawled_path = config.BASE_DIR / ".crawled_urls.txt"
    
    existing_urls = set()
    if crawled_path.exists():
        existing_urls = set(crawled_path.read_text(encoding="utf-8").splitlines())
        
    found_urls = set()
    
    for md_file in out_dir.rglob("*.md"):
        if md_file.name == "index.md": continue
        
        content = md_file.read_text(encoding="utf-8")
        match = re.search(r'- \*\*원본:\*\* \[(https?://www\.threads\.net/.*?)\]', content)
        if match:
            url = match.group(1)
            # URL normalization matches scraper.py logic
            if "?" in url:
                url = url.split("?")[0]
            if "/media" in url:
                url = url.replace("/media", "")
            if url.endswith("/"):
                url = url[:-1]
                
            found_urls.add(url)
            
    # Combine and save
    new_urls = found_urls - existing_urls
    if new_urls:
        with crawled_path.open("a", encoding="utf-8") as f:
            for u in new_urls:
                f.write(u + "\n")
                
    print(f"기존 MD 파일 검색 완료!")
    print(f"새로 발견된 URL: {len(new_urls)}개 -> .crawled_urls.txt 에 기록완료.")
    print(f"총 누적 크롤링 기록 파일: {len(existing_urls) + len(new_urls)}개")

if __name__ == "__main__":
    seed_crawled_urls()
