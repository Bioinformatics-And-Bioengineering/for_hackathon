import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom"; // ★ useNavigate をインポート
import Box from "@mui/material/Box"; // ★ Box をインポート
import NativeSelectDemo from "./components/selectBottun"; // パスはあなたの環境に合わせて調整
import BasicButtons from "./components/button";
// 補完されたデータ定義
const facultyOptions = [
  { value: "default", label: "" },
  { value: "engi", label: "工学部" },
  { value: "edu", label: "教育学部" },
  { value: "sci", label: "理学部" },
];

const departmentOptions = [
  { value: "default", label: "" },
  { value: "info", label: "情報生体工学プログラム" },
  { value: "machine", label: "機械工学プログラム" },
  { value: "electric", label: "電気電子工学プログラム" },
  { value: "chem", label: "化学工学プログラム" },
];

function SelectionPage() {
  const navigate = useNavigate();
  const [message, setMessage] = useState("Loading...");
  const [selectedFaculty, setSelectedFaculty] = useState("");
  const [selectedDepartment, setSelectedDepartment] = useState("");

  const handlePageMove = () => {
    if (selectedFaculty && selectedDepartment) {
      navigate(
        `/credit-entry?faculty=${selectedFaculty}&dept=${selectedDepartment}`
      );
    } else {
      alert("学部と学科を選択してください。");
    }
  };

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
    <div className="SelectionPage">
      {/* 補完された Box とスタイル */}
      <Box
        sx={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          width: "100%",
          padding: 3, // 見やすさのために追加
        }}
      >
        <header>
          <h1>卒業要件確認サイト (学部選択)</h1>
          <p>
            Flaskからのメッセージ: <strong>{message}</strong>
          </p>
        </header>

        {/* 学部選択 (options, labelText, idProp, onChangeを補完) */}
        <h3>学部</h3>
        <NativeSelectDemo
          options={facultyOptions} // ★ 補完
          labelText="学部を選択" // ★ 補完
          idProp="select-faculty" // ★ 補完
          onChange={(e) => setSelectedFaculty(e.target.value)}
        />

        {/* 学科選択 (options, labelText, idProp, onChangeを補完) */}
        <h3>学科</h3>
        <NativeSelectDemo
          options={departmentOptions} // ★ 補完
          labelText="学科を選択" // ★ 補完
          idProp="select-department" // ★ 補完
          onChange={(e) => setSelectedDepartment(e.target.value)}
        />

        <br></br>
        <br></br>

        <BasicButtons onClick={handlePageMove}></BasicButtons>
      </Box>
    </div>
  );
}

export default SelectionPage;
