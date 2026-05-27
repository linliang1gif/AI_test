import { API_BASE_URL, request } from './httpClient'

export const visualAPI = {
  listBaselines: (params = {}) => {
    const qs = new URLSearchParams()
    if (params.case_id) qs.set('case_id', params.case_id)
    if (params.name) qs.set('name', params.name)
    if (params.env) qs.set('env', params.env)
    if (params.viewport) qs.set('viewport', params.viewport)
    if (params.branch) qs.set('branch', params.branch)
    if (params.limit) qs.set('limit', params.limit)
    const s = qs.toString()
    return request(`${API_BASE_URL}/v2/visual/baselines${s ? '?' + s : ''}`)
  },
  listNamespaces: () => request(`${API_BASE_URL}/v2/visual/namespaces`),
  getBaseline: (id) => request(`${API_BASE_URL}/v2/visual/baselines/${encodeURIComponent(id)}`),
  approveBaseline: (id, data = {}) => request(`${API_BASE_URL}/v2/visual/baselines/${encodeURIComponent(id)}/approve`, {
    method: 'POST',
    body: JSON.stringify(data),
  }),
  updateConfig: (id, data) => request(`${API_BASE_URL}/v2/visual/baselines/${encodeURIComponent(id)}/config`, {
    method: 'POST',
    body: JSON.stringify(data),
  }),
  deleteBaseline: (id, data = {}) => request(`${API_BASE_URL}/v2/visual/baselines/${encodeURIComponent(id)}`, {
    method: 'DELETE',
    body: JSON.stringify(data),
  }),
  bulkApprove: (data) => request(`${API_BASE_URL}/v2/visual/bulk/approve`, {
    method: 'POST',
    body: JSON.stringify(data),
  }),
  bulkDelete: (data) => request(`${API_BASE_URL}/v2/visual/bulk/delete`, {
    method: 'POST',
    body: JSON.stringify(data),
  }),
  bulkConfig: (data) => request(`${API_BASE_URL}/v2/visual/bulk/config`, {
    method: 'POST',
    body: JSON.stringify(data),
  }),
  listVersions: (id) => request(`${API_BASE_URL}/v2/visual/baselines/${encodeURIComponent(id)}/versions`),
  rollback: (id, data) => request(`${API_BASE_URL}/v2/visual/baselines/${encodeURIComponent(id)}/rollback`, {
    method: 'POST',
    body: JSON.stringify(data),
  }),
  getWebhookConfig: () => request(`${API_BASE_URL}/v2/visual/webhook/config`),
  testWebhook: (data = {}) => request(`${API_BASE_URL}/v2/visual/webhook/test`, {
    method: 'POST',
    body: JSON.stringify(data),
  }),
  listDeadLetters: (params = {}) => {
    const qs = new URLSearchParams()
    if (params.limit) qs.set('limit', params.limit)
    if (params.include_resolved) qs.set('include_resolved', 'true')
    if (params.event_type) qs.set('event_type', params.event_type)
    const s = qs.toString()
    return request(`${API_BASE_URL}/v2/visual/webhook/dead-letters${s ? '?' + s : ''}`)
  },
  retryDeadLetter: (id) => request(`${API_BASE_URL}/v2/visual/webhook/dead-letters/${id}/retry`, {
    method: 'POST',
  }),
  deleteDeadLetter: (id, data = {}) => request(`${API_BASE_URL}/v2/visual/webhook/dead-letters/${id}`, {
    method: 'DELETE',
    body: JSON.stringify(data),
  }),
  pendingReviews: (params = {}) => {
    const qs = new URLSearchParams()
    if (params.days) qs.set('days', params.days)
    if (params.limit) qs.set('limit', params.limit)
    const s = qs.toString()
    return request(`${API_BASE_URL}/v2/visual/pending-reviews${s ? '?' + s : ''}`)
  },
  getStats: () => request(`${API_BASE_URL}/v2/visual/stats`),
}