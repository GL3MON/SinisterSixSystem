from mmdc import MermaidConverter
from pathlib import Path
import textwrap
import sys
import os

# ------------------ ARTIFACTS PATH ------------------
MERMAID_DIR = Path("artifacts/mermaid")
MERMAID_DIR.mkdir(parents=True, exist_ok=True)

# ------------------ OPTIONAL LLM IMPORT ------------------
try:
    from llm_mermaid import LLMGraphGenerator
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False
    LLMGraphGenerator = None

# ------------------ OPTIONAL GEMINI CONFIG ------------------
try:
    from gemini_mermaid_cofig import GEMINI_API_KEY as DEFAULT_GEMINI_API_KEY
except ImportError:
    DEFAULT_GEMINI_API_KEY = None


# ------------------ INPUT FUNCTION ------------------
def get_topic_from_user() -> str:
    topic = input("Enter any educational topic: ").strip()
    if not topic:
        raise ValueError("Topic cannot be empty")
    return topic


# ------------------ MAIN AGENT ------------------
class EducationalFlowchartAgent:
    def __init__(self, use_llm=False, api_key=None):
        self.converter = MermaidConverter()
        self.use_llm = use_llm
        self.llm_generator = None

        if use_llm:
            if not LLM_AVAILABLE:
                print("[WARN] LLM generator not available.")
                self.use_llm = False
            else:
                try:
                    api_key = api_key or os.getenv("GEMINI_API_KEY") or DEFAULT_GEMINI_API_KEY
                    if api_key:
                        self.llm_generator = LLMGraphGenerator(api_key=api_key)
                    else:
                        print("[WARN] No Gemini API key provided.")
                        self.use_llm = False
                except Exception as e:
                    print(f"[WARN] Failed to initialize LLM generator: {e}")
                    self.use_llm = False

    def text_to_mermaid(self, topic: str) -> str:
        topic = topic.strip()

        if self.use_llm and self.llm_generator:
            print("[INFO] Using LLM for intelligent generation...")
            llm_result = self.llm_generator.generate_graph_with_ids(topic)
            if llm_result:
                print("[OK] LLM generation successful!")
                return llm_result
            print("[WARN] LLM failed, falling back to local generation.")

        mermaid = f"""
graph TD
    A["Start: {topic}"] --> B["Introduction / Definition"]
    B --> C["Main Components"]
    C --> D["Working / Process"]
    D --> E["Intermediate Stages"]
    E --> F["Final Outcome"]
    F --> G["Conclusion / Learning"]
"""
        return textwrap.dedent(mermaid).strip()

    def render(self, topic: str, output_file):
        mermaid_code = self.text_to_mermaid(topic)
        output_path = Path(output_file).resolve()

        print("\nGenerated Mermaid code:\n")
        print(mermaid_code)

        try:
            self.converter.to_png(mermaid_code, output_file=output_path)

            if output_path.exists() and output_path.stat().st_size > 0:
                print(f"\n[SUCCESS] Flowchart generated at: {output_path}")
                print(f"File size: {output_path.stat().st_size} bytes")
            else:
                raise RuntimeError("PNG generated but empty")

        except Exception as e:
            print("Rendering failed:", e)
            raise


# ------------------ ENTRY POINT ------------------
if __name__ == "__main__":

    # Detect LLM flag
    use_llm = "--llm" in sys.argv or "-l" in sys.argv
    if use_llm:
        sys.argv = [arg for arg in sys.argv if arg not in ("--llm", "-l")]

    # Detect API key flag
    api_key = None
    if "--api-key" in sys.argv:
        idx = sys.argv.index("--api-key")
        if idx + 1 < len(sys.argv):
            api_key = sys.argv[idx + 1]
            sys.argv = sys.argv[:idx] + sys.argv[idx + 2 :]

    agent = EducationalFlowchartAgent(use_llm=use_llm, api_key=api_key)

    # Topic selection
    if len(sys.argv) > 1:
        topic = " ".join(sys.argv[1:])
    else:
        topic = get_topic_from_user()

    output = MERMAID_DIR / "educational_flowchart.png"
    agent.render(topic, output)
