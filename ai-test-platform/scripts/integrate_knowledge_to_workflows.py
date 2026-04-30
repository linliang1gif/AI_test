#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
将知识库集成到所有AI测试流程中
让所有流程都能调用Swagger API、前端代码、后端代码知识
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from knowledge.knowledge_manager import KnowledgeManager


def create_knowledge_enhanced_prompt_helper():
    """创建知识增强的Prompt助手"""
    
    helper_code = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Knowledge Enhanced Prompt Helper
为AI Prompt添加知识库上下文
"""

from typing import List, Dict, Any, Optional
from knowledge.knowledge_manager import KnowledgeManager


class KnowledgeEnhancedPromptHelper:
    """知识增强的Prompt助手"""
    
    def __init__(self):
        self.km = KnowledgeManager()
    
    def enhance_prompt_with_api_knowledge(self, prompt: str, query: str, 
                                         top_k: int = 5) -> str:
        """
        使用API知识增强Prompt
        
        Args:
            prompt: 原始prompt
            query: 查询关键词
            top_k: 返回前K个结果
            
        Returns:
            增强后的prompt
        """
        if not self.km.kb or not self.km.kb.available:
            return prompt
        
        try:
            collection = self.km.kb.get_collection("apis")
            if not collection:
                return prompt
            
            results = collection.query(
                query_texts=[query],
                n_results=top_k
            )
            
            if not results or not results['ids']:
                return prompt
            
            # 构建API上下文
            api_context = "\\n\\n【相关API信息】\\n"
            for i, metadata in enumerate(results['metadatas'][0], 1):
                api_context += f"{i}. {metadata['method']} {metadata['path']}\\n"
                api_context += f"   摘要: {metadata['summary']}\\n"
                if 'tags' in metadata:
                    api_context += f"   标签: {metadata['tags']}\\n"
            
            # 将API上下文添加到prompt
            enhanced_prompt = f"{prompt}\\n{api_context}"
            
            return enhanced_prompt
            
        except Exception as e:
            print(f"⚠️ API知识增强失败: {e}")
            return prompt
    
    def enhance_prompt_with_code_knowledge(self, prompt: str, query: str,
                                          code_type: str = "backend",
                                          top_k: int = 3) -> str:
        """
        使用代码知识增强Prompt
        
        Args:
            prompt: 原始prompt
            query: 查询关键词
            code_type: 代码类型 (frontend/backend)
            top_k: 返回前K个结果
            
        Returns:
            增强后的prompt
        """
        if not self.km.kb or not self.km.kb.available:
            return prompt
        
        try:
            collection_name = f"{code_type}_code"
            collection = self.km.kb.get_collection(collection_name)
            if not collection:
                return prompt
            
            results = collection.query(
                query_texts=[query],
                n_results=top_k
            )
            
            if not results or not results['ids']:
                return prompt
            
            # 构建代码上下文
            code_context = f"\\n\\n【相关{code_type}代码】\\n"
            for i, metadata in enumerate(results['metadatas'][0], 1):
                code_context += f"{i}. {metadata['filename']}\\n"
                code_context += f"   路径: {metadata['path']}\\n"
                code_context += f"   语言: {metadata['language']}\\n"
                if 'classes' in metadata:
                    code_context += f"   类: {metadata['classes']}\\n"
                if 'functions' in metadata:
                    funcs = metadata['functions'][:100]  # 限制长度
                    code_context += f"   函数: {funcs}\\n"
            
            # 将代码上下文添加到prompt
            enhanced_prompt = f"{prompt}\\n{code_context}"
            
            return enhanced_prompt
            
        except Exception as e:
            print(f"⚠️ 代码知识增强失败: {e}")
            return prompt
    
    def enhance_prompt_with_full_knowledge(self, prompt: str, query: str) -> str:
        """
        使用完整知识增强Prompt (API + 前端 + 后端)
        
        Args:
            prompt: 原始prompt
            query: 查询关键词
            
        Returns:
            增强后的prompt
        """
        # 1. 添加API知识
        enhanced = self.enhance_prompt_with_api_knowledge(prompt, query, top_k=3)
        
        # 2. 添加后端代码知识
        enhanced = self.enhance_prompt_with_code_knowledge(enhanced, query, "backend", top_k=2)
        
        # 3. 添加前端代码知识
        enhanced = self.enhance_prompt_with_code_knowledge(enhanced, query, "frontend", top_k=2)
        
        return enhanced
    
    def search_related_apis(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        搜索相关API
        
        Args:
            query: 查询关键词
            top_k: 返回前K个结果
            
        Returns:
            API列表
        """
        if not self.km.kb or not self.km.kb.available:
            return []
        
        try:
            collection = self.km.kb.get_collection("apis")
            if not collection:
                return []
            
            results = collection.query(
                query_texts=[query],
                n_results=top_k
            )
            
            if not results or not results['ids']:
                return []
            
            apis = []
            for metadata in results['metadatas'][0]:
                apis.append({
                    'method': metadata['method'],
                    'path': metadata['path'],
                    'summary': metadata['summary'],
                    'tags': metadata.get('tags', '')
                })
            
            return apis
            
        except Exception as e:
            print(f"⚠️ API搜索失败: {e}")
            return []
    
    def search_related_code(self, query: str, code_type: str = "backend",
                           top_k: int = 3) -> List[Dict[str, Any]]:
        """
        搜索相关代码
        
        Args:
            query: 查询关键词
            code_type: 代码类型 (frontend/backend)
            top_k: 返回前K个结果
            
        Returns:
            代码文件列表
        """
        if not self.km.kb or not self.km.kb.available:
            return []
        
        try:
            collection_name = f"{code_type}_code"
            collection = self.km.kb.get_collection(collection_name)
            if not collection:
                return []
            
            results = collection.query(
                query_texts=[query],
                n_results=top_k
            )
            
            if not results or not results['ids']:
                return []
            
            files = []
            for metadata in results['metadatas'][0]:
                files.append({
                    'filename': metadata['filename'],
                    'path': metadata['path'],
                    'language': metadata['language'],
                    'classes': metadata.get('classes', ''),
                    'functions': metadata.get('functions', '')[:100]
                })
            
            return files
            
        except Exception as e:
            print(f"⚠️ 代码搜索失败: {e}")
            return []


# 全局实例
_helper = None

def get_knowledge_helper() -> KnowledgeEnhancedPromptHelper:
    """获取知识助手实例"""
    global _helper
    if _helper is None:
        _helper = KnowledgeEnhancedPromptHelper()
    return _helper
'''
    
    # 写入文件
    helper_file = Path("ai测试/ai-test-platform/utils/knowledge_prompt_helper.py")
    helper_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(helper_file, 'w', encoding='utf-8') as f:
        f.write(helper_code)
    
    print(f"✅ 创建知识增强Prompt助手: {helper_file}")
    
    return helper_file


def create_integration_guide():
    """创建集成指南"""
    
    guide = '''# 知识库集成到AI流程指南

## 📚 概述

知识库已经准备就绪,包含:
- ✅ 814个API接口
- ✅ 500个前端文件
- ✅ 500个后端文件

现在需要将这些知识集成到AI测试流程中。

---

## 🔧 集成方式

### 方式1: 使用KnowledgeEnhancedPromptHelper

```python
from utils.knowledge_prompt_helper import get_knowledge_helper

# 获取助手
helper = get_knowledge_helper()

# 增强Prompt
original_prompt = "生成采购订单的测试用例"
enhanced_prompt = helper.enhance_prompt_with_full_knowledge(
    prompt=original_prompt,
    query="采购订单"
)

# 使用增强后的prompt调用LLM
response = llm_client.generate(enhanced_prompt)
```

### 方式2: 直接搜索知识

```python
from utils.knowledge_prompt_helper import get_knowledge_helper

helper = get_knowledge_helper()

# 搜索相关API
apis = helper.search_related_apis("采购订单", top_k=5)
for api in apis:
    print(f"{api['method']} {api['path']}")

# 搜索相关代码
backend_files = helper.search_related_code("PurchaseOrderService", "backend", top_k=3)
for file in backend_files:
    print(f"{file['filename']}: {file['classes']}")
```

---

## 🎯 需要集成的模块

### 1. Agent Service (agent/agent_service.py)

在生成决策时,增强prompt:

```python
# 原代码
prompt = f"分析这个需求是否需要测试: {requirement}"

# 增强后
from utils.knowledge_prompt_helper import get_knowledge_helper
helper = get_knowledge_helper()

prompt = f"分析这个需求是否需要测试: {requirement}"
enhanced_prompt = helper.enhance_prompt_with_api_knowledge(
    prompt=prompt,
    query=requirement
)
```

### 2. Case Generator (case_generator/case_builder.py)

在生成测试用例时,添加API和代码上下文:

```python
# 在 build_cases 方法中
module_name = module_info['name']

# 搜索相关知识
helper = get_knowledge_helper()
apis = helper.search_related_apis(module_name, top_k=5)
backend_code = helper.search_related_code(module_name, "backend", top_k=3)

# 将知识添加到prompt
context = f"相关API: {apis}\\n相关代码: {backend_code}"
```

### 3. Strategy Service (strategy/strategy_service.py)

在生成策略时,参考API和代码复杂度:

```python
# 在 _generate_module_strategy 方法中
helper = get_knowledge_helper()
apis = helper.search_related_apis(module, top_k=3)

# 根据API数量调整用例数
if len(apis) > 5:
    case_count = case_count * 1.5  # API多,增加用例
```

---

## 📝 集成示例

### 示例1: Agent决策增强

```python
# agent/agent_service.py

def analyze(self, requirement: str) -> dict:
    # 1. 搜索相关知识
    helper = get_knowledge_helper()
    apis = helper.search_related_apis(requirement, top_k=5)
    
    # 2. 构建增强prompt
    api_context = "\\n".join([f"{api['method']} {api['path']}" for api in apis])
    
    prompt = f\"\"\"
分析需求: {requirement}

相关API:
{api_context}

请判断是否需要测试,并给出理由。
\"\"\"
    
    # 3. 调用LLM
    response = self.llm_client.generate(prompt)
    return response
```

### 示例2: 用例生成增强

```python
# case_generator/case_builder.py

def build_cases(self, module_info, scenarios, target_count, priority):
    # 1. 搜索相关知识
    helper = get_knowledge_helper()
    module_name = module_info['name']
    
    apis = helper.search_related_apis(module_name, top_k=5)
    backend_code = helper.search_related_code(module_name, "backend", top_k=3)
    
    # 2. 构建知识上下文
    knowledge_context = f\"\"\"
相关API ({len(apis)}个):
{self._format_apis(apis)}

相关后端代码 ({len(backend_code)}个):
{self._format_code(backend_code)}
\"\"\"
    
    # 3. 生成用例时使用知识
    prompt = f\"\"\"
为模块 {module_name} 生成测试用例

{knowledge_context}

场景: {scenarios}
目标数量: {target_count}
优先级: {priority}

请生成详细的测试用例。
\"\"\"
    
    # 4. 调用LLM
    cases = self.llm_client.generate(prompt)
    return cases
```

---

## ✅ 集成检查清单

- [ ] Agent Service - 决策时使用API知识
- [ ] Strategy Service - 策略时参考代码复杂度
- [ ] Case Generator - 用例生成时使用完整知识
- [ ] Orchestrator - 执行时参考API定义
- [ ] Self Healing - 修复时参考代码实现

---

## 🚀 快速开始

1. 运行集成脚本:
```bash
cd ai测试/ai-test-platform
py integrate_knowledge_to_workflows.py
```

2. 测试知识增强:
```bash
py test_knowledge_integration.py
```

3. 在AI测试控制台中使用:
```bash
py start_platform.py
# 访问 http://localhost:5174/ai-console
# 输入测试需求,AI会自动使用知识库
```

---

**状态**: ⏳ 待集成  
**优先级**: 高  
**预计时间**: 1-2小时
'''
    
    guide_file = Path("ai测试/ai-test-platform/知识库集成指南.md")
    with open(guide_file, 'w', encoding='utf-8') as f:
        f.write(guide)
    
    print(f"✅ 创建集成指南: {guide_file}")
    
    return guide_file


if __name__ == "__main__":
    print("=" * 60)
    print("🔧 知识库集成到AI流程")
    print("=" * 60)
    
    # 1. 创建知识增强助手
    helper_file = create_knowledge_enhanced_prompt_helper()
    
    # 2. 创建集成指南
    guide_file = create_integration_guide()
    
    print("\n" + "=" * 60)
    print("✅ 集成准备完成!")
    print("=" * 60)
    print(f"\n📁 创建的文件:")
    print(f"   1. {helper_file}")
    print(f"   2. {guide_file}")
    
    print(f"\n💡 下一步:")
    print(f"   1. 阅读集成指南: {guide_file}")
    print(f"   2. 在各个模块中使用 KnowledgeEnhancedPromptHelper")
    print(f"   3. 测试知识增强效果")
    
    print("\n🎯 使用示例:")
    print("""
from utils.knowledge_prompt_helper import get_knowledge_helper

helper = get_knowledge_helper()

# 增强Prompt
enhanced_prompt = helper.enhance_prompt_with_full_knowledge(
    prompt="生成采购订单测试用例",
    query="采购订单"
)

# 搜索API
apis = helper.search_related_apis("采购订单", top_k=5)
    """)
    
    print("=" * 60)
