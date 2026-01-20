from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from dotenv import load_dotenv
import os

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")



class RAG:
    def __init__(self, persist_directory: str = "./chroma_db"):
        self.persist_directory = persist_directory
        self.embedding_model = GoogleGenerativeAIEmbeddings(model="gemini-embedding-001", api_key=GOOGLE_API_KEY)
        self.vector_store = Chroma(
            persist_directory=self.persist_directory,
            embedding_function=self.embedding_model,
            collection_name="sinister_six_systems",
        )

    def add_documents(self, documents):
        self.vector_store.add_documents(documents)

    def process_file(self, file_path: str):
        loader = PyPDFLoader(file_path)
        documents = loader.load_and_split(text_splitter=RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200))
        self.add_documents(documents)

    def query(self, query_text: str, k: int = 4, filename: str = None):
        
        if filename:
            results = self.vector_store.similarity_search_with_score(
                query_text, k=k, filter={"source": filename}
            )
        else:
            results = self.vector_store.similarity_search_with_score(query_text, k=k)
        return results