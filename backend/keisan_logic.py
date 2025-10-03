# keisan_logic.py
import os, csv, time, threading
from typing import Dict, Any, List, Tuple, Optional, Iterable
from keisan_core import compute_gpa
try:
    from keisan_requirements import check_requirements  # 任意：実装があれば使用
except Exception:
    def check_requirements(entries):
        return {"summary": "requirements check not configured"}

from save import append_entries as _append_entries  # 主キー指定で上書きマージ

# ============ 設定 ============
# 既定ではフォールバックは使いません（未登録は保存しない）。
ALLOW_FALLBACK = os.getenv("ALLOW_FALLBACK", "0").lower() in {"1", "true", "yes"}
TEMP_CREDITS = float(os.getenv("TEMP_CREDITS", "2.0"))

# subjects.csv ヘッダ対応
ID_KEYS      = {"id", "科目ID"}
NAME_KEYS    = {"name", "科目名", "講義名", "科目"}
CREDITS_KEYS = {"credits", "単位数", "単位"}
FIELD_KEYS   = {"field", "小区分ID", "分野", "カテゴリ"}

# ============ subjects.csv キャッシュ ============
_cache_lock = threading.RLock()
_subj_by_id: Dict[str, Dict[str, Any]] = {}
_subj_by_name_norm: Dict[str, Dict[str, Any]] = {}
_cache_mtime: Optional[float] = None
_cache_path: Optional[str] = None
_last_check = 0.0
CHECK_INTERVAL = 2.0  # 秒

def _subjects_csv_path() -> str:
    env = os.getenv("COURSES_CSV")
    if env:
        return os.path.abspath(env)
    base = os.getenv("DATA_DIR", os.path.dirname(__file__))
    return os.path.abspath(os.path.join(base, "subjects.csv"))

def _normalize_name(s: str) -> str:
    # 全角空白→半角、ローマ数字→アルファベット
    s = (s or "").strip().replace("\u3000", " ")
    return (s.replace("Ⅰ", "I").replace("Ⅱ", "II").replace("Ⅲ", "III")
             .replace("Ⅳ", "IV").replace("Ⅴ", "V"))

def _normalize_headers(fieldnames) -> Dict[str, str]:
    fields = [str(x).strip() for x in (fieldnames or [])]
    def pick(cands: set[str], default: str) -> str:
        for c in fields:
            if c in cands:
                return c
        return default
    return {
        "id":      pick(ID_KEYS, "科目ID"),
        "name":    pick(NAME_KEYS, "科目名"),
        "credits": pick(CREDITS_KEYS, "単位数"),
        "field":   pick(FIELD_KEYS, "小区分ID"),
    }

def _load_subjects_dict(path: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    by_id, by_name_norm = {}, {}
    with open(path, "r", encoding="utf-8-sig", newline="") as f:  # BOM安全
        reader = csv.DictReader(f)
        h = _normalize_headers(reader.fieldnames or [])
        for row in reader:
            sid = (row.get(h["id"], "") or "").strip()
            name = (row.get(h["name"], "") or "").strip()
            if not sid or not name:
                continue
            cr_raw = (row.get(h["credits"], "") or "").strip()
            field_val = (row.get(h["field"], "") or "").strip() or "TBD"
            try:
                credits = float(cr_raw)
            except Exception:
                continue
            if credits <= 0:
                continue
            rec = {"id": sid, "name": name, "credits": credits, "field": field_val}
            by_id[sid] = rec
            by_name_norm[_normalize_name(name)] = rec
    return by_id, by_name_norm

def _maybe_reload_subjects(force: bool = False) -> None:
    global _subj_by_id, _subj_by_name_norm, _cache_mtime, _cache_path, _last_check
    path = _subjects_csv_path()
    now = time.time()
    if not force and (now - _last_check) < CHECK_INTERVAL and _cache_path == path:
        return
    _last_check = now
    try:
        mtime = os.path.getmtime(path)
    except FileNotFoundError:
        with _cache_lock:
            _subj_by_id, _subj_by_name_norm, _cache_mtime, _cache_path = {}, {}, None, path
        return
    if force or (_cache_mtime is None) or (_cache_path != path) or (_cache_mtime != mtime):
        by_id, by_name_norm = _load_subjects_dict(path)
        with _cache_lock:
            _subj_by_id, _subj_by_name_norm = by_id, by_name_norm
            _cache_mtime, _cache_path = mtime, path

def reload_courses_cache() -> None:
    _maybe_reload_subjects(force=True)

def _get_by_id(sid: str) -> Optional[Dict[str, Any]]:
    _maybe_reload_subjects()
    with _cache_lock:
        return _subj_by_id.get(sid)

def _get_by_name(name: str) -> Optional[Dict[str, Any]]:
    _maybe_reload_subjects()
    with _cache_lock:
        return _subj_by_name_norm.get(_normalize_name(name))

# ============ 保存用（寛容）：存在する科目だけを保存、無いものは warning ============

def resolve_entries_for_save_lenient(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    入力: [{"name":"…","grade":"A"}, ...]
    - subjects.csv に存在する科目だけを details に入れて保存対象とする
    - 存在しない科目は details に入れず warnings に積む（保存しない）
    返り値: {"details":[{subject_id,name,grade,credits,field}...], "warnings":[...], "skipped": N}
    """
    details: List[Dict[str, Any]] = []
    warnings: List[str] = []
    skipped = 0

    for i, r in enumerate(rows):
        name = (r.get("name") or "").strip()
        grade = (r.get("grade") or "").strip().upper()

        if not name:
            skipped += 1
            warnings.append(f"entries[{i}].name is empty -> skipped")
            continue
        if grade not in {"A", "B", "C", "D", "F"}:
            skipped += 1
            warnings.append(f"entries[{i}].grade '{grade}' not supported (A/B/C/D/F) -> skipped")
            continue

        rec = _get_by_name(name)
        if not rec:
            skipped += 1
            warnings.append(f"subject name '{name}' not found in subjects.csv -> skipped")
            continue

        details.append({
            "subject_id": rec["id"],    # 保存の主キー
            "name":       rec["name"],  # 保存時点の名称
            "grade":      grade,
            "credits":    float(rec["credits"]),
            "field":      rec["field"],
        })

    return {"details": details, "warnings": warnings, "skipped": skipped}

def save_entries(details: List[Dict[str, Any]],
                 *, fields=("subject_id", "name", "grade", "credits", "field")):
    if not details:
        return
    rows = [{k: d.get(k) for k in fields} for d in details]
    _append_entries(rows, key="subject_id")  # subject_id 主キーで上書きマージ

# ============ その場計算（保存しない）：未登録はスキップ ============

def resolve_entries_for_compute(rows: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    """
    その場計算（保存しない）用:
      - subjects.csv にある科目のみ details に入れる
      - 無い科目は warnings に記録してスキップ
    """
    details: List[Dict[str, Any]] = []
    warnings: List[str] = []

    for i, r in enumerate(rows):
        name = (r.get("name") or "").strip()
        grade = (r.get("grade") or "").strip().upper()
        if not name:
            warnings.append(f"entries[{i}].name is empty -> skipped")
            continue
        if grade not in {"A", "B", "C", "D", "F"}:
            warnings.append(f"entries[{i}].grade '{grade}' not supported -> skipped")
            continue

        rec = _get_by_name(name)
        if not rec:
            warnings.append(f"subject name '{name}' not found in subjects.csv -> skipped")
            continue

        details.append({
            "name":    rec["name"],    # その場計算は subjects 側名でOK
            "grade":   grade,
            "credits": float(rec["credits"]),
            "field":   rec["field"],
        })

    return {"details": details, "warnings": warnings}

# ============ 累積計算（保存値ベース）：entries.csv → GPA ============

def _entries_csv_path() -> str:
    return os.getenv("ENTRIES_CSV", os.path.join(os.path.dirname(__file__), "entries.csv"))

def _load_entries_csv() -> List[Dict[str, Any]]:
    path = _entries_csv_path()
    if not os.path.exists(path):
        return []
    out: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sid   = (row.get("subject_id") or "").strip()
            name  = (row.get("name") or "").strip()
            grade = (row.get("grade") or "").strip().upper()
            credits = row.get("credits")
            field = (row.get("field") or "TBD").strip()
            if not sid or grade not in {"A", "B", "C", "D", "F"}:
                continue
            try:
                cr = float(credits)
            except Exception:
                continue
            if cr <= 0:
                continue
            out.append({"subject_id": sid, "name": name, "grade": grade, "credits": cr, "field": field})
    return out

def compute_from_entries() -> Dict[str, Any]:
    """
    entries.csv 全件を読み、保存値（当時の名称・単位・小区分）で GPA を計算。
    subjects.csv は一致チェックのみ（IDが見つからない場合は warnings を出す）。
    """
    entries = _load_entries_csv()
    if not entries:
        base = {"gpa": 0.0, "total_credits_counted": 0.0, "details": [], "warnings": []}
        try:
            base["requirements"] = check_requirements([])
        except Exception:
            pass
        return base

    warnings: List[str] = []
    resolved: List[Dict[str, Any]] = []

    for e in entries:
        sid = e["subject_id"]
        subj = _get_by_id(sid)  # 参照のみ（出力名には使わない）
        if not subj:
            warnings.append(f"subject_id '{sid}' not found in subjects.csv. Using saved name/credits/field.")

        resolved.append({
            "name":    e["name"],           # 保存名をそのまま
            "grade":   e["grade"],
            "credits": float(e["credits"]),
            "field":   e["field"],
        })

    result = compute_gpa(resolved)   # {"gpa","total_credits_counted","details":[...]}
    result["warnings"] = warnings

    try:
        result["requirements"] = check_requirements()
    except Exception:
        pass

    return result
