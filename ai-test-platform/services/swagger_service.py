#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Swagger/OpenAPI 导入服务
"""

import json
import os
import uuid
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from database.models import ApiSpec, TestCase, Project
from database.repository import ApiSpecRepository, TestCaseRepository
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from modules.swagger import SwaggerTestCaseGenerator
from core import TestCase as CoreTestCase


class SwaggerService:
    """Swagger 导入服务"""
    
    def __init__(self, db: Session):
        self.db = db
        from database.models import ApiSpec, TestCase
        self.api_spec_repo = ApiSpecRepository(ApiSpec, db)
        self.test_case_repo = TestCaseRepository(TestCase, db)
        self.upload_dir = Path(__file__).parent.parent / "uploads" / "swagger"
        self.upload_dir.mkdir(parents=True, exist_ok=True)
    
    def import_from_file(
        self,
        project_id: int,
        file_content: bytes,
        filename: str,
        generate_cases: bool = True
    ) -> Dict:
        """
        从文件导入 Swagger
        
        Args:
            project_id: 项目ID
            file_content: 文件内容
            filename: 文件名
            generate_cases: 是否自动生成测试用例
            
        Returns:
            导入结果
        """
        # 验证项目存在
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ValueError(f"项目不存在: {project_id}")
        
        # 保存文件
        file_id = str(uuid.uuid4())
        file_path = self.upload_dir / f"{file_id}_{filename}"
        file_path.write_bytes(file_content)
        
        # 解析 Swagger
        try:
            swagger_data = json.loads(file_content.decode('utf-8'))
        except Exception as e:
            raise ValueError(f"Swagger 文件解析失败: {str(e)}")
        
        # 提取基本信息
        info = swagger_data.get('info', {})
        version = info.get('version', '1.0.0')
        
        # 统计 API 数量
        paths = swagger_data.get('paths', {})
        api_count = sum(len(methods) for methods in paths.values())
        
        # 创建 ApiSpec 记录
        api_spec = ApiSpec(
            project_id=project_id,
            source_type='file',
            source_url=filename,
            version=version,
            raw_spec_path=str(file_path),
            api_count=api_count,
            imported_at=datetime.now()
        )
        
        self.db.add(api_spec)
        self.db.commit()
        self.db.refresh(api_spec)
        
        # 生成测试用例
        test_cases = []
        if generate_cases:
            test_cases = self._generate_test_cases(
                api_spec_id=api_spec.id,
                swagger_file=str(file_path),
                project_id=project_id
            )
        
        return {
            "api_spec_id": api_spec.id,
            "project_id": project_id,
            "version": version,
            "api_count": api_count,
            "test_cases_generated": len(test_cases),
            "test_case_ids": [tc.id for tc in test_cases],
            "imported_at": api_spec.imported_at.isoformat()
        }
    
    def import_from_url(
        self,
        project_id: int,
        url: str,
        generate_cases: bool = True
    ) -> Dict:
        """
        从 URL 导入 Swagger
        
        Args:
            project_id: 项目ID
            url: Swagger URL
            generate_cases: 是否自动生成测试用例
            
        Returns:
            导入结果
        """
        import requests
        
        # 验证项目存在
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ValueError(f"项目不存在: {project_id}")
        
        # 下载 Swagger
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            swagger_data = response.json()
        except Exception as e:
            raise ValueError(f"Swagger URL 访问失败: {str(e)}")
        
        # 保存文件
        file_id = str(uuid.uuid4())
        filename = f"{file_id}_swagger.json"
        file_path = self.upload_dir / filename
        file_path.write_text(json.dumps(swagger_data, indent=2, ensure_ascii=False))
        
        # 提取基本信息
        info = swagger_data.get('info', {})
        version = info.get('version', '1.0.0')
        
        # 统计 API 数量
        paths = swagger_data.get('paths', {})
        api_count = sum(len(methods) for methods in paths.values())
        
        # 创建 ApiSpec 记录
        api_spec = ApiSpec(
            project_id=project_id,
            source_type='url',
            source_url=url,
            version=version,
            raw_spec_path=str(file_path),
            api_count=api_count,
            imported_at=datetime.now()
        )
        
        self.db.add(api_spec)
        self.db.commit()
        self.db.refresh(api_spec)
        
        # 生成测试用例
        test_cases = []
        if generate_cases:
            test_cases = self._generate_test_cases(
                api_spec_id=api_spec.id,
                swagger_file=str(file_path),
                project_id=project_id
            )
        
        return {
            "api_spec_id": api_spec.id,
            "project_id": project_id,
            "version": version,
            "api_count": api_count,
            "test_cases_generated": len(test_cases),
            "test_case_ids": [tc.id for tc in test_cases],
            "imported_at": api_spec.imported_at.isoformat()
        }
    
    def _generate_test_cases(
        self,
        api_spec_id: int,
        swagger_file: str,
        project_id: int
    ) -> List[TestCase]:
        """
        从 Swagger 生成测试用例
        
        Args:
            api_spec_id: API规范ID
            swagger_file: Swagger文件路径
            project_id: 项目ID
            
        Returns:
            生成的测试用例列表
        """
        try:
            print(f"[DEBUG] 开始生成测试用例: swagger_file={swagger_file}")
            
            # 使用 SwaggerTestCaseGenerator 生成用例
            generator = SwaggerTestCaseGenerator(swagger_file)
            core_test_cases: List[CoreTestCase] = generator.generate_all_testcases()
            
            print(f"[DEBUG] SwaggerTestCaseGenerator 生成了 {len(core_test_cases)} 个用例")
            
            # 转换为数据库模型
            db_test_cases = []
            skipped_count = 0
            
            for core_tc in core_test_cases:
                # 检查是否已存在
                existing = self.db.query(TestCase).filter(TestCase.id == core_tc.id).first()
                if existing:
                    skipped_count += 1
                    continue
                
                db_tc = TestCase(
                    id=core_tc.id,
                    title=core_tc.title,
                    module=core_tc.module,
                    priority=core_tc.priority.value if hasattr(core_tc.priority, 'value') else str(core_tc.priority),
                    status='pending',
                    steps=[],  # 简化处理
                    expected=core_tc.expected,
                    data_type=core_tc.data_type.value if hasattr(core_tc.data_type, 'value') else str(core_tc.data_type),
                    expected_behavior=core_tc.expected_behavior.value if hasattr(core_tc.expected_behavior, 'value') else str(core_tc.expected_behavior),
                    execution_config=core_tc.execution_config,
                    assertions=core_tc.assertions,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    created_by='swagger_import',
                    tags=core_tc.tags if core_tc.tags else [],
                    test_point_id=core_tc.test_point_id,
                    api_id=core_tc.api_id,
                    dataset_id=core_tc.dataset_id,
                    source='swagger'
                )
                
                self.db.add(db_tc)
                db_test_cases.append(db_tc)
            
            print(f"[DEBUG] 跳过已存在用例: {skipped_count} 个")
            print(f"[DEBUG] 准备保存新用例: {len(db_test_cases)} 个")
            
            self.db.commit()
            
            print(f"[DEBUG] 成功保存 {len(db_test_cases)} 个测试用例")
            
            return db_test_cases
            
        except Exception as e:
            print(f"[ERROR] 生成测试用例失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return []
    
    def get_api_spec(self, api_spec_id: int) -> Optional[ApiSpec]:
        """获取 API 规范"""
        return self.api_spec_repo.get_by_id(api_spec_id)
    
    def get_api_specs_by_project(self, project_id: int) -> List[ApiSpec]:
        """获取项目的所有 API 规范"""
        return self.db.query(ApiSpec).filter(ApiSpec.project_id == project_id).all()
    
    def delete_api_spec(self, api_spec_id: int) -> bool:
        """删除 API 规范"""
        api_spec = self.api_spec_repo.get_by_id(api_spec_id)
        if not api_spec:
            return False
        
        # 删除文件
        if api_spec.raw_spec_path and os.path.exists(api_spec.raw_spec_path):
            os.remove(api_spec.raw_spec_path)
        
        # 删除数据库记录
        return self.api_spec_repo.delete(api_spec_id)
