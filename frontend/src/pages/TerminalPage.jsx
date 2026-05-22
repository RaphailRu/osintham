import React, { useEffect, useRef, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { ArrowLeft, Send, Trash2 } from 'lucide-react'
import useStore from '../store'

const HELP_TEXT = `
╔══════════════════════════════════════════════════════╗
║           OsintHAM Web Terminal v0.1.0               ║
╠══════════════════════════════════════════════════════╣
║  Commands:                                           ║
║    help          — Show this help                    ║
║    clear         — Clear terminal                    ║
║    status        — Show investigation status         ║
║    nodes         — List all nodes                    ║
║    edges         — List all edges                    ║
║    stats         — Show graph statistics             ║
║    export json   — Export as JSON                    ║
║    export html   — Export as HTML                    ║
║    find <query>  — Search nodes by label             ║
║    whois <domain> — Simulate WHOIS lookup            ║
║    ping <ip>     — Simulate ping                     ║
║    nslookup <d>  — Simulate DNS lookup               ║
║    hash <text>   — Generate hash of text             ║
║    base64 <text> — Base64 encode                     ║
║    decode <text> — Base64 decode                     ║
║    ipinfo <ip>   — Simulate IP info lookup           ║
║    email <addr>  — Analyze email address             ║
║    phone <num>   — Analyze phone number              ║
╚══════════════════════════════════════════════════════╝
`

const COMMANDS = {
  help: () => HELP_TEXT,
  clear: '__CLEAR__',
  status: (store) => {
    const inv = store.currentInvestigation
    const gd = store.graphData
    return `Investigation: ${inv?.title || 'None'}
Status: ${inv?.status || 'N/A'}
Nodes: ${gd?.nodes?.length || 0}
Edges: ${gd?.edges?.length || 0}
Density: ${gd?.stats?.density || 0}
Components: ${gd?.stats?.components || 0}`
  },
  nodes: (store) => {
    const nodes = store.graphData?.nodes || []
    if (!nodes.length) return 'No nodes in graph.'
    return nodes.map(n => `  [${n.type}] ${n.label} (trust: ${n.trust_level}/5)`).join('\n')
  },
  edges: (store) => {
    const edges = store.graphData?.edges || []
    if (!edges.length) return 'No edges in graph.'
    return edges.map(e => `  ${e.from?.slice(0, 20)} → ${e.to?.slice(0, 20)} [${e.label || 'related'}]`).join('\n')
  },
  stats: (store) => {
    const s = store.graphData?.stats || {}
    return `Graph Statistics:
  Nodes: ${s.node_count || 0}
  Edges: ${s.edge_count || 0}
  Density: ${s.density || 0}
  Connected: ${s.is_connected ? 'Yes' : 'No'}
  Components: ${s.components || 0}`
  },
  'export': (store, args) => {
    const format = args[1] || 'json'
    return `Export to ${format.toUpperCase()} — use the Reports page for full export.\nData available: ${store.graphData?.nodes?.length || 0} nodes, ${store.graphData?.edges?.length || 0} edges.`
  },
  find: (store, args) => {
    const query = args.slice(1).join(' ').toLowerCase()
    if (!query) return 'Usage: find <query>'
    const nodes = store.graphData?.nodes || []
    const matches = nodes.filter(n => n.label.toLowerCase().includes(query))
    if (!matches.length) return `No nodes matching "${query}"`
    return matches.map(n => `  [${n.type}] ${n.label} (trust: ${n.trust_level}/5)`).join('\n')
  },
  whois: (_, args) => {
    const domain = args[1]
    if (!domain) return 'Usage: whois <domain>'
    return `WHOIS Lookup: ${domain}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Registrar: Example Registrar Inc.
Creation Date: 2020-01-15
Expiry Date: 2025-01-15
Nameservers:
  ns1.${domain}
  ns2.${domain}
Status: active
[Simulated response for demo purposes]`
  },
  ping: (_, args) => {
    const host = args[1]
    if (!host) return 'Usage: ping <host>'
    return `PING ${host} (93.184.216.34): 56 data bytes
64 bytes from 93.184.216.34: icmp_seq=0 ttl=56 time=12.3 ms
64 bytes from 93.184.216.34: icmp_seq=1 ttl=56 time=11.8 ms
64 bytes from 93.184.216.34: icmp_seq=2 ttl=56 time=12.1 ms
--- ${host} ping statistics ---
3 packets transmitted, 3 received, 0% packet loss
round-trip min/avg/max = 11.8/12.1/12.3 ms
[Simulated]`
  },
  nslookup: (_, args) => {
    const domain = args[1]
    if (!domain) return 'Usage: nslookup <domain>'
    return `Server:  8.8.8.8
Address: 8.8.8.8#53

Non-authoritative answer:
Name:    ${domain}
Address: 93.184.216.34
[Simulated response]`
  },
  hash: (_, args) => {
    const text = args.slice(1).join(' ')
    if (!text) return 'Usage: hash <text>'
    // Simple hash simulation
    let hash = 0
    for (let i = 0; i < text.length; i++) {
      const char = text.charCodeAt(i)
      hash = ((hash << 5) - hash) + char
      hash = hash & hash
    }
    const md5 = Math.abs(hash).toString(16).padStart(32, '0')
    const sha1 = md5 + md5.slice(0, 8)
    const sha256 = sha1 + sha1
    return `Hash: "${text}"
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MD5:     ${md5}
SHA-1:   ${sha1}
SHA-256: ${sha256}
[Simulated hashes for demo]`
  },
  base64: (_, args) => {
    const text = args.slice(1).join(' ')
    if (!text) return 'Usage: base64 <text>'
    try {
      return `Base64 encode: "${text}"\nResult: ${btoa(text)}`
    } catch {
      return 'Error: Cannot encode (use ASCII characters)'
    }
  },
  decode: (_, args) => {
    const text = args.slice(1).join(' ')
    if (!text) return 'Usage: decode <base64>'
    try {
      return `Base64 decode: "${text}"\nResult: ${atob(text)}`
    } catch {
      return 'Error: Invalid Base64 string'
    }
  },
  ipinfo: (_, args) => {
    const ip = args[1]
    if (!ip) return 'Usage: ipinfo <ip>'
    return `IP Information: ${ip}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Country: United States
City: New York
ISP: Example ISP Corp
ASN: AS12345
Timezone: America/New_York
Coordinates: 40.7128, -74.0060
[Simulated response for demo purposes]`
  },
  email: (_, args) => {
    const email = args[1]
    if (!email) return 'Usage: email <address>'
    const [user, domain] = email.split('@')
    return `Email Analysis: ${email}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Username: ${user || 'N/A'}
Domain: ${domain || 'N/A'}
Format: ${email.includes('@') && email.includes('.') ? 'Valid' : 'Invalid'}
Provider: ${domain || 'Unknown'}
MX Records: mail.${domain || 'example.com'}
[Simulated analysis]`
  },
  phone: (_, args) => {
    const num = args[1]
    if (!num) return 'Usage: phone <number>'
    return `Phone Analysis: ${num}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Format: International
Country: +1 (simulated)
Carrier: Example Carrier
Type: Mobile
Valid: Yes
[Simulated analysis]`
  },
}

export default function TerminalPage() {
  const { id } = useParams()
  const { currentInvestigation, graphData, addLog } = useStore()
  const [history, setHistory] = useState([
    { type: 'system', text: HELP_TEXT }
  ])
  const [input, setInput] = useState('')
  const [cmdHistory, setCmdHistory] = useState([])
  const [cmdHistoryIdx, setCmdHistoryIdx] = useState(-1)
  const scrollRef = useRef(null)
  const inputRef = useRef(null)

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [history])

  const executeCommand = (cmd) => {
    const trimmed = cmd.trim()
    if (!trimmed) return

    const parts = trimmed.split(/\s+/)
    const cmdName = parts[0].toLowerCase()

    setHistory(prev => [...prev, { type: 'input', text: trimmed }])
    setCmdHistory(prev => [trimmed, ...prev])
    setCmdHistoryIdx(-1)

    if (cmdName === 'clear') {
      setHistory([])
      return
    }

    const handler = COMMANDS[cmdName]
    if (handler) {
      const result = handler({ currentInvestigation, graphData }, parts)
      if (result === '__CLEAR__') {
        setHistory([])
      } else {
        setHistory(prev => [...prev, { type: 'output', text: result }])
      }
    } else {
      setHistory(prev => [...prev, {
        type: 'error',
        text: `Command not found: ${cmdName}. Type 'help' for available commands.`
      }])
    }

    addLog(`Terminal: ${trimmed}`)
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      executeCommand(input)
      setInput('')
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      if (cmdHistoryIdx < cmdHistory.length - 1) {
        const newIdx = cmdHistoryIdx + 1
        setCmdHistoryIdx(newIdx)
        setInput(cmdHistory[newIdx])
      }
    } else if (e.key === 'ArrowDown') {
      e.preventDefault()
      if (cmdHistoryIdx > 0) {
        const newIdx = cmdHistoryIdx - 1
        setCmdHistoryIdx(newIdx)
        setInput(cmdHistory[newIdx])
      } else {
        setCmdHistoryIdx(-1)
        setInput('')
      }
    }
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center gap-4 px-4 py-2 bg-[#1e293b] border-b border-[#334155]">
        <Link to={`/investigation/${id}`} className="p-1.5 rounded hover:bg-[#334155] text-[#94a3b8]">
          <ArrowLeft className="w-4 h-4" />
        </Link>
        <span className="text-sm text-[#94a3b8]">Terminal</span>
        <span className="text-xs text-[#64748b]">— {currentInvestigation?.title || 'No investigation'}</span>
        <div className="flex-1" />
        <button
          onClick={() => setHistory([{ type: 'system', text: HELP_TEXT }])}
          className="p-1.5 rounded hover:bg-[#334155] text-[#64748b]"
          title="Clear terminal"
        >
          <Trash2 className="w-4 h-4" />
        </button>
      </div>

      {/* Terminal output */}
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto p-4 font-mono text-sm"
        style={{ background: '#0a0a1a', color: '#22c55e' }}
        onClick={() => inputRef.current?.focus()}
      >
        {history.map((entry, i) => (
          <div
            key={i}
            className={`whitespace-pre-wrap mb-1 ${
              entry.type === 'input' ? 'text-[#818cf8]' :
              entry.type === 'error' ? 'text-red-400' :
              entry.type === 'system' ? 'text-[#64748b]' :
              'text-[#22c55e]'
            }`}
          >
            {entry.type === 'input' && <span className="text-[#6366f1]">❯ </span>}
            {entry.text}
          </div>
        ))}

        {/* Input line */}
        <div className="flex items-center text-[#818cf8]">
          <span className="text-[#6366f1]">❯ </span>
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            className="flex-1 bg-transparent outline-none text-[#22c55e] caret-[#6366f1]"
            autoFocus
            spellCheck={false}
          />
        </div>
      </div>
    </div>
  )
}
