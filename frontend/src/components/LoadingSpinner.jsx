import React from 'react'
import { Loader2 } from 'lucide-react'

export default function LoadingSpinner({ size = 'md', className = '' }) {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-6 h-6',
    lg: 'w-8 h-8',
    xl: 'w-12 h-12'
  }

  return (
    <Loader2 className={`animate-spin ${sizeClasses[size]} ${className}`} />
  )
}

export function LoadingOverlay({ message = 'Loading...' }) {
  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
      <div className="bg-slate-800 rounded-lg p-6 flex flex-col items-center gap-3 border border-slate-600">
        <LoadingSpinner size="lg" />
        <span className="text-white text-sm">{message}</span>
      </div>
    </div>
  )
}

export function LoadingCard({ message = 'Loading...' }) {
  return (
    <div className="flex items-center justify-center p-8">
      <div className="flex flex-col items-center gap-3">
        <LoadingSpinner size="md" />
        <span className="text-slate-400 text-sm">{message}</span>
      </div>
    </div>
  )
}