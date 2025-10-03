# keisan_api.py
from typing import Any, Dict, List
import os
from flask import Blueprint, request, jsonify
from keisan_logic import (
    resolve_entries_for_save_lenient,  # 存在する科目だけ保存、無いものは warnings へ
    save_entries,                      # entries.csv へ保存（主キー: subject_id）
    compute_from_entries,              # entries.csv 全件から累積GPA（保存名で出力）
    reload_courses_cache,              # subjects.csv の初期ロード（app.py 側で呼んでもOK）
    resolve_entries_for_compute,       # その場計算（保存しない/未登録はスキップ）
)
from keisan_core import compute_gpa

PORT = int(os.getenv("PORT", "5000"))
keisan_bp = Blueprint('keisan_api', __name__)

@keisan_bp.post("/gpa/save")
def gpa_save():
    """
    寛容保存：subjects.csv に存在する科目だけを保存。存在しない科目は保存せず warnings に記録。
    ※ GPA は返さない（保存のみ）。
    返り値例:
    {
      "message": "entries processed",
      "saved": 3,
      "skipped": 1,
      "warnings": ["subject name 'テスト' not found in subjects.csv -> skipped"]
    }
    """
    if not request.is_json:
        return jsonify({"error": "Content-Type application/json required"}), 415

    payload: Dict[str, Any] = request.get_json(silent=True) or {}
    rows: List[Dict[str, Any]] = payload.get("entries", [])
    if not isinstance(rows, list):
        return jsonify({"error": "entries must be a list"}), 400

    try:
        resolved = resolve_entries_for_save_lenient(rows)   # {"details":[...], "warnings":[...], "skipped":N}
        saved_count = len(resolved["details"])
        if saved_count > 0:
            save_entries(resolved["details"])
        # 保存が0件でも 200 で返す（実行は止めず、警告を返す）

        return jsonify({
            "message": "entries processed",
            "saved": saved_count,
            "skipped": resolved["skipped"],
            "warnings": resolved["warnings"]
        }), 200

    except Exception:
        return jsonify({"error": "internal error"}), 500

@keisan_bp.get("/gpa/summary")
def gpa_summary():
    """
    累積取得：entries.csv 全件から GPA を返す（保存値＝当時の名称/単位/小区分で計算）。
    返り値例: { "gpa": 3.0, "total_credits_counted": 6.0, "details": [...], "warnings": [...] }
    """
    try:
        result = compute_from_entries()
        return jsonify(result), 200
    except Exception:
        return jsonify({"error": "internal error"}), 500

@keisan_bp.post("/gpa/compute")
def gpa_compute():
    """
    その場計算（保存しない）:
    ・ボディに entries があるときのみ実行。未登録はスキップして warnings に記録。
    ・ボディ無し/不正は 400（累積は /gpa/summary を使う設計に分離したため）。
    返り値例: { "gpa": 2.67, "total_credits_counted": 6.0, "details": [...], "warnings": [...] }
    """
    try:
        if request.is_json:
            payload = request.get_json(silent=True) or {}
            rows = payload.get("entries")
            if isinstance(rows, list) and rows:
                resolved = resolve_entries_for_compute(rows)  # 保存しない・未登録はスキップ
                result = compute_gpa(resolved["details"])
                result["warnings"] = resolved["warnings"]
                return jsonify(result), 200

        return jsonify({
            "error": "entries missing. For cumulative GPA, call GET /gpa/summary"
        }), 400

    except Exception:
        return jsonify({"error": "internal error"}), 500

@keisan_bp.get("/healthz")
def healthz():
    return jsonify({"ok": True}), 200
