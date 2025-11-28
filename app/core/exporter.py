from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional

import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import Alignment, PatternFill


def _is_file_locked(file_path: Path) -> bool:
    """Check if file is locked (being used by another process)."""
    if not file_path.exists():
        return False
    try:
        # On Windows, try to rename the file to itself
        # This will fail if the file is locked
        import os
        import platform
        
        if platform.system() == "Windows":
            # Try to open in exclusive mode
            try:
                with open(file_path, "r+b") as f:
                    pass
            except (IOError, OSError, PermissionError):
                return True
        else:
            # On Unix-like systems, try to rename
            temp_name = str(file_path) + ".tmp_check"
            try:
                os.rename(file_path, temp_name)
                os.rename(temp_name, file_path)
            except (IOError, OSError, PermissionError):
                return True
        return False
    except Exception:
        # If we can't determine, assume it's not locked
        # The actual write will fail if it is
        return False


def export_cases(cases: List[dict], destination: Path, sheet_name: str | None = None) -> Path:
    """Export cases to an Excel file with basic highlighting."""
    if not cases:
        raise ValueError("没有可导出的测试用例")

    destination.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(cases)

    sheet_name = sheet_name or "Sheet1"

    # Check if file is locked
    if _is_file_locked(destination):
        raise PermissionError(
            f"文件被占用，无法写入：{destination}\n"
            "请关闭 Excel 或其他正在使用该文件的程序后重试。"
        )

    try:
        existing_df = _read_existing_sheet(destination, sheet_name)
        df_to_write = df
        if existing_df is not None and not existing_df.empty:
            df_to_write = pd.concat([existing_df, df], ignore_index=True)
        if "序号" in df_to_write.columns:
            df_to_write["序号"] = range(1, len(df_to_write) + 1)

        if destination.exists():
            with pd.ExcelWriter(destination, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
                df_to_write.to_excel(writer, index=False, sheet_name=sheet_name)
        else:
            with pd.ExcelWriter(destination, engine="openpyxl") as writer:
                df_to_write.to_excel(writer, index=False, sheet_name=sheet_name)

        _apply_formatting(destination, sheet_name)
    except PermissionError as e:
        raise PermissionError(
            f"文件写入失败：{destination}\n"
            "可能原因：\n"
            "1. 文件正在被 Excel 或其他程序打开，请先关闭\n"
            "2. 没有写入权限，请检查文件权限设置\n"
            f"原始错误：{e}"
        )
    except Exception as e:
        raise RuntimeError(f"导出失败：{e}")

    return destination


def _read_existing_sheet(destination: Path, sheet_name: str) -> Optional[pd.DataFrame]:
    if not destination.exists():
        return None
    try:
        return pd.read_excel(destination, sheet_name=sheet_name)
    except ValueError:
        # sheet not found
        return None
    except Exception:
        return None


def _apply_formatting(file_path: Path, sheet_name: str) -> None:
    """Apply formatting to the Excel sheet."""
    try:
        workbook = load_workbook(file_path)
        if sheet_name not in workbook.sheetnames:
            workbook.close()
            return

        sheet = workbook[sheet_name]
        highlight = PatternFill(start_color="FFFF99", end_color="FFFF99", fill_type="solid")

        header_map = {}
        for cell in sheet[1]:
            header_map[cell.column_letter] = str(cell.value or "").strip()

        highlight_targets = {"操作步骤", "预期结果"}
        
        # 设置列宽（根据列名设置合适的宽度）
        column_widths = {
            "序号": 8,
            "项目名称": 15,
            "模块名称": 15,
            "子模块名称": 15,
            "功能点": 30,
            "用例标题": 50,
            "前置条件": 40,
            "输入数据": 20,
            "操作步骤": 50,
            "预期结果": 50,
        }

        for col_idx, col in enumerate(sheet.columns, 1):
            header = header_map.get(col[0].column_letter, "")
            # 设置列宽
            if header in column_widths:
                sheet.column_dimensions[col[0].column_letter].width = column_widths[header]
            else:
                sheet.column_dimensions[col[0].column_letter].width = 15
            
            for cell in col:
                # 确保换行符正确显示
                if cell.value and isinstance(cell.value, str):
                    cell.value = cell.value.replace("\r\n", "\n").replace("\r", "\n")
                cell.alignment = Alignment(wrap_text=True, vertical="top")
                if header in highlight_targets and cell.row != 1:
                    value = str(cell.value or "").strip()
                    if not value:
                        cell.fill = highlight

        workbook.save(file_path)
        workbook.close()
    except PermissionError:
        # 如果格式化失败，至少数据已经写入，只提示用户
        raise PermissionError(
            f"无法格式化文件（文件可能被占用）：{file_path}\n"
            "数据已写入，但格式可能不完整。请关闭 Excel 后重新运行。"
        )
    except Exception as e:
        # 格式化失败不影响数据导出，只记录警告
        pass


