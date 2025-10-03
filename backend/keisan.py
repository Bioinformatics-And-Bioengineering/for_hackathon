# -*- coding: utf-8 -*-

from __future__ import annotations
import os
import csv
import time
import threading
from typing import Dict, Any, Tuple, Optional, List
from flask import Flask, request, jsonify


# =========================
# 設定（環境変数で変更可能）
# =========================
PORT = int(os.getenv("PORT", "8000"))
# 未登録科目を暫定値で計算するか（1/true で有効）
ALLOW_FALLBACK = os.getenv("ALLOW_FALLBACK", "1").lower() in {"1", "true", "yes"}
TEMP_CREDITS = float(os.getenv("TEMP_CREDITS", "2.0"))

# 列名エイリアス（日本語ヘッダ対応）
NAME_KEYS    = {"name", "科目名", "講義名", "科目"}
CREDITS_KEYS = {"credits", "単位数", "単位"}
FIELD_KEYS   = {"field", "小区分ID", "分野", "カテゴリ"}

# A~F を 4.0~0.0 に変換（±なし）
GRADE_TO_POINT: Dict[str, float] = {
    "A": 4.0, "B": 3.0, "C": 2.0, "D": 1.0, "F": 0.0,
}

# =========================
# CSV ローダ（BOM 対応）+ キャッシュ
# =========================
_cache_lock = threading.RLock()
_cache: Dict[str, Dict[str, Any]] = {}     # name -> {name, credits, field}
_cache_mtime: Optional[float] = None
_cache_path: Optional[str] = None
_last_check = 0.0
CHECK_INTERVAL = 2.0  # 秒

def _courses_csv_path() -> str:
    """
    CSV パスの解決: COURSES_CSV > DATA_DIR/subjects.csv > ./data/subjects.csv
    """
    env = os.getenv("COURSES_CSV")
    if env:
        return os.path.abspath(env)
    base = os.getenv("DATA_DIR", os.path.dirname(__file__)) 
    return os.path.abspath(os.path.join(base, "subjects.csv"))

def _normalize_headers(fieldnames) -> Dict[str, str]:
    fields = [str(x).strip() for x in (fieldnames or [])]

    def pick(cands: set[str], default: str) -> str:
        for c in fields:
            if c in cands:
                return c
        return default

    # デフォルトは日本語の想定ヘッダを優先（subjects.csv の例に合わせる）
    return {
        "name":    pick(NAME_KEYS, "科目名"),
        "credits": pick(CREDITS_KEYS, "単位数"),
        "field":   pick(FIELD_KEYS, "小区分ID"),
    }

def _load_csv_dict(path: str) -> Dict[str, Dict[str, Any]]:
    """
    subjects.csv を読み込み、name をキーに辞書化。
    BOM 付きでも安全に読むため encoding='utf-8-sig' を使用。
    """
    db: Dict[str, Dict[str, Any]] = {}
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        header_map = _normalize_headers(reader.fieldnames or [])
        for row in reader:
            name = (row.get(header_map["name"], "") or "").strip()
            if not name:
                continue
            credits_raw = (row.get(header_map["credits"], "") or "").strip()
            field_val = (row.get(header_map["field"], "") or "").strip() or "TBD"
            try:
                credits = float(credits_raw)
            except Exception:
                # 数値でない単位はスキップ
                continue
            if credits <= 0:
                continue
            db[name] = {"name": name, "credits": credits, "field": field_val}
    return db

def _maybe_reload(force: bool = False) -> None:
    """
    CSV の更新を 2 秒間隔で検知してリロード。
    """
    global _cache, _cache_mtime, _cache_path, _last_check
    path = _courses_csv_path()
    now = time.time()
    if not force and (now - _last_check) < CHECK_INTERVAL and _cache_path == path:
        return
    _last_check = now

    try:
        mtime = os.path.getmtime(path)
    except FileNotFoundError:
        with _cache_lock:
            _cache, _cache_mtime, _cache_path = {}, None, path
        return

    if force or (_cache_mtime is None) or (_cache_path != path) or (_cache_mtime != mtime):
        db = _load_csv_dict(path)
        with _cache_lock:
            _cache = db
            _cache_mtime = mtime
            _cache_path = path

def get_course_by_name(name: str) -> Tuple[Dict[str, Any], Optional[str]]:
    """
    入力の講義名（科目名）に一致する {name, credits, field} を返す。
    見つからない場合：
      - ALLOW_FALLBACK=True なら暫定クレジットで返し warning 付与
      - False の場合は ValueError
    """
    key = (name or "").strip()
    if not key:
        raise ValueError("course name is empty")

    _maybe_reload()
    with _cache_lock:
        row = _cache.get(key)

    if row:
        return {"name": row["name"], "credits": float(row["credits"]), "field": row["field"]}, None

    if ALLOW_FALLBACK:
        warn = f"'{key}' not in subjects.csv. Fallback TEMP_CREDITS={TEMP_CREDITS} (field=TBD)"
        return {"name": key, "credits": TEMP_CREDITS, "field": "TBD"}, warn

    raise ValueError(f"'{key}' not found in subjects.csv")

def reload_courses_cache() -> None:
    _maybe_reload(force=True)

# =========================
# GPA 計算（純粋ロジック）
# =========================
def compute_gpa(entries_with_meta: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    entries_with_meta: [{"name","grade","credits","field"}...]
    GPA = Σ(point*credits) / Σ(credits) を小数第2位で返す。
    """
    if not entries_with_meta:
        return {"gpa": 0.00, "total_credits_counted": 0.0, "details": []}

    numer = denom = 0.0
    details: List[Dict[str, Any]] = []

    for i, e in enumerate(entries_with_meta):
        name = str(e.get("name", "")).strip()
        grade_raw = str(e.get("grade", "")).strip().upper()
        credits = e.get("credits", 0)

        if not name:
            raise ValueError(f"entries[{i}].name is empty")
        if grade_raw not in GRADE_TO_POINT:
            raise ValueError(f"entries[{i}].grade '{grade_raw}' not supported (A/B/C/D/F)")
        try:
            cr = float(credits)
        except Exception:
            raise ValueError(f"entries[{i}].credits is not a number")
        if cr <= 0:
            raise ValueError(f"entries[{i}].credits must be > 0")

        point = GRADE_TO_POINT[grade_raw]
        numer += point * cr
        denom += cr
        details.append({
            "name": name, "grade": grade_raw, "point": point,
            "credits": cr, "field": e.get("field", "TBD"),
        })

    gpa = round(numer / denom, 2) if denom else 0.00
    return {"gpa": gpa, "total_credits_counted": denom, "details": details}

# =========================
# Flask アプリ
# =========================
def create_app() -> Flask:
    app = Flask(__name__)

    app.config["JSON_AS_ASCII"] = False
    try:
        app.json.ensure_ascii = False
    except Exception:
        pass

    @app.post("/gpa/compute")
    def gpa_compute():
        """
        受信JSON 例:
        {
          "entries": [
            {"name":"微分積分学Ⅰ", "grade":"A"},
            {"name":"線形代数学Ⅰ", "grade":"B"},
            {"name":"情報倫理",   "grade":"F"}
          ]
        }
        """
        if not request.is_json:
            return jsonify({"error": "Content-Type application/json required"}), 415
        payload = request.get_json(silent=True) or {}
        rows = payload.get("entries")
        if not isinstance(rows, list):
            return jsonify({"error": "entries must be a list"}), 400

        try:
            assembled: List[Dict[str, Any]] = []
            warnings: List[str] = []
            for i, r in enumerate(rows):
                name = (r.get("name") or "").strip()
                grade = (r.get("grade") or "").strip().upper()
                course, warn = get_course_by_name(name)  # CSVから credits/field を解決
                if warn:
                    warnings.append(warn)
                assembled.append({
                    "name": name,
                    "grade": grade,
                    "credits": course["credits"],
                    "field": course["field"],  # 小区分ID 等
                })

            result = compute_gpa(assembled)
            result["warnings"] = warnings
            return jsonify(result), 200

        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        except Exception:
            return jsonify({"error": "internal error"}), 500

    @app.get("/healthz")
    def healthz():
        return jsonify({"ok": True}), 200

    return app

# 開発用エントリ
if __name__ == "__main__":
    app = create_app()
    # subjects.csv の初回ロード（存在しなくても起動はする）
    try:
        reload_courses_cache()
    except Exception:
        pass
    app.run(host="0.0.0.0", port=PORT, debug=True)
