import os
from extract_funcs import render_and_crop, extract_json
from prompts import PROMPT_712, PROMPT_FORM12

FOLDER = r"C:\Users\Shubham\Documents\project\7-12 documents"
PDF = os.path.join(FOLDER, "712_GAT_107-2_ORIGINAL.pdf")
WORK = os.path.join(FOLDER, "work")

print("Rendering and cropping...")
paths = render_and_crop(PDF, WORK)
print("Crops:", paths)

print("\nReading 7/12...")
a, model_a = extract_json(paths["712"], PROMPT_712)
print("Model:", model_a)
print("Village:", a.get("village_name"), "| Survey:", a.get("survey_no"))
print("Owners:", [o.get("name") for o in a.get("owners", [])])
print("Old mutations:", len(a.get("old_mutation_numbers", [])))

print("\nReading form 12...")
b, model_b = extract_json(paths["form12"], PROMPT_FORM12)
print("Model:", model_b)
rows = b.get("crop_rows", [])
print("Crop rows:", len(rows))
for r in rows:
    print("  ", r.get("year"), r.get("season"), r.get("crop_name"), r.get("unirrigated_area"))

print("\nDone.")