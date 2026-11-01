import psycopg2
from psycopg2.extras import Json


def log_result(res):
    """Add one row to processing_log. Never stops the batch if logging fails."""
    try:
        conn = psycopg2.connect()
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """INSERT INTO processing_log
                           (file_name, status, record_id, survey_no, village, owners, reasons, raw_json)
                           VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
                        (res["file"], res["status"], res["record_id"] or None,
                         res["survey_no"] or None, res["village"] or None,
                         res["owners"] or None, res["reasons"] or None,
                         Json(res.get("_raw"))),
                    )
        finally:
            conn.close()
    except Exception as e:
        print("   (could not write to processing_log: " + str(e)[:100] + ")")