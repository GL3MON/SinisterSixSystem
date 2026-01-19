import os
import requests
import mimetypes
import io
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

def download_image_utility(query, save_dir, num_results=5):
    """Headless version of your PicCode.py logic."""
    API_KEY = os.getenv("GOOGLE_API_KEY") # Ensure this is your Search API Key
    CX_ID = os.getenv("GOOGLE_CSE_ID")
    
    os.makedirs(save_dir, exist_ok=True)
    
    search_url = "https://www.googleapis.com/customsearch/v1"
    params = {
        'q': query,
        'cx': CX_ID,
        'key': API_KEY,
        'searchType': 'image',
        'num': num_results,
        'safe': 'active'
    }

    try:
        search_res = requests.get(search_url, params=params).json()
        if 'items' not in search_res:
            return None

        for item in search_res['items']:
            img_url = item['link']
            try:
                img_response = requests.get(img_url, timeout=10)
                if 'image' not in img_response.headers.get('Content-Type', ''):
                    continue

                img_bytes = img_response.content
                img = Image.open(io.BytesIO(img_bytes))
                img.verify() # Verify it's a real image

                # Clean filename
                clean_query = "".join([c if c.isalnum() else "_" for c in query[:20]])
                ext = mimetypes.guess_extension(img_response.headers.get('Content-Type')) or '.jpg'
                final_path = os.path.join(save_dir, f"{clean_query}{ext}")
                
                with open(final_path, 'wb') as f:
                    f.write(img_bytes)
                
                return final_path
            except:
                continue
    except Exception as e:
        print(f"Search Error: {e}")
    return None