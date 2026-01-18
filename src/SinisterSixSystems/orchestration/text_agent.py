import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

def text_expert_node(state):
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash", 
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0.3 # Lower temperature for structural accuracy
    )
    
    topic = state["user_input"]
    language = state.get("language", "English")
    
    # System Instruction for LaTeX Tutoring
    system_instruction = f"""
    You are an Academic LaTeX Tutor. Your goal is to create an in-depth, formal educational document in LaTeX.
    Topic: {topic}
    Language: {language}
    
    Strict Structural Requirements:
    1. Use 'article' documentclass.
    2. Include \\usepackage{{amsmath, amssymb}} for formulas.
    3. Use \\section{{}} for main headings and \\subsection{{}} for sub-points.
    4. Formulas MUST be in [ ... ] or \\begin{{equation}} environments.
    5. Include a 'Worked Examples' section with step-by-step solutions using the 'enumerate' environment.
    6. Ensure all special characters like % or $ are properly escaped unless used for LaTeX syntax.
    7. Return ONLY the raw LaTeX code, starting from \\documentclass and ending with \\end{{document}}.
    """
    
    response = llm.invoke(system_instruction)
    
    # We store the LaTeX code in the state
    return {"text_content": response.content}