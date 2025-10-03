# keisan_api.py
from typing import Any, Dict, List
import os
from flask import Flask, request, jsonify
from keisan_logic import (
    resolve_entries_for_save_lenient,  # ← 存在する科目だけ保存、無いものは warnings
    save_entries,                      # entries.csv へ保存（主キー: subject_id）
    compute_from_entries,              # entries.csv 全件から累積GPAを計算（保存名で出力）
    reload_courses_cache,              # subjects.csv の初期ロード
    resolve_entries_for_compute,       # その場計算用（保存しない/未登録はスキップ）
)
from keisan_core import compute_gpa

PORT = int(os.getenv("PORT", "5000"))

def create_app() -> Flask:
    app = Flask(__name__)
    # 日本語を \uXXXX にしない
    app.config["JSON_AS_ASCII"] = False
    try:
        app.json.ensure_ascii = False
    except Exception:
        pass

    @app.post("/gpa/save")
    def gpa_save():
        """
        寛容保存：subjects.csv に存在する科目だけを保存。存在しない科目は保存せず warnings に記録。
        保存後、entries.csv 全件で累積計算した結果を 'result' に同梱して返す。
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

            cumulative = compute_from_entries()

            return jsonify({
                "message": "entries processed",
                "saved": saved_count,
                "skipped": resolved["skipped"],
                "warnings": resolved["warnings"],  # 保存スキップ等の注意
                "result": cumulative               # 直後の累積GPA（保存値ベース）
            }), 200

        except Exception:
            return jsonify({"error": "internal error"}), 500

    @app.post("/gpa/compute")
    def gpa_compute():
        """
        2モード:
        ・ボディに entries があれば: その場で name+grade を解決して計算（保存しない）
            - subjects にない科目はスキップし warnings に記録
        ・ボディが無い/不正なら: entries.csv 全件から累積計算（保存値ベース）
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

            # 従来どおり累積計算（entries.csv を全読み）
            result = compute_from_entries()
            return jsonify(result), 200

        except Exception:
            return jsonify({"error": "internal error"}), 500

    @app.get("/healthz")
    def healthz():
        return jsonify({"ok": True}), 200

    return app

if __name__ == "__main__":
    app = create_app()
    try:
        reload_courses_cache()  # 起動時に subjects.csv を一度ロード（なくても起動続行）
    except Exception:
        pass
    app.run(host="127.0.0.1", port=PORT, debug=True)
