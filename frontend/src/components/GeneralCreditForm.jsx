import React from "react";
import { useState, useEffect } from "react";
import { TextField, Paper, Typography, MenuItem } from "@mui/material";
import { Box } from "@mui/material";

function GeneralCreditForm({ subjectNames }) {
  const [inputGrades, setInputGrades] = useState({});

  const grades = [
    { value: "A", label: "A" },
    { value: "B", label: "B" },
    { value: "C", label: "C" },
    { value: "D", label: "D" },
    { value: "F", label: "F" },
    { value: "P", label: "P" },
  ];
  const handleChange = (subjectName, e) => {
    const newValue = e.target.value;
    setInputGrades((prevGrades) => ({
      ...prevGrades,
      [subjectName]: newValue, // 変更された科目名 (キー) の値を更新
    }));
  };
  // GeneralCreditForm.js (handleSubmit部分のみ)

  // ... (useState, useEffect, handleChange の定義は省略) ...

  // フォーム送信時の処理
  const handleSubmit = async (event) => {
    event.preventDefault(); // 👈 これでページのリロードを防ぎます

    // 1. 送信するデータ（科目名と評定のオブジェクト）
    const submissionData = inputGrades;

    // 2. Flaskでデータを受け取るエンドポイント
    const url = "http://localhost:5000/api/save-credits";

    try {
      const response = await fetch(url, {
        method: "POST", // 👈 POSTメソッドを指定

        // 3. ヘッダー: 送信するデータがJSONであることをサーバーに伝えます
        headers: {
          "Content-Type": "application/json",
        },

        // 4. ボディ: JavaScriptオブジェクトをJSON文字列に変換して格納
        body: JSON.stringify(submissionData),
      });

      // 5. ネットワークエラーチェック
      if (!response.ok) {
        // 例: 404, 500などのHTTPエラーの場合
        throw new Error(
          `データの送信に失敗しました。ステータスコード: ${response.status}`
        );
      }

      const result = await response.json();

      // 6. 成功時の処理 (サーバーからの応答を表示)
      console.log("サーバーからの応答:", result);
      alert(`データを登録しました！ サーバーメッセージ: ${result.message}`);
    } catch (error) {
      // 7. 失敗時の処理 (CORSエラーやネットワーク接続エラーなど)
      console.error("送信エラー:", error);
      alert(`データの送信中にエラーが発生しました。\n詳細: ${error.message}`);
    }
  };

  // ... (省略: return文内の <Box component="form" onSubmit={handleSubmit}> ... )

  useEffect(() => {
    if (Array.isArray(subjectNames)) {
      const initialGrades = subjectNames.reduce((acc, name) => {
        // 既存の値を保持するか、新規科目には空文字列を設定
        acc[name] = inputGrades[name] || "";
        return acc;
      }, {});
      setInputGrades(initialGrades);
    }
  }, [subjectNames]); // subjectNames が変更されたときに実行
  return (
    <Box sx={{ width: "100%", maxWidth: 800, mt: 3 }}>
      {/* 科目名の配列を map で回して、科目数分だけフォーム（Paper）を生成 */}
      {subjectNames.map((subjectName) => (
        <Paper
          key={subjectName} // ★★★ key は subjectName で一意に設定 ★★★
          elevation={3}
          style={{ padding: "20px", margin: "20px 0", width: "100%" }}
        >
          {/* 科目名を動的に表示 */}
          <Typography variant="h5" gutterBottom>
            {subjectName}
          </Typography>

          <TextField
            select
            label="評定"
            // この科目の現在の評定を State から取得
            value={inputGrades[subjectName] || ""}
            variant="outlined"
            fullWidth
            style={{ marginBottom: "15px" }}
            // どの科目の値が変更されたかを引数に渡す
            onChange={(e) => handleChange(subjectName, e)}
          >
            {grades.map((option) => (
              <MenuItem key={option.value} value={option.value}>
                {option.label}
              </MenuItem>
            ))}
          </TextField>
        </Paper>
      ))}

      {/* デバッグ用 */}
      <Paper elevation={1} sx={{ mt: 4, p: 2, bgcolor: "#f4f4f4" }}>
        <Typography variant="subtitle1">現在のフォームState:</Typography>
        <pre style={{ textAlign: "left" }}>
          {JSON.stringify(inputGrades, null, 2)}
        </pre>
      </Paper>
      <button
        onClick={handleSubmit}
        style={{ width: "150px", height: "60px", fontSize: "18px" }}
      >
        確定
      </button>
    </Box>
  );
}

export default GeneralCreditForm;
