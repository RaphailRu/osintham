import React, { useEffect, useRef, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { ArrowLeft, Trash2 } from 'lucide-react'
import useStore from '../store'

const HELP = `
╔══════════════════════════════════════════════════════╗
║        OsintHAM Веб-Терминал v0.5.2                  ║
╠══════════════════════════════════════════════════════╣
║  Команды графа:                                      ║
║    help           — Показать эту справку             ║
║    clear          — Очистить терминал                ║
║    status         — Статус расследования             ║
║    nodes          — Список всех узлов                ║
║    edges          — Список всех связей               ║
║    stats          — Статистика графа                 ║
║    find <запрос>  — Поиск узлов по названию          ║
╠══════════════════════════════════════════════════════╣
║  OSINT команды:                                      ║
║    whois <домен>     — WHOIS информация              ║
║    dns <домен>       — DNS записи                    ║
║    ssl <домен>       — SSL сертификат                ║
║    ping <хост>       — Пинг хоста                    ║
║    hash <текст>      — Генерация хешей               ║
║    base64 <текст>    — Base64 кодирование            ║
║    decode <текст>    — Base64 декодирование          ║
║    ipinfo <ip>       — Информация об IP              ║
║    email <адрес>     — Анализ email                  ║
║    phone <номер>     — Анализ телефона               ║
║    ghdb <домен>      — Google Hacking DB запросы     ║
║    sherlock <ник>    — Поиск по нику (Sherlock)      ║
║    maigret <ник>     — Поиск по нику (Maigret)       ║
║    tools             — Каталог OSINT инструментов    ║
║    scan <цель>       — Полное OSINT сканирование     ║
╚══════════════════════════════════════════════════════╝`

const COMMANDS = {
  help: () => HELP,
  clear: '__CLEAR__',
  status: (s) => { const i=s.currentInvestigation,g=s.graphData; return `Расследование: ${i?.title||'Нет'}\nСтатус: ${i?.status||'N/A'}\nУзлы: ${g?.nodes?.length||0}\nСвязи: ${g?.edges?.length||0}` },
  nodes: (s) => { const n=s.graphData?.nodes||[]; return n.length? n.map(x=>`  [${x.type}] ${x.label} (доверие:${x.trust_level}/5)`).join('\n'):'Нет узлов' },
  edges: (s) => { const e=s.graphData?.edges||[]; return e.length? e.map(x=>`  ${x.from?.slice(0,8)} → ${x.to?.slice(0,8)} [${x.label||'связан'}]`).join('\n'):'Нет связей' },
  stats: (s) => { const st=s.graphData?.stats||{}; return `Статистика:\n  Узлы: ${st.node_count||0}\n  Связи: ${st.edge_count||0}\n  Плотность: ${st.density||0}` },
  find: (s,a) => { const q=a.slice(1).join(' ').toLowerCase(); if(!q) return 'Использование: find <запрос>'; const m=(s.graphData?.nodes||[]).filter(n=>n.label.toLowerCase().includes(q)); return m.length? m.map(n=>`  [${n.type}] ${n.label}`).join('\n') : `Нет совпадений для "${q}"` },
  whois: (_,a) => { if(!a[1]) return 'Использование: whois <домен>'; return `WHOIS: ${a[1]}\nРегистратор: Example Inc.\nСоздан: 2020-01-15\nСтатус: active\n[Демо]` },
  dns: (_,a) => { if(!a[1]) return 'Использование: dns <домен>'; return `DNS: ${a[1]}\nA: 93.184.216.34\nMX: mail.${a[1]}\nNS: ns1.${a[1]}\n[Демо]` },
  ssl: (_,a) => { if(!a[1]) return 'Использование: ssl <домен>'; return `SSL: ${a[1]}\nИздатель: Let's Encrypt\nДействует: 2024-01-15 → 2024-04-15\nКлюч: RSA 2048-bit\n[Демо]` },
  ping: (_,a) => { if(!a[1]) return 'Использование: ping <хост>'; return `PING ${a[1]}: 64 байт, 12.3мс\n[Демо]` },
  hash: (_,a) => { const t=a.slice(1).join(' '); if(!t) return 'Использование: hash <текст>'; let h=0;for(let i=0;i<t.length;i++){h=((h<<5)-h)+t.charCodeAt(i);h=h&h;} return `Хеш: "${t}"\nMD5: ${Math.abs(h).toString(16).padStart(32,'0')}\n[Демо]` },
  base64: (_,a) => { const t=a.slice(1).join(' '); if(!t) return 'Использование: base64 <текст>'; try{return `Base64: ${btoa(t)}`;}catch{return 'Ошибка: используйте ASCII';} },
  decode: (_,a) => { const t=a.slice(1).join(' '); if(!t) return 'Использование: decode <base64>'; try{return `Декодировано: ${atob(t)}`;}catch{return 'Ошибка: невалидный Base64';} },
  ipinfo: (_,a) => { if(!a[1]) return 'Использование: ipinfo <ip>'; return `IP: ${a[1]}\nСтрана: US\nГород: New York\nПровайдер: Example Corp\n[Демо]` },
  email: (_,a) => { if(!a[1]) return 'Использование: email <адрес>'; const[u,d]=a[1].split('@'); return `Email: ${a[1]}\nПользователь: ${u||'N/A'}\nДомен: ${d||'N/A'}\n[Демо]` },
  phone: (_,a) => { if(!a[1]) return 'Использование: phone <номер>'; return `Телефон: ${a[1]}\nСтрана: +1\nТип: Мобильный\n[Демо]` },
  ghdb: (_,a) => { if(!a[1]) return 'Использование: ghdb <домен>'; return `GHDB запросы для ${a[1]}:\n  Email: site:${a[1]} intext:"@" filetype:xls\n  Админ: site:${a[1]} inurl:admin\n  Бэкапы: site:${a[1]} filetype:bak\n  GHDB: https://www.exploit-db.com/google-hacking-database` },
  sherlock: (_,a) => { if(!a[1]) return 'Использование: sherlock <ник>'; return `Sherlock: ${a[1]}\nGitHub: sherlock-project/sherlock\nУстановка: pip install sherlock-project\nЗапуск: sherlock ${a[1]}\nПлатформы: 400+` },
  maigret: (_,a) => { if(!a[1]) return 'Использование: maigret <ник>'; return `Maigret: ${a[1]}\nGitHub: soxoj/maigret\nУстановка: pip install maigret\nЗапуск: maigret ${a[1]}\nПлатформы: 1000+` },
  tools: () => `OSINT Инструменты (40+):
  Поиск по нику: Sherlock, Maigret, Snoop, Holehe
  Email/Утечки: HIBP, Holehe, LeakCheck, BreachHound
  DNS/Сеть: DNSDumpster, Shodan, Censys, ExifTool
  Веб: Wayback Machine, Google Earth, GHDB
  Фреймворки: SpiderFoot, Recon-ng, theHarvester
  Региональные: VK, OK, TeleSINT, Глаз Бога
  Лицо: PimEyes
  Библиотеки: Osintplus, Osixr, js-recon`,
  scan: (_,a) => { const t=a.slice(1).join(' '); if(!t) return 'Использование: scan <цель>'; const type=t.includes('@')?'email':/^\d+\.\d+\.\d+\.\d+$/.test(t)?'ip':/\.\w{2,}$/.test(t)?'domain':'username'; return `Сканирование: ${t}\nТип: ${type}\n[✓] Валидация формата\n[✓] Проверка соцсетей\n[✓] DNS записи\n[✓] SSL сертификат\n[✓] WHOIS\n[Демо режим]` },
}

export default function TerminalPage() {
  const { id } = useParams()
  const { currentInvestigation, graphData, addLog } = useStore()
  const [history, setHistory] = useState([{ type: 'system', text: HELP }])
  const [input, setInput] = useState('')
  const scrollRef = useRef(null)

  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight
  }, [history])

  const executeCommand = (cmd) => {
    const trimmed = cmd.trim()
    if (!trimmed) return
    const parts = trimmed.split(/\s+/)
    const cmdName = parts[0].toLowerCase()
    setHistory(prev => [...prev.slice(-1000), { type: 'input', text: trimmed }])
    const handler = COMMANDS[cmdName]
    if (handler) {
      const result = handler({ currentInvestigation, graphData }, parts)
      if (result === '__CLEAR__') { setHistory([]); return }
      setHistory(prev => [...prev.slice(-1000), { type: 'output', text: result }])
    } else {
      setHistory(prev => [...prev.slice(-1000), { type: 'error', text: `Команда не найдена: ${cmdName}. Введите 'help'.` }])
    }
    addLog(`Терминал: ${trimmed}`)
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') { executeCommand(input); setInput('') }
  }

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center gap-4 px-4 py-2 bg-[#1e293b] border-b border-[#334155]">
        <Link to={`/investigation/${id}`} className="p-1.5 rounded hover:bg-[#334155] text-[#94a3b8]">
          <ArrowLeft className="w-4 h-4" />
        </Link>
        <span className="text-sm text-[#94a3b8]">Терминал</span>
        <span className="text-xs text-[#64748b]">— {currentInvestigation?.title || 'Нет расследования'}</span>
        <div className="flex-1" />
        <button onClick={() => setHistory([{ type: 'system', text: HELP }])}
          className="p-1.5 rounded hover:bg-[#334155] text-[#64748b]" title="Очистить">
          <Trash2 className="w-4 h-4" />
        </button>
      </div>
      <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 font-mono text-sm"
        style={{ background: '#0a0a1a', color: '#22c55e' }}
        onClick={() => document.getElementById('terminal-input')?.focus()}>
        {history.map((entry, i) => (
          <div key={i} className={`whitespace-pre-wrap mb-1 ${
            entry.type === 'input' ? 'text-[#818cf8]' :
            entry.type === 'error' ? 'text-red-400' :
            entry.type === 'system' ? 'text-[#64748b]' : 'text-[#22c55e]'
          }`}>
            {entry.type === 'input' && <span className="text-[#6366f1]">❯ </span>}
            {entry.text}
          </div>
        ))}
        <div className="flex items-center text-[#818cf8]">
          <span className="text-[#6366f1]">❯ </span>
          <input id="terminal-input" type="text" value={input} onChange={e => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            className="flex-1 bg-transparent outline-none text-[#22c55e] caret-[#6366f1]"
            autoFocus spellCheck={false} />
        </div>
      </div>
    </div>
  )
}
