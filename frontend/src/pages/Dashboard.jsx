import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Plus, FolderOpen, Trash2, Clock } from 'lucide-react'
import useStore from '../store'
import { getInvestigations, createInvestigation, deleteInvestigation } from '../api'

export default function Dashboard() {
  const navigate = useNavigate()
  const { investigations, setInvestigations, addLog } = useStore()
  const [showCreate, setShowCreate] = useState(false)
  const [newTitle, setNewTitle] = useState('')
  const [newDesc, setNewDesc] = useState('')

  useEffect(() => {
    loadInvestigations()
  }, [])

  const loadInvestigations = async () => {
    try {
      const res = await getInvestigations()
      setInvestigations(res.data)
    } catch (err) {
      addLog(`Error loading investigations: ${err.message}`)
    }
  }

  const handleCreate = async () => {
    if (!newTitle.trim()) return
    try {
      const res = await createInvestigation({ title: newTitle, description: newDesc })
      addLog(`Created investigation: ${newTitle}`)
      setNewTitle('')
      setNewDesc('')
      setShowCreate(false)
      await loadInvestigations()
      navigate(`/investigation/${res.data.id}`)
    } catch (err) {
      addLog(`Error creating: ${err.message}`)
    }
  }

  const handleDelete = async (id, title) => {
    if (!confirm(`Delete "${title}"? This cannot be undone.`)) return
    try {
      await deleteInvestigation(id)
      addLog(`Deleted investigation: ${title}`)
      await loadInvestigations()
    } catch (err) {
      addLog(`Error deleting: ${err.message}`)
    }
  }

  return (
    <div className="p-8 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">🕷️ OsintHAM</h1>
          <p className="text-[#94a3b8]">OSINT Investigation Constructor — build relationship graphs, collect evidence, generate reports</p>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          className="flex items-center gap-2 px-4 py-2 bg-[#6366f1] hover:bg-[#818cf8] text-white rounded-lg transition-colors font-medium"
        >
          <Plus className="w-5 h-5" />
          New Investigation
        </button>
      </div>

      {/* Create Modal */}
      {showCreate && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
          <div className="bg-[#1e293b] rounded-xl p-6 w-full max-w-md border border-[#334155] animate-fade-in">
            <h2 className="text-xl font-bold text-white mb-4">New Investigation</h2>
            <input
              type="text"
              placeholder="Investigation title..."
              value={newTitle}
              onChange={e => setNewTitle(e.target.value)}
              className="w-full px-4 py-3 bg-[#0f172a] border border-[#334155] rounded-lg text-white placeholder-[#64748b] focus:outline-none focus:border-[#6366f1] mb-3"
              autoFocus
              onKeyDown={e => e.key === 'Enter' && handleCreate()}
            />
            <textarea
              placeholder="Description (optional)..."
              value={newDesc}
              onChange={e => setNewDesc(e.target.value)}
              className="w-full px-4 py-3 bg-[#0f172a] border border-[#334155] rounded-lg text-white placeholder-[#64748b] focus:outline-none focus:border-[#6366f1] mb-4 h-24 resize-none"
            />
            <div className="flex gap-3 justify-end">
              <button
                onClick={() => setShowCreate(false)}
                className="px-4 py-2 text-[#94a3b8] hover:text-white transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleCreate}
                disabled={!newTitle.trim()}
                className="px-6 py-2 bg-[#6366f1] hover:bg-[#818cf8] disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg transition-colors font-medium"
              >
                Create
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Investigation Grid */}
      {investigations.length === 0 ? (
        <div className="text-center py-20">
          <FolderOpen className="w-16 h-16 text-[#334155] mx-auto mb-4" />
          <h2 className="text-xl text-[#64748b] mb-2">No investigations yet</h2>
          <p className="text-[#475569] mb-6">Create your first investigation to get started</p>
          <button
            onClick={() => setShowCreate(true)}
            className="px-6 py-3 bg-[#6366f1] hover:bg-[#818cf8] text-white rounded-lg transition-colors font-medium"
          >
            <Plus className="w-5 h-5 inline mr-2" />
            Create Investigation
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {investigations.map(inv => (
            <div
              key={inv.id}
              className="bg-[#1e293b] border border-[#334155] rounded-xl p-5 hover:border-[#6366f1] transition-all cursor-pointer group animate-fade-in"
              onClick={() => navigate(`/investigation/${inv.id}`)}
            >
              <div className="flex items-start justify-between mb-3">
                <h3 className="text-lg font-semibold text-white group-hover:text-[#818cf8] transition-colors truncate">
                  {inv.title}
                </h3>
                <button
                  onClick={e => { e.stopPropagation(); handleDelete(inv.id, inv.title) }}
                  className="p-1 rounded hover:bg-red-500/20 text-[#64748b] hover:text-red-400 transition-colors opacity-0 group-hover:opacity-100"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
              <p className="text-[#94a3b8] text-sm mb-4 line-clamp-2 h-10">
                {inv.description || 'No description'}
              </p>
              <div className="flex items-center justify-between text-xs text-[#64748b]">
                <div className="flex items-center gap-3">
                  <span>{inv.node_count} nodes</span>
                  <span>{inv.edge_count} edges</span>
                </div>
                <div className="flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  {new Date(inv.updated_at).toLocaleDateString()}
                </div>
              </div>
              <div className="mt-3">
                <span className={`inline-block px-2 py-0.5 rounded text-[10px] font-medium ${
                  inv.status === 'active' ? 'bg-green-500/20 text-green-400' :
                  inv.status === 'paused' ? 'bg-yellow-500/20 text-yellow-400' :
                  'bg-gray-500/20 text-gray-400'
                }`}>
                  {inv.status.toUpperCase()}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
