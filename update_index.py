import config
from pathlib import Path

def generate_index():
    out_dir = config.OUTPUT_DIR
    lines = ["# Threads 저장글 아카이브\n"]
    
    files = sorted(out_dir.glob("*.md"))
    post_files = [f for f in files if f.name not in ["index.md", "github_주소_모음.md"]]
    
    lines.append(f"총 {len(post_files)}개의 글이 저장되어 있습니다.\n")
    lines.append("---")
    lines.append("")
    
    for f in post_files:
        name = f.stem
        rel_path = f.name
        lines.append(f"- [{name}](./{rel_path})")
        
    index_path = out_dir / "index.md"
    index_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"새로운 index.md 가 {index_path} 에 생성되었습니다! (총 {len(post_files)}개)")

if __name__ == "__main__":
    generate_index()
