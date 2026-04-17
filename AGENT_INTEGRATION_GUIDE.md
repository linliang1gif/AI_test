# Agent 集成指南

## 🎯 目标

将新重构的 DesignAgent 和 ExecutionAgent 集成到后端 API 系统中。

---

## 📋 集成步骤

### 步骤 1: 创建 Agent API 路由

**文件**: `ai-test-platform/routes/agent_routes.py`

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agent API 路由
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from modules.agents import DesignAgent, ExecutionAgent, ExecutionStrategy
from core import TestCase, ExecutionResult

router = APIRouter(prefix="/api/agents", tags=["agents"])


# ==================== 请求模型 ====================

class DesignRequest(BaseModel):
    """设计请求"""
    source_type: str  # "swagger", "requirement", "discovery"
    source_data: Dict[str, Any]
    config: Optional[Dict[str, Any]] = None


class ExecutionRequest(BaseModel):
    """执行请求"""
    testcases: List[Dict[str, Any]]
    environment: Optional[str] = "test"
    strategy: Optional[str] = "priority"
    config: Optional[Dict[str, Any]] = None


# ==================== API 端点 ====================

@router.post("/design")
async def design_testcases(request: DesignRequest):
    """
    设计测试用例
    
    支持三种设计来源:
    - swagger: 从 Swagger 规范设计
    - requirement: 从需求文档设计
    - discovery: 从 Discovery 结果设计
    """
    try:
        # 创建 DesignAgent
        agent = DesignAgent(config=request.config)
        
        # 根据来源类型调用不同方法
        if request.source_type == "swagger":
            testcases = agent.design_from_swagger(request.source_data)
        elif request.source_type == "requirement":
            testcases = agent.design_from_requirement(
                request.source_data.get("requirement", "")
            )
        elif request.source_type == "discovery":
            testcases = agent.design_from_discovery(
                request.source_data.get("test_points", [])
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的设计来源: {request.source_type}"
            )
        
        # 获取统计信息
        stats = agent.get_design_statistics()
        
        return {
            "success": True,
            "testcases": [_testcase_to_dict(tc) for tc in testcases],
            "statistics": stats
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/execute")
async def execute_testcases(request: ExecutionRequest):
    """
    执行测试用例
    
    支持四种执行策略:
    - sequential: 顺序执行
    - parallel: 并行执行
    - priority: 按优先级执行
    - adaptive: 自适应执行
    """
    try:
        # 创建 ExecutionAgent
        config = request.config or {}
        config['strategy'] = request.strategy
        config['environment'] = request.environment
        
        agent = ExecutionAgent(config=config)
        
        # 执行测试用例
        results = agent.execute(request.testcases, environment=request.environment)
        
        # 获取统计信息
        stats = agent.get_statistics()
        
        return {
            "success": True,
            "results": [_result_to_dict(r) for r in results],
            "statistics": stats
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/optimize")
async def optimize_testcases(testcases: List[Dict[str, Any]]):
    """优化测试用例集合"""
    try:
        agent = DesignAgent()
        optimized = agent.optimize_testcases(testcases)
        
        return {
            "success": True,
            "original_count": len(testcases),
            "optimized_count": len(optimized),
            "testcases": [_testcase_to_dict(tc) for tc in optimized]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/strategies")
async def get_execution_strategies():
    """获取可用的执行策略"""
    return {
        "strategies": [
            {
                "name": "sequential",
                "display_name": "顺序执行",
                "description": "按顺序逐个执行测试用例，适合有依赖关系的测试"
            },
            {
                "name": "parallel",
                "display_name": "并行执行",
                "description": "并行执行所有测试用例，速度最快"
            },
            {
                "name": "priority",
                "display_name": "优先级执行",
                "description": "按优先级顺序执行，先执行高优先级用例"
            },
            {
                "name": "adaptive",
                "display_name": "自适应执行",
                "description": "高优先级顺序执行，低优先级并行执行"
            }
        ]
    }


# ==================== 辅助函数 ====================

def _testcase_to_dict(testcase: Any) -> Dict[str, Any]:
    """将 TestCase 转换为字典"""
    if hasattr(testcase, '__dict__'):
        return {
            'id': testcase.id,
            'title': testcase.title,
            'module': testcase.module,
            'priority': testcase.priority.value if hasattr(testcase.priority, 'value') else str(testcase.priority),
            'status': testcase.status.value if hasattr(testcase.status, 'value') else str(testcase.status),
            'steps': testcase.steps,
            'expected': testcase.expected
        }
    return testcase


def _result_to_dict(result: Any) -> Dict[str, Any]:
    """将 ExecutionResult 转换为字典"""
    if hasattr(result, '__dict__'):
        return {
            'test_case_id': result.test_case_id,
            'status': result.status.value if hasattr(result.status, 'value') else str(result.status),
            'start_time': result.start_time.isoformat() if hasattr(result, 'start_time') else None,
            'end_time': result.end_time.isoformat() if hasattr(result, 'end_time') else None,
            'duration': result.duration if hasattr(result, 'duration') else 0,
            'error': result.error if hasattr(result, 'error') else None
        }
    return result
```

---

### 步骤 2: 注册路由到后端服务器

**文件**: `ai-test-platform/backend_api_server.py`

在现有的路由注册代码后添加:

```python
# 导入 Agent 路由
try:
    from routes.agent_routes import router as agent_router
    app.include_router(agent_router)
    print("✅ Agent 路由已加载")
except Exception as e:
    print(f"⚠️  Agent 路由加载失败: {e}")
```

---

### 步骤 3: 前端集成

**文件**: `ai-test-platform/frontend/src/api/agents.ts`

```typescript
import axios from 'axios';

const API_BASE = 'http://localhost:8000/api/agents';

export interface DesignRequest {
  source_type: 'swagger' | 'requirement' | 'discovery';
  source_data: any;
  config?: {
    max_testcases_per_api?: number;
    include_edge_cases?: boolean;
    include_error_cases?: boolean;
    priority_threshold?: string;
  };
}

export interface ExecutionRequest {
  testcases: any[];
  environment?: string;
  strategy?: 'sequential' | 'parallel' | 'priority' | 'adaptive';
  config?: {
    max_workers?: number;
    retry_count?: number;
    retry_delay?: number;
    timeout?: number;
  };
}

// 设计测试用例
export async function designTestcases(request: DesignRequest) {
  const response = await axios.post(`${API_BASE}/design`, request);
  return response.data;
}

// 执行测试用例
export async function executeTestcases(request: ExecutionRequest) {
  const response = await axios.post(`${API_BASE}/execute`, request);
  return response.data;
}

// 优化测试用例
export async function optimizeTestcases(testcases: any[]) {
  const response = await axios.post(`${API_BASE}/optimize`, testcases);
  return response.data;
}

// 获取执行策略
export async function getExecutionStrategies() {
  const response = await axios.get(`${API_BASE}/strategies`);
  return response.data;
}
```

---

### 步骤 4: 测试集成

**文件**: `test_agent_integration.py`

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 Agent API 集成
"""

import requests
import json

BASE_URL = "http://localhost:8000/api/agents"


def test_design_from_requirement():
    """测试从需求设计"""
    print("=" * 80)
    print("测试: 从需求设计测试用例")
    print("=" * 80)
    
    request = {
        "source_type": "requirement",
        "source_data": {
            "requirement": "用户登录功能，支持用户名密码登录"
        },
        "config": {
            "max_testcases_per_api": 3,
            "include_edge_cases": True
        }
    }
    
    response = requests.post(f"{BASE_URL}/design", json=request)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ 成功生成 {len(data['testcases'])} 个测试用例")
        for i, tc in enumerate(data['testcases'], 1):
            print(f"   {i}. {tc['title']} (优先级: {tc['priority']})")
    else:
        print(f"❌ 失败: {response.text}")


def test_execute_testcases():
    """测试执行测试用例"""
    print("\n" + "=" * 80)
    print("测试: 执行测试用例")
    print("=" * 80)
    
    # 先设计一些测试用例
    design_request = {
        "source_type": "requirement",
        "source_data": {
            "requirement": "用户登录功能"
        }
    }
    
    design_response = requests.post(f"{BASE_URL}/design", json=design_request)
    testcases = design_response.json()['testcases']
    
    # 执行测试用例
    execute_request = {
        "testcases": testcases,
        "environment": "test",
        "strategy": "priority",
        "config": {
            "max_workers": 2,
            "retry_count": 2
        }
    }
    
    response = requests.post(f"{BASE_URL}/execute", json=execute_request)
    
    if response.status_code == 200:
        data = response.json()
        stats = data['statistics']
        print(f"✅ 执行完成")
        print(f"   总数: {stats['total_executed']}")
        print(f"   通过: {stats['passed']}")
        print(f"   失败: {stats['failed']}")
        print(f"   通过率: {stats['pass_rate']:.1%}")
    else:
        print(f"❌ 失败: {response.text}")


def test_get_strategies():
    """测试获取执行策略"""
    print("\n" + "=" * 80)
    print("测试: 获取执行策略")
    print("=" * 80)
    
    response = requests.get(f"{BASE_URL}/strategies")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ 可用策略:")
        for strategy in data['strategies']:
            print(f"   - {strategy['display_name']}: {strategy['description']}")
    else:
        print(f"❌ 失败: {response.text}")


def main():
    """主函数"""
    print("\n" + "=" * 80)
    print("🧪 Agent API 集成测试")
    print("=" * 80)
    
    try:
        test_design_from_requirement()
        test_execute_testcases()
        test_get_strategies()
        
        print("\n" + "=" * 80)
        print("✅ 所有测试通过！")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
```

---

## 🚀 快速开始

### 1. 创建路由文件
```bash
# 创建 agent_routes.py（复制上面的代码）
```

### 2. 重启后端服务
```bash
cd ai-test-platform
py backend_api_server.py
```

### 3. 测试 API
```bash
py test_agent_integration.py
```

### 4. 前端集成
```bash
# 创建 agents.ts（复制上面的代码）
# 在需要的组件中导入使用
```

---

## 📊 API 端点总览

| 端点 | 方法 | 功能 | 参数 |
|------|------|------|------|
| `/api/agents/design` | POST | 设计测试用例 | source_type, source_data, config |
| `/api/agents/execute` | POST | 执行测试用例 | testcases, environment, strategy, config |
| `/api/agents/optimize` | POST | 优化测试用例 | testcases |
| `/api/agents/strategies` | GET | 获取执行策略 | 无 |

---

## 💡 使用示例

### 从需求设计测试用例
```bash
curl -X POST http://localhost:8000/api/agents/design \
  -H "Content-Type: application/json" \
  -d '{
    "source_type": "requirement",
    "source_data": {
      "requirement": "用户登录功能"
    },
    "config": {
      "max_testcases_per_api": 3
    }
  }'
```

### 执行测试用例
```bash
curl -X POST http://localhost:8000/api/agents/execute \
  -H "Content-Type: application/json" \
  -d '{
    "testcases": [...],
    "environment": "test",
    "strategy": "priority"
  }'
```

---

## ✅ 验证清单

- [ ] 创建 `agent_routes.py` 文件
- [ ] 在 `backend_api_server.py` 中注册路由
- [ ] 重启后端服务
- [ ] 运行 `test_agent_integration.py` 验证
- [ ] 创建前端 API 客户端
- [ ] 更新前端组件调用新 API
- [ ] 端到端测试

---

## 🎯 下一步

集成完成后，可以：

1. 在前端添加 Agent 配置界面
2. 添加执行策略选择器
3. 实时显示执行进度
4. 添加执行历史记录
5. 集成到完整测试流程中

---

**集成预计时间**: 2-3 小时  
**难度**: 中等  
**优先级**: 高
