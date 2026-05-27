import { API_BASE_URL, request } from './httpClient'

export const iterationsAPI = {
  templates: () => request(`${API_BASE_URL}/v2/iteration-templates`),
  list: (projectId, params = {}) => {
    const query = new URLSearchParams(params).toString()
    return request(`${API_BASE_URL}/v2/projects/${projectId}/iterations${query ? '?' + query : ''}`)
  },
  create: (data) => request(`${API_BASE_URL}/v2/iterations`, {
    method: 'POST',
    body: JSON.stringify(data),
  }),
  createForProject: (projectId, data) => request(`${API_BASE_URL}/v2/projects/${projectId}/iterations`, {
    method: 'POST',
    body: JSON.stringify(data),
  }),
  get: (iterationId) => request(`${API_BASE_URL}/v2/iterations/${iterationId}`),
  update: (iterationId, data) => request(`${API_BASE_URL}/v2/iterations/${iterationId}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  }),
  patch: (iterationId, data) => request(`${API_BASE_URL}/v2/iterations/${iterationId}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  }),
  delete: (iterationId, extra = {}) => request(`${API_BASE_URL}/v2/iterations/${iterationId}`, {
    method: 'DELETE',
    body: JSON.stringify(extra),
  }),
  assignCases: (iterationId, caseIds) => request(`${API_BASE_URL}/v2/iterations/${iterationId}/assign-cases`, {
    method: 'POST',
    body: JSON.stringify({ case_ids: caseIds }),
  }),
  unassignCases: (iterationId, caseIds) => request(`${API_BASE_URL}/v2/iterations/${iterationId}/unassign-cases`, {
    method: 'POST',
    body: JSON.stringify({ case_ids: caseIds }),
  }),
  createRequirement: (iterationId, data) => request(`${API_BASE_URL}/v2/iterations/${iterationId}/requirements`, {
    method: 'POST',
    body: JSON.stringify(data),
  }),
  listRequirements: (iterationId) => request(`${API_BASE_URL}/v2/iterations/${iterationId}/requirements`),
  analyzeRequirements: (iterationId, data = {}) => request(`${API_BASE_URL}/v2/iterations/${iterationId}/ai/analyze-requirements`, {
    method: 'POST',
    body: JSON.stringify(data),
  }),
  generateTestPoints: (iterationId) => request(`${API_BASE_URL}/v2/iterations/${iterationId}/test-points/generate`, {
    method: 'POST',
  }),
  listTestPoints: (iterationId, params = {}) => {
    const query = new URLSearchParams(params).toString()
    return request(`${API_BASE_URL}/v2/iterations/${iterationId}/test-points${query ? '?' + query : ''}`)
  },
  confirmTestPoint: (testPointId, confirmed = true) => request(`${API_BASE_URL}/v2/iteration-test-points/${testPointId}/confirm`, {
    method: 'PATCH',
    body: JSON.stringify({ confirmed }),
  }),
  generateTestCases: (iterationId) => request(`${API_BASE_URL}/v2/iterations/${iterationId}/test-cases/generate`, {
    method: 'POST',
  }),
  listTestCases: (iterationId) => request(`${API_BASE_URL}/v2/iterations/${iterationId}/test-cases`),
  manualExecuteCase: (iterationId, caseId, data = {}) => request(`${API_BASE_URL}/v2/iterations/${iterationId}/test-cases/${caseId}/manual-execute`, {
    method: 'POST',
    body: JSON.stringify(data),
  }),
  createExecutionSet: (iterationId, data = {}) => request(`${API_BASE_URL}/v2/iterations/${iterationId}/execution-sets`, {
    method: 'POST',
    body: JSON.stringify(data),
  }),
  listExecutionSets: (iterationId) => request(`${API_BASE_URL}/v2/iterations/${iterationId}/execution-sets`),
  run: (iterationId, data = {}) => request(`${API_BASE_URL}/v2/iterations/${iterationId}/run`, {
    method: 'POST',
    body: JSON.stringify(data),
  }),
  getReport: (iterationId) => request(`${API_BASE_URL}/v2/iterations/${iterationId}/report`),
}