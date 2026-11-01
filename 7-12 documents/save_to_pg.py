import os
import json
import psycopg2
from psycopg2.extras import Json

FOLDER = r"C:\Users\Shubham\Documents\project\7-12 documents"
SOURCE_FILE = "712_GAT_107-2_ORIGINAL.pdf"

def load(name):
    with open(os.path.join(FOLDER, name), encoding="utf-8") as f:
        return json.load(f)

rec = load("clean_record.json")
raw712 = load("extract_712.json")
rawf12 = load("extract_form12.json")

SCHEMA = """
CREATE TABLE IF NOT EXISTS land_records (
    id BIGSERIAL PRIMARY KEY,
    village_code TEXT NOT NULL,
    village_name TEXT,
    taluka TEXT,
    district TEXT,
    pu_id TEXT,
    survey_no TEXT NOT NULL,
    holding_type TEXT,
    local_name TEXT,
    account_no TEXT,
    non_agricultural_area TEXT,
    assessment TEXT,
    other_rights TEXT,
    pending_mutation TEXT,
    last_mutation_no TEXT NOT NULL,
    last_mutation_date TEXT,
    old_mutation_numbers JSONB,
    form12_note TEXT,
    source_file TEXT,
    needs_review BOOLEAN NOT NULL DEFAULT TRUE,
    review_reasons JSONB,
    raw_712_json JSONB,
    raw_form12_json JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (village_code, survey_no, last_mutation_no)
);

CREATE TABLE IF NOT EXISTS owners (
    id BIGSERIAL PRIMARY KEY,
    record_id BIGINT NOT NULL REFERENCES land_records(id) ON DELETE CASCADE,
    name TEXT,
    area TEXT,
    assessment TEXT,
    mutation_no TEXT,
    name_verified BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS crops (
    id BIGSERIAL PRIMARY KEY,
    record_id BIGINT NOT NULL REFERENCES land_records(id) ON DELETE CASCADE,
    year TEXT,
    season TEXT,
    account_no TEXT,
    crop_type TEXT,
    crop_name TEXT,
    irrigated_area TEXT,
    unirrigated_area TEXT,
    irrigation_source TEXT,
    uncultivable_nature TEXT,
    uncultivable_area TEXT,
    remarks TEXT
);
"""

conn = psycopg2.connect()   # reads PGHOST, PGPORT, PGUSER, PGPASSWORD, PGDATABASE

try:
    with conn:                      # one transaction: all saved, or nothing
        with conn.cursor() as cur:
            cur.execute(SCHEMA)

            cur.execute(
                """INSERT INTO land_records
                   (village_code, village_name, taluka, district, pu_id, survey_no,
                    holding_type, local_name, account_no, non_agricultural_area, assessment,
                    other_rights, pending_mutation, last_mutation_no, last_mutation_date,
                    old_mutation_numbers, form12_note, source_file, needs_review,
                    review_reasons, raw_712_json, raw_form12_json)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                   ON CONFLICT (village_code, survey_no, last_mutation_no) DO NOTHING
                   RETURNING id""",
                (
                    rec["village_code"], rec["village_name"], rec["taluka"], rec["district"],
                    rec["pu_id"], rec["survey_no"], rec["holding_type"], rec["local_name"],
                    rec["account_no"], rec["non_agricultural_area"], rec["assessment"],
                    rec["other_rights"], rec["pending_mutation"], rec["last_mutation_no"],
                    rec["last_mutation_date"], Json(rec["old_mutation_numbers"]),
                    rec["form12_note"], SOURCE_FILE, bool(rec["needs_review"]),
                    Json(rec["review_reasons"]), Json(raw712), Json(rawf12),
                ),
            )
            row = cur.fetchone()

            if row is None:
                print("This record (same village, survey no. and last mutation) is already in the database. Nothing was added.")
            else:
                rid = row[0]
                for o in rec["owners"]:
                    cur.execute(
                        """INSERT INTO owners (record_id, name, area, assessment, mutation_no, name_verified)
                           VALUES (%s,%s,%s,%s,%s,FALSE)""",
                        (rid, o["name"], o["area"], o["assessment"], o["mutation_no"]),
                    )
                for c in rec["crop_rows"]:
                    cur.execute(
                        """INSERT INTO crops (record_id, year, season, account_no, crop_type, crop_name,
                           irrigated_area, unirrigated_area, irrigation_source, uncultivable_nature,
                           uncultivable_area, remarks)
                           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                        (rid, c.get("year"), c.get("season"), c.get("account_no"), c.get("crop_type"),
                         c.get("crop_name"), c.get("irrigated_area"), c.get("unirrigated_area"),
                         c.get("irrigation_source"), c.get("uncultivable_nature"),
                         c.get("uncultivable_area"), c.get("remarks")),
                    )
                print("Saved as record id", rid)
except Exception as e:
    print("ERROR: nothing was saved.")
    print(e)
    raise SystemExit(1)

# ---------- Read back what is stored ----------
with conn.cursor() as cur:
    print("\n--- Records in database ---")
    cur.execute("SELECT id, village_name, survey_no, last_mutation_no, needs_review FROM land_records ORDER BY id")
    for r in cur.fetchall():
        print("Record", r[0], "|", r[1], "|", r[2], "| last mutation", r[3], "| needs_review =", r[4])

    print("\n--- Owners ---")
    cur.execute("SELECT record_id, name, area, name_verified FROM owners ORDER BY id")
    for r in cur.fetchall():
        print("Record", r[0], "|", r[1], "| area", r[2], "| verified =", r[3])

    print("\n--- Crops ---")
    cur.execute("SELECT record_id, year, season, crop_name, unirrigated_area FROM crops ORDER BY id")
    for r in cur.fetchall():
        print("Record", r[0], "|", r[1], "|", r[2], "|", r[3], "| unirrigated", r[4])

conn.close()
print("\nDone.")