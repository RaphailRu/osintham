import React, { useEffect, useRef, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { ArrowLeft, Trash2 } from 'lucide-react'
import useStore from '../store'

const HELP_TEXT = `
╔══════════════════════════════════════════════════════╗
║           OsintHAM Web Terminal v0.2.0               ║
╠══════════════════════════════════════════════════════╣
║  Graph Commands:                                     ║
║    help          — Show this help                    ║
║    clear         — Clear terminal                    ║
║    status        — Show investigation status         ║
║    nodes         — List all nodes                    ║
║    edges         — List all edges                    ║
║    stats         — Show graph statistics             ║
║    find <query>  — Search nodes by label             ║
║    export json   — Export as JSON                    ║
╠══════════════════════════════════════════════════════╣
║  OSINT Commands:                                     ║
║    whois <domain>    — WHOIS lookup                  ║
║    dns <domain>      — DNS records                   ║
║    ssl <domain>      — SSL certificate info          ║
║    subdomains <d>    — Subdomain enumeration         ║
║    ping <host>       — Ping host                     ║
║    nslookup <d>      — DNS lookup                    ║
║    ipinfo <ip>       — IP geolocation                ║
║    email <addr>      — Analyze email                 ║
║    phone <num>       — Analyze phone                 ║
║    hash <text>       — Generate hashes               ║
║    base64 <text>     — Base64 encode                 ║
║    decode <text>     — Base64 decode                 ║
║    ghdb <domain>     — Google Hacking DB queries     ║
║    shodan <ip>       — Shodan search link            ║
║    censys <ip>       — Censys search link            ║
║    hibp <email>      — Have I Been Pwned check       ║
║    sherlock <user>   — Sherlock username search      ║
║    maigret <user>    — Maigret username search       ║
║    holehe <email>    — Holehe email check            ║
║    snoop <user>      — Snoop (RU platforms)          ║
║    vk <user>         — VK profile link               ║
║    ok <user>         — OK profile link               ║
║    universal <query> — Universal search links        ║
║    scan <target>     — Full OSINT scan               ║
║    tools             — OSINT tools catalog           ║
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
    const digits = num.replace(/\D/g, '')
    const prefixes = { '1': 'US/Canada', '7': 'RU/KZ', '44': 'UK', '49': 'DE', '86': 'CN', '380': 'UA', '375': 'BY', '91': 'IN' }
    let country = 'Unknown'
    for (const [p, c] of Object.entries(prefixes)) {
      if (digits.startsWith(p)) { country = c; break }
    }
    return `Phone Analysis: ${num}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Digits: ${digits}
Valid: ${digits.length >= 7 && digits.length <= 15 ? 'Yes' : 'No'}
Country: ${country}
[Simulated — install backend for live data]`
  },
  // ── OSINT Commands ──
  dns: (_, args) => {
    const domain = args[1]
    if (!domain) return 'Usage: dns <domain>'
    return `DNS Lookup: ${domain}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  A:     93.184.216.34
  AAAA:  2606:2800:220:1:248:1893:25c8:1946
  MX:    mail.${domain} (priority: 10)
  NS:    ns1.${domain}
  TXT:   v=spf1 include:_spf.google.com ~all
[Simulated — install backend for live DNS]`
  },
  ssl: (_, args) => {
    const domain = args[1]
    if (!domain) return 'Usage: ssl <domain>'
    return `SSL Certificate: ${domain}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Issuer:       Let's Encrypt Authority X3
  Valid From:   2024-01-15
  Valid To:     2024-04-15
  Key Type:     RSA 2048-bit
  Protocol:     TLS 1.3
[Simulated — install backend for live SSL check]`
  },
  subdomains: (_, args) => {
    const domain = args[1]
    if (!domain) return 'Usage: subdomains <domain>'
    return `Subdomain Enumeration: ${domain}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  www.${domain}
  mail.${domain}
  ftp.${domain}
  admin.${domain}
  api.${domain}
  blog.${domain}
  shop.${domain}
  dev.${domain}
  vpn.${domain}
  cdn.${domain}
[Simulated — install backend for live enumeration]`
  },
  ghdb: (_, args) => {
    const domain = args[1]
    if (!domain) return 'Usage: ghdb <domain>'
    return `Google Hacking DB Queries: ${domain}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Emails:    site:${domain} intext:"@" filetype:xls
  Admin:     site:${domain} inurl:admin
  Backups:   site:${domain} filetype:bak | filetype:old
  Config:    site:${domain} filetype:env | filetype:config
  Database:  site:${domain} filetype:sql | filetype:db
  Login:     site:${domain} inurl:login | inurl:signin
  PDFs:      site:${domain} filetype:pdf
  Errors:    site:${domain} intext:"error" | intext:"warning"
  GHDB:      https://www.exploit-db.com/google-hacking-database`
  },
  shodan: (_, args) => {
    const ip = args[1]
    if (!ip) return 'Usage: shodan <ip>'
    return `Shodan Search: ${ip}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Web:       https://www.shodan.io/host/${ip}
  Search:    https://www.shodan.io/search?query=${encodeURIComponent(ip)}
  [Set SHODAN_API_KEY env var for API access]
  [Install backend for live Shodan data]`
  },
  censys: (_, args) => {
    const ip = args[1]
    if (!ip) return 'Usage: censys <ip>'
    return `Censys Search: ${ip}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Hosts:     https://search.censys.io/hosts/${ip}
  Search:    https://search.censys.io/search?q=${encodeURIComponent(ip)}
  [Set CENSYS_API_ID and CENSYS_API_SECRET env vars]`
  },
  hibp: (_, args) => {
    const email = args[1]
    if (!email) return 'Usage: hibp <email>'
    return `Have I Been Pwned: ${email}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Check:     https://haveibeenpwned.com/account/${encodeURIComponent(email)}
  API:       Set HIBP_API_KEY env var
  [Install backend for live HIBP data]`
  },
  sherlock: (_, args) => {
    const user = args[1]
    if (!user) return 'Usage: sherlock <username>'
    return `Sherlock: ${user}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  GitHub:    https://github.com/sherlock-project/sherlock
  Install:   pip install sherlock-project
  Run:       sherlock ${user}
  Sites:     400+ platforms
  Telegram:  @OpenSoucesSearcherUsername_bot`
  },
  maigret: (_, args) => {
    const user = args[1]
    if (!user) return 'Usage: maigret <username>'
    return `Maigret: ${user}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  GitHub:    https://github.com/soxoj/maigret
  Install:   pip install maigret
  Run:       maigret ${user}
  Sites:     1000+ platforms
  [More thorough than Sherlock]`
  },
  holehe: (_, args) => {
    const email = args[1]
    if (!email) return 'Usage: holehe <email>'
    return `Holehe: ${email}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  GitHub:    https://github.com/megadose/holehe
  Install:   pip install holehe
  Run:       holehe ${email}
  Checks:    130+ sites for email registration`
  },
  snoop: (_, args) => {
    const user = args[1]
    if (!user) return 'Usage: snoop <username>'
    return `Snoop: ${user}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  GitHub:    https://github.com/snooppr/snoop
  Focus:     RU social networks (VK, OK, etc.)
  News:      https://myseldon.com
  [Best for Russian-language OSINT]`
  },
  vk: (_, args) => {
    const user = args[1]
    if (!user) return 'Usage: vk <user>'
    return `VKontakte: ${user}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Profile:   https://vk.com/${encodeURIComponent(user)}
  Tool:      https://github.com/AdrianGuretto/OSINTvk
  API:       https://vk.com/dev`
  },
  ok: (_, args) => {
    const user = args[1]
    if (!user) return 'Usage: ok <user>'
    return `Odnoklassniki: ${user}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Profile:   https://ok.ru/profile/${encodeURIComponent(user)}
  Tool:      https://github.com/OSINT-mindset/odnoklassniki-checker`
  },
  universal: (_, args) => {
    const query = args.slice(1).join(' ')
    if (!query) return 'Usage: universal <query>'
    const q = encodeURIComponent(query)
    return `Universal Search: "${query}"
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Google:    https://google.com/search?q=${q}
  DuckDuckGo: https://duckduckgo.com/?q=${q}
  Yandex:    https://yandex.com/search/?text=${q}
  Bing:      https://bing.com/search?q=${q}
  Shodan:    https://shodan.io/search?query=${q}
  Censys:    https://search.censys.io/search?q=${q}
  Wayback:   https://web.archive.org/web/*/${q}
  GHDB:      https://www.exploit-db.com/google-hacking-database`
  },
  scan: (_, args) => {
    const target = args.slice(1).join(' ')
    if (!target) return 'Usage: scan <target>'
    const type = target.includes('@') ? 'email' : /^\d+\.\d+\.\d+\.\d+$/.test(target) ? 'ip' : /\.\w{2,}$/.test(target) ? 'domain' : 'username'
    return `OSINT Scan: ${target}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Type detected: ${type}
  [✓] Format validation
  [✓] Social media check (30+ platforms)
  [✓] DNS records
  [✓] Subdomain enumeration
  [✓] SSL certificate
  [✓] WHOIS lookup
  [⚠] HIBP: API key required
  [⚠] Shodan: API key required
  [Demo mode — install backend for live scanning]`
  },
  tools: () => `OSINT Tools Catalog (40+):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Username Search:
    Sherlock, Maigret, Snoop, Holehe, X-osint, Osintgram

  Email & Breaches:
    HIBP, Holehe, LeakCheck, BreachHound

  DNS & Network:
    DNSDumpster, Shodan, Censys, ExifTool, theHarvester

  Web & Archives:
    Wayback Machine, Google Earth, GHDB

  Frameworks:
    SpiderFoot, Recon-ng, theHarvester, Maltego CE

  Search Engines:
    Intelligence X, Infoooze, Snoop

  Regional (RU/CIS):
    VK Checker, OK Checker, TeleSINT Bot, Глаз Бога

  Face/Image:
    PimEyes

  Libraries:
    Osintplus, Osixr, js-recon, Anastasis, BlackTrace

  Telegram Bots:
    TeleSINT, PRObivon, UsersBox, unamer_search, UniversalSearchBot`,
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
