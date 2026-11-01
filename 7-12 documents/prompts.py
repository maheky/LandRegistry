PROMPT_712 = """
This image is a Maharashtra land record, Gaon Namuna Saat (7/12 extract), in Marathi.
Pale diagonal text like "VIEW ONLY - NOT FOR LEGAL PURPOSE" is a watermark. Ignore it.

Transcribe the data exactly as printed. Do NOT guess, correct, calculate or invent anything.
Keep Marathi text in Devanagari exactly as printed. Keep numbers exactly as printed.
A dash "-" in a cell means empty: use null. If a value is unclear, give your best reading
and add the field name to "uncertain_fields".

pu_id: the 11-digit number printed after "PU-ID" or "ULPIN" under the village name.

LEFT COLUMN (क्षेत्र, एकक व आकारणी). Farmland has these rows. Fill only what is printed.
- "land_types": every row listed under "अ) लागवड योग्य क्षेत्र" (for example जिरायत, बागायत,
  वरकस), each as {"label": the printed label, "area": the value or null}.
- total_cultivable: एकूण ला.यो. क्षेत्र
- pot_kharab_a: वर्ग (अ), pot_kharab_b: वर्ग (ब), total_pot_kharab: एकूण पो.ख.
- total_area: एकूण क्षेत्र (अ+ब)
- assessment: आकारणी, special_assessment: जुडी किंवा विशेष आकारणी
A non-agricultural plot instead has अकृषिक "बिन शेती" क्षेत्र: put it in non_agricultural_area.
Areas appear as 0.32.30 or as 0.3230. Copy them exactly as printed.

OWNERS. Owners are grouped by account number (खाते क्र.). Return one entry per person,
in the order printed, and repeat the account number of the group on every person in it.
- Some owners and whole account groups are crossed out with a line through the text and
  shown inside square brackets [ ]. They are former owners. Return them too, with
  "removed": true. Give the name WITHOUT the bracket characters and without dashes.
- An owner's "area", "assessment" and "po_kh" are ONLY the values printed on that
  owner's own line.
- A line such as "सामाईक क्षेत्र" (joint area) belongs to the whole group. Do NOT copy
  its values onto the owners. Put each such line in "joint_areas" with the account number
  of its group, its values, and "removed" true if it is crossed out.
- mutation_no: the number in brackets in the फे.फा. column on that owner's line.

old_mutation_numbers: every number in the row that begins "जुने फेरफार क्र.", from the
first to the last, in printed order. last_mutation_no and last_mutation_date come from
"शेवटचा फेरफार क्रमांक" in the rights column.

Return ONLY valid JSON with these keys:
{
  "village_name": "",
  "village_code": "",
  "taluka": "",
  "district": "",
  "pu_id": "",
  "survey_no": "",
  "holding_type": "",
  "local_name": "",
  "area_details": {
      "land_types": [{"label": "", "area": null}],
      "total_cultivable": null,
      "pot_kharab_a": null,
      "pot_kharab_b": null,
      "total_pot_kharab": null,
      "total_area": null,
      "non_agricultural_area": null,
      "assessment": null,
      "special_assessment": null
  },
  "owners": [
      {"account_no": "", "name": "", "removed": false, "area": null,
       "assessment": null, "po_kh": null, "mutation_no": null}
  ],
  "joint_areas": [
      {"account_no": "", "area": null, "assessment": null, "po_kh": null, "removed": false}
  ],
  "other_rights": "",
  "pending_mutation": "",
  "last_mutation_no": "",
  "last_mutation_date": "",
  "old_mutation_numbers": [],
  "boundary_marks": null,
  "uncertain_fields": []
}
"""

PROMPT_FORM12 = """
This image is a Maharashtra land record, Gaon Namuna Baara (crop register), in Marathi.
Pale diagonal text like "VIEW ONLY - NOT FOR LEGAL PURPOSE" is a watermark. Ignore it.
The rows of numbers like (1), (2), (3) are column numbers, not data. Ignore them.
The row with units is a units row, not data.

Transcribe ONLY the data rows under the headers, exactly as printed.
A data row may have no crop name and instead describe land that is not cultivated
(for example text in the स्वरूप column and an area in the last क्षेत्र column).
That is still a data row.
Do NOT guess, correct, or invent anything. Keep Marathi in Devanagari and numbers as printed.
If a cell is blank, use null. If a value is unclear, give your best reading and add the
field name to "uncertain_fields". If there are no data rows, return an empty crop_rows list.

Return ONLY valid JSON:
{
  "village_name": "",
  "village_code": "",
  "taluka": "",
  "district": "",
  "survey_no": "",
  "crop_rows": [
    {
      "year": "",
      "season": "",
      "account_no": null,
      "crop_type": null,
      "crop_name": null,
      "irrigated_area": null,
      "unirrigated_area": null,
      "irrigation_source": null,
      "uncultivable_nature": null,
      "uncultivable_area": null,
      "remarks": null
    }
  ],
  "note_text": "",
  "uncertain_fields": []
}
"""