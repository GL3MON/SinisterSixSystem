from SinisterSixSystems.logging import logger
from SinisterSixSystems.constants import GRAPH_GENERATION_PROMPT
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import os

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

class GraphGenerator:
    def __init__(self):
        self.prompt = PromptTemplate(input_variables=[""], template=GRAPH_GENERATION_PROMPT)
        self.output_parser = StrOutputParser()
        self.model = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.0, api_key=GOOGLE_API_KEY)

    

    