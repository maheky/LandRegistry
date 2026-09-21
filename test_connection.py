import os
import psycopg2
from google import genai

# 1. Test PostgreSQL Connection
print("Testing PostgreSQL connection...")
try:
    conn = psycopg2.connect(
        dbname="reference_db",
        user="postgres",       # change if your username is different
        password="mahek",  # replace with your postgres password
        host="localhost",
        port=5433
    )
    cur = conn.cursor()
    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';")
    tables = cur.fetchall()
    print("PostgreSQL Connected successfully!")
    print("Tables found:", [t[0] for t in tables])
    cur.close()
    conn.close()
except Exception as e:
    print("PostgreSQL connection error:", e)

# 2. Test Gemini API Key
print("\nTesting Gemini API connection...")
try:
    # If not set in environment, you can pass api_key="AIza..." inside Client(api_key=...)
    client = genai.Client()
    response = client.models.generate_content(
        model="gemini-3.3-flash",
        contents="Say 'API ready' in one short sentence."
    )
    print("Gemini API Status:", response.text.strip())
except Exception as e:
    print("Gemini API error:", e)