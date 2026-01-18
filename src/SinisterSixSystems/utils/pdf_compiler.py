import subprocess
import os

def compile_latex_to_pdf(tex_file_path):
    """
    Compiles a .tex file into a .pdf using MiKTeX's pdflatex.
    """
    if not os.path.exists(tex_file_path):
        print(f"❌ Error: File {tex_file_path} not found.")
        return None

    # Get the directory and filename
    output_dir = os.path.dirname(tex_file_path)
    file_name = os.path.basename(tex_file_path)
    
    print(f"📄 Compiling {file_name}...")

    try:
        # pdflatex command
        # -interaction=nonstopmode: Don't stop for errors
        # -output-directory: Where to put the PDF
        command = [
            "pdflatex",
            "-interaction=nonstopmode",
            f"-output-directory={output_dir}",
            tex_file_path
        ]

        # Run the command
        # We run it twice because LaTeX needs two passes for references/table of contents
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
            
            # Clean up auxiliary files (.log, .aux) created by LaTeX
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