#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
鉴权配置加密/解密工具
最小封装接口,预留后续完整加密实现
"""

import json
import base64
from typing import Dict, Any, Optional


class AuthCrypto:
    """
    鉴权配置加密器
    
    当前实现: Base64编码(非加密,仅混淆)
    TODO: 后续替换为AES/Fernet加密
    """
    
    @staticmethod
    def encrypt_auth_config(auth_config: Optional[Dict[str, Any]]) -> Optional[str]:
        """
        加密鉴权配置
        
        Args:
            auth_config: 鉴权配置字典
            
        Returns:
            加密后的字符串
        """
        if not auth_config:
            return None
        
        try:
            # 序列化为JSON
            json_str = json.dumps(auth_config)
            
            # Base64编码(TODO: 替换为真实加密)
            encoded = base64.b64encode(json_str.encode('utf-8')).decode('utf-8')
            
            return encoded
        except Exception as e:
            raise ValueError(f"加密失败: {str(e)}")
    
    @staticmethod
    def decrypt_auth_config(encrypted_config: Optional[str]) -> Optional[Dict[str, Any]]:
        """
        解密鉴权配置
        
        Args:
            encrypted_config: 加密的配置字符串
            
        Returns:
            解密后的配置字典
        """
        if not encrypted_config:
            return None
        
        try:
            # Base64解码(TODO: 替换为真实解密)
            decoded = base64.b64decode(encrypted_config.encode('utf-8')).decode('utf-8')
            
            # 反序列化JSON
            auth_config = json.loads(decoded)
            
            return auth_config
        except Exception as e:
            raise ValueError(f"解密失败: {str(e)}")
    
    @staticmethod
    def mask_sensitive_value(value: str) -> str:
        """
        脱敏敏感值
        
        Args:
            value: 原始值
            
        Returns:
            脱敏后的值
        """
        if not value or not isinstance(value, str):
            return "****"
        
        if len(value) <= 8:
            return "****"
        
        # 显示前4位和后4位
        return f"{value[:4]}****{value[-4:]}"


# 全局实例
auth_crypto = AuthCrypto()
