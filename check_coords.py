import pypdfium2 as pdfium
import os
import re

PDF_FOLDER = "."

# Common keywords in Indian cadastral survey reports
COORD_PATTERN = re.compile(r"(Easting|Northing|X-Coord|Y-Coord|Coordinate|Traverse|Latitude|Longitude|V1|V2)", re.IGNORECASE)

files = [f for f in os.listdir(PDF_FOLDER) if f.endswith(".pdf")]
print(f"Scanning {len(files)} files for coordinate tables...")

found_any = False

for file_name in files:
    file_path = os.path.join(PDF_FOLDER, file_name)
    pdf = pdfium.PdfDocument(file_path)
    
    for page_idx, page in enumerate(pdf):
        text = page.get_textpage().get_text_range()
        matches = COORD_PATTERN.findall(text)
        if len(matches) >= 3:
            print(f"\nPotential coordinate data in: {file_name} (Page {page_idx + 1})")
            print("Snippet:")
            # Print a snippet around the match
            lines = [line.strip() for line in text.split("\n") if line.strip()]
            for line in lines[:15]:
                print(f"  {line}")
            found_any = True
            break
    if found_any:
        break

if not found_any:
    print("\nNo coordinate/traverse text tables detected in the text layer of the PDFs.")