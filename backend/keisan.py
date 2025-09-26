# -*- coding: utf-8 -*-
"""
�P��t�@�C���Łibackend �����ɒu���j
- CSV: backend/data/subjects.csv�i�f�t�H���g�j
  - ���ϐ��ŏ㏑���\: COURSES_CSV=/abs/path/to/subjects.csv
  - �������� DATA_DIR=./data �isubjects.csv �͂��̒����ɂ���z��j
- API:
  POST /gpa/compute
  body:
    {
      "entries": [
        {"name":"�����ϕ��w�T","grade":"A"},
        {"name":"���`�㐔�w�T","grade":"B"}
      ]
    }
  �߂�:
    {
      "gpa": 2.67,
      "total_credits_counted": 5.0,
      "details": [...],
      "warnings": [...]
    }
"""

from __future__ import annotations
import os
import csv
import time
import threading
from typing import Dict, Any, Tuple, Optional, List
from flask import Flask, request, jsonify


# =========================
# �ݒ�i���ϐ��ŕύX�\�j
# =========================
PORT = int(os.getenv("PORT", "8000"))
# ���o�^�Ȗڂ��b��l�Ōv�Z���邩�i1/true �ŗL���j
ALLOW_FALLBACK = os.getenv("ALLOW_FALLBACK", "1").lower() in {"1", "true", "yes"}
TEMP_CREDITS = float(os.getenv("TEMP_CREDITS", "2.0"))

# �񖼃G�C���A�X�i���{��w�b�_�Ή��j
NAME_KEYS    = {"name", "�Ȗږ�", "�u�`��", "�Ȗ�"}
CREDITS_KEYS = {"credits", "�P�ʐ�", "�P��"}
FIELD_KEYS   = {"field", "���敪ID", "����", "�J�e�S��"}

# A~F �� 4.0~0.0 �ɕϊ��i�}�Ȃ��j
GRADE_TO_POINT: Dict[str, float] = {
    "A": 4.0, "B": 3.0, "C": 2.0, "D": 1.0, "F": 0.0,
}

# =========================
# CSV ���[�_�iBOM �Ή��j+ �L���b�V��
# =========================
_cache_lock = threading.RLock()
_cache: Dict[str, Dict[str, Any]] = {}     # name -> {name, credits, field}
_cache_mtime: Optional[float] = None
_cache_path: Optional[str] = None
_last_check = 0.0
CHECK_INTERVAL = 2.0  # �b

def _courses_csv_path() -> str:
    """
    CSV �p�X�̉���: COURSES_CSV > DATA_DIR/subjects.csv > ./data/subjects.csv
    """
    env = os.getenv("COURSES_CSV")
    if env:
        return os.path.abspath(env)
    base = os.getenv("DATA_DIR", os.path.join(os.path.dirname(__file__), "data"))
    return os.path.abspath(os.path.join(base, "subjects.csv"))

def _normalize_headers(fieldnames) -> Dict[str, str]:
    fields = [str(x).strip() for x in (fieldnames or [])]

    def pick(cands: set[str], default: str) -> str:
        for c in fields:
            if c in cands:
                return c
        return default

    # �f�t�H���g�͓��{��̑z��w�b�_��D��isubjects.csv �̗�ɍ��킹��j
    return {
        "name":    pick(NAME_KEYS, "�Ȗږ�"),
        "credits": pick(CREDITS_KEYS, "�P�ʐ�"),
        "field":   pick(FIELD_KEYS, "���敪ID"),
    }

def _load_csv_dict(path: str) -> Dict[str, Dict[str, Any]]:
    """
    subjects.csv ��ǂݍ��݁Aname ���L�[�Ɏ������B
    BOM �t���ł����S�ɓǂނ��� encoding='utf-8-sig' ���g�p�B
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
                # ���l�łȂ��P�ʂ̓X�L�b�v
                continue
            if credits <= 0:
                continue
            db[name] = {"name": name, "credits": credits, "field": field_val}
    return db

def _maybe_reload(force: bool = False) -> None:
    """
    CSV �̍X�V�� 2 �b�Ԋu�Ō��m���ă����[�h�B
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
    ���͂̍u�`���i�Ȗږ��j�Ɉ�v���� {name, credits, field} ��Ԃ��B
    ������Ȃ��ꍇ�F
      - ALLOW_FALLBACK=True �Ȃ�b��N���W�b�g�ŕԂ� warning �t�^
      - False �̏ꍇ�� ValueError
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
# GPA �v�Z�i�������W�b�N�j
# =========================
def compute_gpa(entries_with_meta: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    entries_with_meta: [{"name","grade","credits","field"}...]
    GPA = ��(point*credits) / ��(credits) ��������2�ʂŕԂ��B
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
# Flask �A�v��
# =========================
def create_app() -> Flask:
    app = Flask(__name__)

    @app.post("/gpa/compute")
    def gpa_compute():
        """
        ��MJSON ��:
        {
          "entries": [
            {"name":"�����ϕ��w�T", "grade":"A"},
            {"name":"���`�㐔�w�T", "grade":"B"},
            {"name":"���ϗ�",   "grade":"F"}
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
                course, warn = get_course_by_name(name)  # CSV���� credits/field ������
                if warn:
                    warnings.append(warn)
                assembled.append({
                    "name": name,
                    "grade": grade,
                    "credits": course["credits"],
                    "field": course["field"],  # ���敪ID ��
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

# �J���p�G���g��
if __name__ == "__main__":
    app = create_app()
    # subjects.csv �̏��񃍁[�h�i���݂��Ȃ��Ă��N���͂���j
    try:
        reload_courses_cache()
    except Exception:
        pass
    app.run(host="0.0.0.0", port=PORT, debug=True)
