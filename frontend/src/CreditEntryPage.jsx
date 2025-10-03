import GeneralCreditForm from "./components/GeneralCreditForm"; // 👈 インポート
import { useSearchParams } from "react-router-dom";
import { Box } from "@mui/material";
import { useState, useEffect } from "react";

function CreditEntryPage() {
  // ... (useSearchParamsなどのロジックはそのまま)
  const [searchParams] = useSearchParams();

  // 💡 修正: URLから学部と学科の情報を取得し、変数として定義
  const faculty = searchParams.get("faculty");
  const dept = searchParams.get("dept");
  const [message, setMessage] = useState("Loading...");

  // 補完された useEffect (Flask API呼び出し)
  useEffect(() => {
    fetch("http://localhost:5000/api/message")
      .then((response) => {
        if (!response.ok) {
          throw new Error("Network response was not ok");
        }
        return response.json();
      })
      .then((data) => {
        setMessage(data.message);
      })
      .catch((error) => {
        console.error("Fetch error: ", error);
        setMessage("Failed to connect to Flask API.");
      });
  }, []);

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
        <p>
          Flaskからのメッセージ: <strong>{message}</strong>
        </p>
        <h2>単位入力フォーム</h2>
        <p>
          選択された学部: <strong>{faculty}</strong> / 学科:{" "}
          <strong>{dept}</strong>
        </p>

        {/* フォームコンポーネントを配置！ */}
        <GeneralCreditForm />

        {/* 他の専門科目フォームなどをここに追加 */}
      </Box>
    </div>
  );
}

export default CreditEntryPage;
