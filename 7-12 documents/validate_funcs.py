import re
from datetime import datetime

# Village names are set from the village code, because the AI sometimes misreads a letter.
KNOWN_VILLAGES = {"553617": "कडाव"}

HEADINGS = {"कुळाचे नाव व खंड", "इतर अधिकार", "इतर"}
AREA_RE = re.compile(r"\d+\.\d{2}\.?\d{2}")      # 0.32.30 or 0.3230
SURVEY_RE = re.compile(
    r"\d+(?:[/\-]\d+)*(?:[/\-]?[\u0900-\u097FA-Za-z]+)?(?:[/\-]\d+)*"
)
NAME_RE = re.compile(r"[\u0900-\u097F\u200c\u200d\s.]+")
SCALAR_KEYS = (
    "total_cultivable", "pot_kharab_a", "pot_kharab_b", "total_pot_kharab",
    "total_area", "non_agricultural_area", "assessment", "special_assessment",
)
AREA_KEYS = (
    "total_cultivable", "pot_kharab_a", "pot_kharab_b", "total_pot_kharab",
    "total_area", "non_agricultural_area",
)


def clean_val(x):
    """None for empty or dash cells, otherwise the stripped text."""
    if x is None:
        return None
    s = str(x).strip()
    return None if s in ("", "-", "\u2014") else s


def first_number(s):
    m = re.findall(r"\d+", str(s or ""))
    return m[0] if m else None


def area_to_sqm(s):
    """'H.RR.SS' or 'H.RRSS' (hectare, are, sq metre) to square metres, or None."""
    s = clean_val(s)
    if s is None or not AREA_RE.fullmatch(s):
        return None
    whole, rest = s.split(".", 1)
    rest = rest.replace(".", "")
    return int(whole) * 10000 + int(rest[:2]) * 100 + int(rest[2:])


def clean_name(s):
    s = re.sub(r"[\[\]\-\u2014()]", " ", str(s or ""))
    return re.sub(r"\s+", " ", s).strip()


def clean_account(s):
    s = re.sub(r"[\[\]\s]", "", str(s or ""))
    return s or None


def clean_rights(text):
    lines = []
    for line in (text or "").split("\n"):
        line = line.strip()
        if not line or re.fullmatch(r"[-.\s]+", line) or line in HEADINGS:
            continue
        lines.append(line)
    return " ".join(lines)


def parts_sum(values):
    vals = [v for v in values if v is not None]
    return sum(vals) if vals else None


def build_record(a, b, source_file):
    """Merge the 7/12 (a) and form 12 (b) extractions. Returns (record, failures)."""
    failures = []
    notes = []

    def check(ok, label):
        if not ok and label not in failures:
            failures.append(label)

    # ---------- areas ----------
    raw_area = a.get("area_details") or {}
    land_types = []
    for item in raw_area.get("land_types") or []:
        if isinstance(item, dict):
            land_types.append({"label": clean_val(item.get("label")),
                               "area": clean_val(item.get("area"))})
    fields = {k: clean_val(raw_area.get(k)) for k in SCALAR_KEYS}
    fields["land_types"] = land_types
    total_area = fields["total_area"] or fields["non_agricultural_area"]

    # ---------- owners ----------
    owners = []
    bracket_fix = False
    for o in a.get("owners") or []:
        if not isinstance(o, dict):
            continue
        raw_name = str(o.get("name") or "")
        in_brackets = "[" in raw_name or "]" in raw_name
        removed = bool(o.get("removed")) or in_brackets
        if in_brackets and not o.get("removed"):
            bracket_fix = True
        owners.append({
            "account_no": clean_account(o.get("account_no")),
            "name": clean_name(raw_name),
            "removed": removed,
            "area": clean_val(o.get("area")),
            "assessment": clean_val(o.get("assessment")),
            "mutation_no": first_number(o.get("mutation_no")),
        })
    if bracket_fix:
        notes.append("An owner whose name was in brackets was treated as removed")
    current = [o for o in owners if not o["removed"]]

    joint_current = []
    for j in a.get("joint_areas") or []:
        if isinstance(j, dict) and not j.get("removed") and clean_val(j.get("area")):
            joint_current.append(clean_val(j.get("area")))

    # a joint area copied onto individual owners is cleared
    copied = False
    for o in current:
        if o["area"] and o["area"] in joint_current:
            o["area"] = None
            copied = True
    if copied:
        notes.append("A joint area was copied onto owners; the per-owner areas were cleared")

    accounts = []
    for o in current:
        if o["account_no"] and o["account_no"] not in accounts:
            accounts.append(o["account_no"])

    # ---------- other fields ----------
    other_rights = clean_rights(a.get("other_rights"))
    rights_refs = re.findall(r"\(\s*(\d+)\s*\)", other_rights)
    old_muts = [first_number(x) for x in (a.get("old_mutation_numbers") or [])]

    code_a, code_b = a.get("village_code"), b.get("village_code")
    name_a, name_b = a.get("village_name"), b.get("village_name")
    if str(code_a) in KNOWN_VILLAGES:
        village_name = KNOWN_VILLAGES[str(code_a)]
        if name_a != village_name or name_b != village_name:
            notes.append("Village name was read as '" + str(name_a) + "' / '" + str(name_b)
                         + "' and set from the village code")
    else:
        village_name = name_a
        check(name_a == name_b, "Village name differs between 7/12 and form 12")

    record = {
        "village_name": village_name,
        "village_code": code_a,
        "taluka": a.get("taluka"),
        "district": a.get("district"),
        "pu_id": a.get("pu_id"),
        "survey_no": a.get("survey_no"),
        "holding_type": a.get("holding_type"),
        "local_name": a.get("local_name"),
        "account_no": "; ".join(accounts) if accounts else None,
        "non_agricultural_area": fields["non_agricultural_area"],
        "assessment": fields["assessment"],
        "total_area": total_area,
        "joint_area": "; ".join(joint_current) if joint_current else None,
        "area_summary": fields,
        "owners": owners,
        "other_rights": other_rights,
        "pending_mutation": (a.get("pending_mutation") or "").strip(" ."),
        "last_mutation_no": first_number(a.get("last_mutation_no")),
        "last_mutation_date": a.get("last_mutation_date"),
        "old_mutation_numbers": old_muts,
        "crop_rows": b.get("crop_rows") or [],
        "form12_note": b.get("note_text"),
        "source_file": source_file,
    }

    # ---------- identity checks (a failure means the record is NOT saved) ----------
    check(bool(re.fullmatch(r"\d{6}", str(code_a))), "Village code is not 6 digits")
    check(code_a == code_b, "Village code differs between 7/12 and form 12")
    check(bool(re.fullmatch(r"[0-9A-Za-z]{11}", str(record["pu_id"]))), "PU-ID / ULPIN is not 11 characters")
    check(bool(SURVEY_RE.fullmatch(str(record["survey_no"]))), "Survey number has an invalid format")
    check(a.get("survey_no") == b.get("survey_no"), "Survey number differs between 7/12 and form 12")

    # ---------- area checks ----------
    check(total_area is not None and bool(AREA_RE.fullmatch(total_area)),
          "Total area is missing or not a valid area")
    for k in AREA_KEYS:
        if fields[k] is not None:
            check(bool(AREA_RE.fullmatch(fields[k])), "Area '" + k + "' is not a valid area")

    S = {k: area_to_sqm(fields[k]) for k in AREA_KEYS}
    lt_sqm = []
    for lt in land_types:
        if lt["area"] is not None:
            v = area_to_sqm(lt["area"])
            check(v is not None, "Land type '" + str(lt["label"]) + "' has an invalid area")
            if v is not None:
                lt_sqm.append(v)
    cult_sum = sum(lt_sqm) if lt_sqm else None
    pk_sum = parts_sum([S["pot_kharab_a"], S["pot_kharab_b"]])

    if S["total_cultivable"] is not None and cult_sum is not None:
        check(cult_sum == S["total_cultivable"], "Land types do not add up to the cultivable total")
    if S["total_pot_kharab"] is not None and pk_sum is not None:
        check(pk_sum == S["total_pot_kharab"], "Pot-kharab parts do not add up to the pot-kharab total")
    cult = S["total_cultivable"] if S["total_cultivable"] is not None else cult_sum
    pk = S["total_pot_kharab"] if S["total_pot_kharab"] is not None else pk_sum
    if S["total_area"] is not None and cult is not None:
        check(S["total_area"] == cult + (pk or 0), "Total area does not equal cultivable + pot-kharab")

    if fields["assessment"] is None:
        notes.append("No assessment (aakarani) was read")
    else:
        check(bool(re.fullmatch(r"\d+\.\d{2}", fields["assessment"])), "Assessment is not in N.NN format")

    # ---------- owner checks ----------
    check(len(current) > 0, "No current (not crossed-out) owner found")
    for o in current:
        check(bool(o["name"]) and bool(NAME_RE.fullmatch(o["name"])),
              "A current owner name is empty or has non-Devanagari characters")
    if any(o["removed"] and o["name"] and not NAME_RE.fullmatch(o["name"]) for o in owners):
        notes.append("A removed owner's name has non-Devanagari characters")

    candidates = {v for v in (S["total_area"], S["total_cultivable"],
                              S["non_agricultural_area"], cult_sum) if v is not None}
    all_sqm = [area_to_sqm(o["area"]) for o in current if o["area"]]
    all_sqm += [area_to_sqm(x) for x in joint_current]
    if not all_sqm:
        notes.append("No current owner area was printed")
    elif None in all_sqm or sum(all_sqm) not in candidates:
        notes.append("Current owner areas do not add up to a total area: check manually")

    # ---------- mutation checks ----------
    check(None not in old_muts, "An old mutation number could not be read")
    nums = [int(x) for x in old_muts if x]
    if nums:
        check(nums == sorted(nums) and len(nums) == len(set(nums)),
              "Old mutation numbers are not in ascending order")
    else:
        notes.append("No old mutation numbers were read")

    last = record["last_mutation_no"]
    check(last is not None, "Last mutation number could not be read")
    if last is not None:
        if nums:
            check(int(last) >= max(nums), "Last mutation number is lower than the highest old mutation number")
        for o in current:
            if o["mutation_no"]:
                check(int(o["mutation_no"]) <= int(last),
                      "An owner's mutation number is higher than the last mutation number")
    if any(r not in old_muts for r in rights_refs):
        notes.append("A mutation number in the rights text is not in the old list")

    try:
        datetime.strptime(str(record["last_mutation_date"]), "%d/%m/%Y")
        date_ok = True
    except ValueError:
        date_ok = False
    check(date_ok, "Last mutation date is not a valid dd/mm/yyyy date")

    # ---------- form 12 ----------
    for i, row in enumerate(record["crop_rows"], 1):
        check(bool(re.fullmatch(r"\d{4}-\d{2}", str(row.get("year")))),
              "Crop row " + str(i) + ": year is not like 2020-21")
        areas = [row.get("irrigated_area"), row.get("unirrigated_area"), row.get("uncultivable_area")]
        check(any(x and re.fullmatch(r"\d+\.\d+", str(x)) for x in areas),
              "Crop row " + str(i) + ": no valid area")
    if not record["crop_rows"]:
        notes.append("Form 12 has no rows")

    for label, src in (("7/12", a), ("form 12", b)):
        if src.get("uncertain_fields"):
            notes.append(label + " fields the model was unsure about: " + ", ".join(src["uncertain_fields"]))

    notes.append("Owner names and other text must be checked by a human before they are trusted")

    record["needs_review"] = True
    record["review_reasons"] = notes + ["FAILED: " + f for f in failures]
    return record, failures