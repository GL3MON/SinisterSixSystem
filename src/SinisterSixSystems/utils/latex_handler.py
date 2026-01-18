import os

def save_latex_file(content, filename="lesson_output.tex"):
    # Define the new artifacts path
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    output_dir = os.path.join(base_dir, "artifacts", "latex")
    
    # Create the directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    file_path = os.path.join(output_dir, filename)
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    print(f"✅ LaTeX source saved to: {file_path}")
    return file_path