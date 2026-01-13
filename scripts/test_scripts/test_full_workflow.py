"""
Full Workflow Test for Orchestrator Service
Tests end-to-end flow with actual Excel/DOCX files
"""
import httpx
import json
import time

def print_section(title):
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)

def test_full_workflow():
    """Test complete orchestration workflow with real files"""
    
    # Test query that should match CEP W6 files
    test_query = "Create document for CEP Wave 6"
    
    print_section("FULL WORKFLOW TEST")
    print(f"Query: {test_query}")
    print(f"Expected Files:")
    print(f"  - Excel: CEP W6 OPNNEG TEMPLATE.xlsx")
    print(f"  - Template: OpenNeg_CEP_Template.docx")
    
    # Step 1: Call Orchestrator
    print_section("STEP 1: Calling Orchestrator (/process)")
    
    try:
        with httpx.Client(timeout=300.0) as client:
            start_time = time.time()
            
            response = client.post(
                "http://localhost:8002/process",
                json={"query": test_query, "session_id": "full_workflow_test"}
            )
            
            elapsed = time.time() - start_time
            
            print(f"\nStatus Code: {response.status_code}")
            print(f"Response Time: {elapsed:.2f}s")
            
            if response.status_code == 200:
                result = response.json()
                print(f"\nResponse Type: {result.get('status', 'UNKNOWN')}")
                
                # Display routing decision
                if result.get('routing_decision'):
                    print_section("ROUTING DECISION")
                    routing = result['routing_decision']
                    print(f"Type: {routing.get('type')}")
                    print(f"Message: {routing.get('response', routing.get('message', 'N/A'))}")
                    
                    if routing.get('type') == 'routing':
                        routing_data = json.loads(routing.get('routing', '{}'))
                        print(f"\nAgent: {routing_data.get('agent')}")
                        print(f"Subagent: {routing_data.get('subagent')}")
                        print(f"Client: {routing_data.get('client_name')}")
                        print(f"Wave: {routing_data.get('wave_number')}")
                
                # Display file resolution
                if result.get('file_resolution'):
                    print_section("FILE RESOLUTION")
                    files = result['file_resolution']
                    for file_type, path in files.items():
                        if path:
                            print(f"✅ {file_type}: {path}")
                        else:
                            print(f"❌ {file_type}: NOT FOUND")
                
                # Display execution result
                if result.get('execution_result'):
                    print_section("EXECUTION RESULT")
                    exec_result = result['execution_result']
                    print(f"Status: {exec_result.get('status', 'UNKNOWN')}")
                    print(f"Message: {exec_result.get('message', 'N/A')}")
                    
                    if exec_result.get('output_files'):
                        print(f"\nOutput Files Generated:")
                        for file in exec_result['output_files']:
                            print(f"  - {file}")
                    
                    if exec_result.get('summary'):
                        print(f"\nSummary:")
                        summary = exec_result['summary']
                        print(f"  Groups: {summary.get('groups_generated', 0)}")
                        print(f"  Notices: {summary.get('notices_generated', 0)}")
                        print(f"  Merged: {summary.get('merged_files', 0)}")
                
                # Display errors
                if result.get('errors'):
                    print_section("ERRORS")
                    for error in result['errors']:
                        print(f"❌ {error}")
                
                # Overall status
                print_section("OVERALL STATUS")
                status = result.get('status')
                if status == 'SUCCESS':
                    print("✅ WORKFLOW COMPLETED SUCCESSFULLY")
                elif status == 'AWAITING_USER_INPUT':
                    print("⏸️  AWAITING USER INPUT (Clarification needed)")
                elif status == 'FAILED':
                    print("❌ WORKFLOW FAILED")
                else:
                    print(f"⚠️  UNKNOWN STATUS: {status}")
                
                # Save full response
                with open('full_workflow_result.json', 'w') as f:
                    json.dump(result, f, indent=2)
                print(f"\n📄 Full response saved to: full_workflow_result.json")
                
            else:
                print(f"\n❌ ERROR: HTTP {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"Details: {json.dumps(error_detail, indent=2)}")
                except:
                    print(f"Response: {response.text}")
    
    except httpx.TimeoutException:
        print("\n❌ ERROR: Request timed out (>300s)")
    except httpx.ConnectError as e:
        print(f"\n❌ ERROR: Cannot connect to Orchestrator")
        print(f"Details: {e}")
    except Exception as e:
        print(f"\n❌ ERROR: {type(e).__name__}: {e}")

if __name__ == "__main__":
    test_full_workflow()
