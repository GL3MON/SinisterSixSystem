import os
import re

def sanitize_filename(text):
    """Removes illegal Windows characters from filenames."""
    # Keeps only alphanumeric, space, and underscore
    clean = re.sub(r'[^\w\s-]', '', text[:30]).strip()
    return clean.replace(' ', '_')

def latex_saver_node(state):
    """Saves the validated LaTeX code to a .tex file."""
    print("📍 [DEBUG] Entered LaTeX Saver Node")
    content = state.get("text_content", "")
    filename = sanitize_filename(state["user_input"]) + ".tex"
    path = os.path.join("artifacts", "latex", filename)
    
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    
    print(f"✅ LaTeX saved to: {path}")
    return {"file_path": path}

def markdown_saver_node(state):
    """Saves the clean markdown content to an .md file."""
    print("📍 [DEBUG] Entered Markdown Saver Node")
    content = state.get("markdown_content", "")
    filename = sanitize_filename(state["user_input"]) + ".md"
    path = os.path.join("artifacts", "markdown", filename)
    
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    
    print(f"✅ Markdown saved to: {path}")
    return state