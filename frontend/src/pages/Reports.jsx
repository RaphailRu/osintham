import React, { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { FileText, Download, ExternalLink, ArrowLeft } from 'lucide-react'
import useStore from '../store'
import { getReportJson, getReportHtml, getReportMarkdown } from '../api'

export default function Reports() {
  const { id } = useParams()
  const { currentInvestigation, addLog } = useStore()
  const [report, setReport] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadReport()
  }, [id])

  const loadReport = async () => {
    try {
      const res = await getReportJson(id)
      setReport(res.data)
      addLog('Report generated')
    } catch (err) {
      addLog(`Error generating report: ${err.message}`)
    } finally {
      setLoading(false)
    }
  }

  const downloadJson = () => {
    if (!report) return
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `osintham_report_${id.slice(0, 8)}.json`
    a.click()
    addLog('Downloaded JSON report')
  }

  const downloadHtml = async () => {
    try {
      const res = await getReportHtml(id)
      const blob = new Blob([res.data], { type: 'text/html' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `osintham_report_${id.slice(0, 8)}.html`
      a.click()
      URL.revokeObjectURL(url)
      addLog('Downloaded HTML report')
    } catch (err) {
      addLog(`Error: ${err.message}`)
    }
  }

  const downloadMarkdown = async () => {
    try {
      const res = await getReportMarkdown(id)
      const blob = new Blob([res.data], { type: 'text/markdown' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `osintham_report_${id.slice(0, 8)}.md`
      a.click()
      URL.revokeObjectURL(url)
      addLog('Downloaded Markdown report')
    } catch (err) {
      addLog(`Error: ${err.message}`)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-[#64748b]">Generating report...</div>
      </div>
    )
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex items-center gap-4 mb-6">
        <Link to={`/investigation/${id}`} className="p-2 rounded-lg hover:bg-[#334155] text-[#94a3b8]">
          <ArrowLeft className="w-5 h-5" />
        </Link>
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <FileText className="w-6 h-6 text-[#6366f1]" />
            Reports
          </h1>
          <p className="text-[#64748b]">{currentInvestigation?.title || 'Investigation'}</p>
        </div>
      </div>

      {/* Export buttons */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <button
          onClick={downloadJson}
          className="p-4 bg-[#1e293b] border border-[#334155] rounded-xl hover:border-[#6366f1] transition-colors text-left"
        >
          <div className="text-2xl mb-2">📋</div>
          <h3 className="font-semibold text-white">JSON Export</h3>
          <p className="text-sm text-[#64748b]">Machine-readable format for import into other tools</p>
        </button>
        <button
          onClick={downloadHtml}
          className="p-4 bg-[#1e293b] border border-[#334155] rounded-xl hover:border-[#6366f1] transition-colors text-left"
        >
          <div className="text-2xl mb-2">🌐</div>
          <h3 className="font-semibold text-white">HTML Report</h3>
          <p className="text-sm text-[#64748b]">Formatted report, viewable in browser</p>
        </button>
        <button
          onClick={downloadMarkdown}
          className="p-4 bg-[#1e293b] border border-[#334155] rounded-xl hover:border-[#6366f1] transition-colors text-left"
        >
          <div className="text-2xl mb-2">📝</div>
          <h3 className="font-semibold text-white">Markdown</h3>
          <p className="text-sm text-[#64748b]">Plain text format, good for documentation</p>
        </button>
      </div>

      {/* Report preview */}
      {report && (
        <div className="bg-[#1e293b] border border-[#334155] rounded-xl overflow-hidden">
          <div className="p-4 border-b border-[#334155]">
            <h2 className="font-semibold text-white">Report Preview</h2>
            <p className="text-sm text-[#64748b]">Generated: {new Date(report.generated_at).toLocaleString()}</p>
          </div>

          <div className="p-4">
            {/* Summary */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
              <div className="bg-[#0f172a] rounded-lg p-3 text-center">
                <div className="text-2xl font-bold text-[#6366f1]">{report.summary.total_nodes}</div>
                <div className="text-xs text-[#64748b]">Total Nodes</div>
              </div>
              <div className="bg-[#0f172a] rounded-lg p-3 text-center">
                <div className="text-2xl font-bold text-[#10b981]">{report.summary.total_edges}</div>
                <div className="text-xs text-[#64748b]">Total Edges</div>
              </div>
              <div className="bg-[#0f172a] rounded-lg p-3 text-center">
                <div className="text-2xl font-bold text-[#f59e0b]">{Object.keys(report.summary.node_types).length}</div>
                <div className="text-xs text-[#64748b]">Node Types</div>
              </div>
              <div className="bg-[#0f172a] rounded-lg p-3 text-center">
                <div className="text-2xl font-bold text-[#ec4899]">{report.summary.avg_trust}</div>
                <div className="text-xs text-[#64748b]">Avg Trust</div>
              </div>
            </div>

            {/* Node types breakdown */}
            <h3 className="text-sm font-semibold text-[#94a3b8] mb-2">Node Types</h3>
            <div className="flex flex-wrap gap-2 mb-6">
              {Object.entries(report.summary.node_types).map(([type, count]) => (
                <span key={type} className="px-3 py-1 bg-[#0f172a] rounded-full text-sm text-white">
                  {type}: <span className="text-[#6366f1] font-bold">{count}</span>
                </span>
              ))}
            </div>

            {/* Nodes table */}
            <h3 className="text-sm font-semibold text-[#94a3b8] mb-2">Nodes</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-[#64748b] border-b border-[#334155]">
                    <th className="text-left py-2 px-3">Type</th>
                    <th className="text-left py-2 px-3">Label</th>
                    <th className="text-left py-2 px-3">Trust</th>
                    <th className="text-left py-2 px-3">Source</th>
                  </tr>
                </thead>
                <tbody>
                  {report.nodes.map(node => (
                    <tr key={node.id} className="border-b border-[#334155]/50 hover:bg-[#334155]/20">
                      <td className="py-2 px-3">
                        <span className="px-2 py-0.5 bg-[#6366f1]/20 text-[#818cf8] rounded text-xs">{node.type}</span>
                      </td>
                      <td className="py-2 px-3 text-white">{node.label}</td>
                      <td className="py-2 px-3">{'⭐'.repeat(node.trust_level)}</td>
                      <td className="py-2 px-3 text-[#64748b]">{node.source || '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
