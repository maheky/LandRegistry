import psycopg2

conn = psycopg2.connect()
with conn:
    with conn.cursor() as cur:
        cur.execute("ALTER TABLE owners ADD COLUMN IF NOT EXISTS account_no TEXT")
        cur.execute("ALTER TABLE owners ADD COLUMN IF NOT EXISTS is_removed BOOLEAN NOT NULL DEFAULT FALSE")
        cur.execute(
            "UPDATE owners o SET account_no = r.account_no "
            "FROM land_records r WHERE o.record_id = r.id AND o.account_no IS NULL"
        )
        print("Owners updated with account numbers:", cur.rowcount)
        cur.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'owners' ORDER BY ordinal_position"
        )
        print("Owner columns:", [r[0] for r in cur.fetchall()])
conn.close()
print("Done.")