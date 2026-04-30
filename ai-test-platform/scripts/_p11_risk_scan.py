"""Phase 11D: Scan 814 APIs for risk classification"""
import sys, json
sys.path.insert(0, ".")
from app.executor_v2.risk_classifier import scan_swagger_risks

swagger_path = r"scripts\swaggerApi (1).json"
result = scan_swagger_risks(swagger_path)

print(f"Total APIs: {result['total']}")
print(f"  Low:    {result['low']}")
print(f"  Medium: {result['medium']}")
print(f"  High:   {result['high']}")

print(f"\n=== HIGH risk APIs ({result['high']}) ===")
for api in result["high_apis"]:
    print(f"  {api['method']:6} {api['path']:<55} {api['summary']}")

print(f"\n=== LOW risk APIs (showing first 30 of {result['low']}) ===")
for api in result["low_apis"][:30]:
    print(f"  {api['method']:6} {api['path']:<55} {api['summary']}")

print(f"\n=== Recommended 20 regression APIs ===")
for i, api in enumerate(result["recommended_regression"], 1):
    print(f"  {i:2}. {api['method']:6} {api['path']:<55} {api['summary']}")

# Output to JSON for report
with open("output/risk_classification.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)
print(f"\nFull results saved to output/risk_classification.json")
