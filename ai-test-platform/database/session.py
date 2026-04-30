#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库会话管理
支持SQLite和PostgreSQL
"""

import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager
from typing import Generator

from .models import Base

# 数据库配置
DB_TYPE = os.getenv('DB_TYPE', 'sqlite')  # sqlite/postgresql
DB_PATH = os.getenv('DB_PATH', 'data/test_platform.db')
DB_URL = os.getenv('DATABASE_URL')  # PostgreSQL连接字符串

# 构建数据库URL
if DB_URL:
    # 使用环境变量中的数据库URL(优先级最高)
    DATABASE_URL = DB_URL
elif DB_TYPE == 'postgresql':
    # PostgreSQL配置
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '5432')
    DB_NAME = os.getenv('DB_NAME', 'test_platform')
    DB_USER = os.getenv('DB_USER', 'postgres')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    DATABASE_URL = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
else:
    # SQLite配置(默认)
    db_path = Path(DB_PATH)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    DATABASE_URL = f'sqlite:///{db_path}'

# 创建引擎
if DB_TYPE == 'sqlite':
    # SQLite特殊配置
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},  # SQLite多线程支持
        poolclass=StaticPool,  # 使用静态连接池
        echo=False  # 生产环境关闭SQL日志
    )
else:
    # PostgreSQL配置
    engine = create_engine(
        DATABASE_URL,
        pool_size=10,  # 连接池大小
        max_overflow=20,  # 最大溢出连接数
        pool_pre_ping=True,  # 连接前ping检查
        echo=False
    )

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """
    初始化数据库
    创建所有表
    """
    try:
        Base.metadata.create_all(bind=engine)
        print(f"✅ 数据库初始化成功: {DATABASE_URL}")
        return True
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        return False


def drop_all_tables():
    """
    删除所有表(危险操作,仅用于测试)
    """
    try:
        Base.metadata.drop_all(bind=engine)
        print("⚠️  所有表已删除")
        return True
    except Exception as e:
        print(f"❌ 删除表失败: {e}")
        return False


def get_db() -> Generator[Session, None, None]:
    """
    获取数据库会话(依赖注入用)
    
    用法:
        from fastapi import Depends
        
        @app.get("/api/projects")
        def get_projects(db: Session = Depends(get_db)):
            return db.query(Project).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    获取数据库会话(上下文管理器)
    
    用法:
        with get_db_session() as db:
            projects = db.query(Project).all()
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def close_db():
    """
    关闭数据库连接
    """
    engine.dispose()
    print("✅ 数据库连接已关闭")


def get_db_info():
    """
    获取数据库信息
    """
    return {
        "type": DB_TYPE,
        "url": DATABASE_URL.replace(os.getenv('DB_PASSWORD', ''), '***') if 'postgresql' in DATABASE_URL else DATABASE_URL,
        "engine": str(engine),
        "pool_size": engine.pool.size() if hasattr(engine.pool, 'size') else 'N/A'
    }
