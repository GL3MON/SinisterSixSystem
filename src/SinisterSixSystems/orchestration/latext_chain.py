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
from src.SinisterSixSystems.orchestration.scoring_agent import scoring_node
from src.SinisterSixSystems.orchestration.lightning_optimizer import lightning_optimizer_node

def reduce_latest(current, new):
    return new

def latest(current, new):
    return new

class AgentState(TypedDict):
    user_input: Annotated[str, latest]
    text_content: Annotated[str, latest]
    score: Annotated[int, latest]      # Track content quality
    retry_count: Annotated[int, operator.add] # Ensure "one-time" run
    markdown_content: Annotated[str, latest]
    file_path: Annotated[str, latest]
    pdf_path: Annotated[str, latest]
    
from langgraph.graph import StateGraph, START, END

def build_sequential_graph():
    workflow = StateGraph(AgentState)

    # 1. ADD ALL NODES (Including Scoring and Optimizer)
    workflow.add_node("router", router_node)
    workflow.add_node("text_expert", text_expert_node)
    workflow.add_node("scoring", scoring_node)           # Evaluates efficiency
    workflow.add_node("lightning", lightning_optimizer_node) # Agent Lightning
    workflow.add_node("validator", latex_validator_node)
    workflow.add_node("markdown_gen", markdown_generator_node)
    workflow.add_node("saver", latex_saver_node)
    workflow.add_node("markdown_saver", markdown_saver_node)
    workflow.add_node("pdf_compiler", pdf_compiler_node)

    # 2. DEFINE EDGES (Sequential Flow with Conditional Branching)
    workflow.add_edge(START, "router")
    workflow.add_edge("router", "text_expert")
    workflow.add_edge("text_expert", "scoring") # Send content for evaluation

    # 3. CONDITIONAL ROUTING (The "One-Time" Logic)
    workflow.add_conditional_edges(
        "scoring",
        check_efficiency, # This function decides whether to optimize or finish
        {
            "optimize": "lightning", # Route to Agent Lightning if score is low
            "finish": "validator"     # Route to formatting if score is good
        }
    )

    # 4. REJOIN AFTER OPTIMIZATION
    workflow.add_edge("lightning", "validator") # Optimized code still needs validation

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

def check_efficiency(state):
    score = state.get("score", 0)
    retry = state.get("retry_count", 0)
    
    print(f"📊 [REPORT] Scoring Agent assigned: {score}/10")
    
    if score < 8 and retry < 1:
        print(f"⚠️  Efficiency below threshold. Sending to Agent Lightning...")
        return "optimize"
    
    print(f"✅ Efficiency meets threshold or max retries reached. Finalizing...")
    return "finish"

if __name__ == "__main__":
    task = "What is 3d calculus?"
    asyncio.run(run_task(task))