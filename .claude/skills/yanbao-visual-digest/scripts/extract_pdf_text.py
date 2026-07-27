#!/usr/bin/env python3
"""Dump the full text of a research-report PDF so you can read the WHOLE thing before selecting.

Usage:
    python extract_pdf_text.py <report.pdf> [start_page] [end_page]

Reads every page by default. If a chart's numbers only live in the image (text
extraction returns little), render that page instead:
    python -c "import fitz; fitz.open('r.pdf')[15].get_pixmap(dpi=140).save('p16.png')"
then Read the PNG.
"""
import sys
import fitz  # pymupdf

if len(sys.argv) < 2:
    sys.exit("usage: extract_pdf_text.py <report.pdf> [start] [end]")
path = sys.argv[1]
doc = fitz.open(path)
n = len(doc)
a = int(sys.argv[2]) if len(sys.argv) > 2 else 1
b = int(sys.argv[3]) if len(sys.argv) > 3 else n
print(f"FILE: {path}\nPAGES: {n}\n")
for i in range(max(0, a - 1), min(b, n)):
    print(f"\n\n========== PAGE {i+1} ==========")
    print(doc[i].get_text())
