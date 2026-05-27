#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
鉴权配置业务逻辑
"""

from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from database.models import AuthProfile
from database import get_environment_repo
from schemas.project_schemas import AuthProfileCreate, AuthProfileUpdate
from utils.auth_crypto import auth_crypto


class AuthService:
    """鉴权服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.env_repo = get_environment_repo(db)

    def _decrypt_and_upgrade_config(self, auth_profile: AuthProfile) -> Optional[Dict[str, Any]]:
        """读取鉴权配置；旧格式在成功解密后升级为当前密文格式。"""
        auth_config = auth_crypto.decrypt_auth_config(auth_profile.auth_config)
        if auth_config and auth_crypto.needs_reencrypt(auth_profile.auth_config):
            auth_profile.auth_config = auth_crypto.encrypt_auth_config(auth_config)
            self.db.commit()
            self.db.refresh(auth_profile)
        return auth_config
    
    def create_auth_profile(self, auth_data: AuthProfileCreate) -> AuthProfile:
        """创建鉴权配置"""
        # 检查环境是否存在
        environment = self.env_repo.get_by_id(auth_data.environment_id)
        if not environment:
            raise ValueError(f"环境ID {auth_data.environment_id} 不存在")
        
        # 检查是否已有鉴权配置
        existing = self.db.query(AuthProfile).filter(
            AuthProfile.environment_id == auth_data.environment_id
        ).first()
        if existing:
            raise ValueError(f"环境ID {auth_data.environment_id} 已有鉴权配置")
        
        # 加密auth_config
        encrypted_config = auth_crypto.encrypt_auth_config(auth_data.auth_config)
        
        auth_profile = AuthProfile(
            environment_id=auth_data.environment_id,
            auth_type=auth_data.auth_type.value,
            auth_config=encrypted_config,
            default_headers=auth_data.default_headers
        )
        
        self.db.add(auth_profile)
        self.db.commit()
        self.db.refresh(auth_profile)
        
        return auth_profile
    
    def get_auth_profile(self, auth_id: int) -> Optional[AuthProfile]:
        """获取鉴权配置"""
        return self.db.query(AuthProfile).filter(AuthProfile.id == auth_id).first()
    
    def get_by_environment(self, environment_id: int) -> Optional[AuthProfile]:
        """根据环境ID获取鉴权配置"""
        return self.db.query(AuthProfile).filter(
            AuthProfile.environment_id == environment_id
        ).first()
    
    def update_auth_profile(self, auth_id: int, auth_data: AuthProfileUpdate) -> Optional[AuthProfile]:
        """更新鉴权配置"""
        auth_profile = self.get_auth_profile(auth_id)
        if not auth_profile:
            return None
        
        if auth_data.auth_type is not None:
            auth_profile.auth_type = auth_data.auth_type.value
        
        if auth_data.auth_config is not None:
            # 加密auth_config
            auth_profile.auth_config = auth_crypto.encrypt_auth_config(auth_data.auth_config)
        
        if auth_data.default_headers is not None:
            auth_profile.default_headers = auth_data.default_headers
        
        self.db.commit()
        self.db.refresh(auth_profile)
        
        return auth_profile
    
    def delete_auth_profile(self, auth_id: int) -> bool:
        """删除鉴权配置"""
        auth_profile = self.get_auth_profile(auth_id)
        if not auth_profile:
            return False
        
        self.db.delete(auth_profile)
        self.db.commit()
        return True
    
    def mask_sensitive_data(self, auth_profile: AuthProfile) -> Dict[str, Any]:
        """脱敏敏感数据"""
        auth_config = self._decrypt_and_upgrade_config(auth_profile)
        
        if not auth_config:
            return {}
        
        # 脱敏处理
        masked_config = {}
        for key, value in auth_config.items():
            if key in ['token', 'key_value', 'password', 'secret']:
                # 敏感字段脱敏
                masked_config[key] = auth_crypto.mask_sensitive_value(str(value))
            else:
                masked_config[key] = value
        
        return masked_config
    
    def get_decrypted_config(self, auth_profile: AuthProfile) -> Optional[Dict[str, Any]]:
        """
        获取解密后的配置(仅内部使用,不对外暴露)
        
        用于执行测试时获取真实鉴权信息
        """
        return self._decrypt_and_upgrade_config(auth_profile)
