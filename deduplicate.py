import os
import re
from pathlib import Path
import config
from update_index import generate_index

def deduplicate():
    out_dir = config.OUTPUT_DIR
    
    seen_suffixes = set()
    deleted_count = 0
    kept_count = 0
    
    # 각 카테고리 폴더 순회
    for cat in config.CATEGORIES:
        cat_dir = out_dir / cat
        if not cat_dir.exists():
            continue
            
        md_files = sorted(list(cat_dir.glob("*.md")))
        
        for md_file in md_files:
            if md_file.name == "index.md":
                continue
                
            # 파일명에서 post_XXX_ 부분을 제외한 부분 추출
            # 예: post_008_darkcommis_2026-01-26_4_COLORS...md
            # -> darkcommis_2026-01-26_4_COLORS...md
            match = re.match(r'^post_\d+_(.+)$', md_file.name)
            
            if match:
                suffix = match.group(1)
                
                # 완전히 동일한 제목의 파일이 이미 있다면 삭제
                if suffix in seen_suffixes:
                    print(f"중복 삭제: [{cat}] {md_file.name}")
                    md_file.unlink()
                    deleted_count += 1
                else:
                    seen_suffixes.add(suffix)
                    kept_count += 1
            else:
                # 패턴이 다를 경우 전체 이름으로 중복 체크
                if md_file.name in seen_suffixes:
                    md_file.unlink()
                    deleted_count += 1
                else:
                    seen_suffixes.add(md_file.name)
                    kept_count += 1
                
    print(f"\n총 {deleted_count}개의 중복 파일 삭제 완료. {kept_count}개 유지.")
    
    print("\nindex.md 파일을 새로 생성합니다...")
    generate_index()

if __name__ == "__main__":
    deduplicate()
