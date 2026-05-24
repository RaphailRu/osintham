import React, { useState } from 'react'
import { HashRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom'
import Sidebar from './components/Sidebar'
import Dashboard from './pages/Dashboard'
import Investigation from './pages/Investigation'
import Reports from './pages/Reports'
import TerminalPage from './pages/TerminalPage'
import OsintFramework from './components/OsintFramework'
import SpiderFoot from './components/SpiderFoot'
import ToastContainer from './components/ToastContainer'
import ErrorBoundary from './components/ErrorBoundary'
import CreateInvestigationModal from './components/CreateInvestigationModal'
import useStore from './store'

function AppContent() {
  const location = useLocation()
  const sidebarOpen = useStore(s => s.sidebarOpen)
  const [showCreateModal, setShowCreateModal] = useState(false)

  const isInvestigationPage = location.pathname.includes('/investigation/')

  return (
    <div className="flex h-screen overflow-hidden bg-[#0f172a]">
      <Sidebar onNewInvestigation={() => setShowCreateModal(true)} />

      <main className={`flex-1 overflow-auto transition-all duration-300 ${sidebarOpen ? 'ml-72' : 'ml-0'}`}>
        {/* Top bar */}
        <div className="sticky top-0 z-30 flex items-center justify-between px-4 py-3 bg-[#1e293b]/95 backdrop-blur-sm border-b border-[#334155]">
          <div className="flex items-center gap-3">
            <button
              onClick={() => useStore.getState().setSidebarOpen(!sidebarOpen)}
              className="p-2 rounded-lg hover:bg-[#334155] text-[#94a3b8] hover:text-white transition-colors"
              title="Toggle sidebar"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
            <span className="text-sm text-[#94a3b8]">
              {isInvestigationPage ? useStore.getState().currentInvestigation?.title || 'Investigation' : 'Dashboard'}
            </span>
          </div>
          <div className="flex items-center gap-2">
            {isInvestigationPage && (
              <>
                <button
                  onClick={() => setShowCreateModal(true)}
                  className="flex items-center gap-1.5 px-3 py-1.5 bg-[#6366f1] hover:bg-[#818cf8] text-white rounded-lg text-sm transition-colors"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                  </svg>
                  New
                </button>
              </>
            )}
          </div>
        </div>

        {/* Page content */}
        <div className="h-[calc(100vh-57px)] overflow-auto">
          <Routes>
            <Route path="/" element={<Dashboard onNewInvestigation={() => setShowCreateModal(true)} />} />
            <Route path="/investigation/:id" element={<Investigation />} />
            <Route path="/investigation/:id/reports" element={<Reports />} />
            <Route path="/investigation/:id/terminal" element={<TerminalPage />} />
            <Route path="/framework" element={<OsintFramework />} />
            <Route path="/spiderfoot" element={<SpiderFoot />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </div>
      </main>

      {showCreateModal && (
        <CreateInvestigationModal
          onClose={() => setShowCreateModal(false)}
          onCreated={(inv) => {
            setShowCreateModal(false)
            window.location.href = `/investigation/${inv.id}`
          }}
        />
      )}

      <ToastContainer />
    </div>
  )
}

export default function App() {
  return (
    <ErrorBoundary>
      <HashRouter>
        <AppContent />
      </HashRouter>
    </ErrorBoundary>
  )
}
