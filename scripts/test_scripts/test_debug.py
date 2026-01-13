import httpx
import json

payload = {"query": "Create document for CEP Wave 6", "session_id": "test_1"}

# Test Repi
print("--- Testing Repi (8001) ---")
try:
    with httpx.Client() as client:
        r = client.post("http://localhost:8001/chat/chat", params=payload, timeout=30.0)
        print(f"Status: {r.status_code}")
        print(f"Response: {r.text[:500]}")
except Exception as e:
    print(f"Repi Error: {e}")

# Test Orchestrator
print("\n--- Testing Orchestrator (8002) ---")
try:
    with httpx.Client() as client:
        r = client.post("http://localhost:8002/process", json=payload, timeout=300.0)
        print(f"Status: {r.status_code}")
        try:
            print(f"Response: {json.dumps(r.json(), indent=2)}")
        except:
            print(f"Response: {r.text}")
except Exception as e:
    print(f"Orchestrator Error: {e}")
