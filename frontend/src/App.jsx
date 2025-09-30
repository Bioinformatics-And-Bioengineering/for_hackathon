import React from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";

// ページコンポーネントをインポート
import SelectionPage from "./selectionPage";

function App() {
  return (
    // ★★★ これがルーターコンポーネントです
    <BrowserRouter>
      <Routes>
        {/* SelectionPage は BrowserRouter の子としてレンダリングされる */}
        <Route path="/" element={<SelectionPage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
