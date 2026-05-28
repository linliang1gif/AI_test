const HINTS = {
  PLAYWRIGHT_BROWSER_MISSING: {
    title: 'Playwright 浏览器未安装',
    reason: '后端无法启动 Chromium 浏览器。',
    suggestion: '请在后端环境运行 python -m playwright install chromium 后重启服务。',
  },
  AUTH_PROFILE_MISSING: {
    title: 'Web UI 登录态不存在',
    reason: '没有可用于 Web UI 自动化的 token、Cookie 或 localStorage。',
    suggestion: '请重新保存 Web UI 登录会话，或在环境中配置有效鉴权。',
  },
  AUTH_TOKEN_INVALID: {
    title: '登录态已失效',
    reason: '当前 token 过期、无效，或不是可用的 access_token。',
    suggestion: '请重新登录目标系统并保存新的 Web UI 登录会话。',
  },
  AUTH_TOKEN_BLACKLISTED: {
    title: '登录态已进入黑名单',
    reason: '目标系统已拒绝当前 token。',
    suggestion: '请重新登录并保存新的 access_token，避免继续使用旧 token。',
  },
  WEB_UI_LOGIN_REQUIRED: {
    title: '目标页面跳转到登录页',
    reason: '打开目标页面后被重定向到 SSO 或 login 页面。',
    suggestion: '请重新保存 Web UI 登录会话，并确认账号有该页面权限。',
  },
  TARGET_SYSTEM_UNREACHABLE: {
    title: '目标系统不可访问',
    reason: '后端无法访问目标系统地址。',
    suggestion: '请检查目标系统地址、网络、VPN、代理和环境配置。',
  },
  UNKNOWN_EXECUTION_ERROR: {
    title: '执行失败',
    reason: '执行过程中发生未知错误。',
    suggestion: '请查看 trace_id 和原始错误详情定位后端日志。',
  },
}

export function parseApiError(error) {
  const fallback = {
    code: 'UNKNOWN_EXECUTION_ERROR',
    message: error?.message || '执行失败',
    details: {},
    raw: error?.message || '',
  }

  if (error?.data && typeof error.data === 'object') {
    return { ...fallback, ...error.data, raw: error.data }
  }

  const text = error?.message || ''
  const match = text.match(/^API调用失败:\s*\d+\s*(.*)$/s)
  const raw = match ? match[1] : text
  try {
    const parsed = JSON.parse(raw)
    return { ...fallback, ...parsed, raw: parsed }
  } catch {
    return { ...fallback, raw }
  }
}

export function getErrorHint(error) {
  const parsed = parseApiError(error)
  const hint = HINTS[parsed.code] || HINTS.UNKNOWN_EXECUTION_ERROR
  const details = parsed.details && typeof parsed.details === 'object' ? parsed.details : {}
  return {
    code: parsed.code || 'UNKNOWN_EXECUTION_ERROR',
    title: hint.title,
    reason: parsed.message || hint.reason,
    suggestion: parsed.suggestion || details.suggestion || hint.suggestion,
    traceId: parsed.trace_id || details.trace_id || '',
    details,
    raw: parsed.raw,
  }
}

export function formatErrorHintText(error, prefix = '执行失败') {
  const hint = getErrorHint(error)
  return [
    `${prefix}: ${hint.title}`,
    `原因: ${hint.reason}`,
    `建议: ${hint.suggestion}`,
    hint.traceId ? `trace_id: ${hint.traceId}` : '',
  ].filter(Boolean).join('\n')
}
