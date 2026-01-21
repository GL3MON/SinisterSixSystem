import os
import json
import warnings
import typing_extensions as typing
from gtts import gTTS
import google.generativeai as genai
from bing_image_downloader import downloader  # Replacement library
from dotenv import load_dotenv
import matplotlib.pyplot as plt
from PIL import Image

# Robust MoviePy Imports
try:
    from moviepy import ImageClip, AudioFileClip, concatenate_videoclips
except ImportError:
    from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips

# =============================================================================
# 1. SETUP & CREDENTIALS
# =============================================================================
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("Missing GEMINI_API_KEY! Check your .env file.")

genai.configure(api_key=GEMINI_API_KEY)
warnings.filterwarnings("ignore")

# =============================================================================
# 2. SCHEMA & BING DOWNLOADER HELPER
# =============================================================================
class Slide(typing.TypedDict):
    title: str
    content_text: str
    narration: str
    search_keyword: str

class LessonScript(typing.TypedDict):
    slides: typing.List[Slide]

def get_bing_image(query, output_dir, limit=1):
    """
    Uses bing-image-downloader to fetch images.
    Returns the path to the first downloaded image.
    """
    print(f"🔍 Searching Bing for: {query}...")
    try:
        # Downloads images into a subfolder named after the query
        downloader.download(
            query,
            limit=limit,
            output_dir=output_dir,
            adult_filter_off=True,
            force_replace=False,
            timeout=60,
            verbose=False
        )
        
        # Identify the downloaded file path
        query_folder = os.path.join(output_dir, query)
        if os.path.exists(query_folder):
            files = os.listdir(query_folder)
            if files:
                return os.path.join(query_folder, files[0])
    except Exception as e:
        print(f"⚠️ Bing download error: {e}")
    return None

# =============================================================================
# 3. MAIN EXECUTION ENGINE
# =============================================================================
def create_video(content_for_video: str, output_dir: str, idx: int):
    os.makedirs(output_dir, exist_ok=True)

    # Step 1: Generate Script via Gemini
    model = genai.GenerativeModel(
        "gemini-2.5-flash",
        generation_config={
            "response_mime_type": "application/json",
            "response_schema": LessonScript
        }
    )

    prompt = f"Convert these facts into a 3-slide video script with keywords for real-world images: {content_for_video}"

    try:
        response = model.generate_content(prompt)
        script_data = json.loads(response.text)
        slides = script_data.get("slides", [])
    except Exception as e:
        print(f"❌ Scripting failed: {e}")
        return

    if not slides:
        print("❌ No slides generated.")
        return

    slide_paths, audio_paths = [], []

    # Step 2: Slide and Audio Creation
    for i, slide in enumerate(slides):
        title = slide.get("title", "Quick Fact")
        content = slide.get("content_text", "No description.")
        narration = slide.get("narration", content)
        keyword = slide.get("search_keyword", title)

        print(f"\n🎬 Processing Slide {i+1}: {title}")

        # Audio generation
        a_path = os.path.join(output_dir, f"audio_{i}.mp3")
        gTTS(text=narration, lang="en").save(a_path)
        audio_paths.append(a_path)

        # Image generation using Bing
        img_path = get_bing_image(keyword, output_dir)

        # Slide Design with Matplotlib
        plt.figure(figsize=(16, 9), facecolor="#121212")
        ax = plt.gca()
        ax.set_facecolor("#121212")
        plt.axis("off")

        image_loaded = False
        if img_path and os.path.exists(img_path):
            try:
                img = Image.open(img_path).convert("RGB")
                plt.imshow(img)
                image_loaded = True
            except:
                image_loaded = False

        # Overlay text on the slide
        text_color = "white"
        if image_loaded:
            plt.text(0.5, 0.1, title.upper(), color=text_color, fontsize=32, ha="center", va="center", 
                     weight="bold", transform=ax.transAxes, bbox=dict(facecolor="black", alpha=0.7, pad=14))
        else:
            plt.text(0.5, 0.42, title.upper(), color=text_color, fontsize=44, ha="center", va="center", 
                     weight="bold", transform=ax.transAxes, bbox=dict(facecolor="black", alpha=0.75, pad=18))
            plt.text(0.5, 0.58, content, color=text_color, fontsize=26, ha="center", va="center", 
                     transform=ax.transAxes, bbox=dict(facecolor="black", alpha=0.55, pad=18), wrap=True)

        s_path = os.path.join(output_dir, f"slide_{i}.png")
        plt.savefig(s_path, bbox_inches="tight", pad_inches=0)
        plt.close()
        slide_paths.append(s_path)

    # Step 3: Video Rendering
    print("\n📦 Rendering final video...")
    clips = []
    for s, a in zip(slide_paths, audio_paths):
        if os.path.exists(s) and os.path.exists(a):
            audio = AudioFileClip(a)
            clip = ImageClip(s).with_duration(audio.duration).with_audio(audio)
            clips.append(clip)

    if clips:
        output = os.path.join(output_dir, f"video_{idx}.mp4")
        concatenate_videoclips(clips, method="compose").write_videofile(output, fps=24)
        print(f"✨ Success! Video saved to {output}")
    else:
        print("❌ Video rendering failed: No valid clips.")

if __name__ == "__main__":
    FACTUAL_DATA = """
    The human heart is a muscular organ that pumps blood through the body.
    It beats about 100,000 times a day.
    The heart is located in the chest cavity, between the lungs.
    """
    OUTPUT_DIR = "bing_lesson_video"
    create_video(FACTUAL_DATA, OUTPUT_DIR)