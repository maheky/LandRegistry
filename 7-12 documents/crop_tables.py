from PIL import Image
import os

Image.MAX_IMAGE_PIXELS = None

FOLDER = r"C:\Users\Shubham\Documents\project\7-12 documents"
SRC = os.path.join(FOLDER, "page_full.png")

page = Image.open(SRC)
w, h = page.size
print("Page size:", w, "x", h)

# Crop boxes as fractions of the page: (left, top, right, bottom)
BOXES = {
    "crop_712.png":    (0.166, 0.08, 0.835, 0.285),
    "crop_form12.png": (0.166, 0.285, 0.835, 0.435),
}

for name, (l, t, r, b) in BOXES.items():
    box = (int(l * w), int(t * h), int(r * w), int(b * h))
    crop = page.crop(box)
    path = os.path.join(FOLDER, name)
    crop.save(path)
    print("Saved", name, "size:", crop.size)

print("Done. Open the two crop files and check them.")