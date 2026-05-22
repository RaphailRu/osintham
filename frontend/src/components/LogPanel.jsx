import React, { useRef, useEffect } from 'react'
import { Trash2 } from 'lucide-react'
import useStore from '../store'

export default function LogPanel() {
  const logEntries = useStore(s => s.logEntries)
  const clearLog = useStore(s => s.clearLog)
  const scrollRef = useRef(null)

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [logEntries])

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-3 py-2 border-b border-[#334155]">
        <span className="text-xs font-semibold text-[#64748b] uppercase tracking-wider">Activity Log</span>
        <button
          onClick={clearLog}
          className="p-1 rounded hover:bg-[#334155] text-[#64748b] hover:text-white"
          title="Clear log"
        >
          <Trash2 className="w-3 h-3" />
        </button>
      </div>
      <div ref={scrollRef} className="flex-1 overflow-y-auto p-3 log-panel" style={{ fontFamily: 'monospace', fontSize: '11px' }}>
        {logEntries.length === 0 ? (
          <div className="text-[#475569] text-center py-4">
            No activity yet. Start building your graph.
          </div>
        ) : (
          logEntries.map((entry, i) => (
            <div key={i} className="log-entry">
              <span className="log-time">[{entry.time.toLocaleTimeString()}]</span>
              {entry.message}
            </div>
          ))
        )}
      </div>
    </div>
  )
}
