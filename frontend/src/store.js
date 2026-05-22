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

  // Actions
  setInvestigations: (investigations) => set({ investigations }),
  setCurrentInvestigation: (inv) => set({ currentInvestigation: inv }),
  setGraphData: (data) => set({ graphData: data }),
  setSelectedNode: (node) => set({ selectedNode: node }),
  setSelectedEdge: (edge) => set({ selectedEdge: edge }),
  setTemplates: (templates) => set({ templates }),
  setActiveTab: (tab) => set({ activeTab: tab }),
  setSidebarOpen: (open) => set({ sidebarOpen: open }),

  addLog: (message) => set((state) => ({
    logEntries: [...state.logEntries, { time: new Date(), message }]
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
