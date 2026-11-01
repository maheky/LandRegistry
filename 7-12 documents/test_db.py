import os
import json
import psycopg2
from validate_funcs import build_record
from db_funcs import save_record

FOLDER = r"C:\Users\Shubham\Documents\project\7-12 documents"

def load(name):
    with open(os.path.join(FOLDER, name), encoding="utf-8") as f:
        return json.load(f)

a = load("extract_712.json")
b = load("extract_form12.json")

rec, failures = build_record(a, b, "712_GAT_107-2_ORIGINAL.pdf")
print("Failures:", failures if failures else "none")

status, rid = save_record(rec, a, b)
print("Result:", status, rid)

conn = psycopg2.connect()
cur = conn.cursor()
for table in ("land_records", "owners", "crops"):
    cur.execute("SELECT count(*) FROM " + table)
    print(table + " rows:", cur.fetchone()[0])
conn.close()