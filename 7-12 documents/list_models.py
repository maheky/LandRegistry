import os
from google import genai

client = genai.Client(api_key=os.getenv("GENAI_API_KEY"))

for m in client.models.list():
    name = m.name
    if "gemini" in name and "image" not in name and "tts" not in name:
        print(name)