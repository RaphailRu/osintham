import React, { useEffect, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import {
  Network, FileText, Settings, Search, Plus, Star, 
  ChevronLeft, ChevronRight, Home, Bug, Zap, 
  Download, Upload, Moon, Sun, User, Clock,
  FolderOpen, Trash2
} from 'lucide-react'
import useStore from '../store'
import { getInvestigations, createInvestigation, deleteInvestigation } from '../api'

const NAV_ITEMS = [
  { id: 'dashboard', icon: Home, label: 'Dashboard', path: '/' },
  { id: 'investigation', icon: Network, label: 'Investigation', path: '/investigation/:id', children: [
    { id: 'graph', icon: Network, label: 'Graph', path: '' },
    { id: 'scanner', icon: Zap, label: 'OSINT Scanner', path: '/scanner' },
    { id: 'tools', icon: Bug, label: 'Tools Catalog', path: '/tools' }
  ]},
  { id: 'reports', icon: FileText, label: 'Reports', path: '/investigation/:id/reports' },
  { id: 'settings', icon: Settings, label: 'Settings', path: '/investigation/:id/settings' }
]

export default function Sidebar() {
  const location = useLocation()
  const {
    sidebarOpen, setSidebarOpen, investigations, setInvestigations,
    currentInvestigation, activeTab, setActiveTab, theme, toggleTheme,
    favorites, addFavorite, removeFavorite, recentInvestigations,
    addRecentInvestigation, searchQuery, setSearchQuery
  } = useStore()
  
  const [search, setSearch] = useState('')
  const [showCreate, setShowCreate] = useState(false)
  const [newTitle, setNewTitle] = useState('')
  const [newDesc, setNewDesc] = useState('')

  useEffect(() => {
    loadInvestigations()
  }, [])

  useEffect(() => {
    setSearch(searchQuery)
  }, [searchQuery])

  const loadInvestigations = async () => {
    try {
      const res = await getInvestigations()
      setInvestigations(res.data)
    } catch (err) {
      console.error('Error loading investigations:', err)
    }
  }

  const handleCreate = async () => {
    if (!newTitle.trim()) return
    try {
      const res = await createInvestigation({ title: newTitle, description: newDesc })
      addRecentInvestigation(res.data)
      setNewTitle('')
      setNewDesc('')
      setShowCreate(false)
      await loadInvestigations()
    } catch (err) {
      console.error('Error creating investigation:', err)
    }
  }

  const handleDelete = async (id, title) => {
    if (!confirm(`Delete "${title}"? This cannot be undone.`)) return
    try {
      await deleteInvestigation(id)
      await loadInvestigations()
    } catch (err) {
      console.error('Error deleting investigation:', err)
    }
  }

  const toggleFavorite = (id) => {
    const inv = investigations.find(i => i.id === id)
    if (inv) {
      const isFavorite = favorites.some(f => f.id === id)
      if (isFavorite) {
        removeFavorite(id)
      } else {
        addFavorite(inv)
      }
    }
  }

  const filtered = investigations.filter(inv =>
    inv.title.toLowerCase().includes(search.toLowerCase())
  )

  const activePath = location.pathname
  const activeMainNav = NAV_ITEMS.find(item => 
    activePath.startsWith(item.path.replace(':id', currentInvestigation?.id || ''))
  )?.id || 'dashboard'

  const isInvestigationPath = activePath.includes('/investigation/')
  const currentInvestigationId = isInvestigationPath ? activePath.split('/')[2] : null

  return (
    <>
      {/* Mobile backdrop */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}
      
      {/* Sidebar */}
      <aside className={`fixed left-0 top-0 h-full bg-slate-900 border-r border-slate-700 z-50 transition-all duration-300 flex flex-col ${
        sidebarOpen ? 'w-72' : 'w-0 overflow-hidden'
      }`}>
        
        {/* Header */}
        <div className="p-4 border-b border-slate-700">
          <div className="flex items-center justify-between mb-4">
            <Link to="/" className="flex items-center gap-2 text-lg font-bold text-white hover:text-blue-400 transition-colors">
              <Bug className="w-6 h-6 text-blue-500" />
              <span>OsintHAM</span>
            </Link>
            <div className="flex items-center gap-2">
              <button
                onClick={toggleTheme}
                className="p-1.5 rounded hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
                title={theme === 'dark' ? 'Switch to light theme' : 'Switch to dark theme'}
              >
                {theme === 'dark' ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
              </button>
              <button
                onClick={() => setSidebarOpen(!sidebarOpen)}
                className="p-1.5 rounded hover:bg-slate-800 text-slate-400 hover:text-white transition-colors lg:hidden"
              >
                {sidebarOpen ? <ChevronLeft className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
              </button>
            </div>
          </div>

          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
            <input
              type="text"
              placeholder="Search investigations..."
              value={search}
              onChange={e => {
                setSearch(e.target.value)
                setSearchQuery(e.target.value)
              }}
              className="w-full pl-9 pr-3 py-2 bg-slate-800 border border-slate-600 rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
            />
          </div>
        </div>

        {/* Main Navigation */}
        {currentInvestigationId && (
          <div className="border-b border-slate-700">
            <nav className="p-2">
              {NAV_ITEMS
                .filter(item => item.id === 'investigation')
                .flatMap(item => 
                  item.children.map(child => (
                    <button
                      key={child.id}
                      onClick={() => {
                        setActiveTab(child.id)
                        window.location.hash = child.path
                      }}
                      className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                        activeTab === child.id
                          ? 'bg-blue-500 text-white'
                          : 'text-slate-400 hover:text-white hover:bg-slate-800'
                      }`}
                    >
                      <child.icon className="w-4 h-4" />
                      {child.label}
                    </button>
                  ))
                )}
            </nav>
          </div>
        )}

        {/* Quick Actions */}
        <div className="p-3 border-b border-slate-700">
          <div className="flex gap-2">
            <button
              onClick={() => setShowCreate(true)}
              className="flex-1 flex items-center gap-2 px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition-colors"
            >
              <Plus className="w-4 h-4" />
              New
            </button>
            <button className="p-2 bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white rounded-lg transition-colors">
              <Download className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Investigation List */}
        <div className="flex-1 overflow-y-auto">
          <div className="p-3">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                Investigations
              </h3>
              <span className="text-xs text-slate-500">
                {investigations.length} total
              </span>
            </div>

            {filtered.length === 0 ? (
              <div className="text-center py-8 text-slate-500 text-sm">
                {search ? 'No matches found' : 'No investigations yet'}
              </div>
            ) : (
              <div className="space-y-1">
                {filtered.map(inv => (
                  <div
                    key={inv.id}
                    className="group relative"
                  >
                    <Link
                      to={`/investigation/${inv.id}`}
                      className={`block p-3 rounded-lg transition-colors ${
                        currentInvestigationId === inv.id
                          ? 'bg-blue-500 text-white'
                          : 'hover:bg-slate-800 text-slate-300 hover:text-white'
                      }`}
                    >
                      <div className="flex items-start justify-between mb-1">
                        <div className="flex-1 min-w-0">
                          <div className="font-medium text-sm truncate">{inv.title}</div>
                          {inv.description && (
                            <div className="text-xs text-slate-500 mt-1 line-clamp-1">
                              {inv.description}
                            </div>
                          )}
                        </div>
                        <div className="flex items-center gap-1 ml-2">
                          <button
                            onClick={(e) => {
                              e.preventDefault()
                              toggleFavorite(inv.id)
                            }}
                            className="p-0.5 rounded hover:bg-white/10 text-slate-400 hover:text-white transition-colors"
                          >
                            <Star className={`w-3 h-3 ${
                              favorites.some(f => f.id === inv.id) ? 'fill-yellow-400 text-yellow-400' : ''
                            }`} />
                          </button>
                          <button
                            onClick={(e) => {
                              e.preventDefault()
                              handleDelete(inv.id, inv.title)
                            }}
                            className="p-0.5 rounded hover:bg-red-500/20 text-slate-400 hover:text-red-400 transition-colors opacity-0 group-hover:opacity-100"
                          >
                            <Trash2 className="w-3 h-3" />
                          </button>
                        </div>
                      </div>
                      
                      <div className="flex items-center gap-3 mt-2 text-xs text-slate-500">
                        <div className="flex items-center gap-1">
                          <Network className="w-3 h-3" />
                          <span>{inv.node_count} nodes</span>
                        </div>
                        <span>•</span>
                        <div className="flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          <span>{new Date(inv.updated_at).toLocaleDateString()}</span>
                        </div>
                        <span className={`px-1.5 py-0.5 rounded text-xs font-medium ${
                          inv.status === 'active' ? 'bg-green-500/20 text-green-400' :
                          inv.status === 'paused' ? 'bg-yellow-500/20 text-yellow-400' :
                          'bg-slate-500/20 text-slate-400'
                        }`}>
                          {inv.status}
                        </span>
                      </div>
                    </Link>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="p-3 border-t border-slate-700">
          <div className="flex items-center justify-between text-xs text-slate-500">
            <span>OsintHAM v0.2.0</span>
            <div className="flex items-center gap-2">
              <span>{recentInvestigations.length} recent</span>
              <span>•</span>
              <span>{favorites.length} favorites</span>
            </div>
          </div>
        </div>
      </aside>

      {/* Create Investigation Modal */}
      {showCreate && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 lg:z-60">
          <div className="bg-slate-800 rounded-xl p-6 w-full max-w-md border border-slate-600 animate-fade-in">
            <h2 className="text-xl font-bold text-white mb-4">New Investigation</h2>
            <input
              type="text"
              placeholder="Investigation title..."
              value={newTitle}
              onChange={e => setNewTitle(e.target.value)}
              className="w-full px-4 py-3 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 mb-3"
              autoFocus
              onKeyDown={e => e.key === 'Enter' && handleCreate()}
            />
            <textarea
              placeholder="Description (optional)..."
              value={newDesc}
              onChange={e => setNewDesc(e.target.value)}
              className="w-full px-4 py-3 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 mb-4 h-24 resize-none"
            />
            <div className="flex gap-3 justify-end">
              <button
                onClick={() => setShowCreate(false)}
                className="px-4 py-2 text-slate-400 hover:text-white transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleCreate}
                disabled={!newTitle.trim()}
                className="px-6 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg transition-colors font-medium"
              >
                Create
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}