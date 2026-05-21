/**
 * 新组件使用演示
 * 这个文件展示了如何使用新添加的UI组件
 */

import { useState } from 'react'
import { useToast } from './src/components/ui/Toast'
import ConfirmDialog from './src/components/ui/ConfirmDialog'
import { Skeleton, SkeletonText, SkeletonCard, SkeletonTable, SkeletonDetailPage } from './src/components/ui/Skeleton'
import PageHeader from './src/components/PageHeader'
import DetailCard from './src/components/DetailCard'

// ============================================
// 1. Toast 通知组件演示
// ============================================
function ToastDemo() {
  const toast = useToast()

  return (
    <div className="space-y-4 p-6">
      <h2 className="text-xl font-bold">Toast 通知演示</h2>
      
      <div className="flex gap-3">
        <button
          onClick={() => toast.success('操作成功！')}
          className="px-4 py-2 bg-green-600 text-white rounded-md"
        >
          成功提示
        </button>
        
        <button
          onClick={() => toast.error('操作失败，请重试')}
          className="px-4 py-2 bg-red-600 text-white rounded-md"
        >
          错误提示
        </button>
        
        <button
          onClick={() => toast.warning('请注意检查数据')}
          className="px-4 py-2 bg-yellow-600 text-white rounded-md"
        >
          警告提示
        </button>
        
        <button
          onClick={() => toast.info('这是一条信息', 5000)}
          className="px-4 py-2 bg-blue-600 text-white rounded-md"
        >
          信息提示（5秒）
        </button>
      </div>
    </div>
  )
}

// ============================================
// 2. 确认对话框演示
// ============================================
function ConfirmDialogDemo() {
  const [showWarning, setShowWarning] = useState(false)
  const [showDanger, setShowDanger] = useState(false)
  const [showInfo, setShowInfo] = useState(false)
  const [loading, setLoading] = useState(false)
  const toast = useToast()

  const handleConfirm = async (type) => {
    setLoading(true)
    // 模拟异步操作
    await new Promise(resolve => setTimeout(resolve, 1500))
    setLoading(false)
    
    // 关闭对话框
    setShowWarning(false)
    setShowDanger(false)
    setShowInfo(false)
    
    toast.success(`${type}操作已确认`)
  }

  return (
    <div className="space-y-4 p-6">
      <h2 className="text-xl font-bold">确认对话框演示</h2>
      
      <div className="flex gap-3">
        <button
          onClick={() => setShowWarning(true)}
          className="px-4 py-2 bg-yellow-600 text-white rounded-md"
        >
          警告对话框
        </button>
        
        <button
          onClick={() => setShowDanger(true)}
          className="px-4 py-2 bg-red-600 text-white rounded-md"
        >
          危险对话框
        </button>
        
        <button
          onClick={() => setShowInfo(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded-md"
        >
          信息对话框
        </button>
      </div>

      {/* 警告对话框 */}
      <ConfirmDialog
        isOpen={showWarning}
        onClose={() => setShowWarning(false)}
        onConfirm={() => handleConfirm('警告')}
        title="确认操作"
        message="此操作可能会影响系统性能，确定要继续吗？"
        confirmText="继续"
        cancelText="取消"
        type="warning"
        loading={loading}
      />

      {/* 危险对话框 */}
      <ConfirmDialog
        isOpen={showDanger}
        onClose={() => setShowDanger(false)}
        onConfirm={() => handleConfirm('删除')}
        title="删除确认"
        message="确定要删除此项吗？此操作不可恢复，所有相关数据也将被删除。"
        confirmText="删除"
        cancelText="取消"
        type="danger"
        loading={loading}
      />

      {/* 信息对话框 */}
      <ConfirmDialog
        isOpen={showInfo}
        onClose={() => setShowInfo(false)}
        onConfirm={() => handleConfirm('信息')}
        title="提示"
        message="是否要保存当前的更改？"
        confirmText="保存"
        cancelText="取消"
        type="info"
        loading={loading}
      />
    </div>
  )
}

// ============================================
// 3. 骨架屏演示
// ============================================
function SkeletonDemo() {
  const [loading, setLoading] = useState(true)

  return (
    <div className="space-y-6 p-6">
      <h2 className="text-xl font-bold">骨架屏演示</h2>
      
      <button
        onClick={() => setLoading(!loading)}
        className="px-4 py-2 bg-blue-600 text-white rounded-md"
      >
        {loading ? '显示内容' : '显示骨架屏'}
      </button>

      {loading ? (
        <div className="space-y-6">
          {/* 基础骨架屏 */}
          <div>
            <h3 className="text-lg font-semibold mb-3">基础骨架屏</h3>
            <Skeleton className="w-full h-4 mb-2" />
            <Skeleton className="w-3/4 h-4 mb-2" />
            <Skeleton className="w-1/2 h-4" />
          </div>

          {/* 文本骨架屏 */}
          <div>
            <h3 className="text-lg font-semibold mb-3">文本骨架屏</h3>
            <SkeletonText lines={4} />
          </div>

          {/* 卡片骨架屏 */}
          <div>
            <h3 className="text-lg font-semibold mb-3">卡片骨架屏</h3>
            <div className="grid grid-cols-3 gap-4">
              <SkeletonCard />
              <SkeletonCard />
              <SkeletonCard />
            </div>
          </div>

          {/* 表格骨架屏 */}
          <div>
            <h3 className="text-lg font-semibold mb-3">表格骨架屏</h3>
            <SkeletonTable rows={5} columns={4} />
          </div>
        </div>
      ) : (
        <div className="space-y-6">
          <div className="p-4 bg-white border border-slate-200 rounded-md">
            <h3 className="text-lg font-semibold mb-2">实际内容</h3>
            <p className="text-slate-600">这是加载完成后显示的实际内容</p>
          </div>
        </div>
      )}
    </div>
  )
}

// ============================================
// 4. PageHeader 演示
// ============================================
function PageHeaderDemo() {
  const toast = useToast()

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-bold p-6">PageHeader 演示</h2>
      
      {/* 带返回按钮的页面头部 */}
      <PageHeader
        showBack={true}
        breadcrumbs={[
          { label: '首页', href: '/' },
          { label: '项目管理', href: '/projects' },
          { label: '项目详情' }
        ]}
        title="企业管理系统"
        description="这是一个企业级管理系统项目"
        meta={
          <div className="flex items-center space-x-3 mt-2">
            <span className="px-2 py-1 bg-green-100 text-green-700 rounded text-sm">
              进行中
            </span>
            <span className="text-sm text-slate-600">版本: v2.1.0</span>
          </div>
        }
        actions={[
          {
            label: '编辑',
            onClick: () => toast.info('编辑项目'),
            variant: 'default'
          },
          {
            label: '发布',
            onClick: () => toast.success('项目已发布'),
            variant: 'primary'
          }
        ]}
      />
    </div>
  )
}

// ============================================
// 5. DetailCard 演示
// ============================================
function DetailCardDemo() {
  return (
    <div className="space-y-6 p-6">
      <h2 className="text-xl font-bold">DetailCard 演示</h2>
      
      {/* 基础卡片 */}
      <DetailCard title="基本信息">
        <div className="space-y-3">
          <div className="flex justify-between">
            <span className="text-slate-600">项目名称</span>
            <span className="text-slate-900 font-medium">企业管理系统</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-600">创建时间</span>
            <span className="text-slate-900">2024-01-15</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-600">负责人</span>
            <span className="text-slate-900">张三</span>
          </div>
        </div>
      </DetailCard>

      {/* 带额外操作的卡片 */}
      <DetailCard 
        title="项目统计" 
        extra={
          <button className="text-sm text-blue-600 hover:text-blue-700">
            查看详情
          </button>
        }
      >
        <div className="grid grid-cols-3 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-slate-900">156</div>
            <div className="text-sm text-slate-600">测试用例</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">142</div>
            <div className="text-sm text-slate-600">通过</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-red-600">14</div>
            <div className="text-sm text-slate-600">失败</div>
          </div>
        </div>
      </DetailCard>
    </div>
  )
}

// ============================================
// 完整演示页面
// ============================================
export default function ComponentDemo() {
  return (
    <div className="min-h-screen bg-slate-50">
      <div className="max-w-7xl mx-auto py-8 space-y-8">
        <div className="bg-white rounded-lg shadow-sm">
          <ToastDemo />
        </div>
        
        <div className="bg-white rounded-lg shadow-sm">
          <ConfirmDialogDemo />
        </div>
        
        <div className="bg-white rounded-lg shadow-sm">
          <SkeletonDemo />
        </div>
        
        <div className="bg-white rounded-lg shadow-sm">
          <PageHeaderDemo />
        </div>
        
        <div className="bg-white rounded-lg shadow-sm">
          <DetailCardDemo />
        </div>
      </div>
    </div>
  )
}

// ============================================
// 使用提示
// ============================================
/*
1. Toast 使用：
   - 必须在 ToastProvider 内部使用
   - 通过 useToast() hook 调用
   - 支持自定义显示时长

2. ConfirmDialog 使用：
   - 通过 state 控制显示/隐藏
   - loading 状态需要手动管理
   - 支持3种类型：warning, danger, info

3. Skeleton 使用：
   - 在数据加载时显示
   - 结构应该与实际内容一致
   - 提供多种预设组件

4. PageHeader 使用：
   - showBack 控制返回按钮
   - breadcrumbs 支持点击导航
   - actions 支持多个操作按钮

5. DetailCard 使用：
   - 用于详情页的信息展示
   - extra 可以添加额外操作
   - 支持响应式布局
*/
