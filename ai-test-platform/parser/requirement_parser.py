#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI Test Platform - 需求解析模块

负责读取和解析各种格式的需求文档。
"""

import os
import uuid
from pathlib import Path
from typing import Optional, Dict, Any
from config.config import get_config

# 知识库（懒加载）
try:
    from knowledge.business_knowledge import BusinessKnowledge
    _biz_kb = BusinessKnowledge()
except Exception:
    _biz_kb = None

class RequirementParser:
    """需求解析器"""
    
    def __init__(self):
        self.config = get_config()
    
    def read_requirement_file(self, file_path: str = None) -> str:
        """读取需求文件"""
        if file_path is None:
            file_path = self.config.paths.data_dir / "requirement.txt"
        
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"需求文件不存在: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if not content.strip():
                raise ValueError("需求文件内容为空")
            
            return content.strip()
            
        except UnicodeDecodeError:
            # 尝试其他编码
            try:
                with open(file_path, 'r', encoding='gbk') as f:
                    content = f.read()
                return content.strip()
            except UnicodeDecodeError:
                raise ValueError(f"无法读取需求文件，编码格式不支持: {file_path}")
    
    def parse_requirement_sections(self, content: str, source_file: str = "") -> Dict[str, str]:
        """解析需求文档的各个章节，并将需求条目入库"""
        sections = {}
        current_section = "overview"
        current_content = []

        lines = content.split('\n')

        for line in lines:
            line = line.strip()

            if self._is_section_header(line):
                if current_content:
                    sections[current_section] = '\n'.join(current_content).strip()
                current_section = self._extract_section_name(line)
                current_content = []
            else:
                if line:
                    current_content.append(line)

        if current_content:
            sections[current_section] = '\n'.join(current_content).strip()

        # 将需求条目入库（第三阶段）
        if _biz_kb:
            try:
                for section_name, section_content in sections.items():
                    if section_content:
                        req_id = f"REQ-{uuid.uuid4().hex[:8].upper()}"
                        _biz_kb.save_requirement(
                            req_id=req_id,
                            content=section_content[:500],
                            module=section_name,
                            source_file=source_file
                        )
                # 提取并入库业务规则
                rules = self._extract_business_rules(content)
                for rule in rules:
                    _biz_kb.save_business_rule(
                        rule_text=rule,
                        module="业务规则",
                        source_req_id=""
                    )
                if rules:
                    print(f"✅ 需求入库完成，提取业务规则 {len(rules)} 条")
            except Exception as e:
                print(f"⚠️ 需求入库失败（静默）: {e}")

        return sections
    
    def _is_section_header(self, line: str) -> bool:
        """判断是否为章节标题"""
        # 检测各种章节标题格式
        patterns = [
            line.startswith('#'),  # Markdown格式
            line.startswith('第') and ('章' in line or '节' in line),  # 中文章节
            line.endswith('：') or line.endswith(':'),  # 冒号结尾
            (line.isupper() and len(line.split()) <= 5),  # 全大写短标题
            any(keyword in line.lower() for keyword in [
                '需求', '功能', '接口', '流程', '规则', '约束', 
                'requirement', 'function', 'api', 'process'
            ])
        ]
        
        return any(patterns)
    
    def _extract_section_name(self, line: str) -> str:
        """提取章节名称"""
        # 移除标记符号
        name = line.replace('#', '').replace('：', '').replace(':', '').strip()
        
        # 转换为标准的章节名
        name_mapping = {
            '概述': 'overview',
            '功能需求': 'functional_requirements',
            '非功能需求': 'non_functional_requirements',
            '接口需求': 'api_requirements',
            '业务流程': 'business_process',
            '数据需求': 'data_requirements',
            '约束条件': 'constraints',
            '验收标准': 'acceptance_criteria'
        }
        
        return name_mapping.get(name, name.lower().replace(' ', '_'))
    
    def extract_key_information(self, content: str) -> Dict[str, Any]:
        """提取关键信息"""
        sections = self.parse_requirement_sections(content)
        
        key_info = {
            'title': self._extract_title(content),
            'version': self._extract_version(content),
            'modules': self._extract_modules(content),
            'apis': self._extract_apis(content),
            'business_rules': self._extract_business_rules(content),
            'constraints': self._extract_constraints(content),
            'sections': sections
        }
        
        return key_info
    
    def _extract_title(self, content: str) -> str:
        """提取文档标题"""
        lines = content.split('\n')[:10]  # 只检查前10行
        
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):
                # 可能是标题
                if len(line) < 100 and ('系统' in line or '平台' in line or '需求' in line):
                    return line
        
        return "未知项目"
    
    def _extract_version(self, content: str) -> str:
        """提取版本信息"""
        import re
        
        version_patterns = [
            r'版本[：:]?\s*([v]?\d+\.\d+(?:\.\d+)?)',
            r'version[：:]?\s*([v]?\d+\.\d+(?:\.\d+)?)',
            r'v(\d+\.\d+(?:\.\d+)?)'
        ]
        
        for pattern in version_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return "1.0.0"
    
    def _extract_modules(self, content: str) -> list:
        """提取功能模块"""
        modules = []
        
        # 查找模块相关的关键词
        module_keywords = ['模块', '功能', '子系统', 'module', 'function']
        
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if any(keyword in line.lower() for keyword in module_keywords):
                # 提取可能的模块名
                if '：' in line or ':' in line:
                    parts = line.split('：' if '：' in line else ':')
                    if len(parts) > 1:
                        module_name = parts[0].strip()
                        if len(module_name) < 50:  # 合理的模块名长度
                            modules.append(module_name)
        
        return list(set(modules))  # 去重
    
    def _extract_apis(self, content: str) -> list:
        """提取API接口"""
        apis = []
        
        # 查找API相关的关键词
        api_patterns = [
            r'/api/\w+',
            r'POST|GET|PUT|DELETE\s+/\w+',
            r'接口[：:]?\s*(\w+)',
        ]
        
        import re
        for pattern in api_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            apis.extend(matches)
        
        return list(set(apis))  # 去重
    
    def _extract_business_rules(self, content: str) -> list:
        """提取业务规则"""
        rules = []
        
        # 查找规则相关的关键词
        rule_keywords = ['规则', '约束', '限制', '条件', 'rule', 'constraint']
        
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if any(keyword in line.lower() for keyword in rule_keywords):
                if len(line) > 10 and len(line) < 200:  # 合理的规则长度
                    rules.append(line)
        
        return rules
    
    def _extract_constraints(self, content: str) -> list:
        """提取约束条件"""
        constraints = []
        
        # 查找约束相关的关键词
        constraint_keywords = ['必须', '不能', '应该', '禁止', 'must', 'should', 'cannot']
        
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if any(keyword in line.lower() for keyword in constraint_keywords):
                if len(line) > 10 and len(line) < 200:  # 合理的约束长度
                    constraints.append(line)
        
        return constraints
    
    def validate_requirement(self, content: str) -> Dict[str, Any]:
        """验证需求文档的完整性"""
        validation_result = {
            'is_valid': True,
            'warnings': [],
            'errors': [],
            'suggestions': []
        }
        
        # 检查文档长度
        if len(content) < 100:
            validation_result['errors'].append("需求文档内容过短，可能不完整")
            validation_result['is_valid'] = False
        
        # 检查关键章节
        sections = self.parse_requirement_sections(content)
        required_sections = ['functional_requirements', 'api_requirements']
        
        for section in required_sections:
            if section not in sections:
                validation_result['warnings'].append(f"缺少重要章节: {section}")
        
        # 检查是否包含API信息
        apis = self._extract_apis(content)
        if not apis:
            validation_result['warnings'].append("未发现API接口信息，可能影响接口测试生成")
        
        # 检查是否包含业务规则
        rules = self._extract_business_rules(content)
        if not rules:
            validation_result['suggestions'].append("建议补充业务规则信息，有助于生成更准确的测试用例")
        
        return validation_result

def create_sample_requirement():
    """创建示例需求文档"""
    sample_content = """
# 用户管理系统需求文档

版本：v1.0.0

## 概述
用户管理系统是一个基于Web的用户信息管理平台，提供用户注册、登录、信息管理等核心功能。

## 功能需求

### 用户注册模块
- 用户可以通过邮箱或手机号注册账户
- 注册时需要验证邮箱或手机号的有效性
- 密码需要满足安全要求：至少8位，包含字母和数字

### 用户登录模块
- 支持邮箱/手机号 + 密码登录
- 支持记住登录状态
- 连续登录失败3次后锁定账户30分钟

### 用户信息管理模块
- 用户可以查看和编辑个人信息
- 支持头像上传功能
- 支持密码修改功能

## 接口需求

### 用户注册接口
- POST /api/user/register
- 参数：email, phone, password, confirm_password
- 返回：注册结果和用户ID

### 用户登录接口
- POST /api/user/login
- 参数：username, password, remember_me
- 返回：登录token和用户信息

### 获取用户信息接口
- GET /api/user/profile
- 参数：无（需要token验证）
- 返回：用户详细信息

### 更新用户信息接口
- PUT /api/user/profile
- 参数：nickname, avatar, phone等
- 返回：更新结果

## 业务规则
1. 用户名必须唯一，不能重复
2. 邮箱格式必须正确
3. 手机号必须是有效的中国大陆手机号
4. 密码不能包含用户名
5. 头像文件大小不能超过2MB

## 约束条件
- 系统必须支持并发访问
- 响应时间不能超过3秒
- 数据必须加密存储
- 必须记录用户操作日志
"""
    
    config = get_config()
    requirement_file = config.paths.data_dir / "requirement.txt"
    
    with open(requirement_file, 'w', encoding='utf-8') as f:
        f.write(sample_content)
    
    print(f"示例需求文档已创建: {requirement_file}")
    return requirement_file