import React, { useState, useEffect } from 'react'
import { Search, Shield, Globe, Zap, Database, Network, Users, MapPin, FileText, AlertTriangle } from 'lucide-react'

const CATEGORY_ICONS = {
  'Разведка (Recon)': Globe,
  'Угрозы (Threat)': AlertTriangle,
  'Соцсети (Social)': Users,
  'DNS': Database,
  'Сеть (Network)': Network,
  'Утечки (Leaks)': FileText,
  'Геолокация (Geo)': MapPin,
  'Другое (Other)': Zap,
}

export default function SpiderFoot() {
  const [categories, setCategories] = useState([])
  const [selectedCategory, setSelectedCategory] = useState(null)
  const [modules, setModules] = useState([])
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState(null)

  useEffect(() => { fetchCategories(); fetchStats() }, [])

  const fetchCategories = async () => {
    try {
      const res = await fetch('/api/spiderfoot/categories')
      setCategories(await res.json())
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const fetchStats = async () => {
    try {
      const res = await fetch('/api/spiderfoot/stats')
      setStats(await res.json())
    } catch (err) { console.error(err) }
  }

  const fetchCategory = async (name) => {
    try {
      const res = await fetch(`/api/spiderfoot/category/${encodeURIComponent(name)}`)
      const data = await res.json()
      setSelectedCategory(data)
      setModules(data.modules || [])
    } catch (err) { console.error(err) }
  }

  const searchModules = async (e) => {
    e.preventDefault()
    if (!search.trim()) return
    try {
      const res = await fetch(`/api/spiderfoot/search?q=${encodeURIComponent(search)}`)
      const data = await res.json()
      setModules(data.results || [])
      setSelectedCategory(null)
    } catch (err) { console.error(err) }
  }

  if (loading) return <div className="flex items-center justify-center h-full text-[#64748b]">Загрузка...</div>

  return (
    <div className="h-full flex">
      <div className="w-72 bg-[#1e293b] border-r border-[#334155] flex flex-col">
        <div className="p-4 border-b border-[#334155]">
          <h2 className="font-bold text-white mb-1 flex items-center gap-2">
            <Shield className="w-5 h-5 text-[#6366f1]" /> SpiderFoot
          </h2>
          <p className="text-xs text-[#64748b]">233 модуля OSINT-сканирования</p>
          {stats && (
            <div className="grid grid-cols-2 gap-2 mt-3 text-xs">
              <div className="bg-[#0f172a] rounded p-2 text-center">
                <div className="text-lg font-bold text-[#6366f1]">{stats.total_modules}</div>
                <div className="text-[#64748b]">Модулей</div>
              </div>
              <div className="bg-[#0f172a] rounded p-2 text-center">
                <div className="text-lg font-bold text-[#10b981]">8</div>
                <div className="text-[#64748b]">Категорий</div>
              </div>
            </div>
          )}
        </div>

        <form onSubmit={searchModules} className="p-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#64748b]" />
            <input type="text" value={search} onChange={e => setSearch(e.target.value)}
              placeholder="Поиск модулей..."
              className="w-full pl-9 pr-3 py-2 bg-[#0f172a] border border-[#334155] rounded-lg text-sm text-white placeholder-[#64748b] focus:outline-none focus:border-[#6366f1]" />
          </div>
        </form>

        <div className="flex-1 overflow-y-auto p-2">
          <div className="text-xs font-semibold text-[#64748b] uppercase tracking-wider px-2 py-1">
            Категории
          </div>
          {categories.map(cat => {
            const Icon = CATEGORY_ICONS[cat.name] || Zap
            return (
              <button key={cat.name} onClick={() => fetchCategory(cat.name)}
                className={`w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors ${
                  selectedCategory?.name === cat.name ? 'bg-[#6366f1] text-white' : 'text-[#94a3b8] hover:bg-[#334155] hover:text-white'
                }`}>
                <Icon className="w-3 h-3 flex-shrink-0" />
                <span className="truncate flex-1 text-left">{cat.name}</span>
                <span className="text-xs opacity-60">{cat.module_count}</span>
              </button>
            )
          })}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-6">
        {selectedCategory && (
          <div className="mb-4">
            <button onClick={() => { setSelectedCategory(null); setModules([]) }}
              className="text-[#6366f1] hover:text-[#818cf8] text-sm mb-2">← Назад</button>
            <h2 className="text-xl font-bold text-white">{selectedCategory.name}</h2>
            <p className="text-[#64748b] text-sm">{modules.length} модулей</p>
          </div>
        )}
        {search && (
          <div className="mb-4">
            <h2 className="text-xl font-bold text-white">Поиск: "{search}"</h2>
            <p className="text-[#64748b] text-sm">{modules.length} найдено</p>
          </div>
        )}
        {!selectedCategory && !search && (
          <div className="text-center py-20">
            <Shield className="w-16 h-16 text-[#334155] mx-auto mb-4" />
            <h2 className="text-xl text-[#64748b] mb-2">SpiderFoot OSINT Scanner</h2>
            <p className="text-[#475569] mb-4">Выберите категорию или используйте поиск</p>
            {stats && (
              <div className="inline-grid grid-cols-4 gap-3 mt-4">
                {stats.categories.map(cat => (
                  <div key={cat.name} className="bg-[#1e293b] rounded-lg p-3 text-center cursor-pointer hover:border-[#6366f1] border border-[#334155]"
                    onClick={() => fetchCategory(cat.name)}>
                    <div className="text-xl font-bold text-[#6366f1]">{cat.count}</div>
                    <div className="text-xs text-[#64748b] truncate">{cat.name}</div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
        {modules.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {modules.map((mod, i) => (
              <div key={i} className="bg-[#1e293b] border border-[#334155] rounded-lg p-3 hover:border-[#6366f1] transition-colors">
                <div className="font-mono text-sm text-[#818cf8]">{mod}</div>
                <div className="text-xs text-[#64748b] mt-1">{mod.replace('sfp_', '').replace(/_/g, ' ')}</div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
