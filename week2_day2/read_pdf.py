"""
Reads a PDF file and prints the extracted text.

Run: python read_pdf.py
"""

import os
import sys
from pypdf import PdfReader

sys.stdout.reconfigure(encoding="utf-8")

script_dir = os.path.dirname(os.path.abspath(__file__))
pdf_path = os.path.join(script_dir, "CENG 202. _Week5. Lecture 10-Stack.pdf")

reader = PdfReader(pdf_path)

text = ""
for page in reader.pages:
    text += page.extract_text()

print(text)
