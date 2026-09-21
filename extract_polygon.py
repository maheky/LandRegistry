import ctypes
import pypdfium2 as pdfium
import pypdfium2.raw as pdfium_c

doc = pdfium.PdfDocument("CAD_GAT_1.pdf")
page = doc[0]

path_objects = [obj for obj in page.get_objects() if obj.type == pdfium_c.FPDF_PAGEOBJ_PATH]
print(f"Total vector paths found: {len(path_objects)}")

found_candidates = []

for idx, path in enumerate(path_objects):
    left, bottom, right, top = path.get_bounds()
    width = right - left
    height = top - bottom
    
    # Filter out borders, full page bounds, or very small ticks
    if 50 < width < 500 and 50 < height < 400:
        found_candidates.append((idx, width, height, path))

print(f"Candidate Parcel Paths: {len(found_candidates)}")

x_val = ctypes.c_float()
y_val = ctypes.c_float()

for idx, w, h, path in found_candidates:
    num_segments = pdfium_c.FPDFPath_CountSegments(path.raw)
    points = []
    
    for s_idx in range(num_segments):
        seg = pdfium_c.FPDFPath_GetPathSegment(path.raw, s_idx)
        success = pdfium_c.FPDFPathSegment_GetPoint(seg, ctypes.byref(x_val), ctypes.byref(y_val))
        if success:
            points.append((round(x_val.value, 2), round(y_val.value, 2)))
            
    # Check if this path forms a multi-vertex polygon (your Gat 1 boundary has ~14-16 vertices)
    if 10 <= len(points) <= 30:
        print(f"\nMatch Found -> Path Index: {idx} | Vertices Count: {len(points)}")
        print(f"Bounding Dimensions: Width={w:.2f} pt, Height={h:.2f} pt")
        print(f"Vertex Coordinates (X, Y in PDF points):")
        for p_idx, pt in enumerate(points):
            print(f"  V{p_idx + 1}: {pt}")