"""
Multi-Turn Conversation Test for Orchestrator Service
Simulates a complete conversation flow with clarifications
"""
import httpx
import json
import time

def call_orchestrator(query, session_id="multi_turn_test"):
    """Call orchestrator and return response"""
    with httpx.Client(timeout=300.0) as client:
        response = client.post(
            "http://localhost:8002/process",
            json={"query": query, "session_id": session_id}
        )
        return response.status_code, response.json()

def print_response(turn, query, status_code, result):
    """Print formatted response"""
    print(f"\n{'='*80}")
    print(f"TURN {turn}: {query}")
    print(f"{'='*80}")
    print(f"Status Code: {status_code}")
    print(f"Response Status: {result.get('status')}")
    
    if result.get('message'):
        print(f"\nAssistant: {result['message']}")
    
    if result.get('routing_decision'):
        routing = result['routing_decision']
        if routing.get('type') == 'routing':
            routing_data = json.loads(routing.get('routing', '{}'))
            print(f"\n✅ ROUTING DECISION:")
            print(f"   Agent: {routing_data.get('agent')}")
            print(f"   Subagent: {routing_data.get('subagent')}")
            print(f"   Client: {routing_data.get('client_name')}")
            print(f"   Wave: {routing_data.get('wave_number')}")
    
    if result.get('file_resolution'):
        print(f"\n📁 FILE RESOLUTION:")
        for file_type, path in result['file_resolution'].items():
            status = "✅" if path else "❌"
            print(f"   {status} {file_type}: {path or 'NOT FOUND'}")
    
    if result.get('execution_result'):
        exec_result = result['execution_result']
        print(f"\n🚀 EXECUTION RESULT:")
        print(f"   Status: {exec_result.get('status')}")
        if exec_result.get('output_files'):
            print(f"   Output Files:")
            for file in exec_result['output_files']:
                print(f"     - {file}")
    
    if result.get('errors'):
        print(f"\n❌ ERRORS:")
        for error in result['errors']:
            print(f"   - {error}")

def main():
    print("="*80)
    print("MULTI-TURN CONVERSATION TEST")
    print("="*80)
    
    session_id = f"multi_turn_{int(time.time())}"
    
    # Turn 1: Initial query
    status, result = call_orchestrator(
        "Create document for CEP Wave 6",
        session_id
    )
    print_response(1, "Create document for CEP Wave 6", status, result)
    
    # Check if we need to continue
    if result.get('status') == 'AWAITING_USER_INPUT':
        # Turn 2: Provide client name
        status, result = call_orchestrator(
            "CEP",
            session_id
        )
        print_response(2, "CEP", status, result)
    
    # Check if we need confirmation
    if result.get('status') == 'AWAITING_USER_INPUT':
        response_text = result.get('message', '').lower()
        if 'confirm' in response_text or 'proceed' in response_text:
            # Turn 3: Confirm
            status, result = call_orchestrator(
                "Yes, proceed",
                session_id
            )
            print_response(3, "Yes, proceed", status, result)
    
    # Final status
    print(f"\n{'='*80}")
    print("FINAL STATUS")
    print(f"{'='*80}")
    final_status = result.get('status')
    if final_status == 'SUCCESS':
        print("✅ WORKFLOW COMPLETED SUCCESSFULLY!")
    elif final_status == 'AWAITING_USER_INPUT':
        print("⏸️  Still awaiting user input")
        print(f"Message: {result.get('message')}")
    elif final_status == 'FAILED':
        print("❌ WORKFLOW FAILED")
        if result.get('errors'):
            for error in result['errors']:
                print(f"   - {error}")
    
    # Save final result
    with open('multi_turn_result.json', 'w') as f:
        json.dump(result, f, indent=2)
    print(f"\n📄 Final response saved to: multi_turn_result.json")

if __name__ == "__main__":
    main()
