import os
import re
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

load_dotenv()

def markdown_generator_node(state):
    print("📍 [DEBUG] Entered Markdown Generator Node")

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0
    )

    validated_latex = state.get("text_content", "")

    markdown_prompt = f"""
You are a Web Content Writer. Extract ONLY the theoretical explanation.

STRICT RULES:
1. NO FORMULAS: Remove all math environments entirely.
2. Theory Only: Focus on conceptual definitions.
3. Headings: Use '#' for sections and '##' for sub-sections.
4. NO WRAPPERS: Do not output the word 'markdown', do not use backticks.

INPUT:
{validated_latex}
"""

    response = llm.invoke(markdown_prompt)
    content = response.content

    # ================= ABSOLUTE CLEANUP =================

    # 1. Remove BOM / zero-width / invisible characters
    content = content.lstrip("\ufeff\u200b\u200c\u200d\n\r\t ")

    # 2. REMOVE FIRST LINE IF IT IS ```markdown OR ```
    content = re.sub(
        r'(?i)^\s*```markdown\s*\n?',
        '',
        content
    )

    content = re.sub(
        r'(?i)^\s*```\s*\n?',
        '',
        content
    )

    # 3. Remove closing ```
    content = re.sub(
        r'\n?\s*```\s*$',
        '',
        content
    )

    # 4. Remove ANY remaining fenced blocks (safety net)
    content = re.sub(
        r'```(?:markdown)?[\s\S]*?```',
        lambda m: m.group(0).replace('```', ''),
        content,
        flags=re.IGNORECASE
    )

    # 5. Remove lines like "# Markdown"
    content = re.sub(
        r'(?im)^\s*#\s*markdown\s*$',
        '',
        content
    )

    # 6. Final trim
    clean_content = content.strip()

    return {"markdown_content": clean_content}