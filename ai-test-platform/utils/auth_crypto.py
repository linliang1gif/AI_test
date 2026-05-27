#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
鉴权配置加密/解密工具。

存储格式：
- enc:v1:<fernet-token>：当前真实加密格式
- <base64-json>：旧版混淆格式，读取兼容
- <json>：更早期明文 JSON，读取兼容
"""

import base64
import hashlib
import json
import os
from typing import Dict, Any, Optional

from cryptography.fernet import Fernet, InvalidToken


class AuthCrypto:
    """鉴权配置加密器"""

    VERSION_PREFIX = "enc:v1:"
    LEGACY_DEV_SECRET = "ai-test-platform-dev-auth-config-key"

    @classmethod
    def _get_fernet(cls) -> Fernet:
        key = os.getenv("AUTH_CONFIG_KEY", "").strip()
        if key:
            return Fernet(key.encode("utf-8"))

        seed = os.getenv("JWT_SECRET_KEY", cls.LEGACY_DEV_SECRET).encode("utf-8")
        derived_key = base64.urlsafe_b64encode(hashlib.sha256(seed).digest())
        return Fernet(derived_key)

    @staticmethod
    def _loads_json_object(raw: str) -> Optional[Dict[str, Any]]:
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise ValueError("鉴权配置必须是JSON对象")
        return data

    @classmethod
    def encrypt_auth_config(cls, auth_config: Optional[Dict[str, Any]]) -> Optional[str]:
        """
        加密鉴权配置。

        Args:
            auth_config: 鉴权配置字典

        Returns:
            带版本前缀的密文字符串
        """
        if not auth_config:
            return None

        try:
            json_str = json.dumps(auth_config, ensure_ascii=False, separators=(",", ":"))
            token = cls._get_fernet().encrypt(json_str.encode("utf-8")).decode("utf-8")
            return f"{cls.VERSION_PREFIX}{token}"
        except Exception as e:
            raise ValueError(f"加密失败: {str(e)}")

    @classmethod
    def decrypt_auth_config(cls, encrypted_config: Optional[str]) -> Optional[Dict[str, Any]]:
        """
        解密鉴权配置。

        兼容读取当前 Fernet 密文、旧 Base64(JSON) 和旧明文 JSON。
        """
        if not encrypted_config:
            return None

        raw_config = encrypted_config.strip()
        if not raw_config:
            return None

        try:
            if raw_config.startswith(cls.VERSION_PREFIX):
                token = raw_config[len(cls.VERSION_PREFIX):]
                decoded = cls._get_fernet().decrypt(token.encode("utf-8")).decode("utf-8")
                return cls._loads_json_object(decoded)

            if raw_config.startswith("{"):
                return cls._loads_json_object(raw_config)

            decoded = base64.b64decode(raw_config.encode("utf-8")).decode("utf-8")
            return cls._loads_json_object(decoded)
        except (InvalidToken, Exception) as e:
            raise ValueError(f"解密失败: {str(e)}")

    @classmethod
    def needs_reencrypt(cls, encrypted_config: Optional[str]) -> bool:
        """判断存量配置是否需要升级为当前加密格式。"""
        if not encrypted_config:
            return False
        return not encrypted_config.strip().startswith(cls.VERSION_PREFIX)
    
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
