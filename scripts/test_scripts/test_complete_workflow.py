"""
Complete Workflow Test - With Confirmation
Tests the full end-to-end workflow including confirmation step
"""
import httpx
import json
import time

def call_orchestrator(query, session_id):
    """Call Repo Unified Process"""
    with httpx.Client(timeout=300.0) as client:
        response = client.post(
            "http://localhost:8001/process/process",
            json={"query": query, "session_id": session_id}
        )
        return response.status_code, response.json()

def print_step(step_num, title, result):
    """Print step results"""
    print(f"\n{'='*80}")
    print(f"STEP {step_num}: {title}")
    print(f"{'='*80}")
    print(f"Status: {result.get('status')}")
    if result.get('message'):
        print(f"Message: {result['message']}")

def main():
    print("="*80)
    print("COMPLETE WORKFLOW TEST - CEP WAVE 6")
    print("="*80)
    
    session_id = f"complete_workflow_{int(time.time())}"
    
    # Step 1: Initial query
    print("\n🔹 Sending initial query...")
    status, result1 = call_orchestrator(
        "I need to create an open negotiation document for client CEP wave number 6",
        session_id
    )
    print_step(1, "Initial Query", result1)
    
    # Step 2: Confirm if needed
    if result1.get('status') == 'AWAITING_USER_INPUT':
        response_type = result1.get('routing_decision', {}).get('type')
        
        if response_type == 'confirmation':
            print("\n🔹 Sending confirmation...")
            time.sleep(1)  # Brief pause
            
            status, result2 = call_orchestrator(
                "Yes, please proceed",
                session_id
            )
            print_step(2, "Confirmation", result2)
            
            # Use result2 for final analysis
            final_result = result2
        else:
            final_result = result1
    else:
        final_result = result1
    
    # Display final results
    print(f"\n{'='*80}")
    print("FINAL RESULTS")
    print(f"{'='*80}")
    
    # Routing
    if final_result.get('routing_decision'):
        routing = final_result['routing_decision']
        if routing.get('type') == 'routing':
            routing_data = json.loads(routing.get('routing', '{}'))
            print(f"\n✅ ROUTING DECISION:")
            print(f"   Agent: {routing_data.get('agent')}")
            print(f"   Subagent: {routing_data.get('subagent')}")
            print(f"   Client: {routing_data.get('client_name')}")
            print(f"   Wave: {routing_data.get('wave_number')}")
    
    # File Resolution
    if final_result.get('file_resolution'):
        print(f"\n✅ FILE RESOLUTION:")
        for file_type, path in final_result['file_resolution'].items():
            if path:
                print(f"   ✓ {file_type}: {path}")
            else:
                print(f"   ✗ {file_type}: NOT FOUND")
    
    # Execution
    if final_result.get('execution_result'):
        exec_result = final_result['execution_result']
        print(f"\n✅ EXECUTION RESULT:")
        print(f"   Status: {exec_result.get('status')}")
        
        if exec_result.get('output_files'):
            print(f"\n   Generated Files:")
            for file in exec_result['output_files']:
                print(f"      📄 {file}")
        
        if exec_result.get('summary'):
            summary = exec_result['summary']
            print(f"\n   Summary:")
            print(f"      Groups Generated: {summary.get('groups_generated', 0)}")
            print(f"      Notices Generated: {summary.get('notices_generated', 0)}")
            print(f"      Merged Files: {summary.get('merged_files', 0)}")
    
    # Errors
    if final_result.get('errors'):
        print(f"\n❌ ERRORS:")
        for error in final_result['errors']:
            print(f"   - {error}")
    
    # Overall Status
    print(f"\n{'='*80}")
    status = final_result.get('status')
    if status == 'SUCCESS':
        print("🎉 WORKFLOW COMPLETED SUCCESSFULLY!")
        print("   All files resolved and document generated")
    elif status == 'AWAITING_USER_INPUT':
        print("⏸️  WORKFLOW PAUSED - Awaiting user input")
    elif status == 'FAILED':
        print("❌ WORKFLOW FAILED")
    else:
        print(f"⚠️  STATUS: {status}")
    print("="*80)
    
    # Save results
    with open('complete_workflow_result.json', 'w') as f:
        json.dump(final_result, f, indent=2)
    print(f"\n📄 Results saved to: complete_workflow_result.json")

if __name__ == "__main__":
    main()
