import psycopg2
import pandas as pd

DB_CONFIG = {
    "dbname": "land_registry",
    "user": "postgres",
    "password": "mahek",  # <-- Put your pgAdmin password
    "host": "localhost",
    "port": "5433"
}

conn = psycopg2.connect(**DB_CONFIG)

# SQL Query pulling complete tabular data + non-null geometry numbers
query = """
SELECT 
    c.id,
    c.survey_gat_no,
    c.khata_no,
    c.owner_names,
    c.total_area_ha,
    c.pot_kharaba_ha,
    c.cultivable_area_ha,
    COALESCE(
        ROUND((ST_Area(c.geom::geography) / 10000.0)::numeric, 4),
        ROUND((ST_Area(p.geom::geography) / 10000.0)::numeric, 4)
    ) AS gis_calc_area_ha,
    COALESCE(
        ROUND(ST_Perimeter(c.geom::geography)::numeric, 2),
        ROUND(ST_Perimeter(p.geom::geography)::numeric, 2)
    ) AS perimeter_meters,
    COALESCE(ST_NPoints(c.geom), ST_NPoints(p.geom)) AS boundary_corners,
    COALESCE(
        ROUND(ST_X(ST_Centroid(c.geom))::numeric, 6),
        ROUND(ST_X(ST_Centroid(p.geom))::numeric, 6)
    ) AS centroid_lon,
    COALESCE(
        ROUND(ST_Y(ST_Centroid(c.geom))::numeric, 6),
        ROUND(ST_Y(ST_Centroid(p.geom))::numeric, 6)
    ) AS centroid_lat
FROM cadastral_parcels c
LEFT JOIN cadastral_parcels p 
    ON p.survey_gat_no = split_part(c.survey_gat_no, '/', 1)
ORDER BY 
    COALESCE(NULLIF(regexp_replace(split_part(c.survey_gat_no, '/', 1), '\D', '', 'g'), '')::integer, 0),
    COALESCE(NULLIF(regexp_replace(split_part(c.survey_gat_no, '/', 2), '\D', '', 'g'), '')::integer, 0),
    c.survey_gat_no;
"""

df = pd.read_sql_query(query, conn)
conn.close()

# Export to real Excel file
output_file = "cadastral_parcels_full.xlsx"
df.to_excel(output_file, index=False, engine="openpyxl")

print(f"Successfully exported {len(df)} records to {output_file}")