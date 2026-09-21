import os
from typing import List, Optional
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
import psycopg2
from psycopg2.extras import execute_values

# 1. Structured Data Schema
class Owner(BaseModel):
    khata_number: Optional[str] = Field(default=None, description="खाता क्रमांक")
    owner_name: str = Field(description="खातेदाराचे नाव (Full name of occupant/owner)")
    mutation_number: Optional[str] = Field(default=None, description="फेरफार क्रमांक")

class Crop(BaseModel):
    crop_year: Optional[str] = Field(default=None, description="वर्ष (e.g. 2020-21)")
    crop_name: Optional[str] = Field(default=None, description="पिकाचे नाव")
    area_cultivated: Optional[float] = Field(default=None, description="क्षेत्र / लागवडीखालील क्षेत्र")
    irrigation_type: Optional[str] = Field(default=None, description="जलसिंचनाचे साधन / प्रकार")

class SatbaraExtract(BaseModel):
    district: Optional[str] = Field(default=None, description="जिल्हा (e.g., रायगड)")
    taluka: Optional[str] = Field(default=None, description="तालुका")
    village_name: Optional[str] = Field(default=None, description="गाव (e.g., कसाव)")
    village_code: Optional[str] = Field(default=None, description="गाव संकेतांक (e.g., 553617)")
    gat_number: str = Field(description="गट क्रमांक / सर्व्हे क्रमांक (e.g., 107/2)")
    occupant_class: Optional[str] = Field(default=None, description="धारणा पद्धती (e.g., भोगवटादार वर्ग-1)")
    total_area_ha: Optional[float] = Field(default=None, description="एकूण क्षेत्र (Total area in Hectare-Are format, e.g. 0.7890)")
    assessment_rupees: Optional[float] = Field(default=None, description="आकारणी (Assessment amount in Rs)")
    document_date: Optional[str] = Field(default=None, description="दिनांक in YYYY-MM-DD format if available")
    owners: List[Owner] = Field(default_factory=list)
    other_rights: List[str] = Field(default_factory=list, description="इतर अधिकार entries, encumbrances, or notes")
    crops: List[Crop] = Field(default_factory=list)

# 2. Extract Document Details with Gemini
def extract_satbara_data(pdf_path: str, api_key: str) -> SatbaraExtract:
    print(f"Uploading and analyzing {pdf_path}...")
    client = genai.Client(api_key=api_key)
    
    uploaded_file = client.files.upload(file=pdf_path)

    prompt = (
        "You are an expert at reading Maharashtra Land Record 7/12 (Satbara) documents in Marathi. "
        "Extract all details into the required JSON schema. "
        "Convert all Marathi numerals (०, १, २, ३...) to English numerals (0, 1, 2, 3...). "
        "Carefully parse Gaon Namuna 7 (ownership, Gat number, area) and Gaon Namuna 12 (crop register). "
        "Ignore watermarks like 'VIEW ONLY NOT FOR LEGAL PURPOSE'."
    )

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=[uploaded_file, prompt],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=SatbaraExtract,
            temperature=0.0
        )
    )

    return SatbaraExtract.model_validate_json(response.text)

# 3. Store into PostgreSQL
def insert_into_postgres(data: SatbaraExtract, db_config: dict):
    print("Saving extracted data into PostgreSQL (reference_db)...")
    conn = psycopg2.connect(**db_config)
    cur = conn.cursor()

    try:
        # Insert Parcel Record
        cur.execute("""
            INSERT INTO land_parcels 
            (district, taluka, village_name, village_code, gat_number, occupant_class, total_area_ha, assessment_rupees, document_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id;
        """, (
            data.district,
            data.taluka,
            data.village_name,
            data.village_code,
            data.gat_number,
            data.occupant_class,
            data.total_area_ha,
            data.assessment_rupees,
            data.document_date
        ))
        parcel_id = cur.fetchone()[0]

        # Insert Owners
        if data.owners:
            owner_rows = [
                (parcel_id, o.khata_number, o.owner_name, o.mutation_number)
                for o in data.owners
            ]
            execute_values(cur, """
                INSERT INTO land_owners (parcel_id, khata_number, owner_name, mutation_number)
                VALUES %s;
            """, owner_rows)

        # Insert Other Rights
        if data.other_rights:
            right_rows = [(parcel_id, r) for r in data.other_rights]
            execute_values(cur, """
                INSERT INTO other_rights (parcel_id, right_description)
                VALUES %s;
            """, right_rows)

        # Insert Crop Details
        if data.crops:
            crop_rows = [
                (parcel_id, c.crop_year, c.crop_name, c.area_cultivated, c.irrigation_type)
                for c in data.crops
            ]
            execute_values(cur, """
                INSERT INTO crop_records (parcel_id, crop_year, crop_name, area_cultivated, irrigation_type)
                VALUES %s;
            """, crop_rows)

        conn.commit()
        print(f"\nSuccess! Record inserted with parcel_id: {parcel_id}")

    except Exception as err:
        conn.rollback()
        print("Database error:", err)
        raise
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    GEMINI_API_KEY = ""  # <-- paste your Gemini API key here

    DB_SETTINGS = {
        "dbname": "reference_db",
        "user": "postgres",
        "password": "mahek",              # <-- paste your PostgreSQL password here
        "host": "localhost",
        "port": 5433
    }

    FILE_PATH = "712_GAT_107-2_ORIGINAL.pdf"

    extracted_info = extract_satbara_data(FILE_PATH, GEMINI_API_KEY)
    
    print("\n--- Extracted Data Preview ---")
    print(extracted_info.model_dump_json(indent=2))

    insert_into_postgres(extracted_info, DB_SETTINGS)