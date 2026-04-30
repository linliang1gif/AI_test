#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SVN 工具模块
支持从 SVN 下载文件的多种方式
"""

import subprocess
import tempfile
import requests
from pathlib import Path
from typing import Optional, Tuple
import os
import shutil

from config.svn_config import SVN_CONFIG


class SVNDownloader:
    """SVN 文件下载器"""
    
    def __init__(self):
        self.temp_dir = SVN_CONFIG["temp_dir"]
        self.max_size = SVN_CONFIG["max_file_size_mb"] * 1024 * 1024
        self.timeout = SVN_CONFIG["timeout"]
    
    def download(
        self, 
        svn_url: str, 
        username: Optional[str] = None, 
        password: Optional[str] = None
    ) -> Tuple[bool, Optional[str], str]:
        """
        从 SVN 下载文件
        
        Args:
            svn_url: SVN 文件地址
            username: SVN 用户名（可选）
            password: SVN 密码（可选）
        
        Returns:
            (成功标志, 本地文件路径, 错误信息)
        """
        # 验证 URL
        if not svn_url:
            return False, None, "SVN URL 不能为空"
        
        # 检查文件扩展名
        file_ext = Path(svn_url).suffix.lower()
        if file_ext not in SVN_CONFIG["supported_extensions"]:
            return False, None, f"不支持的文件类型: {file_ext}"
        
        # 使用默认凭据（如果未提供）
        username = username or SVN_CONFIG["default_username"]
        password = password or SVN_CONFIG["default_password"]
        
        # 尝试不同的下载方式
        methods = [
            ("SVN 命令行", self._download_via_cli),
            ("HTTP/HTTPS", self._download_via_http),
        ]
        
        for method_name, method_func in methods:
            try:
                print(f"🔄 尝试使用 {method_name} 下载...")
                success, file_path, error = method_func(svn_url, username, password)
                if success:
                    print(f"✅ 使用 {method_name} 下载成功")
                    return True, file_path, ""
                else:
                    print(f"⚠️  {method_name} 失败: {error}")
            except Exception as e:
                print(f"❌ {method_name} 异常: {e}")
                continue
        
        return False, None, "所有下载方式均失败，请检查 SVN 地址和凭据"
    
    def _download_via_cli(
        self, 
        svn_url: str, 
        username: Optional[str], 
        password: Optional[str]
    ) -> Tuple[bool, Optional[str], str]:
        """使用 SVN 命令行下载"""
        # 检查 svn 命令是否可用
        if not self._check_svn_cli():
            return False, None, "SVN 命令行工具未安装"
        
        # 创建临时文件
        file_ext = Path(svn_url).suffix
        temp_file = tempfile.NamedTemporaryFile(
            delete=False, 
            suffix=file_ext,
            dir=self.temp_dir
        )
        temp_file.close()
        
        # 构建命令
        cmd = ['svn', 'export', svn_url, temp_file.name, '--force', '--non-interactive']
        
        if username and password:
            cmd.extend(['--username', username, '--password', password])
        
        try:
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True,
                timeout=self.timeout
            )
            
            if result.returncode == 0:
                # 检查文件大小
                file_size = os.path.getsize(temp_file.name)
                if file_size > self.max_size:
                    os.unlink(temp_file.name)
                    return False, None, f"文件过大: {file_size / 1024 / 1024:.2f} MB"
                
                return True, temp_file.name, ""
            else:
                os.unlink(temp_file.name)
                return False, None, result.stderr or "SVN 导出失败"
        
        except subprocess.TimeoutExpired:
            os.unlink(temp_file.name)
            return False, None, "下载超时"
        except Exception as e:
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
            return False, None, str(e)
    
    def _download_via_http(
        self, 
        svn_url: str, 
        username: Optional[str], 
        password: Optional[str]
    ) -> Tuple[bool, Optional[str], str]:
        """通过 HTTP/HTTPS 下载（如果 SVN 支持 WebDAV）"""
        # 将 svn:// 转换为 http:// 或 https://
        if svn_url.startswith('svn://'):
            http_url = svn_url.replace('svn://', 'http://')
        elif svn_url.startswith('svn+ssh://'):
            return False, None, "不支持 svn+ssh 协议的 HTTP 下载"
        else:
            http_url = svn_url
        
        # 创建临时文件
        file_ext = Path(svn_url).suffix
        temp_file = tempfile.NamedTemporaryFile(
            delete=False, 
            suffix=file_ext,
            dir=self.temp_dir
        )
        temp_file.close()
        
        try:
            # 准备认证
            auth = None
            if username and password:
                auth = (username, password)
            
            # 下载文件
            response = requests.get(
                http_url, 
                auth=auth, 
                timeout=self.timeout,
                stream=True
            )
            
            if response.status_code == 200:
                # 检查文件大小
                content_length = response.headers.get('content-length')
                if content_length and int(content_length) > self.max_size:
                    return False, None, f"文件过大: {int(content_length) / 1024 / 1024:.2f} MB"
                
                # 写入文件
                with open(temp_file.name, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                # 再次检查文件大小
                file_size = os.path.getsize(temp_file.name)
                if file_size > self.max_size:
                    os.unlink(temp_file.name)
                    return False, None, f"文件过大: {file_size / 1024 / 1024:.2f} MB"
                
                return True, temp_file.name, ""
            else:
                os.unlink(temp_file.name)
                return False, None, f"HTTP 错误: {response.status_code}"
        
        except requests.exceptions.Timeout:
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
            return False, None, "下载超时"
        except Exception as e:
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
            return False, None, str(e)
    
    def _check_svn_cli(self) -> bool:
        """检查 SVN 命令行工具是否可用"""
        try:
            result = subprocess.run(
                ['svn', '--version'], 
                capture_output=True, 
                timeout=5
            )
            return result.returncode == 0
        except:
            return False
    
    def cleanup_temp_files(self, max_age_hours: int = 24):
        """清理临时文件"""
        import time
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        for file_path in self.temp_dir.glob("*"):
            if file_path.is_file():
                file_age = current_time - file_path.stat().st_mtime
                if file_age > max_age_seconds:
                    try:
                        file_path.unlink()
                        print(f"🗑️  已删除过期临时文件: {file_path.name}")
                    except Exception as e:
                        print(f"⚠️  删除临时文件失败: {e}")


# 全局实例
svn_downloader = SVNDownloader()
