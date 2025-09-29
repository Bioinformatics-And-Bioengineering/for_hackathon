// src/App.jsx (または src/App.js) の内容を以下に上書き
import MultipleSelectChip from "./components/selectBottun";
import React, { useState, useEffect } from "react";
import Box from "@mui/material/Box";
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
      <Box
        sx={{
          display: "flex", // Flexboxを有効化
          flexDirection: "column", // 子要素を縦方向に並べる
          alignItems: "center", // 水平方向（クロス軸）に中央寄せ
          // 画面全体で中央に配置したい場合は以下のスタイルも検討
          // minHeight: '100vh',
          // justifyContent: 'center', // 垂直方向（主軸）に中央寄せ
          width: "100%", // 必要に応じて幅を設定
        }} //あ
      >
        <header className="App-header">
          <h1>kagoshima-univercity 成績要件確認</h1>
          <p>
            Flaskからのメッセージ: <strong>{message}</strong>
          </p>
        </header>
        <h3>学部</h3>
        <MultipleSelectChip></MultipleSelectChip>
        <h3>学科</h3>
        <MultipleSelectChip></MultipleSelectChip>
      </Box>
    </div>
  );
}

export default App;
