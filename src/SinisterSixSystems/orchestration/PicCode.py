import os
import requests
import mimetypes
import io
from dotenv import load_dotenv
from PIL import Image
from tkinter import Tk, filedialog

# 1. Load Credentials
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
CX_ID = os.getenv("GOOGLE_CSE_ID")

def get_user_directory():
    """Opens a file dialog for the user to select a saving location."""
    print("Please select a folder to save your educational materials...")
    root = Tk()
    root.withdraw()  # Hide the main tkinter window
    root.attributes('-topmost', True) # Bring the dialog to the front
    selected_dir = filedialog.askdirectory(title="Select Save Location")
    root.destroy()
    return selected_dir if selected_dir else os.getcwd()

def is_valid_image(data):
    """Verifies if the byte data is actually a viewable image."""
    try:
        img = Image.open(io.BytesIO(data))
        img.verify()  # Check for corruption
        return True
    except Exception:
        return False

def download_teaching_materials(query, num_results=5):
    save_path = get_user_directory()
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
    }

    # Step 1: Search for multiple candidates (fallback strategy)
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
            print("No images found.")
            return

        # Step 2: Loop through results until a valid one is found
        for i, item in enumerate(search_res['items']):
            img_url = item['link']
            print(f"Checking link {i+1}: {img_url[:50]}...")

            try:
                img_response = requests.get(img_url, headers=headers, timeout=10, stream=True)
                
                # Verify Content-Type
                content_type = img_response.headers.get('Content-Type', '')
                if 'image' not in content_type:
                    continue

                # Read content to verify
                img_bytes = img_response.content
                
                if is_valid_image(img_bytes):
                    ext = mimetypes.guess_extension(content_type) or '.jpg'
                    final_filename = os.path.join(save_path, f"teaching_visual_{query.replace(' ', '_')}{ext}")
                    
                    with open(final_filename, 'wb') as f:
                        f.write(img_bytes)
                    
                    print(f"✅ Success! Viewable image saved to: {final_filename}")
                    return # Stop after the first successful, valid download
                else:
                    print(f"⚠️ Link {i+1} was corrupted or invalid. Trying next...")
            
            except Exception as e:
                print(f"❌ Failed to reach link {i+1}. Error: {e}")

        print("Failed to find a valid image in the top results.")

    except Exception as e:
        print(f"Search API Error: {e}")

if __name__ == "__main__":
    subject = input("Enter teaching topic for image: ")
    download_teaching_materials(subject)