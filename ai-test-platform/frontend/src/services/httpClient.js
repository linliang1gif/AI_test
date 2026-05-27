// 统一请求基础层，供 services/api.js 及后续拆分模块复用。
export const API_BASE_URL = '/api'
export const PILOT_API_BASE_URL = '/api/v2'

export function generateTraceId() {
  const ts = Date.now().toString(36)
  const rand = Math.random().toString(36).substring(2, 10)
  return `fe-${ts}-${rand}`
}

export function getRoleHeader() {
  const role = localStorage.getItem('pilot_role') || 'admin'
  return { 'X-User-Role': role }
}

export async function request(url, config = {}) {
  const defaultConfig = {
    headers: {
      'Content-Type': 'application/json',
      'X-Trace-Id': generateTraceId(),
      ...getRoleHeader(),
      ...config.headers,
    },
    ...config,
  }

  try {
    const response = await fetch(url, defaultConfig)

    if (!response.ok) {
      const errorText = await response.text()

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
    if (!error.message.startsWith('404')) {
      console.error('API请求错误:', error)
    }
    throw error
  }
}