import React, { useState } from 'react'
import {
  Search, Filter, Star, Download, Play, Pause,
  Settings, Zap, Globe, Mail, Phone, User, Building,
  Hash, Calendar, FileText, Link as LinkIcon, Database,
  Eye, Edit, Trash2, Network, X
} from 'lucide-react'
import useStore from '../store'

const TOOLS_CATEGORIES = [
  {
    id: 'osint',
    name: 'OSINT Tools',
    icon: Zap,
    color: 'text-blue-400',
    bgColor: 'bg-blue-500/20',
    tools: [
      { id: 'email_finder', name: 'Email Finder', icon: Mail, description: 'Find email addresses associated with domains', category: 'recon' },
      { id: 'phone_lookup', name: 'Phone Lookup', icon: Phone, description: 'Get information from phone numbers', category: 'recon' },
      { id: 'social_search', name: 'Social Media Search', icon: Globe, description: 'Search across social platforms', category: 'recon' },
      { id: 'domain_whois', name: 'Domain WHOIS', icon: Database, description: 'Get domain registration information', category: 'recon' },
      { id: 'ip_geolocation', name: 'IP Geolocation', icon: Hash, description: 'Get location and ISP info for IP addresses', category: 'recon' },
      { id: 'people_search', name: 'People Search', icon: User, description: 'Find information about individuals', category: 'recon' },
      { id: 'company_search', name: 'Company Search', icon: Building, description: 'Business and corporate information', category: 'recon' },
      { id: 'document_search', name: 'Document Search', icon: FileText, description: 'Search for public documents and records', category: 'recon' }
    ]
  },
  {
    id: 'analysis',
    name: 'Analysis Tools',
    icon: Database,
    color: 'text-green-400',
    bgColor: 'bg-green-500/20',
    tools: [
      { id: 'relationship_analysis', name: 'Relationship Analysis', icon: Network, description: 'Analyze connections between entities', category: 'analysis' },
      { id: 'timeline_analysis', name: 'Timeline Analysis', icon: Calendar, description: 'Create and analyze event timelines', category: 'analysis' },
      { id: 'sentiment_analysis', name: 'Sentiment Analysis', icon: Eye, description: 'Analyze text sentiment and emotion', category: 'analysis' },
      { id: 'pattern_detection', name: 'Pattern Detection', icon: Hash, description: 'Find patterns in data and relationships', category: 'analysis' }
    ]
  },
  {
    id: 'automation',
    name: 'Automation Tools',
    icon: Settings,
    color: 'text-purple-400',
    bgColor: 'bg-purple-500/20',
    tools: [
      { id: 'web_scraper', name: 'Web Scraper', icon: Globe, description: 'Extract data from websites', category: 'automation' },
      { id: 'data_exporter', name: 'Data Exporter', icon: Download, description: 'Export investigation data', category: 'automation' },
      { id: 'report_generator', name: 'Report Generator', icon: FileText, description: 'Generate investigation reports', category: 'automation' },
      { id: 'workflow_automation', name: 'Workflow Automation', icon: Play, description: 'Automate repetitive tasks', category: 'automation' }
    ]
  }
]

export default function ToolsCatalog() {
  const { 
    toolsFilter, setToolsFilter, activeToolsTab, setActiveToolsTab,
    addNotification, addLog 
  } = useStore()
  
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedCategory, setSelectedCategory] = useState('all')
  const [selectedTool, setSelectedTool] = useState(null)
  const [favorites, setFavorites] = useState([])

  const filteredTools = TOOLS_CATEGORIES
    .filter(category => selectedCategory === 'all' || category.id === selectedCategory)
    .flatMap(category => 
      category.tools.filter(tool =>
        tool.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        tool.description.toLowerCase().includes(searchQuery.toLowerCase())
      )
    )

  const toggleFavorite = (toolId) => {
    const isFavorite = favorites.includes(toolId)
    if (isFavorite) {
      setFavorites(favorites.filter(id => id !== toolId))
    } else {
      setFavorites([...favorites, toolId])
    }
  }

  const runTool = (tool) => {
    addNotification({
      type: 'info',
      title: 'Tool Started',
      message: `Started ${tool.name} tool`
    })
    addLog(`Started tool: ${tool.name}`)
    // Here you would implement the actual tool execution logic
  }

  const ToolCard = ({ tool, category }) => {
    const isFavorite = favorites.includes(tool.id)
    
    return (
      <div className="bg-slate-800 border border-slate-700 rounded-lg p-4 hover:border-slate-600 transition-all hover:shadow-lg">
        <div className="flex items-start justify-between mb-3">
          <div className={`p-2 rounded-lg ${category.bgColor}`}>
            <tool.icon className={`w-5 h-5 ${category.color}`} />
          </div>
          <div className="flex items-center gap-1">
            <button
              onClick={() => toggleFavorite(tool.id)}
              className="p-1 rounded hover:bg-slate-700 text-slate-400 hover:text-yellow-400 transition-colors"
            >
              <Star className={`w-4 h-4 ${isFavorite ? 'fill-yellow-400 text-yellow-400' : ''}`} />
            </button>
          </div>
        </div>

        <h3 className="font-semibold text-white mb-2">{tool.name}</h3>
        <p className="text-slate-400 text-sm mb-3 line-clamp-2">{tool.description}</p>

        <div className="flex items-center gap-2 mb-3">
          <span className="px-2 py-1 bg-slate-700 text-slate-300 text-xs rounded-full">
            {tool.category}
          </span>
        </div>

        <div className="flex gap-2">
          <button
            onClick={() => runTool(tool)}
            className="flex-1 flex items-center gap-2 px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm transition-colors"
          >
            <Play className="w-3 h-3" />
            Run
          </button>
          <button className="p-2 bg-slate-700 hover:bg-slate-600 text-slate-400 hover:text-white rounded-lg transition-colors">
            <Settings className="w-3 h-3" />
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="h-full bg-slate-900 text-white">
      {/* Header */}
      <div className="p-6 border-b border-slate-700">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-bold">Tools Catalog</h2>
          <div className="flex items-center gap-2">
            <button className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm transition-colors">
              <Download className="w-4 h-4 inline mr-2" />
              Export Config
            </button>
          </div>
        </div>

        {/* Search and Filters */}
        <div className="flex gap-3">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
            <input
              type="text"
              placeholder="Search tools..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-3 py-2 bg-slate-800 border border-slate-600 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
            />
          </div>
          <div className="relative">
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="px-3 py-2 bg-slate-800 border border-slate-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
            >
              <option value="all">All Categories</option>
              {TOOLS_CATEGORIES.map(category => (
                <option key={category.id} value={category.id}>{category.name}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Categories Navigation */}
      <div className="px-6 py-3 border-b border-slate-700">
        <div className="flex gap-2 overflow-x-auto">
          <button
            onClick={() => setActiveToolsTab('catalog')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              activeToolsTab === 'catalog'
                ? 'bg-blue-600 text-white'
                : 'bg-slate-800 text-slate-400 hover:text-white hover:bg-slate-700'
            }`}
          >
            Tools
          </button>
          <button
            onClick={() => setActiveToolsTab('favorites')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-2 ${
              activeToolsTab === 'favorites'
                ? 'bg-blue-600 text-white'
                : 'bg-slate-800 text-slate-400 hover:text-white hover:bg-slate-700'
            }`}
          >
            <Star className={`w-4 h-4 ${favorites.length > 0 ? 'fill-yellow-400 text-yellow-400' : ''}`} />
            Favorites ({favorites.length})
          </button>
          <button
            onClick={() => setActiveToolsTab('history')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              activeToolsTab === 'history'
                ? 'bg-blue-600 text-white'
                : 'bg-slate-800 text-slate-400 hover:text-white hover:bg-slate-700'
            }`}
          >
            Recent Tools
          </button>
        </div>
      </div>

      {/* Tools Grid */}
      <div className="flex-1 overflow-y-auto p-6">
        {activeToolsTab === 'favorites' ? (
          <div>
            <h3 className="text-lg font-semibold mb-4">Favorite Tools</h3>
            {favorites.length === 0 ? (
              <div className="text-center py-12 text-slate-500">
                <Star className="w-12 h-12 mx-auto mb-3 opacity-50" />
                <p>No favorite tools yet</p>
                <p className="text-sm">Click the star icon on any tool to add it to favorites</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {TOOLS_CATEGORIES
                  .flatMap(category => category.tools)
                  .filter(tool => favorites.includes(tool.id))
                  .map(tool => {
                    const category = TOOLS_CATEGORIES.find(c => c.tools.some(t => t.id === tool.id))
                    return (
                      <ToolCard key={tool.id} tool={tool} category={category} />
                    )
                  })}
              </div>
            )}
          </div>
        ) : (
          <div>
            <h3 className="text-lg font-semibold mb-4">
              {selectedCategory === 'all' ? 'All Tools' : TOOLS_CATEGORIES.find(c => c.id === selectedCategory)?.name}
              <span className="text-slate-500 text-sm font-normal ml-2">
                ({filteredTools.length} tools)
              </span>
            </h3>
            
            {filteredTools.length === 0 ? (
              <div className="text-center py-12 text-slate-500">
                <Search className="w-12 h-12 mx-auto mb-3 opacity-50" />
                <p>No tools found matching your search</p>
                <p className="text-sm">Try adjusting your search terms or filters</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {filteredTools.map(tool => {
                  const category = TOOLS_CATEGORIES.find(c => c.tools.some(t => t.id === tool.id))
                  return (
                    <ToolCard key={tool.id} tool={tool} category={category} />
                  )
                })}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Tool Detail Modal */}
      {selectedTool && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
          <div className="bg-slate-800 rounded-xl p-6 w-full max-w-2xl max-h-[80vh] overflow-y-auto border border-slate-600">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-bold">{selectedTool.name}</h3>
              <button
                onClick={() => setSelectedTool(null)}
                className="p-1 rounded hover:bg-slate-700 text-slate-400 hover:text-white transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-blue-500/20">
                  <selectedTool.icon className="w-6 h-6 text-blue-400" />
                </div>
                <div>
                  <span className="text-slate-400">Category:</span>
                  <span className="ml-2">OSINT Tools</span>
                </div>
              </div>

              <div>
                <h4 className="font-semibold mb-2">Description</h4>
                <p className="text-slate-400">{selectedTool.description}</p>
              </div>

              <div>
                <h4 className="font-semibold mb-2">Configuration</h4>
                <div className="bg-slate-700 rounded-lg p-4 space-y-3">
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="text-sm text-slate-400">Timeout (seconds)</label>
                      <input
                        type="number"
                        defaultValue="30"
                        className="w-full mt-1 px-3 py-2 bg-slate-800 border border-slate-600 rounded-lg text-white"
                      />
                    </div>
                    <div>
                      <label className="text-sm text-slate-400">Max Results</label>
                      <input
                        type="number"
                        defaultValue="10"
                        className="w-full mt-1 px-3 py-2 bg-slate-800 border border-slate-600 rounded-lg text-white"
                      />
                    </div>
                  </div>
                </div>
              </div>

              <div className="flex gap-3 pt-4">
                <button
                  onClick={() => {
                    runTool(selectedTool)
                    setSelectedTool(null)
                  }}
                  className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
                >
                  Run Tool
                </button>
                <button
                  onClick={() => setSelectedTool(null)}
                  className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}