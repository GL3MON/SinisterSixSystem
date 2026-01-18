import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

def list_supported_models():
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    print("--- Supported Models for your API Key ---")
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                # We want the name without the 'models/' prefix for LangChain
                print(f"Name: {m.name.replace('models/', '')}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    list_supported_models()