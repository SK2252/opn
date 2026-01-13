import requests
import json
import time

BASE_URL = "http://localhost:8002"

def run_test():
    print("🚀 Starting End-to-End Verification...")
    
    # Session ID for continuity
    session_id = f"test_sess_{int(time.time())}"
    
    # Step 1: Initial Request
    print("\n[1] Sending initial request...")
    payload1 = {
        "query": "I need to create an open negotiation document for client CEP wave number 6",
        "session_id": session_id
    }
    
    try:
        r1 = requests.post(f"{BASE_URL}/process", json=payload1)
        r1.raise_for_status()
        res1 = r1.json()
        print(f"Status: {res1.get('status')}")
        print(f"Message: {res1.get('message')}")
        
        if res1.get("status") != "AWAITING_USER_INPUT":
            print("❌ Failed: Expected AWAITING_USER_INPUT")
            return
            
    except Exception as e:
        print(f"❌ Failed Step 1: {e}")
        return

    # Step 2: Confirmation
    print("\n[2] Sending confirmation 'yes'...")
    payload2 = {
        "query": "yes",
        "session_id": session_id
    }
    
    try:
        r2 = requests.post(f"{BASE_URL}/process", json=payload2)
        r2.raise_for_status()
        res2 = r2.json()
        
        print(f"Status: {res2.get('status')}")
        
        # Check for execution result
        exec_result = res2.get("execution_result", {})
        if not exec_result:
            print("❌ Failed: No execution_result found")
            print(json.dumps(res2, indent=2))
            return

        exec_status = exec_result.get("status")
        errors = exec_result.get("errors", [])
        
        print(f"Execution Status: {exec_status}")
        
        if errors:
            print(f"❌ Execution Errors: {errors}")
            # Check specifically for the "int64" error
            if any("int64" in str(e) for e in errors):
                print("💥 CRITICAL: Int64 error still present!")
            else:
                print("⚠️ Other errors present (might be file missing etc, which is okay for this test)")
        else:
            print("✅ Success: No errors in execution!")
            
        print("\nFull Response Snippet:")
        print(json.dumps(exec_result, indent=2)[:500] + "...")

    except Exception as e:
        print(f"❌ Failed Step 2: {e}")
        if 'r2' in locals():
            print(f"Response: {r2.text}")

if __name__ == "__main__":
    run_test()
