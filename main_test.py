import os
import asyncio
from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END

# Import your state and nodes
from src.SinisterSixSystems.orchestration.state import AgentState
from src.SinisterSixSystems.orchestration.router import router_node
from src.SinisterSixSystems.orchestration.text_agent import text_expert_node
from src.SinisterSixSystems.utils.latex_handler import save_latex_file

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

if __name__ == "__main__":
    asyncio.run(run_test("Explain Newtons law of motions"))