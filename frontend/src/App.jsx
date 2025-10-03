import React from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import CreditEntryPage from "./CreditEntryPage";

// ページコンポーネントをインポート
import SelectionPage from "./selectionPage";

function App() {
  return (
    // ★★★ これがルーターコンポーネントです
    <BrowserRouter>
      <Routes>
        {/* SelectionPage は BrowserRouter の子としてレンダリングされる */}
        <Route path="/" element={<SelectionPage />} />
        <Route path="/credit-entry" element={<CreditEntryPage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
