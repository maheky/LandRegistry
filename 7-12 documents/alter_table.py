import psycopg2

conn = psycopg2.connect()
with conn:
    with conn.cursor() as cur:
        cur.execute("ALTER TABLE land_records ADD COLUMN IF NOT EXISTS total_area TEXT")
        cur.execute("ALTER TABLE land_records ADD COLUMN IF NOT EXISTS joint_area TEXT")
        cur.execute("ALTER TABLE land_records ADD COLUMN IF NOT EXISTS area_summary JSONB")
        cur.execute(
            "UPDATE land_records SET total_area = non_agricultural_area "
            "WHERE total_area IS NULL AND non_agricultural_area IS NOT NULL"
        )
        print("Rows updated:", cur.rowcount)

        cur.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'land_records' ORDER BY ordinal_position"
        )
        print("Columns:", [r[0] for r in cur.fetchall()])
conn.close()
print("Done.")