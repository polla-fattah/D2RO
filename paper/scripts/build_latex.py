import os
import subprocess
import sys

MIKTEX_BIN = r"C:\Users\Polla\AppData\Local\Programs\MiKTeX\miktex\bin\x64"
PDFLATEX = os.path.join(MIKTEX_BIN, "pdflatex.exe")
BIBTEX = os.path.join(MIKTEX_BIN, "bibtex.exe")
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def run_step(cmd, desc):
    print(f"=== {desc} ===")
    res = subprocess.run(cmd, cwd=BASE_DIR, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"Error during {desc}: Return code {res.returncode}")
        # Print tail of stdout/stderr
        lines = res.stdout.splitlines()[-20:]
        print("\n".join(lines))
        if res.stderr:
            print("STDERR:\n" + res.stderr)
    else:
        print(f"  -> SUCCESS ({desc})")
    return res.returncode

def main():
    print("Starting automated IEEE Transactions LaTeX compilation...")
    run_step([PDFLATEX, "-interaction=nonstopmode", "paper.tex"], "1. PDFLaTeX Pass 1")
    run_step([BIBTEX, "paper"], "2. BibTeX Compilation")
    run_step([PDFLATEX, "-interaction=nonstopmode", "paper.tex"], "3. PDFLaTeX Pass 2 (Linking References)")
    run_step([PDFLATEX, "-interaction=nonstopmode", "paper.tex"], "4. PDFLaTeX Pass 3 (Final Resolution)")
    
    pdf_path = os.path.join(BASE_DIR, "paper.pdf")
    if os.path.exists(pdf_path):
        size_kb = os.path.getsize(pdf_path) / 1024
        print(f"\n=======================================================")
        print(f"  PAPER.PDF SUCCESSFULLY CREATED: {pdf_path}")
        print(f"  File Size: {size_kb:.1f} KB")
        print(f"=======================================================")
    else:
        print("\nFailed to generate paper.pdf")

if __name__ == "__main__":
    main()
