import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

const SOURCE_LABELS = {
  product_artifact: '产品产物',
  test_case: '测试用例',
  manual: '手动创建',
};

const STATUS_LABELS = {
  created: '已创建',
  planning: '生成中',
  planned: '已生成',
  archived: '已归档',
};

const STATUS_COLORS = {
  created: 'bg-slate-100 text-slate-700',
  planning: 'bg-amber-100 text-amber-700',
  planned: 'bg-green-100 text-green-700',
  archived: 'bg-gray-100 text-gray-500',
};

export default function DevStudio() {
  const navigate = useNavigate();
  const [tasks, setTasks] = useState([]);
  const [keyword, setKeyword] = useState('');
  const [loading, setLoading] = useState(false);
  const [total, setTotal] = useState(0);

  const fetchTasks = async (kw = '') => {
    setLoading(true);
    try {
      const params = new URLSearchParams({ page: '1', page_size: '50' });
      if (kw) params.set('keyword', kw);
      const res = await fetch(`/api/v2/dev-studio/tasks?${params}`);
      const data = await res.json();
      setTasks(data.items || []);
      setTotal(data.total || 0);
    } catch (e) {
      console.error('加载失败', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchTasks(); }, []);

  const handleSearch = (e) => {
    e.preventDefault();
    fetchTasks(keyword);
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* 头部 */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-900 mb-2">AI 研发工坊</h1>
        <p className="text-slate-500">
          从 PRD / 验收标准 / 测试用例出发，AI 自动生成开发计划、API 设计、数据库设计、影响文件分析和测试计划。
        </p>
      </div>

      {/* 操作栏 */}
      <div className="flex items-center justify-between mb-6 gap-4">
        <form onSubmit={handleSearch} className="flex gap-2 flex-1 max-w-md">
          <input
            type="text"
            value={keyword}
            onChange={e => setKeyword(e.target.value)}
            placeholder="搜索开发任务..."
            className="flex-1 px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button type="submit" className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700">
            搜索
          </button>
        </form>
        <button
          onClick={() => navigate('/dev-studio/new')}
          className="px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm hover:bg-indigo-700 whitespace-nowrap"
        >
          + 新建开发任务
        </button>
      </div>

      {/* 统计 */}
      <div className="text-sm text-slate-500 mb-4">共 {total} 个开发任务</div>

      {/* 列表 */}
      {loading ? (
        <div className="text-center py-12 text-slate-400">加载中...</div>
      ) : tasks.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-slate-400 mb-4">暂无开发任务</p>
          <button
            onClick={() => navigate('/dev-studio/new')}
            className="px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm hover:bg-indigo-700"
          >
            创建第一个开发任务
          </button>
        </div>
      ) : (
        <div className="grid gap-4">
          {tasks.map(task => (
            <div
              key={task.dev_task_id}
              onClick={() => navigate(`/dev-studio/${task.dev_task_id}`)}
              className="bg-white border border-slate-200 rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <h3 className="text-base font-semibold text-slate-800 mb-1">{task.title || '未命名任务'}</h3>
                  <div className="flex items-center gap-3 text-sm text-slate-500">
                    <span className="px-2 py-0.5 rounded bg-slate-100 text-slate-600 text-xs">
                      {SOURCE_LABELS[task.source_type] || task.source_type}
                    </span>
                    <span className={`px-2 py-0.5 rounded text-xs ${STATUS_COLORS[task.status] || 'bg-slate-100 text-slate-600'}`}>
                      {STATUS_LABELS[task.status] || task.status}
                    </span>
                    {task.idea_id && <span className="text-xs text-blue-500">idea: {task.idea_id.slice(0, 12)}...</span>}
                    <span>{task.created_at?.slice(0, 16).replace('T', ' ')}</span>
                  </div>
                  {task.description && (
                    <p className="text-sm text-slate-500 mt-2 line-clamp-2">{task.description}</p>
                  )}
                </div>
                <span className="text-slate-400 text-sm">→</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
