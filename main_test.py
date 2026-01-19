import asyncio
from langgraph.graph import StateGraph, START, END
from typing import TypedDict
import operator
from typing import Annotated, TypedDict, Union

# Import nodes from your reconstructed files
from src.SinisterSixSystems.orchestration.agent_logic import router_node, text_expert_node
from src.SinisterSixSystems.orchestration.latex_validator import latex_validator_node
from src.SinisterSixSystems.orchestration.markdown_agent import markdown_generator_node
from src.SinisterSixSystems.utils.savers import latex_saver_node, markdown_saver_node
from src.SinisterSixSystems.utils.pdf_compiler import pdf_compiler_node

def reduce_latest(current, new):
    return new

class AgentState(TypedDict):
    # We wrap every key that could be updated in parallel with Annotated and our reducer
    user_input: Annotated[str, reduce_latest]
    text_content: Annotated[str, reduce_latest]
    markdown_content: Annotated[str, reduce_latest]
    file_path: Annotated[str, reduce_latest]
    pdf_path: Annotated[str, reduce_latest]
    
def build_sequential_graph():
    workflow = StateGraph(AgentState)

    # 1. ADD NODES
    workflow.add_node("router", router_node)
    workflow.add_node("text_expert", text_expert_node)
    workflow.add_node("validator", latex_validator_node)
    workflow.add_node("markdown_gen", markdown_generator_node)
    workflow.add_node("saver", latex_saver_node)
    workflow.add_node("markdown_saver", markdown_saver_node)
    workflow.add_node("pdf_compiler", pdf_compiler_node)

    # 2. DEFINE EDGES (Sequential Flow)
    workflow.add_edge(START, "router")
    workflow.add_edge("router", "text_expert")
    workflow.add_edge("text_expert", "validator")
    
    # Path for LaTeX/PDF
    workflow.add_edge("validator", "saver")
    workflow.add_edge("saver", "pdf_compiler")
    workflow.add_edge("pdf_compiler", END)
    
    # Path for Markdown/Web
    workflow.add_edge("validator", "markdown_gen")
    workflow.add_edge("markdown_gen", "markdown_saver")
    workflow.add_edge("markdown_saver", END)

    return workflow.compile()

async def run_task(prompt: str):
    app = build_sequential_graph()
    inputs = {"user_input": prompt}
    print(f"🚀 Starting Multi-Agent Task: {prompt}")
    print("=" * 50)
    
    async for event in app.astream(inputs, stream_mode="updates"):
        for node, values in event.items():
            print(f"✅ NODE FINISHED: {node}")

if __name__ == "__main__":
    task = "What is 3d calculus?"
    asyncio.run(run_task(task))