import urllib.request
import json

BASE = "http://localhost:8000"

def test(label, url):
    print(f"\n{'='*60}")
    print(f"TEST: {label}")
    print(f"URL:  {url}")
    try:
        with urllib.request.urlopen(url) as resp:
            data = json.loads(resp.read())
            print(f"STATUS: OK")
            return data
    except Exception as e:
        print(f"FAILED: {e}")
        return None

def post_test(label, url, body):
    print(f"\n{'='*60}")
    print(f"TEST: {label}")
    print(f"URL:  {url}")
    try:
        req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read())
            print(f"STATUS: OK")
            return data
    except Exception as e:
        print(f"FAILED: {e}")
        return None

# 1. GET /regions
data = test("GET /regions", f"{BASE}/regions")
if data:
    print(f"  Regions count: {len(data)}")
    for r in data:
        print(f"    id={r['id']} name={r['name']}")

# 2. GET /regions/2/foods (Tamil Nadu)
data = test("GET /regions/2/foods (Tamil Nadu)", f"{BASE}/regions/2/foods")
if data:
    print(f"  Region: {data['region']['name']}")
    print(f"  Food count: {data['count']}")
    for f in data['foods'][:3]:
        print(f"    - {f['food_name']} ({f['Calories_kcal']} kcal)")

# 3. GET /foods?query=idli
data = test("GET /foods?query=idli", f"{BASE}/foods?query=idli")
if data:
    print(f"  Results: {len(data)}")
    for d in data[:3]:
        print(f"    {d['food_name']} | region={d.get('region')} | cuisine={d.get('cuisine_type')} | unit={d.get('serving_unit')} | wt={d.get('serving_weight_g')}")

# 4. POST /food-logs (quantity based)
data = post_test("POST /food-logs (quantity)", f"{BASE}/food-logs", {"user_id": 1, "food_id": 1, "quantity": 2})
if data:
    print(f"  Log: {json.dumps(data, indent=2)[:200]}")

# 5. GET /health
data = test("GET /health", f"{BASE}/health")
if data:
    print(f"  {data}")

# 6. ML feature vector check
print(f"\n{'='*60}")
print("TEST: ML predictor feature vector dimensions")
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
try:
    from ml.predictor import extract_features
    import numpy as np
    class FakeImp:
        deficits = {"Calories_kcal": 300, "Protein_g": 20, "user_region": "Tamil Nadu"}
        rank = 1
        rule_score = 50
    class FakeFood:
        Calories_kcal = 200
        Protein_g = 10
        Fats_g = 5
        Carbohydrates_g = 30
        region_rel = None
        region = "Tamil Nadu"
    feats = extract_features(FakeImp(), FakeFood())
    print(f"STATUS: OK")
    print(f"  Feature vector length: {len(feats)} (expected 12)")
    print(f"  Features: {feats}")
except Exception as e:
    print(f"FAILED: {e}")

print(f"\n{'='*60}")
print("ALL CHECKS COMPLETE")
