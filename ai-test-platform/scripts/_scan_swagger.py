"""扫描 swagger 文件，找到用户上传的 814 API 的文件"""
import json, os, glob

dirs = [
    r"G:\AI项目\ai测试\ai-test-platform\scripts",
    r"G:\AI项目\ai测试\ai-test-platform\uploads\swagger",
]

for d in dirs:
    for f in glob.glob(os.path.join(d, "*.json")):
        try:
            with open(f, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            paths = data.get("paths", {})
            api_count = sum(len(m) for m in paths.values())
            info = data.get("info", {})
            host = data.get("host", "")
            base = data.get("basePath", "")
            servers = data.get("servers", [])
            server_url = servers[0].get("url", "") if servers else ""
            title = info.get("title", "")
            print(f"{os.path.basename(f)}: {api_count} APIs | host={host}{base} server={server_url} | {title}")
            # first 3 paths
            for path, methods in list(paths.items())[:3]:
                for method in methods:
                    summary = methods[method].get("summary", "")[:40] if isinstance(methods[method], dict) else ""
                    print(f"  {method.upper()} {path}  {summary}")
        except Exception as e:
            print(f"{os.path.basename(f)}: ERROR {e}")
    print()
