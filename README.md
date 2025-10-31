# プロジェクト起動手順

## バックエンド起動（Flask）

1. Python をインストール
2. バックエンドのディレクトリに移動

   ```bash
   cd backend
   ```

3. （任意）仮想環境を作成して有効化

   Python の仮想環境を使うと、プロジェクトごとに依存パッケージを分離できます。
   すでにグローバル環境を使う場合はこの手順はスキップして構いません。

   **Windows:**

   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

   **Mac / Linux / WSL:**

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

4. パッケージをインストール

   ```bash
   pip install -r requirements.txt
   ```

5. Flask アプリを起動

   ```bash
   python app.py
   ```

6. ブラウザで確認

   ```
   http://localhost:5000/
   ```

   Swagger UI（Flasgger 導入済みの場合）は以下で確認できます。

   ```
   http://localhost:5000/apidocs
   ```

## フロントエンド起動

1. フロントエンドに移動
2. npm をインストール
   `npm install`
3. 実行する
   `npm start`
