from google.genai.types import Transcription
from SinisterSixSystems.logging import logger
from SinisterSixSystems.constants import AUDIO_GENERATION_TUTOR_PROMPT, AUDIO_GENERATION_STORY_PROMPT
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import START, END, StateGraph
from SinisterSixSystems.components.tts import TTS
from dotenv import load_dotenv
import os
from typing import List, TypedDict

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

class AudioAgentState(TypedDict):
    transcript: List[dict[str, str]]
    mode: str
    markdown_document: str

class AudioAgent:
    def __init__(self):
        self.output_parser = StrOutputParser()
        self.model = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.0, api_key=GOOGLE_API_KEY)
        self.state = {
            "transcript": [],   
            "mode": "tutor",
            "markdown_document": ""
        }

        self.tts = TTS()
    
    def generate_transcript_tutor(self, state: AudioAgentState):
        prompt_template = PromptTemplate(input_variables=["markdown_document"], template=AUDIO_GENERATION_TUTOR_PROMPT)
        audio_generation_tutor_chain = prompt_template | self.model | self.output_parser
        response = audio_generation_tutor_chain.invoke({"markdown_document": state.get("markdown_document", "")})
        
        transcripts = []
        for idx, line in enumerate(response.split("\n")):
            if line.strip() != "":
                transcripts.append({
                    "voice": "alba",
                    "text": line.strip().replace(":", " ")
                })

        self.tts.generate_batch_audio(transcripts)

        return {
            "transcript": transcripts,
            "markdown_document": state.get("markdown_document", ""),
            "mode": state.get("mode", "tutor")
        }

    def generate_audio_story_mode(self, state: AudioAgentState):
        transcripts = []

        prompt_template = PromptTemplate(input_variables=["markdown_document"], template=AUDIO_GENERATION_STORY_PROMPT)
        audio_generation_story_chain = prompt_template | self.model | self.output_parser
        response = audio_generation_story_chain.invoke({"markdown_document": state.get("markdown_document", "")})
        for line in response.split("\n"):
            if line.strip() != "":
                if line.startswith("PA:"):
                    transcripts.append({
                        "voice": "alba",
                        "text": line.replace("PA:", "").strip().replace(":", " ")
                    })
                elif line.startswith("PB:"):
                    transcripts.append({
                        "voice": "eponine",
                        "text": line.replace("PB:", "").strip().replace(":", " ")
                    })
                transcripts.append({
                    "voice": "alba",
                    "text": line.strip().replace(":", " ")
                })

        self.tts.generate_batch_audio(transcripts)

        return {
            "transcript": transcripts,
            "markdown_document": state.get("markdown_document", ""),
            "mode": state.get("mode", "story")
        }

    def route_by_mode(self, state: AudioAgentState) -> str:
        """Conditional routing function that determines the next node based on mode."""
        mode = state.get("mode", "tutor")
        if mode == "tutor":
            return "generate_tutor"
        else:
            return "generate_story"
    
    def route_node(self, state: AudioAgentState):
        """Pass-through node that just returns the state for routing."""
        return state
    
    def compile(self):
        workflow = StateGraph[AudioAgentState, None, AudioAgentState, AudioAgentState](AudioAgentState)
        workflow.add_node("route", self.route_node)
        workflow.add_node("generate_tutor", self.generate_transcript_tutor)
        workflow.add_node("generate_story", self.generate_audio_story_mode)
        
        # Start with routing node
        workflow.add_edge(START, "route")
        
        # Route based on mode
        workflow.add_conditional_edges(
            "route",
            self.route_by_mode,
            {
                "generate_tutor": "generate_tutor",
                "generate_story": "generate_story"
            }
        )
        
        # Both generate nodes go to END
        workflow.add_edge("generate_tutor", END)
        workflow.add_edge("generate_story", END)
        
        return workflow.compile()


if __name__ == "__main__":
    audio_agent = AudioAgent()
    compiled_workflow = audio_agent.compile()

    initial_state = {
        "transcript": [],
        "mode": "story",
        "markdown_document": open("/mnt/2028B41628B3E944/Projects/SinisterSixSystem/artifacts/markdown/What_is_photosy.md", "r").read()
    }

    for output in compiled_workflow.stream(initial_state):
        for _, value in output.items():
            print(value)