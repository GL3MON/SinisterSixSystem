import subprocess
import os

def pdf_compiler_node(state):
    """
    LangGraph node that triggers the PDF compilation.
    """
    print("📍 [DEBUG] Entered PDF Compiler Node")
    tex_path = state.get("file_path")
    
    if not tex_path:
        print("❌ Error: No file_path found in state.")
        return state
        
    pdf_path = compile_latex_to_pdf(tex_path)
    return {**state, "pdf_path": pdf_path}

def compile_latex_to_pdf(tex_file_path):
    """
    Compiles a .tex file into a .pdf using MiKTeX's pdflatex.
    """
    if not os.path.exists(tex_file_path):
        print(f"❌ Error: File {tex_file_path} not found.")
        return None

    output_dir = os.path.dirname(tex_file_path)
    file_name = os.path.basename(tex_file_path)
    
    print(f"📄 Compiling {file_name}...")

    try:
        command = [
            "pdflatex",
            "-interaction=nonstopmode",
            f"-output-directory={output_dir}",
            tex_file_path
        ]

        # Run twice for proper reference rendering
        for _ in range(2):
            result = subprocess.run(
                command, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True
            )

        if result.returncode == 0:
            pdf_path = tex_file_path.replace(".tex", ".pdf")
            print(f"✅ SUCCESS: PDF generated at {pdf_path}")
            
            # Cleanup auxiliary files
            cleanup_extensions = [".aux", ".log", ".out"]
            for ext in cleanup_extensions:
                aux_file = tex_file_path.replace(".tex", ext)
                if os.path.exists(aux_file):
                    os.remove(aux_file)
            
            return pdf_path
        else:
            print(f"❌ LaTeX Error: \n{result.stdout}")
            return None

    except FileNotFoundError:
        print("❌ Error: 'pdflatex' not found. Is MiKTeX installed and added to PATH?")
        return None