from SinisterSixSystems.logging import logger
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import START, END, StateGraph
from langchain.tools import tool

from SinisterSixSystems.orchestration.graph_generator import GraphGenerator
from SinisterSixSystems.orchestration.audio_agent import AudioAgent
from SinisterSixSystems.constants import ORCHESTRATOR_PROMPT, MARKDOWN_AGENT_PROMPT

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.messages import ToolMessage

from dotenv import load_dotenv
from typing import TypedDict, List
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
        Generates an image based on the provided description.
        Args:
            description (str): The description for image generation.
        Returns:
            str: Status message indicating completion of image generation.
        """
        # Placeholder for image generation logic
        ROOT_DIR = f"./artifacts/processed_files/{query[:50]}/"

        logger.info(f"Image generation invoked with description: {description[:200]}")
        
        headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        }

        search_url = "https://www.googleapis.com/customsearch/v1"
        params = {
            'q': description,
            'cx': GOOGLE_CSE_ID,
            'key': GOOGLE_API_KEY,
            'searchType': 'image',
            'num': 1,
            'safe': 'off'
        }

        try:
            search_res = requests.get(search_url, headers=headers, params=params).json()
            # import random
            
            # random_idx = random.randint(0, len(search_res.get("items", [])) - 1) if "items" in search_res else 0
            
            if "items" not in search_res:
                logger.error(f"No image results found for query: {description[:100]}")
                return "Image generation failed: No results found."
            
            for idx, item in enumerate(search_res["items"]):
                
                # if idx != random_idx:
                #     continue
                try:
                    image_url = item["link"]
                    logger.info(f"Downloading image from URL: {image_url}")
                    
                    image_response = requests.get(image_url, headers=headers, timeout=10, stream=True)

                    content_type = image_response.headers.get('Content-Type', '')
                    if 'image' not in content_type:
                        logger.warning(f"URL did not return an image: {image_url}")
                        continue
                    
                    img_bytes = image_response.content

                    try:
                        img = Image.open(io.BytesIO(img_bytes))
                        img.verify()  # Check for corruption
                        os.makedirs(os.path.join(ROOT_DIR, "images"), exist_ok=True)
                        ext = mimetypes.guess_extension(content_type) or ".jpg"
                        final_filename = os.path.join(os.path.join(ROOT_DIR, "images"), f"image_{placeholder_idx}{ext}")

                        with open(final_filename, "wb") as f:
                            f.write(img_bytes)
                        
                        logger.info(f"Image saved to {final_filename}")

                    except Exception:
                        logger.warning(f"Downloaded file is not a valid image: {image_url}")
                        continue
                    
                except Exception as e:
                    logger.error(f"Error downloading image from {image_url}: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Error during image search: {e}")
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
        prompt_template = PromptTemplate(input_variables=["messages"], template=ORCHESTRATOR_PROMPT)
        orchestrator_chain = prompt_template | self.model_with_tools
        response = orchestrator_chain.invoke({"messages": state.get("messages", [])})

        logger.info(f"Orchestrator Response: {response}")
        return {
            "messages": state.get("messages", []) + [response]
        }
    
    def process_markdown_files(self, unprocessed_markdown: str, query: str) -> str:
        ROOT_DIR = "./artifacts/processed_files/"

        if not os.path.exists(ROOT_DIR):
            os.makedirs(ROOT_DIR)
        
        os.makedirs(os.path.join(ROOT_DIR, query[:50]), exist_ok=True)

        pattern = re.compile(r"<\s*(graph|image|mermaid)\s*:\s*([^>]+?)\s*>", re.IGNORECASE)

        matches = list(pattern.finditer(unprocessed_markdown))

        print(len(matches), "placeholders found.")

        dir_path = os.path.join(ROOT_DIR, query[:50])
        os.makedirs(dir_path, exist_ok=True)


        processed_markdown = unprocessed_markdown
        extracted_placeholder = []

        for idx, m in enumerate(matches):
            matched_text = m.group(0)
            logger.info(f"Placeholder {idx}: {matched_text[:20]}")
            placeholder_type = m.group(1).lower()
            processed_markdown = processed_markdown.replace(matched_text, f"<{placeholder_type}_{idx}>\n")
            extracted_placeholder.append({
                "type": placeholder_type,
                "idx": idx,
                "description": m.group(2).strip(),
            })

        with open(os.path.join(dir_path, "processed_document.md"), "w") as f:
            f.write(processed_markdown)
        
        with open(os.path.join(dir_path, "extracted_placeholders.json"), "w") as f:
            json.dump(extracted_placeholder, f, indent=4)

        for placeholder in extracted_placeholder:
            logger.info(f"Processing placeholder: {placeholder}")
            if placeholder["type"] == "graph":
                self.graph_tool(placeholder["description"], placeholder['idx'], f"./artifacts/processed_files/{query[:50]}/graphs/")
            elif placeholder["type"] == "image":
                self.image_generation_tool(placeholder["description"], query, placeholder['idx'])
            
        return processed_markdown

        

        
    def process_placeholder(self, state: OrchestratorState) -> OrchestratorState:
        prompt_template = PromptTemplate(input_variables=["messages"], template=MARKDOWN_AGENT_PROMPT)
        orchestrator = prompt_template | self.model
        response = orchestrator.invoke({"messages": state.get("messages", [])})

        markdown_document = response.content.replace("```markdown", "").replace("```", "").strip()
        
        with open("./artifacts/markdown/generated_document.md", "w") as f:
            f.write(markdown_document)

        self.process_markdown_files(markdown_document, state["messages"][0].content)

        return {
            "messages": state.get("messages", []) + [response],
            "markdown_document": markdown_document,
        }

    def compile(self):
        workflow = StateGraph(OrchestratorState)

        workflow.add_node("orchestrate", self.orchestrate)
        workflow.add_node("tool_invocation", self.tool_invocation)
        workflow.add_node("process_placeholder", self.process_placeholder)

        workflow.add_edge(START, "orchestrate")
        workflow.add_edge("orchestrate", "process_placeholder")
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
                HumanMessage(content="Explain the independence struggle of India with relevant graphs and images."),
            ]
    }

    for output in compiled_workflow.stream(initial_state):
        for _, value in output.items():
            pass
    
    logger.info(f"Orchestration Output: {output}")