# SVN 集成方案

**目标**: 让 AI 测试平台能够直接从 SVN 读取需求文档

---

## 🎯 功能需求

### 用户场景
1. 用户输入 SVN 地址（如：`svn://server/project/docs/requirement.docx`）
2. 系统自动从 SVN 下载文档
3. 解析文档内容
4. 生成测试用例

### 支持的文档类型
- `.docx` - Word 文档
- `.txt` - 文本文件
- `.md` - Markdown 文件
- `.pdf` - PDF 文档（需要额外库）

---

## 🔧 技术实现

### 方案 1: 使用 pysvn 库（推荐）

**安装**:
```bash
pip install pysvn
```

**代码示例**:
```python
import pysvn
import tempfile
from pathlib import Path

def download_from_svn(svn_url: str, username: str = None, password: str = None):
    """从 SVN 下载文件"""
    client = pysvn.Client()
    
    # 设置认证
    if username and password:
        client.set_default_username(username)
        client.set_default_password(password)
    
    # 创建临时文件
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=Path(svn_url).suffix)
    
    try:
        # 从 SVN 导出文件
        client.export(svn_url, temp_file.name)
        return temp_file.name
    except Exception as e:
        print(f"SVN 下载失败: {e}")
        return None
```

### 方案 2: 使用 svn 命令行（简单）

**前提**: 系统已安装 SVN 客户端

**代码示例**:
```python
import subprocess
import tempfile
from pathlib import Path

def download_from_svn_cli(svn_url: str, username: str = None, password: str = None):
    """使用 SVN 命令行下载文件"""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=Path(svn_url).suffix)
    
    # 构建 SVN 命令
    cmd = ['svn', 'export', svn_url, temp_file.name, '--force']
    
    if username and password:
        cmd.extend(['--username', username, '--password', password])
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            return temp_file.name
        else:
            print(f"SVN 错误: {result.stderr}")
            return None
    except Exception as e:
        print(f"SVN 下载失败: {e}")
        return None
```

### 方案 3: 使用 HTTP/HTTPS（如果 SVN 支持 WebDAV）

**代码示例**:
```python
import requests
import tempfile
from pathlib import Path

def download_from_svn_http(svn_url: str, username: str = None, password: str = None):
    """通过 HTTP 从 SVN 下载文件"""
    # 将 svn:// 转换为 http://
    http_url = svn_url.replace('svn://', 'http://')
    
    auth = (username, password) if username and password else None
    
    try:
        response = requests.get(http_url, auth=auth, stream=True)
        response.raise_for_status()
        
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=Path(svn_url).suffix)
        
        with open(temp_file.name, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        return temp_file.name
    except Exception as e:
        print(f"HTTP 下载失败: {e}")
        return None
```

---

## 📝 后端 API 实现

### 新增 API 端点

**文件**: `ai-test-platform/backend_api_server.py`

```python
from pydantic import BaseModel
from typing import Optional

class SVNRequest(BaseModel):
    """SVN 请求"""
    svn_url: str
    username: Optional[str] = None
    password: Optional[str] = None

@app.post("/api/testcases/generate-from-svn")
async def generate_testcases_from_svn(request: SVNRequest):
    """从 SVN 生成测试用例"""
    try:
        print(f"📥 从 SVN 下载文件: {request.svn_url}")
        
        # 1. 从 SVN 下载文件
        temp_file = download_from_svn_cli(
            request.svn_url,
            request.username,
            request.password
        )
        
        if not temp_file:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "message": "从 SVN 下载文件失败"
                }
            )
        
        # 2. 读取文件内容
        file_path = Path(temp_file)
        filename = Path(request.svn_url).name
        
        with open(file_path, 'rb') as f:
            content = f.read()
        
        # 3. 解析文件内容（复用现有逻辑）
        text_content = ""
        
        if filename.endswith('.docx'):
            # Word 文档解析
            from docx import Document
            from io import BytesIO
            doc = Document(BytesIO(content))
            paragraphs = [para.text.strip() for para in doc.paragraphs if para.text.strip()]
            text_content = '\n'.join(paragraphs)
        else:
            # 文本文件
            text_content = content.decode('utf-8', errors='ignore')
        
        # 4. 生成测试用例（复用现有逻辑）
        generated_cases = await _generate_testcases_with_ai(
            text_content,
            filename,
            'deepseek'  # 或从配置读取
        )
        
        # 5. 转换并保存
        final_cases = []
        import time
        import uuid
        
        base_timestamp = int(time.time() * 1000)
        
        for idx, tc in enumerate(generated_cases):
            case_id = f"TC_{base_timestamp}_{idx}_{uuid.uuid4().hex[:6]}"
            
            final_case = {
                "id": case_id,
                "title": tc['title'],
                "module": tc['module'],
                "priority": tc['priority'].lower(),
                "status": "pending",
                "steps": tc['steps'],
                "expected": tc['expected'],
                "source": f"svn:{request.svn_url}",
                "type": tc.get('type', '功能测试')
            }
            final_cases.append(final_case)
        
        # 6. 保存到数据库
        test_cases_db.extend(final_cases)
        
        # 7. 清理临时文件
        file_path.unlink()
        
        return JSONResponse(
            content={
                "success": True,
                "count": len(final_cases),
                "testCases": final_cases,
                "message": f"从 SVN 成功生成 {len(final_cases)} 个测试用例"
            }
        )
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": f"生成失败: {str(e)}"
            }
        )
```

---

## 🎨 前端实现

### 新增 SVN 输入组件

**文件**: `ai-test-platform/frontend/src/components/SVNInput.jsx`

```jsx
import { useState } from 'react'
import { Download } from 'lucide-react'

export default function SVNInput({ onGenerate }) {
  const [svnUrl, setSvnUrl] = useState('')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    if (!svnUrl) {
      alert('请输入 SVN 地址')
      return
    }
    
    setLoading(true)
    
    try {
      const response = await fetch('http://localhost:8000/api/testcases/generate-from-svn', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          svn_url: svnUrl,
          username: username || null,
          password: password || null
        })
      })
      
      const data = await response.json()
      
      if (data.success) {
        alert(`成功生成 ${data.count} 个测试用例`)
        if (onGenerate) onGenerate(data.testCases)
      } else {
        alert(`生成失败: ${data.message}`)
      }
    } catch (error) {
      alert(`请求失败: ${error.message}`)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="bg-white rounded-lg border border-slate-200 p-6">
      <h3 className="text-lg font-semibold mb-4">从 SVN 生成测试用例</h3>
      
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-2">
            SVN 地址 *
          </label>
          <input
            type="text"
            value={svnUrl}
            onChange={(e) => setSvnUrl(e.target.value)}
            placeholder="svn://server/project/docs/requirement.docx"
            className="w-full px-3 py-2 border border-slate-300 rounded-md"
            required
          />
        </div>
        
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">
              用户名（可选）
            </label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="SVN 用户名"
              className="w-full px-3 py-2 border border-slate-300 rounded-md"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">
              密码（可选）
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="SVN 密码"
              className="w-full px-3 py-2 border border-slate-300 rounded-md"
            />
          </div>
        </div>
        
        <button
          type="submit"
          disabled={loading}
          className="w-full flex items-center justify-center px-4 py-2 bg-slate-700 text-white rounded-md hover:bg-slate-800 disabled:opacity-50"
        >
          <Download className="w-4 h-4 mr-2" />
          {loading ? '生成中...' : '从 SVN 生成测试用例'}
        </button>
      </form>
      
      <div className="mt-4 text-sm text-slate-600">
        <p>支持的文件格式:</p>
        <ul className="list-disc list-inside mt-2">
          <li>.docx - Word 文档</li>
          <li>.txt - 文本文件</li>
          <li>.md - Markdown 文件</li>
        </ul>
      </div>
    </div>
  )
}
```

### 集成到测试用例页面

**文件**: `ai-test-platform/frontend/src/pages/TestCases.jsx`

```jsx
import SVNInput from '../components/SVNInput'

// 在页面中添加 SVN 输入组件
<div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
  {/* 现有的文件上传组件 */}
  <FileUpload onGenerate={handleGenerate} />
  
  {/* 新增的 SVN 输入组件 */}
  <SVNInput onGenerate={handleGenerate} />
</div>
```

---

## 🔐 安全考虑

### 1. 密码加密
```python
# 不要在日志中打印密码
print(f"📥 从 SVN 下载文件: {request.svn_url}")  # ✅
print(f"密码: {request.password}")  # ❌ 不要这样做
```

### 2. 访问控制
```python
# 限制可访问的 SVN 服务器
ALLOWED_SVN_SERVERS = [
    'svn://internal-server',
    'https://svn.company.com'
]

def is_allowed_svn_url(url: str) -> bool:
    return any(url.startswith(server) for server in ALLOWED_SVN_SERVERS)
```

### 3. 文件大小限制
```python
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

if file_size > MAX_FILE_SIZE:
    raise Exception("文件太大，超过 10MB 限制")
```

---

## 📦 安装依赖

### 方案 1: pysvn（推荐）
```bash
# Windows
pip install pysvn

# Linux
sudo apt-get install python3-svn
pip install pysvn

# macOS
brew install subversion
pip install pysvn
```

### 方案 2: SVN 命令行
```bash
# Windows
# 下载并安装 TortoiseSVN 或 SlikSVN

# Linux
sudo apt-get install subversion

# macOS
brew install subversion
```

---

## 🧪 测试步骤

### 1. 测试 SVN 连接
```python
# test_svn_connection.py
import subprocess

def test_svn():
    result = subprocess.run(['svn', '--version'], capture_output=True, text=True)
    print(result.stdout)
    
    if result.returncode == 0:
        print("✅ SVN 已安装")
    else:
        print("❌ SVN 未安装")

test_svn()
```

### 2. 测试文件下载
```python
# test_svn_download.py
svn_url = "svn://your-server/path/to/requirement.docx"
username = "your-username"
password = "your-password"

temp_file = download_from_svn_cli(svn_url, username, password)

if temp_file:
    print(f"✅ 下载成功: {temp_file}")
else:
    print("❌ 下载失败")
```

### 3. 测试完整流程
```bash
# 启动后端
cd ai-test-platform
py backend_api_server.py

# 测试 API
curl -X POST http://localhost:8000/api/testcases/generate-from-svn \
  -H "Content-Type: application/json" \
  -d '{
    "svn_url": "svn://server/project/docs/requirement.docx",
    "username": "user",
    "password": "pass"
  }'
```

---

## 📋 配置文件

### SVN 配置

**文件**: `ai-test-platform/config/svn_config.py`

```python
class SVNConfig:
    """SVN 配置"""
    
    # 允许的 SVN 服务器
    ALLOWED_SERVERS = [
        'svn://internal-server',
        'https://svn.company.com'
    ]
    
    # 默认超时（秒）
    TIMEOUT = 30
    
    # 最大文件大小（字节）
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
    
    # 支持的文件类型
    SUPPORTED_EXTENSIONS = ['.docx', '.txt', '.md', '.pdf']
    
    # 临时文件目录
    TEMP_DIR = 'temp/svn'
```

---

## 🎯 使用示例

### 场景 1: 公司内部 SVN
```
SVN 地址: svn://svn.company.com/projects/v1.2.2/需求文档.docx
用户名: zhangsan
密码: ********
```

### 场景 2: 外部 SVN（HTTP）
```
SVN 地址: https://svn.example.com/repo/docs/requirement.txt
用户名: user
密码: ********
```

### 场景 3: 无需认证的 SVN
```
SVN 地址: svn://public-server/open-project/spec.md
用户名: (留空)
密码: (留空)
```

---

## ✅ 优势

1. **自动化** - 无需手动下载文件
2. **版本控制** - 直接从 SVN 获取最新版本
3. **集成** - 与现有测试用例生成流程无缝集成
4. **安全** - 支持认证和访问控制
5. **便捷** - 只需输入 SVN 地址即可

---

## 🚀 实施步骤

1. **安装 SVN 客户端**
   ```bash
   # 根据操作系统选择安装方式
   ```

2. **添加后端 API**
   - 复制上面的代码到 `backend_api_server.py`

3. **创建前端组件**
   - 创建 `SVNInput.jsx` 组件

4. **测试功能**
   - 测试 SVN 连接
   - 测试文件下载
   - 测试完整流程

5. **部署上线**
   - 配置允许的 SVN 服务器
   - 设置安全策略

---

**实施时间**: 预计 2-4 小时  
**难度**: 中等  
**优先级**: 高（如果需求都在 SVN 上）

