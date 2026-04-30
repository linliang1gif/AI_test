#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI Test Platform - 数据管理器

负责管理内存数据与文件数据的同步，确保数据一致性。
"""

import json
import threading
import time
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from utils.logger import get_logger

logger = get_logger("data_manager")

class DataManager:
    """数据管理器 - 确保数据一致性"""
    
    def __init__(self, data_file: str = "data/platform_data.json"):
        self.data_file = Path(data_file)
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 内存数据
        self._memory_data = {}
        
        # 线程锁
        self._lock = threading.RLock()
        
        # 最后同步时间
        self._last_sync = None
        self._last_file_mtime = None
        
        # 初始化数据
        self._load_from_file()
        
        logger.info(f"数据管理器初始化完成 - 数据文件: {self.data_file}")
    
    def _load_from_file(self):
        """从文件加载数据"""
        with self._lock:
            try:
                if self.data_file.exists():
                    with open(self.data_file, 'r', encoding='utf-8') as f:
                        file_data = json.load(f)
                    
                    self._memory_data = file_data
                    self._last_file_mtime = self.data_file.stat().st_mtime
                    self._last_sync = time.time()
                    
                    logger.debug(f"从文件加载数据成功 - 记录数: {len(self._memory_data)}")
                else:
                    # 创建默认数据结构
                    self._memory_data = {
                        "projects": [],
                        "apis": [],
                        "test_cases": [],
                        "test_runs": [],
                        "reports": [],
                        "scripts": [],
                        "metadata": {
                            "created_at": datetime.now().isoformat(),
                            "version": "1.0.0"
                        }
                    }
                    self._save_to_file()
                    logger.info("创建默认数据结构")
                    
            except Exception as e:
                logger.error(f"从文件加载数据失败", e)
                # 使用默认数据结构
                self._memory_data = {
                    "projects": [],
                    "apis": [],
                    "test_cases": [],
                    "test_runs": [],
                    "reports": [],
                    "scripts": [],
                    "metadata": {
                        "created_at": datetime.now().isoformat(),
                        "version": "1.0.0",
                        "load_error": str(e)
                    }
                }
    
    def _save_to_file(self):
        """保存数据到文件"""
        try:
            # 确保metadata存在
            if "metadata" not in self._memory_data:
                self._memory_data["metadata"] = {
                    "created_at": datetime.now().isoformat(),
                    "version": "1.0.0"
                }
            
            # 更新元数据
            self._memory_data["metadata"]["updated_at"] = datetime.now().isoformat()
            
            # 原子写入
            temp_file = self.data_file.with_suffix('.tmp')
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(self._memory_data, f, ensure_ascii=False, indent=2)
            
            # 原子替换 - Windows兼容处理
            import os
            if os.name == 'nt':  # Windows系统
                # Windows下需要先删除目标文件
                if self.data_file.exists():
                    try:
                        self.data_file.unlink()
                    except PermissionError:
                        # 如果删除失败,等待一小段时间后重试
                        time.sleep(0.1)
                        self.data_file.unlink()
                temp_file.rename(self.data_file)
            else:
                # Unix系统可以直接替换
                temp_file.replace(self.data_file)
            
            self._last_file_mtime = self.data_file.stat().st_mtime
            self._last_sync = time.time()
            
            logger.debug("数据保存到文件成功")
            
        except Exception as e:
            logger.error(f"保存数据到文件失败", e)
            raise
    
    def _check_file_changes(self):
        """检查文件是否被外部修改"""
        if not self.data_file.exists():
            return False
        
        current_mtime = self.data_file.stat().st_mtime
        return current_mtime != self._last_file_mtime
    
    def sync_data(self, force: bool = False):
        """同步数据"""
        with self._lock:
            try:
                # 检查是否需要同步
                if not force and not self._check_file_changes():
                    return
                
                logger.info("检测到文件变化，开始同步数据")
                
                # 备份当前内存数据
                memory_backup = self._memory_data.copy()
                
                # 重新加载文件数据
                if self.data_file.exists():
                    with open(self.data_file, 'r', encoding='utf-8') as f:
                        file_data = json.load(f)
                    
                    # 合并数据（文件数据优先）
                    merged_data = self._merge_data(memory_backup, file_data)
                    self._memory_data = merged_data
                    
                    self._last_file_mtime = self.data_file.stat().st_mtime
                    self._last_sync = time.time()
                    
                    logger.info("数据同步完成")
                
            except Exception as e:
                logger.error(f"数据同步失败", e)
                # 恢复备份数据
                self._memory_data = memory_backup
                raise
    
    def _merge_data(self, memory_data: Dict[str, Any], file_data: Dict[str, Any]) -> Dict[str, Any]:
        """合并内存数据和文件数据"""
        merged = file_data.copy()
        
        # 合并策略：文件数据优先，但保留内存中的临时数据
        for key in ["projects", "apis", "test_cases", "test_runs", "reports", "scripts"]:
            if key in memory_data and key in file_data:
                # 基于ID合并列表数据
                merged[key] = self._merge_list_data(memory_data[key], file_data[key])
            elif key in memory_data:
                merged[key] = memory_data[key]
        
        return merged
    
    def _merge_list_data(self, memory_list: List[Dict], file_list: List[Dict]) -> List[Dict]:
        """合并列表数据"""
        # 简单策略：使用文件数据，但保留内存中新增的项
        file_ids = {item.get('id') for item in file_list if 'id' in item}
        
        merged = file_list.copy()
        
        # 添加内存中的新项
        for item in memory_list:
            if 'id' in item and item['id'] not in file_ids:
                merged.append(item)
        
        return merged
    
    def get_data(self, key: str, default: Any = None) -> Any:
        """获取数据"""
        with self._lock:
            # 检查是否需要同步
            if self._check_file_changes():
                self.sync_data()
            
            return self._memory_data.get(key, default)
    
    def set_data(self, key: str, value: Any, save: bool = True):
        """设置数据"""
        with self._lock:
            self._memory_data[key] = value
            
            if save:
                self._save_to_file()
            
            logger.debug(f"设置数据: {key}")
    
    def add_item(self, collection: str, item: Dict[str, Any], save: bool = True):
        """添加项到集合"""
        with self._lock:
            if collection not in self._memory_data:
                self._memory_data[collection] = []
            
            # 确保有ID
            if 'id' not in item:
                item['id'] = self._generate_id()
            
            # 添加时间戳
            item['created_at'] = datetime.now().isoformat()
            
            self._memory_data[collection].append(item)
            
            if save:
                self._save_to_file()
            
            logger.debug(f"添加项到 {collection}: {item.get('id')}")
            return item['id']
    
    def update_item(self, collection: str, item_id: str, updates: Dict[str, Any], save: bool = True):
        """更新集合中的项"""
        with self._lock:
            if collection not in self._memory_data:
                return False
            
            for item in self._memory_data[collection]:
                if item.get('id') == item_id:
                    item.update(updates)
                    item['updated_at'] = datetime.now().isoformat()
                    
                    if save:
                        self._save_to_file()
                    
                    logger.debug(f"更新项 {collection}/{item_id}")
                    return True
            
            return False
    
    def delete_item(self, collection: str, item_id: str, save: bool = True):
        """删除集合中的项"""
        with self._lock:
            if collection not in self._memory_data:
                return False
            
            original_count = len(self._memory_data[collection])
            self._memory_data[collection] = [
                item for item in self._memory_data[collection] 
                if item.get('id') != item_id
            ]
            
            deleted = len(self._memory_data[collection]) < original_count
            
            if deleted and save:
                self._save_to_file()
                logger.debug(f"删除项 {collection}/{item_id}")
            
            return deleted
    
    def _generate_id(self) -> str:
        """生成唯一ID"""
        return f"{int(time.time() * 1000)}"
    
    def get_stats(self) -> Dict[str, Any]:
        """获取数据统计"""
        with self._lock:
            stats = {
                "last_sync": self._last_sync,
                "file_exists": self.data_file.exists(),
                "collections": {}
            }
            
            for key, value in self._memory_data.items():
                if isinstance(value, list):
                    stats["collections"][key] = len(value)
            
            return stats

# 全局数据管理器实例
_data_manager = None

def get_data_manager() -> DataManager:
    """获取数据管理器实例"""
    global _data_manager
    if _data_manager is None:
        _data_manager = DataManager()
    return _data_manager