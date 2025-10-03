import React from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import CreditEntryPage from "./CreditEntryPage";
// ページコンポーネントをインポート
import SelectionPage from "./selectionPage";

import ResultsPage from "./ResultsPage"; //kohe

function App() {
  return (
    // ★★★ これがルーターコンポーネントです
    <BrowserRouter>
      <Routes>
        {/* SelectionPage は BrowserRouter の子としてレンダリングされる */}
        <Route path="/" element={<SelectionPage />} />
        <Route path="/credit-entry" element={<CreditEntryPage />} />
        <Route path="/results" element={<ResultsPage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
