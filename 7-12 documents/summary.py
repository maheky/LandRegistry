import os
import csv
import json
import glob
from collections import Counter
import psycopg2

FOLDER = r"C:\Users\Shubham\Documents\project\7-12 documents"
REPORTS = os.path.join(FOLDER, "reports")
os.makedirs(REPORTS, exist_ok=True)

conn = psycopg2.connect()
cur = conn.cursor()

cur.execute("""
    SELECT DISTINCT ON (file_name)
           file_name, status, record_id, survey_no, village, owners, reasons, run_at, raw_json
    FROM processing_log
    ORDER BY file_name, run_at DESC, id DESC
""")
latest = {r[0]: r for r in cur.fetchall()}

cur.execute("SELECT file_name, count(*) FROM processing_log GROUP BY file_name")
tries = dict(cur.fetchall())

cur.execute("SELECT count(*) FROM land_records")
db_records = cur.fetchone()[0]
conn.close()

pdfs = sorted(os.path.basename(p) for p in glob.glob(os.path.join(FOLDER, "712_GAT_*.pdf")))
names = sorted(set(pdfs) | set(latest))

rows = []
counts = Counter()
reason_counts = Counter()
failed_details = []

for name in names:
    r = latest.get(name)
    if r is None:
        counts["pending"] += 1
        rows.append({"file": name, "status": "pending", "tries": 0, "last_run": "",
                     "record_id": "", "survey_no": "", "village": "", "owners": "", "reasons": ""})
        continue

    _, status, rid, survey, village, owners, reasons, run_at, raw = r
    counts[status] += 1
    rows.append({"file": name, "status": status, "tries": tries.get(name, 1),
                 "last_run": str(run_at)[:19], "record_id": rid or "",
                 "survey_no": survey or "", "village": village or "",
                 "owners": owners or "", "reasons": reasons or ""})

    if status == "failed_validation":
        for part in (reasons or "").split(" | "):
            reason_counts[part] += 1
    if status == "error":
        reason_counts["ERROR: " + (reasons or "")[:70]] += 1
    if status in ("failed_validation", "error"):
        failed_details.append({"file": name, "status": status, "reasons": reasons, "raw": raw})

master = os.path.join(REPORTS, "master_report.csv")
cols = ["file", "status", "tries", "last_run", "record_id", "survey_no", "village", "owners", "reasons"]
with open(master, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols)
    w.writeheader()
    w.writerows(rows)

details = os.path.join(REPORTS, "failed_details.json")
with open(details, "w", encoding="utf-8") as f:
    json.dump(failed_details, f, ensure_ascii=False, indent=1)

print("================ OVERALL SUMMARY ================")
print("PDF files in the project folder :", len(pdfs))
print("Records in the database         :", db_records)
print("")
print("Latest status of each file:")
for s in ("saved", "duplicate", "failed_validation", "error", "pending"):
    print("  " + s.ljust(18), counts.get(s, 0))
print("")
if reason_counts:
    print("Most common reasons for failure:")
    for reason, n in reason_counts.most_common(10):
        print("  " + str(n).rjust(3), "x", reason)
print("")
print("Master report  :", master)
print("Failed details :", details, "(", len(failed_details), "files )")