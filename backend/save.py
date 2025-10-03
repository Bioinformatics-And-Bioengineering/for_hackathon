# save.py
import os, csv
from typing import List, Dict, Any

def _entries_csv_path() -> str:
    return os.getenv("ENTRIES_CSV", os.path.join(os.path.dirname(__file__), "entries.csv"))

def append_entries(rows: List[Dict[str, Any]], key: str = "subject_id"):
    """
    rows: [{subject_id,name,grade,credits,field}, ...]
    既存 entries.csv を読み込み、主キー(key)が同じものは上書き、無ければ追加。
    出力は UTF-8 (BOM付)。
    """
    path = _entries_csv_path()
    existing = {}

    # 既存読み込み
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for r in reader:
                if r.get(key):
                    existing[r[key]] = r

    # 上書きマージ
    for r in rows:
        if r.get(key) is None:
            continue
        existing[r[key]] = {**existing.get(r[key], {}), **r}

    # 書き出し
    fieldnames = ["subject_id", "name", "grade", "credits", "field"]
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(existing.values())
