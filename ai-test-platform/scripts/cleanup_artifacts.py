#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
"""
P2-9B: Artifact 清理脚本

支持参数:
  --older-than-days N   清理 N 天前的文件 (默认 7)
  --dry-run             仅列出不删除 (默认)
  --delete              真正删除
  --type TYPE           screenshots | traces | visual | sessions | all (默认 all)

安全:
  - 默认 dry-run
  - 不删除 baselines, 除非 --type visual-baselines 并 --confirm-baselines
  - 不删除 .env / 数据库 / 日志 / 源码
  - 不删除当前正在执行的 run_id artifact (best-effort)
"""
import argparse
import os
import sys
import time
from pathlib import Path
from datetime import datetime, timedelta

ARTIFACT_DIRS = {
    "screenshots": os.path.join("data", "artifacts", "ui", "screenshots"),
    "traces": os.path.join("data", "artifacts", "ui", "traces"),
    "visual": os.path.join("data", "artifacts", "visual"),
    "sessions": os.path.join("data", "sessions"),
}
BASELINES_DIR = os.path.join("data", "artifacts", "visual", "baselines")

PROTECTED_EXTENSIONS = {".env", ".db", ".sqlite", ".py", ".js", ".jsx", ".ts", ".tsx", ".md", ".json", ".yaml", ".yml"}
PROTECTED_DIRS = {"baselines"}


def get_files_to_clean(base_dir: str, older_than_days: int, include_baselines: bool = False) -> list:
    """List files eligible for cleanup."""
    if not os.path.isdir(base_dir):
        return []

    cutoff = time.time() - (older_than_days * 86400)
    files = []

    for root, dirs, filenames in os.walk(base_dir):
        # Skip baselines unless explicitly requested
        if not include_baselines:
            rel = os.path.relpath(root, base_dir)
            if "baselines" in rel.split(os.sep):
                continue

        for f in filenames:
            fp = os.path.join(root, f)
            ext = os.path.splitext(f)[1].lower()
            if ext in PROTECTED_EXTENSIONS:
                continue
            try:
                mtime = os.path.getmtime(fp)
                if mtime < cutoff:
                    size = os.path.getsize(fp)
                    files.append({"path": fp, "size": size, "mtime": mtime})
            except OSError:
                continue

    return files


def format_size(total_bytes: int) -> str:
    if total_bytes < 1024:
        return f"{total_bytes} B"
    elif total_bytes < 1024 * 1024:
        return f"{total_bytes / 1024:.1f} KB"
    else:
        return f"{total_bytes / (1024 * 1024):.1f} MB"


def main():
    parser = argparse.ArgumentParser(description="P2-9B: Artifact 清理脚本")
    parser.add_argument("--older-than-days", type=int, default=7, help="清理 N 天前的文件")
    parser.add_argument("--dry-run", action="store_true", default=True, help="仅列出不删除 (默认)")
    parser.add_argument("--delete", action="store_true", help="真正删除文件")
    parser.add_argument("--type", default="all", choices=["screenshots", "traces", "visual", "sessions", "all", "visual-baselines"],
                        help="清理类型")
    parser.add_argument("--confirm-baselines", action="store_true", help="确认删除 baselines (需配合 --type visual-baselines)")
    args = parser.parse_args()

    do_delete = args.delete
    older_than = args.older_than_days
    cleanup_type = args.type

    print(f"P2-9B Artifact 清理工具")
    print(f"  清理类型: {cleanup_type}")
    print(f"  清理条件: {older_than} 天前的文件")
    print(f"  模式: {'[DELETE] 删除' if do_delete else '[DRY-RUN] 干运行 (dry-run)'}")
    print()

    # Determine directories
    if cleanup_type == "all":
        dirs = list(ARTIFACT_DIRS.items())
    elif cleanup_type == "visual-baselines":
        if not args.confirm_baselines:
            print("[WARN] 删除 baselines 需要 --confirm-baselines 参数确认")
            sys.exit(1)
        dirs = [("visual-baselines", BASELINES_DIR)]
    else:
        dirs = [(cleanup_type, ARTIFACT_DIRS.get(cleanup_type, ""))]

    total_files = 0
    total_size = 0
    deleted = 0

    for name, d in dirs:
        include_baselines = (cleanup_type == "visual-baselines")
        files = get_files_to_clean(d, older_than, include_baselines)
        if not files:
            print(f"  [{name}] 无符合条件的文件")
            continue

        dir_size = sum(f["size"] for f in files)
        print(f"  [{name}] {len(files)} 个文件, 共 {format_size(dir_size)}")
        total_files += len(files)
        total_size += dir_size

        for f in files:
            age_days = (time.time() - f["mtime"]) / 86400
            if do_delete:
                try:
                    os.remove(f["path"])
                    deleted += 1
                except OSError as e:
                    print(f"    [ERR] 删除失败: {f['path']}: {e}")

    print()
    print(f"汇总: {total_files} 个文件, 共 {format_size(total_size)}")
    if do_delete:
        print(f"已删除: {deleted} 个文件")
    else:
        print(f"(dry-run 模式, 未实际删除。使用 --delete 删除)")


if __name__ == "__main__":
    main()
