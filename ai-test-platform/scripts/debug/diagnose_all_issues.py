"""
全面诊断脚本 - 找出所有问题
"""
import requests
import json
import sys
from pathlib import Path


def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)


def check_backend_modules():
    """检查后端模块"""
    print_section("1. 后端模块检查")
    
    modules = [
        ("Test Agent", "/api/agent/health"),
        ("Strategy Engine", "/api/strategy/health"),  
        ("Orchestrator", "/api/orchestrator/health"),
        ("Self-Healing", "/api/healing/health"),
        ("Pipeline", "/api/pipeline/health"),
    ]
    
    issues = []
    for name, endpoint in modules:
        try:
            r = requests.get(f"http://localhost:8000{endpoint}", timeout=3)
            if r.status_code == 200:
                data = r.json()
                status = data.get('status', 'unknown')
                if status == 'healthy':
                    print(f"✅ {name}: 正常")
                else:
                    print(f"⚠️  {name}: {status}")
                    issues.append(f"{name} 状态异常: {status}")
            else:
                print(f"❌ {name}: HTTP {r.status_code}")
                issues.append(f"{name} 返回错误: {r.status_code}")
        except Exception as e:
            print(f"❌ {name}: {str(e)}")
            issues.append(f"{name} 无法访问: {str(e)}")
    
    return issues


def check_ai_models():
    """检查AI模型配置"""
    print_section("2. AI模型配置检查")
    
    issues = []
    env_file = Path(".env")
    
    if not env_file.exists():
        print("❌ .env 文件不存在")
        issues.append(".env 文件缺失")
        return issues
    
    # 读取配置
    config = {}
    with open(env_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                config[key] = value
    
    # 检查关键配置
    required_keys = [
        'ANTHROPIC_API_KEY',
        'ANTHROPIC_BASE_URL',
        'DEFAULT_AI_PROVIDER',
        'DEFAULT_AI_MODEL'
    ]
    
    for key in required_keys:
        if key in config and config[key]:
            print(f"✅ {key}: 已配置")
        else:
            print(f"❌ {key}: 未配置")
            issues.append(f"{key} 未配置")
    
    return issues


def check_database():
    """检查数据库"""
    print_section("3. 数据库检查")
    
    issues = []
    
    # 检查SQLite
    db_file = Path("data/platform_data.json")
    if db_file.exists():
        print(f"✅ 数据文件存在: {db_file}")
        try:
            with open(db_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print(f"   - 项目数: {len(data.get('projects', []))}")
                print(f"   - API数: {len(data.get('apis', []))}")
                print(f"   - 测试用例数: {len(data.get('testcases', []))}")
        except Exception as e:
            print(f"⚠️  数据文件读取失败: {e}")
            issues.append(f"数据文件损坏: {e}")
    else:
        print(f"❌ 数据文件不存在: {db_file}")
        issues.append("数据文件缺失")
    
    # 检查ChromaDB
    chroma_dir = Path("chroma_db")
    if chroma_dir.exists():
        print(f"✅ ChromaDB目录存在")
    else:
        print(f"⚠️  ChromaDB目录不存在")
        issues.append("ChromaDB未初始化")
    
    return issues


def check_frontend():
    """检查前端"""
    print_section("4. 前端检查")
    
    issues = []
    
    # 检查前端文件
    frontend_dir = Path("frontend")
    if not frontend_dir.exists():
        print("❌ frontend目录不存在")
        issues.append("前端代码缺失")
        return issues
    
    # 检查关键文件
    key_files = [
        "package.json",
        "src/pages/AiTestConsole.jsx",
        "src/pages/Projects.jsx",
        "src/pages/TestCases.jsx"
    ]
    
    for file in key_files:
        file_path = frontend_dir / file
        if file_path.exists():
            print(f"✅ {file}")
        else:
            print(f"❌ {file} 缺失")
            issues.append(f"前端文件缺失: {file}")
    
    # 检查前端服务
    try:
        r = requests.get("http://localhost:5173", timeout=3)
        if r.status_code == 200:
            print("✅ 前端服务运行正常")
        else:
            print(f"⚠️  前端服务异常: HTTP {r.status_code}")
            issues.append(f"前端服务异常: {r.status_code}")
    except:
        print("❌ 前端服务未运行")
        issues.append("前端服务未启动")
    
    return issues


def test_complete_workflow():
    """测试完整工作流"""
    print_section("5. 完整工作流测试")
    
    issues = []
    
    # 测试五阶段流程
    print("\n测试五阶段AI流程...")
    try:
        r = requests.post(
            "http://localhost:8000/api/pipeline/run",
            json={
                "requirement": "用户登录功能需要支持手机号登录",
                "context": {"priority": "P0"}
            },
            timeout=30
        )
        
        if r.status_code == 200:
            result = r.json()
            trace_id = result.get('trace_id')
            print(f"✅ Pipeline执行成功 (Trace: {trace_id})")
            
            # 检查各阶段
            stages = result.get('stages', {})
            for stage_name in ['agent', 'strategy', 'orchestrator', 'healing', 'report']:
                stage_data = stages.get(stage_name, {})
                status = stage_data.get('status', 'unknown')
                if status == 'success':
                    print(f"   ✅ {stage_name}: 成功")
                elif status == 'skipped':
                    print(f"   ⏭️  {stage_name}: 跳过")
                else:
                    print(f"   ❌ {stage_name}: {status}")
                    issues.append(f"{stage_name}阶段失败: {status}")
        else:
            print(f"❌ Pipeline执行失败: HTTP {r.status_code}")
            print(f"   错误: {r.text}")
            issues.append(f"Pipeline执行失败: {r.status_code}")
    except Exception as e:
        print(f"❌ Pipeline执行异常: {str(e)}")
        issues.append(f"Pipeline执行异常: {str(e)}")
    
    # 测试传统流程
    print("\n测试传统流程...")
    try:
        # 测试项目创建
        r = requests.post(
            "http://localhost:8000/api/projects",
            json={
                "name": "测试项目",
                "description": "诊断测试"
            },
            timeout=5
        )
        if r.status_code == 200:
            print("✅ 项目创建成功")
        else:
            print(f"⚠️  项目创建失败: HTTP {r.status_code}")
            issues.append(f"项目创建失败: {r.status_code}")
    except Exception as e:
        print(f"❌ 项目创建异常: {str(e)}")
        issues.append(f"项目创建异常: {str(e)}")
    
    return issues


def check_dependencies():
    """检查依赖"""
    print_section("6. Python依赖检查")
    
    issues = []
    required_packages = [
        'fastapi',
        'uvicorn',
        'requests',
        'anthropic',
        'chromadb',
        'pydantic'
    ]
    
    import importlib
    for package in required_packages:
        try:
            importlib.import_module(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} 未安装")
            issues.append(f"缺少依赖: {package}")
    
    return issues


def main():
    """主函数"""
    print("\n" + "="*60)
    print("  🔍 AI测试平台 - 全面诊断")
    print("="*60)
    
    all_issues = []
    
    # 运行所有检查
    all_issues.extend(check_backend_modules())
    all_issues.extend(check_ai_models())
    all_issues.extend(check_database())
    all_issues.extend(check_frontend())
    all_issues.extend(test_complete_workflow())
    all_issues.extend(check_dependencies())
    
    # 总结
    print_section("📊 诊断总结")
    
    if not all_issues:
        print("\n🎉 恭喜!没有发现问题,系统运行正常!")
        print("\n✅ 可以开始使用了:")
        print("   http://localhost:5173/ai-test-console")
        return 0
    else:
        print(f"\n⚠️  发现 {len(all_issues)} 个问题:\n")
        for i, issue in enumerate(all_issues, 1):
            print(f"{i}. {issue}")
        
        print("\n💡 建议:")
        print("1. 查看上面的详细错误信息")
        print("2. 根据错误类型逐个修复")
        print("3. 修复后重新运行此脚本验证")
        
        return 1


if __name__ == "__main__":
    sys.exit(main())
