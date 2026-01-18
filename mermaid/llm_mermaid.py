"""
LLM-based Mermaid Graph Generator
Generates intelligent, topic-specific flowcharts with proper graph IDs
using Large Language Models (Google Gemini API).
"""

import os
from typing import Optional


class LLMGraphGenerator:
    """
    Uses LLM (Google Gemini API) to generate intelligent Mermaid flowchart syntax
    with proper graph IDs and topic-specific content.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize LLM Graph Generator with Google Gemini API.
        
        Args:
            api_key: Google Gemini API key. If None, uses GEMINI_API_KEY environment variable.
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.client = None
        
        if self.api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self.client = genai.GenerativeModel('gemini-pro')
                print("[OK] LLM Graph Generator initialized with Google Gemini API")
            except ImportError:
                raise ImportError(
                    "Google Generative AI library not installed. Install it with: pip install google-generativeai\n"
                    "The LLM feature requires the google-generativeai package to work."
                )
        else:
            print("[WARN] No API key provided. LLM generation will not work.")
            print("   Set GEMINI_API_KEY environment variable or pass api_key parameter.")
            print("   Get your API key from: https://makersuite.google.com/app/apikey")
    
    def generate_graph_with_ids(self, topic: str, model: str = "gemini-pro") -> Optional[str]:
        """
        Generate Mermaid flowchart syntax with proper graph IDs using Google Gemini LLM.
        
        Args:
            topic: The educational topic to generate a flowchart for
            model: Gemini model to use (default: gemini-pro)
        
        Returns:
            Valid Mermaid syntax string with proper graph IDs, or None if generation fails
        """
        if not self.client:
            raise ValueError(
                "Gemini client not initialized. Provide an API key in __init__() or "
                "set GEMINI_API_KEY environment variable."
            )
        
        prompt = f"""Generate a detailed educational Mermaid flowchart diagram for: "{topic}"

CRITICAL REQUIREMENTS:
1. Use 'graph TD' (top-down direction)
2. Use proper node IDs: A, B, C, D, E, F, G, H, I, J, K, L, M... (single uppercase letters)
3. Each node must have a unique ID and a descriptive label
4. Use DIFFERENT SHAPES for variety:
   - Round: ([Start/End])
   - Rectangular: ["Process"]
   - Diamond: {{Decision}}
   - Cylindrical: ("Database/Storage") - Note: Use DOUBLE parentheses ONLY
   - Hexagon: {{"Special Process"}}
5. Add CYCLIC ARROWS if the topic involves a cycle (like water cycle, carbon cycle, etc.):
   - Use --> for forward flow
   - Add back arrows (e.g., I --> B) to show cycle continuation
6. DO NOT use colors or style statements - use ONLY different shapes to distinguish nodes
7. Make nodes topic-specific and educational
8. Include at least 5-10 nodes for a comprehensive flowchart
9. If topic is a CYCLE, ensure there's a return arrow to show the cycle repeats
10. Use clear, educational labels for each step/stage
11. Return ONLY the Mermaid syntax code, nothing else
12. Do NOT include markdown code blocks (```mermaid or ```)
13. Do NOT include explanations or additional text

Example format with different shapes and cycles (NO COLORS):
graph TD
    A([Start: Water Cycle]) --> B["Evaporation"]
    B --> C["Condensation"]
    C --> D{{Cloud Formation}}
    D --> E["Precipitation"]
    E --> F(("Collection"))
    F --> G["Storage"]
    G --> A

CRITICAL SYNTAX RULES:
- Each arrow MUST be on its own line: A --> B (NOT: A --> B --> C)
- Use DOUBLE parentheses for cylindrical: (("Label")) NOT [("Label")]
- DO NOT include any style or color statements - use ONLY shapes
- Ensure all brackets [ ], parentheses ( ), and braces {{ }} are properly matched
- Keep node labels simple and in quotes: ["Label"]
- Avoid special characters in labels that might break parsing

Now generate for topic: {topic}. Use different shapes (round, rectangular, diamond, cylindrical) and add cyclic arrows if it's a cycle. DO NOT use colors or style statements - shapes only.

Mermaid code:"""

        try:
            # Google Gemini API
            system_instruction = (
                "You are an expert at creating educational flowcharts in Mermaid syntax. "
                "Always use proper node IDs (A, B, C, etc.) and return ONLY valid Mermaid code. "
                "CRITICAL: Use different shapes (round, rectangular, diamond, cylindrical) to "
                "distinguish nodes. Add cyclic arrows when topics involve cycles. "
                "DO NOT use colors or style statements - shapes only. "
                "Never include markdown code blocks or explanations."
            )
            
            full_prompt = f"{system_instruction}\n\n{prompt}"
            
            response = self.client.generate_content(
                full_prompt,
                generation_config={
                    "temperature": 0.7,
                    "max_output_tokens": 2500,
                }
            )
            
            mermaid_code = response.text.strip()
            
            # Clean up: Remove markdown code blocks if present
            mermaid_code = self._clean_mermaid_code(mermaid_code)
            
            # Validate and fix basic structure
            if not mermaid_code.startswith("graph"):
                # Try to extract if wrapped in text
                lines = mermaid_code.split("\n")
                for i, line in enumerate(lines):
                    if line.strip().startswith("graph"):
                        mermaid_code = "\n".join(lines[i:])
                        break
            
            # Fix common syntax issues that cause blank images
            mermaid_code = self._fix_mermaid_syntax(mermaid_code)
            
            return mermaid_code.strip()
            
        except Exception as e:
            print(f"[ERROR] LLM generation failed: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _fix_mermaid_syntax(self, code: str) -> str:
        """
        Fix common Mermaid syntax issues that cause rendering failures.
        
        Args:
            code: Mermaid code string
        
        Returns:
            Fixed Mermaid code string
        """
        lines = code.split("\n")
        fixed_lines = []
        
        for line in lines:
            original_line = line
            line = line.strip()
            if not line:
                continue
            
            # Skip empty lines and comments
            if line.startswith("%%"):
                continue
            
            # Fix cylindrical shape syntax issues
            import re
            # Fix [("label")] -> (("label"))
            line = re.sub(r'\[\(\("([^"]+)"\)\)\]', r'(("\1"))', line)
            # Fix [("label")] -> (("label"))
            line = re.sub(r'\[\(\("([^"]+)"\)\]', r'(("\1"))', line)
            # Fix [("label") -> (("label"))
            line = re.sub(r'\[\(\("([^"]+)"\)', r'(("\1"))', line)
            # Fix ("label"] -> (("label"))
            line = re.sub(r'\(\("([^"]+)"\]', r'(("\1"))', line)
            # Fix [("label") with single quote -> (("label"))
            line = re.sub(r'\[\("([^"]+)"\)\]', r'(("\1"))', line)
            # Fix M[("label")] -> M(("label"))
            line = re.sub(r'([A-Z])\[\(\("([^"]+)"\)\)\]', r'\1(("\2"))', line)
            
            # Fix diamond shape syntax: {Label} -> {{Label}} or {Label") -> {{Label}}
            # Single { } should be {{ }} for decision nodes
            # Fix unmatched brackets: {"Label") -> {{"Label"}}
            line = re.sub(r'\{"([^"]+)"\)', r'{{"\1"}}', line)
            # Fix {Label} --> to {{Label}} -->
            line = re.sub(r'\{([^}]+)\}(?!\})\s*-->', r'{{\1}} -->', line)
            # Fix --> {Label} to --> {{Label}}
            line = re.sub(r'-->\s*\{([^}]+)\}(?!\})', r'--> {{\1}}', line)
            
            # Fix "Return to X" nodes - convert to actual connections
            # Pattern: NODE["Return to X"] should become NODE --> X
            if 'Return to' in line or 'return to' in line:
                return_match = re.search(r'\["Return to ([A-Z])"\]', line)
                if return_match:
                    target_node = return_match.group(1)
                    # Extract the source node ID
                    source_match = re.search(r'^([A-Z])', line)
                    if source_match:
                        source_node = source_match.group(1)
                        # Replace with actual connection
                        line = f"{source_node} --> {target_node}"
            
            # Fix unmatched brackets: {Label] -> {{Label}}
            # Pattern: NODE{Label] should be NODE{{Label}}
            if '{' in line and line.count('{') < line.count('}'):
                # Unmatched opening brace - likely should be double braces
                line = re.sub(r'([A-Z])\{([^}]+)\]', r'\1{{\2}}', line)
            elif '{' in line and not line.count('}}'):
                # Single { without matching }} - check if it's a decision node
                if ' --> ' in line or '-->' in line:
                    # Fix: NODE{Label] --> to NODE{{Label}} -->
                    line = re.sub(r'([A-Z])\{([^}]+)\](\s*-->)', r'\1{{\2}}\3', line)
                    # Fix: --> NODE{Label] to --> NODE{{Label}}
                    line = re.sub(r'(-->\s*)([A-Z])\{([^}]+)\]', r'\1\2{{\3}}', line)
            
            # Fix unmatched brackets: {Label") -> {{Label"}}
            if '{"' in line and '")' in line and '}}' not in line:
                line = re.sub(r'\{("([^"]+)")\}', r'{{\1}}', line)
                # Also fix: {"Label") -> {{"Label"}}
                line = re.sub(r'\{"([^"]+)"\)', r'{{"\1"}}', line)
            
            # Fix chained arrows - split into separate lines
            # A --> B --> C should become:
            # A --> B
            # B --> C  
            import re
            if " --> " in line or "-->" in line:
                # Check for multiple arrows on one line
                arrow_count = line.count(" --> ") + line.count("-->")
                if arrow_count > 1:
                    # Split by arrows
                    parts = re.split(r'\s*-->\s*', line)
                    if len(parts) > 2:
                        # Extract node IDs and rebuild as separate connections
                        new_connections = []
                        for i in range(len(parts) - 1):
                            left = parts[i].strip()
                            right = parts[i + 1].strip()
                            
                            # Extract node ID from left
                            left_id = re.search(r'^([A-Z])', left)
                            # Extract node ID from right
                            right_id = re.search(r'^([A-Z])', right)
                            
                            if left_id and right_id:
                                new_connections.append(f"{left_id.group(1)} --> {right_id.group(1)}")
                        
                        if new_connections:
                            # If first part is a full node definition, keep it; otherwise just use connections
                            if re.match(r'^[A-Z]', parts[0]) and ('[' in parts[0] or '(' in parts[0] or '{' in parts[0]):
                                # It's a node definition, keep it separate
                                node_def = parts[0].strip()
                                fixed_lines.append(node_def)
                            
                            # Add all connections
                            for conn in new_connections:
                                fixed_lines.append(conn)
                            continue
            
            # Fix double brackets: [["Label"]] -> ["Label"]
            # Pattern: NODE[["Label"]] should be NODE["Label"]
            if '[["' in line or '["[' in line:
                line = re.sub(r'\[\["([^"]+)"\]\]', r'["\1"]', line)
                line = re.sub(r'\["\[([^\]]+)\]"\]', r'["\1"]', line)
            
            # Remove style statements - user wants shapes only, no colors
            if line.startswith("style "):
                # Skip all style/color statements
                continue
            
            # Fix single parentheses: ("label") -> ["label"] 
            # Single parentheses are not valid Mermaid syntax for nodes
            # Pattern: NODE("label") should be NODE["label"] for rectangular
            # Also fix: NODE("label") without quotes -> NODE["label"]
            if '(' in line and ')' in line and not line.strip().startswith('graph'):
                # Check if it's a single-parentheses node pattern
                # Pattern: NODE("Label") or NODE(Label)
                single_paren_pattern = r'([A-Z])\(([^()]+)\)(?!\))'
                if re.search(single_paren_pattern, line):
                    # Convert single parentheses to rectangular brackets
                    # First, handle quoted labels: ("Label") -> ["Label"]
                    line = re.sub(r'\((".*?")\)(?!\))', r'[\1]', line)
                    # Then handle unquoted: (Label) -> ["Label"]
                    line = re.sub(r'([A-Z])\(([^()"]+)\)(?!\))', r'\1["\2"]', line)
            
            # Remove trailing spaces inside brackets/braces/parentheses
            # Fix: ["Label "] -> ["Label"]
            line = re.sub(r'\["([^"]*?)\s+"\]', r'["\1"]', line)
            # Fix: (("Label ")) -> (("Label"))
            line = re.sub(r'\(\("([^"]*?)\s+"\)\)', r'(("\1"))', line)
            # Fix: {{Label }} -> {{Label}}
            line = re.sub(r'\{\{([^}]*?)\s+\}\}', r'{{\1}}', line)
            # Fix: ([Label ]) -> ([Label])
            line = re.sub(r'\(\[([^\]]*?)\s+\]\)', r'([\1])', line)
            
            # Fix multi-line labels that break syntax
            # Remove lines with unclosed quotes or brackets that span multiple lines
            if line.count('"') % 2 != 0:
                # Unmatched quotes - likely multi-line label, skip this problematic line
                continue
            
            # Keep valid lines (separate style lines)
            if line.startswith("graph"):
                fixed_lines.append(line)
            elif " --> " in line or "-->" in line:
                # Only keep arrow lines if they have proper node syntax
                # Check both sides have valid node IDs
                if re.search(r'[A-Z]', line):
                    fixed_lines.append(line)
            elif '"' in line or "'" in line or "[" in line or "(" in line or "{" in line:
                # Valid node definition line - but check it's not broken
                # Skip if it looks like a broken multi-line label
                if not (line.count('(') > 2 and line.count(')') < 2):
                    fixed_lines.append(line)
        
        # Return only node definitions (no style statements)
        return "\n".join(fixed_lines)
    
    def _clean_mermaid_code(self, code: str) -> str:
        """
        Remove markdown code blocks and extra formatting from LLM output.
        
        Args:
            code: Raw code string from LLM
        
        Returns:
            Cleaned Mermaid code string
        """
        # Remove leading/trailing whitespace
        code = code.strip()
        
        # Remove markdown code blocks
        if code.startswith("```"):
            lines = code.split("\n")
            # Skip first line if it's a code block marker
            if lines[0].startswith("```"):
                lines = lines[1:]
            # Remove last line if it's a closing marker
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            code = "\n".join(lines)
        
        return code.strip()
    
    def is_available(self) -> bool:
        """
        Check if LLM generation is available (API key configured).
        
        Returns:
            True if LLM can be used, False otherwise
        """
        return self.client is not None


# Example usage and testing
if __name__ == "__main__":
    import sys
    
    # Get API key from environment or argument
    api_key = os.getenv("GEMINI_API_KEY")
    if len(sys.argv) > 1 and sys.argv[1] != "--help":
        api_key = sys.argv[1]
    
    if not api_key:
        print("Usage: python llm_graph_generator.py [GEMINI_API_KEY]")
        print("Or set GEMINI_API_KEY environment variable")
        print("\nExample:")
        print('  python llm_graph_generator.py "AIza..."')
        print('  export GEMINI_API_KEY="AIza..." && python llm_graph_generator.py')
        print("\nNote: Get your API key from https://makersuite.google.com/app/apikey")
        sys.exit(1)
    
    # Test the generator
    generator = LLMGraphGenerator(api_key=api_key)
    
    test_topic = input("Enter a topic to test LLM generation: ").strip()
    if not test_topic:
        test_topic = "Photosynthesis Process"
        print(f"Using default topic: {test_topic}")
    
    print(f"\n[INFO] Generating flowchart for: {test_topic}")
    print("   (This may take a few seconds...)\n")
    
    result = generator.generate_graph_with_ids(test_topic)
    
    if result:
        print("[OK] Successfully generated Mermaid code:\n")
        print("=" * 60)
        print(result)
        print("=" * 60)
        newline_char = '\n'
        print(f"\n[OK] Generated {len([line for line in result.split(newline_char) if '-->' in line])} connections")
        print(f"[OK] Code length: {len(result)} characters")
    else:
        print("[ERROR] Failed to generate flowchart")
