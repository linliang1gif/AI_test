import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

const TYPE_LABELS = {
  product_solution: '产品方案',
  prd: 'PRD',
  prototype: '原型',
  test_strategy: '测试策略',
  acceptance_criteria: '验收标准',
};

export default function ProductStudio() {
  const navigate = useNavigate();
  const [ideas, setIdeas] = useState([]);
  const [keyword, setKeyword] = useState('');
  const [loading, setLoading] = useState(false);
  const [total, setTotal] = useState(0);

  const fetchIdeas = async (kw = '') => {
    setLoading(true);
    try {
      const params = new URLSearchParams({ page: '1', page_size: '50' });
      if (kw) params.set('keyword', kw);
      const res = await fetch(`/api/v2/product-studio/ideas?${params}`);
      const data = await res.json();
      setIdeas(data.items || []);
      setTotal(data.total || 0);
    } catch (e) {
      console.error('加载失败', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchIdeas(); }, []);

  const handleSearch = (e) => {
    e.preventDefault();
    fetchIdeas(keyword);
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* 头部 */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-900 mb-2">AI 产品工坊</h1>
        <p className="text-slate-500">
          从产品想法出发，AI 自动生成产品方案、PRD、原型说明、测试策略和验收标准。
        </p>
      </div>

      {/* 操作栏 */}
      <div className="flex items-center justify-between mb-6 gap-4">
        <form onSubmit={handleSearch} className="flex gap-2 flex-1 max-w-md">
          <input
            type="text"
            value={keyword}
            onChange={e => setKeyword(e.target.value)}
            placeholder="搜索产品想法..."
            className="flex-1 px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            type="submit"
            className="px-4 py-2 bg-slate-100 text-slate-700 rounded-lg text-sm hover:bg-slate-200"
          >
            搜索
          </button>
        </form>
        <button
          onClick={() => navigate('/product-studio/new')}
          className="px-5 py-2.5 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 shadow-sm"
        >
          + 新建产品想法
        </button>
      </div>

      {/* 列表 */}
      {loading ? (
        <div className="text-center py-20 text-slate-400">加载中...</div>
      ) : ideas.length === 0 ? (
        <div className="text-center py-20">
          <div className="text-4xl mb-4">💡</div>
          <p className="text-slate-500 mb-4">还没有产品想法，点击上方按钮开始</p>
        </div>
      ) : (
        <div className="space-y-3">
          <div className="text-sm text-slate-500 mb-2">共 {total} 个想法</div>
          {ideas.map(idea => {
            const s = idea.artifact_summary || {};
            return (
              <div
                key={idea.idea_id}
                onClick={() => navigate(`/product-studio/${idea.idea_id}`)}
                className="bg-white border border-slate-200 rounded-xl p-5 hover:shadow-md hover:border-blue-200 cursor-pointer transition-all"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h3 className="text-base font-semibold text-slate-900 mb-1">{idea.title}</h3>
                    <p className="text-sm text-slate-500 line-clamp-1">
                      {idea.product_direction || idea.pain_points || '暂无描述'}
                    </p>
                  </div>
                  <div className="text-xs text-slate-400 whitespace-nowrap ml-4">
                    {idea.created_at ? new Date(idea.created_at).toLocaleDateString() : ''}
                  </div>
                </div>
                {/* 标签 */}
                <div className="flex gap-2 mt-3 flex-wrap">
                  {Object.entries(TYPE_LABELS).map(([key, label]) => {
                    const has = s[`has_${key === 'product_solution' ? 'solution' : key}`];
                    return (
                      <span
                        key={key}
                        className={`px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          has
                            ? 'bg-green-50 text-green-700 border border-green-200'
                            : 'bg-slate-50 text-slate-400 border border-slate-100'
                        }`}
                      >
                        {has ? '✓' : '○'} {label}
                      </span>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
