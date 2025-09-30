import GeneralCreditForm from "./components/GeneralCreditForm"; // 👈 インポート
import { useSearchParams } from "react-router-dom";

function CreditEntryPage() {
  // ... (useSearchParamsなどのロジックはそのまま)
  const [searchParams] = useSearchParams();

  // 💡 修正: URLから学部と学科の情報を取得し、変数として定義
  const faculty = searchParams.get("faculty");
  const dept = searchParams.get("dept");
  return (
    <div style={{ padding: "20px", textAlign: "center" }}>
      <h2>単位入力フォーム</h2>
      <p>
        選択された学部: <strong>{faculty}</strong> / 学科:{" "}
        <strong>{dept}</strong>
      </p>

      {/* フォームコンポーネントを配置！ */}
      <GeneralCreditForm />

      {/* 他の専門科目フォームなどをここに追加 */}
    </div>
  );
}

export default CreditEntryPage;
