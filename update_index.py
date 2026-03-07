import config
from pathlib import Path

def generate_index():
    out_dir = config.OUTPUT_DIR
    lines = ["# Threads 저장글 아카이브\n"]
    
    total_count = 0
    grouped = {cat: [] for cat in config.CATEGORIES}
    
    # 각 카테고리 폴더 순회
    for cat in config.CATEGORIES:
        cat_dir = out_dir / cat
        if cat_dir.exists():
            for md_file in cat_dir.glob("*.md"):
                if md_file.name == "index.md":
                    continue
                # 파일 안에서 제목(--- 아래 첫 줄 또는 파일명) 찾거나 생략
                name = md_file.stem
                # 상대 경로
                rel_path = f"{cat}/{md_file.name}"
                grouped[cat].append((name, rel_path))
                total_count += 1
                
    for cat in config.CATEGORIES:
        files = grouped[cat]
        if files:
            lines.append(f"## {cat} ({len(files)})\n")
            for name, path in files:
                lines.append(f"- [{name}](./{path})")
            lines.append("")
            
    lines.insert(1, f"총 {total_count}개의 글이 카테고리별로 분류되었습니다.\n")
    
    index_path = out_dir / "index.md"
    index_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"새로운 index.md 가 {index_path} 에 생성되었습니다!")

if __name__ == "__main__":
    generate_index()
