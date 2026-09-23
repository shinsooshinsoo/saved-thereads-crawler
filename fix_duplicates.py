import re
from pathlib import Path
import config

def remove_duplicated_comments_from_main():
    out_dir = config.OUTPUT_DIR
    fixed_count = 0
    
    for md_file in out_dir.rglob("*.md"):
        if md_file.name == "index.md": continue
        
        content = md_file.read_text(encoding="utf-8")
        if '\n## 댓글\n' not in content:
            continue
            
        main_part, comments_part = content.split('\n## 댓글\n', 1)
        
        # 1. 댓글 작성자 목록 수집
        comment_authors = set()
        for line in comments_part.split('\n'):
            m = re.match(r'> \*\*([\w._]+):\*\*', line)
            if m:
                comment_authors.add(m.group(1).lower())
                
        # 2. 첫 번째로 의미 있는(길이가 긴) 댓글 텍스트 찾기
        lines_in_comments = comments_part.split('\n')
        anchor = None
        for line in lines_in_comments:
            line = line.strip()
            if not line or line.startswith("> **"):
                continue
            if len(line.replace(" ", "")) >= 10:
                anchor = line
                break
                
        if not anchor:
            continue
            
        # 3. 본문에서 해당 텍스트 위치 찾기 (마지막으로 등장하는 위치)
        idx = main_part.rfind(anchor)
        if idx == -1:
            continue
            
        # 중복이 시작되는 지점 이전까지 자름
        head_str = main_part[:idx]
        head_lines = head_str.split('\n')
        
        # 4. 쓰레기값(UI 요소, 작성자, 날짜 등) 제거 루프 (뒤에서부터)
        garbage_patterns = [
            re.compile(r'^인기순$'),
            re.compile(r'^활동 보기$'),
            re.compile(r'^더 보기$'),
            re.compile(r'^번역 보기$'),
            re.compile(r'^\d{4}-\d{2}-\d{2}.*$'), # date
            re.compile(r'^\d+$'), # pure digits (1, 5, etc)
            re.compile(r'^/$'),   # slash
            re.compile(r'^답글 \d+개 보기$'),
            re.compile(r'^스레드$'),
        ]
        
        # 원본 작성자 이름 추출
        author_match = re.search(r'- \*\*원본:\*\* .*?/@(.*?)/post/', main_part)
        author_name = author_match.group(1).lower() if author_match else ""
        
        original_length = len(head_lines)
        
        while head_lines:
            last_line = head_lines[-1].strip()
            if not last_line:
                head_lines.pop()
                continue
                
            is_garbage = False
            
            # 패턴 매칭
            for p in garbage_patterns:
                if p.match(last_line):
                    is_garbage = True
                    break
                    
            # 단일 단어(작성자 이름일 가능성)
            if not is_garbage and len(last_line.split()) == 1:
                ll_lower = last_line.lower()
                if ll_lower == author_name or ll_lower in comment_authors:
                    is_garbage = True
                    
            if is_garbage:
                head_lines.pop()
            else:
                break
                
        # 만약 본문이 전부 지워졌다면(원래 본문이 없었던 경우 등), 로직 취소
        if not head_lines:
            continue
            
        new_main_part = '\n'.join(head_lines).strip()
        new_content = new_main_part + "\n\n## 댓글\n" + comments_part
        
        if new_content != content:
            md_file.write_text(new_content, encoding="utf-8")
            print(f"중복 제거: {md_file.parent.name}/{md_file.name}")
            fixed_count += 1

    print(f"\n총 {fixed_count}개의 파일에서 중복된 본문 꼬리 부분(댓글) 삭제 완료!")

if __name__ == "__main__":
    remove_duplicated_comments_from_main()
