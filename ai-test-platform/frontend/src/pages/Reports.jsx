import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { reportsAPI } from '../services/api'
import api from '../services/api'

export default function Reports() {
  const navigate = useNavigate()
  const [reports, setReports] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [testRuns, setTestRuns] = useState([])
  const [showGenerateDialog, setShowGenerateDialog] = useState(false)
  const [selectedTestRun, setSelectedTestRun] = useState('')
  const [generating, setGenerating] = useState(false)

  useEffect(() => {
    loadReports()
    loadTestRuns()
  }, [])

  const loadReports = async () => {
    setLoading(true)
    try {
      const data = await reportsAPI.getAll()
      setReports(data.items || [])
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const loadTestRuns = async () => {
    try {
      const data = await api.v2.testRuns.getList({ limit: 50 })
      const runs = Array.isArray(data) ? data : (data.items || data.testRuns || [])
      setTestRuns(runs.filter(r => r.status === 'passed' || r.status === 'failed'))
    } catch {}
  }

  const handleGenerateReport = async () => {
    if (!selectedTestRun) return
    try {
      setGenerating(true)
      await reportsAPI.generate({ run_id: selectedTestRun })
      await loadReports()
      setShowGenerateDialog(false)
      setSelectedTestRun('')
    } catch (error) {
      alert('生成报告失败: ' + error.message)
    } finally {
      setGenerating(false)
    }
  }

  const getPassRateColor = (rate) => {
    if (rate >= 90) return 'text-green-600'
    if (rate >= 75) return 'text-yellow-600'
    return 'text-red-600'
  }

  const avgPassRate = reports.length
    ? Math.round(reports.reduce((s, r) => s + (r.pass_rate || 0), 0) / reports.length)
    : 0

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">测试报告</h1>
          <p className="text-slate-500 text-sm">查看和分析测试执行报告</p>
        </div>
        <button
          className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700"
          onClick={() => setShowGenerateDialog(true)}
        >
          生成报告
        </button>
      </div>

      {/* Generate Dialog */}
      {showGenerateDialog && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl p-6 max-w-md w-full">
            <h3 className="text-lg font-semibold mb-4">生成测试报告</h3>
            <label className="block text-sm font-medium text-slate-700 mb-2">选择测试运行</label>
            <select
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm mb-4"
              value={selectedTestRun}
              onChange={e => setSelectedTestRun(e.target.value)}
            >
              <option value="">请选择...</option>
              {testRuns.map(run => (
                <option key={run.id} value={run.id}>
                  {run.id} — {run.status} ({run.passed_cases || 0}/{run.total_cases || 0} 通过)
                </option>
              ))}
            </select>
            <div className="flex gap-2 justify-end">
              <button className="px-4 py-2 border border-slate-300 rounded-lg text-sm" onClick={() => { setShowGenerateDialog(false); setSelectedTestRun('') }}>取消</button>
              <button
                className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm disabled:opacity-50"
                onClick={handleGenerateReport}
                disabled={generating || !selectedTestRun}
              >
                {generating ? '生成中...' : '生成报告'}
              </button>
            </div>
          </div>
        </div>
      )}

      {loading && <p className="text-slate-500 text-sm">加载中...</p>}
      {error && <div className="p-3 bg-red-50 text-red-600 rounded-lg text-sm">加载失败: {error}</div>}

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-4 text-center">
          <div className="text-2xl font-bold text-blue-600">{reports.length}</div>
          <div className="text-sm text-slate-500">报告总数</div>
        </div>
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-4 text-center">
          <div className={`text-2xl font-bold ${getPassRateColor(avgPassRate)}`}>{avgPassRate}%</div>
          <div className="text-sm text-slate-500">平均通过率</div>
        </div>
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-4 text-center">
          <div className="text-2xl font-bold text-purple-600">{reports.reduce((s, r) => s + (r.total_tests || 0), 0)}</div>
          <div className="text-sm text-slate-500">总用例数</div>
        </div>
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-4 text-center">
          <div className="text-2xl font-bold text-red-600">{reports.reduce((s, r) => s + (r.failed || 0), 0)}</div>
          <div className="text-sm text-slate-500">总失败数</div>
        </div>
      </div>

      {/* Reports list */}
      {!loading && reports.length === 0 && (
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-12 text-center">
          <p className="text-lg text-slate-500">暂无报告，请先执行测试并生成报告。</p>
        </div>
      )}

      <div className="space-y-3">
        {reports.map(r => (
          <div key={r.report_id} className="bg-white rounded-xl shadow-sm border border-slate-200 p-4 flex items-center justify-between hover:shadow-md transition">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <h3 className="font-medium text-slate-900 truncate">{r.title}</h3>
                {r.app_mode === 'real' && (
                  <span className="px-2 py-0.5 text-xs rounded-full bg-red-100 text-red-700 font-medium">真实模式</span>
                )}
                {r.app_mode === 'real' && r.allow_unsafe_methods && (
                  <span className="px-2 py-0.5 text-xs rounded-full bg-orange-100 text-orange-700 font-medium">含写操作</span>
                )}
              </div>
              <div className="text-sm text-slate-500 mt-1 flex gap-4 flex-wrap">
                <span>类型: {r.report_type}</span>
                <span>用例: {r.total_tests || 0}</span>
                <span className={getPassRateColor(r.pass_rate || 0)}>通过率: {r.pass_rate || 0}%</span>
                <span>通过: {r.passed || 0}</span>
                <span className="text-red-600">失败: {r.failed || 0}</span>
                <span>{r.created_at ? new Date(r.created_at).toLocaleString() : ''}</span>
              </div>
            </div>
            <div className="flex gap-2 ml-4 shrink-0">
              <button
                className="px-3 py-1.5 text-sm border border-slate-300 rounded-lg hover:bg-slate-50"
                onClick={() => navigate(`/reports/${r.report_id}`)}
              >
                详情
              </button>
              {r.download_url && (
                <a
                  href={r.download_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="px-3 py-1.5 text-sm border border-slate-300 rounded-lg hover:bg-slate-50"
                >
                  下载
                </a>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
