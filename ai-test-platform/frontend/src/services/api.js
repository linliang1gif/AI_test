// API 服务配置文件
// 统一管理所有 API 调用

// ==================== API Base URL 配置 ====================
const API_BASE_URL = '/api'  // 使用代理路径，Vite会自动转发到 http://localhost:8000
const PILOT_API_BASE_URL = '/api/pilot'

function getRoleHeader() {
  const role = localStorage.getItem('pilot_role') || 'admin'
  return { 'X-User-Role': role }
}

// ==================== 通用请求函数 ====================
async function request(url, config = {}) {
  const defaultConfig = {
    headers: {
      'Content-Type': 'application/json',
      ...getRoleHeader(),
      ...config.headers,
    },
    ...config,
  }

  try {
    const response = await fetch(url, defaultConfig)
    
    if (!response.ok) {
      const errorText = await response.text()
      
      // 404错误不重试,直接抛出
      if (response.status === 404) {
        console.warn(`API 404: ${url} - 该接口不可用`)
        throw new Error(`404 ${errorText}`)
      }
      
      throw new Error(`API调用失败: ${response.status} ${errorText}`)
    }
    
    if (response.status === 204) {
      return null
    }

    const responseText = await response.text()
    if (!responseText) {
      return null
    }

    return JSON.parse(responseText)
  } catch (error) {
    // 404错误静默处理,不在控制台重复输出
    if (!error.message.startsWith('404')) {
      console.error('API请求错误:', error)
    }
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
    getAll: () => request(`${PILOT_API_BASE_URL}/projects`),
    get: (id) => request(`${PILOT_API_BASE_URL}/projects/${id}`),
    create: (data) => request(`${PILOT_API_BASE_URL}/projects`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),
    update: (id, data) => request(`${PILOT_API_BASE_URL}/projects/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),
    delete: (id) => request(`${PILOT_API_BASE_URL}/projects/${id}`, {
      method: 'DELETE',
    }),
  },

  environments: {
    create: (data) => request(`${PILOT_API_BASE_URL}/environments`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),
    update: (id, data) => request(`${PILOT_API_BASE_URL}/environments/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),
  },

  // ==================== API 管理 ====================
  apis: {
    getAll: (projectId) => request(`${PILOT_API_BASE_URL}/apis${projectId ? `?project_id=${projectId}` : ''}`),
    importFromUrl: (data) => request(`${PILOT_API_BASE_URL}/openapi/import-url`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),
    importFromFile: ({ projectId, environmentId, file }) => {
      const formData = new FormData()
      formData.append('file', file)
      return fetch(`${PILOT_API_BASE_URL}/openapi/import-file?project_id=${projectId}&environment_id=${environmentId}`, {
        method: 'POST',
        headers: {
          ...getRoleHeader(),
        },
        body: formData,
      }).then(async res => {
        if (!res.ok) throw new Error(await res.text())
        return res.json()
      })
    },
    generateCases: (data) => request(`${PILOT_API_BASE_URL}/test-cases/generate`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),
    execute: (data) => request(`${API_BASE_URL}/execute-api`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),
    saveAsTestCase: (data) => request(`${API_BASE_URL}/save-api-as-testcase`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  },

  // ==================== Swagger ====================
  swagger: {
    upload: (file) => {
      const formData = new FormData()
      formData.append('file', file)
      return fetch(`${API_BASE_URL}/upload/swagger`, {
        method: 'POST',
        headers: {
          ...getRoleHeader(),
        },
        body: formData,
      }).then(res => {
        if (!res.ok) throw new Error('上传失败')
        return res.json()
      })
    },
    parse: (file) => {
      const formData = new FormData()
      formData.append('file', file)
      return fetch(`${API_BASE_URL}/swagger/parse`, {
        method: 'POST',
        headers: {
          ...getRoleHeader(),
        },
        body: formData,
      }).then(res => {
        if (!res.ok) throw new Error('解析失败')
        return res.json()
      })
    },
  },

  // ==================== 测试用例 ====================
  testCases: {
    getAll: (projectId) => request(`${PILOT_API_BASE_URL}/test-cases${projectId ? `?project_id=${projectId}` : ''}`),
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
    generateFromSVN: (data) => request(`${API_BASE_URL}/ai/generate-testcases-from-svn`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),
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
    getAll: (projectId) => request(`${PILOT_API_BASE_URL}/test-runs${projectId ? `?project_id=${projectId}` : ''}`),
    start: (data) => request(`${PILOT_API_BASE_URL}/test-runs`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),
    getStatus: (id) => request(`${PILOT_API_BASE_URL}/test-runs/${id}`),
    get: (id) => request(`${PILOT_API_BASE_URL}/test-runs/${id}`),
  },

  // ==================== 报告 ====================
  reports: {
    getAll: (projectId) => request(`${PILOT_API_BASE_URL}/reports${projectId ? `?project_id=${projectId}` : ''}`),
    get: (id) => request(`${PILOT_API_BASE_URL}/reports/${id}`),
    generate: (data) => request(`${PILOT_API_BASE_URL}/reports/generate`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  },

  system: {
    getSettings: () => request(`${PILOT_API_BASE_URL}/system/settings`),
    updateSetting: (data) => request(`${PILOT_API_BASE_URL}/system/settings`, {
      method: 'PUT',
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
    switchProvider: (data) => request(`${API_BASE_URL}/ai/providers/switch`, {
      method: 'POST',
      body: JSON.stringify(data),
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
    // V2 智能执行Pipeline
    runIntelligent: (data) => request(`${API_BASE_URL}/v2/test/run-intelligent`, {
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

  // ==================== V2 API - 项目配置 ====================
  v2: {
    projects: {
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
      delete: (id) => request(`${API_BASE_URL}/v2/projects/${id}`, {
        method: 'DELETE',
      }),
      getEnvironments: (id) => request(`${API_BASE_URL}/v2/projects/${id}/environments`),
    },

    environments: {
      create: (data) => request(`${API_BASE_URL}/v2/environments`, {
        method: 'POST',
        body: JSON.stringify(data),
      }),
      get: (id) => request(`${API_BASE_URL}/v2/environments/${id}`),
      update: (id, data) => request(`${API_BASE_URL}/v2/environments/${id}`, {
        method: 'PUT',
        body: JSON.stringify(data),
      }),
      delete: (id) => request(`${API_BASE_URL}/v2/environments/${id}`, {
        method: 'DELETE',
      }),
      getAuthProfile: (id) => request(`${API_BASE_URL}/v2/environments/${id}/auth-profile`),
    },

    authProfiles: {
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
    },

    testRuns: {
      create: (data) => request(`${API_BASE_URL}/v2/test-runs`, {
        method: 'POST',
        body: JSON.stringify(data),
      }),
      get: (id) => request(`${API_BASE_URL}/v2/test-runs/${id}`),
      updateStatus: (id, data) => request(`${API_BASE_URL}/v2/test-runs/${id}/status`, {
        method: 'PUT',
        body: JSON.stringify(data),
      }),
      getList: (params = {}) => {
        const query = new URLSearchParams(params).toString()
        return request(`${API_BASE_URL}/v2/test-runs${query ? '?' + query : ''}`)
      },
      getCases: (id) => request(`${API_BASE_URL}/v2/test-runs/${id}/cases`),
      getHistory: (id) => request(`${API_BASE_URL}/v2/test-runs/${id}/history`),
    },

    observability: {
      getRuns: (params = {}) => {
        const query = new URLSearchParams(params).toString()
        return request(`${API_BASE_URL}/v2/observability/runs${query ? '?' + query : ''}`)
      },
      getRunDetail: (runId) => request(`${API_BASE_URL}/v2/observability/runs/${runId}`),
      getRunCases: (runId) => request(`${API_BASE_URL}/v2/observability/runs/${runId}/cases`),
      getRunCaseDetail: (runId, caseId) => request(`${API_BASE_URL}/v2/observability/runs/${runId}/cases/${caseId}`),
      getCaseSteps: (caseId) => request(`${API_BASE_URL}/v2/observability/cases/${caseId}/steps`),
      getStepSnapshot: (stepId) => request(`${API_BASE_URL}/v2/observability/steps/${stepId}/snapshot`),
      getHistory: (entityType, entityId) => request(`${API_BASE_URL}/v2/observability/history/${entityType}/${entityId}`),
      getByTraceId: (traceId) => request(`${API_BASE_URL}/v2/observability/trace/${traceId}`),
      generateReport: (runId, format = 'html') => request(`${API_BASE_URL}/v2/test-runs/${runId}/report`, {
        method: 'POST',
        body: JSON.stringify({ format }),
      }),
      downloadReport: (runId, format = 'html') => `${API_BASE_URL}/v2/test-runs/${runId}/report/download?format=${format}`,
    },

    swagger: {
      importFromUrl: (data) => request(`${API_BASE_URL}/v2/swagger/import-url`, {
        method: 'POST',
        body: JSON.stringify(data),
      }),
      importFromFile: (projectId, file, generateCases = true) => {
        // 确保 projectId 是有效数字
        if (!projectId || isNaN(projectId)) {
          return Promise.reject(new Error('项目ID无效'))
        }
        const formData = new FormData()
        formData.append('file', file)
        return fetch(`${API_BASE_URL}/v2/swagger/import-file?project_id=${projectId}&generate_cases=${generateCases}`, {
          method: 'POST',
          body: formData,
        }).then(res => {
          if (!res.ok) throw new Error('导入失败')
          return res.json()
        })
      },
      getApiSpecs: (projectId) => {
        // 只有当 projectId 是有效数字时才添加查询参数
        const query = (projectId && !isNaN(projectId)) ? `?project_id=${projectId}` : ''
        return request(`${API_BASE_URL}/v2/swagger/api-specs${query}`)
      },
      getApiSpec: (apiSpecId) => request(`${API_BASE_URL}/v2/swagger/api-specs/${apiSpecId}`),
      deleteApiSpec: (apiSpecId) => request(`${API_BASE_URL}/v2/swagger/api-specs/${apiSpecId}`, {
        method: 'DELETE',
      }),
      generateTestCases: (apiSpecId) => request(`${API_BASE_URL}/v2/swagger/generate-test-cases`, {
        method: 'POST',
        body: JSON.stringify({ api_spec_id: apiSpecId }),
      }),
    },

    testCases: {
      getAll: (params = {}) => {
        const query = new URLSearchParams(params).toString()
        return request(`${API_BASE_URL}/v2/test-cases${query ? '?' + query : ''}`)
      },
      get: (testCaseId) => request(`${API_BASE_URL}/v2/test-cases/${testCaseId}`),
      execute: (caseId, data = {}) => request(`${API_BASE_URL}/v2/test-cases/${caseId}/execute`, {
        method: 'POST',
        body: JSON.stringify(data),
      }),
      batchExecute: (caseIds, data = {}) => request(`${API_BASE_URL}/v2/test-cases/batch-execute`, {
        method: 'POST',
        body: JSON.stringify({ case_ids: caseIds, ...data }),
      }),
      previewVariables: (caseId, datasetId) => request(`${API_BASE_URL}/v2/test-cases/${caseId}/preview-variables?dataset_id=${datasetId || ''}`),
    },

    execution: {
      trigger: (data) => request(`${API_BASE_URL}/v2/execution/trigger`, {
        method: 'POST',
        body: JSON.stringify(data),
      }),
      triggerSimple: () => request(`${API_BASE_URL}/v2/execution/trigger-simple`, {
        method: 'POST',
      }),
    },

    // ==================== Executor V2 - 真实HTTP执行引擎 ====================
    executorV2: {
      execute: (data) => request(`${API_BASE_URL}/v2/execute`, {
        method: 'POST',
        body: JSON.stringify(data),
      }),
      executeBatch: (data) => request(`${API_BASE_URL}/v2/execute/batch`, {
        method: 'POST',
        body: JSON.stringify(data),
      }),
      getRunResults: (runId) => request(`${API_BASE_URL}/v2/execute/runs/${runId}`),
      getRunSummary: (runId) => request(`${API_BASE_URL}/v2/execute/runs/${runId}/summary`),
      getResultDetail: (recordId) => request(`${API_BASE_URL}/v2/execute/results/${recordId}`),
      generateFromSwagger: (data) => request(`${API_BASE_URL}/v2/execute/generate-from-swagger`, {
        method: 'POST',
        body: JSON.stringify(data),
      }),
      generateAndRun: (data) => request(`${API_BASE_URL}/v2/execute/generate-and-run`, {
        method: 'POST',
        body: JSON.stringify(data),
      }),
      setToken: (data) => request(`${API_BASE_URL}/v2/execute/auth/set-token`, {
        method: 'POST',
        body: JSON.stringify(data),
      }),
      getAuthStatus: () => request(`${API_BASE_URL}/v2/execute/auth/status`),
      clearToken: (envKey = 'default') => request(`${API_BASE_URL}/v2/execute/auth/clear?env_key=${envKey}`, {
        method: 'DELETE',
      }),
      aiGenerateAssertions: (data) => request(`${API_BASE_URL}/v2/execute/ai/generate-assertions`, {
        method: 'POST',
        body: JSON.stringify(data),
      }),
      aiEnhanceCases: (data) => request(`${API_BASE_URL}/v2/execute/ai/enhance-cases`, {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    },
  },
}

// ==================== 导出默认对象 ====================
export default api

// ==================== 导出命名对象(兼容旧代码) ====================
export const dashboardAPI = api.dashboard
export const projectsAPI = api.projects
export const environmentsAPI = api.environments
export const apisAPI = api.apis
export const swaggerAPI = api.swagger
export const testCasesAPI = api.testCases
export const testDataAPI = api.testData
export const datasetsAPI = api.datasets
export const automationAPI = api.automation
export const testRunsAPI = api.testRuns
export const reportsAPI = api.reports
export const systemAPI = api.system
export const aiAPI = api.ai
export const agentAPI = api.agent
export const pipelineAPI = api.pipeline
export const knowledgeAPI = api.knowledge
export const tasksAPI = api.tasks
export const executorV2API = api.v2.executorV2
