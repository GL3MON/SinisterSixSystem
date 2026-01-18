import os
import asyncio
from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END

# Import your state and nodes
from src.SinisterSixSystems.orchestration.state import AgentState
from src.SinisterSixSystems.orchestration.router import router_node
from src.SinisterSixSystems.orchestration.text_agent import text_expert_node
from src.SinisterSixSystems.utils.latex_handler import save_latex_file
from src.SinisterSixSystems.utils.pdf_compiler import compile_latex_to_pdf
from src.SinisterSixSystems.orchestration.latex_validator import latex_validator_node
from src.SinisterSixSystems.utils.markdown_handler import save_markdown_file
from src.SinisterSixSystems.orchestration.markdown_agent import markdown_generator_node

load_dotenv()

# --- THE SAVER NODE FUNCTION ---
def latex_saver_node(state: AgentState):
    print("📍 [DEBUG] Entered Saver Node")
    content = state.get("text_content")
    
    if content:
        # Create a clean filename from the prompt
        topic_name = state["user_input"][:15].strip().replace(" ", "_")
        file_path = save_latex_file(content, filename=f"{topic_name}.tex")
        print(f"✅ [DEBUG] LaTeX saved at: {file_path}")
    else:
        print("❌ [DEBUG] No text_content found in state!")
        
    return state

# --- GRAPH BUILDER ---
def build_test_graph():
    # 1. Initialize with State
    workflow = StateGraph(AgentState)

    # 2. ADD NODES FIRST (Crucial: Define the nodes before the edges)
    workflow.add_node("router", router_node)
    workflow.add_node("text_expert", text_expert_node)
    workflow.add_node("saver", latex_saver_node)

    # 3. ADD EDGES (Connecting the defined nodes)
    workflow.add_edge(START, "router")
    workflow.add_edge("router", "text_expert")
    workflow.add_edge("text_expert", "saver")
    workflow.add_edge("saver", END)

    # 4. Compile
    return workflow.compile()

async def run_test(user_prompt: str):
    app = build_test_graph()
    inputs = {"user_input": user_prompt}
    
    print(f"\n🚀 Starting Multi-Agent Task: {user_prompt}\n" + "="*50)
    
    async for event in app.astream(inputs, stream_mode="updates"):
        for node_name, output in event.items():
            print(f"\n✅ NODE FINISHED: {node_name}")
            # Optional: print snippet of output to console
    
    print("\n" + "="*50 + "\n🎯 Task Sequence Complete.")

# 1. Define the Node
def pdf_compiler_node(state):
    print("📍 [DEBUG] Entered PDF Compiler Node")
    
    # Updated path to the artifacts folder
    topic_name = state["user_input"][:15].strip().replace(" ", "_")
    base_dir = os.getcwd() # Gets C:\Users\admin\SinisterSixSystem
    tex_path = os.path.join(base_dir, "artifacts", "latex", f"{topic_name}.tex")
    
    # Trigger MiKTeX compilation
    pdf_path = compile_latex_to_pdf(tex_path)
    
    return {"media_assets": {"pdf_path": pdf_path}}

# 2. Add to build_test_graph()
def build_test_graph():
    workflow = StateGraph(AgentState)

    # 1. ADD ALL NODES
    workflow.add_node("router", router_node)
    workflow.add_node("text_expert", text_expert_node)
    workflow.add_node("validator", latex_validator_node) # Crucial for clean code
    workflow.add_node("saver", latex_saver_node)
    workflow.add_node("pdf_compiler", pdf_compiler_node)
    workflow.add_node("markdown_gen", markdown_generator_node)

    # 2. DEFINE THE EDGES
    workflow.add_edge(START, "router")
    workflow.add_edge("router", "text_expert")
    workflow.add_edge("text_expert", "validator") # Clean the content first

    # --- PARALLEL FAN-OUT ---
    # From the validator, we branch into two separate paths:
    workflow.add_edge("validator", "saver")        # Path A: Towards PDF
    workflow.add_edge("validator", "markdown_gen") # Path B: Towards Website Markdown

    # --- PATH A: PDF Pipeline ---
    workflow.add_edge("saver", "pdf_compiler")
    workflow.add_edge("pdf_compiler", END)

    # --- PATH B: Markdown Pipeline ---
    workflow.add_edge("markdown_gen", END)

    return workflow.compile()

def markdown_saver_node(state: AgentState):
    print("📍 [DEBUG] Entered Markdown Saver Node")
    content = state.get("markdown_content")
    
    if content:
        # Create a clean filename
        topic_name = state["user_input"][:15].strip().replace(" ", "_")
        file_path = save_markdown_file(content, filename=f"{topic_name}.md")
        print(f"✅ [DEBUG] Markdown saved at: {file_path}")
    else:
        print("❌ [DEBUG] No markdown_content found in state!")
        
    return state

def build_test_graph():
    workflow = StateGraph(AgentState)

    # 1. ADD NODES
    workflow.add_node("router", router_node)
    workflow.add_node("text_expert", text_expert_node)
    workflow.add_node("validator", latex_validator_node)
    workflow.add_node("saver", latex_saver_node)
    workflow.add_node("pdf_compiler", pdf_compiler_node)
    workflow.add_node("markdown_gen", markdown_generator_node)
    workflow.add_node("markdown_saver", markdown_saver_node) # NEW NODE

    # 2. DEFINE EDGES
    workflow.add_edge(START, "router")
    workflow.add_edge("router", "text_expert")
    workflow.add_edge("text_expert", "validator")

    # --- PARALLEL BRANCHING ---
    workflow.add_edge("validator", "saver")          # Towards PDF
    workflow.add_edge("validator", "markdown_gen")   # Towards Website Content

    # --- PDF PATH ---
    workflow.add_edge("saver", "pdf_compiler")
    workflow.add_edge("pdf_compiler", END)

    # --- MARKDOWN PATH ---
    workflow.add_edge("markdown_gen", "markdown_saver") # Generate -> Save
    workflow.add_edge("markdown_saver", END)            # Save -> Finish

    return workflow.compile()

if __name__ == "__main__":
    asyncio.run(run_test("What is photosynthesis?"))