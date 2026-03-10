import os
import re
import time
from pathlib import Path
import config
from google import genai
from update_index import generate_index

def clean_rename_with_ai():
    client = genai.Client(api_key=config.GEMINI_API_KEY)
    out_dir = config.OUTPUT_DIR
    
    # 1. Collect all MD files
    md_files = []
    for md_file in out_dir.rglob("*.md"):
        if md_file.name == "index.md": continue
        # 이미 이름이 바뀐 파일('post_'로 시작하지 않는 파일)은 건너뜀
        if not md_file.name.startswith("post_"): 
            continue
        md_files.append(md_file)
        
    if not md_files:
        print("새로 이름을 변경할 파일이 없습니다. (모두 이미 변경됨)")
        return
        
    print(f"총 {len(md_files)}개의 파일을 숫자를 제거한 간결한 제목으로 변경합니다.")
    
    rename_count = 0
    used_names = set()
    
    for i, md_file in enumerate(md_files, 1):
        content = md_file.read_text(encoding="utf-8")
        
        # Extract body content (below ---)
        body = content
        if "---" in content:
            parts = content.split("---")
            if len(parts) >= 3:
                body = parts[2].strip()
        
        # 2. Ask Gemini for an extremely concise and intuitive title
        prompt = (
            f"다음은 Threads 게시글 내용이야. 숫자를 전혀 포함하지 말고, 이 내용을 가장 잘 나타내는 **아주 간결하고 직관적인 제목**을 딱 하나만 지어줘.\n"
            f"- 반드시 한글 또는 영문으로만 구성할 것 (숫자 제외)\n"
            f"- 공백 포함 15자 이내\n"
            f"- 조사(~는, ~가 등)를 생략하고 핵심 키워드 중심으로 지을 것\n"
            f"- 제목만 말할 것\n\n"
            f"내용:\n{body[:1000]}"
        )
        
        new_title = ""
        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model=config.GEMINI_MODEL,
                    contents=prompt,
                )
                raw_title = response.text.strip().replace('"', '').replace("'", "")
                # Remove any remaining numbers and special chars
                clean_title = re.sub(r'[0-9]', '', raw_title)
                clean_title = re.sub(r'[\\/*?:"<>|]', '', clean_title).strip()
                clean_title = clean_title.replace(" ", "_")
                new_title = clean_title
                if new_title:
                    break
            except Exception as e:
                if "429" in str(e):
                    time.sleep(10)
                    continue
                break
        
        if not new_title:
            new_title = "제목없음"
            
        # 3. Handle duplicates
        base_name = new_title
        counter = 1
        while f"{md_file.parent}/{new_title}.md" in used_names or (md_file.parent / f"{new_title}.md").exists():
            if (md_file.parent / f"{new_title}.md").exists() and (md_file.parent / f"{new_title}.md") == md_file:
                break
            new_title = f"{base_name}_{counter}"
            counter += 1
            
        new_filename = f"{new_title}.md"
        new_path = md_file.parent / new_filename
        used_names.add(f"{md_file.parent}/{new_title}.md")
        
        if md_file != new_path:
            try:
                os.rename(md_file, new_path)
                print(f"[{i}/{len(md_files)}] {md_file.name} \n   -> {new_filename}")
                rename_count += 1
            except Exception as e:
                print(f"  [!] 오류: {e}")
                
        # API Delay
        time.sleep(config.CLASSIFY_DELAY_SEC)
        
    print(f"\n총 {rename_count}개의 파일을 간결한 제목으로 정리했습니다!")
    print("인덱스를 갱신합니다...")
    generate_index()

if __name__ == "__main__":
    clean_rename_with_ai()
