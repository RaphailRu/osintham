import React, { useState } from 'react'
import { Search, Loader, CheckCircle, XCircle, AlertTriangle, Globe, Mail, Phone, User, Hash, Link, Shield, Server } from 'lucide-react'

const SCAN_TYPES = [
  { value: 'auto', label: '🔍 Auto-detect', icon: Search },
  { value: 'email', label: '📧 Email', icon: Mail },
  { value: 'phone', label: '📱 Phone', icon: Phone },
  { value: 'domain', label: '🌐 Domain', icon: Globe },
  { value: 'ip', label: '📍 IP Address', icon: Hash },
  { value: 'username', label: '👤 Username', icon: User },
  { value: 'url', label: '🔗 URL', icon: Link },
]

export default function OsintScanner({ investigationId, onNodeAdded }) {
  const [target, setTarget] = useState('')
  const [scanType, setScanType] = useState('auto')
  const [scanning, setScanning] = useState(false)
  const [results, setResults] = useState(null)
  const [error, setError] = useState(null)
  const [activeTab, setActiveTab] = useState('results')

  const API_BASE = import.meta.env.VITE_API_URL || '/api'

  const handleScan = async () => {
    if (!target.trim()) return
    setScanning(true)
    setError(null)
    setResults(null)

    try {
      const endpoint = scanType === 'auto'
        ? `${API_BASE}/osint/scan`
        : `${API_BASE}/osint/${scanType}/${encodeURIComponent(target.trim())}`

      const resp = scanType === 'auto'
        ? await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ target: target.trim(), target_type: scanType })
          })
        : await fetch(endpoint)

      if (!resp.ok) throw new Error(`Scan failed: ${resp.status}`)
      const data = await resp.json()
      setResults(data)
      setActiveTab('results')
    } catch (err) {
      setError(err.message)
    } finally {
      setScanning(false)
    }
  }

  const handleEnrich = async () => {
    if (!target.trim() || !investigationId) return
    setScanning(true)
    setError(null)

    try {
      const resp = await fetch(`${API_BASE}/osint/enrich/${investigationId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          target: target.trim(),
          target_type: scanType,
          auto_add_nodes: true
        })
      })
      if (!resp.ok) throw new Error(`Enrichment failed: ${resp.status}`)
      const data = await resp.json()
      setResults(data.scan_result)
      setActiveTab('results')
      if (onNodeAdded) onNodeAdded(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setScanning(false)
    }
  }

  return (
    <div className="bg-[#1e293b] border border-[#334155] rounded-xl overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 border-b border-[#334155] flex items-center gap-2">
        <Search className="w-4 h-4 text-[#6366f1]" />
        <span className="font-semibold text-white text-sm">OSINT Scanner</span>
      </div>

      {/* Input */}
      <div className="p-4 space-y-3">
        <div className="flex gap-2">
          <select
            value={scanType}
            onChange={e => setScanType(e.target.value)}
            className="px-3 py-2 bg-[#0f172a] border border-[#334155] rounded-lg text-white text-sm focus:outline-none focus:border-[#6366f1]"
          >
            {SCAN_TYPES.map(t => (
              <option key={t.value} value={t.value}>{t.label}</option>
            ))}
          </select>
          <input
            type="text"
            value={target}
            onChange={e => setTarget(e.target.value)}
            placeholder="Enter target (email, domain, IP, username...)"
            className="flex-1 px-3 py-2 bg-[#0f172a] border border-[#334155] rounded-lg text-white text-sm placeholder-[#64748b] focus:outline-none focus:border-[#6366f1]"
            onKeyDown={e => e.key === 'Enter' && handleScan()}
          />
        </div>

        <div className="flex gap-2">
          <button
            onClick={handleScan}
            disabled={scanning || !target.trim()}
            className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-[#6366f1] hover:bg-[#818cf8] disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg text-sm font-medium transition-colors"
          >
            {scanning ? <Loader className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
            {scanning ? 'Scanning...' : 'Scan'}
          </button>
          {investigationId && (
            <button
              onClick={handleEnrich}
              disabled={scanning || !target.trim()}
              className="flex items-center gap-2 px-4 py-2 bg-[#10b981] hover:bg-[#34d399] disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg text-sm font-medium transition-colors"
            >
              <Shield className="w-4 h-4" />
              Scan & Add to Graph
            </button>
          )}
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="mx-4 mb-3 p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm flex items-center gap-2">
          <XCircle className="w-4 h-4 flex-shrink-0" />
          {error}
        </div>
      )}

      {/* Results */}
      {results && (
        <div className="border-t border-[#334155]">
          {/* Tabs */}
          <div className="flex border-b border-[#334155]">
            <button
              onClick={() => setActiveTab('results')}
              className={`px-4 py-2 text-xs font-medium ${activeTab === 'results' ? 'text-[#6366f1] border-b-2 border-[#6366f1]' : 'text-[#64748b]'}`}
            >
              Results
            </button>
            <button
              onClick={() => setActiveTab('nodes')}
              className={`px-4 py-2 text-xs font-medium ${activeTab === 'nodes' ? 'text-[#6366f1] border-b-2 border-[#6366f1]' : 'text-[#64748b]'}`}
            >
              Suggested Nodes ({results.suggested_nodes?.length || 0})
            </button>
            <button
              onClick={() => setActiveTab('raw')}
              className={`px-4 py-2 text-xs font-medium ${activeTab === 'raw' ? 'text-[#6366f1] border-b-2 border-[#6366f1]' : 'text-[#64748b]'}`}
            >
              Raw JSON
            </button>
          </div>

          <div className="p-4 max-h-96 overflow-y-auto">
            {activeTab === 'results' && <ResultsView results={results} />}
            {activeTab === 'nodes' && <NodesView nodes={results.suggested_nodes} edges={results.suggested_edges} />}
            {activeTab === 'raw' && (
              <pre className="text-xs text-[#94a3b8] overflow-x-auto whitespace-pre-wrap">
                {JSON.stringify(results, null, 2)}
              </pre>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

function ResultsView({ results }) {
  const r = results.results || {}

  return (
    <div className="space-y-4">
      {/* Detected type */}
      <div className="flex items-center gap-2 text-sm">
        <span className="text-[#64748b]">Detected type:</span>
        <span className="px-2 py-0.5 bg-[#6366f1]/20 text-[#818cf8] rounded text-xs font-medium">
          {results.detected_type}
        </span>
      </div>

      {/* Email analysis */}
      {r.email_analysis && (
        <div className="bg-[#0f172a] rounded-lg p-3">
          <h4 className="text-sm font-semibold text-white mb-2 flex items-center gap-2">
            <Mail className="w-4 h-4 text-[#ef4444]" /> Email Analysis
          </h4>
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div><span className="text-[#64748b]">Valid:</span> {r.email_analysis.is_valid_format ? '✅' : '❌'}</div>
            <div><span className="text-[#64748b]">MX:</span> {r.email_analysis.has_mx ? '✅' : '❌'}</div>
            <div><span className="text-[#64748b]">Disposable:</span> {r.email_analysis.is_disposable ? '⚠️ Yes' : '✅ No'}</div>
            <div><span className="text-[#64748b]">Free provider:</span> {r.email_analysis.is_free_provider ? 'Yes' : 'No'}</div>
          </div>
          {r.email_analysis.mx_records?.length > 0 && (
            <div className="mt-2 text-xs">
              <span className="text-[#64748b]">MX Records:</span>
              {r.email_analysis.mx_records.map((mx, i) => (
                <div key={i} className="text-[#94a3b8] pl-2">{mx}</div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Breaches */}
      {r.breaches && (
        <div className="bg-[#0f172a] rounded-lg p-3">
          <h4 className="text-sm font-semibold text-white mb-2 flex items-center gap-2">
            <Shield className="w-4 h-4 text-[#f59e0b]" /> Data Breaches
          </h4>
          {r.breaches.breaches?.length > 0 ? (
            <div className="space-y-2">
              <div className="text-xs text-red-400 font-medium">
                ⚠️ Found in {r.breaches.total_breaches} breach(es)
              </div>
              {r.breaches.breaches.slice(0, 5).map((b, i) => (
                <div key={i} className="text-xs pl-2 border-l-2 border-red-500/30">
                  <div className="text-white">{b.name}</div>
                  <div className="text-[#64748b]">{b.domain} — {b.date}</div>
                </div>
              ))}
            </div>
          ) : r.breaches.checked ? (
            <div className="text-xs text-green-400">✅ No breaches found</div>
          ) : (
            <div className="text-xs text-[#64748b]">Could not check (API key required)</div>
          )}
        </div>
      )}

      {/* Domain analysis */}
      {r.domain_analysis && (
        <div className="bg-[#0f172a] rounded-lg p-3">
          <h4 className="text-sm font-semibold text-white mb-2 flex items-center gap-2">
            <Globe className="w-4 h-4 text-[#f59e0b]" /> Domain Analysis
          </h4>
          {r.domain_analysis.whois && (
            <div className="text-xs space-y-1">
              {r.domain_analysis.whois.registrar && (
                <div><span className="text-[#64748b]">Registrar:</span> <span className="text-white">{r.domain_analysis.whois.registrar}</span></div>
              )}
              {r.domain_analysis.whois.creation_date && (
                <div><span className="text-[#64748b]">Created:</span> <span className="text-white">{r.domain_analysis.whois.creation_date}</span></div>
              )}
              {r.domain_analysis.whois.expiration_date && (
                <div><span className="text-[#64748b]">Expires:</span> <span className="text-white">{r.domain_analysis.whois.expiration_date}</span></div>
              )}
            </div>
          )}
          {r.domain_analysis.dns && Object.keys(r.domain_analysis.dns).length > 0 && (
            <div className="mt-2 text-xs">
              <span className="text-[#64748b]">DNS Records:</span>
              {Object.entries(r.domain_analysis.dns).map(([type, records]) => (
                <div key={type} className="pl-2">
                  <span className="text-[#818cf8]">{type}:</span>{' '}
                  <span className="text-[#94a3b8]">{records.join(', ')}</span>
                </div>
              ))}
            </div>
          )}
          {r.domain_analysis.subdomains?.length > 0 && (
            <div className="mt-2 text-xs">
              <span className="text-[#64748b]">Subdomains found:</span>
              <div className="flex flex-wrap gap-1 mt-1">
                {r.domain_analysis.subdomains.map((sd, i) => (
                  <span key={i} className="px-1.5 py-0.5 bg-[#6366f1]/10 text-[#818cf8] rounded text-[10px]">{sd}</span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* IP analysis */}
      {r.ip_analysis && (
        <div className="bg-[#0f172a] rounded-lg p-3">
          <h4 className="text-sm font-semibold text-white mb-2 flex items-center gap-2">
            <Hash className="w-4 h-4 text-[#ec4899]" /> IP Analysis
          </h4>
          {r.ip_analysis.geolocation && (
            <div className="text-xs space-y-1">
              <div><span className="text-[#64748b]">Location:</span> <span className="text-white">
                {r.ip_analysis.geolocation.city}, {r.ip_analysis.geolocation.region}, {r.ip_analysis.geolocation.country}
              </span></div>
              <div><span className="text-[#64748b]">ISP:</span> <span className="text-white">{r.ip_analysis.geolocation.isp}</span></div>
              <div><span className="text-[#64748b]">ASN:</span> <span className="text-white">{r.ip_analysis.geolocation.asn}</span></div>
              {r.ip_analysis.reverse_dns && (
                <div><span className="text-[#64748b]">Reverse DNS:</span> <span className="text-white">{r.ip_analysis.reverse_dns}</span></div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Username search */}
      {r.username_search && (
        <div className="bg-[#0f172a] rounded-lg p-3">
          <h4 className="text-sm font-semibold text-white mb-2 flex items-center gap-2">
            <User className="w-4 h-4 text-[#10b981]" /> Username Search
          </h4>
          <div className="text-xs mb-2">
            <span className="text-[#64748b]">Checked:</span> {r.username_search.platforms_checked} platforms
          </div>
          {r.username_search.found?.length > 0 ? (
            <div className="space-y-1">
              <div className="text-green-400 text-xs font-medium">✅ Found on {r.username_search.found.length} platform(s)</div>
              {r.username_search.found.map((f, i) => (
                <div key={i} className="flex items-center gap-2 text-xs pl-2">
                  <CheckCircle className="w-3 h-3 text-green-400" />
                  <span className="text-white font-medium">{f.platform}</span>
                  <a href={f.url} target="_blank" rel="noopener noreferrer" className="text-[#818cf8] hover:underline truncate">
                    {f.url}
                  </a>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-xs text-[#64748b]">Not found on checked platforms</div>
          )}
        </div>
      )}

      {/* URL analysis */}
      {r.url_analysis && (
        <div className="bg-[#0f172a] rounded-lg p-3">
          <h4 className="text-sm font-semibold text-white mb-2 flex items-center gap-2">
            <Link className="w-4 h-4 text-[#6366f1]" /> URL Analysis
          </h4>
          <div className="text-xs space-y-1">
            <div><span className="text-[#64748b]">Status:</span> <span className="text-white">{r.url_analysis.status_code}</span></div>
            {r.url_analysis.technologies?.length > 0 && (
              <div>
                <span className="text-[#64748b]">Technologies:</span>
                <div className="flex flex-wrap gap-1 mt-1">
                  {r.url_analysis.technologies.map((t, i) => (
                    <span key={i} className="px-1.5 py-0.5 bg-[#6366f1]/10 text-[#818cf8] rounded text-[10px]">{t}</span>
                  ))}
                </div>
              </div>
            )}
            {r.url_analysis.security && Object.keys(r.url_analysis.security).length > 0 && (
              <div>
                <span className="text-[#64748b]">Security Headers:</span>
                <div className="grid grid-cols-2 gap-1 mt-1">
                  {Object.entries(r.url_analysis.security).map(([name, status]) => (
                    <div key={name} className="text-[10px]">{status} {name}</div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Phone analysis */}
      {r.phone_analysis && (
        <div className="bg-[#0f172a] rounded-lg p-3">
          <h4 className="text-sm font-semibold text-white mb-2 flex items-center gap-2">
            <Phone className="w-4 h-4 text-[#f97316]" /> Phone Analysis
          </h4>
          <div className="text-xs space-y-1">
            <div><span className="text-[#64748b]">Valid:</span> {r.phone_analysis.is_valid ? '✅' : '❌'}</div>
            <div><span className="text-[#64748b]">Country:</span> <span className="text-white">{r.phone_analysis.country || 'Unknown'}</span></div>
            <div><span className="text-[#64748b]">Cleaned:</span> <span className="text-white">{r.phone_analysis.cleaned}</span></div>
          </div>
        </div>
      )}
    </div>
  )
}

function NodesView({ nodes, edges }) {
  if (!nodes?.length) return <div className="text-[#64748b] text-sm">No suggested nodes</div>
  return (
    <div className="space-y-3">
      <div className="text-xs text-[#64748b]">{nodes.length} nodes, {edges?.length || 0} edges suggested</div>
      {nodes.map((n, i) => (
        <div key={i} className="bg-[#0f172a] rounded-lg p-3 text-xs">
          <div className="flex items-center gap-2 mb-1">
            <span className="px-1.5 py-0.5 bg-[#6366f1]/20 text-[#818cf8] rounded">{n.type}</span>
            <span className="text-white font-medium">{n.label}</span>
          </div>
          <div className="text-[#64748b]">Trust: {'⭐'.repeat(n.trust_level)} | Source: {n.source}</div>
        </div>
      ))}
    </div>
  )
}
