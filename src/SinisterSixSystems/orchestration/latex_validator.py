import re
from langchain_google_genai import ChatGoogleGenerativeAI

def latex_validator_node(state):
    print("📍 [DEBUG] Entered LaTeX Validator Node")
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)
    raw_latex = state.get("text_content", "")
    
    # STEP 1: Aggressive cleanup of hallucinated 'htbp]' text
    # This removes any instance of 'htbp]' not preceded by '['
    clean_latex = re.sub(r'(?<!\[)htbp\]', '', raw_latex)
    
    validation_prompt = f"""
    You are a LaTeX expert. Fix this code for MiKTeX:
    - CONSTRAIN PLACEMENT: Every \\begin{{figure}} MUST use the exact format \\begin{{figure}}[htbp].
    - STRIP STRAY TEXT: Ensure 'htbp]' never appears as plain text outside of brackets.
    - PREVENT OVERLAP: Use 'axis lines=middle' and 'enlargelimits=true' for all PGFPlots graphs.
    - SCALING: Ensure graph width is exactly 0.7\\textwidth.
    
    CONTENT: {clean_latex}
    """
    
    response = llm.invoke(validation_prompt)
    content = response.content

    # STEP 2: Final regex guardrail to force correct command syntax
    # This ensures any mangled figure tags are rewritten correctly
    content = re.sub(r'\\begin{figure}\[?.*?\]?', r'\\begin{figure}[htbp]', content)
    
    # Remove markdown backticks
    content = content.replace("```latex", "").replace("```", "").strip()
    
    if "\\documentclass" in content:
        content = content[content.find("\\documentclass"):]

    return {"text_content": content}