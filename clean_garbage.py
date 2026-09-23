import re
from pathlib import Path
import config

def clean_garbage_lines(lines, author):
    garbage_patterns = [
        re.compile(r'^인기순$'),
        re.compile(r'^활동 보기$'),
        re.compile(r'^더 보기.*'),
        re.compile(r'^번역 보기$'),
        re.compile(r'^\d{4}-\d{2}-\d{2}.*$'), # time
        re.compile(r'^[\d,]+[kK만천]?$'), # numbers 1, 8, 841, 1.5만 등
        re.compile(r'^/$'),
        re.compile(r'^답글 \d+개 보기$'),
        re.compile(r'^스레드$'),
        re.compile(r'^숨기기$'),
        re.compile(r'^신고하기$'),
        re.compile(r'^링크 복사$'),
    ]
    
    author_lower = author.lower() if author else ""
    tags = ["공부법", "AI Threads", "video games", "사주", "1인개발", "신비주의", "아마존KDP", "비즈니스 영어", "콜랙티오", "바이브코딩 Vibe coding", "끌어당김의법칙", "리얼리티트랜서핑"]

    cleaned = []
    for line in lines:
        s_line = line.strip()
        if not s_line:
            continue
            
        is_garbage = False
        
        for p in garbage_patterns:
            if p.match(s_line):
                is_garbage = True
                break
                
        if not is_garbage and author_lower and s_line.lower() == author_lower:
            is_garbage = True
            
        if not is_garbage and s_line in tags:
            is_garbage = True
            
        if not is_garbage:
            cleaned.append(line)
            
    return cleaned

def clean_all_md_files_full():
    out_dir = config.OUTPUT_DIR
    fixed_count = 0
    
    for md_file in out_dir.rglob("*.md"):
        if md_file.name == "index.md": continue
        
        content = md_file.read_text(encoding="utf-8")
        
        # 원본에서 작성자 추출
        author_match = re.search(r'- \*\*원본:\*\* .*?/@(.*?)/post/', content)
        author = author_match.group(1) if author_match else ""
        
        blocks = content.split('\n## 댓글\n')
        main_part = blocks[0]
        comments_part = blocks[1] if len(blocks) > 1 else ""
        
        # 1. 메인 본문 정리
        main_split = main_part.split('\n---\n')
        if len(main_split) >= 2:
            header = main_split[0]
            body_lines = main_split[1].split('\n')
            
            cleaned_body = clean_garbage_lines(body_lines, author)
            new_main = header + "\n---\n\n" + "\n".join(cleaned_body)
        else:
            new_main = main_part
            
        # 2. 댓글 정리
        new_comments = ""
        if comments_part:
            cleaned_comments_list = []
            comment_blocks = comments_part.split('\n> **')
            for i, cb in enumerate(comment_blocks):
                if i == 0 and not cb.strip(): 
                    continue
                
                if i > 0 or comments_part.startswith("> **"):
                    cb = "> **" + cb
                
                c_lines = cb.split('\n')
                c_lines = clean_garbage_lines(c_lines, author)
                cleaned_comments_list.append('\n'.join(c_lines))
                
            new_comments = "\n\n".join(cleaned_comments_list)
            
        new_content = new_main
        if new_comments.strip():
            new_content += "\n\n## 댓글\n\n" + new_comments.strip() + "\n"
            
        if new_content != content:
            md_file.write_text(new_content, encoding="utf-8")
            print(f"전체 가비지 청소 완료: {md_file.parent.name}/{md_file.name}")
            fixed_count += 1
            
    print(f"\n총 {fixed_count}개의 파일에서 중간중간 껴있는 모든 가비지 글자들 싹 청소 완료!")

if __name__ == "__main__":
    clean_all_md_files_full()
