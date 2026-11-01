import os
import json
import copy
from validate_funcs import build_record

FOLDER = r"C:\Users\Shubham\Documents\project\7-12 documents"

def load(name):
    with open(os.path.join(FOLDER, name), encoding="utf-8") as f:
        return json.load(f)

a = load("extract_712.json")
b = load("extract_form12.json")

print("=== TEST 1: your real data ===")
rec, failures = build_record(a, b, "712_GAT_107-2_ORIGINAL.pdf")
print("Failures:", failures if failures else "none")
print("Notes:")
for n in rec["review_reasons"]:
    print(" -", n)
print("Owners:", [o["name"] for o in rec["owners"]])
print("Crop rows:", len(rec["crop_rows"]))
print("Old mutations:", len(rec["old_mutation_numbers"]))

print("\n=== TEST 2: data broken on purpose ===")
a2 = copy.deepcopy(a)
a2["area_details"]["assessment"] = "7O9.00"      # letter O instead of zero
a2["last_mutation_no"] = "5818"                   # not the highest mutation
a2["village_code"] = "55361"                      # one digit missing
rec2, failures2 = build_record(a2, b, "broken.pdf")
print("Failures found:", len(failures2))
for f in failures2:
    print(" -", f)