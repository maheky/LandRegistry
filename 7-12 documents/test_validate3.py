import copy
from validate_funcs import build_record


def area(land, cult, pa, tpk, total, assess):
    return {"land_types": land, "total_cultivable": cult, "pot_kharab_a": pa,
            "pot_kharab_b": None, "total_pot_kharab": tpk, "total_area": total,
            "non_agricultural_area": None, "assessment": assess, "special_assessment": None}


COMMON = {"village_name": "कडाव", "village_code": "553617", "taluka": "कर्जत", "district": "रायगड",
          "holding_type": "भोगवटादार वर्ग -1", "pending_mutation": "नाही.", "uncertain_fields": []}

# ---- 104-3: crossed-out owners, one current owner ----
a104 = dict(COMMON, pu_id="21841114763", survey_no="104/3", local_name="x",
    area_details=area([{"label": "जिरायत", "area": "0.01.00"}, {"label": "बागायत", "area": "-"}],
                      "0.01.00", "0.00.50", "0.00.50", "0.01.50", "0.02"),
    owners=[
        {"account_no": "[249]", "name": "[जुना मालक एक", "removed": True, "mutation_no": "( 5829 )"},
        {"account_no": "[249]", "name": "[जुना मालक दोन", "removed": True, "mutation_no": "( 5839 )"},
        {"account_no": "[249]", "name": "[जुना मालक तीन", "removed": False, "mutation_no": "( 5839 )"},
        {"account_no": "[941]", "name": "[जुना मालक चार", "removed": True, "mutation_no": "( 5847 )"},
        {"account_no": "942", "name": "सावित्री जी चन्नापगोल", "removed": False, "area": "0.01.00",
         "assessment": "0.02", "po_kh": "0.00.50", "mutation_no": "( 5847 )"},
    ],
    joint_areas=[{"account_no": "[249]", "area": "0", "assessment": "0", "removed": True}],
    other_rights="तुकडा ( 594 )", last_mutation_no="5847", last_mutation_date="21/10/2020",
    old_mutation_numbers=["104", "199", "251", "402", "527", "594", "1003", "1034", "1223",
                          "1774", "2037", "3390", "5596", "5619", "5655", "5714", "5829", "5832"])
b104 = {"village_name": "कडाव", "village_code": "553617", "survey_no": "104/3", "uncertain_fields": [],
        "crop_rows": [{"year": "2022-23", "season": "खरीप", "crop_name": "भात", "unirrigated_area": "0.0100"},
                      {"year": "2023-24", "season": "खरीप", "uncultivable_nature": "राब पड",
                       "uncultivable_area": "0.0150"}]}

# ---- 101-3: third land type (वरकस), 4-digit areas, joint area ----
a101 = dict(COMMON, pu_id="18709727033", survey_no="101/3", local_name="y",
    area_details=area([{"label": "जिरायत", "area": "-"}, {"label": "बागायत", "area": "-"},
                       {"label": "वरकस", "area": "0.09.90"}],
                      "0.09.90", "0.01.30", "0.01.30", "0.11.20", "0.09"),
    owners=[
        {"account_no": "[66]", "name": "[दिनकर हरि कोशे", "removed": True, "area": "0.09.90",
         "mutation_no": "( 5690 )"},
        {"account_no": "804", "name": "जयश्री श्रीकांत अकोलकर", "removed": False, "mutation_no": "( 5690 )"},
        {"account_no": "804", "name": "मोहिनी विद्याधर देशपांडे", "removed": False, "mutation_no": "( 5690 )"},
        {"account_no": "804", "name": "योगिनी दिपक कट्टी", "removed": False, "mutation_no": "( 5690 )"},
        {"account_no": "804", "name": "सोनाली प्रदिप कुलकर्णी", "removed": False, "mutation_no": "( 5690 )"},
    ],
    joint_areas=[{"account_no": "804", "area": "0.0990", "assessment": "0.09", "removed": False}],
    other_rights="तुकडा ( 594 )", last_mutation_no="5714", last_mutation_date="21/03/2018",
    old_mutation_numbers=["478", "496", "594", "897", "1223", "3916", "3994", "5655", "5714"])
b101 = {"village_name": "कडाव", "village_code": "553617", "survey_no": "101/3", "uncertain_fields": [],
        "crop_rows": [{"year": "2021-22", "season": "संपूर्ण वर्ष", "uncultivable_nature": "राब पड",
                       "uncultivable_area": "0.0990"}]}


def run(title, a, b):
    print("\n=== " + title)
    rec, f = build_record(a, b, "test.pdf")
    print("Failures:", f if f else "none")
    return rec


rec = run("TEST 1: 104-3 (crossed-out owners)", a104, b104)
print("Current owners:", [o["name"] for o in rec["owners"] if not o["removed"]])
print("Removed owners:", sum(1 for o in rec["owners"] if o["removed"]))
print("Account:", rec["account_no"], "| Total area:", rec["total_area"])

rec = run("TEST 2: 101-3 (वरकस land type, joint area 0.0990)", a101, b101)
print("Current owners:", len([o for o in rec["owners"] if not o["removed"]]))
print("Joint area:", rec["joint_area"], "| Account:", rec["account_no"])

x = copy.deepcopy(a104)
x["area_details"]["total_area"] = "0.01.80"
run("TEST 3: one digit misread in the total area", x, b104)

x = copy.deepcopy(a101)
x["village_name"] = "कढाव"
rec = run("TEST 4: village name misread (कढाव)", x, b101)
print("Village saved as:", rec["village_name"])

x = copy.deepcopy(a104)
x["last_mutation_no"] = "5700"
run("TEST 5: last mutation lower than the old list", x, b104)

x = copy.deepcopy(a104)
for o in x["owners"]:
    o["removed"] = True
run("TEST 6: every owner crossed out", x, b104)