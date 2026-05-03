/**
 * P2-9A.1: 用例类型 Tab 切换
 */
export default function CaseTypeTabs({ sourceFilter, testCases, onChangeFilter }) {
  const tabs = [
    { key: 'all', label: '全部', count: testCases.length },
    { key: 'functional', label: '功能测试', count: testCases.filter(tc => !['swagger','demo_swagger','demo_seed'].includes(tc.source) && tc.case_type !== 'web_ui').length },
    { key: 'api', label: '接口测试', count: testCases.filter(tc => ['swagger','demo_swagger','demo_seed'].includes(tc.source) || tc.case_type === 'api').length },
    { key: 'web_ui', label: 'Web UI', count: testCases.filter(tc => tc.case_type === 'web_ui').length },
  ]

  return (
    <div className="flex gap-2">
      {tabs.map(tab => (
        <button
          key={tab.key}
          onClick={() => onChangeFilter(tab.key)}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            sourceFilter === tab.key
              ? 'bg-blue-600 text-white'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          {tab.label} ({tab.count})
        </button>
      ))}
    </div>
  )
}
