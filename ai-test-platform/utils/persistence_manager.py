#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
数据持久化管理器
统一管理所有数据的持久化存储
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime


class PersistenceManager:
    """数据持久化管理器"""
    
    def __init__(self, storage_dir: str = "storage"):
        """初始化持久化管理器"""
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # 数据文件路径
        self.test_cases_file = self.storage_dir / "test_cases.json"
        self.apis_file = self.storage_dir / "apis.json"
        self.projects_file = self.storage_dir / "projects.json"
        self.test_runs_file = self.storage_dir / "test_runs.json"
        
        # 初始化数据
        self._init_data()
    
    def _init_data(self):
        """初始化数据文件"""
        if not self.test_cases_file.exists():
            self._save_json(self.test_cases_file, [])
        
        if not self.apis_file.exists():
            self._save_json(self.apis_file, [])
        
        if not self.projects_file.exists():
            self._save_json(self.projects_file, [])
        
        if not self.test_runs_file.exists():
            self._save_json(self.test_runs_file, [])
    
    def _load_json(self, file_path: Path) -> Any:
        """加载JSON文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载文件失败 {file_path}: {e}")
            return []
    
    def _save_json(self, file_path: Path, data: Any):
        """保存JSON文件"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存文件失败 {file_path}: {e}")
    
    # ==================== 测试用例管理 ====================
    
    def get_test_cases(self) -> List[Dict[str, Any]]:
        """获取所有测试用例"""
        return self._load_json(self.test_cases_file)
    
    def save_test_case(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """保存测试用例"""
        test_cases = self.get_test_cases()
        
        # 生成ID
        if 'id' not in test_case:
            test_case['id'] = len(test_cases) + 1
        
        # 添加时间戳
        test_case['created_at'] = datetime.now().isoformat()
        test_case['updated_at'] = datetime.now().isoformat()
        
        test_cases.append(test_case)
        self._save_json(self.test_cases_file, test_cases)
        
        return test_case
    
    def update_test_case(self, test_case_id: int, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """更新测试用例"""
        test_cases = self.get_test_cases()
        
        for i, tc in enumerate(test_cases):
            if tc.get('id') == test_case_id:
                test_cases[i].update(updates)
                test_cases[i]['updated_at'] = datetime.now().isoformat()
                self._save_json(self.test_cases_file, test_cases)
                return test_cases[i]
        
        return None
    
    def delete_test_case(self, test_case_id: int) -> bool:
        """删除测试用例"""
        test_cases = self.get_test_cases()
        
        for i, tc in enumerate(test_cases):
            if tc.get('id') == test_case_id:
                test_cases.pop(i)
                self._save_json(self.test_cases_file, test_cases)
                return True
        
        return False
    
    # ==================== API管理 ====================
    
    def get_apis(self) -> List[Dict[str, Any]]:
        """获取所有API"""
        return self._load_json(self.apis_file)
    
    def save_api(self, api: Dict[str, Any]) -> Dict[str, Any]:
        """保存API"""
        apis = self.get_apis()
        
        if 'id' not in api:
            api['id'] = len(apis) + 1
        
        api['created_at'] = datetime.now().isoformat()
        
        apis.append(api)
        self._save_json(self.apis_file, apis)
        
        return api
    
    def save_apis_batch(self, apis: List[Dict[str, Any]]):
        """批量保存API"""
        existing_apis = self.get_apis()
        
        for api in apis:
            if 'id' not in api:
                api['id'] = len(existing_apis) + 1
            api['created_at'] = datetime.now().isoformat()
            existing_apis.append(api)
        
        self._save_json(self.apis_file, existing_apis)
    
    def clear_apis(self):
        """清空所有API"""
        self._save_json(self.apis_file, [])
    
    # ==================== 项目管理 ====================
    
    def get_projects(self) -> List[Dict[str, Any]]:
        """获取所有项目"""
        return self._load_json(self.projects_file)
    
    def save_project(self, project: Dict[str, Any]) -> Dict[str, Any]:
        """保存项目"""
        projects = self.get_projects()
        
        if 'id' not in project:
            project['id'] = len(projects) + 1
        
        project['created_at'] = datetime.now().isoformat()
        project['updated_at'] = datetime.now().isoformat()
        
        projects.append(project)
        self._save_json(self.projects_file, projects)
        
        return project
    
    # ==================== 测试运行管理 ====================
    
    def get_test_runs(self) -> List[Dict[str, Any]]:
        """获取所有测试运行"""
        return self._load_json(self.test_runs_file)
    
    def save_test_run(self, test_run: Dict[str, Any]) -> Dict[str, Any]:
        """保存测试运行"""
        test_runs = self.get_test_runs()
        
        if 'id' not in test_run:
            test_run['id'] = len(test_runs) + 1
        
        test_run['created_at'] = datetime.now().isoformat()
        
        test_runs.append(test_run)
        self._save_json(self.test_runs_file, test_runs)
        
        return test_run
    
    def update_test_run(self, test_run_id: int, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """更新测试运行"""
        test_runs = self.get_test_runs()
        
        for i, tr in enumerate(test_runs):
            if tr.get('id') == test_run_id:
                test_runs[i].update(updates)
                test_runs[i]['updated_at'] = datetime.now().isoformat()
                self._save_json(self.test_runs_file, test_runs)
                return test_runs[i]
        
        return None
    
    # ==================== 统计信息 ====================
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "test_cases_count": len(self.get_test_cases()),
            "apis_count": len(self.get_apis()),
            "projects_count": len(self.get_projects()),
            "test_runs_count": len(self.get_test_runs())
        }


# 全局实例
persistence_manager = PersistenceManager()
