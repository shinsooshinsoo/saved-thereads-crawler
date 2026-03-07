import os
import shutil
import time
from pathlib import Path
from google import genai
import config

def fix_classification():
    client = genai.Client(api_key=config.GEMINI_API_KEY)
    info_dir = config.OUTPUT_DIR / "정보"
    
    if not info_dir.exists():
        print("정보 폴더가 없습니다.")
        return
        
    md_files = list(info_dir.glob("*.md"))
    print(f"총 {len(md_files)}개의 MD 파일을 재분류합니다...")
    
    categories_created = set()
    
    for i, md_file in enumerate(md_files, 1):
        content = md_file.read_text(encoding="utf-8")
        
        # 본문 텍스트 추출 (--- 아래쪽 내용)
        parts = content.split("---")
        if len(parts) >= 3:
            text_to_classify = parts[2].strip()
        else:
            text_to_classify = content
            
        # 재분류
        prompt = (
            f"다음 글을 [{', '.join(config.CATEGORIES)}] 중 **정확히 하나**로 분류해줘.\n"
            f"카테고리 이름만 한 단어로 답해. 다른 말은 하지 마.\n\n"
            f"글:\n{text_to_classify[:1500]}"
        )
        
        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model=config.GEMINI_MODEL,
                    contents=prompt,
                )
                category = response.text.strip()
                break
            except Exception as e:
                err_msg = str(e)
                if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg:
                    print(f"  [!] Rate Limit 초과. 30초 대기... (재시도 {attempt+1})")
                    time.sleep(30)
                    continue
                category = "정보"
                break
        else:
            category = "정보"
            
        print(f"[{i}/{len(md_files)}] {md_file.name[:20]}... -> {category}")
        
        # 잘못된 카테고리면 기본값
        if category not in config.CATEGORIES:
            continue
            
        if category == "정보":
            continue
            
        # 파일 내용에 적힌 주제 업데이트
        updated_content = content.replace("- **주제:** 정보", f"- **주제:** {category}")
        
        # 파일 이동
        target_dir = config.OUTPUT_DIR / category
        target_dir.mkdir(exist_ok=True)
        img_target_dir = target_dir / "images"
        img_target_dir.mkdir(exist_ok=True)
        
        # 안의 이미지 경로들도 옮겨야 함 (간단하게 파일 시스템만 이동)
        # 이미지 파일들 옮기기
        import re
        images = re.findall(r'!\[.*?\]\(\.\/images\/(.*?)\)', updated_content)
        for img in images:
            img_src = info_dir / "images" / img
            img_dst = img_target_dir / img
            if img_src.exists():
                shutil.copy(img_src, img_dst) # 유지방식
                
        # 새 카테고리로 쓰기
        new_md_path = target_dir / md_file.name
        new_md_path.write_text(updated_content, encoding="utf-8")
        
        # 기존 파일 삭제
        md_file.unlink()
        
        time.sleep(config.CLASSIFY_DELAY_SEC)
        
    print("\n재분류 완료! index.md를 새로 생성하려면 python main.py를 변경된 코드로 수행하거나 수동으로 진행하면 됩니다.")

if __name__ == "__main__":
    fix_classification()
