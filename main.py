from langgraph.graph import StateGraph, START, END
from src.SinisterSixSystems.orchestration.state import AgentState
from src.SinisterSixSystems.orchestration.router import router_node
from src.SinisterSixSystems.orchestration.text_agent import text_expert_node

# 1. Initialize Graph
workflow = StateGraph(AgentState)

# 2. Add Nodes
workflow.add_node("router", router_node)
workflow.add_node("text_expert", text_expert_node)
workflow.add_node("saver", latex_saver_node)
# 3. Define Flow
workflow.add_edge(START, "router")
workflow.add_edge("router", "text_expert")
workflow.add_edge("text_expert", "saver")
workflow.add_edge("saver", END)
# 4. Compile
app = workflow.compile()

# Example Execution
if __name__ == "__main__":
    inputs = {"user_input": "Explain how photosynthesis works"}
    for output in app.stream(inputs):
        print(output)

# 1. Define a new node function
def latex_saver_node(state):
    content = state.get("text_content")
    if content:
        save_latex_file(content, filename="lesson_output.tex")
    return state # No state changes needed, just a side effect