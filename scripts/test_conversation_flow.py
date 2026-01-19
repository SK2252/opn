"""
Test multi-turn conversation flow with Repo
"""

import requests
import json

REPO_URL = "http://localhost:8001"
SESSION_ID = "test_session_123"

def send_query(query, session_id=SESSION_ID):
    """Send a query to Repo and get response."""
    response = requests.post(
        f"{REPO_URL}/chat/chat",
        params={"query": query, "session_id": session_id}
    )
    return response.json()

print("=" * 70)
print("🔄 Testing Multi-Turn Conversation Flow")
print("=" * 70)

# Turn 1: Initial query
print("\n📝 Turn 1: User query")
query1 = "I want to create open negotiation documents"
print(f"   Query: '{query1}'")
response1 = send_query(query1)
print(f"   Response Type: {response1.get('type')}")
print(f"   Response: {response1.get('response', '')[:150]}...")

# Turn 2: Provide client name
if response1.get('type') == 'clarification':
    print("\n📝 Turn 2: Answering clarification")
    query2 = "CEP"
    print(f"   Query: '{query2}'")
    response2 = send_query(query2, SESSION_ID)
    print(f"   Response Type: {response2.get('type')}")
    print(f"   Response: {response2.get('response', '')[:150]}...")
    
    # Turn 3: Provide wave number
    if response2.get('type') == 'clarification':
        print("\n📝 Turn 3: Answering second clarification")
        query3 = "Wave 6"
        print(f"   Query: '{query3}'")
        response3 = send_query(query3, SESSION_ID)
        print(f"   Response Type: {response3.get('type')}")
        
        if response3.get('type') == 'confirmation':
            print(f"   ✅ Got confirmation request!")
            print(f"   Agent: {response3.get('agent_name')}")
            print(f"   Subagent: {response3.get('subagent_name')}")
            
            # Turn 4: Confirm routing
            print("\n📝 Turn 4: Confirming routing")
            query4 = "yes"
            print(f"   Query: '{query4}'")
            response4 = send_query(query4, SESSION_ID)
            print(f"   Response Type: {response4.get('type')}")
            
            if response4.get('type') == 'routing':
                print("\n" + "=" * 70)
                print("✅ SUCCESS! Got routing response!")
                print("=" * 70)
                routing = response4.get('routing', {})
                if isinstance(routing, str):
                    routing = json.loads(routing)
                print(f"\n🎯 Routing Decision:")
                print(json.dumps(routing, indent=2))
                print(f"\n📌 Next Step: Call OPN-Agent with these parameters")
            else:
                print(f"\n⚠️  Expected routing but got: {response4.get('type')}")
        else:
            print(f"\n⚠️  Expected confirmation but got: {response3.get('type')}")
            print(f"   Response: {response3.get('response')}")
