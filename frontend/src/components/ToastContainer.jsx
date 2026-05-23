import React, { useEffect, useState } from 'react'
import { X, CheckCircle, AlertCircle, AlertTriangle, Info } from 'lucide-react'
import useStore from '../store'

export default function ToastContainer() {
  const { notifications, removeNotification } = useStore()
  
  const getIcon = (type) => {
    switch (type) {
      case 'success': return <CheckCircle className="w-4 h-4" />
      case 'error': return <AlertCircle className="w-4 h-4" />
      case 'warning': return <AlertTriangle className="w-4 h-4" />
      case 'info': default: return <Info className="w-4 h-4" />
    }
  }

  const getBgColor = (type) => {
    switch (type) {
      case 'success': return 'bg-green-500/90'
      case 'error': return 'bg-red-500/90'
      case 'warning': return 'bg-yellow-500/90'
      case 'info': default: return 'bg-blue-500/90'
    }
  }

  useEffect(() => {
    const timer = setTimeout(() => {
      if (notifications.length > 0) {
        removeNotification(notifications[0].id)
      }
    }, 5000)

    return () => clearTimeout(timer)
  }, [notifications, removeNotification])

  if (notifications.length === 0) return null

  return (
    <div className="fixed top-4 right-4 z-50 space-y-2">
      {notifications.map((notification) => (
        <div
          key={notification.id}
          className={`${getBgColor(notification.type)} text-white px-4 py-3 rounded-lg shadow-lg backdrop-blur-sm animate-slide-in-right flex items-center gap-3 min-w-[300px] max-w-md`}
        >
          {getIcon(notification.type)}
          <div className="flex-1">
            <div className="font-medium text-sm">{notification.title}</div>
            <div className="text-xs opacity-90">{notification.message}</div>
          </div>
          <button
            onClick={() => removeNotification(notification.id)}
            className="text-white/70 hover:text-white transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      ))}
    </div>
  )
}