import React, { useState } from 'react'
import { X, Plus } from 'lucide-react'
import useStore from '../store'
import { createInvestigation } from '../api'

export default function CreateInvestigationModal({ onClose, onCreated }) {
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const { addLog, addNotification } = useStore()

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!title.trim()) {
      setError('Название обязательно')
      return
    }
    setLoading(true)
    setError(null)
    try {
      const res = await createInvestigation({ title: title.trim(), description: description.trim() })
      addLog(`Создано расследование: ${title}`)
      addNotification({ type: 'success', title: 'Создано', message: `Расследование "${title}" создано` })
      if (onCreated) onCreated(res.data)
      onClose()
    } catch (err) {
      setError(err.message || 'Ошибка при создании')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50" onClick={onClose}>
      <div className="bg-[#1e293b] rounded-xl p-6 w-full max-w-md border border-[#334155] animate-fade-in"
        onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <Plus className="w-5 h-5 text-[#6366f1]" />
            Новое расследование
          </h2>
          <button onClick={onClose} className="p-1 rounded hover:bg-[#334155] text-[#94a3b8]">
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm text-[#94a3b8] mb-1">Название *</label>
            <input type="text" value={title} onChange={e => setTitle(e.target.value)}
              placeholder="Введите название..."
              className="w-full px-4 py-3 bg-[#0f172a] border border-[#334155] rounded-lg text-white placeholder-[#64748b] focus:outline-none focus:border-[#6366f1]"
              autoFocus />
          </div>
          <div>
            <label className="block text-sm text-[#94a3b8] mb-1">Описание</label>
            <textarea value={description} onChange={e => setDescription(e.target.value)}
              placeholder="Описание (необязательно)..."
              className="w-full px-4 py-3 bg-[#0f172a] border border-[#334155] rounded-lg text-white placeholder-[#64748b] focus:outline-none focus:border-[#6366f1] h-24 resize-none" />
          </div>
          {error && (
            <div className="text-red-400 text-sm bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2">{error}</div>
          )}
          <div className="flex gap-3 justify-end">
            <button type="button" onClick={onClose} className="px-4 py-2 text-[#94a3b8] hover:text-white transition-colors">Отмена</button>
            <button type="submit" disabled={loading || !title.trim()}
              className="flex items-center gap-2 px-6 py-2 bg-[#6366f1] hover:bg-[#818cf8] disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg transition-colors font-medium">
              {loading ? 'Создание...' : 'Создать'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
