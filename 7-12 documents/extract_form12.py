import os
import json
from PIL import Image
from google import genai
from google.genai import types

FOLDER = r"C:\Users\Shubham\Documents\project\7-12 documents"
IMAGE = os.path.join(FOLDER, "crop_form12.png")
OUT = os.path.join(FOLDER, "extract_form12.json")
MODEL = "gemini-3.5-flash"   # fallback: "gemini-flash-latest"

client = genai.Client(api_key=os.getenv("GENAI_API_KEY"))

PROMPT = """
This image is a Maharashtra land record, Gaon Namuna Baara (crop register), in Marathi.
Pale diagonal text like "VIEW ONLY - NOT FOR LEGAL PURPOSE" is a watermark. Ignore it.
The rows of numbers like (१), (२), (३) are column numbers, not data. Ignore them.
The row with units (हे.आर. / चौ.मी) is a units row, not data.

Transcribe ONLY the data rows under the headers, exactly as printed.
Do NOT guess, correct, or invent anything. Keep Marathi in Devanagari and numbers as printed.
If a cell is blank, use null. If a value is unclear, give your best reading and add the
field name to "uncertain_fields".

Return ONLY valid JSON:
{
  "village_name": "",
  "village_code": "",
  "taluka": "",
  "district": "",
  "survey_no": "",                  (भूमापन क्रमांक व उपविभाग)
  "crop_rows": [
    {
      "year": "",                   (वर्ष)
      "season": "",                 (हंगाम)
      "account_no": null,           (खाते क्रमांक)
      "crop_type": "",              (पिकाचा प्रकार)
      "crop_name": "",              (पिकाचे नाव)
      "irrigated_area": null,       (जल सिंचित)
      "unirrigated_area": null,     (अजल सिंचित)
      "irrigation_source": null,    (जल सिंचनाचे साधन)
      "uncultivable_nature": null,  (स्वरूप)
      "uncultivable_area": null,    (क्षेत्र)
      "remarks": null               (शेरा)
    }
  ],
  "note_text": "",                  (the टीप line)
  "uncertain_fields": []
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