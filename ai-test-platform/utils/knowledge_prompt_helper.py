#!/usr/bin/env python3
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
            api_context = "\n\n【相关API信息】\n"
            for i, metadata in enumerate(results['metadatas'][0], 1):
                api_context += f"{i}. {metadata['method']} {metadata['path']}\n"
                api_context += f"   摘要: {metadata['summary']}\n"
                if 'tags' in metadata:
                    api_context += f"   标签: {metadata['tags']}\n"
            
            # 将API上下文添加到prompt
            enhanced_prompt = f"{prompt}\n{api_context}"
            
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
            code_context = f"\n\n【相关{code_type}代码】\n"
            for i, metadata in enumerate(results['metadatas'][0], 1):
                code_context += f"{i}. {metadata['filename']}\n"
                code_context += f"   路径: {metadata['path']}\n"
                code_context += f"   语言: {metadata['language']}\n"
                if 'classes' in metadata:
                    code_context += f"   类: {metadata['classes']}\n"
                if 'functions' in metadata:
                    funcs = metadata['functions'][:100]  # 限制长度
                    code_context += f"   函数: {funcs}\n"
            
            # 将代码上下文添加到prompt
            enhanced_prompt = f"{prompt}\n{code_context}"
            
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
            for i, metadata in enumerate(results['metadatas'][0]):
                distance = results['distances'][0][i] if 'distances' in results else 0
                similarity = 1 - distance  # 转换为相似度
                
                apis.append({
                    'method': metadata['method'],
                    'path': metadata['path'],
                    'summary': metadata['summary'],
                    'tags': metadata.get('tags', ''),
                    'similarity': similarity
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
            for i, metadata in enumerate(results['metadatas'][0]):
                distance = results['distances'][0][i] if 'distances' in results else 0
                similarity = 1 - distance  # 转换为相似度
                
                files.append({
                    'filename': metadata['filename'],
                    'path': metadata['path'],
                    'language': metadata['language'],
                    'classes': metadata.get('classes', ''),
                    'functions': metadata.get('functions', '')[:100],
                    'similarity': similarity
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
