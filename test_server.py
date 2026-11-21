import json
import os
import sys
import urllib.request

PORT = int(os.environ.get("PORT", 8080))
BASE_URL = f"http://127.0.0.1:{PORT}"

def test_api():
    print(f"Testing CivicResolve Server endpoints on {BASE_URL}...")
    # 1. Health
    with urllib.request.urlopen(f"{BASE_URL}/api/health") as res:
        data = json.loads(res.read().decode())
        print("✓ Health check:", data["status"])
        assert data["status"] == "healthy"

    # 2. Config
    with urllib.request.urlopen(f"{BASE_URL}/api/config") as res:
        data = json.loads(res.read().decode())
        print("✓ Config check:", data["gemini_source"])

    # 3. Departments
    with urllib.request.urlopen(f"{BASE_URL}/api/departments") as res:
        data = json.loads(res.read().decode())
        print(f"✓ Departments check: {len(data['departments'])} departments loaded")
        assert len(data["departments"]) >= 6

    # 4. Analytics
    with urllib.request.urlopen(f"{BASE_URL}/api/analytics") as res:
        data = json.loads(res.read().decode())
        print(f"✓ Analytics check: {data['total_issues']} total issues, {data['critical_count']} critical")
        assert data["total_issues"] >= 5

    # 5. Issues list
    with urllib.request.urlopen(f"{BASE_URL}/api/issues") as res:
        data = json.loads(res.read().decode())
        print(f"✓ Issues check: {len(data['issues'])} issues in list")
        assert len(data["issues"]) >= 5

    # 6. AI Classify endpoint
    payload = json.dumps({
        "title": "Severe Water Pipe Rupture",
        "description": "Clean water is gushing across the road flooding hospital entrance",
        "location": "Near Central Hospital"
    }).encode("utf-8")
    req = urllib.request.Request(f"{BASE_URL}/api/ai/classify", data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as res:
        ai_data = json.loads(res.read().decode())
        print(f"✓ AI Classifier check: Category='{ai_data['category']}', Priority='{ai_data['priority']}', Dept='{ai_data['recommended_department']}'")
        assert ai_data["category"] == "Water Supply & Drainage"
        assert ai_data["priority"] in ["Critical", "High"]

    # 7. Static file serving (index.html)
    with urllib.request.urlopen(f"{BASE_URL}/") as res:
        html = res.read().decode()
        print(f"✓ Static frontend check: Loaded {len(html)} bytes of HTML")
        assert "CivicResolve" in html

    print("\n🎉 ALL TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_api()
