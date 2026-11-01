import os
import re
import json
from datetime import datetime

FOLDER = r"C:\Users\Shubham\Documents\project\7-12 documents"

with open(os.path.join(FOLDER, "extract_712.json"), encoding="utf-8") as f:
    a = json.load(f)
with open(os.path.join(FOLDER, "extract_form12.json"), encoding="utf-8") as f:
    b = json.load(f)

reasons = []

def check(ok, label):
    print(("[OK]   " if ok else "[FLAG] ") + label)
    if not ok:
        reasons.append(label)

def first_number(s):
    m = re.findall(r"\d+", str(s or ""))
    return m[0] if m else None

# ---------- 1. Clean ----------
HEADINGS = {"कुळाचे नाव व खंड", "इतर अधिकार", "इतर"}
lines = []
for line in (a.get("other_rights") or "").split("\n"):
    line = line.strip()
    if not line or re.fullmatch(r"[-.\s]+", line) or line in HEADINGS:
        continue
    lines.append(line)
other_rights = " ".join(lines)
rights_refs = re.findall(r"\(\s*(\d+)\s*\)", other_rights)

owners = []
for o in a.get("owners", []):
    owners.append({
        "name": (o.get("name") or "").strip(),
        "area": o.get("area"),
        "assessment": o.get("assessment"),
        "mutation_no": first_number(o.get("mutation_no")),
        "name_verified": False,
    })

old_muts = [first_number(x) for x in a.get("old_mutation_numbers", [])]

record = {
    "village_name": a.get("village_name"),
    "village_code": a.get("village_code"),
    "taluka": a.get("taluka"),
    "district": a.get("district"),
    "pu_id": a.get("pu_id"),
    "survey_no": a.get("survey_no"),
    "holding_type": a.get("holding_type"),
    "local_name": a.get("local_name"),
    "account_no": a.get("account_no"),
    "non_agricultural_area": (a.get("area_details") or {}).get("non_agricultural_area"),
    "assessment": (a.get("area_details") or {}).get("assessment"),
    "owners": owners,
    "other_rights": other_rights,
    "other_rights_mutation_refs": rights_refs,
    "pending_mutation": (a.get("pending_mutation") or "").strip(" ."),
    "last_mutation_no": first_number(a.get("last_mutation_no")),
    "last_mutation_date": a.get("last_mutation_date"),
    "old_mutation_numbers": old_muts,
    "crop_rows": b.get("crop_rows", []),
    "form12_note": b.get("note_text"),
}

# ---------- 2. Validate ----------
print("\n--- Checks ---")
check(bool(re.fullmatch(r"\d{6}", str(record["village_code"]))), "Village code is 6 digits")
check(bool(re.fullmatch(r"\d{11}", str(record["pu_id"]))), "PU-ID is 11 digits")
check(bool(re.fullmatch(r"\d+(/\d+[A-Za-z]?)?", str(record["survey_no"]))), "Survey number has a valid format")

check(a.get("village_code") == b.get("village_code"), "Village code same in 7/12 and form 12")
check(a.get("village_name") == b.get("village_name"), "Village name same in 7/12 and form 12")
check(a.get("survey_no") == b.get("survey_no"), "Survey number same in 7/12 and form 12")

check(bool(re.fullmatch(r"\d+\.\d{2}\.\d{2}", str(record["non_agricultural_area"]))), "Area has format N.NN.NN")
check(bool(re.fullmatch(r"\d+\.\d{2}", str(record["assessment"]))), "Assessment has format N.NN")

if len(owners) == 1:
    check(owners[0]["area"] == record["non_agricultural_area"], "Single owner's area equals total area")
else:
    check(False, "More than one owner: area sum must be checked manually")

check(all(re.fullmatch(r"[\u0900-\u097F\s.]+", o["name"]) for o in owners) and len(owners) > 0,
      "Owner names contain only Devanagari letters")

nums = [int(x) for x in old_muts if x]
check(nums == sorted(nums) and len(nums) == len(set(nums)), "Old mutation numbers are in ascending order")
check(bool(nums) and record["last_mutation_no"] == str(max(nums)), "Last mutation number is the highest in the old list")
check(all(o["mutation_no"] in old_muts for o in owners), "Each owner's mutation number appears in the old list")
check(all(r in old_muts for r in rights_refs), "Mutation numbers inside the rights text appear in the old list")

try:
    datetime.strptime(str(record["last_mutation_date"]), "%d/%m/%Y")
    ok_date = True
except ValueError:
    ok_date = False
check(ok_date, "Last mutation date is a valid dd/mm/yyyy date")

check(len(record["crop_rows"]) > 0, "Form 12 has at least one crop row")
for i, row in enumerate(record["crop_rows"], 1):
    check(bool(re.fullmatch(r"\d{4}-\d{2}", str(row.get("year")))), "Crop row " + str(i) + ": year looks like 2020-21")
    areas = [row.get("irrigated_area"), row.get("unirrigated_area")]
    check(any(x for x in areas) and all(x is None or re.fullmatch(r"\d+\.\d+", str(x)) for x in areas),
          "Crop row " + str(i) + ": has a numeric area")

# Gemini's own doubts
for name, src in (("7/12", a), ("form 12", b)):
    if src.get("uncertain_fields"):
        check(False, name + " uncertain fields reported by model: " + ", ".join(src["uncertain_fields"]))

# ---------- 3. Needs review ----------
reasons.append("Owner names and other text must be checked by a human before they are trusted")
record["needs_review"] = True
record["review_reasons"] = reasons

out = os.path.join(FOLDER, "clean_record.json")
with open(out, "w", encoding="utf-8") as f:
    json.dump(record, f, ensure_ascii=False, indent=2)

print("\nNeeds review:", record["needs_review"])
print("Reasons:")
for r in reasons:
    print(" -", r)
print("\nSaved to:", out)