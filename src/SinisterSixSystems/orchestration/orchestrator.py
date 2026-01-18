from SinisterSixSystems.logging import logger
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import START, END, StateGraph
from langchain.tools import tool

from SinisterSixSystems.orchestration.graph_generator import GraphGenerator
from SinisterSixSystems.constants import ORCHESTRATOR_PROMPT

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.messages import ToolMessage

from dotenv import load_dotenv
from typing import TypedDict, List
import os

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

class OrchestratorState(TypedDict):
    messages: list


class Orchestrator:
    def __init__(self):
        self.output_parser = StrOutputParser()
        self.model = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.0, api_key=GOOGLE_API_KEY)
        
        self.tools = [
            self.graph_tool,
            self.audio_generation_tool
        ]

        self.model_with_tools = self.model.bind_tools(self.tools)
    
    @staticmethod
    @tool
    def graph_tool(query: str) -> str:
        """
        Creates mathematical plots based on the provided query using matplotlib and returns the file path of the saved plot image.
        Args:
            query (str): The query containing details about the plot to be created.
        Returns:
            str: Status message indicating completion of graph generation.
        """

        graph_generator = GraphGenerator()
        workflow_graph = graph_generator.compile()

        logger.info(f"Graph Tool Invoked with Query: {query}")

        initial_state = {
            "query": query,
            "extracted_code": "",
            "retry_count": 0,
            "error_message": ""
        }

        for output in workflow_graph.stream(initial_state):
            for _, value in output.items():
                print(value)
        
        logger.info(f"Graph Tool Output: {value}")

        return "Graph generation completed."
        

    @staticmethod
    @tool
    def audio_generation_tool(mode: str) -> str:
        """
        Generates audio based on the provided mode using the AudioAgent component.
        Args:
            mode (str): The mode for audio generation, either 'tutor' or 'story'.
        Returns:
            str: Status message indicating completion of audio generation.
        """
        from SinisterSixSystems.orchestration.audio_agent import AudioAgent

        audio_agent = AudioAgent()
        initial_state = {
            "transcript": [],
            "mode": mode,
            "markdown_document":  open(os.path.join("./artifacts/markdown/", os.listdir("./artifacts/markdown/")[0]), "r").read()
        }

        for output in audio_agent.generate_audio(initial_state):
            for _, value in output.items():
                pass
        
        return "Audio generation completed."


    def orchestrate(self, state: OrchestratorState) -> OrchestratorState:
        prompt_template = PromptTemplate(input_variables=["messages"], template=ORCHESTRATOR_PROMPT)
        orchestrator_chain = prompt_template | self.model_with_tools
        response = orchestrator_chain.invoke({"messages": state.get("messages", [])})

        logger.info(f"Orchestrator Response: {response}")
        return {
            "messages": state.get("messages", []) + [response]
        }

    def tool_invocation(self, state: OrchestratorState) -> OrchestratorState:
        pass

    def compile(self):
        workflow = StateGraph(OrchestratorState)

        workflow.add_node("orchestrate", self.orchestrate)
        workflow.add_node("tool_invocation", self.tool_invocation)

        workflow.add_edge(START, "orchestrate")

        workflow.add_conditional_edges(
            "orchestrate",
            lambda state: (
                "tool_invocation"
                if isinstance(state["messages"][-1], AIMessage)
                and state["messages"][-1].tool_calls
                else END
            ),
        )

        workflow.add_edge("tool_invocation", "orchestrate")

        return workflow.compile()

    
    def tool_invocation(self, state: OrchestratorState) -> OrchestratorState:
        last_message = state["messages"][-1]

        # If no tool calls → pass through
        if not isinstance(last_message, AIMessage) or not last_message.tool_calls:
            return state

        new_messages = state["messages"][:]

        for tool_call in last_message.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]

            logger.info(f"Invoking tool: {tool_name} with args: {tool_args}")

            tool_fn = {tool.name: tool for tool in self.tools}.get(tool_name)

            if tool_fn is None:
                raise ValueError(f"Tool {tool_name} not found")

            result = tool_fn.invoke(tool_args)

            new_messages.append(
                ToolMessage(
                    content=result,
                    tool_call_id=tool_call["id"]
                )
            )

        return {"messages": new_messages}


if __name__ == "__main__":
    orchestrator = Orchestrator()
    compiled_workflow = orchestrator.compile()

    initial_state = {
            "messages": [
                HumanMessage(content="Create a plot for the function y = sin(x) from 0 to 2π. Use graph tool")
            ]
    }

    for output in compiled_workflow.stream(initial_state):
        for _, value in output.items():
            pass
    
    logger.info(f"Orchestration Output: {output}")