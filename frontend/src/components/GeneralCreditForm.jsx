import React from "react";
import { useState } from "react";
import { TextField, Paper, Typography, MenuItem } from "@mui/material";

function GeneralCreditForm() {
  const [grade, setGrade] = useState("");

  const grades = [
    { value: "A", label: "A" },
    { value: "B", label: "B" },
    { value: "C", label: "C" },
    { value: "D", label: "D" },
    { value: "F", label: "F" },
    { value: "P", label: "P" },
  ];
  const handleChange = (e) => {
    setGrade(e.target.value);
  };
  return (
    <Paper
      elevation={3}
      style={{ padding: "20px", margin: "20px", width: "30%" }}
    >
      <Typography variant="h5" gutterBottom>
        講義名
      </Typography>
      <TextField
        select
        label="評定"
        value={grade}
        variant="outlined"
        fullWidth
        style={{ marginBottom: "15px" }}
        onChange={handleChange}
      >
        {grades.map((option) => (
          <MenuItem key={option.value} value={option.value}>
            {option.label}
          </MenuItem>
        ))}
      </TextField>
      {/* 他の教養科目の入力欄をここに追加 */}
    </Paper>
  );
}

export default GeneralCreditForm;
