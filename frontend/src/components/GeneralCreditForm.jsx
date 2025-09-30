import React from "react";
import { TextField, Paper, Typography } from "@mui/material";

function GeneralCreditForm() {
  return (
    <Paper
      elevation={3}
      style={{ padding: "20px", margin: "20px", width: "80%" }}
    >
      <Typography variant="h5" gutterBottom>
        教養科目（〇〇単位以上必須）
      </Typography>
      <TextField
        label="人文科学単位"
        type="number"
        variant="outlined"
        fullWidth
        style={{ marginBottom: "15px" }}
      />
      {/* 他の教養科目の入力欄をここに追加 */}
    </Paper>
  );
}

export default GeneralCreditForm;
