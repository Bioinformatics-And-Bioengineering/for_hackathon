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
    </Box>
  );
}

export default GeneralCreditForm;
