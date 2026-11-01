import os
import json
from PIL import Image
from google import genai
from google.genai import types

FOLDER = r"C:\Users\Shubham\Documents\project\7-12 documents"
IMAGE = os.path.join(FOLDER, "crop_712.png")
OUT = os.path.join(FOLDER, "extract_712.json")
MODEL = "gemini-3.5-flash"   # fallback: "gemini-flash-latest"

client = genai.Client(api_key=os.getenv("GENAI_API_KEY"))

PROMPT = """
This image is a Maharashtra land record, Gaon Namuna Saat (7/12 extract), in Marathi.
Pale diagonal text like "VIEW ONLY - NOT FOR LEGAL PURPOSE" is a watermark. Ignore it.

Transcribe the data exactly as printed. Do NOT guess, correct, or invent anything.
Keep Marathi text in Devanagari exactly as printed. Keep numbers exactly as printed.
If a value is blank, use null. If a value is unclear, give your best reading and add
the field name to "uncertain_fields".

Return ONLY valid JSON with these keys:
{
  "village_name": "",
  "village_code": "",
  "taluka": "",
  "district": "",
  "pu_id": "",
  "survey_no": "",                (भूमापन क्रमांक व उपविभाग)
  "holding_type": "",             (भू-धारणा पध्दती)
  "local_name": "",               (शेताचे स्थानिक नाव)
  "area_details": {
      "non_agricultural_area": "",  (बिन शेती)
      "assessment": ""              (आकारणी)
  },
  "account_no": "",               (खाते क्र.)
  "owners": [
      {"name": "", "area": "", "assessment": "", "po_kh": null, "mutation_no": ""}
  ],
  "other_rights": "",             (इतर अधिकार, full text)
  "pending_mutation": "",         (प्रलंबित फेरफार)
  "last_mutation_no": "",
  "last_mutation_date": "",
  "old_mutation_numbers": [],     (जुने फेरफार क्र., every number in order)
  "boundary_marks": null,         (सीमा आणि भूमापन चिन्हे)
  "uncertain_fields": [],
  "raw_text": ""                  (all readable text, top to bottom)
}
"""

img = Image.open(IMAGE)
print("Sending image to", MODEL, "... please wait")

response = client.models.generate_content(
    model=MODEL,
    contents=[img, PROMPT],
    config=types.GenerateContentConfig(
        temperature=0,
        response_mime_type="application/json",
    ),
)

text = response.text
try:
    data = json.loads(text)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(json.dumps(data, ensure_ascii=False, indent=2))
    print("\nSaved to:", OUT)
except json.JSONDecodeError:
    print("Model did not return valid JSON. Raw reply:")
    print(text)