import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Plus, FolderOpen, Trash2, Clock } from 'lucide-react'
import useStore from '../store'
import { getInvestigations, deleteInvestigation } from '../api'
import CreateInvestigationModal from '../components/CreateInvestigationModal'

export default function Dashboard() {
  const navigate = useNavigate()
  const { investigations, setInvestigations, addLog } = useStore()
  const [showCreate, setShowCreate] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadInvestigations()
  }, [])

  const loadInvestigations = async () => {
    try {
      const res = await getInvestigations()
      setInvestigations(res.data)
    } catch (err) {
      addLog(`Error loading investigations: ${err.message}`)
    } finally {
      setLoading(false)
    }
  }

  const handleCreated = (inv) => {
    setShowCreate(false)
    navigate(`/investigation/${inv.id}`)
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

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-[#64748b]">Loading investigations...</div>
      </div>
    )
  }

  return (
    <div className="p-8 max-w-6xl mx-auto">
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

      {showCreate && (
        <CreateInvestigationModal
          onClose={() => setShowCreate(false)}
          onCreated={handleCreated}
        />
      )}

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
                  aria-label={`Delete ${inv.title}`}
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
