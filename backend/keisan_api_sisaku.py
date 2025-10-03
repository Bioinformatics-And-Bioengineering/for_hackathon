from flask import Flask, request, Response
import pandas as pd
import json
import os
from keisan_logic import assemble_and_compute as assemble_and_compute_with_requirements

app = Flask(__name__)

SUBJECTS_CSV = "subjects.csv"
ENTRIES_CSV = "entries.csv"

# GPA 点数変換
GRADE_POINTS = {
    "A": 4.0,
    "B": 3.0,
    "C": 2.0,
    "D": 1.0,
    "F": 0.0
}

# CSV 読み込み
subjects_df = pd.read_csv(SUBJECTS_CSV)

def assemble_and_compute(rows):
    details = []
    total_points = 0
    total_credits = 0
    warnings = []

    for r in rows:
        name = r.get("name")
        grade = r.get("grade")
        subj = subjects_df[subjects_df["科目名"] == name]

        if subj.empty:
            warnings.append(f"'{name}' not in subjects.csv. Skipped.")
            continue  # CSVに保存も計算もスキップ

        credits = float(subj["単位数"].values[0])
        field = int(subj["小区分ID"].values[0])
        point = GRADE_POINTS.get(grade, 0.0)

        details.append({
            "name": name,
            "grade": grade,
            "credits": credits,
            "field": field,
            "point": point
        })

        total_points += credits * point
        total_credits += credits

    gpa = round(total_points / total_credits, 2) if total_credits > 0 else 0.0

    # entries.csv に追記（存在する科目のみ）
    if details:
        df_entries = pd.DataFrame(details)[["name", "grade", "credits", "field"]]
        if os.path.exists(ENTRIES_CSV):
            existing = pd.read_csv(ENTRIES_CSV)
            # 同じ name があれば上書き
            df_entries = pd.concat([existing[~existing["name"].isin(df_entries["name"])], df_entries], ignore_index=True)
        df_entries.to_csv(ENTRIES_CSV, index=False, encoding="utf-8-sig")

    return {
        "details": details,
        "gpa": gpa,
        "total_credits_counted": total_credits,
        "warnings": warnings
    }

@app.post("/gpa/compute")
def compute_gpa():
    if not request.is_json:
        return Response(json.dumps({"error": "Content-Type application/json required"}, ensure_ascii=False, indent=2), mimetype="application/json"), 415
    payload = request.get_json()
    rows = payload.get("entries", [])
    if not isinstance(rows, list):
        return Response(json.dumps({"error": "entries must be a list"}, ensure_ascii=False, indent=2), mimetype="application/json"), 400
    try:
        result = assemble_and_compute_with_requirements(rows)
        return Response(json.dumps(result, ensure_ascii=False, indent=2), mimetype="application/json"), 200
    except Exception as e:
        return Response(json.dumps({"error": str(e)}, ensure_ascii=False, indent=2), mimetype="application/json"), 500

@app.post("/gpa/save")
def save_entries():
    if not request.is_json:
        return Response(json.dumps({"error": "Content-Type application/json required"}, ensure_ascii=False, indent=2), mimetype="application/json"), 415
    payload = request.get_json()
    rows = payload.get("entries", [])
    if not isinstance(rows, list):
        return Response(json.dumps({"error": "entries must be a list"}, ensure_ascii=False, indent=2), mimetype="application/json"), 400
    try:
        # assemble_and_compute 内で CSV 保存処理も行う
        assemble_and_compute(rows)
        return Response(json.dumps({"message": "entries saved"}, ensure_ascii=False, indent=2), mimetype="application/json"), 200
    except Exception as e:
        return Response(json.dumps({"error": str(e)}, ensure_ascii=False, indent=2), mimetype="application/json"), 500

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000, debug=True)
