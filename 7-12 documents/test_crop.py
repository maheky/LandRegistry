import os
from PIL import Image
from extract_funcs import render_and_crop

FOLDER = r"C:\Users\Shubham\Documents\project\7-12 documents"
WORK = os.path.join(FOLDER, "work")

FILES = [
    "712_GAT_107-2_ORIGINAL.pdf",     # control: the sample we know
    "712_GAT_101-3_ORIGINAL.pdf",
    "712_GAT_104-3_ORIGINAL.pdf",
    "712_GAT_104-4-A_ORIGINAL.pdf",
]

os.makedirs(WORK, exist_ok=True)
for name in FILES:
    path = os.path.join(FOLDER, name)
    if not os.path.exists(path):
        print(name, "-> file not found, skipped")
        continue
    paths = render_and_crop(path, WORK)
    img = Image.open(paths["712"])
    print(name, "-> crop size", img.size, "->", os.path.basename(paths["712"]))

print("Done. Open the images in the work folder.")