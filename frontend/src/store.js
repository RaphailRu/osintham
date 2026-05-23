import { create } from 'zustand'

const useStore = create((set, get) => ({
  // State
  investigations: [],
  currentInvestigation: null,
  graphData: { nodes: [], edges: [], stats: {}, centrality: {}, communities: [] },
  selectedNode: null,
  selectedEdge: null,
  logEntries: [],
  templates: [],
  sidebarOpen: true,
  activeTab: 'graph', // graph, nodes, edges, reports, terminal
  
  // UI State
  theme: 'dark', // dark, light
  loading: false,
  errors: [],
  notifications: [],
  searchQuery: '',
  activeToolsTab: 'scanner', // scanner, catalog, settings
  toolsFilter: '',
  
  // Settings
  settings: {
    apiKeys: {},
    scannerConfig: {},
    theme: 'dark',
    autoSave: true,
    notifications: true,
    maxNodes: 1000,
    maxEdges: 5000
  },
  
  // Recent Investigations
  recentInvestigations: [],
  favorites: [],
  
  // Export/Import
  exportFormat: 'json', // json, csv, pdf
  isExporting: false,
  isImporting: false,

  // Actions
  setInvestigations: (investigations) => set({ investigations }),
  setCurrentInvestigation: (inv) => set({ currentInvestigation: inv }),
  setGraphData: (data) => set({ graphData: data }),
  setSelectedNode: (node) => set({ selectedNode: node }),
  setSelectedEdge: (edge) => set({ selectedEdge: edge }),
  setTemplates: (templates) => set({ templates }),
  setActiveTab: (tab) => set({ activeTab: tab }),
  setSidebarOpen: (open) => set({ sidebarOpen: open }),
  
  // Theme Actions
  setTheme: (theme) => set({ theme }),
  toggleTheme: () => set((state) => ({ theme: state.theme === 'dark' ? 'light' : 'dark' })),
  
  // Loading Actions
  setLoading: (loading) => set({ loading }),
  setIsExporting: (isExporting) => set({ isExporting }),
  setIsImporting: (isImporting) => set({ isImporting }),
  
  // Error Handling
  addError: (error) => set((state) => ({ 
    errors: [...state.errors, { id: Date.now(), message: error, timestamp: new Date() }].slice(-50)
  })),
  clearErrors: () => set({ errors: [] }),
  removeError: (id) => set((state) => ({ 
    errors: state.errors.filter(err => err.id !== id)
  })),
  
  // Notifications
  addNotification: (notification) => set((state) => ({ 
    notifications: [...state.notifications, { 
      id: Date.now(), 
      ...notification, 
      timestamp: new Date() 
    }]
  })),
  removeNotification: (id) => set((state) => ({ 
    notifications: state.notifications.filter(notif => notif.id !== id)
  })),
  clearNotifications: () => set({ notifications: [] }),
  
  // Search
  setSearchQuery: (query) => set({ searchQuery: query }),
  
  // Tools
  setActiveToolsTab: (tab) => set({ activeToolsTab: tab }),
  setToolsFilter: (filter) => set({ toolsFilter: filter }),
  
  // Settings
  updateSettings: (newSettings) => set((state) => ({
    settings: { ...state.settings, ...newSettings }
  })),
  setApiKeys: (apiKeys) => set((state) => ({
    settings: { ...state.settings, apiKeys }
  })),
  setScannerConfig: (config) => set((state) => ({
    settings: { ...state.settings, scannerConfig: config }
  })),
  
  // Recent Investigations
  addRecentInvestigation: (inv) => set((state) => ({
    recentInvestigations: [inv, ...state.recentInvestigations.filter(r => r.id !== inv.id)].slice(0, 10)
  })),
  
  // Favorites
  addFavorite: (inv) => set((state) => ({
    favorites: [...state.favorites.filter(f => f.id !== inv.id), inv]
  })),
  removeFavorite: (id) => set((state) => ({
    favorites: state.favorites.filter(f => f.id !== id)
  })),
  toggleFavorite: (id) => set((state) => {
    const inv = state.investigations.find(i => i.id === id)
    if (!inv) return state
    const isFavorite = state.favorites.some(f => f.id === id)
    return isFavorite 
      ? { favorites: state.favorites.filter(f => f.id !== id) }
      : { favorites: [...state.favorites, inv] }
  }),
  
  // Export/Import
  setExportFormat: (format) => set({ exportFormat: format }),

  // Log Actions
  addLog: (message) => set((state) => ({
    logEntries: [...state.logEntries, { time: new Date(), message }].slice(-500)
  })),

  clearLog: () => set({ logEntries: [] }),

  // Add node to local graph
  addNodeToGraph: (node) => set((state) => ({
    graphData: {
      ...state.graphData,
      nodes: [...state.graphData.nodes, node],
    }
  })),

  // Add edge to local graph
  addEdgeToGraph: (edge) => set((state) => ({
    graphData: {
      ...state.graphData,
      edges: [...state.graphData.edges, edge],
    }
  })),

  // Remove node from local graph
  removeNodeFromGraph: (nodeId) => set((state) => ({
    graphData: {
      ...state.graphData,
      nodes: state.graphData.nodes.filter(n => n.id !== nodeId),
      edges: state.graphData.edges.filter(e => e.from !== nodeId && e.to !== nodeId),
    }
  })),

  // Remove edge from local graph
  removeEdgeFromGraph: (edgeId) => set((state) => ({
    graphData: {
      ...state.graphData,
      edges: state.graphData.edges.filter(e => e.id !== edgeId),
    }
  })),
}))

export default useStore