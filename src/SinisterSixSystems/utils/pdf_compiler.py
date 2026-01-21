import subprocess
import os
from SinisterSixSystems.utils.savers import sanitize_filename

def pdf_compiler_node(state):
    """
    LangGraph node that triggers the PDF compilation.
    """
    print("📍 [DEBUG] Entered PDF Compiler Node")
    filepath = state.get("file_path")
    tex_path = os.path.join(filepath, f"latex/{sanitize_filename(state['user_input'])}.tex")

    if not tex_path:
        print("❌ Error: No file_path found in state.")
        return state
        
    pdf_path = compile_latex_to_pdf(state, filepath)
    return {**state, "pdf_path": pdf_path}

def compile_latex_to_pdf(state, file_path):
    """
    Compiles a .tex file into a .pdf using MiKTeX's pdflatex.
    """
    if not os.path.exists(file_path):
        print(f"❌ Error: File {file_path} not found.")
        return None

    output_dir = os.path.join(os.path.dirname(file_path), "pdf")
    os.makedirs(output_dir, exist_ok=True)

    file_name = os.path.basename(file_path)
    tex_file_path = os.path.join(file_path, f"latex/{sanitize_filename(state['user_input'])}.tex")
    pdf_path = os.path.join(file_path, f"pdf/{sanitize_filename(state['user_input'])}.pdf")

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