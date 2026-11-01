import psycopg2
from psycopg2.extras import Json

COLUMNS = [
    "village_code", "village_name", "taluka", "district", "pu_id", "survey_no",
    "holding_type", "local_name", "account_no", "non_agricultural_area", "assessment",
    "total_area", "joint_area", "area_summary", "other_rights", "pending_mutation",
    "last_mutation_no", "last_mutation_date", "old_mutation_numbers", "form12_note",
    "source_file", "needs_review", "review_reasons", "raw_712_json", "raw_form12_json",
]


def save_record(rec, raw712, rawf12):
    """Save one validated record. Returns ('saved', id) or ('duplicate', None)."""
    values = [
        rec["village_code"], rec["village_name"], rec["taluka"], rec["district"],
        rec["pu_id"], rec["survey_no"], rec["holding_type"], rec["local_name"],
        rec["account_no"], rec["non_agricultural_area"], rec["assessment"],
        rec["total_area"], rec["joint_area"], Json(rec["area_summary"]),
        rec["other_rights"], rec["pending_mutation"], rec["last_mutation_no"],
        rec["last_mutation_date"], Json(rec["old_mutation_numbers"]),
        rec["form12_note"], rec["source_file"], bool(rec["needs_review"]),
        Json(rec["review_reasons"]), Json(raw712), Json(rawf12),
    ]
    sql = (
        "INSERT INTO land_records (" + ", ".join(COLUMNS) + ") VALUES ("
        + ", ".join(["%s"] * len(COLUMNS)) + ") "
        "ON CONFLICT (village_code, survey_no, last_mutation_no) DO NOTHING RETURNING id"
    )

    conn = psycopg2.connect()   # reads PGHOST, PGPORT, PGUSER, PGPASSWORD, PGDATABASE
    try:
        with conn:              # one transaction: all saved, or nothing
            with conn.cursor() as cur:
                cur.execute(sql, values)
                row = cur.fetchone()
                if row is None:
                    return "duplicate", None

                rid = row[0]
                for o in rec["owners"]:
                    cur.execute(
                        """INSERT INTO owners (record_id, name, area, assessment, mutation_no,
                                               name_verified, account_no, is_removed)
                           VALUES (%s,%s,%s,%s,%s,FALSE,%s,%s)""",
                        (rid, o["name"], o["area"], o["assessment"], o["mutation_no"],
                         o["account_no"], bool(o["removed"])),
                    )
                for c in rec["crop_rows"]:
                    cur.execute(
                        """INSERT INTO crops (record_id, year, season, account_no, crop_type, crop_name,
                           irrigated_area, unirrigated_area, irrigation_source, uncultivable_nature,
                           uncultivable_area, remarks)
                           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                        (rid, c.get("year"), c.get("season"), c.get("account_no"), c.get("crop_type"),
                         c.get("crop_name"), c.get("irrigated_area"), c.get("unirrigated_area"),
                         c.get("irrigation_source"), c.get("uncultivable_nature"),
                         c.get("uncultivable_area"), c.get("remarks")),
                    )
                return "saved", rid
    finally:
        conn.close()