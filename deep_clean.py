import re
from pathlib import Path
import config

def deep_clean_duplicates():
    out_dir = config.OUTPUT_DIR
    fixed_count = 0
    
    for md_file in out_dir.rglob("*.md"):
        if md_file.name == "index.md": continue
        
        content = md_file.read_text(encoding="utf-8")
        
        if '\n## 댓글\n' not in content:
            continue
            
        blocks = content.split('\n## 댓글\n')
        main_part = blocks[0]
        comments_part = blocks[1]
        
        main_header = ""
        main_body = main_part
        if '\n---\n' in main_part:
            parts = main_part.split('\n---\n', 1)
            main_header = parts[0] + '\n---\n\n'
            main_body = parts[1]
            
        # Parse comments
        comment_blocks = comments_part.split('\n> **')
        
        cut_index = len(main_body)
        found_match = False
        
        for i, cb in enumerate(comment_blocks):
            if not cb.strip(): continue
            
            # Re-add prefix if lost
            if i > 0 or comments_part.startswith("> **"):
                cb = "> **" + cb
                
            # Remove header line and any tags/dates
            lines = cb.split('\n')
            content_lines = []
            for l in lines:
                l = l.strip()
                if l.startswith("> **"): continue
                if len(l) <= 10 and not re.search(r'[.!?]$', l): continue # skip generic short tags, dates, author names
                content_lines.append(l)
                
            if not content_lines: continue
            
            # Find the longest contiguous chunk of lines in this comment that exists in main_body
            # Actually, simply taking the first significant line of the comment and searching for it is powerful.
            # Let's try searching for the first 2 lines joined by \n
            
            chunk_to_search = ""
            if len(content_lines) >= 2:
                chunk_to_search = content_lines[0] + "\n" + content_lines[1]
            elif len(content_lines) == 1:
                chunk_to_search = content_lines[0]
                
            if len(chunk_to_search) < 20: 
                continue # ignore too short generic comments
                
            idx = main_body.find(chunk_to_search)
            if idx != -1:
                if idx < cut_index:
                    cut_index = idx
                    found_match = True
                    
            # Fallback: try searching just the first line if it's long enough
            if len(content_lines[0]) >= 30:
                idx = main_body.find(content_lines[0])
                if idx != -1:
                    if idx < cut_index:
                        cut_index = idx
                        found_match = True
                        
        if found_match and cut_index < len(main_body):
            # Truncate main body
            new_main_body = main_body[:cut_index].strip()
            
            new_content = main_header + new_main_body + "\n\n## 댓글\n" + comments_part
            
            if new_content != content:
                md_file.write_text(new_content, encoding="utf-8")
                print(f"딥 클린 중복 제거: {md_file.parent.name}/{md_file.name}")
                fixed_count += 1
                
    print(f"\n총 {fixed_count}개의 파일에서 본문 속 중복 댓글 블록 제거 완료!")

if __name__ == "__main__":
    deep_clean_duplicates()
