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
    entries_with_meta: List[Dict[str, Any]],
    *,
    req_csv: str = REQ_CSV,
    subcats_csv: str = SUBCATS_CSV,
    cats_csv: str = CATS_CSV,
    maincats_csv: str = MAINCATS_CSV,
) -> Dict[str, Any]:
    """
    entries_with_meta: [{"name","grade","credits","field"}...]
      - grade == "F" は取得単位に含めない
      - field は subjects.csv の「小区分ID」に相当することを想定
    戻り値:
    {
      "ok": bool,
      "by_subcategory": [
        {"小区分ID":7, "小区分":"分野基盤科目", "required":6, "earned":6, "short":0},
        ...
      ],
      "by_major": [
        {"大区分ID":1, "大区分":"プログラム科目", "required":XX, "earned":YY, "short":max(0, ...)}
      ],
      "by_maincategory": [
        {"カテゴリID":2, "カテゴリ区分":"情報生体専門科目", "required":..., "earned":..., "short":...}
      ],
      "short_summary": {"合計不足": 14},  # 0 ならクリア
      "warnings": [...]
    }
    """
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

