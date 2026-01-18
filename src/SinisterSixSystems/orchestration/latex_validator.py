import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

def latex_validator_node(state):
    print("📍 [DEBUG] Entered LaTeX Validator Node")
    
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash", 
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0
    )
    
    raw_latex = state.get("text_content", "")
    
    validation_prompt = f"""
    You are a LaTeX Quality Assurance Agent. Your job is to fix syntax errors in the following LaTeX code to ensure it compiles perfectly in MiKTeX.

    **STRICT CORRECTION RULES:**
    1. **Fix Math Delimiters:** Change all instances of `[` and `]` used for equations to `\\[` and `\\]`.
    2. **Fix Text in Math Mode:** Any plain text found inside math environments (like "Sincetheacceleration") must be wrapped in \\text{{ }} with proper spacing.
    3. **Remove Source Markers:** Delete all occurrences of `` (where x is a number). These cause blank pages and "Missing \\begin{{document}}" errors.
    4. **Ensure Preamble:** Verify \\documentclass, \\usepackage{{amsmath}}, and \\begin{{document}} are present.
    5. **No Markdown:** Do not wrap the output in markdown code blocks. Return ONLY the raw LaTeX string.

    **RAW LATEX TO FIX:**
    {raw_latex}
    """
    
    response = llm.invoke(validation_prompt)
    
    # Update the state with the cleaned LaTeX code
    return {"text_content": response.content}