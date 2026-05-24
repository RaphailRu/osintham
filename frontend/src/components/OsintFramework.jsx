import React, { useState, useEffect } from 'react'
import { Search, ExternalLink, Folder, Globe, Star, Filter, ChevronRight, ChevronDown } from 'lucide-react'

const API_BASE = import.meta.env.VITE_API_URL || '/api'

export default function OsintFramework() {
  const [categories, setCategories] = useState([])
  const [selectedCategory, setSelectedCategory] = useState(null)
  const [tools, setTools] = useState([])
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState(null)

  useEffect(() => {
    fetchCategories()
    fetchStats()
  }, [])

  const fetchCategories = async () => {
    try {
      const res = await fetch(`${API_BASE}/framework/categories`)
      const data = await res.json()
      setCategories(data)
    } catch (err) {
      console.error('Error:', err)
    } finally {
      setLoading(false)
    }
  }

  const fetchStats = async () => {
    try {
      const res = await fetch(`${API_BASE}/framework/stats`)
      const data = await res.json()
      setStats(data)
    } catch (err) {
      console.error('Error:', err)
    }
  }

  const fetchCategory = async (name) => {
    try {
      const res = await fetch(`${API_BASE}/framework/category/${encodeURIComponent(name)}`)
      const data = await res.json()
      setSelectedCategory(data)
      setTools(data.items || [])
    } catch (err) {
      console.error('Error:', err)
    }
  }

  const searchTools = async (e) => {
    e.preventDefault()
    if (!search.trim()) return
    try {
      const res = await fetch(`${API_BASE}/framework/search?q=${encodeURIComponent(search)}&limit=50`)
      const data = await res.json()
      setTools(data.results || [])
      setSelectedCategory(null)
    } catch (err) {
      console.error('Error:', err)
    }
  }

  if (loading) return <div className="flex items-center justify-center h-full text-[#64748b]">Загрузка...</div>

  return (
    <div className="h-full flex">
      {/* Left sidebar — categories */}
      <div className="w-72 bg-[#1e293b] border-r border-[#334155] flex flex-col">
        <div className="p-4 border-b border-[#334155]">
          <h2 className="font-bold text-white mb-3">OSINT Framework</h2>
          {stats && (
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="bg-[#0f172a] rounded p-2 text-center">
                <div className="text-lg font-bold text-[#6366f1]">{stats.total_nodes}</div>
                <div className="text-[#64748b]">Всего</div>
              </div>
              <div className="bg-[#0f172a] rounded p-2 text-center">
                <div className="text-lg font-bold text-[#10b981]">{stats.tools_with_url}</div>
                <div className="text-[#64748b]">С URL</div>
              </div>
            </div>
          )}
        </div>

        <form onSubmit={searchTools} className="p-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#64748b]" />
            <input type="text" value={search} onChange={e => setSearch(e.target.value)}
              placeholder="Поиск инструментов..."
              className="w-full pl-9 pr-3 py-2 bg-[#0f172a] border border-[#334155] rounded-lg text-sm text-white placeholder-[#64748b] focus:outline-none focus:border-[#6366f1]" />
          </div>
        </form>

        <div className="flex-1 overflow-y-auto p-2">
          <div className="text-xs font-semibold text-[#64748b] uppercase tracking-wider px-2 py-1">
            Категории ({categories.length})
          </div>
          {categories.map(cat => (
            <button key={cat.name} onClick={() => fetchCategory(cat.name)}
              className={`w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors ${
                selectedCategory?.name === cat.name
                  ? 'bg-[#6366f1] text-white'
                  : 'text-[#94a3b8] hover:bg-[#334155] hover:text-white'
              }`}>
              <Folder className="w-3 h-3 flex-shrink-0" />
              <span className="truncate flex-1 text-left">{cat.name}</span>
              <span className="text-xs opacity-60">{cat.total_items}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Main content */}
      <div className="flex-1 overflow-y-auto p-6">
        {selectedCategory && (
          <div className="mb-4">
            <button onClick={() => { setSelectedCategory(null); setTools([]) }}
              className="text-[#6366f1] hover:text-[#818cf8] text-sm mb-2">
              ← Назад к категориям
            </button>
            <h2 className="text-xl font-bold text-white">{selectedCategory.name}</h2>
            <p className="text-[#64748b] text-sm">{tools.length} инструментов</p>
          </div>
        )}

        {search && (
          <div className="mb-4">
            <h2 className="text-xl font-bold text-white">Результаты поиска: "{search}"</h2>
            <p className="text-[#64748b] text-sm">{tools.length} найдено</p>
          </div>
        )}

        {!selectedCategory && !search && (
          <div className="text-center py-20">
            <Globe className="w-16 h-16 text-[#334155] mx-auto mb-4" />
            <h2 className="text-xl text-[#64748b] mb-2">OSINT Framework</h2>
            <p className="text-[#475569] mb-4">Выберите категорию или используйте поиск</p>
            {stats && (
              <div className="inline-grid grid-cols-3 gap-4 mt-4">
                <div className="bg-[#1e293b] rounded-lg p-4">
                  <div className="text-2xl font-bold text-[#6366f1]">{stats.total_nodes}</div>
                  <div className="text-xs text-[#64748b]">Всего узлов</div>
                </div>
                <div className="bg-[#1e293b] rounded-lg p-4">
                  <div className="text-2xl font-bold text-[#10b981]">{stats.tools_with_url}</div>
                  <div className="text-xs text-[#64748b]">С сайтами</div>
                </div>
                <div className="bg-[#1e293b] rounded-lg p-4">
                  <div className="text-2xl font-bold text-[#f59e0b]">{stats.total_categories}</div>
                  <div className="text-xs text-[#64748b]">Категорий</div>
                </div>
              </div>
            )}
          </div>
        )}

        {tools.length > 0 && (
          <div className="space-y-2">
            {tools.map((tool, i) => (
              <div key={i} className="bg-[#1e293b] border border-[#334155] rounded-lg p-4 hover:border-[#6366f1] transition-colors">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h3 className="font-semibold text-white">{tool.name}</h3>
                    {tool.description && (
                      <p className="text-sm text-[#94a3b8] mt-1">{tool.description}</p>
                    )}
                    {tool.url && (
                      <a href={tool.url} target="_blank" rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 text-sm text-[#6366f1] hover:text-[#818cf8] mt-2">
                        <ExternalLink className="w-3 h-3" />
                        {tool.url.length > 60 ? tool.url.slice(0, 60) + '...' : tool.url}
                      </a>
                    )}
                  </div>
                  <div className="flex items-center gap-2 ml-4">
                    {tool.pricing && (
                      <span className={`px-2 py-0.5 rounded text-xs ${
                        tool.pricing === 'free' ? 'bg-green-500/20 text-green-400' :
                        tool.pricing === 'freemium' ? 'bg-yellow-500/20 text-yellow-400' :
                        'bg-red-500/20 text-red-400'
                      }`}>
                        {tool.pricing}
                      </span>
                    )}
                    {tool.status && tool.status !== 'live' && (
                      <span className={`px-2 py-0.5 rounded text-xs ${
                        tool.status === 'deprecated' ? 'bg-red-500/20 text-red-400' :
                        'bg-yellow-500/20 text-yellow-400'
                      }`}>
                        {tool.status}
                      </span>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
