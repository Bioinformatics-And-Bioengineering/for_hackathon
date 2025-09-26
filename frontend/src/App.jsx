// src/App.jsx (または src/App.js) の内容を以下に上書き
import MultipleSelectChip from "./components/selectBottun";
import React, { useState, useEffect } from "react";
// import './App.css'; // スタイルを気にしないならコメントアウトしてもOK

function App() {
  // Flaskから受け取るメッセージを保持するためのステート
  const [message, setMessage] = useState("Loading...");

  // コンポーネントがマウントされた後に一度だけAPIを呼び出す
  useEffect(() => {
    // ⚠️ FlaskサーバーのURLとポート番号を指定 (通常5000)
    fetch("http://localhost:5000/api/message")
      .then((response) => {
        if (!response.ok) {
          throw new Error("Network response was not ok");
        }
        return response.json(); // JSON形式でレスポンスを解析
      })
      .then((data) => {
        // 取得したデータからmessageフィールドをステートにセット
        setMessage(data.message);
      })
      .catch((error) => {
        console.error("Fetch error: ", error);
        setMessage("Failed to connect to Flask API.");
      });
  }, []); // 初回レンダリング時のみ実行

  return (
    <div className="App">
      <header className="App-header">
        <h1>Flask & React 連携サンプル</h1>
        <p>
          Flaskからのメッセージ: <strong>{message}</strong>
        </p>
      </header>
      <MultipleSelectChip></MultipleSelectChip>
    </div>
  );
}

export default App;
