import React, { useEffect, useState } from 'react'
import { Link, useParams, useNavigate } from 'react-router-dom'
import {
  Network, FileText, Terminal, ChevronLeft, ChevronRight,
  Plus, Search, Settings, Bug
} from 'lucide-react'
import useStore from '../store'
import { getInvestigations } from '../api'

const NAV_ITEMS = [
  { id: 'graph', icon: Network, label: 'Graph', path: '' },
  { id: 'reports', icon: FileText, label: 'Reports', path: '/reports' },
  { id: 'terminal', icon: Terminal, label: 'Terminal', path: '/terminal' },
]

export default function Sidebar() {
  const { id } = useParams()
  const navigate = useNavigate()
  const {
    sidebarOpen, setSidebarOpen, investigations, setInvestigations,
    currentInvestigation, activeTab, setActiveTab
  } = useStore()
  const [search, setSearch] = useState('')

  useEffect(() => {
    getInvestigations().then(res => setInvestigations(res.data))
  }, [])

  const filtered = investigations.filter(inv =>
    inv.title.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <aside className={`fixed left-0 top-0 h-full bg-[#1e293b] border-r border-[#334155] z-50 transition-all duration-300 flex flex-col ${sidebarOpen ? 'w-64' : 'w-0 overflow-hidden'}`}>
      {/* Header */}
      <div className="p-4 border-b border-[#334155]">
        <div className="flex items-center justify-between mb-3">
          <Link to="/" className="flex items-center gap-2 text-lg font-bold text-white hover:text-[#818cf8]">
            <Bug className="w-6 h-6 text-[#6366f1]" />
            <span>OsintHAM</span>
          </Link>
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="p-1 rounded hover:bg-[#334155] text-[#94a3b8]"
          >
            {sidebarOpen ? <ChevronLeft className="w-5 h-5" /> : <ChevronRight className="w-5 h-5" />}
          </button>
        </div>

        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#64748b]" />
          <input
            type="text"
            placeholder="Search investigations..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="w-full pl-9 pr-3 py-2 bg-[#0f172a] border border-[#334155] rounded-lg text-sm text-white placeholder-[#64748b] focus:outline-none focus:border-[#6366f1]"
          />
        </div>
      </div>

      {/* Navigation (when in investigation) */}
      {id && (
        <div className="flex border-b border-[#334155]">
          {NAV_ITEMS.map(item => (
            <button
              key={item.id}
              onClick={() => {
                setActiveTab(item.id)
                navigate(`/investigation/${id}${item.path}`)
              }}
              className={`flex-1 flex flex-col items-center gap-1 py-3 text-xs transition-colors ${
                activeTab === item.id
                  ? 'text-[#6366f1] border-b-2 border-[#6366f1]'
                  : 'text-[#94a3b8] hover:text-white'
              }`}
            >
              <item.icon className="w-4 h-4" />
              {item.label}
            </button>
          ))}
        </div>
      )}

      {/* Investigation List */}
      <div className="flex-1 overflow-y-auto p-2">
        <div className="flex items-center justify-between px-2 py-2">
          <span className="text-xs font-semibold text-[#64748b] uppercase tracking-wider">
            Investigations
          </span>
          <Link
            to="/"
            className="p-1 rounded hover:bg-[#334155] text-[#64748b] hover:text-[#6366f1]"
            title="New Investigation"
          >
            <Plus className="w-4 h-4" />
          </Link>
        </div>

        {filtered.length === 0 ? (
          <div className="text-center py-8 text-[#64748b] text-sm">
            {search ? 'No matches found' : 'No investigations yet'}
          </div>
        ) : (
          filtered.map(inv => (
            <Link
              key={inv.id}
              to={`/investigation/${inv.id}`}
              className={`block p-3 rounded-lg mb-1 transition-colors ${
                id === inv.id
                  ? 'bg-[#6366f1] text-white'
                  : 'hover:bg-[#334155] text-[#94a3b8] hover:text-white'
              }`}
            >
              <div className="font-medium text-sm truncate">{inv.title}</div>
              <div className="flex items-center gap-2 mt-1 text-xs opacity-70">
                <span>{inv.node_count} nodes</span>
                <span>•</span>
                <span className={`px-1.5 py-0.5 rounded text-[10px] ${
                  inv.status === 'active' ? 'bg-green-500/20 text-green-400' :
                  inv.status === 'paused' ? 'bg-yellow-500/20 text-yellow-400' :
                  'bg-gray-500/20 text-gray-400'
                }`}>
                  {inv.status}
                </span>
              </div>
            </Link>
          ))
        )}
      </div>

      {/* Footer */}
      <div className="p-3 border-t border-[#334155]">
        <div className="flex items-center gap-2 text-xs text-[#64748b]">
          <Settings className="w-3 h-3" />
          <span>OsintHAM v0.1.0</span>
        </div>
      </div>
    </aside>
  )
}
