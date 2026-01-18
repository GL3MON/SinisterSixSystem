from typing import TypedDict, List, Annotated
import operator

class AgentState(TypedDict):
    # Core inputs
    user_input: str
    file_path: str  # For Type 3: PDF uploads
    
    # Routing Decisions
    route_type: str  # "type_1", "type_2", or "type_3"
    required_outputs: List[str]  # ["text", "audio", "video", "diagram"]
    
    # Generated Content
    text_content: str
    media_assets: dict  # Paths to generated images, audio, etc.
    
    # Meta
    language: str
    difficulty: str