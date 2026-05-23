import React from 'react'

const TRUST_LABELS = {
  1: { text: 'Rumor', color: 'bg-red-500' },
  2: { text: 'Dubious', color: 'bg-orange-500' },
  3: { text: 'Uncertain', color: 'bg-yellow-500' },
  4: { text: 'Reliable', color: 'bg-green-400' },
  5: { text: 'Verified', color: 'bg-green-500' },
}

export default function TrustBadge({ level }) {
  const info = TRUST_LABELS[level] || TRUST_LABELS[3]
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium text-white ${info.color}`}>
      {'⭐'.repeat(level)} {info.text}
    </span>
  )
}
