import React, { useState, useEffect } from 'react'
import { X, Save } from 'lucide-react'

const NODE_TYPES = [
  { value: 'person', label: '👤 Person' },
  { value: 'email', label: '📧 Email' },
  { value: 'phone', label: '📱 Phone' },
  { value: 'social_account', label: '🌐 Social Account' },
  { value: 'organization', label: '🏢 Organization' },
  { value: 'domain', label: '🔗 Domain' },
  { value: 'ip', label: '📍 IP Address' },
  { value: 'event', label: '📅 Event' },
  { value: 'document', label: '📄 Document' },
]

export default function NodeEditor({ templates, onSave, onClose }) {
  const [type, setType] = useState('person')
  const [label, setLabel] = useState('')
  const [trustLevel, setTrustLevel] = useState(3)
  const [source, setSource] = useState('')
  const [fields, setFields] = useState([])
  const [fieldValues, setFieldValues] = useState({})

  useEffect(() => {
    const tmpl = templates.find(t => t.node_type === type)
    if (tmpl && tmpl.fields) {
      setFields(tmpl.fields)
      const defaults = {}
      tmpl.fields.forEach(f => { defaults[f.name] = '' })
      setFieldValues(defaults)
    } else {
      setFields([])
      setFieldValues({})
    }
  }, [type, templates])

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!label.trim()) return

    onSave({
      type,
      label: label.trim(),
      trust_level: trustLevel,
      source,
      data: fieldValues,
    })
  }

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
      <div className="bg-[#1e293b] rounded-xl w-full max-w-lg max-h-[90vh] overflow-y-auto border border-[#334155] animate-fade-in">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-[#334155]">
          <h2 className="text-lg font-bold text-white">Add Node</h2>
          <button onClick={onClose} className="p-1 rounded hover:bg-[#334155] text-[#94a3b8]">
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-4 space-y-4">
          {/* Type */}
          <div>
            <label className="block text-sm text-[#94a3b8] mb-1">Type</label>
            <select
              value={type}
              onChange={e => setType(e.target.value)}
              className="w-full px-3 py-2 bg-[#0f172a] border border-[#334155] rounded-lg text-white focus:outline-none focus:border-[#6366f1]"
            >
              {NODE_TYPES.map(t => (
                <option key={t.value} value={t.value}>{t.label}</option>
              ))}
            </select>
          </div>

          {/* Label */}
          <div>
            <label className="block text-sm text-[#94a3b8] mb-1">Label *</label>
            <input
              type="text"
              value={label}
              onChange={e => setLabel(e.target.value)}
              placeholder="Display name..."
              className="w-full px-3 py-2 bg-[#0f172a] border border-[#334155] rounded-lg text-white placeholder-[#64748b] focus:outline-none focus:border-[#6366f1]"
              required
            />
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
            <div className="flex justify-between text-xs text-[#64748b] mt-1">
              <span>Rumor</span>
              <span>Verified</span>
            </div>
          </div>

          {/* Source */}
          <div>
            <label className="block text-sm text-[#94a3b8] mb-1">Source</label>
            <input
              type="text"
              value={source}
              onChange={e => setSource(e.target.value)}
              placeholder="Where did this information come from?"
              className="w-full px-3 py-2 bg-[#0f172a] border border-[#334155] rounded-lg text-white placeholder-[#64748b] focus:outline-none focus:border-[#6366f1]"
            />
          </div>

          {/* Dynamic fields from template */}
          {fields.length > 0 && (
            <div className="border-t border-[#334155] pt-4">
              <h3 className="text-sm font-semibold text-[#94a3b8] mb-3">Questionnaire</h3>
              <div className="space-y-3">
                {fields.map(field => (
                  <div key={field.name}>
                    <label className="block text-sm text-[#94a3b8] mb-1">
                      {field.label} {field.required && <span className="text-red-400">*</span>}
                    </label>
                    {field.type === 'textarea' ? (
                      <textarea
                        value={fieldValues[field.name] || ''}
                        onChange={e => setFieldValues({ ...fieldValues, [field.name]: e.target.value })}
                        placeholder={field.label}
                        className="w-full px-3 py-2 bg-[#0f172a] border border-[#334155] rounded-lg text-white placeholder-[#64748b] focus:outline-none focus:border-[#6366f1] h-20 resize-none"
                      />
                    ) : field.type === 'select' ? (
                      <select
                        value={fieldValues[field.name] || ''}
                        onChange={e => setFieldValues({ ...fieldValues, [field.name]: e.target.value })}
                        className="w-full px-3 py-2 bg-[#0f172a] border border-[#334155] rounded-lg text-white focus:outline-none focus:border-[#6366f1]"
                      >
                        <option value="">Select...</option>
                        {(field.options || []).map(opt => (
                          <option key={opt} value={opt}>{opt}</option>
                        ))}
                      </select>
                    ) : (
                      <input
                        type={field.type === 'datetime-local' ? 'datetime-local' : field.type === 'date' ? 'date' : field.type === 'url' ? 'url' : field.type === 'email' ? 'email' : field.type === 'tel' ? 'tel' : 'text'}
                        value={fieldValues[field.name] || ''}
                        onChange={e => setFieldValues({ ...fieldValues, [field.name]: e.target.value })}
                        placeholder={field.label}
                        className="w-full px-3 py-2 bg-[#0f172a] border border-[#334155] rounded-lg text-white placeholder-[#64748b] focus:outline-none focus:border-[#6366f1]"
                      />
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

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
              disabled={!label.trim()}
              className="flex items-center gap-2 px-6 py-2 bg-[#6366f1] hover:bg-[#818cf8] disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg transition-colors font-medium"
            >
              <Save className="w-4 h-4" />
              Add Node
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
