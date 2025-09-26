from flask import Flask, jsonify
from flask_cors import CORS # 👈 CORS対応のために必要

app = Flask(__name__)
# 開発環境でReactからのアクセスを許可するためにCORSを設定
# 本番環境ではより厳格な設定が必要です
CORS(app) 

@app.route('/api/message')
def get_message():
    """
    メッセージをJSON形式で返すAPIエンドポイント
    """
    # 実際にはここでデータベースからのデータ取得などの処理が行われます
    data = {
        "message": "Hello World!",
        "status": "success"
    }
    return jsonify(data)

if __name__ == '__main__':
    # 開発サーバーをポート5000で起動 (Reactは通常3000で動くため)
    app.run(debug=True, port=5000)