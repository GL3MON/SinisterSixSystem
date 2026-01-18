import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel, Field
from typing import List

load_dotenv()

class RouteSchema(BaseModel):
    route_type: str = Field(description="One of: 'type_1', 'type_2', 'type_3'")
    required_outputs: List[str] = Field(description="List of formats: text, audio, image, video, diagram")

def router_node(state):
    # Initialize the high-performance Gemini 2.5 Flash
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash", 
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0
    )
    
    # Bind the schema to the LLM
    structured_llm = llm.with_structured_output(RouteSchema)
    
    # YOUR SYSTEM PROMPT GOES HERE
    system_prompt = """
    Analyze the user input and follow these strict rules:
    1. If the user asks for a general explanation (e.g., 'What is...', 'Explain...'), 
       categorize as 'type_1' and set required_outputs to ['text', 'audio', 'image', 'video', 'diagram'].
    2. If the user asks for specific formats (e.g., 'give me a summary and audio'), 
       categorize as 'type_2' and list ONLY those formats.
    3. If the user mentions a document, file, or PDF, categorize as 'type_3'.
    """
    
    # Pass both the system instructions and the user input
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=state["user_input"])
    ]
    
    result = structured_llm.invoke(messages)
    
    return {
        "route_type": result.route_type,
        "required_outputs": result.required_outputs
    }