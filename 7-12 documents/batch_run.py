import os
import csv
import json
import time
import shutil
from datetime import datetime

from extract_funcs import render_and_crop, extract_json
from prompts import PROMPT_712, PROMPT_FORM12
from validate_funcs import build_record
from db_funcs import save_record
from log_funcs import log_result

FOLDER = r"C:\Users\Shubham\Documents\project\7-12 documents"
INCOMING = os.path.join(FOLDER, "incoming")
PROCESSED = os.path.join(FOLDER, "processed")
FAILED = os.path.join(FOLDER, "failed")
WORK = os.path.join(FOLDER, "work")
REPORTS = os.path.join(FOLDER, "reports")

PAUSE_SECONDS = 15   # keeps the free Gemini tier under its per-minute limit


def unique_dest(folder, name):
    dest = os.path.join(folder, name)
    if os.path.exists(dest):
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base, ext = os.path.splitext(name)
        dest = os.path.join(folder, base + "_" + stamp + ext)
    return dest


def is_quota_error(reasons):
    return "429" in reasons or "RESOURCE_EXHAUSTED" in reasons


def process_one(pdf_path):
    """Run the whole pipeline on one PDF. Returns a result dict."""
    name = os.path.basename(pdf_path)
    result = {"file": name, "status": "", "record_id": "", "survey_no": "",
              "village": "", "owners": "", "reasons": ""}
    a = None
    b = None
    try:
        paths = render_and_crop(pdf_path, WORK)
        a, _ = extract_json(paths["712"], PROMPT_712)
        b, _ = extract_json(paths["form12"], PROMPT_FORM12)

        rec, failures = build_record(a, b, name)
        result["survey_no"] = rec.get("survey_no") or ""
        result["village"] = rec.get("village_name") or ""
        result["owners"] = "; ".join(o["name"] for o in rec["owners"])

        if failures:
            result["status"] = "failed_validation"
            result["reasons"] = " | ".join(failures)
        else:
            status, rid = save_record(rec, a, b)
            result["status"] = status
            result["record_id"] = rid if rid is not None else ""
            result["reasons"] = " | ".join(rec["review_reasons"])
    except Exception as e:
        result["status"] = "error"
        result["reasons"] = str(e).replace("\n", " ")[:500]

    result["_raw"] = {"extract_712": a, "extract_form12": b}
    return result


def main():
    for folder in (INCOMING, PROCESSED, FAILED, WORK, REPORTS):
        os.makedirs(folder, exist_ok=True)

    pdfs = sorted(f for f in os.listdir(INCOMING) if f.lower().endswith(".pdf"))
    if not pdfs:
        print("No PDF files found in:", INCOMING)
        return

    print("Found", len(pdfs), "PDF file(s).\n")
    results = []

    try:
        for i, name in enumerate(pdfs, 1):
            print("[" + str(i) + "/" + str(len(pdfs)) + "]", name)
            src = os.path.join(INCOMING, name)
            res = process_one(src)

            if res["status"] in ("failed_validation", "error"):
                print("   ->", res["status"], res["reasons"][:150])
            else:
                print("   ->", res["status"])

            # Free quota used up: stop, keep this file in 'incoming', run again later
            if res["status"] == "error" and is_quota_error(res["reasons"]):
                print("   Free quota reached. Stopping now.")
                print("   This file stays in 'incoming'. Run again later.")
                break

            if res["status"] in ("saved", "duplicate"):
                shutil.move(src, unique_dest(PROCESSED, name))
            else:
                dest = unique_dest(FAILED, name)
                shutil.move(src, dest)
                with open(dest + ".review.json", "w", encoding="utf-8") as f:
                    json.dump({"reasons": res["reasons"], "raw": res["_raw"]},
                              f, ensure_ascii=False, indent=2)

            log_result(res)
            results.append(res)
            if i < len(pdfs):
                time.sleep(PAUSE_SECONDS)
    finally:
        if results:
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report = os.path.join(REPORTS, "report_" + stamp + ".csv")
            cols = ["file", "status", "record_id", "survey_no", "village", "owners", "reasons"]
            with open(report, "w", encoding="utf-8-sig", newline="") as f:
                w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
                w.writeheader()
                w.writerows(results)

            print("\n--- Summary ---")
            for s in ("saved", "duplicate", "failed_validation", "error"):
                print(s + ":", sum(1 for r in results if r["status"] == s))
            print("Report:", report)
            print("Overall picture: py -3.11 summary.py")


if __name__ == "__main__":
    main()