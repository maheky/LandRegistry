from pdf2image import convert_from_path
import os

POPPLER = r"C:\poppler\poppler-26.09.0\Library\bin"
FOLDER = r"C:\Users\Shubham\Documents\project\7-12 documents"
PDF = os.path.join(FOLDER, "712_GAT_107-2_ORIGINAL.pdf")
OUT = os.path.join(FOLDER, "page_full.png")

if not os.path.exists(PDF):
    raise SystemExit("PDF not found: " + PDF)

print("Rendering at 500 DPI, please wait...")
pages = convert_from_path(PDF, dpi=500, poppler_path=POPPLER)
print("Pages found:", len(pages))

page = pages[0]
page.save(OUT)
print("Image size (width x height):", page.size)
print("Saved to:", OUT)