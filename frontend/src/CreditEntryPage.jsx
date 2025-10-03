import GeneralCreditForm from "./components/GeneralCreditForm"; // 👈 インポート
//import { useSearchParams } from "react-router-dom";
import { Box, CircularProgress, Typography } from "@mui/material";
import { useState, useEffect } from "react";

//kohe
import { useSearchParams, useNavigate } from "react-router-dom";
import BasicButtons from "./components/button";

function CreditEntryPage() {
  const navigate = useNavigate();
  // ... (useSearchParamsなどのロジックはそのまま)
  const [searchParams] = useSearchParams();

  // 💡 修正: URLから学部と学科の情報を取得し、変数として定義
  const faculty = searchParams.get("faculty");
  const dept = searchParams.get("dept");
  const [subjectNames, setSubjectNames] = useState(null); // 初期値を null に変更 (ロード中を表す)

  // 補完された useEffect (Flask API呼び出し)
  useEffect(() => {
    fetch("http://localhost:5000/api/subjects")
      .then((response) => {
        if (!response.ok) {
          throw new Error("Network response was not ok");
        }
        return response.json();
      })
      .then((data) => {
        setSubjectNames(data.subjects);
      })
      .catch((error) => {
        console.error("Fetch error: ", error);
        setSubjectNames("Failed to connect to Flask API.");
      });
  }, []);
  // ロード中またはエラー表示
  if (subjectNames === null) {
    return (
      <Box sx={{ display: "flex", justifyContent: "center", p: 5 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (typeof subjectNames === "string") {
    return (
      <Box sx={{ textAlign: "center", p: 5 }}>
        <Typography color="error">エラー: {subjectNames}</Typography>
      </Box>
    );
  }
  const handleGoResults = () => {
    const g = localStorage.getItem("gpa");
    const params = new URLSearchParams();
    if (faculty) params.set("faculty", faculty);
    if (dept) params.set("dept", dept);
    if (g) params.set("gpa", g);
    navigate(`/results${params.toString() ? `?${params}` : ""}`);
  };

  return (
    <div style={{ padding: "20px", textAlign: "center" }}>
      <Box
        sx={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          width: "100%",
          padding: 3, // 見やすさのために追加
        }}
      >
        <h2>単位入力フォーム</h2>
        <p>
          選択された学部: <strong>{faculty}</strong> / 学科:{" "}
          <strong>{dept}</strong>
        </p>

        {/* フォームコンポーネントを配置！ */}
        <GeneralCreditForm subjectNames={subjectNames} />
        {/* 他の専門科目フォームなどをここに追加 */}
        <BasicButtons onClick={handleGoResults} />
      </Box>
    </div>
  );
}

export default CreditEntryPage;
