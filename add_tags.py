import os
import re
import time
from pathlib import Path
import config

def add_tags_to_posts():
    out_dir = config.OUTPUT_DIR
    
    md_files = []
    for md_file in out_dir.rglob("*.md"):
        if md_file.name == "index.md": continue
        md_files.append(md_file)
        
    print(f"총 {len(md_files)}개의 마크다운 파일을 검사하여 태그를 추가합니다...")
    
    tagged_count = 0
    
    for i, md_file in enumerate(md_files, 1):
        content = md_file.read_text(encoding="utf-8")
        
        # 이미 태그가 추가된 파일이면 건너뛰기
        if "\n- **태그:**" in content:
            continue
            
        # 본문 내용 추출 (--- 아래쪽 내용)
        body = content
        if "---" in content:
            parts = content.split("---")
            if len(parts) >= 3:
                body = parts[2].strip()
        
        # 2. Gemini에게 태그 추천받기
        prompt = (
            f"다음은 Threads(스레드) 게시글의 내용이야. 이 글의 핵심적인 키워드 3~5개를 해시태그 형식으로 추출해줘.\n"
            f"- 반드시 '#키워드1 #키워드2 #키워드3' 형태로 띄어쓰기로 구분해서 한 줄로 출력할 것.\n"
            f"- 예시: #인공지능 #생산성 #구글\n"
            f"- 다른 부연 설명은 전혀 하지 말고, 오직 해시태그들만 말할 것.\n\n"
            f"내용:\n{body[:1500]}"
        )
        
        new_tags = ""
        for attempt in range(3):
            try:
                response_text = config.generate_content(prompt)
                raw_tags = response_text.strip()
                # 여러 줄일 경우 첫 줄만 혹은 개행을 공백으로 변경
                raw_tags = raw_tags.replace("\n", " ")
                
                # 안전장치: #로 시작하지 않는 단어가 있으면 #를 붙임, 아니면 그냥 정규표현식으로 추출
                words = raw_tags.split()
                clean_tags = []
                for w in words:
                    w = w.strip()
                    if not w: continue
                    if not w.startswith("#"):
                        w = "#" + w
                    clean_tags.append(w)
                
                new_tags = " ".join(clean_tags[:5])  # 최대 5개까지만
                break
            except Exception as e:
                if "429" in str(e) or "503" in str(e):
                    print(f"  [!] 서버 바쁨/제한: 5초 대기... ({e})")
                    time.sleep(5)
                    continue
                else:
                    print(f"  [!] LLM 오류: {e}")
                    break
        
        if not new_tags:
            print(f"[{i}/{len(md_files)}] 태그 생성 실패: {md_file.name}")
            continue
            
        # 3. 마크다운 파일 내용 수정 (주제: ... 바로 아랫줄에 삽입)
        # '- **주제:** 기술' 패턴 찾기
        pattern = r"(- \*\*주제:\*\* [^\n]+)"
        match = re.search(pattern, content)
        if match:
            # 매칭된 줄 바로 밑에 태그 삽입
            replacement = match.group(1) + f"\n- **태그:** {new_tags}"
            new_content = content.replace(match.group(1), replacement, 1)
            
            md_file.write_text(new_content, encoding="utf-8")
            print(f"[{i}/{len(md_files)}] 태그 추가 완료: {md_file.name} -> {new_tags}")
            tagged_count += 1
        else:
            print(f"[{i}/{len(md_files)}] 스킵 (주제 라인을 찾지 못함): {md_file.name}")
            
        # API 딜레이
        time.sleep(config.CLASSIFY_DELAY_SEC)
        
    print(f"\n완료! 총 {tagged_count}개의 파일에 AI가 생성한 태그(#해시태그)를 삽입했습니다.")

if __name__ == "__main__":
    add_tags_to_posts()
