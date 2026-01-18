from typing import TypedDict, List, Annotated
import operator

class AgentState(TypedDict):
    user_input: str
    route_type: str
    required_outputs: List[str]
    text_content: str      # Holds the LaTeX code
    markdown_content: str  # NEW: Holds the website-ready text
    media_assets: dict
    language: str
    difficulty: str