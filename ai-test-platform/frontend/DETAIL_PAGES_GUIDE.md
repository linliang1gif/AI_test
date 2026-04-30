# 详情页面使用指南

## 已完成的重构

### 1. 通用组件
已创建以下企业级通用组件：

- **PageHeader** - 页面头部组件
  - 面包屑导航
  - 标题和描述
  - 操作按钮组
  - 元数据展示

- **DetailCard** - 详情卡片组件
  - 统一的卡片样式
  - 标题和额外操作区
  - 6px圆角

- **StatusBadge** - 状态标签组件
  - Success/Warning/Error三色系统
  - 小/中/大三种尺寸
  - 统一的视觉风格

- **MetaInfo** - 元数据信息组件
  - 网格布局
  - 标签-值对展示
  - 响应式设计

- **EmptyState** - 空状态组件
  - 图标+文字+操作按钮
  - 统一的空状态体验

### 2. 详情页面

#### 测试用例详情页 (`/test-cases/:id`)
- 面包屑导航：测试管理 > 测试用例 > 用例名称
- 基本信息卡片：创建人、时间、版本等8个字段
- Tab标签页：
  - 用例详情：描述、前置条件、测试步骤、预期结果、测试数据
  - 执行历史：历史执行记录列表
- 操作按钮：执行测试、编辑、更多（删除）
- 状态标签：通过/失败/待执行
- 优先级标签：高/中/低

#### 测试报告详情页 (`/reports/:id`)
- 面包屑导航：测试管理 > 测试报告 > 报告名称
- 基本信息卡片：创建人、时间、耗时等8个字段
- 统计概览：4个统计卡片（总数/通过/失败/跳过）
- Tab标签页：
  - 测试概览：通过率分布、关键指标
  - 用例明细：测试用例表格
  - 趋势分析：近7日通过率趋势图
- 操作按钮：下载报告、分享

#### 项目详情页 (`/projects/:id`)
- 面包屑导航：项目管理 > 项目名称
- 基本信息卡片：负责人、团队、创建人等8个字段
- 统计概览：4个统计卡片（API/用例/覆盖率/通过率）
- Tab标签页：
  - 项目概览：描述、基础URL、最近活动
  - 团队成员：成员列表卡片
  - 配置信息：执行配置、通知配置
- 操作按钮：项目设置、更多（删除）

### 3. 路由配置
已在App.jsx中添加以下路由：
```javascript
<Route path="/test-cases/:id" element={<TestCaseDetail />} />
<Route path="/reports/:id" element={<ReportDetail />} />
<Route path="/projects/:id" element={<ProjectDetail />} />
```

### 4. 列表页跳转
已更新以下列表页，支持点击跳转到详情页：
- ProjectsPro.jsx - 项目名称点击跳转
- Reports.jsx - 查看按钮跳转
- TestCases.jsx - 查看详情按钮跳转

### 5. 样式规范
已创建 `src/styles/enterprise.css` 统一样式：
- 圆角：统一6px
- 主色调：slate-700 (#334155)
- 文字色：slate-900 (主要)、slate-600 (次要)
- 边框色：slate-200
- 响应式滚动条样式
- 表格样式优化

## 使用方法

### 1. 在列表页添加跳转
```javascript
import { useNavigate } from 'react-router-dom'

const navigate = useNavigate()

// 点击跳转
<button onClick={() => navigate(`/test-cases/${id}`)}>
  查看详情
</button>
```

### 2. 使用PageHeader组件
```javascript
import PageHeader from '../components/PageHeader'

<PageHeader
  breadcrumbs={[
    { label: '首页', href: '/' },
    { label: '当前页' }
  ]}
  title="页面标题"
  description="页面描述"
  meta={<StatusBadge status="成功" type="success" />}
  actions={[
    {
      label: '主要操作',
      icon: <Icon />,
      variant: 'primary',
      onClick: handleAction
    }
  ]}
/>
```

### 3. 使用DetailCard组件
```javascript
import DetailCard from '../components/DetailCard'

<DetailCard title="卡片标题" extra={<button>操作</button>}>
  <p>卡片内容</p>
</DetailCard>
```

### 4. 使用StatusBadge组件
```javascript
import StatusBadge from '../components/StatusBadge'

<StatusBadge 
  status="通过" 
  type="success"  // success/warning/error/info/default
  size="md"       // sm/md/lg
/>
```

### 5. 使用MetaInfo组件
```javascript
import MetaInfo from '../components/MetaInfo'

<MetaInfo
  items={[
    { label: '创建人', value: '张三' },
    { label: '创建时间', value: '2024-05-20' }
  ]}
/>
```

### 6. 使用EmptyState组件
```javascript
import EmptyState from '../components/EmptyState'
import { FileQuestion } from 'lucide-react'

<EmptyState
  icon={FileQuestion}
  title="暂无数据"
  description="还没有添加任何内容"
  action={<button>添加</button>}
/>
```

## 设计规范

### 布局结构
1. 顶部：PageHeader（面包屑 + 标题 + 操作）
2. 基本信息：MetaInfo卡片（8个字段）
3. 统计概览：4个统计卡片（可选）
4. 内容区：Tab标签页分类展示
5. 最大宽度：1400px居中

### 颜色规范
- 主色：slate-700 (#334155)
- 成功：green-600
- 警告：yellow-600
- 错误：red-600
- 信息：blue-600

### 间距规范
- 卡片间距：24px (gap-6)
- 内容内边距：24px (p-6)
- 小间距：12px (gap-3)

### 圆角规范
- 统一：6px (rounded-md)
- 小圆角：4px (rounded-sm)
- 圆形：9999px (rounded-full)

## 响应式设计
- 最大宽度：1400px
- 移动端：自动适配100%宽度
- 表格：横向滚动
- 网格：自动调整列数

## 加载状态
所有详情页都包含：
- Loading状态：居中显示加载动画
- 空状态：使用EmptyState组件
- 错误状态：红色提示框

## 交互规范
- 主要操作：平铺显示
- 危险操作：收入"更多"下拉菜单
- 按钮禁用：disabled状态+opacity-50
- 悬停效果：hover:bg-slate-50

## 下一步
可以继续添加更多详情页：
- API详情页
- 测试执行详情页
- 数据集详情页
- 用户详情页
