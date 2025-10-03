# requirements.py
from __future__ import annotations
from typing import List, Dict, Any, Tuple
import csv
import os

# 既定パス（環境変数で差し替え可）
REQ_CSV = os.getenv("GRAD_REQ_CSV", os.path.abspath(os.path.join(os.path.dirname(__file__), "graduation_requirements.csv")))
SUBCATS_CSV = os.getenv("SUBCATEGORIES_CSV", os.path.abspath(os.path.join(os.path.dirname(__file__), "subcategories.csv")))
CATS_CSV = os.getenv("CATEGORIES_CSV", os.path.abspath(os.path.join(os.path.dirname(__file__), "categories.csv")))
MAINCATS_CSV = os.getenv("MAINCATEGORIES_CSV", os.path.abspath(os.path.join(os.path.dirname(__file__), "maincategories.csv")))
ENTRIES_CSV = os.getenv("ENTRIES_CSV", os.path.abspath(os.path.join(os.path.dirname(__file__), "entries.csv")))


def _load_graduation_requirements(path: str = REQ_CSV) -> Dict[int, float]:
    """
    graduation_requirements.csv:
      小区分ID,単位数
      7,6
      8,2
      ...
    """
    req: Dict[int, float] = {}
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                sid = int(str(row.get("小区分ID", "")).strip())
                credits = float(str(row.get("単位数", "")).strip())
            except Exception:
                continue
            if sid > 0 and credits >= 0:
                req[sid] = credits
    return req

def _load_subcategories(path: str = SUBCATS_CSV) -> Dict[int, Dict[str, Any]]:
    """
    subcategories.csv:
      小区分ID,小区分,大区分ID
    """
    db: Dict[int, Dict[str, Any]] = {}
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for r in reader:
            try:
                sid = int(str(r.get("小区分ID", "")).strip())
                name = (r.get("小区分", "") or "").strip()
                mid = int(str(r.get("大区分ID", "")).strip())
            except Exception:
                continue
            db[sid] = {"name": name or f"小区分{sid}", "major_id": mid}
    return db

def _load_categories(path: str = CATS_CSV) -> Dict[int, Dict[str, Any]]:
    """
    categories.csv:
      大区分ID,大区分,カテゴリID
    """
    db: Dict[int, Dict[str, Any]] = {}
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for r in reader:
            try:
                mid = int(str(r.get("大区分ID", "")).strip())
                mname = (r.get("大区分", "") or "").strip()
                cid = int(str(r.get("カテゴリID", "")).strip())
            except Exception:
                continue
            db[mid] = {"name": mname or f"大区分{mid}", "category_id": cid}
    return db

def _load_maincategories(path: str = MAINCATS_CSV) -> Dict[int, str]:
    """
    maincategories.csv:
      カテゴリID,カテゴリ区分
    """
    db: Dict[int, str] = {}
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for r in reader:
            try:
                cid = int(str(r.get("カテゴリID", "")).strip())
                cname = (r.get("カテゴリ区分", "") or "").strip()
            except Exception:
                continue
            db[cid] = cname or f"カテゴリ{cid}"
    return db

def _safe_int(x: Any) -> int | None:
    try:
        return int(str(x).strip())
    except Exception:
        return None

def check_requirements(
    *,
    entries_csv: str = ENTRIES_CSV,
    req_csv: str = REQ_CSV,
    subcats_csv: str = SUBCATS_CSV,
    cats_csv: str = CATS_CSV,
    maincats_csv: str = MAINCATS_CSV,
) -> Dict[str, Any]:
    """
    entries.csv を読み取り、卒業要件を集計する。
    """
    # ★ここが新規：常に CSV を読む
    entries_with_meta = _load_entries_from_csv(entries_csv)
    
    # マスタ読込
    req_map = _load_graduation_requirements(req_csv)
    sub_db = _load_subcategories(subcats_csv)
    cat_db = _load_categories(cats_csv)
    main_db = _load_maincategories(maincats_csv)

    warnings: List[str] = []

    # 小区分ごとの取得単位集計（落第は除外）
    earned_by_sub: Dict[int, float] = {}
    for e in entries_with_meta:
        grade = str(e.get("grade", "")).strip().upper()
        if grade == "F":
            continue
        field = e.get("field", "")
        sid = _safe_int(field)
        if sid is None:
            # subjects.csv に見つからず TBD などの場合
            warnings.append(f"科目「{e.get('name','')}」の小区分IDが不明（field='{field}'）のため要件集計に含めません。")
            continue
        cr = float(e.get("credits", 0) or 0)
        if cr > 0:
            earned_by_sub[sid] = earned_by_sub.get(sid, 0.0) + cr

    # 小区分ごとの required/earned/short
    by_subcategory = []
    ok = True
    total_short = 0.0
    for sid, required in req_map.items():
        earned = earned_by_sub.get(sid, 0.0)
        short = max(0.0, required - earned)
        if short > 0:
            ok = False
            total_short += short
        sub_name = sub_db.get(sid, {}).get("name", f"小区分{sid}")
        by_subcategory.append({
            "小区分ID": sid,
            "小区分": sub_name,
            "required": required,
            "earned": round(earned, 2),
            "short": round(short, 2),
        })

    # 大区分（major）・カテゴリ（maincategory）へ集計
    # 小区分 -> 大区分 -> カテゴリ の階層で、要件(required)も合算
    # ※ graduation_requirements.csv に載っていない小区分は要件0扱い
    major_agg: Dict[int, Dict[str, float]] = {}
    main_agg: Dict[int, Dict[str, float]] = {}

    for row in by_subcategory:
        sid = row["小区分ID"]
        required = float(row["required"])
        earned = float(row["earned"])
        major_id = sub_db.get(sid, {}).get("major_id")
        if major_id is not None:
            m = major_agg.setdefault(major_id, {"required": 0.0, "earned": 0.0})
            m["required"] += required
            m["earned"] += earned

            # major -> category
            cat_info = cat_db.get(major_id)
            if cat_info:
                cid = cat_info["category_id"]
                c = main_agg.setdefault(cid, {"required": 0.0, "earned": 0.0})
                c["required"] += required
                c["earned"] += earned

    by_major = []
    for mid, agg in major_agg.items():
        mname = cat_db.get(mid, {}).get("name", f"大区分{mid}")
        short = max(0.0, agg["required"] - agg["earned"])
        by_major.append({
            "大区分ID": mid,
            "大区分": mname,
            "required": round(agg["required"], 2),
            "earned": round(agg["earned"], 2),
            "short": round(short, 2),
        })

    by_maincategory = []
    for cid, agg in main_agg.items():
        cname = main_db.get(cid, f"カテゴリ{cid}")
        short = max(0.0, agg["required"] - agg["earned"])
        by_maincategory.append({
            "カテゴリID": cid,
            "カテゴリ区分": cname,
            "required": round(agg["required"], 2),
            "earned": round(agg["earned"], 2),
            "short": round(short, 2),
        })

    return {
        "ok": ok and (total_short <= 0.0),
        "by_subcategory": sorted(by_subcategory, key=lambda r: r["小区分ID"]),
        "by_major": sorted(by_major, key=lambda r: r["大区分ID"]),
        "by_maincategory": sorted(by_maincategory, key=lambda r: r["カテゴリID"]),
        "short_summary": {"合計不足": round(total_short, 2)},
        "warnings": warnings,
    }

def _normalize_entry_row(row: Dict[str, Any]) -> Dict[str, Any]:
    # 想定: 科目名/name, 評価/grade, 単位数/credits, 小区分ID/field/subcategory_id
    def pick(d, keys, default=""):
        for k in keys:
            if k in d and d[k] not in (None, ""):
                return d[k]
        return default

    name = pick(row, ["科目名", "name", "subject", "title"])
    grade = str(pick(row, ["評価", "grade"])).strip().upper()

    credits_raw = pick(row, ["単位数", "credits"])
    try:
        credits = float(str(credits_raw).strip()) if credits_raw != "" else 0.0
    except Exception:
        credits = 0.0

    field_raw = pick(row, ["小区分ID", "field", "subcategory_id"])
    try:
        field = int(str(field_raw).strip()) if field_raw != "" else None
    except Exception:
        field = None

    return {"name": name, "grade": grade, "credits": credits, "field": field}

def _load_entries_from_csv(path: str = ENTRIES_CSV) -> List[Dict[str, Any]]:
    entries: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            entries.append(_normalize_entry_row(row))
    return entries
