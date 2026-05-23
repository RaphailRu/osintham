import React, { useEffect, useRef, useState, useCallback } from 'react'
import { useParams } from 'react-router-dom'
import cytoscape from 'cytoscape'
import dagre from 'cytoscape-dagre'
import dagreLib from 'dagre'
import {
  Plus, ZoomIn, ZoomOut, Maximize2, X, Save,
  User, Mail, Phone, Globe, Building, Hash, Calendar, FileText, Link as LinkIcon
} from 'lucide-react'
import useStore from '../store'
import { getGraph, createNode, createEdge, deleteNode, deleteEdge, getTemplates } from '../api'
import NodeEditor from '../components/NodeEditor'
import EdgeEditor from '../components/EdgeEditor'
import LogPanel from '../components/LogPanel'
import TrustBadge from '../components/TrustBadge'
import OsintScanner from '../components/OsintScanner'

cytoscape.use(dagre)

const NODE_ICONS = {
  person: User,
  email: Mail,
  phone: Phone,
  social_account: Globe,
  organization: Building,
  domain: Globe,
  ip: Hash,
  event: Calendar,
  document: FileText,
}

const NODE_COLORS = {
  person: '#8b5cf6',
  email: '#ef4444',
  phone: '#f97316',
  social_account: '#10b981',
  organization: '#06b6d4',
  domain: '#f59e0b',
  ip: '#ec4899',
  event: '#6366f1',
  document: '#64748b',
}

export default function Investigation() {
  const { id } = useParams()
  const cyRef = useRef(null)
  const containerRef = useRef(null)
  const {
    graphData, setGraphData, selectedNode, setSelectedNode,
    selectedEdge, setSelectedEdge, addLog, templates, setTemplates
  } = useStore()

  const [showNodeEditor, setShowNodeEditor] = useState(false)
  const [showEdgeEditor, setShowEdgeEditor] = useState(false)
  const [editingNode, setEditingNode] = useState(null)
  const [connectingFrom, setConnectingFrom] = useState(null)

  // Load graph data
  const loadGraph = useCallback(async () => {
    try {
      const res = await getGraph(id)
      setGraphData(res.data)
      addLog(`Graph loaded: ${res.data.nodes?.length || 0} nodes, ${res.data.edges?.length || 0} edges`)
    } catch (err) {
      addLog(`Error loading graph: ${err.message}`)
    }
  }, [id])

  useEffect(() => {
    loadGraph()
    if (templates.length === 0) {
      getTemplates().then(res => setTemplates(res.data))
    }
  }, [])

  // Initialize Cytoscape
  useEffect(() => {
    if (!containerRef.current || !graphData.nodes?.length) return

    const elements = []
    graphData.nodes.forEach(n => {
      elements.push({
        data: {
          id: n.id,
          label: n.label,
          type: n.type,
          trust_level: n.trust_level,
          color: NODE_COLORS[n.type] || '#6366f1',
          ...n,
        }
      })
    })
    graphData.edges.forEach(e => {
      elements.push({
        data: {
          id: e.id,
          source: e.from,
          target: e.to,
          label: e.label,
          trust_level: e.trust_level,
          ...e,
        }
      })
    })

    const cy = cytoscape({
      container: containerRef.current,
      elements,
      style: [
        {
          selector: 'node',
          style: {
            'background-color': 'data(color)',
            'label': 'data(label)',
            'text-valign': 'center',
            'text-halign': 'center',
            'color': '#fff',
            'font-size': '11px',
            'text-outline-color': '#000',
            'text-outline-width': '2px',
            'width': 40,
            'height': 40,
            'border-width': 2,
            'border-color': '#fff',
          }
        },
        {
          selector: 'node:selected',
          style: {
            'border-width': 4,
            'border-color': '#fbbf24',
            'width': 50,
            'height': 50,
          }
        },
        {
          selector: 'edge',
          style: {
            'width': 2,
            'line-color': '#475569',
            'target-arrow-color': '#475569',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier',
            'label': 'data(label)',
            'font-size': '9px',
            'color': '#94a3b8',
            'text-background-color': '#1e293b',
            'text-background-opacity': 1,
            'text-background-padding': '2px',
          }
        },
        {
          selector: 'edge:selected',
          style: {
            'width': 3,
            'line-color': '#6366f1',
            'target-arrow-color': '#6366f1',
          }
        },
      ],
      layout: {
        name: 'dagre',
        rankDir: 'TB',
        nodeSep: 60,
        rankSep: 80,
        padding: 30,
      },
      minZoom: 0.3,
      maxZoom: 3,
      wheelSensitivity: 0.3,
    })

    // Click handlers
    cy.on('tap', 'node', evt => {
      const node = evt.target
      setSelectedNode(node.data())
      setSelectedEdge(null)
    })

    cy.on('tap', 'edge', evt => {
      const edge = evt.target
      setSelectedEdge(edge.data())
      setSelectedNode(null)
    })

    cy.on('tap', evt => {
      if (evt.target === cy) {
        setSelectedNode(null)
        setSelectedEdge(null)
      }
    })

    // Right-click for context menu
    cy.on('cxttap', 'node', evt => {
      const node = evt.target
      setConnectingFrom(node.data().id)
    })

    cyRef.current = cy

    return () => {
      cy.destroy()
    }
  }, [graphData])

  // Handle zoom
  const handleZoom = (delta) => {
    if (!cyRef.current) return
    const cy = cyRef.current
    cy.zoom(cy.zoom() + delta)
  }

  const handleFit = () => {
    if (cyRef.current) cyRef.current.fit()
  }

  // Add node
  const handleAddNode = async (nodeData) => {
    try {
      const res = await createNode(id, nodeData)
      addLog(`Added node: ${nodeData.label} (${nodeData.type})`)
      setShowNodeEditor(false)
      await loadGraph()
    } catch (err) {
      addLog(`Error adding node: ${err.message}`)
    }
  }

  // Add edge
  const handleAddEdge = async (edgeData) => {
    try {
      const res = await createEdge(id, edgeData)
      addLog(`Added edge: ${edgeData.from_node} → ${edgeData.to_node}`)
      setShowEdgeEditor(false)
      setConnectingFrom(null)
      await loadGraph()
    } catch (err) {
      addLog(`Error adding edge: ${err.message}`)
    }
  }

  // Delete selected
  const handleDeleteSelected = async () => {
    if (selectedNode) {
      if (!confirm(`Delete node "${selectedNode.label}"?`)) return
      await deleteNode(selectedNode.id)
      addLog(`Deleted node: ${selectedNode.label}`)
      setSelectedNode(null)
      await loadGraph()
    } else if (selectedEdge) {
      await deleteEdge(selectedEdge.id)
      addLog(`Deleted edge`)
      setSelectedEdge(null)
      await loadGraph()
    }
  }

  // Quick connect mode
  const handleQuickConnect = async (targetId) => {
    if (!connectingFrom || connectingFrom === targetId) return
    await handleAddEdge({
      from_node: connectingFrom,
      to_node: targetId,
      label: 'related to',
      trust_level: 3,
    })
  }

  return (
    <div className="h-full flex flex-col">
      {/* Toolbar */}
      <div className="flex items-center justify-between px-4 py-2 bg-[#1e293b] border-b border-[#334155]">
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowNodeEditor(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-[#6366f1] hover:bg-[#818cf8] text-white rounded-lg text-sm transition-colors"
          >
            <Plus className="w-4 h-4" />
            Add Node
          </button>
          <button
            onClick={() => setShowEdgeEditor(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-[#334155] hover:bg-[#475569] text-white rounded-lg text-sm transition-colors"
          >
            <LinkIcon className="w-4 h-4" />
            Add Edge
          </button>
          {(selectedNode || selectedEdge) && (
            <button
              onClick={handleDeleteSelected}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-red-500/20 hover:bg-red-500/30 text-red-400 rounded-lg text-sm transition-colors"
            >
              <X className="w-4 h-4" />
              Delete Selected
            </button>
          )}
        </div>

        <div className="flex items-center gap-1">
          <button onClick={() => handleZoom(0.2)} className="p-1.5 rounded hover:bg-[#334155] text-[#94a3b8]">
            <ZoomIn className="w-4 h-4" />
          </button>
          <button onClick={() => handleZoom(-0.2)} className="p-1.5 rounded hover:bg-[#334155] text-[#94a3b8]">
            <ZoomOut className="w-4 h-4" />
          </button>
          <button onClick={handleFit} className="p-1.5 rounded hover:bg-[#334155] text-[#94a3b8]">
            <Maximize2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Main content */}
      <div className="flex-1 flex">
        {/* Graph area */}
        <div className="flex-1 relative">
          {!graphData.nodes?.length ? (
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="text-center">
                <div className="text-6xl mb-4">🕸️</div>
                <h2 className="text-xl text-[#64748b] mb-2">Empty Graph</h2>
                <p className="text-[#475569] mb-4">Add your first node to start building the investigation</p>
                <button
                  onClick={() => setShowNodeEditor(true)}
                  className="px-6 py-3 bg-[#6366f1] hover:bg-[#818cf8] text-white rounded-lg transition-colors font-medium"
                >
                  <Plus className="w-5 h-5 inline mr-2" />
                  Add First Node
                </button>
              </div>
            </div>
          ) : (
            <div ref={containerRef} className="graph-container" />
          )}

          {/* Connecting mode indicator */}
          {connectingFrom && (
            <div className="absolute top-4 left-1/2 -translate-x-1/2 bg-[#fbbf24] text-black px-4 py-2 rounded-lg text-sm font-medium animate-pulse">
              Click on target node to connect, or press Escape to cancel
            </div>
          )}
        </div>

        {/* Right panel */}
        <div className="w-80 bg-[#1e293b] border-l border-[#334155] flex flex-col overflow-hidden">
          {/* Selected node/edge info */}
          {selectedNode && (
            <div className="p-4 border-b border-[#334155] animate-fade-in">
              <div className="flex items-center gap-2 mb-3">
                <div className="w-4 h-4 rounded-full" style={{ background: selectedNode.color }} />
                <h3 className="font-semibold text-white truncate">{selectedNode.label}</h3>
              </div>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-[#64748b]">Type:</span>
                  <span className="text-white">{selectedNode.type}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-[#64748b]">Trust:</span>
                  <TrustBadge level={selectedNode.trust_level} />
                </div>
                {selectedNode.source && (
                  <div className="flex justify-between">
                    <span className="text-[#64748b]">Source:</span>
                    <span className="text-white truncate max-w-[180px]">{selectedNode.source}</span>
                  </div>
                )}
                {selectedNode.data && Object.keys(selectedNode.data).length > 0 && (
                  <div className="mt-3 pt-3 border-t border-[#334155]">
                    <div className="text-[#64748b] text-xs mb-2">Data:</div>
                    {Object.entries(selectedNode.data).map(([k, v]) => (
                      <div key={k} className="flex justify-between text-xs py-1">
                        <span className="text-[#64748b]">{k}:</span>
                        <span className="text-white truncate max-w-[150px]">{String(v)}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}

          {selectedEdge && (
            <div className="p-4 border-b border-[#334155] animate-fade-in">
              <h3 className="font-semibold text-white mb-3">🔗 Connection</h3>
              <div className="space-y-2 text-sm">
                <div><span className="text-[#64748b]">From:</span> <span className="text-white">{selectedEdge.source}</span></div>
                <div><span className="text-[#64748b]">To:</span> <span className="text-white">{selectedEdge.target}</span></div>
                <div><span className="text-[#64748b]">Label:</span> <span className="text-white">{selectedEdge.label || 'N/A'}</span></div>
                <div className="flex justify-between items-center">
                  <span className="text-[#64748b]">Trust:</span>
                  <TrustBadge level={selectedEdge.trust_level} />
                </div>
              </div>
            </div>
          )}

          {/* Graph stats */}
          <div className="p-4 border-b border-[#334155]">
            <h3 className="text-xs font-semibold text-[#64748b] uppercase tracking-wider mb-2">Graph Stats</h3>
            <div className="grid grid-cols-2 gap-2 text-sm">
              <div className="bg-[#0f172a] rounded p-2 text-center">
                <div className="text-lg font-bold text-[#6366f1]">{graphData.stats?.node_count || 0}</div>
                <div className="text-[#64748b] text-xs">Nodes</div>
              </div>
              <div className="bg-[#0f172a] rounded p-2 text-center">
                <div className="text-lg font-bold text-[#10b981]">{graphData.stats?.edge_count || 0}</div>
                <div className="text-[#64748b] text-xs">Edges</div>
              </div>
              <div className="bg-[#0f172a] rounded p-2 text-center">
                <div className="text-lg font-bold text-[#f59e0b]">{graphData.stats?.density || 0}</div>
                <div className="text-[#64748b] text-xs">Density</div>
              </div>
              <div className="bg-[#0f172a] rounded p-2 text-center">
                <div className="text-lg font-bold text-[#ec4899]">{graphData.stats?.components || 0}</div>
                <div className="text-[#64748b] text-xs">Components</div>
              </div>
            </div>
          </div>

          {/* Log */}
          <div className="flex-1 flex flex-col min-h-0">
            <LogPanel />
          </div>
        </div>
      </div>

      {/* Modals */}
      {showNodeEditor && (
        <NodeEditor
          templates={templates}
          onSave={handleAddNode}
          onClose={() => setShowNodeEditor(false)}
        />
      )}
      {showEdgeEditor && (
        <EdgeEditor
          nodes={graphData.nodes || []}
          onSave={handleAddEdge}
          onClose={() => setShowEdgeEditor(false)}
        />
      )}
    </div>
  )
}
