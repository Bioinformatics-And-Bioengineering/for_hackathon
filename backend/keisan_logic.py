# logic.py
import os, csv, time, threading
from typing import Dict, Any, Tuple, Optional, List
from keisan_core import compute_gpa
from keisan_requirements import check_requirements  #追加した

# ===== 設定（環境変数で変更可）=====
ALLOW_FALLBACK = os.getenv("ALLOW_FALLBACK", "1").lower() in {"1", "true", "yes"}
TEMP_CREDITS = float(os.getenv("TEMP_CREDITS", "2.0"))

# 列名エイリアス
NAME_KEYS    = {"name", "科目名", "講義名", "科目"}
CREDITS_KEYS = {"credits", "単位数", "単位"}
FIELD_KEYS   = {"field", "小区分ID", "分野", "カテゴリ"}

# ===== CSVパス（backend直下 subjects.csv を既定）=====
def _courses_csv_path() -> str:
    env = os.getenv("COURSES_CSV")
    if env:
        return os.path.abspath(env)
    base = os.getenv("DATA_DIR", os.path.dirname(__file__))  # backend/
    return os.path.abspath(os.path.join(base, "subjects.csv"))

# ===== 軽量キャッシュ =====
_cache_lock = threading.RLock()
_cache: Dict[str, Dict[str, Any]] = {}  # name -> {name, credits, field}
_cache_mtime: Optional[float] = None
_cache_path: Optional[str] = None
_last_check = 0.0
CHECK_INTERVAL = 2.0

def _normalize_headers(fieldnames) -> Dict[str, str]:
    fields = [str(x).strip() for x in (fieldnames or [])]
    def pick(cands: set[str], default: str) -> str:
        for c in fields:
            if c in cands:
                return c
        return default
    return {
        "name":    pick(NAME_KEYS, "科目名"),
        "credits": pick(CREDITS_KEYS, "単位数"),
        "field":   pick(FIELD_KEYS, "小区分ID"),
    }

def _load_csv_dict(path: str) -> Dict[str, Dict[str, Any]]:
    db: Dict[str, Dict[str, Any]] = {}
    with open(path, "r", encoding="utf-8-sig", newline="") as f:  # BOM対応
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
                continue
            if credits <= 0:
                continue
            db[name] = {"name": name, "credits": credits, "field": field_val}
    return db

def _maybe_reload(force: bool = False) -> None:
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

# ===== ロジックの公開API：入力（name, grade）を受けて「計算-ready」へ組み立て =====
def assemble_and_compute(entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    entries: [{"name":"…","grade":"A"}, ...]
    - CSVから credits / field を解決
    - GPAを計算
    - warnings を付与
    """
    assembled: List[Dict[str, Any]] = []
    warnings: List[str] = []
    for i, r in enumerate(entries):
        name = (r.get("name") or "").strip()
        grade = (r.get("grade") or "").strip().upper()
        course, warn = get_course_by_name(name)
        if warn:
            warnings.append(warn)
        assembled.append({
            "name": name,
            "grade": grade,
            "credits": course["credits"],
            "field": course["field"],
        })
    result = compute_gpa(assembled)
    result["warnings"] = warnings

    # ★ 卒業要件の判定を追加（CSVから要件を読み込み）（追加した)
    req_report = check_requirements(assembled)
    result["requirements"] = req_report

    return result
