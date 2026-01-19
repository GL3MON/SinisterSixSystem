import os
import requests
import mimetypes
import io
from PIL import Image
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

load_dotenv()

def image_extraction_node(state):
    print("📍 [DEBUG] Entered Image Extraction Node")
    
    # Generate the search query using Gemini
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)
    prompt = f"Create a short, descriptive image search query for: {state['user_input']}"
    query = llm.invoke(prompt).content.strip().replace('"', '')
    
    print(f"🔎 [DEBUG] Generated Image Query: {query}")
    
    API_KEY = os.getenv("GOOGLE_API_KEY") 
    CX_ID = os.getenv("GOOGLE_CSE_ID")
    
    # Path logic for artifacts
    base_dir = os.getcwd()
    save_dir = os.path.join(base_dir, "artifacts", "image")
    os.makedirs(save_dir, exist_ok=True)
    
    search_url = "https://www.googleapis.com/customsearch/v1"
    params = {'q': query, 'cx': CX_ID, 'key': API_KEY, 'searchType': 'image', 'num': 3}

    try:
        search_res = requests.get(search_url, params=params).json()
        if 'items' in search_res:
            for item in search_res['items']:
                img_url = item['link']
                try:
                    res = requests.get(img_url, timeout=10)
                    if 'image' in res.headers.get('Content-Type', ''):
                        img = Image.open(io.BytesIO(res.content))
                        img.verify()
                        
                        ext = mimetypes.guess_extension(res.headers.get('Content-Type')) or '.jpg'
                        # Clean filename string
                        clean_name = ''.join(x for x in query[:15] if x.isalnum())
                        filename = f"visual_{clean_name}{ext}"
                        final_path = os.path.join(save_dir, filename)
                        
                        with open(final_path, 'wb') as f:
                            f.write(res.content)
                        
                        print(f"✅ [DEBUG] Image saved at: {final_path}")
                        return {"media_assets": {"image_path": final_path}}
                except: continue
    except Exception as e:
        print(f"❌ Image Error: {e}")
    
    return state