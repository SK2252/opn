"""
Direct Workflow Test - Explicit Query
Tests with a complete query that should trigger immediate routing
"""
import httpx
import json
import time

def test_explicit_query():
    """Test with explicit, complete query"""
    
    # Explicit query with all information
    query = "I need to create an open negotiation document for client CEP wave number 6"
    
    print("="*80)
    print("EXPLICIT QUERY TEST")
    print("="*80)
    print(f"Query: {query}")
    print(f"\nExpected Behavior:")
    print("  1. Repi routes to 'Open Negotiation Agent'")
    print("  2. File resolver finds:")
    print("     - Excel: CEP W6 OPNNEG TEMPLATE.xlsx")
    print("     - Template: OpenNeg_CEP_Template.docx")
    print("  3. OPN-Agent processes the files")
    print("  4. Returns generated documents")
    
    try:
        with httpx.Client(timeout=300.0) as client:
            print(f"\n{'='*80}")
            print("CALLING ORCHESTRATOR")
            print("="*80)
            
            start_time = time.time()
            response = client.post(
                "http://localhost:8002/process",
                json={
                    "query": query,
                    "session_id": f"explicit_test_{int(time.time())}"
                }
            )
            elapsed = time.time() - start_time
            
            print(f"Status Code: {response.status_code}")
            print(f"Response Time: {elapsed:.2f}s")
            
            if response.status_code == 200:
                result = response.json()
                
                # Save result
                with open('explicit_test_result.json', 'w') as f:
                    json.dump(result, f, indent=2)
                
                print(f"\n{'='*80}")
                print(f"RESULT: {result.get('status')}")
                print("="*80)
                
                # Routing Decision
                if result.get('routing_decision'):
                    routing = result['routing_decision']
                    print(f"\n📍 ROUTING:")
                    print(f"   Type: {routing.get('type')}")
                    
                    if routing.get('type') == 'routing':
                        routing_data = json.loads(routing.get('routing', '{}'))
                        print(f"   ✅ Agent: {routing_data.get('agent')}")
                        print(f"   ✅ Subagent: {routing_data.get('subagent')}")
                        print(f"   ✅ Client: {routing_data.get('client_name')}")
                        print(f"   ✅ Wave: {routing_data.get('wave_number')}")
                    elif routing.get('type') in ['clarification', 'confirmation']:
                        print(f"   ⚠️  {routing.get('response')}")
                
                # File Resolution
                if result.get('file_resolution'):
                    print(f"\n📁 FILE RESOLUTION:")
                    files = result['file_resolution']
                    for file_type, path in files.items():
                        if path:
                            print(f"   ✅ {file_type}: {path}")
                        else:
                            print(f"   ❌ {file_type}: NOT FOUND")
                
                # Execution
                if result.get('execution_result'):
                    exec_result = result['execution_result']
                    print(f"\n🚀 EXECUTION:")
                    print(f"   Status: {exec_result.get('status')}")
                    print(f"   Message: {exec_result.get('message', 'N/A')}")
                    
                    if exec_result.get('output_files'):
                        print(f"\n   📄 Output Files:")
                        for file in exec_result['output_files']:
                            print(f"      - {file}")
                    
                    if exec_result.get('summary'):
                        summary = exec_result['summary']
                        print(f"\n   📊 Summary:")
                        print(f"      Groups: {summary.get('groups_generated', 0)}")
                        print(f"      Notices: {summary.get('notices_generated', 0)}")
                        print(f"      Merged: {summary.get('merged_files', 0)}")
                
                # Errors
                if result.get('errors'):
                    print(f"\n❌ ERRORS:")
                    for error in result['errors']:
                        print(f"   - {error}")
                
                # Final Status
                print(f"\n{'='*80}")
                status = result.get('status')
                if status == 'SUCCESS':
                    print("✅ SUCCESS - Full workflow completed!")
                elif status == 'AWAITING_USER_INPUT':
                    print("⏸️  AWAITING INPUT - Clarification needed")
                    print(f"   Message: {result.get('message')}")
                elif status == 'FAILED':
                    print("❌ FAILED - Workflow encountered errors")
                else:
                    print(f"⚠️  UNKNOWN STATUS: {status}")
                print("="*80)
                
                print(f"\n📄 Full result saved to: explicit_test_result.json")
                
            else:
                print(f"\n❌ HTTP ERROR: {response.status_code}")
                try:
                    print(json.dumps(response.json(), indent=2))
                except:
                    print(response.text)
    
    except Exception as e:
        print(f"\n❌ ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_explicit_query()
