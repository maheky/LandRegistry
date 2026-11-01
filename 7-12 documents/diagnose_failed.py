import os
import re
import json
import glob

FOLDER = r"C:\Users\Shubham\Documents\project\7-12 documents"
OUT = os.path.join(FOLDER, "reports", "diagnosis.txt")
OK_CHARS = re.compile(r"[\u0900-\u097F\s.]")

lines = []


def say(text):
    lines.append(text)
    print(text)


files = sorted(glob.glob(os.path.join(FOLDER, "failed", "*.review.json")))
say("Failed files: " + str(len(files)))

for path in files:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    raw = data.get("raw") or {}
    a = raw.get("extract_712") or {}
    b = raw.get("extract_form12") or {}

    say("")
    say("=== " + os.path.basename(path).replace(".review.json", ""))
    say("Reasons: " + str(data.get("reasons")))
    say("Village 7/12 : " + ascii(a.get("village_name")))
    say("Village f12  : " + ascii(b.get("village_name")))
    say("Survey 7/12 / f12: " + ascii(a.get("survey_no")) + " / " + ascii(b.get("survey_no")))
    say("Last mutation: " + str(a.get("last_mutation_no")))
    say("Old mutations: " + str(a.get("old_mutation_numbers")))
    for o in a.get("owners") or []:
        name = o.get("name") or ""
        odd = [(c, hex(ord(c))) for c in name if not OK_CHARS.fullmatch(c)]
        say("Owner mutation_no: " + str(o.get("mutation_no")) + " | odd characters in name: " + str(odd))
    for r in b.get("crop_rows") or []:
        say("Crop row year: " + ascii(r.get("year")))

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("\nSaved to:", OUT)