import os
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

load_dotenv()
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)

def router_node(state):
    print("📍 [DEBUG] Entered Router Node")
    return state

def text_expert_node(state):
    print("📍 [DEBUG] Entered Text Expert Node")
    
    prompt = f"""
    Act as an Academic LaTeX Expert. Create a lesson for: {state['user_input']}.
    
    **CONTENT REQUIREMENTS:**
    - Concept explanation, worked examples, and 3-level exercises.
    - Q1: Solution, Q2: Hint.

    **INTERNAL GRAPH (PGFPLOTS) SPECS:**
    - Include exactly one graph using \\begin{{axis}}.
    - Use 'axis lines=middle' and 'enlargelimits' to prevent label overlapping.
    - Use 'width=0.7\\textwidth, height=6cm'.
    - Wrap in \\begin{{figure}}[htbp] (no extra brackets).

    **TECHNICAL:**
    - Include \\usepackage{{pgfplots}} and \\pgfplotsset{{compat=1.18}}.
    """
    
    response = llm.invoke(prompt)
    return {"text_content": response.content}