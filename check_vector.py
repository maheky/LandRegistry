import pypdfium2 as pdfium
import os

files = [f for f in os.listdir(".") if f.endswith(".pdf")]
doc = pdfium.PdfDocument(files[0])
page = doc[0]

# Inspect object types on page 1
image_count = 0
for obj in page.get_objects():
    if obj.type == pdfium.raw.FPDF_PAGEOBJ_IMAGE:
        image_count += 1

print(f"File: {files[0]}")
print(f"Raster images found on page: {image_count}")
print(f"Total graphic objects (paths/lines/text): {len(list(page.get_objects()))}")