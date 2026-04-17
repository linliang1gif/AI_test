# 🚀 AI测试平台 - 快速开始

## 一键启动

```bash
cd G:\AI项目\ai测试
.\restart_all.bat
```

等待10秒后自动打开浏览器访问 http://localhost:5173

## 验证功能

```bash
# 测试所有API接口
py test_all_apis.py

# 检查系统状态
py check_system_status.py
```

## 核心功能

### 1. API测试
- 执行HTTP请求（GET/POST/PUT/DELETE）
- 查看响应结果和响应时间
- 保存为测试用例

### 2. 测试用例管理
- 查看所有测试用例（40个）
- 创建新测试用例
- 批量删除测试用例

### 3. 自动化脚本
- 从测试用例生成Python脚本
- 下载脚本到本地
- 在线执行脚本
- 查看执行结果

### 4. 测试数据生成
- 智能生成测试数据
- 支持多种数据类型
- 数据集管理

## API使用示例

```javascript
import api from '@/services/api'

// 执行API测试
const result = await api.apis.execute({
  method: 'GET',
  url: 'https://api.example.com/users'
})

// 保存为测试用例
await api.apis.saveAsTestCase({
  api_info: { name: '获取用户', method: 'GET', path: '/users' },
  execution_result: result
})

// 生成脚本
const script = await api.automation.generateScript(testCaseId)

// 执行脚本
const execResult = await api.automation.executeScript(script.script_id)
```

## 服务地址

- 前端：http://localhost:5173
- 后端：http://localhost:8000
- API文档：http://localhost:8000/docs

## 数据文件

所有数据保存在：`ai-test-platform/data/platform_data.json`

## 常见问题

### Q: 前端显示"Failed to fetch"
A: 检查后端服务是否运行，重启服务：`.\restart_all.bat`

### Q: 脚本执行失败
A: 检查Python环境，确保安装了requests库：`pip install requests`

### Q: 数据丢失
A: 数据保存在JSON文件中，检查文件是否存在

## 技术栈

- 后端：FastAPI + Python 3.x
- 前端：React + Vite
- 数据：JSON文件持久化

## 文档

- `API_EXAMPLES.md` - API接口示例
- `COMPLETE_FIX_SUMMARY.md` - 完整修复总结
- `FINAL_COMPLETION_REPORT.md` - 最终完成报告

---

**版本：** v1.2.0  
**状态：** ✅ 所有功能正常运行  
**测试通过率：** 100%
