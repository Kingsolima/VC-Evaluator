# utils/pdf.py
import os
from fpdf import FPDF

def generate_pdf_from_text(text: str, output_path: str):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=12)

    lines = text.strip().split("\n")
    for line in lines:
        pdf.multi_cell(0, 10, line)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    pdf.output(output_path)
    return output_path
