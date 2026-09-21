import os
import re
import math
import ctypes
import pypdfium2 as pdfium
import pypdfium2.raw as pdfium_c
import psycopg2

DB_CONFIG = {
    "dbname": "land_registry",
    "user": "postgres",
    "password": "mahek",  # <-- Your pgAdmin password
    "host": "localhost",
    "port": "5433"
}

PDF_FOLDER = "."

BASE_ORIGIN_X = 323500.0
BASE_ORIGIN_Y = 2092400.0
PLOT_SPACING_METERS = 250.0
GRID_COLUMNS = 7

BLOCK_SPLIT_REGEX = re.compile(r"(?=Survey\s*No\.?\s*:)", re.IGNORECASE)
SURVEY_REGEX = re.compile(r"Survey\s*No\.?\s*:\s*([^\n\r]+?)(?=(?:Total\s*Area|Pot|Owner|$))", re.IGNORECASE)
TOTAL_AREA_REGEX = re.compile(r"Total\s*Area\s*:\s*([\d\.]+)", re.IGNORECASE)
POT_KHARABA_REGEX = re.compile(r"Pot\s*kharaba\s*:\s*([\d\.]+)", re.IGNORECASE)
OWNER_REGEX = re.compile(r"Owner\s*Name\s*:\s*(.+?)(?=(?:Khata\s*No\.?|$))", re.IGNORECASE | re.DOTALL)
KHATA_REGEX = re.compile(r"Khata\s*No\.?\s*:\s*(\d+)", re.IGNORECASE)

def calculate_polygon_area(points):
    area = 0.0
    for i in range(len(points) - 1):
        area += points[i][0] * points[i + 1][1] - points[i + 1][0] * points[i][1]
    return abs(area) / 2.0

def extract_true_parcel_polygon(page):
    path_objects = [obj for obj in page.get_objects() if obj.type == pdfium_c.FPDF_PAGEOBJ_PATH]
    x_val, y_val = ctypes.c_float(), ctypes.c_float()
    candidates = []

    for path in path_objects:
        left, bottom, right, top = path.get_bounds()
        w, h = right - left, top - bottom
        
        if 50 < w < 450 and 50 < h < 350:
            num_segments = pdfium_c.FPDFPath_CountSegments(path.raw)
            if 10 <= num_segments <= 60:
                pts = []
                for s in range(num_segments):
                    seg = pdfium_c.FPDFPath_GetPathSegment(path.raw, s)
                    if pdfium_c.FPDFPathSegment_GetPoint(seg, ctypes.byref(x_val), ctypes.byref(y_val)):
                        pts.append((round(x_val.value, 2), round(y_val.value, 2)))
                
                has_sheet_margin_clip = any(pt[0] <= 0 or pt[1] <= 0 for pt in pts)
                if len(pts) >= 6 and not has_sheet_margin_clip:
                    dx = pts[0][0] - pts[-1][0]
                    dy = pts[0][1] - pts[-1][1]
                    if math.sqrt(dx * dx + dy * dy) < 5.0:
                        poly_area = calculate_polygon_area(pts)
                        candidates.append((poly_area, pts))

    if candidates:
        candidates.sort(key=lambda x: x[0], reverse=True)
        return candidates[0][1], candidates[0][0]

    return None, 0.0

def parse_pdf(pdf_path, grid_index):
    doc = pdfium.PdfDocument(pdf_path)
    page = doc[0]
    
    text = "\n".join([p.get_textpage().get_text_range() for p in doc])
    blocks = BLOCK_SPLIT_REGEX.split(text)
    
    records_map = {}
    for block in blocks:
        if not block.strip():
            continue
        s_m = SURVEY_REGEX.search(block)
        a_m = TOTAL_AREA_REGEX.search(block)
        p_m = POT_KHARABA_REGEX.search(block)
        o_m = OWNER_REGEX.search(block)
        k_m = KHATA_REGEX.search(block)

        if s_m and a_m and o_m and k_m:
            survey_no = re.sub(r"\s+", "", s_m.group(1).strip())
            total_area = float(a_m.group(1).strip())
            pot_kharaba = float(p_m.group(1).strip()) if p_m else 0.0
            owner_clean = re.sub(r"[-_]+$", "", o_m.group(1).strip())
            owner_clean = re.sub(r"\s+", " ", owner_clean)
            khata_no = k_m.group(1).strip()
            
            if survey_no not in records_map:
                records_map[survey_no] = {
                    "survey_gat_no": survey_no,
                    "khata_no": khata_no,
                    "total_area_ha": total_area,
                    "pot_kharaba_ha": pot_kharaba,
                    "owner_names": owner_clean
                }

    records = list(records_map.values())
    raw_points, canvas_area = extract_true_parcel_polygon(page)
    
    gat_total_ha = sum(r["total_area_ha"] for r in records) if records else 1.0
    wkt_geom = None

    col = grid_index % GRID_COLUMNS
    row = grid_index // GRID_COLUMNS
    origin_x = BASE_ORIGIN_X + (col * PLOT_SPACING_METERS)
    origin_y = BASE_ORIGIN_Y - (row * PLOT_SPACING_METERS)

    if raw_points and canvas_area > 0 and gat_total_ha > 0:
        target_m2 = gat_total_ha * 10000.0
        scale = math.sqrt(target_m2 / canvas_area)
        
        min_x = min(p[0] for p in raw_points)
        min_y = min(p[1] for p in raw_points)
        
        utm_pts = []
        for x, y in raw_points:
            ux = origin_x + (x - min_x) * scale
            uy = origin_y + (y - min_y) * scale
            utm_pts.append(f"{ux:.2f} {uy:.2f}")
            
        if utm_pts[0] != utm_pts[-1]:
            utm_pts.append(utm_pts[0])
            
        wkt_geom = f"POLYGON(({', '.join(utm_pts)}))"

    base_gat = records[0]["survey_gat_no"].split("/")[0] if records else "1"
    
    # Collect real khata numbers (e.g., '528, 529') instead of 'GAT_PARENT'
    unique_khatas = sorted(list(set(r["khata_no"] for r in records)))
    combined_khata_str = ", ".join(unique_khatas) if unique_khatas else "N/A"

    return records, wkt_geom, base_gat, gat_total_ha, combined_khata_str

def run_pipeline():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    cur.execute("""
        DROP TABLE IF EXISTS cadastral_parcels CASCADE;
        CREATE TABLE cadastral_parcels (
            id SERIAL PRIMARY KEY,
            survey_gat_no TEXT UNIQUE NOT NULL,
            khata_no TEXT NOT NULL,
            total_area_ha NUMERIC(10, 4) NOT NULL,
            pot_kharaba_ha NUMERIC(10, 4) NOT NULL DEFAULT 0.0000,
            cultivable_area_ha NUMERIC(10, 4) GENERATED ALWAYS AS (total_area_ha - pot_kharaba_ha) STORED,
            owner_names TEXT NOT NULL,
            geom GEOMETRY(Polygon, 4326),
            created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX idx_parcels_gat ON cadastral_parcels(survey_gat_no);
        CREATE INDEX idx_parcels_geom ON cadastral_parcels USING GIST(geom);
    """)
    conn.commit()

    files = sorted([f for f in os.listdir(PDF_FOLDER) if f.endswith(".pdf")])
    print(f"Ingesting {len(files)} files...")

    for idx, file_name in enumerate(files):
        file_path = os.path.join(PDF_FOLDER, file_name)
        records, wkt_geom, base_gat, gat_total_ha, combined_khata_str = parse_pdf(file_path, idx)

        # 1. Insert parent Gat with its real Khata number(s)
        if wkt_geom:
            cur.execute("""
                INSERT INTO cadastral_parcels (
                    survey_gat_no, khata_no, total_area_ha, pot_kharaba_ha, owner_names, geom
                )
                VALUES (%s, %s, %s, 0.0000, %s, ST_Transform(ST_SetSRID(ST_GeomFromText(%s), 32643), 4326))
                ON CONFLICT (survey_gat_no) DO UPDATE 
                SET geom = EXCLUDED.geom, khata_no = EXCLUDED.khata_no;
            """, (base_gat, combined_khata_str, gat_total_ha, f"Gat {base_gat} Outer Boundary", wkt_geom))

        # 2. Insert the child sub-divisions with their exact individual Khata numbers
        for rec in records:
            cur.execute("""
                INSERT INTO cadastral_parcels (
                    survey_gat_no, khata_no, total_area_ha, pot_kharaba_ha, owner_names
                )
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (survey_gat_no) DO NOTHING;
            """, (
                rec["survey_gat_no"], rec["khata_no"], 
                rec["total_area_ha"], rec["pot_kharaba_ha"], 
                rec["owner_names"]
            ))

    conn.commit()
    cur.close()
    conn.close()
    print("Database updated: Khata numbers normalized and geometry synced.")

if __name__ == "__main__":
    run_pipeline()