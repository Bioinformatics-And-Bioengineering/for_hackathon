import Box from '@mui/material/Box'
import MultipleSelectChip from '../../components/selectBottun'
import React, { useEffect, useState } from 'react'
// import './App.css'; // スタイルを気にしないならコメントアウトしてもOK

function Home() {
  // Flaskから受け取るメッセージを保持するためのステート
  const [message, setMessage] = useState('Loading...')

  // コンポーネントがマウントされた後に一度だけAPIを呼び出す
  useEffect(() => {
    // ⚠️ FlaskサーバーのURLとポート番号を指定 (通常5000)
    fetch('http://localhost:5000/api/message')
      .then((response) => {
        if (!response.ok) {
          throw new Error('Network response was not ok')
        }
        return response.json() // JSON形式でレスポンスを解析
      })
      .then((data) => {
        // 取得したデータからmessageフィールドをステートにセット
        setMessage(data.message)
      })
      .catch((error) => {
        console.error('Fetch error: ', error)
        setMessage('Failed to connect to Flask API.')
      })
  }, []) // 初回レンダリング時のみ実行

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column', // 縦並び
        justifyContent: 'center', // 縦方向の中央
        alignItems: 'center', // 横方向の中央
        textAlign: 'center',
      }}
    >
      <p>
        Flaskからのメッセージ: <strong>{message}</strong>
      </p>
      <MultipleSelectChip />
    </Box>
  )
}

export default Home
