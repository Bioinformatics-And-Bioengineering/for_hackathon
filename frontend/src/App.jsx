// src/App.jsx (または src/App.js) の内容を以下に上書き
import React from 'react'
import Home from './pages/Home'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import Header from './components/Header'
// import './App.css'; // スタイルを気にしないならコメントアウトしてもOK

function App() {
  return (
    <BrowserRouter>
      <Header />
      <Routes>
        <Route path='/' element={<Home />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
