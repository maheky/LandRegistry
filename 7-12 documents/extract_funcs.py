import os
import json
import time
import numpy as np
from pdf2image import convert_from_path
from PIL import Image
from google import genai
from google.genai import types

Image.MAX_IMAGE_PIXELS = None

POPPLER = r"C:\poppler\poppler-26.09.0\Library\bin"
MODEL = "gemini-3.5-flash"
FALLBACK_MODEL = "gemini-flash-latest"
DPI = 500

# Crop window as fractions of the page. The bottom is found automatically.
LEFT = 0.166
RIGHT = 0.835
TOP = 0.08
SEARCH_BOTTOM = 0.90      # never look below this part of the page
MARGIN_PX = 80            # extra white space kept under the last printed line
DARK = 110                # pixels darker than this count as ink (the watermark is lighter)
MIN_DARK_PIXELS = 12      # a row needs this much ink to count as printed content

LETTER_RATIO = 8.5 / 11.0

PREFIX = (
    "This picture shows two Maharashtra land-record tables, one above the other: "
    "Gaon Namuna Saat (7/12, ownership) and, below it, Gaon Namuna Baara (crop register). "
    "The instructions below say which one to read. Read ONLY that table and ignore the "
    "other one. Where the instructions say 'this image', they mean that one table.\n\n"
)


def find_bottom(page):
    """Return the pixel row just below the last printed line inside the table area."""
    w, h = page.size
    x0, x1 = int(LEFT * w), int(RIGHT * w)
    y0, y1 = int(TOP * h), int(SEARCH_BOTTOM * h)
    gray = np.asarray(page.convert("L"))[y0:y1, x0:x1]
    ink_per_row = (gray < DARK).sum(axis=1)
    rows = np.nonzero(ink_per_row >= MIN_DARK_PIXELS)[0]
    if len(rows) == 0:
        raise ValueError("No table content found on the page")
    return min(y0 + int(rows[-1]) + MARGIN_PX, h)


def render_and_crop(pdf_path, work_dir):
    """Render page 1 and save one tall crop that holds both tables.
    Returns {'712': path, 'form12': path}; both keys point to the same image."""
    base = os.path.splitext(os.path.basename(pdf_path))[0]
    pages = convert_from_path(
        pdf_path, dpi=DPI, poppler_path=POPPLER, first_page=1, last_page=1
    )
    page = pages[0]
    w, h = page.size

    if abs(w / h - LETTER_RATIO) > 0.02:
        raise ValueError(
            "Page is not Letter-shaped (" + str(w) + "x" + str(h) + "). "
            "The crop only fits the standard Mahabhulekh print layout."
        )

    bottom = find_bottom(page)
    crop = page.crop((int(LEFT * w), int(TOP * h), int(RIGHT * w), bottom))
    out = os.path.join(work_dir, base + "_tables.png")
    crop.save(out)
    return {"712": out, "form12": out}


_client = None


def get_client():
    global _client
    if _client is None:
        _client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    return _client


def extract_json(image_path, prompt):
    """Send the crop to Gemini. Returns (data_dict, model_used)."""
    img = Image.open(image_path)
    full_prompt = PREFIX + prompt
    last_error = None

    for model in (MODEL, FALLBACK_MODEL):
        for attempt in range(4):
            try:
                response = get_client().models.generate_content(
                    model=model,
                    contents=[img, full_prompt],
                    config=types.GenerateContentConfig(
                        temperature=0,
                        response_mime_type="application/json",
                    ),
                )
                data = json.loads(response.text)
                if not isinstance(data, dict):
                    raise ValueError("Model returned JSON that is not an object")
                return data, model
            except Exception as e:
                last_error = e
                msg = str(e)
                if "429" in msg or "RESOURCE_EXHAUSTED" in msg:
                    wait = 30 * (attempt + 1)
                    print("   rate limit hit, waiting", wait, "seconds...")
                    time.sleep(wait)
                elif "503" in msg or "UNAVAILABLE" in msg:
                    wait = 20 * (attempt + 1)
                    print("   Google server busy, waiting", wait, "seconds...")
                    time.sleep(wait)
                elif "404" in msg or "not found" in msg.lower():
                    break   # this model is unavailable: try the fallback model
                else:
                    time.sleep(5)

    raise RuntimeError("Extraction failed: " + str(last_error))