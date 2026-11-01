import os
import re
import csv
import glob
from datetime import datetime
import psycopg2

FOLDER = r"C:\Users\Shubham\Documents\project\7-12 documents"
REPORTS = os.path.join(FOLDER, "reports")

SCHEMA = """
CREATE TABLE IF NOT EXISTS processing_log (
    id BIGSERIAL PRIMARY KEY,
    run_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    file_name TEXT NOT NULL,
    status TEXT NOT NULL,
    record_id BIGINT,
    survey_no TEXT,
    village TEXT,
    owners TEXT,
    reasons TEXT,
    raw_json JSONB
);
CREATE INDEX IF NOT EXISTS processing_log_file_idx ON processing_log (file_name, run_at);
CREATE OR REPLACE VIEW latest_status AS
SELECT DISTINCT ON (file_name)
       file_name, status, record_id, survey_no, village, owners, reasons, run_at
FROM processing_log
ORDER BY file_name, run_at DESC, id DESC;
"""

INSERT = """INSERT INTO processing_log
            (run_at, file_name, status, record_id, survey_no, village, owners, reasons)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)"""

conn = psycopg2.connect()
with conn:
    with conn.cursor() as cur:
        cur.execute(SCHEMA)
        cur.execute("SELECT count(*) FROM processing_log")
        existing = cur.fetchone()[0]

        if existing:
            print("The log already has", existing, "rows. Import of old reports skipped.")
        else:
            total = 0
            for path in sorted(glob.glob(os.path.join(REPORTS, "report_*.csv"))):
                m = re.search(r"report_(\d{8})_(\d{6})", os.path.basename(path))
                when = datetime.strptime(m.group(1) + m.group(2), "%Y%m%d%H%M%S") if m else datetime.now()
                count = 0
                with open(path, encoding="utf-8-sig", newline="") as f:
                    for row in csv.DictReader(f):
                        rid = row.get("record_id") or None
                        cur.execute(INSERT, (
                            when, row["file"], row["status"],
                            int(rid) if rid else None,
                            row.get("survey_no") or None, row.get("village") or None,
                            row.get("owners") or None, row.get("reasons") or None,
                        ))
                        count += 1
                total += count
                print("Imported", count, "rows from", os.path.basename(path))
            print("Imported", total, "rows in total.")
conn.close()
print("Done.")