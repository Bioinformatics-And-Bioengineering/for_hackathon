import Box from '@mui/material/Box'
import React from 'react'

function Header() {
  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column', // 縦並び
        justifyContent: 'center', // 縦方向の中央
        alignItems: 'center', // 横方向の中央
        textAlign: 'center',
        minHeight: '100px',
        backgroundColor: '#24517fff',
        color: '#9d9898ff',
      }}
    >
      <h1>Flask & React 連携サンプル</h1>
    </Box>
  )
}

export default Header
