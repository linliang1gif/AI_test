import React, { useState, useEffect } from 'react'
import { reportsAPI } from '../services/api'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { 
  FileText, 
  Download, 
  Eye, 
  Calendar,
  TrendingUp,
  AlertTriangle,
  CheckCircle,
  BarChart3,
  PieChart
} from 'lucide-react'

export default function Reports() {
  const [reports, setReports] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [selectedReport, setSelectedReport] = useState(null)
  const [testRuns, setTestRuns] = useState([])
  const [showGenerateDialog, setShowGenerateDialog] = useState(false)
  const [selectedTestRun, setSelectedTestRun] = useState(null)
  const [generating, setGenerating] = useState(false)

  useEffect(() => {
    loadReports()
    loadTestRuns()
  }, [])

  const loadReports = () => {
    reportsAPI.getAll()
      .then(data => {
        const list = data.reports || []
        setReports(list)
        if (list.length > 0) setSelectedReport(list[0])
      })
      .catch(err => setError(err.message))
      .finally(() => setLoading(false))
  }

  const loadTestRuns = () => {
    fetch('/api/test-runs')
      .then(res => {
        if (!res.ok) throw new Error('HTTP error! status: ' + res.status)
        return res.json()
      })
      .then(data => {
        const runs = data.testRuns || []
        // 只显示已完成的测试运行
        setTestRuns(runs.filter(r => r.status === 'completed'))
      })
      .catch(err => console.error('加载测试运行失败:', err))
  }

  const handleGenerateReport = async () => {
    alert('当前后端未开放 /api/reports/generate 接口，请先通过测试执行流程自动生成报告。')
  }

  const handleViewReport = async (report) => {
    try {
      const data = await reportsAPI.getById(report.id)
      alert(JSON.stringify(data.report || report, null, 2))
    } catch (err) {
      alert('获取报告详情失败: ' + err.message)
    }
  }

  const handleDownloadReport = async (report) => {
    await handleViewReport(report)
  }

  const handleDeleteReport = async (report) => {
    alert('当前后端未开放删除报告接口。')
  }

  const getTypeColor = (type) => {
    switch (type) {
      case 'Comprehensive Report': return 'bg-blue-100 text-blue-800'
      case 'Coverage Report': return 'bg-green-100 text-green-800'
      case 'Healing Report': return 'bg-purple-100 text-purple-800'
      case 'Bug Report': return 'bg-red-100 text-red-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getPassRateColor = (rate) => {
    if (rate >= 90) return 'text-green-600'
    if (rate >= 75) return 'text-yellow-600'
    return 'text-red-600'
  }

  const ReportCard = ({ report }) => (
    <Card 
      className={`cursor-pointer transition-all hover:shadow-md ${
        selectedReport?.id === report.id ? 'ring-2 ring-blue-500' : ''
      }`}
      onClick={() => setSelectedReport(report)}
    >
      <CardContent className="p-4">
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <FileText className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <h3 className="font-medium text-gray-900">{report.name}</h3>
              <span className={`inline-block px-2 py-1 rounded-full text-xs font-medium ${getTypeColor(report.type)} mt-1`}>
                {report.type}
              </span>
            </div>
          </div>
          <div className="text-right text-sm text-gray-600">
            <p>{report.date}</p>
            <p>{report.size}</p>
          </div>
        </div>
        
        <div className="grid grid-cols-3 gap-4 text-center text-sm mb-3">
          <div>
            <p className="font-medium text-gray-900">{report.testRuns}</p>
            <p className="text-gray-500">测试运行</p>
          </div>
          <div>
            <p className={`font-medium ${getPassRateColor(report.passRate)}`}>
              {report.passRate}%
            </p>
            <p className="text-gray-500">通过率</p>
          </div>
          <div>
            <p className="font-medium text-gray-900">{report.format}</p>
            <p className="text-gray-500">格式</p>
          </div>
        </div>
        
        <div className="flex space-x-2">
          <Button size="sm" variant="outline" className="flex-1" onClick={() => handleViewReport(report)}>
            <Eye className="w-3 h-3 mr-1" />
            查看
          </Button>
          <Button size="sm" variant="outline" className="flex-1" onClick={() => handleDownloadReport(report)}>
            <Download className="w-3 h-3 mr-1" />
            下载
          </Button>
          <Button size="sm" variant="outline" onClick={(e) => { e.stopPropagation(); handleDeleteReport(report); }}>
            <span className="text-red-600">删除</span>
          </Button>
        </div>
      </CardContent>
    </Card>
  )

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">测试报告</h1>
          <p className="text-gray-600">查看和分析测试执行报告</p>
        </div>
        <Button className="bg-blue-600 hover:bg-blue-700" onClick={() => setShowGenerateDialog(true)}>
          <FileText className="w-4 h-4 mr-2" />
          生成报告
        </Button>
      </div>

      {/* Generate Report Dialog */}
      {showGenerateDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full">
            <h3 className="text-lg font-semibold mb-4">生成测试报告</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  选择测试运行
                </label>
                <select
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  value={selectedTestRun || ''}
                  onChange={(e) => setSelectedTestRun(Number(e.target.value))}
                >
                  <option value="">请选择...</option>
                  {testRuns.map(run => (
                    <option key={run.id} value={run.id}>
                      {run.name} - {run.passed}/{run.totalTests} 通过
                    </option>
                  ))}
                </select>
              </div>
              <div className="flex space-x-2 justify-end">
                <Button variant="outline" onClick={() => { setShowGenerateDialog(false); setSelectedTestRun(null); }}>
                  取消
                </Button>
                <Button 
                  className="bg-blue-600 hover:bg-blue-700" 
                  onClick={handleGenerateReport}
                  disabled={generating || !selectedTestRun}
                >
                  {generating ? '生成中...' : '生成报告'}
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}

      {loading && <p className="text-gray-500 text-sm">加载中...</p>}
      {error && <div className="p-3 bg-red-50 text-red-600 rounded-md text-sm">加载失败: {error}</div>}

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4 text-center">
            <div className="flex items-center justify-center mb-2">
              <FileText className="w-8 h-8 text-blue-600" />
            </div>
            <p className="text-2xl font-bold text-blue-600">{reports.length}</p>
            <p className="text-sm text-gray-600">报告总数</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <div className="flex items-center justify-center mb-2">
              <TrendingUp className="w-8 h-8 text-green-600" />
            </div>
            <p className="text-2xl font-bold text-green-600">
              {reports.length ? Math.round(reports.reduce((sum, r) => sum + r.passRate, 0) / reports.length) : 0}%
            </p>
            <p className="text-sm text-gray-600">平均通过率</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <div className="flex items-center justify-center mb-2">
              <CheckCircle className="w-8 h-8 text-purple-600" />
            </div>
            <p className="text-2xl font-bold text-purple-600">
              {reports.reduce((sum, r) => sum + r.testRuns, 0)}
            </p>
            <p className="text-sm text-gray-600">测试运行总数</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <div className="flex items-center justify-center mb-2">
              <Calendar className="w-8 h-8 text-orange-600" />
            </div>
            <p className="text-2xl font-bold text-orange-600">7</p>
            <p className="text-sm text-gray-600">天覆盖</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Reports List */}
        <div className="lg:col-span-2 space-y-4">
          <h2 className="text-xl font-semibold">最近的报告</h2>
          <div className="space-y-4">
            {reports.map((report) => (
              <ReportCard key={report.id} report={report} />
            ))}
          </div>
        </div>

        {/* Report Preview */}
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>报告预览</CardTitle>
            </CardHeader>
            <CardContent>
              {selectedReport && (
                <div className="space-y-4">
                  <div>
                    <h3 className="font-medium mb-2">{selectedReport.name}</h3>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-600">类型:</span>
                        <span className={`px-2 py-1 rounded text-xs ${getTypeColor(selectedReport.type)}`}>
                          {selectedReport.type}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">日期:</span>
                        <span>{selectedReport.date}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">大小:</span>
                        <span>{selectedReport.size}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">通过率:</span>
                        <span className={getPassRateColor(selectedReport.passRate)}>
                          {selectedReport.passRate}%
                        </span>
                      </div>
                    </div>
                  </div>
                  
                  {/* Mock Report Content */}
                  <div className="border rounded-lg p-4 bg-gray-50">
                    <h4 className="font-medium mb-3">报告摘要</h4>
                    <div className="space-y-2 text-sm">
                      <div className="flex items-center space-x-2">
                        <CheckCircle className="w-4 h-4 text-green-500" />
                        <span>142 个测试通过</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <AlertTriangle className="w-4 h-4 text-red-500" />
                        <span>18 个测试失败</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <BarChart3 className="w-4 h-4 text-blue-500" />
                        <span>85% 代码覆盖率</span>
                      </div>
                    </div>
                  </div>
                  
                  <div className="space-y-2">
                    <Button className="w-full" onClick={() => handleViewReport(selectedReport)}>
                      <Eye className="w-4 h-4 mr-2" />
                      查看完整报告
                    </Button>
                    <Button variant="outline" className="w-full" onClick={() => handleDownloadReport(selectedReport)}>
                      <Download className="w-4 h-4 mr-2" />
                      下载报告
                    </Button>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Report Types */}
          <Card>
            <CardHeader>
              <CardTitle>报告类型</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex items-center space-x-3 p-2 bg-blue-50 rounded">
                <BarChart3 className="w-5 h-5 text-blue-600" />
                <div>
                  <p className="font-medium text-blue-800">综合报告</p>
                  <p className="text-xs text-blue-600">完整的测试执行报告</p>
                </div>
              </div>
              <div className="flex items-center space-x-3 p-2 bg-green-50 rounded">
                <PieChart className="w-5 h-5 text-green-600" />
                <div>
                  <p className="font-medium text-green-800">覆盖率报告</p>
                  <p className="text-xs text-green-600">测试覆盖率分析</p>
                </div>
              </div>
              <div className="flex items-center space-x-3 p-2 bg-purple-50 rounded">
                <TrendingUp className="w-5 h-5 text-purple-600" />
                <div>
                  <p className="font-medium text-purple-800">自愈报告</p>
                  <p className="text-xs text-purple-600">自动修复活动日志</p>
                </div>
              </div>
              <div className="flex items-center space-x-3 p-2 bg-red-50 rounded">
                <AlertTriangle className="w-5 h-5 text-red-600" />
                <div>
                  <p className="font-medium text-red-800">Bug分析</p>
                  <p className="text-xs text-red-600">失败分析报告</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Export Options */}
      <Card>
        <CardHeader>
          <CardTitle>导出和分享</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium">批量导出</p>
              <p className="text-sm text-gray-600">以不同格式导出多个报告</p>
            </div>
            <div className="flex space-x-2">
              <Button variant="outline" onClick={() => alert('PDF导出功能暂未实现')}>
                导出为PDF
              </Button>
              <Button variant="outline" onClick={() => alert('Excel导出功能暂未实现')}>
                导出为Excel
              </Button>
              <Button variant="outline" onClick={() => alert('邮件分享功能暂未实现')}>
                通过邮件分享
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
