#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
代码库导入知识库脚本
将前后端代码索引到ChromaDB知识库中,让AI理解系统实现
"""

import os
import sys
import json
from pathlib import Path
from typing import List, Dict, Any

sys.path.insert(0, str(Path(__file__).parent))

from knowledge.knowledge_manager import KnowledgeManager


class CodebaseIndexer:
    """代码库索引器"""
    
    def __init__(self):
        self.km = KnowledgeManager()
        self.supported_extensions = {
            # 后端
            '.java': 'java',
            '.kt': 'kotlin',
            '.py': 'python',
            '.go': 'go',
            '.cs': 'csharp',
            # 前端
            '.js': 'javascript',
            '.jsx': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.vue': 'vue',
            # 配置
            '.xml': 'xml',
            '.yml': 'yaml',
            '.yaml': 'yaml',
            '.json': 'json',
            '.properties': 'properties'
        }
        
        self.exclude_dirs = {
            'node_modules', 'target', 'build', 'dist', '.git', 
            '__pycache__', '.idea', '.vscode', 'logs', 'temp'
        }
        
        self.exclude_files = {
            '.class', '.jar', '.war', '.ear', '.zip', 
            '.tar', '.gz', '.log', '.lock'
        }
    
    def scan_directory(self, directory: str, max_files: int = 1000) -> List[Dict[str, Any]]:
        """
        扫描目录,收集代码文件
        
        Args:
            directory: 目录路径
            max_files: 最大文件数
            
        Returns:
            文件信息列表
        """
        print(f"\n📂 扫描目录: {directory}")
        
        files = []
        dir_path = Path(directory)
        
        if not dir_path.exists():
            print(f"❌ 目录不存在: {directory}")
            return files
        
        for root, dirs, filenames in os.walk(dir_path):
            # 排除特定目录
            dirs[:] = [d for d in dirs if d not in self.exclude_dirs]
            
            for filename in filenames:
                # 检查文件扩展名
                ext = Path(filename).suffix.lower()
                if ext not in self.supported_extensions:
                    continue
                
                # 排除特定文件
                if any(filename.endswith(e) for e in self.exclude_files):
                    continue
                
                file_path = Path(root) / filename
                
                try:
                    # 读取文件内容
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    # 跳过空文件或过大文件
                    if not content or len(content) > 100000:  # 100KB限制
                        continue
                    
                    # 提取文件信息
                    file_info = {
                        'path': str(file_path),
                        'relative_path': str(file_path.relative_to(dir_path)),
                        'filename': filename,
                        'extension': ext,
                        'language': self.supported_extensions[ext],
                        'content': content,
                        'size': len(content),
                        'lines': content.count('\n') + 1
                    }
                    
                    files.append(file_info)
                    
                    if len(files) >= max_files:
                        print(f"⚠️ 达到最大文件数限制: {max_files}")
                        return files
                    
                except Exception as e:
                    print(f"⚠️ 读取文件失败: {file_path} - {e}")
                    continue
        
        print(f"✅ 扫描完成,找到 {len(files)} 个代码文件")
        return files
    
    def extract_code_metadata(self, file_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        提取代码元数据
        
        Args:
            file_info: 文件信息
            
        Returns:
            元数据
        """
        content = file_info['content']
        language = file_info['language']
        
        metadata = {
            'path': file_info['relative_path'],
            'filename': file_info['filename'],
            'language': language,
            'lines': file_info['lines'],
            'size': file_info['size']
        }
        
        # Java特定提取
        if language == 'java':
            # 提取包名
            import re
            package_match = re.search(r'package\s+([\w.]+);', content)
            if package_match:
                metadata['package'] = package_match.group(1)
            
            # 提取类名
            class_matches = re.findall(r'(?:public|private|protected)?\s*(?:abstract|final)?\s*class\s+(\w+)', content)
            if class_matches:
                metadata['classes'] = ','.join(class_matches[:5])
            
            # 提取接口名
            interface_matches = re.findall(r'(?:public|private|protected)?\s*interface\s+(\w+)', content)
            if interface_matches:
                metadata['interfaces'] = ','.join(interface_matches[:5])
        
        # JavaScript/TypeScript特定提取
        elif language in ['javascript', 'typescript']:
            # 提取函数名
            import re
            func_matches = re.findall(r'(?:function|const|let|var)\s+(\w+)\s*[=\(]', content)
            if func_matches:
                metadata['functions'] = ','.join(func_matches[:10])
            
            # 提取组件名(React)
            component_matches = re.findall(r'(?:function|const)\s+([A-Z]\w+)\s*[=\(]', content)
            if component_matches:
                metadata['components'] = ','.join(component_matches[:5])
        
        # Python特定提取
        elif language == 'python':
            import re
            # 提取类名
            class_matches = re.findall(r'class\s+(\w+)', content)
            if class_matches:
                metadata['classes'] = ','.join(class_matches[:5])
            
            # 提取函数名
            func_matches = re.findall(r'def\s+(\w+)', content)
            if func_matches:
                metadata['functions'] = ','.join(func_matches[:10])
        
        return metadata
    
    def generate_document_text(self, file_info: Dict[str, Any]) -> str:
        """
        生成用于向量化的文档文本
        
        Args:
            file_info: 文件信息
            
        Returns:
            文档文本
        """
        content = file_info['content']
        
        # 提取关键部分(前500行)
        lines = content.split('\n')[:500]
        content_sample = '\n'.join(lines)
        
        # 生成文档
        doc_text = f"""
文件: {file_info['relative_path']}
语言: {file_info['language']}
行数: {file_info['lines']}

代码内容:
{content_sample}
        """.strip()
        
        return doc_text
    
    def import_to_knowledge(self, files: List[Dict[str, Any]], 
                           collection_name: str = "codebase") -> Dict[str, Any]:
        """
        导入代码到知识库
        
        Args:
            files: 文件列表
            collection_name: 集合名称
            
        Returns:
            导入结果
        """
        print(f"\n💾 导入到知识库集合: {collection_name}")
        
        if not self.km.kb or not self.km.kb.available:
            print("❌ 知识库不可用")
            return {'success': 0, 'failed': 0}
        
        # 获取或创建集合
        try:
            collection = self.km.kb.get_collection(collection_name)
            if not collection:
                collection = self.km.kb.create_collection(collection_name)
                print(f"✅ 创建集合: {collection_name}")
            else:
                print(f"✅ 使用现有集合: {collection_name}")
        except Exception as e:
            print(f"❌ 集合创建失败: {e}")
            return {'success': 0, 'failed': 0}
        
        # 批量导入
        success_count = 0
        failed_count = 0
        
        batch_size = 50
        for i in range(0, len(files), batch_size):
            batch = files[i:i+batch_size]
            
            try:
                documents = []
                metadatas = []
                ids = []
                
                for file_info in batch:
                    # 生成文档
                    doc_text = self.generate_document_text(file_info)
                    documents.append(doc_text)
                    
                    # 提取元数据
                    metadata = self.extract_code_metadata(file_info)
                    metadatas.append(metadata)
                    
                    # 生成ID
                    file_id = f"code_{hash(file_info['relative_path']) % 1000000}"
                    ids.append(file_id)
                
                # 批量添加
                collection.add(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids
                )
                
                success_count += len(batch)
                print(f"   进度: {success_count}/{len(files)}")
                
            except Exception as e:
                failed_count += len(batch)
                print(f"⚠️ 批次导入失败: {e}")
        
        print(f"\n✅ 导入完成:")
        print(f"   成功: {success_count}")
        print(f"   失败: {failed_count}")
        
        return {'success': success_count, 'failed': failed_count}


def import_frontend_code(frontend_path: str = "G:/新建文件夹 (3)/前端-1.2.1"):
    """导入前端代码"""
    print("=" * 60)
    print("🎨 导入前端代码")
    print("=" * 60)
    
    indexer = CodebaseIndexer()
    
    # 扫描前端目录
    files = indexer.scan_directory(frontend_path, max_files=500)
    
    if not files:
        print("❌ 未找到前端代码文件")
        return False
    
    # 统计信息
    print(f"\n📊 前端代码统计:")
    lang_stats = {}
    for f in files:
        lang = f['language']
        lang_stats[lang] = lang_stats.get(lang, 0) + 1
    
    for lang, count in sorted(lang_stats.items(), key=lambda x: x[1], reverse=True):
        print(f"   {lang}: {count} 个文件")
    
    # 导入到知识库
    result = indexer.import_to_knowledge(files, "frontend_code")
    
    return result['success'] > 0


def import_backend_code(backend_path: str = "G:/新建文件夹 (3)/后端1.2.1"):
    """导入后端代码"""
    print("\n" + "=" * 60)
    print("⚙️ 导入后端代码")
    print("=" * 60)
    
    indexer = CodebaseIndexer()
    
    # 扫描后端目录
    files = indexer.scan_directory(backend_path, max_files=500)
    
    if not files:
        print("❌ 未找到后端代码文件")
        return False
    
    # 统计信息
    print(f"\n📊 后端代码统计:")
    lang_stats = {}
    for f in files:
        lang = f['language']
        lang_stats[lang] = lang_stats.get(lang, 0) + 1
    
    for lang, count in sorted(lang_stats.items(), key=lambda x: x[1], reverse=True):
        print(f"   {lang}: {count} 个文件")
    
    # 导入到知识库
    result = indexer.import_to_knowledge(files, "backend_code")
    
    return result['success'] > 0


def test_code_search():
    """测试代码搜索"""
    print("\n" + "=" * 60)
    print("🧪 测试代码搜索")
    print("=" * 60)
    
    km = KnowledgeManager()
    
    # 测试查询
    test_queries = [
        ("前端", "frontend_code", "用户登录组件"),
        ("前端", "frontend_code", "路由配置"),
        ("后端", "backend_code", "采购订单Service"),
        ("后端", "backend_code", "入库单Controller"),
        ("后端", "backend_code", "数据库Mapper")
    ]
    
    for code_type, collection_name, query in test_queries:
        print(f"\n🔍 查询 [{code_type}]: {query}")
        
        collection = km.kb.get_collection(collection_name)
        if not collection:
            print(f"   ❌ 集合不存在: {collection_name}")
            continue
        
        try:
            results = collection.query(
                query_texts=[query],
                n_results=3
            )
            
            if results and results['ids']:
                for i, metadata in enumerate(results['metadatas'][0], 1):
                    print(f"\n   {i}. {metadata['filename']}")
                    print(f"      路径: {metadata['path']}")
                    print(f"      语言: {metadata['language']}")
                    print(f"      行数: {metadata['lines']}")
                    if 'classes' in metadata:
                        print(f"      类: {metadata['classes']}")
                    if 'functions' in metadata:
                        print(f"      函数: {metadata['functions'][:100]}")
            else:
                print("   ❌ 未找到相关代码")
                
        except Exception as e:
            print(f"   ❌ 搜索失败: {e}")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🚀 代码库导入知识库")
    print("=" * 60)
    
    # 导入前端代码
    frontend_success = import_frontend_code()
    
    # 导入后端代码
    backend_success = import_backend_code()
    
    # 测试搜索
    if frontend_success or backend_success:
        test_code_search()
    
    # 总结
    print("\n" + "=" * 60)
    print("📋 导入总结")
    print("=" * 60)
    
    if frontend_success:
        print("✅ 前端代码导入成功")
    else:
        print("❌ 前端代码导入失败")
    
    if backend_success:
        print("✅ 后端代码导入成功")
    else:
        print("❌ 后端代码导入失败")
    
    print("\n💡 现在AI可以:")
    print("   1. 理解你的系统代码结构")
    print("   2. 查找相关的类和方法")
    print("   3. 生成更准确的测试用例")
    print("   4. 理解业务逻辑实现")
    print("=" * 60)
