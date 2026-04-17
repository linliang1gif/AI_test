"""验证Maven安装和配置"""
import subprocess
import os
import sys
from pathlib import Path

print("=" * 60)
print("Maven 安装验证工具")
print("=" * 60)
print()

# 检查1: Maven命令是否可用
print("1. 检查Maven命令...")
try:
    result = subprocess.run(
        ["mvn", "-version"],
        capture_output=True,
        text=True,
        timeout=10
    )
    
    if result.returncode == 0:
        print("✅ Maven命令可用")
        print()
        print("Maven版本信息:")
        print("-" * 60)
        print(result.stdout)
        print("-" * 60)
    else:
        print("❌ Maven命令执行失败")
        print(result.stderr)
        sys.exit(1)
        
except FileNotFoundError:
    print("❌ Maven命令未找到")
    print()
    print("可能的原因:")
    print("1. Maven未安装")
    print("2. 环境变量未配置")
    print("3. 需要重新打开命令行窗口")
    print()
    print("解决方案:")
    print("1. 运行 install_maven.ps1 自动安装")
    print("2. 或查看 MAVEN_INSTALL_GUIDE.md 手动安装")
    sys.exit(1)
    
except Exception as e:
    print(f"❌ 检查失败: {e}")
    sys.exit(1)

# 检查2: MAVEN_HOME环境变量
print()
print("2. 检查MAVEN_HOME环境变量...")
maven_home = os.environ.get('MAVEN_HOME')
if maven_home:
    print(f"✅ MAVEN_HOME = {maven_home}")
    
    # 检查目录是否存在
    if Path(maven_home).exists():
        print(f"✅ Maven目录存在")
    else:
        print(f"⚠️  警告: Maven目录不存在: {maven_home}")
else:
    print("⚠️  警告: MAVEN_HOME环境变量未设置")
    print("   虽然Maven可以运行，但建议设置此变量")

# 检查3: Maven配置文件
print()
print("3. 检查Maven配置文件...")
user_home = Path.home()
settings_file = user_home / ".m2" / "settings.xml"

if settings_file.exists():
    print(f"✅ 配置文件存在: {settings_file}")
    
    # 检查是否配置了镜像
    content = settings_file.read_text(encoding='utf-8')
    if 'aliyun' in content.lower() or 'mirror' in content.lower():
        print("✅ 已配置镜像加速")
    else:
        print("⚠️  警告: 未配置镜像，下载依赖可能较慢")
        print("   建议配置阿里云镜像加速")
else:
    print(f"⚠️  配置文件不存在: {settings_file}")
    print("   建议创建配置文件并配置阿里云镜像")

# 检查4: 本地仓库
print()
print("4. 检查Maven本地仓库...")
repo_dir = user_home / ".m2" / "repository"
if repo_dir.exists():
    print(f"✅ 本地仓库存在: {repo_dir}")
    
    # 统计仓库大小
    try:
        total_size = sum(f.stat().st_size for f in repo_dir.rglob('*') if f.is_file())
        size_mb = total_size / (1024 * 1024)
        print(f"   仓库大小: {size_mb:.1f} MB")
    except:
        pass
else:
    print(f"ℹ️  本地仓库不存在（首次使用时会自动创建）")
    print(f"   位置: {repo_dir}")

# 检查5: Java环境
print()
print("5. 检查Java环境...")
try:
    result = subprocess.run(
        ["java", "-version"],
        capture_output=True,
        text=True,
        timeout=10
    )
    
    if result.returncode == 0:
        # Java版本信息在stderr中
        version_info = result.stderr.split('\n')[0]
        print(f"✅ Java已安装: {version_info}")
    else:
        print("❌ Java检查失败")
        
except FileNotFoundError:
    print("❌ Java未安装")
    print("   Maven需要Java环境才能运行")
    print("   请先安装JDK")
except Exception as e:
    print(f"❌ Java检查失败: {e}")

# 总结
print()
print("=" * 60)
print("验证完成！")
print("=" * 60)
print()

# 给出建议
print("📋 下一步操作:")
print()
print("1. 如果所有检查都通过，可以开始使用Maven:")
print("   cd \"D:\\360Downloads\\蓝点\\recycle-server-feature-1.2.2 (1)\\recycle-server-feature-1.2.2\"")
print("   mvn clean install -DskipTests")
print()
print("2. 如果有警告，建议:")
print("   - 配置MAVEN_HOME环境变量")
print("   - 创建settings.xml配置阿里云镜像")
print("   - 查看 MAVEN_INSTALL_GUIDE.md 获取详细说明")
print()
print("3. 启动Java后端服务:")
print("   运行 start_java_backend.bat")
print()
