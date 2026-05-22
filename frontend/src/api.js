import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_URL || '/api'

const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
})

// ── Investigations ──
export const getInvestigations = () => api.get('/investigations')
export const getInvestigation = (id) => api.get(`/investigations/${id}`)
export const createInvestigation = (data) => api.post('/investigations', data)
export const updateInvestigation = (id, data) => api.put(`/investigations/${id}`, data)
export const deleteInvestigation = (id) => api.delete(`/investigations/${id}`)

// ── Nodes ──
export const createNode = (invId, data) => api.post(`/investigations/${invId}/nodes`, data)
export const updateNode = (nodeId, data) => api.put(`/nodes/${nodeId}`, data)
export const deleteNode = (nodeId) => api.delete(`/nodes/${nodeId}`)

// ── Edges ──
export const createEdge = (invId, data) => api.post(`/investigations/${invId}/edges`, data)
export const updateEdge = (edgeId, data) => api.put(`/edges/${edgeId}`, data)
export const deleteEdge = (edgeId) => api.delete(`/edges/${edgeId}`)

// ── Graph ──
export const getGraph = (invId) => api.get(`/investigations/${invId}/graph`)
export const findPaths = (invId, source, target) =>
  api.get(`/investigations/${invId}/paths?source=${source}&target=${target}`)
export const findConnected = (invId, nodeId) =>
  api.get(`/investigations/${invId}/connected/${nodeId}`)

// ── Reports ──
export const getReportJson = (invId) => api.get(`/investigations/${invId}/report`)
export const getReportHtml = (invId) => api.get(`/investigations/${invId}/report/html`)
export const getReportMarkdown = (invId) => api.get(`/investigations/${invId}/report/markdown`)

// ── Templates ──
export const getTemplates = () => api.get('/templates')
export const getTemplateByType = (type) => api.get(`/templates/${type}`)

export default api
