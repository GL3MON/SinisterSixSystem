from mmdc import MermaidConverter
from pathlib import Path
import textwrap
import sys
import os

# Try to import LLM generator (optional)
try:
    from llm_mermaid import LLMGraphGenerator
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False
    LLMGraphGenerator = None

# Try to import Gemini config (optional)
try:
    from gemini_mermaid_cofig import GEMINI_API_KEY as DEFAULT_GEMINI_API_KEY
except ImportError:
    DEFAULT_GEMINI_API_KEY = None

class EducationalFlowchartAgent:
    def __init__(self, use_llm=False, api_key=None):
        self.converter = MermaidConverter()
        self.use_llm = use_llm
        self.llm_generator = None
        
        if use_llm:
            if not LLM_AVAILABLE:
                print("[WARN] LLM generator not available. Install requirements: pip install google-generativeai")
                self.use_llm = False
            else:
                try:
                    # Try to get API key from parameter, environment variable, or config file
                    api_key = api_key or os.getenv("GEMINI_API_KEY") or DEFAULT_GEMINI_API_KEY
                    if api_key:
                        self.llm_generator = LLMGraphGenerator(api_key=api_key)
                    else:
                        print("[WARN] No Gemini API key provided. Set GEMINI_API_KEY or pass api_key parameter.")
                        print("   Get your API key from: https://makersuite.google.com/app/apikey")
                        print("   Or create a gemini_config.py file with your API key")
                        self.use_llm = False
                except Exception as e:
                    print(f"[WARN] Failed to initialize LLM generator: {e}")
                    self.use_llm = False

    def text_to_mermaid(self, topic: str) -> str:
        """
        Generate Mermaid syntax with proper graph IDs.
        Uses LLM if available and enabled, otherwise uses local generation.
        """
        topic = topic.strip()
        
        # Try LLM generation first if enabled
        if self.use_llm and self.llm_generator:
            print("[INFO] Using LLM for intelligent generation...")
            llm_result = self.llm_generator.generate_graph_with_ids(topic)
            if llm_result:
                print("[OK] LLM generation successful!")
                return llm_result
            else:
                print("[WARN] LLM generation failed, falling back to local generation...")
        
        # Fallback to local generation with proper graph IDs
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

    def render(self, topic: str, output_file: str):
        mermaid_code = self.text_to_mermaid(topic)
        output_path = Path(output_file).resolve()

        # Debug print
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


if __name__ == "__main__":
    # Check for LLM usage flag
    use_llm = "--llm" in sys.argv or "-l" in sys.argv
    if use_llm:
        sys.argv = [arg for arg in sys.argv if arg not in ["--llm", "-l"]]
    
    # Get API key if provided
    api_key = None
    if "--api-key" in sys.argv:
        idx = sys.argv.index("--api-key")
        if idx + 1 < len(sys.argv):
            api_key = sys.argv[idx + 1]
            sys.argv = sys.argv[:idx] + sys.argv[idx+2:]
    
    agent = EducationalFlowchartAgent(use_llm=use_llm, api_key=api_key)

    if len(sys.argv) > 1:
        topic = " ".join(sys.argv[1:])
        output = "educational_flowchart.png"
    else:
        topic = input("Enter any educational topic: ").strip()
        if not topic:
            raise ValueError("Topic cannot be empty")
        
        if LLM_AVAILABLE and not agent.use_llm:
            use_llm_input = input("Use LLM for intelligent generation? (y/n, default: n): ").strip().lower()
            if use_llm_input == 'y':
                if not agent.llm_generator:
                    api_key_input = input("Enter Gemini API key (or press Enter to use GEMINI_API_KEY env var): ").strip()
                    if api_key_input:
                        api_key = api_key_input
                    agent = EducationalFlowchartAgent(use_llm=True, api_key=api_key)
        
        output = "educational_flowchart.png"

    agent.render(topic, output)
