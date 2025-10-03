import React, { useMemo, useState } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import {
  Container,
  Box,
  Paper,
  Typography,
  Divider,
  Chip,
  Button,
} from "@mui/material";

export default function ResultsPage() {
  const [sp] = useSearchParams();
  const navigate = useNavigate();

  // ① ?gpa=3.21 があれば優先、② localStorage("gpa")、③ それもなければ null
  const initial = useMemo(() => {
    const q = sp.get("gpa");
    if (q !== null && q !== "") return q;
    const saved = localStorage.getItem("gpa");
    return saved ?? null;
  }, [sp]);

  const [gpa, setGpa] = useState(initial);

  // 表示用の丸め（数値でなければ null 扱い）
  const gpaDisp = useMemo(() => {
    const n = Number(gpa);
    return Number.isFinite(n) ? n.toFixed(2) : null;
  }, [gpa]);

  // 評価バッジの色
  const chipColor = useMemo(() => {
    if (gpaDisp === null) return "default";
    const n = Number(gpaDisp);
    if (n >= 3.0) return "success";
    if (n >= 2.0) return "warning";
    return "error";
  }, [gpaDisp]);

  return (
    <Container maxWidth="sm">
      <Box sx={{ py: 4, display: "flex", flexDirection: "column", gap: 2 }}>
        <Typography variant="h5" align="center">
          結果
        </Typography>

        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            GPA
          </Typography>
          <Divider sx={{ mb: 2 }} />
          <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
            <Typography variant="h3" component="div">
              {gpaDisp ?? "—"}
            </Typography>
            <Chip
              label={gpaDisp ? `評価: ${gpaDisp}` : "未計算"}
              color={chipColor}
              variant={gpaDisp ? "filled" : "outlined"}
            />
          </Box>

          {!gpaDisp && (
            <Typography variant="body2" sx={{ mt: 2 }} color="text.secondary">
              まだGPAが渡されていません。動作確認は
              <code> /results?gpa=3.21 </code>
              にアクセスするか、下のボタンを押してください。
            </Typography>
          )}

          <Box sx={{ mt: 3, display: "flex", gap: 1 }}>
            <Button variant="outlined" onClick={() => navigate(-1)}>
              戻る
            </Button>
            <Button
              variant="contained"
              onClick={() => {
                const demo = "3.21";
                localStorage.setItem("gpa", demo);
                setGpa(demo); // リロードなしで反映
              }}
            >
              デモ用に 3.21 を保存
            </Button>
          </Box>
        </Paper>
      </Box>
    </Container>
  );
}
