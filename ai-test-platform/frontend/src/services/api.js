// API 服务配置文件
// 统一管理所有 API 调用

// ==================== API Base URL 配置 ====================
const API_BASE_URL = '/api'  // 使用代理路径，Vite会自动转发到 http://localhost:8000
const PILOT_API_BASE_URL = '/api/v2'  // Pilot路由已禁用，统一使用v2路由

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
    create: (data) => {
      // 适配后端Environment模型：name字段是枚举(dev/test/staging/prod)
      // 如果前端传了自定义名称，将其作为description，name使用env_type
      const adaptedData = {
        project_id: data.project_id,
        name: data.env_type || data.name || 'test', // 使用枚举值
        base_url: data.base_url,
        is_protected: data.is_protected || false,
        allow_write: data.allow_write !== false,
        timeout_seconds: data.timeout_seconds || 30,
        retry_count: data.retry_count || 0
      }
      return request(`${PILOT_API_BASE_URL}/environments`, {
        method: 'POST',
        body: JSON.stringify(adaptedData),
      })
    },
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
    execute: (data) => { console.warn('[DEPRECATED] api.apis.execute -> use api.v2.testCases.execute'); return request(`${API_BASE_URL}/execute-api`, { method: 'POST', body: JSON.stringify(data) }) },
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
    batchDelete: (ids) => request(`${API_BASE_URL}/v2/test-cases/batch-delete`, {
      method: 'POST',
      body: JSON.stringify({ ids }),
    }),
    generate: (file, options = {}) => {
      const formData = new FormData()
      formData.append('file', file)
      if (options.module) formData.append('module', options.module)
      if (options.count) formData.append('count', String(options.count))
      if (options.provider) formData.append('provider', options.provider)
      if (options.extra_requirements) formData.append('extra_requirements', options.extra_requirements)
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 300000)
      return fetch(`${API_BASE_URL}/ai/generate-testcases-from-file`, {
        method: 'POST',
        body: formData,
        signal: controller.signal,
      }).then(async res => {
        clearTimeout(timeoutId)
        if (!res.ok) {
          const body = await res.text().catch(() => '')
          try { const j = JSON.parse(body); throw new Error(j.error || j.detail || j.message || `HTTP ${res.status}`) } catch(e) { if (e instanceof SyntaxError) throw new Error(body || `生成失败 (HTTP ${res.status})`); throw e }
        }
        return res.json()
      }).catch(err => {
        clearTimeout(timeoutId)
        if (err.name === 'AbortError') throw new Error('AI生成超时(>5分钟)，请检查AI服务是否正常')
        throw err
      })
    },
    generateFromFolder: (folderPath, options = {}) => {
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 300000)
      return fetch(`${API_BASE_URL}/ai/generate-testcases-from-folder`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ folder_path: folderPath, ...options }),
        signal: controller.signal,
      }).then(async res => {
        clearTimeout(timeoutId)
        if (!res.ok) {
          const body = await res.text().catch(() => '')
          try { const j = JSON.parse(body); throw new Error(j.error || j.detail || j.message || `HTTP ${res.status}`) } catch(e) { if (e instanceof SyntaxError) throw new Error(body || `生成失败 (HTTP ${res.status})`); throw e }
        }
        return res.json()
      }).catch(err => {
        clearTimeout(timeoutId)
        if (err.name === 'AbortError') throw new Error('AI生成超时(>5分钟)')
        throw err
      })
    },
    generateFromSVN: (data) => request(`${API_BASE_URL}/ai/generate-testcases-from-svn`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),
    generateScript: (testCaseId) => request(`${API_BASE_URL}/testcases/${testCaseId}/generate-script`, {
      method: 'POST',
    }),
    execute: (testCaseId) => { console.warn('[DEPRECATED] api.testCases.execute -> use api.v2.testCases.execute'); return request(`${API_BASE_URL}/testcases/${testCaseId}/execute`, { method: 'POST' }) },
    manualExecute: (testCaseId, data) => { console.warn('[DEPRECATED] api.testCases.manualExecute'); return request(`${API_BASE_URL}/testcases/${testCaseId}/manual-execute`, { method: 'POST', body: JSON.stringify(data) }) },
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
      return request(`${PILOT_API_BASE_URL}/test-data/datasets${query ? '?' + query : ''}`)
    },
    create: (data) => request(`${PILOT_API_BASE_URL}/test-data/datasets`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),
    get: (id) => request(`${PILOT_API_BASE_URL}/test-data/datasets/${id}`),
    update: (id, data) => request(`${PILOT_API_BASE_URL}/test-data/datasets/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),
    delete: (id) => request(`${PILOT_API_BASE_URL}/test-data/datasets/${id}`, {
      method: 'DELETE',
    }),
    use: (id) => request(`${PILOT_API_BASE_URL}/test-data/datasets/${id}/use`, {
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
    reviewCases: (data) => request(`${PILOT_API_BASE_URL}/ai/test-cases/review`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),
    healCases: (data) => request(`${PILOT_API_BASE_URL}/ai/test-cases/heal`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),
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
      getCases: (id) => request(`${API_BASE_URL}/v2/observability/runs/${id}/cases`),
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
      generateAiAnalysis: (runId, force = false) => request(`${API_BASE_URL}/v2/test-runs/${runId}/ai-analysis`, {
        method: 'POST',
        body: JSON.stringify({ force }),
      }),
      getAiAnalysis: (runId) => request(`${API_BASE_URL}/v2/test-runs/${runId}/ai-analysis`),
    },

    dashboard: {
      getSummary: () => request(`${API_BASE_URL}/v2/dashboard/summary`),
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
        // 大文件解析+生成用例可能耗时较长，给 5 分钟超时
        const controller = new AbortController()
        const timeoutId = setTimeout(() => controller.abort(), 300000)
        return fetch(`${API_BASE_URL}/v2/swagger/import-file?project_id=${projectId}&generate_cases=${generateCases}`, {
          method: 'POST',
          body: formData,
          signal: controller.signal,
        }).then(res => {
          clearTimeout(timeoutId)
          if (!res.ok) return res.text().then(t => { throw new Error(t || `HTTP ${res.status}`) })
          return res.json()
        }).catch(err => {
          clearTimeout(timeoutId)
          if (err.name === 'AbortError') throw new Error('导入超时，文件过大请耐心等待或拆分文件')
          throw err
        })
      },
      getApiSpecs: (projectId) => {
        // 后端实际路径是 /api/v2/swagger/api-specs
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
      coverage: (projectId) => {
        const query = (projectId && !isNaN(projectId)) ? `?project_id=${projectId}` : ''
        return request(`${API_BASE_URL}/v2/swagger/coverage${query}`)
      },
    },

    // 获取系统运行模式
    getAppMode: async () => {
      try {
        const res = await fetch('/health')
        if (res.ok) {
          const data = await res.json()
          return data.app_mode || 'mock'
        }
      } catch {}
      return 'mock'
    },

    testCases: {
      getAll: (params = {}) => {
        const query = new URLSearchParams(params).toString()
        return request(`${API_BASE_URL}/v2/test-cases${query ? '?' + query : ''}`)
      },
      get: (testCaseId) => request(`${API_BASE_URL}/v2/test-cases/${testCaseId}`),
      create: (data) => request(`${API_BASE_URL}/v2/test-cases`, {
        method: 'POST',
        body: JSON.stringify(data),
      }),
      update: (testCaseId, data) => request(`${API_BASE_URL}/v2/test-cases/${testCaseId}`, {
        method: 'PUT',
        body: JSON.stringify(data),
      }),
      execute: (caseId, data = {}) => request(`${API_BASE_URL}/v2/test-cases/${caseId}/execute`, {
        method: 'POST',
        body: JSON.stringify(data),
      }),
      batchExecute: (caseIds, data = {}) => request(`${API_BASE_URL}/v2/test-cases/batch-execute`, {
        method: 'POST',
        body: JSON.stringify({ case_ids: caseIds, ...data }),
      }),
      batchExecutePreset: (preset, data = {}) => request(`${API_BASE_URL}/v2/test-cases/batch-execute`, {
        method: 'POST',
        body: JSON.stringify({ preset, skip_destructive: true, ...data }),
      }),
      previewVariables: (caseId, datasetId) => request(`${API_BASE_URL}/v2/test-cases/${caseId}/preview-variables?dataset_id=${datasetId || ''}`),
      // Phase 16: 治理
      govern: (force = false) => request(`${API_BASE_URL}/v2/test-cases/govern`, {
        method: 'POST',
        body: JSON.stringify({ force }),
      }),
      governanceSummary: () => request(`${API_BASE_URL}/v2/test-cases/governance-summary`),
      recommended: (preset, limit = 500) => request(`${API_BASE_URL}/v2/test-cases/recommended/${preset}?limit=${limit}`),
      filtered: (params = {}) => {
        const query = new URLSearchParams(params).toString()
        return request(`${API_BASE_URL}/v2/test-cases/filtered${query ? '?' + query : ''}`)
      },
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

    // ==================== Demo (Phase 17) ====================
    demo: {
      init: () => request(`${API_BASE_URL}/v2/demo/init`, { method: 'POST' }),
      reset: () => request(`${API_BASE_URL}/v2/demo/reset`, { method: 'POST' }),
      status: () => request(`${API_BASE_URL}/v2/demo/status`),
    },

    // ==================== Performance Testing (P2-6B) ====================
    performance: {
      run: (data) => request(`${API_BASE_URL}/v2/performance/run`, {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    },

    // ==================== Web UI Batch (P2-7) ====================
    webUiBatch: {
      run: (data) => request(`${API_BASE_URL}/v2/web-ui/batch-run`, {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    },

    // ==================== UI Testing ====================
    ui: {
      scanPage: (data) => request(`${API_BASE_URL}/v2/ui/scan`, {
        method: 'POST',
        body: JSON.stringify(data),
      }),
      saveLoginSession: (data) => request(`${API_BASE_URL}/v2/ui/login-session`, {
        method: 'POST',
        body: JSON.stringify(data),
      }),
      getLoginSession: (projectId) => request(`${API_BASE_URL}/v2/ui/login-session/${projectId}`),
      deleteLoginSession: (projectId) => request(`${API_BASE_URL}/v2/ui/login-session/${projectId}`, {
        method: 'DELETE',
      }),
      aiGenerate: (data) => request(`${API_BASE_URL}/v2/ui/ai-generate`, {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    },

    // ── 需求-代码对比 ──
    codeCompare: {
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
      getTapdConfig: () => request(`${API_BASE_URL}/v2/code-compare/tapd/config`),
      saveTapdConfig: (data) => request(`${API_BASE_URL}/v2/code-compare/tapd/config`, {
        method: 'POST',
        body: JSON.stringify(data),
      }),
      testTapdConnection: () => request(`${API_BASE_URL}/v2/code-compare/tapd/test`, { method: 'POST' }),
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
export const codeCompareAPI = api.v2.codeCompare
