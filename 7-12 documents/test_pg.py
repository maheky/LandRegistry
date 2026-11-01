import psycopg2

conn = psycopg2.connect()   # reads PGHOST, PGPORT, PGUSER, PGPASSWORD, PGDATABASE
cur = conn.cursor()

cur.execute("SELECT current_database()")
print("Database:", cur.fetchone()[0])

cur.execute("SHOW server_encoding")
print("Server encoding:", cur.fetchone()[0])

cur.execute("SHOW client_encoding")
print("Client encoding:", cur.fetchone()[0])

cur.execute("SELECT %s", ("कडाव",))
print("Marathi round-trip:", cur.fetchone()[0])

print("\n--- Existing tables (non-system) ---")
cur.execute("""
    SELECT table_schema, table_name
    FROM information_schema.tables
    WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
    ORDER BY table_schema, table_name
""")
rows = cur.fetchall()
if rows:
    for schema, name in rows:
        print(schema + "." + name)
else:
    print("(no tables yet)")

conn.close()
print("\nConnection OK")