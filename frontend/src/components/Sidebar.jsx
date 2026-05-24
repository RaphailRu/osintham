import React, { useEffect, useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import {
  Home, Network, FileText, Terminal, Settings, Search, Plus,
  ChevronLeft, ChevronRight, Bug, Zap, Star, Trash2, Clock,
  ChevronDown, ChevronRight as ChevronRightIcon
} from 'lucide-react'
import useStore from '../store'
import { getInvestigations, deleteInvestigation } from '../api'

const MAIN_NAV = [
  { id: 'dashboard', icon: Home, label: 'Главная', path: '/' },
]

const INVESTIGATION_NAV = [
  { id: 'graph', icon: Network, label: 'Граф', path: '' },
  { id: 'reports', icon: FileText, label: 'Отчёты', path: '/reports' },
  { id: 'terminal', icon: Terminal, label: 'Терминал', path: '/terminal' },
]

export default function Sidebar({ onNewInvestigation }) {
  const location = useLocation()
  const navigate = useNavigate()
  const {
    sidebarOpen, setSidebarOpen, investigations, setInvestigations,
    currentInvestigation, setCurrentInvestigation, theme, toggleTheme,
    favorites, addFavorite, removeFavorite
  } = useStore()

  const [search, setSearch] = useState('')
  const [expandedGroups, setExpandedGroups] = useState({ investigations: true })

  useEffect(() => {
    loadInvestigations()
  }, [])

  const loadInvestigations = async () => {
    try {
      const res = await getInvestigations()
      setInvestigations(res.data)
    } catch (err) {
      // Fallback to empty list if API not available
      console.log('API not available, using local data')
    }
  }

  const handleDelete = async (id, title, e) => {
    e.preventDefault()
    e.stopPropagation()
    if (!confirm(`Delete "${title}"?`)) return
    try {
      await deleteInvestigation(id)
      await loadInvestigations()
      if (currentInvestigation?.id === id) {
        navigate('/')
      }
    } catch (err) {
      console.error('Error deleting:', err)
    }
  }

  const toggleFavorite = (id, e) => {
    e.preventDefault()
    e.stopPropagation()
    const inv = investigations.find(i => i.id === id)
    if (inv) {
      const isFav = favorites.some(f => f.id === id)
      if (isFav) removeFavorite(id)
      else addFavorite(inv)
    }
  }

  const toggleGroup = (group) => {
    setExpandedGroups(prev => ({ ...prev, [group]: !prev[group] }))
  }

  const filtered = investigations.filter(inv =>
    inv.title.toLowerCase().includes(search.toLowerCase())
  )

  const isActive = (path) => {
    if (path === '/') return location.pathname === '/'
    return location.pathname.startsWith(path)
  }

  const currentInvId = currentInvestigation?.id

  return (
    <aside className={`fixed left-0 top-0 h-full bg-[#1e293b] border-r border-[#334155] z-40 transition-all duration-300 flex flex-col ${
      sidebarOpen ? 'w-72' : 'w-0 overflow-hidden'
    }`}>

      {/* Header */}
      <div className="p-4 border-b border-[#334155] flex-shrink-0">
        <div className="flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2 text-lg font-bold text-white hover:text-[#818cf8] transition-colors">
            <Bug className="w-6 h-6 text-[#6366f1]" />
            <span>OsintHAM</span>
          </Link>
          <div className="flex items-center gap-1">
            <button
              onClick={toggleTheme}
              className="p-1.5 rounded-lg hover:bg-[#334155] text-[#94a3b8] hover:text-white transition-colors"
              title="Toggle theme"
            >
              {theme === 'dark' ? '☀️' : '🌙'}
            </button>
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="p-1.5 rounded-lg hover:bg-[#334155] text-[#94a3b8] hover:text-white transition-colors"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Search */}
      <div className="p-3 border-b border-[#334155] flex-shrink-0">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#64748b]" />
          <input
            type="text"
            placeholder="Search..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="w-full pl-9 pr-3 py-2 bg-[#0f172a] border border-[#334155] rounded-lg text-sm text-white placeholder-[#64748b] focus:outline-none focus:border-[#6366f1]"
          />
        </div>
      </div>

      {/* Navigation */}
      <div className="flex-1 overflow-y-auto">
        {/* Main nav */}
        <div className="p-2">
          {MAIN_NAV.map(item => (
            <Link
              key={item.id}
              to={item.path}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                isActive(item.path)
                  ? 'bg-[#6366f1] text-white'
                  : 'text-[#94a3b8] hover:text-white hover:bg-[#334155]'
              }`}
            >
              <item.icon className="w-4 h-4" />
              {item.label}
            </Link>
          ))}
        </div>

        {/* Investigation pages nav */}
        {currentInvId && (
          <div className="px-2 pb-2">
            <div className="border-t border-[#334155] pt-2">
              <div className="px-3 py-1 text-xs font-semibold text-[#64748b] uppercase tracking-wider">
                Investigation
              </div>
              {INVESTIGATION_NAV.map(item => {
                const fullPath = `/investigation/${currentInvId}${item.path}`
                return (
                  <Link
                    key={item.id}
                    to={fullPath}
                    className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                      isActive(fullPath)
                        ? 'bg-[#6366f1] text-white'
                        : 'text-[#94a3b8] hover:text-white hover:bg-[#334155]'
                    }`}
                  >
                    <item.icon className="w-4 h-4" />
                    {item.label}
                  </Link>
                )
              })}
            </div>
          </div>
        )}

        {/* Investigations list */}
        <div className="px-2 pb-2">
          <button
            onClick={() => toggleGroup('investigations')}
            className="w-full flex items-center justify-between px-3 py-1 text-xs font-semibold text-[#64748b] uppercase tracking-wider hover:text-[#94a3b8] transition-colors"
          >
            <span>Investigations ({investigations.length})</span>
            {expandedGroups.investigations ? <ChevronDown className="w-3 h-3" /> : <ChevronRightIcon className="w-3 h-3" />}
          </button>

          {expandedGroups.investigations && (
            <div className="mt-1 space-y-0.5">
              {filtered.length === 0 ? (
                <div className="text-center py-4 text-[#64748b] text-xs">
                  {search ? 'No matches' : 'No investigations'}
                </div>
              ) : (
                filtered.map(inv => {
                  const isActiveInv = currentInvId === inv.id
                  return (
                    <div key={inv.id} className="group relative">
                      <Link
                        to={`/investigation/${inv.id}`}
                        onClick={() => setCurrentInvestigation(inv)}
                        className={`block p-2.5 rounded-lg transition-colors ${
                          isActiveInv
                            ? 'bg-[#6366f1]/20 border border-[#6366f1]/30'
                            : 'hover:bg-[#334155]'
                        }`}
                      >
                        <div className="flex items-center gap-2">
                          <div className={`w-2 h-2 rounded-full flex-shrink-0 ${
                            inv.status === 'active' ? 'bg-green-400' :
                            inv.status === 'paused' ? 'bg-yellow-400' : 'bg-gray-400'
                          }`} />
                          <span className="text-sm text-white truncate flex-1">{inv.title}</span>
                          <div className="flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity">
                            <button
                              onClick={(e) => toggleFavorite(inv.id, e)}
                              className="p-1 rounded hover:bg-white/10"
                              title="Избранное"
                            >
                              <Star className={`w-3 h-3 ${favorites.some(f => f.id === inv.id) ? 'fill-yellow-400 text-yellow-400' : 'text-[#64748b]'}`} />
                            </button>
                            <button
                              onClick={(e) => handleDelete(inv.id, inv.title, e)}
                              className="p-1 rounded hover:bg-red-500/20"
                              title="Удалить"
                            >
                              <Trash2 className="w-3 h-3 text-[#64748b] hover:text-red-400" />
                            </button>
                          </div>
                        </div>
                        <div className="flex items-center gap-2 mt-1 text-xs text-[#64748b]">
                          <span>{inv.node_count || 0} узлов</span>
                          <span>•</span>
                          <Clock className="w-3 h-3" />
                          <span>{new Date(inv.updated_at || Date.now()).toLocaleDateString()}</span>
                        </div>
                      </Link>
                    </div>
                  )
                })
              )}
            </div>
          )}
        </div>
      </div>

      {/* Footer */}
      <div className="p-3 border-t border-[#334155] flex-shrink-0">
        <button
          onClick={onNewInvestigation}
          className="w-full flex items-center justify-center gap-2 px-3 py-2.5 bg-[#6366f1] hover:bg-[#818cf8] text-white rounded-lg text-sm font-medium transition-colors"
        >
          <Plus className="w-4 h-4" />
          Новое расследование
        </button>
        <div className="flex items-center justify-between mt-2 text-xs text-[#64748b]">
          <span>OsintHAM v0.5.1</span>
          <span>{favorites.length} ⭐</span>
        </div>
      </div>
    </aside>
  )
}
