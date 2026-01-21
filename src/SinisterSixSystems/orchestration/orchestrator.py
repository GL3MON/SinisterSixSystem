from SinisterSixSystems.logging import logger
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import START, END, StateGraph
from langchain.agents import create_agent
from langchain.tools import tool
from bing_image_downloader import downloader
import shutil

from SinisterSixSystems.orchestration.graph_generator import GraphGenerator
from SinisterSixSystems.orchestration.audio_agent import AudioAgent
from SinisterSixSystems.constants import ORCHESTRATOR_PROMPT, MARKDOWN_AGENT_PROMPT, RAG_AGENT_PROMPT
from SinisterSixSystems.components.rag import RAG
from SinisterSixSystems.utils import sanitze_filename

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.messages import ToolMessage

from dotenv import load_dotenv
from typing import TypedDict, List
from functools import partial
from PIL import Image
import mimetypes
import io
import os
import re
import json
import requests

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")

class OrchestratorState(TypedDict):
    messages: list
    markdown_document: str
    document: str
    summarized_rag_content: str


class Orchestrator:
    def __init__(self):
        self.output_parser = StrOutputParser()
        self.model = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.0, api_key=GOOGLE_API_KEY)
        
        self.tools = [
            self.graph_tool,
            self.audio_generation_tool
        ]

        self.retrieval_system = RAG()

        self.model_with_tools = self.model.bind_tools(self.tools)
    
    @staticmethod
    def graph_tool(query: str, graph_id: str, path: str) -> str:
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
            "graph_id": graph_id, 
            "path": path,
            "file_name": f"graph_{graph_id}.png",
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
    def image_generation_tool(description: str, query: str, placeholder_idx: int) -> str:
        """
        Generates an image using Bing Image Downloader.
        Args:
            description (str): The description for image search.
            query (str): User query (used for folder naming).
            placeholder_idx (int): Index for deterministic image naming.
        Returns:
            str: Status message indicating completion.
        """

        ROOT_DIR = f"./artifacts/processed_files/{sanitze_filename(query)}"
        IMAGES_DIR = os.path.join(ROOT_DIR, "images")
        TEMP_DIR = os.path.join(ROOT_DIR, "_bing_tmp")

        os.makedirs(IMAGES_DIR, exist_ok=True)
        os.makedirs(TEMP_DIR, exist_ok=True)

        logger.info(f"Bing image generation invoked with description: {description[:200]}")

        try:
            downloader.download(
                description,
                limit=7,
                output_dir=TEMP_DIR,
                adult_filter_off=True,
                force_replace=False,
                timeout=60,
                verbose=False
            )

            query_folder = os.path.join(TEMP_DIR, description)
            if not os.path.exists(query_folder):
                logger.error("No images downloaded from Bing.")
                return "Image generation failed: No results found."

            for file in os.listdir(query_folder):
                file_path = os.path.join(query_folder, file)

                try:
                    with open(file_path, "rb") as f:
                        img_bytes = f.read()

                    img = Image.open(io.BytesIO(img_bytes))
                    img.verify()

                    final_path = os.path.join(
                        IMAGES_DIR,
                        f"image_{placeholder_idx}.png"
                    )

                    with open(final_path, "wb") as f:
                        f.write(img_bytes)

                    logger.info(f"Image saved to {final_path}")

                    shutil.rmtree(TEMP_DIR, ignore_errors=True)
                    return f"Image saved to {final_path}"

                except Exception:
                    logger.warning(f"Invalid image file skipped: {file}")
                    continue

            shutil.rmtree(TEMP_DIR, ignore_errors=True)
            return "Image generation failed: No valid images."

        except Exception as e:
            logger.error(f"Bing image download error: {e}")
            shutil.rmtree(TEMP_DIR, ignore_errors=True)
            return "Image generation failed due to an error."

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
        prompt_template = PromptTemplate(input_variables=["messages", "document"], template=ORCHESTRATOR_PROMPT)
        orchestrator_chain = prompt_template | self.model_with_tools
        response = orchestrator_chain.invoke({"messages": state.get("messages", []), "document": state.get("summarized_rag_content", "")})

        logger.info(f"Orchestrator Response: {response}")
        return {
            "messages": state.get("messages", []) + [response],
        }
    
    def process_markdown_files(self, unprocessed_markdown: str, query: str) -> str:
        ROOT_DIR = "./artifacts/processed_files/"

        if not os.path.exists(ROOT_DIR):
            os.makedirs(ROOT_DIR)
        
        os.makedirs(os.path.join(ROOT_DIR, sanitze_filename(query)), exist_ok=True)

        pattern = re.compile(r"<\s*(graph|image|mermaid)\s*:\s*([^>]+?)\s*>", re.IGNORECASE)

        matches = list(pattern.finditer(unprocessed_markdown))

        print(len(matches), "placeholders found.")

        dir_path = os.path.join(ROOT_DIR, sanitze_filename(query))
        os.makedirs(dir_path, exist_ok=True)


        processed_markdown = unprocessed_markdown
        extracted_placeholder = []

        for idx, m in enumerate(matches):
            matched_text = m.group(0)
            logger.info(f"Placeholder {idx}: {matched_text[:20]}")
            placeholder_type = m.group(1).lower()
            processed_markdown = processed_markdown.replace(matched_text, f"![{sanitze_filename(m.group(2).strip())}](/artifacts/processed_files/{sanitze_filename(query)}/{placeholder_type}s/{placeholder_type}_{idx}.png)\n")
            extracted_placeholder.append({
                "type": placeholder_type,
                "idx": idx,
                "description": m.group(2).strip(),
            })

        
        with open(os.path.join(dir_path, "extracted_placeholders.json"), "w") as f:
            json.dump(extracted_placeholder, f, indent=4)

        for placeholder in extracted_placeholder:
            logger.info(f"Processing placeholder: {placeholder}")
            if placeholder["type"] == "graph":
                self.graph_tool(placeholder["description"], placeholder['idx'], f"./artifacts/processed_files/{sanitze_filename(query)}/graphs/")
            elif placeholder["type"] == "image":
                if "Image generation failed: No results found." == self.image_generation_tool(placeholder["description"], query, placeholder['idx']):
                    processed_markdown = processed_markdown.replace(f"![{sanitze_filename(placeholder['description'])}](/artifacts/processed_files/{sanitze_filename(query)}/images/image_{placeholder['idx']}.png)\n", "")
                    logger.error(f"No image results found for placeholder: {placeholder}")
            
        with open(os.path.join(dir_path, "processed_document.md"), "w") as f:
            f.write(processed_markdown)
        return processed_markdown
    
    def process_placeholder(self, state: OrchestratorState) -> OrchestratorState:
        prompt_template = PromptTemplate(input_variables=["messages", "document"], template=MARKDOWN_AGENT_PROMPT)
        orchestrator = prompt_template | self.model
        response = orchestrator.invoke({"messages": state.get("messages", []), "document": state.get("summarized_rag_content", "")})

        markdown_document = response.content.replace("```markdown", "").replace("```", "").strip()
        
        with open("./artifacts/markdown/generated_document.md", "w") as f:
            f.write(markdown_document)

        self.process_markdown_files(markdown_document, state["messages"][0].content)

        return {
            "messages": state.get("messages", []) + [response],
            "markdown_document": markdown_document,
        }
    
    def start(self, state: OrchestratorState) -> OrchestratorState:
        return state
    
    def rag(self, state: OrchestratorState) -> OrchestratorState:
        prompt_template = PromptTemplate(input_variables=["query"], template=RAG_AGENT_PROMPT)
        filename = state["document"]

        from langchain.tools import tool

        @tool
        def rag_tool(query: str):
            """
            This RAG tool retrieves relevant documents for answering a user query.

            Args:
                query (str): User query

            Returns:
                list[str]: Retrieved document contents
            """

            docs = self.retrieval_system.retrieve_documents(
                query=query,
                filename=filename
            )

            if hasattr(docs[0], "page_content"):
                return [doc.page_content for doc in docs]

            return docs


        rag_tools = [
            rag_tool
        ]

        rag_agent = create_agent(
            model=self.model,
            tools=rag_tools,
            system_prompt=prompt_template
        )

        summarized_document = rag_agent.invoke({"query": state["messages"][0].content})
        logger.info(f"RAG Agent Summarized Document: {summarized_document[:100]}")

        return {
            "messages": state.get("messages", []),
            "document": filename,
            "summarized_rag_content": summarized_document
        }
    
    def should_do_rag(self, state: OrchestratorState) -> bool:
        if state.get("document", "") == "":
            return "orchestrate"
        return "rag"

    def compile(self):
        workflow = StateGraph(OrchestratorState)

        workflow.add_node("start", self.start)
        workflow.add_node("orchestrate", self.orchestrate)
        workflow.add_node("tool_invocation", self.tool_invocation)
        workflow.add_node("rag", self.rag)
        workflow.add_node("process_placeholder", self.process_placeholder)
        
        workflow.add_edge(START, "start")

        workflow.add_conditional_edges(
            "start",
            self.should_do_rag,
            {
                "orchestrate": "process_placeholder",
                "rag": "rag"
            }
        )

        workflow.add_edge("rag", "process_placeholder")
        # workflow.add_conditional_edges(
        #     "orchestrate",
        #     lambda state: (
        #         "tool_invocation"
        #         if isinstance(state["messages"][-1], AIMessage)
        #         and state["messages"][-1].tool_calls
        #         else END
        #     ),
        # )
        workflow.add_edge("process_placeholder", END)

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
                HumanMessage(content="Explain steam engines with relevant graphs and images." ),
            ],
            "document": "",
    }

    for output in compiled_workflow.stream(initial_state):
        for _, value in output.items():
            pass
    
    logger.info(f"Orchestration Output: {output}")