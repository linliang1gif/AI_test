import { API_BASE_URL, request } from './httpClient'

export const codeCompareAPI = {
  uploadCodeSnapshot: (formData) => fetch(`${API_BASE_URL}/v2/code-compare/upload`, {
    method: 'POST',
    body: formData,
  }).then(r => r.json()),
  cloneRepo: (data) => request(`${API_BASE_URL}/v2/code-compare/clone-repo`, {
    method: 'POST',
    body: JSON.stringify(data),
  }),
  analyzeRequirementCodeCompare: (data) => request(`${API_BASE_URL}/v2/code-compare/analyze`, {
    method: 'POST',
    body: JSON.stringify(data),
  }),
  cacheRequirement: (data) => request(`${API_BASE_URL}/v2/code-compare/cache-requirement`, {
    method: 'POST',
    body: JSON.stringify(data),
  }),
  getCodeCompareReports: () => request(`${API_BASE_URL}/v2/code-compare/reports`),
  getCodeCompareReportDetail: (reportId) => request(`${API_BASE_URL}/v2/code-compare/reports/${reportId}`),
  confirmCodeCompareFinding: (reportId, data) => request(`${API_BASE_URL}/v2/code-compare/reports/${reportId}/confirm`, {
    method: 'POST',
    body: JSON.stringify(data),
  }),
  convertFindingToDefect: (findingId, data) => request(`${API_BASE_URL}/v2/code-compare/findings/${findingId}/convert-to-defect`, {
    method: 'POST',
    body: JSON.stringify(data),
  }),
  convertFindingToTestCase: (findingId, data) => request(`${API_BASE_URL}/v2/code-compare/findings/${findingId}/convert-to-test-case`, {
    method: 'POST',
    body: JSON.stringify(data),
  }),
  convertFindingToQuestion: (findingId, data) => request(`${API_BASE_URL}/v2/code-compare/findings/${findingId}/convert-to-question`, {
    method: 'POST',
    body: JSON.stringify(data),
  }),
  markFindingFalsePositive: (findingId, data) => request(`${API_BASE_URL}/v2/code-compare/findings/${findingId}/mark-false-positive`, {
    method: 'POST',
    body: JSON.stringify(data),
  }),
  pushFindingToTapd: (findingId, data = {}) => request(`${API_BASE_URL}/v2/code-compare/findings/${findingId}/push-to-tapd`, {
    method: 'POST',
    body: JSON.stringify(data),
  }),
  batchPushFindingsToTapd: (data) => request(`${API_BASE_URL}/v2/code-compare/findings/batch-push-to-tapd`, {
    method: 'POST',
    body: JSON.stringify(data),
  }),
  syncFindingTapdStatus: (findingId) => request(`${API_BASE_URL}/v2/code-compare/findings/${findingId}/sync-tapd-status`, {
    method: 'POST',
  }),
  syncReportTapdStatus: (reportId) => request(`${API_BASE_URL}/v2/code-compare/reports/${reportId}/sync-tapd-status`, {
    method: 'POST',
  }),
  getTapdConfig: () => request(`${API_BASE_URL}/v2/code-compare/tapd/config`),
  saveTapdConfig: (data) => request(`${API_BASE_URL}/v2/code-compare/tapd/config`, {
    method: 'POST',
    body: JSON.stringify(data),
  }),
  testTapdConnection: () => request(`${API_BASE_URL}/v2/code-compare/tapd/test`, { method: 'POST' }),
}