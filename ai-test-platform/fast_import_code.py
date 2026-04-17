#!/usr/bin/env python3
"""快速导入代码库 - 批量处理"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from knowledge.knowledge_manager import KnowledgeManager


def scan_code_files(directory, code_type="backend"):
    """扫描代码文件"""
    print(f"\n📂 扫描{code_type}代码: {directory}")
    
    # 文件扩展名
    if code_type == "backend":
        extensions = {'.java', '.xml', '.properties', '.yml', '.yaml'}
    else:  # frontend
        extensions = {'.js', '.jsx', '.ts', '.tsx', '.vue', '.css', '.html'}
    
    # 排除目录
    exclude_dirs = {'node_modules', 'target', 'build', 'dist', '.git', '__pycache__', '.idea', 'logs'}
    
    files = []
    dir_path = Path(directory)
    
    if not dir_path.exists():
        print(f"❌ 目录不存在: {directory}")
        return files
    
    for root, dirs, filenames in os.walk(dir_path):
        # 排除目录
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        for filename in filenames:
            ext = Path(filename).suffix.lower()
            if ext not in extensions:
                continue
            
            file_path = Path(root) / filename
            
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # 跳过空文件或过大文件
                if not content or len(content) > 50000:  # 50KB限制
                    continue
                
                # 提取关键信息
                rel_path = str(file_path.relative_to(dir_path))
                
                # 简单提取类名和函数名
                classes = []
                functions = []
                
                if ext == '.java':
                    # 提取Java类名
                    for line in content.split('\n'):
                        if 'class ' in line and '{' in line:
                            parts = line.split('class ')
                            if len(parts) > 1:
                                class_name = parts[1].split()[0].split('{')[0]
                                classes.append(class_name)
                        elif 'public ' in line and '(' in line:
                            parts = line.split()
                            for i, part in enumerate(parts):
                                if '(' in part and i > 0:
                                    functions.append(parts[i-1])
                                    break
                
                elif ext in {'.js', '.jsx', '.ts', '.tsx'}:
                    # 提取JS/TS函数名
                    for line in content.split('\n'):
                        if 'function ' in line:
                            parts = line.split('function ')
                            if len(parts) > 1:
                                func_name = parts[1].split('(')[0].strip()
                                functions.append(func_name)
                        elif 'const ' in line and '=>' in line:
                            parts = line.split('const ')
                            if len(parts) > 1:
                                func_name = parts[1].split('=')[0].strip()
                                functions.append(func_name)
                
                files.append({
                    'path': rel_path,
                    'filename': filename,
                    'language': ext[1:],
                    'content': content[:1000],  # 只取前1000字符
                    'classes': ','.join(classes[:5]),
                    'functions': ','.join(functions[:10]),
                    'size': len(content)
                })
                
                if len(files) % 100 == 0:
                    print(f"   已扫描 {len(files)} 个文件...")
                
            except Exception as e:
                continue
    
    print(f"✅ 扫描完成: {len(files)} 个文件")
    return files


def import_code(code_type="backend", directory=None):
    """导入代码"""
    print("=" * 60)
    print(f"🚀 快速导入{code_type}代码")
    print("=" * 60)
    
    # 默认路径
    if not directory:
        if code_type == "backend":
            directory = "../../后端1.2.1"
        else:
            directory = "../../前端-1.2.1"
    
    # 1. 扫描文件
    files = scan_code_files(directory, code_type)
    
    if not files:
        print("❌ 没有找到代码文件")
        return
    
    # 2. 准备批量数据
    print(f"\n💾 准备批量导入...")
    km = KnowledgeManager()
    collection_name = f"{code_type}_code"
    collection = km.kb.get_collection(collection_name)
    
    if not collection:
        print(f"❌ 集合不可用: {collection_name}")
        return
    
    documents = []
    metadatas = []
    ids = []
    
    for i, file_info in enumerate(files):
        doc_id = f"{code_type}_{i}_{file_info['filename'].replace('.', '_')}"
        
        # 文档文本
        doc_text = f"{file_info['filename']} {file_info['path']} {file_info['classes']} {file_info['functions']} {file_info['content']}"
        
        # 元数据
        metadata = {
            "filename": file_info['filename'],
            "path": file_info['path'],
            "language": file_info['language'],
            "classes": file_info['classes'],
            "functions": file_info['functions'],
            "type": code_type
        }
        
        documents.append(doc_text)
        metadatas.append(metadata)
        ids.append(doc_id)
    
    # 3. 批量导入
    batch_size = 100
    total = len(documents)
    
    print(f"\n📦 批量导入 (每批{batch_size}个)...")
    
    for i in range(0, total, batch_size):
        end = min(i + batch_size, total)
        batch_docs = documents[i:end]
        batch_metas = metadatas[i:end]
        batch_ids = ids[i:end]
        
        try:
            collection.add(
                documents=batch_docs,
                metadatas=batch_metas,
                ids=batch_ids
            )
            print(f"   ✅ 已导入 {end}/{total}")
        except Exception as e:
            print(f"   ❌ 批次 {i}-{end} 失败: {e}")
    
    # 4. 验证
    print(f"\n🔍 验证导入...")
    count = collection.count()
    print(f"✅ 集合中共有 {count} 个文档")
    
    # 测试搜索
    results = collection.query(
        query_texts=["采购订单"],
        n_results=3
    )
    
    if results and results['ids']:
        print(f"\n✅ 搜索测试通过:")
        for i, meta in enumerate(results['metadatas'][0], 1):
            print(f"   {i}. {meta['filename']} - {meta['path']}")
    
    print(f"\n" + "=" * 60)
    print("🎉 导入完成!")
    print("=" * 60)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='快速导入代码库')
    parser.add_argument('--type', choices=['backend', 'frontend', 'both'], 
                       default='both', help='代码类型')
    parser.add_argument('--backend-path', help='后端代码路径')
    parser.add_argument('--frontend-path', help='前端代码路径')
    
    args = parser.parse_args()
    
    if args.type in ['backend', 'both']:
        import_code('backend', args.backend_path)
    
    if args.type in ['frontend', 'both']:
        import_code('frontend', args.frontend_path)
