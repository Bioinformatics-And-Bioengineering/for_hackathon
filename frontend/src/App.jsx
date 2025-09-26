// src/App.jsx (または src/App.js) の内容を以下に上書き

import React, { useState, useEffect } from 'react';
// import './App.css'; // スタイルを気にしないならコメントアウトしてもOK


import { useTheme } from '@mui/material/styles';
import Box from '@mui/material/Box';
import OutlinedInput from '@mui/material/OutlinedInput';
import InputLabel from '@mui/material/InputLabel';
import MenuItem from '@mui/material/MenuItem';
import FormControl from '@mui/material/FormControl';
import Select from '@mui/material/Select';
import Chip from '@mui/material/Chip';

function App() {
  // Flaskから受け取るメッセージを保持するためのステート
  const [message, setMessage] = useState('Loading...');

  const ITEM_HEIGHT = 48;
const ITEM_PADDING_TOP = 8;
const MenuProps = {
  PaperProps: {
    style: {
      maxHeight: ITEM_HEIGHT * 4.5 + ITEM_PADDING_TOP,
      width: 250,
    },
  },
};
const names = [
  'Oliver Hansen',
  'Van Henry',
  'April Tucker',
  'Ralph Hubbard',
  'Omar Alexander',
  'Carlos Abbott',
  'Miriam Wagner',
  'Bradley Wilkerson',
  'Virginia Andrews',
  'Kelly Snyder',
];

function getStyles(name, personName, theme) {
  return {
    fontWeight: personName.includes(name)
      ? theme.typography.fontWeightMedium
      : theme.typography.fontWeightRegular,
  };
}

  const theme = useTheme();
  const [personName, setPersonName] = React.useState([]);

  const handleChange = (event) => {
    const {
      target: { value },
    } = event;
    setPersonName(
      // On autofill we get a stringified value.
      typeof value === 'string' ? value.split(',') : value,
    );
  };






  // コンポーネントがマウントされた後に一度だけAPIを呼び出す
  useEffect(() => {
    // ⚠️ FlaskサーバーのURLとポート番号を指定 (通常5000)
    fetch('http://localhost:5000/api/message') 
      .then(response => {
        if (!response.ok) {
          throw new Error('Network response was not ok');
        }
        return response.json(); // JSON形式でレスポンスを解析
      })
      .then(data => {
        // 取得したデータからmessageフィールドをステートにセット
        setMessage(data.message);
      })
      .catch(error => {
        console.error("Fetch error: ", error);
        setMessage('Failed to connect to Flask API.');
      });
  }, []); // 初回レンダリング時のみ実行

  return (
    <div className="App">
      <header className="App-header">
        <h1>Flask & React 連携サンプル</h1>
        <p>
          Flaskからのメッセージ: <strong>{message}</strong>
        </p>
      </header>
<div>
      <FormControl sx={{ m: 1, width: 300 }}>
        <InputLabel id="demo-multiple-chip-label">Chip</InputLabel>
        <Select
          labelId="demo-multiple-chip-label"
          id="demo-multiple-chip"
          multiple
          value={personName}
          onChange={handleChange}
          input={<OutlinedInput id="select-multiple-chip" label="Chip" />}
          renderValue={(selected) => (
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
              {selected.map((value) => (
                <Chip key={value} label={value} />
              ))}
            </Box>
          )}
          MenuProps={MenuProps}
        >
          {names.map((name) => (
            <MenuItem
              key={name}
              value={name}
              style={getStyles(name, personName, theme)}
            >
              {name}
            </MenuItem>
          ))}
        </Select>
      </FormControl>
    </div>
    </div>
  );
}

export default App;