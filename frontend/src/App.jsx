import React, { useState } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Sidebar from './components/Sidebar'
import Dashboard from './pages/Dashboard'
import Investigation from './pages/Investigation'
import Reports from './pages/Reports'
import TerminalPage from './pages/TerminalPage'
import useStore from './store'

function App() {
  const sidebarOpen = useStore(s => s.sidebarOpen)

  return (
    <BrowserRouter>
      <div className="flex h-screen overflow-hidden">
        <Sidebar />
        <main className={`flex-1 overflow-auto transition-all duration-300 ${sidebarOpen ? 'ml-64' : 'ml-0'}`}>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/investigation/:id" element={<Investigation />} />
            <Route path="/investigation/:id/reports" element={<Reports />} />
            <Route path="/investigation/:id/terminal" element={<TerminalPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}

export default App
