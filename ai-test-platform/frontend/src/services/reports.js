import { API_BASE_URL, request } from './httpClient'

export const reportsAPI = {
  getAll: (params = {}) => {
    const query = new URLSearchParams(params).toString()
    return request(`${API_BASE_URL}/v2/reports${query ? '?' + query : ''}`)
  },
  get: (reportId) => request(`${API_BASE_URL}/v2/reports/${reportId}`),
  generate: (data) => request(`${API_BASE_URL}/v2/test-runs/${data.run_id}/report`, {
    method: 'POST',
    body: JSON.stringify({ format: data.format || 'html' }),
  }),
  getByRunId: (runId) => request(`${API_BASE_URL}/v2/reports?run_id=${runId}`),
}