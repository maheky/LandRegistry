import copy
from validate_funcs import build_record

a = {
    "village_name": "कडाव", "village_code": "553617", "taluka": "कर्जत", "district": "रायगड",
    "pu_id": "31762808656", "survey_no": "101/1/अ", "holding_type": "भोगवटादार वर्ग - 2",
    "local_name": "चांभार नाडी",
    "area_details": {
        "jirayat": "0.32.30", "bagayat": "-", "total_cultivable": "0.32.30",
        "pot_kharab_a": "0.04.30", "pot_kharab_b": "-", "total_pot_kharab": "0.04.30",
        "total_area": "0.36.60", "non_agricultural_area": None,
        "assessment": "0.29", "special_assessment": "-",
    },
    "joint_area": "0.32.30", "account_no": "184",
    "owners": [
        {"name": "नारायण शंकर मुने", "area": None, "mutation_no": "1809"},
        {"name": "गणपत शंकर मुने", "area": None, "mutation_no": "1809"},
        {"name": "वामन शंकर मुने", "area": None, "mutation_no": "1809"},
        {"name": "रामचंद्र शंकर मुने", "area": None, "mutation_no": "1809"},
    ],
    "other_rights": "तुकडा ( 594 ) पाईपलाईन ( 4066 )",
    "pending_mutation": "नाही.", "last_mutation_no": "5821", "last_mutation_date": "05/04/2020",
    "old_mutation_numbers": ["108", "499", "594", "1137", "1455", "1809",
                             "3243", "3246", "4066", "5655", "5714", "5821"],
    "uncertain_fields": [],
}
b = {
    "village_name": "कडाव", "village_code": "553617", "survey_no": "101/1/अ",
    "crop_rows": [{"year": "2023-24", "season": "खरीप", "account_no": "184*",
                   "crop_type": None, "crop_name": None, "irrigated_area": None,
                   "unirrigated_area": None, "uncultivable_nature": "राब पड",
                   "uncultivable_area": "0.3230"}],
    "note_text": "", "uncertain_fields": [],
}

print("=== TEST 1: correct reading of the farmland 7/12 ===")
rec, f = build_record(a, b, "test.pdf")
print("Failures:", f if f else "none")
print("Total area:", rec["total_area"], "| Joint area:", rec["joint_area"])

print("\n=== TEST 2: one digit misread in the total area (0.36.60 -> 0.36.80) ===")
a2 = copy.deepcopy(a)
a2["area_details"]["total_area"] = "0.36.80"
rec, f = build_record(a2, b, "test.pdf")
print("Failures:", f if f else "none")

print("\n=== TEST 3: joint area copied onto every owner (the earlier Gemini mistake) ===")
a3 = copy.deepcopy(a)
for o in a3["owners"]:
    o["area"] = "0.32.30"
rec, f = build_record(a3, b, "test.pdf")
print("Failures:", f if f else "none")
print("Owner areas now:", [o["area"] for o in rec["owners"]])
print("Notes:", [n for n in rec["review_reasons"] if "joint" in n])

print("\n=== TEST 4: survey number with a typo (letter O instead of zero) ===")
a4 = copy.deepcopy(a)
a4["survey_no"] = "1O1/1/अ"
b4 = copy.deepcopy(b)
b4["survey_no"] = "1O1/1/अ"
rec, f = build_record(a4, b4, "test.pdf")
print("Failures:", f if f else "none")