// API 服务配置文件
// 统一管理所有 API 调用

// ==================== API Base URL 配置 ====================
const API_BASE_URL = '/api'  // 使用代理路径，Vite会自动转发到 http://localhost:8000

// ==================== 通用请求函数 ====================
async function request(url, config = {}) {
  const defaultConfig = {
    headers: {
      'Content-Type': 'application/json',
      ...config.headers,
    },
    ...config,
  }

  try {
    const response = await fetch(url, defaultConfig)
    
    if (!response.ok) {
      const errorText = await response.text()
      throw new Error(`API调用失败: ${response.status} ${errorText}`)
    }
    
    return await response.json()
  } catch (error) {
    console.error('API请求错误:', error)
    throw error
  }
}

// ==================== API 接口定义 ====================

export const api = {
  // ==================== 健康检查 ====================
  health: {
    check: () => request('/health'),
  },

  // ==================== Dashboard ====================
  dashboard: {
    getStats: () => request(`${API_BASE_URL}/dashboard/stats`),
  },

  // ==================== 项目管理 ====================
  projects: {
    getAll: () => request(`${API_BASE_URL}/projects`),
    create: (data) => request(`${API_BASE_URL}/projects`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),
    delete: (id) => request(`${API_BASE_URL}/projects/${id}`, {
      method: 'DELETE',
    }),
  },

  // ==================== API 管理 ====================
  apis: {
    getAll: () => request(`${API_BASE_URL}/apis`),
    execute: (data) => request(`${API_BASE_URL}/execute-api`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),
    saveAsTestCase: (data) => request(`${API_BASE_URL}/save-api-as-testcase`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),
    parseSwagger: (url) => request(`${API_BASE_URL}/swagger/parse`, {
      method: 'POST',
      body: JSON.stringify({ url }),
    }),
    smokeRunFromKb: (data) => request(`${API_BASE_URL}/knowledge/testcases/search`, {
      method: 'POST',
      body: JSON.stringify(data || {}),
    }),
  },

  // ==================== Swagger ====================
  swagger: {
    upload: (file) => {
      const formData = new FormData()
      formData.append('file', file)
      return fetch(`${API_BASE_URL}/swagger/upload`, {
        method: 'POST',
        body: formData,
      }).then(res => {
        if (!res.ok) throw new Error('上传失败')
        return res.json()
      })
    },
    parse: (url) => request(`${API_BASE_URL}/swagger/parse`, {
      method: 'POST',
      body: JSON.stringify({ url }),
    }),
  },

  // ==================== 测试用例 ====================
  testCases: {
    getAll: () => request(`${API_BASE_URL}/test-cases`),
    create: (data) => request(`${API_BASE_URL}/test-cases`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),
    batchDelete: (ids) => request(`${API_BASE_URL}/testcases/batch-delete`, {
      method: 'POST',
      body: JSON.stringify({ ids }),
    }),
    generate: (file) => {
      const formData = new FormData()
      formData.append('file', file)
      return fetch(`${API_BASE_URL}/testcases/generate`, {
        method: 'POST',
        body: formData,
      }).then(res => {
        if (!res.ok) throw new Error('生成失败')
        return res.json()
      })
    },
    generateScript: (testCaseId) => request(`${API_BASE_URL}/testcases/${testCaseId}/generate-script`, {
      method: 'POST',
    }),
    execute: (testCaseId) => request(`${API_BASE_URL}/testcases/${testCaseId}/execute`, {
      method: 'POST',
    }),
    manualExecute: (testCaseId, data) => request(`${API_BASE_URL}/testcases/${testCaseId}/manual-execute`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),
    bindDataset: (testCaseId, datasetId) => request(`${API_BASE_URL}/test-cases/${testCaseId}/bind-dataset`, {
      method: 'POST',
      body: JSON.stringify({ dataset_id: datasetId }),
    }),
    exportExcel: () => fetch(`${API_BASE_URL}/test-cases/export`).then(res => {
      if (!res.ok) throw new Error('导出失败')
      return res.blob()
    }),
  },

  // ==================== 测试数据 ====================
  testData: {
    generate: (data) => request(`${API_BASE_URL}/test-data/generate`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),
    smartGenerate: (data) => request(`${API_BASE_URL}/test-data/smart-generate`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),
    smartObject: (data) => request(`${API_BASE_URL}/test-data/smart-object`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),
    evaluate: (data) => request(`${API_BASE_URL}/test-data/evaluate`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),
    getTemplates: () => request(`${API_BASE_URL}/test-data/templates`),
    getStats: () => request(`${API_BASE_URL}/test-data/stats`),
    getScenarios: (entityType) => request(`${API_BASE_URL}/test-data/scenarios/${entityType}`),
    getDatasets: (params = {}) => {
      const query = new URLSearchParams(params).toString()
      return request(`${API_BASE_URL}/test-data/datasets${query ? '?' + query : ''}`)
    },
  },

  // ==================== 数据集管理 ====================
  datasets: {
    getAll: (params = {}) => {
      const query = new URLSearchParams(params).toString()
      return request(`${API_BASE_URL}/test-data/datasets${query ? '?' + query : ''}`)
    },
    create: (data) => request(`${API_BASE_URL}/test-data/datasets`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),
    get: (id) => request(`${API_BASE_URL}/test-data/datasets/${id}`),
    update: (id, data) => request(`${API_BASE_URL}/test-data/datasets/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),
    delete: (id) => request(`${API_BASE_URL}/test-data/datasets/${id}`, {
      method: 'DELETE',
    }),
    use: (id) => request(`${API_BASE_URL}/test-data/datasets/${id}/use`, {
      method: 'POST',
    }),
  },

  // ==================== 自动化脚本 ====================
  automation: {
    getScripts: () => request(`${API_BASE_URL}/automation/scripts`),
    generateScript: (testCaseId) => request(`${API_BASE_URL}/automation/scripts/generate`, {
      method: 'POST',
      body: JSON.stringify({ test_case_id: testCaseId }),
    }),
    downloadScript: (scriptId) => fetch(`${API_BASE_URL}/automation/scripts/${scriptId}/download`).then(res => {
      if (!res.ok) throw new Error('下载失败')
      return res.text()
    }),
    executeScript: (scriptId) => request(`${API_BASE_URL}/automation/scripts/${scriptId}/execute`, {
      method: 'POST',
    }),
  },

  // ==================== 测试运行 ====================
  testRuns: {
    getAll: () => request(`${API_BASE_URL}/test-runs`),
    start: (data) => request(`${API_BASE_URL}/test-runs/start`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),
    getStatus: (id) => request(`${API_BASE_URL}/test-runs/${id}/status`),
  },

  // ==================== 报告 ====================
  reports: {
    getAll: () => request(`${API_BASE_URL}/reports`),
    get: (id) => request(`${API_BASE_URL}/reports/${id}`),
    getById: (id) => request(`${API_BASE_URL}/reports/${id}`),
    generate: (data) => request(`${API_BASE_URL}/reports/generate`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  },

  // ==================== AI 功能 ====================
  ai: {
    getCurrent: () => request(`${API_BASE_URL}/ai/current`),
    generate: (data) => request(`${API_BASE_URL}/ai/generate`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),
    getProviders: () => request(`${API_BASE_URL}/ai/providers/list`),
    getProviderStatus: (providerId) => request(`${API_BASE_URL}/ai/providers/${providerId}/status`),
    testProvider: (providerId) => request(`${API_BASE_URL}/ai/providers/${providerId}/test`, {
      method: 'POST',
    }),
    selectProvider: (providerId) => request(`${API_BASE_URL}/ai/providers/select`, {
      method: 'POST',
      body: JSON.stringify({ provider: providerId }),
    }),
    switchProvider: (providerId, model) => request(`${API_BASE_URL}/ai/providers/switch`, {
      method: 'POST',
      body: JSON.stringify({ provider: providerId, model }),
    }),
    getAgents: () => request(`${API_BASE_URL}/ai/agents`),
  },

  // ==================== Agent ====================
  agent: {
    analyze: (data) => request(`${API_BASE_URL}/agent/analyze`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),
    getHistory: (limit = 10) => request(`${API_BASE_URL}/agent/history?limit=${limit}`),
  },

  // ==================== Pipeline ====================
  pipeline: {
    run: (data) => request(`${API_BASE_URL}/pipeline/run`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  },

  // ==================== 知识库 ====================
  knowledge: {
    getStats: () => request(`${API_BASE_URL}/knowledge/stats`),
    searchTestCases: (data) => request(`${API_BASE_URL}/knowledge/testcases/search`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),
    getCoverage: () => request(`${API_BASE_URL}/knowledge/coverage`),
  },

  // ==================== 任务管理 ====================
  tasks: {
    getStatus: (taskId) => request(`${API_BASE_URL}/tasks/${taskId}/status`),
  },
}

// ==================== 导出默认对象 ====================
export default api

// ==================== 导出命名对象(兼容旧代码) ====================
export const dashboardAPI = api.dashboard
export const projectsAPI = api.projects
export const apisAPI = api.apis
export const swaggerAPI = api.swagger
export const testCasesAPI = api.testCases
export const testDataAPI = api.testData
export const datasetsAPI = api.datasets
export const automationAPI = api.automation
export const testRunsAPI = api.testRuns
export const reportsAPI = api.reports
export const aiAPI = api.ai
export const agentAPI = api.agent
export const pipelineAPI = api.pipeline
export const knowledgeAPI = api.knowledge
export const tasksAPI = api.tasks
