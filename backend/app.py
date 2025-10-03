# 必要なライブラリをインポート
from flask import Flask, jsonify
from flask_cors import CORS
import csv

from keisan_api import keisan_bp
# keisan_logic.pyから初期化用の関数をインポートする場合
from keisan_logic import reload_courses_cache

# Flaskアプリケーションのインスタンスを作成
app = Flask(__name__)

# ★★★ この一行を追加 ★★★
# JSONレスポンスで日本語がUnicodeエスケープされないように設定
app.json.ensure_ascii = False

# CORS（Cross-Origin Resource Sharing）を有効にする
CORS(app)

# --- keisan_apiで定義したブループリントをappに登録します ---
app.register_blueprint(keisan_bp)

# '/api/subjects' というURLにGETリクエストが来たときに実行される関数を定義
@app.route('/api/subjects', methods=['GET'])
def get_subjects():
    """
    subjects.csvから科目名を読み込み、JSON形式で返す関数
    """
    subject_names = []
    try:
        # subjects.csvをUTF-8エンコーディングで開く
        with open('subjects.csv', mode='r', encoding='utf-8-sig') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if '科目名' in row:
                    subject_names.append(row['科目名'])
                
        return jsonify({'subjects': subject_names})

    except FileNotFoundError:
        return jsonify({'error': 'subjects.csvが見つかりません。'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# このファイルが直接実行された場合にサーバーを起動
if __name__ == '__main__':
     # ★★★ ここから追加 ★★★
    # アプリケーションに登録されている全ルートを一覧表示する
    print("--- Registered Routes ---")
    for rule in app.url_map.iter_rules():
        # methodsにはGET, POSTなどが、ruleにはURLのパスが入っている
        print(f"Endpoint: {rule.endpoint}, Methods: {rule.methods}, URL: {rule}")
    print("-------------------------")
    # ★★★ ここまで追加 ★★★
    app.run(debug=True, port=5000)