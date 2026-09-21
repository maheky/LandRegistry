import os
import re
import pypdfium2 as pdfium
import psycopg2

DB_CONFIG = {
    "dbname": "land_registry",
    "user": "postgres",
    "password": "mahek",  # <-- Put your actual pgAdmin password
    "host": "localhost",
    "port": "5433"
}

PDF_FOLDER = "."

# Pattern that accurately extracts all 5 fields
RECORD_REGEX = re.compile(
    r"Survey\s*No\.?\s*:\s*(?P<survey>[^\n\r]+?)\s*"
    r"Total\s*Area\s*:\s*(?P<total_area>[\d\.]+)\s*"
     r"Khata\s*No\.?\s*:\s*(?P<khata>\d+)\s*"
    r"Pot\s*kharaba\s*:\s*(?P<pot_kharaba>[\d\.]+)\s*"
    r"Owner\s*Name\s*:\s*(?P<owner>.+?)",
    re.DOTALL | re.IGNORECASE
)

def extract_clean_text(pdf_path):
    pdf = pdfium.PdfDocument(pdf_path)
    full_text = []
    for page in pdf:
        text_page = page.get_textpage()
        num_rects = text_page.count_rects()
        words = []
        for i in range(num_rects):
            w = text_page.get_text_bounded(*text_page.get_rect(i))
            if w:
                words.append(w)
        page_str = " ".join(words) if words else text_page.get_text_range()
        full_text.append(page_str)
    return "\n".join(full_text)

def parse_pdf(pdf_path):
    raw_text = extract_clean_text(pdf_path)
    extracted = []

    for match in RECORD_REGEX.finditer(raw_text):
        survey_gat = match.group("survey").strip()
        survey_gat = re.sub(r"\s+", "", survey_gat)

        total_area = float(match.group("total_area").strip())
        pot_kharaba = float(match.group("pot_kharaba").strip())

        owner_str = match.group("owner").strip()
        owner_clean = re.sub(r"\s+", " ", owner_str)

        khata_no = match.group("khata").strip()

        parts = survey_gat.split("/", 1)
        base_gat = parts[0]
        sub_div = parts[1] if len(parts) > 1 else None

        extracted.append({
            "survey_gat_no": survey_gat,
            "base_gat_no": base_gat,
            "sub_division_no": sub_div,
            "total_area_ha": total_area,
            "pot_kharaba_ha": pot_kharaba,
            "owner_names": owner_clean,
            "khata_no": khata_no
        })
    return extracted

def run_import():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    cur.execute("SELECT village_id FROM villages WHERE village_name = 'कडाव' LIMIT 1;")
    row = cur.fetchone()
    if not row:
        print("Village 'कडाव' not found.")
        return
    village_id = row[0]

    files = [f for f in os.listdir(PDF_FOLDER) if f.endswith(".pdf")]
    print(f"Reading {len(files)} PDF files...")

    total_inserted = 0

    for file_name in files:
        file_path = os.path.join(PDF_FOLDER, file_name)
        plots = parse_pdf(file_path)

        for p in plots:
            # 1. Insert into khatas
            cur.execute("""
                INSERT INTO khatas (village_id, khata_no)
                VALUES (%s, %s)
                ON CONFLICT (village_id, khata_no) DO NOTHING;
            """, (village_id, p["khata_no"]))

            cur.execute("""
                SELECT khata_id FROM khatas 
                WHERE village_id = %s AND khata_no = %s;
            """, (village_id, p["khata_no"]))
            khata_id = cur.fetchone()[0]

            # 2. Insert into cadastral_parcels with both khata_id and khata_no column
            cur.execute("""
                INSERT INTO cadastral_parcels (
                    village_id, khata_id, khata_no, survey_gat_no, 
                    base_gat_no, sub_division_no, 
                    total_area_ha, pot_kharaba_ha, owner_names
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (village_id, survey_gat_no) DO NOTHING;
            """, (
                village_id, khata_id, p["khata_no"], p["survey_gat_no"],
                p["base_gat_no"], p["sub_division_no"],
                p["total_area_ha"], p["pot_kharaba_ha"],
                p["owner_names"]
            ))
            total_inserted += 1

    conn.commit()
    cur.close()
    conn.close()
    print(f"Done! Cleanly inserted {total_inserted} plot records with separate Khata numbers.")

if __name__ == "__main__":
    run_import()