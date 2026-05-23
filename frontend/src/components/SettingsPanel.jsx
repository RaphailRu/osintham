import React, { useState } from 'react'
import { 
  Settings, X, Save, Moon, Sun, Bell, Save as SaveIcon, 
  Key, Database, Download, Upload, Trash2, RotateCcw,
  Server, Wifi, Shield, Zap
} from 'lucide-react'
import useStore from '../store'
import { getSettings, updateSettings, exportData, importData } from '../api'

export default function SettingsPanel() {
  const { 
    settings, updateSettings, theme, toggleTheme, 
    addNotification, setIsExporting, setIsImporting 
  } = useStore()
  
  const [activeTab, setActiveTab] = useState('general')
  const [isLoading, setIsLoading] = useState(false)
  const [tempSettings, setTempSettings] = useState(settings)
  const [apiKeys, setApiKeys] = useState(settings.apiKeys || {})
  const [scannerConfig, setScannerConfig] = useState(settings.scannerConfig || {})

  const tabs = [
    { id: 'general', label: 'General', icon: Settings },
    { id: 'theme', label: 'Appearance', icon: theme === 'dark' ? Moon : Sun },
    { id: 'api', label: 'API Keys', icon: Key },
    { id: 'scanner', label: 'Scanner', icon: Zap },
    { id: 'data', label: 'Data', icon: Database }
  ]

  const handleSaveSettings = async () => {
    setIsLoading(true)
    try {
      await updateSettings(tempSettings)
      updateSettings(tempSettings)
      addNotification({
        type: 'success',
        title: 'Settings Saved',
        message: 'Your settings have been updated successfully'
      })
    } catch (err) {
      addNotification({
        type: 'error',
        title: 'Save Failed',
        message: 'Failed to save settings: ' + err.message
      })
    } finally {
      setIsLoading(false)
    }
  }

  const handleExport = async () => {
    setIsExporting(true)
    try {
      const data = await exportData()
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `osintham-export-${new Date().toISOString().split('T')[0]}.json`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
      
      addNotification({
        type: 'success',
        title: 'Export Complete',
        message: 'Data exported successfully'
      })
    } catch (err) {
      addNotification({
        type: 'error',
        title: 'Export Failed',
        message: 'Failed to export data: ' + err.message
      })
    } finally {
      setIsExporting(false)
    }
  }

  const handleImport = async (event) => {
    const file = event.target.files[0]
    if (!file) return

    setIsImporting(true)
    try {
      const text = await file.text()
      const data = JSON.parse(text)
      await importData(data)
      
      addNotification({
        type: 'success',
        title: 'Import Complete',
        message: 'Data imported successfully'
      })
    } catch (err) {
      addNotification({
        type: 'error',
        title: 'Import Failed',
        message: 'Failed to import data: ' + err.message
      })
    } finally {
      setIsImporting(false)
      event.target.value = ''
    }
  }

  const resetSettings = () => {
    setTempSettings({
      theme: 'dark',
      autoSave: true,
      notifications: true,
      maxNodes: 1000,
      maxEdges: 5000,
      apiKeys: {},
      scannerConfig: {}
    })
    addNotification({
      type: 'info',
      title: 'Settings Reset',
      message: 'All settings have been reset to defaults'
    })
  }

  return (
    <div className="h-full bg-slate-900 text-white">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-slate-700">
        <h2 className="text-xl font-bold flex items-center gap-2">
          <Settings className="w-5 h-5" />
          Settings
        </h2>
        <div className="flex items-center gap-2">
          <button
            onClick={resetSettings}
            className="px-3 py-1.5 text-sm bg-slate-700 hover:bg-slate-600 rounded-lg transition-colors flex items-center gap-1"
          >
            <RotateCcw className="w-3 h-3" />
            Reset
          </button>
          <button
            onClick={handleSaveSettings}
            disabled={isLoading}
            className="px-4 py-1.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg transition-colors flex items-center gap-2 font-medium"
          >
            {isLoading ? (
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
            ) : (
              <>
                <SaveIcon className="w-4 h-4" />
                Save
              </>
            )}
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-slate-700">
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 px-4 py-3 text-sm font-medium transition-colors ${
              activeTab === tab.id
                ? 'text-blue-400 border-b-2 border-blue-400'
                : 'text-slate-400 hover:text-white hover:bg-slate-800'
            }`}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4">
        {activeTab === 'general' && (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-semibold mb-4">General Settings</h3>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <label className="text-sm font-medium">Auto Save</label>
                    <p className="text-xs text-slate-400">Automatically save changes</p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={tempSettings.autoSave}
                      onChange={(e) => setTempSettings({ ...tempSettings, autoSave: e.target.checked })}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-slate-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                  </label>
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <label className="text-sm font-medium">Notifications</label>
                    <p className="text-xs text-slate-400">Show system notifications</p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={tempSettings.notifications}
                      onChange={(e) => setTempSettings({ ...tempSettings, notifications: e.target.checked })}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-slate-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                  </label>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium">Max Nodes</label>
                    <input
                      type="number"
                      value={tempSettings.maxNodes}
                      onChange={(e) => setTempSettings({ ...tempSettings, maxNodes: parseInt(e.target.value) })}
                      className="w-full mt-1 px-3 py-2 bg-slate-800 border border-slate-600 rounded-lg text-white"
                      min="100"
                      max="10000"
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium">Max Edges</label>
                    <input
                      type="number"
                      value={tempSettings.maxEdges}
                      onChange={(e) => setTempSettings({ ...tempSettings, maxEdges: parseInt(e.target.value) })}
                      className="w-full mt-1 px-3 py-2 bg-slate-800 border border-slate-600 rounded-lg text-white"
                      min="100"
                      max="50000"
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'theme' && (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-semibold mb-4">Appearance</h3>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <label className="text-sm font-medium">Theme</label>
                    <p className="text-xs text-slate-400">Choose your preferred theme</p>
                  </div>
                  <button
                    onClick={toggleTheme}
                    className="flex items-center gap-2 px-4 py-2 bg-slate-800 border border-slate-600 rounded-lg hover:bg-slate-700 transition-colors"
                  >
                    {theme === 'dark' ? (
                      <>
                        <Sun className="w-4 h-4" />
                        Light Theme
                      </>
                    ) : (
                      <>
                        <Moon className="w-4 h-4" />
                        Dark Theme
                      </>
                    )}
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'api' && (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-semibold mb-4">API Keys</h3>
              <div className="space-y-4">
                {Object.entries(apiKeys).map(([service, key]) => (
                  <div key={service} className="space-y-2">
                    <label className="text-sm font-medium flex items-center gap-2">
                      <Key className="w-4 h-4" />
                      {service.charAt(0).toUpperCase() + service.slice(1)} API
                    </label>
                    <input
                      type="password"
                      value={key}
                      onChange={(e) => setApiKeys({ ...apiKeys, [service]: e.target.value })}
                      className="w-full px-3 py-2 bg-slate-800 border border-slate-600 rounded-lg text-white"
                      placeholder={`Enter ${service} API key`}
                    />
                  </div>
                ))}
                
                <button
                  onClick={() => {
                    const newService = prompt('Enter service name:')
                    if (newService) {
                      setApiKeys({ ...apiKeys, [newService]: '' })
                    }
                  }}
                  className="flex items-center gap-2 px-3 py-2 bg-slate-800 border border-slate-600 rounded-lg hover:bg-slate-700 transition-colors text-sm"
                >
                  <Plus className="w-4 h-4" />
                  Add API Key
                </button>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'scanner' && (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-semibold mb-4">Scanner Configuration</h3>
              <div className="space-y-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">Request Timeout (ms)</label>
                  <input
                    type="number"
                    value={scannerConfig.timeout || 30000}
                    onChange={(e) => setScannerConfig({ ...scannerConfig, timeout: parseInt(e.target.value) })}
                    className="w-full px-3 py-2 bg-slate-800 border border-slate-600 rounded-lg text-white"
                    min="1000"
                    max="120000"
                  />
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium">Max Concurrent Requests</label>
                  <input
                    type="number"
                    value={scannerConfig.maxConcurrent || 5}
                    onChange={(e) => setScannerConfig({ ...scannerConfig, maxConcurrent: parseInt(e.target.value) })}
                    className="w-full px-3 py-2 bg-slate-800 border border-slate-600 rounded-lg text-white"
                    min="1"
                    max="20"
                  />
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium">Rate Limit (requests/minute)</label>
                  <input
                    type="number"
                    value={scannerConfig.rateLimit || 60}
                    onChange={(e) => setScannerConfig({ ...scannerConfig, rateLimit: parseInt(e.target.value) })}
                    className="w-full px-3 py-2 bg-slate-800 border border-slate-600 rounded-lg text-white"
                    min="1"
                    max="600"
                  />
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'data' && (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-semibold mb-4">Data Management</h3>
              <div className="space-y-4">
                <div className="flex items-center justify-between p-4 bg-slate-800 rounded-lg border border-slate-600">
                  <div className="flex items-center gap-3">
                    <Download className="w-5 h-5 text-blue-400" />
                    <div>
                      <div className="font-medium">Export Data</div>
                      <div className="text-xs text-slate-400">Download all your investigations and settings</div>
                    </div>
                  </div>
                  <button
                    onClick={handleExport}
                    disabled={isExporting}
                    className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg transition-colors"
                  >
                    {isExporting ? 'Exporting...' : 'Export'}
                  </button>
                </div>

                <div className="flex items-center justify-between p-4 bg-slate-800 rounded-lg border border-slate-600">
                  <div className="flex items-center gap-3">
                    <Upload className="w-5 h-5 text-green-400" />
                    <div>
                      <div className="font-medium">Import Data</div>
                      <div className="text-xs text-slate-400">Upload data from a previous export</div>
                    </div>
                  </div>
                  <label className="px-4 py-2 bg-green-600 hover:bg-green-700 rounded-lg transition-colors cursor-pointer">
                    {isImporting ? 'Importing...' : 'Import'}
                    <input
                      type="file"
                      accept=".json"
                      onChange={handleImport}
                      className="hidden"
                      disabled={isImporting}
                    />
                  </label>
                </div>

                <div className="flex items-center justify-between p-4 bg-slate-800 rounded-lg border border-slate-600">
                  <div className="flex items-center gap-3">
                    <Trash2 className="w-5 h-5 text-red-400" />
                    <div>
                      <div className="font-medium">Clear All Data</div>
                      <div className="text-xs text-slate-400">Permanently delete all investigations and settings</div>
                    </div>
                  </div>
                  <button className="px-4 py-2 bg-red-600 hover:bg-red-700 rounded-lg transition-colors">
                    Clear All
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}