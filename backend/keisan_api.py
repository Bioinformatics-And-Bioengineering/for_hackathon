# api.py
from typing import Any, Dict
import os
from flask import Flask, request, jsonify
from logic import assemble_and_compute, reload_courses_cache

PORT = int(os.getenv("PORT", "8000"))

def create_app() -> Flask:
    app = Flask(__name__)
    # ���{�ꂪ \u �G�X�P�[�v����Ȃ��悤��
    app.config["JSON_AS_ASCII"] = False
    try:
        app.json.ensure_ascii = False
    except Exception:
        pass

    @app.post("/gpa/compute")
    def gpa_compute():
        if not request.is_json:
            return jsonify({"error": "Content-Type application/json required"}), 415
        payload: Dict[str, Any] = request.get_json(silent=True) or {}
        rows = payload.get("entries")
        if not isinstance(rows, list):
            return jsonify({"error": "entries must be a list"}), 400
        try:
            result = assemble_and_compute(rows)
            return jsonify(result), 200
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        except Exception:
            return jsonify({"error": "internal error"}), 500

    @app.get("/healthz")
    def healthz():
        return jsonify({"ok": True}), 200

    return app

if __name__ == "__main__":
    app = create_app()
    try:
        reload_courses_cache()  # �N�����Ɉ�x�ǂݍ��ށi���݂��Ȃ��Ă�OK�j
    except Exception:
        pass
    app.run(host="0.0.0.0", port=PORT, debug=True)
