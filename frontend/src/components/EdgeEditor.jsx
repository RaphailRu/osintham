import React, { useState } from 'react'
import { X, Save, Link } from 'lucide-react'

const RELATIONSHIP_TYPES = [
  'owns', 'belongs to', 'related to', 'works for', 'communicates with',
  'same person as', 'mentioned in', 'created', 'located at', 'connected to',
  'family of', 'friend of', 'colleague of', 'customer of', 'supplier of',
  'registered to', 'hosted on', 'resolves to', 'subdomain of',
]

export default function EdgeEditor({ nodes, onSave, onClose }) {
  const [fromNode, setFromNode] = useState('')
  const [toNode, setToNode] = useState('')
  const [label, setLabel] = useState('')
  const [trustLevel, setTrustLevel] = useState(3)
  const [bidirectional, setBidirectional] = useState(false)

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!fromNode || !toNode) return

    onSave({
      from_node: fromNode,
      to_node: toNode,
      label: label.trim() || 'related to',
      trust_level: trustLevel,
      bidirectional,
    })
  }

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
      <div className="bg-[#1e293b] rounded-xl w-full max-w-md border border-[#334155] animate-fade-in">
        <div className="flex items-center justify-between p-4 border-b border-[#334155]">
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <Link className="w-5 h-5 text-[#6366f1]" />
            Add Connection
          </h2>
          <button onClick={onClose} className="p-1 rounded hover:bg-[#334155] text-[#94a3b8]">
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-4 space-y-4">
          {/* From Node */}
          <div>
            <label className="block text-sm text-[#94a3b8] mb-1">From Node *</label>
            <select
              value={fromNode}
              onChange={e => setFromNode(e.target.value)}
              className="w-full px-3 py-2 bg-[#0f172a] border border-[#334155] rounded-lg text-white focus:outline-none focus:border-[#6366f1]"
              required
            >
              <option value="">Select source node...</option>
              {nodes.map(n => (
                <option key={n.id} value={n.id}>{n.label} ({n.type})</option>
              ))}
            </select>
          </div>

          {/* To Node */}
          <div>
            <label className="block text-sm text-[#94a3b8] mb-1">To Node *</label>
            <select
              value={toNode}
              onChange={e => setToNode(e.target.value)}
              className="w-full px-3 py-2 bg-[#0f172a] border border-[#334155] rounded-lg text-white focus:outline-none focus:border-[#6366f1]"
              required
            >
              <option value="">Select target node...</option>
              {nodes.map(n => (
                <option key={n.id} value={n.id}>{n.label} ({n.type})</option>
              ))}
            </select>
          </div>

          {/* Relationship Type */}
          <div>
            <label className="block text-sm text-[#94a3b8] mb-1">Relationship</label>
            <input
              type="text"
              value={label}
              onChange={e => setLabel(e.target.value)}
              placeholder="e.g., owns, related to, works for..."
              list="relationship-types"
              className="w-full px-3 py-2 bg-[#0f172a] border border-[#334155] rounded-lg text-white placeholder-[#64748b] focus:outline-none focus:border-[#6366f1]"
            />
            <datalist id="relationship-types">
              {RELATIONSHIP_TYPES.map(t => (
                <option key={t} value={t} />
              ))}
            </datalist>
          </div>

          {/* Trust Level */}
          <div>
            <label className="block text-sm text-[#94a3b8] mb-1">Trust Level: {trustLevel}/5</label>
            <input
              type="range"
              min="1"
              max="5"
              value={trustLevel}
              onChange={e => setTrustLevel(Number(e.target.value))}
              className="w-full accent-[#6366f1]"
            />
          </div>

          {/* Bidirectional */}
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="bidirectional"
              checked={bidirectional}
              onChange={e => setBidirectional(e.target.checked)}
              className="w-4 h-4 accent-[#6366f1]"
            />
            <label htmlFor="bidirectional" className="text-sm text-[#94a3b8]">
              Bidirectional (two-way relationship)
            </label>
          </div>

          {/* Actions */}
          <div className="flex gap-3 justify-end pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-[#94a3b8] hover:text-white transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!fromNode || !toNode}
              className="flex items-center gap-2 px-6 py-2 bg-[#6366f1] hover:bg-[#818cf8] disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg transition-colors font-medium"
            >
              <Save className="w-4 h-4" />
              Add Connection
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
