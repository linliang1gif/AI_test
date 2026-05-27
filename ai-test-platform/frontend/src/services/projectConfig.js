import { API_BASE_URL, request } from './httpClient'

export const projectsAPI = {
  getAll: (params = {}) => {
    const query = new URLSearchParams(params).toString()
    return request(`${API_BASE_URL}/v2/projects${query ? '?' + query : ''}`)
  },
  get: (id) => request(`${API_BASE_URL}/v2/projects/${id}`),
  create: (data) => request(`${API_BASE_URL}/v2/projects`, {
    method: 'POST',
    body: JSON.stringify(data),
  }),
  update: (id, data) => request(`${API_BASE_URL}/v2/projects/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  }),
  delete: (id, extra = {}) => request(`${API_BASE_URL}/v2/projects/${id}`, {
    method: 'DELETE',
    body: JSON.stringify(extra),
  }),
  getEnvironments: (id) => request(`${API_BASE_URL}/v2/projects/${id}/environments`),
}

export const environmentsAPI = {
  create: (data) => request(`${API_BASE_URL}/v2/environments`, {
    method: 'POST',
    body: JSON.stringify(data),
  }),
  get: (id) => request(`${API_BASE_URL}/v2/environments/${id}`),
  update: (id, data) => request(`${API_BASE_URL}/v2/environments/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  }),
  delete: (id, extra = {}) => request(`${API_BASE_URL}/v2/environments/${id}`, {
    method: 'DELETE',
    body: JSON.stringify(extra),
  }),
  getAuthProfile: (id) => request(`${API_BASE_URL}/v2/environments/${id}/auth-profile`),
}

export const authProfilesAPI = {
  create: (data) => request(`${API_BASE_URL}/v2/auth-profiles`, {
    method: 'POST',
    body: JSON.stringify(data),
  }),
  get: (id) => request(`${API_BASE_URL}/v2/auth-profiles/${id}`),
  update: (id, data) => request(`${API_BASE_URL}/v2/auth-profiles/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  }),
  delete: (id) => request(`${API_BASE_URL}/v2/auth-profiles/${id}`, {
    method: 'DELETE',
  }),
}