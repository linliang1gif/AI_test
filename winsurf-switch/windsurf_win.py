"""
Windsurf 账号快速切换工具
功能：
1. 保存当前账号为Profile
2. 切换到已保存的Profile
3. 列出所有Profile
4. 删除Profile
"""

import os
import sys
import json
import shutil
import sqlite3
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime
from pathlib import Path

# 配置路径
APPDATA = os.environ.get('APPDATA', '')
LOCALAPPDATA = os.environ.get('LOCALAPPDATA', '')
USERPROFILE = os.environ.get('USERPROFILE', '')

WINDSURF_DATA = os.path.join(APPDATA, 'Windsurf')
WINDSURF_USER = os.path.join(WINDSURF_DATA, 'User')
WINDSURF_GLOBAL_STORAGE = os.path.join(WINDSURF_USER, 'globalStorage')
STATE_DB = os.path.join(WINDSURF_GLOBAL_STORAGE, 'state.vscdb')

# 需要备份的额外目录
SESSION_STORAGE = os.path.join(WINDSURF_DATA, 'Session Storage')
LOCAL_STORAGE = os.path.join(WINDSURF_DATA, 'Local Storage')
NETWORK_DIR = os.path.join(WINDSURF_DATA, 'Network')

CODEIUM_DIR = os.path.join(USERPROFILE, '.codeium', 'windsurf')

# Profile存储目录 (保存到脚本运行的当前目录)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROFILES_DIR = os.path.join(SCRIPT_DIR, 'windsurf_profiles')


class WindsurfAccountSwitcher:
    def __init__(self, root):
        self.root = root
        self.root.title("Windsurf 账号切换器 (Windows) - 开源免费")
        self.root.geometry("550x540")
        self.root.resizable(True, True)
        
        # 确保Profile目录存在
        os.makedirs(PROFILES_DIR, exist_ok=True)
        
        self.setup_ui()
        self.refresh_profiles()
        self.show_current_account()
    
    def setup_ui(self):
        # 当前账号信息
        info_frame = ttk.LabelFrame(self.root, text="当前账号", padding=10)
        info_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.current_account_label = ttk.Label(info_frame, text="正在读取...", font=('Microsoft YaHei', 10))
        self.current_account_label.pack(anchor=tk.W)
        
        self.current_email_label = ttk.Label(info_frame, text="", foreground='gray')
        self.current_email_label.pack(anchor=tk.W)
        
        # Profile列表
        list_frame = ttk.LabelFrame(self.root, text="已保存的账号配置", padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 创建Treeview
        columns = ('name', 'email', 'date')
        self.profile_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=8)
        self.profile_tree.heading('name', text='配置名称')
        self.profile_tree.heading('email', text='邮箱')
        self.profile_tree.heading('date', text='保存时间')
        self.profile_tree.column('name', width=120)
        self.profile_tree.column('email', width=180)
        self.profile_tree.column('date', width=150)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.profile_tree.yview)
        self.profile_tree.configure(yscrollcommand=scrollbar.set)
        
        self.profile_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 按钮区
        btn_frame = ttk.Frame(self.root, padding=10)
        btn_frame.pack(fill=tk.X)
        
        ttk.Button(btn_frame, text="保存当前账号", command=self.save_current_profile).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="切换账号", command=self.on_switch_click).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="删除配置", command=self.delete_profile).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="📂 打开目录", command=self.open_profiles_dir).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="刷新", command=self.refresh_all).pack(side=tk.RIGHT, padx=5)
        
        # 作者信息水印区域
        author_frame = ttk.LabelFrame(self.root, text="✨ 作者信息 ✨", padding=8)
        author_frame.pack(fill=tk.X, padx=10, pady=8)
        
        # 作者名称
        author_name = ttk.Label(
            author_frame, 
            text="👨‍💻 传康KK（万能程序员）",
            foreground='#e91e63',
            font=('Microsoft YaHei', 11, 'bold')
        )
        author_name.pack(anchor=tk.CENTER, pady=(0, 5))
        
        # 微信联系
        wechat_info = ttk.Label(
            author_frame,
            text="📱 微信：1837620622    📧 邮箱：2040168455@qq.com",
            foreground='#1a73e8',
            font=('Microsoft YaHei', 9)
        )
        wechat_info.pack(anchor=tk.CENTER, pady=2)
        
        # 平台信息
        platform_info = ttk.Label(
            author_frame,
            text="🎬 咸鱼/B站：万能程序员    ⭐ GitHub：github.com/1837620622",
            foreground='#666666',
            font=('Microsoft YaHei', 9)
        )
        platform_info.pack(anchor=tk.CENTER, pady=2)
        
        # Star提示
        star_info = ttk.Label(
            author_frame,
            text="🌟 开源免费，欢迎 Star 支持！",
            foreground='#ff9800',
            font=('Microsoft YaHei', 9, 'bold')
        )
        star_info.pack(anchor=tk.CENTER, pady=(5, 0))
        
        # 状态栏
        self.status_var = tk.StringVar(value="就绪 | 开源免费，欢迎Star支持！")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)
    
    def get_current_account_info(self):
        """从state.vscdb读取当前账号信息"""
        try:
            if not os.path.exists(STATE_DB):
                return None, None
            
            conn = sqlite3.connect(STATE_DB)
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM ItemTable WHERE key='windsurfAuthStatus'")
            row = cursor.fetchone()
            conn.close()
            
            if row:
                data = json.loads(row[0])
                return data.get('name', '未知'), data.get('email', '未知')
            return None, None
        except Exception as e:
            print(f"读取账号信息失败: {e}")
            return None, None
    
    def show_current_account(self):
        """显示当前账号信息"""
        name, email = self.get_current_account_info()
        if name:
            self.current_account_label.config(text=f"👤 {name}")
            self.current_email_label.config(text=f"📧 {email}")
        else:
            self.current_account_label.config(text="未登录或无法读取")
            self.current_email_label.config(text="")
    
    def refresh_profiles(self):
        """刷新Profile列表"""
        # 清空列表
        for item in self.profile_tree.get_children():
            self.profile_tree.delete(item)
        
        if not os.path.exists(PROFILES_DIR):
            return
        
        for profile_name in os.listdir(PROFILES_DIR):
            profile_path = os.path.join(PROFILES_DIR, profile_name)
            if os.path.isdir(profile_path):
                meta_file = os.path.join(profile_path, 'profile_meta.json')
                if os.path.exists(meta_file):
                    try:
                        with open(meta_file, 'r', encoding='utf-8') as f:
                            meta = json.load(f)
                        self.profile_tree.insert('', tk.END, values=(
                            profile_name,
                            meta.get('email', '未知'),
                            meta.get('saved_at', '未知')
                        ))
                    except:
                        self.profile_tree.insert('', tk.END, values=(profile_name, '读取失败', ''))
    
    def refresh_all(self):
        """刷新所有信息"""
        self.show_current_account()
        self.refresh_profiles()
        self.status_var.set("已刷新")
    
    def open_profiles_dir(self):
        """打开配置文件存储目录"""
        # 确保目录存在
        os.makedirs(PROFILES_DIR, exist_ok=True)
        # Windows 使用 explorer 打开目录
        os.startfile(PROFILES_DIR)
        self.status_var.set(f"已打开目录: {PROFILES_DIR}")
    
    def is_windsurf_running(self):
        """检查Windsurf是否正在运行"""
        try:
            result = subprocess.run(
                ['tasklist', '/FI', 'IMAGENAME eq Windsurf.exe'],
                capture_output=True, text=True
            )
            return 'Windsurf.exe' in result.stdout
        except:
            return False
    
    def verify_switch(self, expected_email):
        """验证切换是否成功"""
        _, current_email = self.get_current_account_info()
        return current_email == expected_email
    
    def on_switch_click(self):
        """切换按钮点击事件"""
        try:
            self.status_var.set("正在切换...")
            self.root.update()  # 强制更新UI
            self.switch_profile()
        except Exception as e:
            messagebox.showerror("异常", f"切换过程发生异常:\n{e}")
            import traceback
            traceback.print_exc()
    
    def force_quit_windsurf(self):
        """强制退出 Windsurf 进程"""
        try:
            subprocess.run(['taskkill', '/F', '/IM', 'Windsurf.exe'], capture_output=True)
            import time
            time.sleep(1)  # 等待进程完全退出
            return not self.is_windsurf_running()
        except:
            return False
    
    def save_current_profile(self):
        """保存当前账号为Profile"""
        # 检查 Windsurf 是否正在运行
        if self.is_windsurf_running():
            result = messagebox.askyesno(
                "警告", 
                "检测到 Windsurf 正在运行！\n\n"
                "为确保认证数据完整保存，建议先关闭 Windsurf。\n\n"
                "是否强制关闭 Windsurf 后继续？"
            )
            if result:
                self.status_var.set("正在关闭 Windsurf...")
                self.root.update()
                if not self.force_quit_windsurf():
                    messagebox.showerror("错误", "无法关闭 Windsurf，请手动关闭后重试")
                    return
            else:
                return
        
        name, email = self.get_current_account_info()
        if not name:
            messagebox.showerror("错误", "无法读取当前账号信息，请确保已登录Windsurf")
            return
        
        # 使用邮箱前缀作为默认名称
        default_name = email.split('@')[0] if email else "profile"
        profile_name = simpledialog.askstring("保存配置", "请输入配置名称:", initialvalue=default_name)
        
        if not profile_name:
            return
        
        # 清理非法字符
        profile_name = "".join(c for c in profile_name if c.isalnum() or c in ('_', '-', '.'))
        
        profile_path = os.path.join(PROFILES_DIR, profile_name)
        
        if os.path.exists(profile_path):
            if not messagebox.askyesno("确认", f"配置 '{profile_name}' 已存在，是否覆盖？"):
                return
            shutil.rmtree(profile_path)
        
        try:
            os.makedirs(profile_path)
            
            # ★★★ 核心改进：复制整个 globalStorage 目录 ★★★
            global_storage_backup = os.path.join(profile_path, 'globalStorage')
            if os.path.exists(WINDSURF_GLOBAL_STORAGE):
                # 复制整个目录，排除大型备份文件
                shutil.copytree(
                    WINDSURF_GLOBAL_STORAGE, 
                    global_storage_backup,
                    ignore=shutil.ignore_patterns('*.backup.*', 'ms-*')
                )
            
            # 复制Session Storage
            if os.path.exists(SESSION_STORAGE):
                shutil.copytree(SESSION_STORAGE, os.path.join(profile_path, 'Session Storage'))
            
            # 复制Local Storage
            if os.path.exists(LOCAL_STORAGE):
                shutil.copytree(LOCAL_STORAGE, os.path.join(profile_path, 'Local Storage'))
            
            # 复制Network目录(包含Cookies)
            if os.path.exists(NETWORK_DIR):
                shutil.copytree(NETWORK_DIR, os.path.join(profile_path, 'Network'))
            
            # 复制.codeium目录中的关键文件
            codeium_backup = os.path.join(profile_path, 'codeium')
            if os.path.exists(CODEIUM_DIR):
                # 只复制关键文件，不复制大型缓存
                os.makedirs(codeium_backup, exist_ok=True)
                for item in ['installation_id', 'user_settings.pb']:
                    src = os.path.join(CODEIUM_DIR, item)
                    if os.path.exists(src):
                        shutil.copy2(src, codeium_backup)
            
            # 保存元数据
            meta = {
                'name': name,
                'email': email,
                'saved_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            with open(os.path.join(profile_path, 'profile_meta.json'), 'w', encoding='utf-8') as f:
                json.dump(meta, f, ensure_ascii=False, indent=2)
            
            self.refresh_profiles()
            self.status_var.set(f"已保存配置: {profile_name}")
            messagebox.showinfo("成功", f"配置 '{profile_name}' 保存成功！\n\n已备份 globalStorage 完整目录。")
        
        except Exception as e:
            messagebox.showerror("错误", f"保存失败: {e}")
    
    def switch_profile(self):
        """切换到选中的Profile"""
        selected = self.profile_tree.selection()
        if not selected:
            messagebox.showwarning("警告", "请先选择要切换的配置")
            return
        
        # 注意：Treeview返回的数字可能是整数，需要转换为字符串
        profile_name = str(self.profile_tree.item(selected[0])['values'][0])
        target_email = str(self.profile_tree.item(selected[0])['values'][1])
        profile_path = os.path.join(PROFILES_DIR, profile_name)
        
        # 调试信息
        print(f"[DEBUG] 切换操作开始")
        print(f"[DEBUG] profile_name: {profile_name}, type: {type(profile_name)}")
        print(f"[DEBUG] target_email: {target_email}")
        print(f"[DEBUG] profile_path: {profile_path}")
        print(f"[DEBUG] profile_path exists: {os.path.exists(profile_path)}")
        
        # 检查配置目录是否存在
        if not os.path.exists(profile_path):
            messagebox.showerror("错误", f"配置目录不存在: {profile_path}")
            return
        
        # 获取当前账号
        _, current_email = self.get_current_account_info()
        print(f"[DEBUG] current_email: {current_email}")
        
        if current_email == target_email:
            messagebox.showinfo("提示", f"当前已经是账号 '{target_email}'")
            return
        
        # 检查 Windsurf 是否正在运行
        if self.is_windsurf_running():
            result = messagebox.askyesno(
                "警告", 
                f"检测到 Windsurf 正在运行！\n\n"
                f"当前账号: {current_email}\n"
                f"目标账号: {target_email}\n\n"
                f"切换账号需要先关闭 Windsurf。\n\n"
                f"是否强制关闭 Windsurf 后继续切换？"
            )
            if result:
                self.status_var.set("正在关闭 Windsurf...")
                self.root.update()
                if not self.force_quit_windsurf():
                    messagebox.showerror("错误", "无法关闭 Windsurf，请手动关闭后重试")
                    return
            else:
                return
        else:
            # Windsurf 未运行，确认切换
            if not messagebox.askyesno("确认切换", f"当前账号: {current_email}\n目标账号: {target_email}\n\n确定要切换吗？"):
                return
        
        errors = []
        success_items = []
        
        # ★★★ 核心改进：检查并还原整个 globalStorage 目录 ★★★
        global_storage_backup = os.path.join(profile_path, 'globalStorage')
        if os.path.exists(global_storage_backup):
            try:
                # 删除现有的 globalStorage 目录
                if os.path.exists(WINDSURF_GLOBAL_STORAGE):
                    shutil.rmtree(WINDSURF_GLOBAL_STORAGE)
                # 复制备份的 globalStorage 目录
                shutil.copytree(global_storage_backup, WINDSURF_GLOBAL_STORAGE)
                success_items.append("globalStorage (完整目录)")
                print(f"[DEBUG] globalStorage 目录还原成功")
            except Exception as e:
                errors.append(f"globalStorage: {str(e)[:80]}")
                print(f"[DEBUG] globalStorage 还原失败: {e}")
        else:
            # 兼容旧版配置：只复制 state.vscdb
            state_backup = os.path.join(profile_path, 'state.vscdb')
            print(f"[DEBUG] state_backup: {state_backup}, exists: {os.path.exists(state_backup)}")
            try:
                if os.path.exists(state_backup):
                    shutil.copy2(state_backup, STATE_DB)
                    success_items.append("state.vscdb")
                    print(f"[DEBUG] state.vscdb 复制成功")
                else:
                    errors.append("state.vscdb: 文件不存在")
            except Exception as e:
                errors.append(f"state.vscdb: {e}")
                print(f"[DEBUG] state.vscdb 复制失败: {e}")
        
        # 2. 尝试复制Session Storage
        session_backup = os.path.join(profile_path, 'Session Storage')
        try:
            if os.path.exists(session_backup):
                if os.path.exists(SESSION_STORAGE):
                    shutil.rmtree(SESSION_STORAGE)
                shutil.copytree(session_backup, SESSION_STORAGE)
                success_items.append("Session Storage")
        except Exception as e:
            errors.append(f"Session Storage: {str(e)[:50]}")
        
        # 3. 尝试复制Local Storage
        local_backup = os.path.join(profile_path, 'Local Storage')
        try:
            if os.path.exists(local_backup):
                if os.path.exists(LOCAL_STORAGE):
                    shutil.rmtree(LOCAL_STORAGE)
                shutil.copytree(local_backup, LOCAL_STORAGE)
                success_items.append("Local Storage")
        except Exception as e:
            errors.append(f"Local Storage: {str(e)[:50]}")
        
        # 4. 尝试复制Network
        network_backup = os.path.join(profile_path, 'Network')
        try:
            if os.path.exists(network_backup):
                if os.path.exists(NETWORK_DIR):
                    shutil.rmtree(NETWORK_DIR)
                shutil.copytree(network_backup, NETWORK_DIR)
                success_items.append("Network")
        except Exception as e:
            errors.append(f"Network: {str(e)[:50]}")
        
        # 5. 复制codeium配置
        codeium_backup = os.path.join(profile_path, 'codeium')
        try:
            if os.path.exists(codeium_backup):
                for item in os.listdir(codeium_backup):
                    src = os.path.join(codeium_backup, item)
                    dst = os.path.join(CODEIUM_DIR, item)
                    shutil.copy2(src, dst)
                success_items.append("codeium")
        except Exception as e:
            errors.append(f"codeium: {str(e)[:50]}")
        
        # 刷新显示
        self.show_current_account()
        
        # 刷新显示
        self.root.update()  # 强制更新UI
        
        # 验证切换结果
        _, new_email = self.get_current_account_info()
        print(f"[DEBUG] 切换后账号: {new_email}")
        
        if new_email == target_email:
            self.status_var.set(f"[OK] 切换成功: {profile_name}")
            msg = f"[OK] 切换成功!\n\n当前账号: {target_email}\n\n成功复制: {', '.join(success_items)}"
            if errors:
                msg += f"\n\n部分文件复制失败(不影响使用):\n" + "\n".join(errors)
            msg += "\n\n请重启 Windsurf 生效。"
            messagebox.showinfo("切换成功", msg)
        else:
            self.status_var.set(f"[FAIL] 切换失败")
            msg = f"[FAIL] 切换失败\n\n期望: {target_email}\n实际: {new_email}\n\n错误信息:\n" + "\n".join(errors) if errors else f"期望: {target_email}\n实际: {new_email}"
            messagebox.showerror("切换失败", msg)
    
    def delete_profile(self):
        """删除选中的Profile"""
        selected = self.profile_tree.selection()
        if not selected:
            messagebox.showwarning("警告", "请先选择要删除的配置")
            return
        
        # 转换为字符串，防止纯数字配置名导致的类型错误
        profile_name = str(self.profile_tree.item(selected[0])['values'][0])
        
        if not messagebox.askyesno("确认删除", f"确定要删除配置 '{profile_name}'？\n\n此操作不可恢复。"):
            return
        
        try:
            profile_path = os.path.join(PROFILES_DIR, profile_name)
            shutil.rmtree(profile_path)
            self.refresh_profiles()
            self.status_var.set(f"已删除配置: {profile_name}")
        except Exception as e:
            messagebox.showerror("错误", f"删除失败: {e}")


def main():
    root = tk.Tk()
    
    # 设置样式
    style = ttk.Style()
    style.theme_use('clam')
    
    app = WindsurfAccountSwitcher(root)
    root.mainloop()


if __name__ == '__main__':
    main()
