import os

def save_markdown_file(content, filename):
    base_dir = os.getcwd()
    output_dir = os.path.join(base_dir, "artifacts", "markdown")
    os.makedirs(output_dir, exist_ok=True)
    
    file_path = os.path.join(output_dir, filename)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    print(f"✅ Markdown saved to: {file_path}")
    return file_path