"""
Register OPN-Agent with Repi Router

This script registers the Open Negotiation Agent with the Repi routing system
so it can be discovered and routed to by user queries.
"""

import requests
import json

# Repi router endpoint
REPI_URL = "http://localhost:8001"

def register_agent():
    """Register the Open Negotiation Agent with Repi."""
    
    agent_data = {
        "name": "Open Negotiation Agent",
        "description": "Processes Open Negotiation documents including Excel grouping, notice generation, and file organization for healthcare providers. Generates group files, notices, and merged outputs from Excel templates.",
        "capabilities": [
            "document_generation",
            "excel_processing",
            "pdf_creation",
            "word_processing",
            "file_organization",
            "template_processing"
        ]
    }
    
    print("=" * 60)
    print("🔗 Registering OPN-Agent with Repi Router")
    print("=" * 60)
    print(f"\n📍 Endpoint: {REPI_URL}/ingest/agent")
    print(f"📝 Agent: {agent_data['name']}")
    print(f"📋 Capabilities: {', '.join(agent_data['capabilities'])}")
    
    try:
        response = requests.post(
            f"{REPI_URL}/ingest/agent",
            json=agent_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ SUCCESS: Agent registered!")
            print(f"   Agent ID: {result.get('agent_id')}")
            print(f"   Vector ID: {result.get('vector_id')}")
            return True
        else:
            print(f"\n❌ ERROR: Registration failed!")
            print(f"   Status Code: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"\n❌ ERROR: Cannot connect to Repi at {REPI_URL}")
        print("   Make sure Repi is running on port 8001")
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        return False

def test_routing():
    """Test if routing works for a sample query."""
    
    print("\n" + "=" * 60)
    print("🧪 Testing Routing")
    print("=" * 60)
    
    query = "Create document for CEP Wave 6"
    print(f"\n📝 Query: '{query}'")
    
    try:
        response = requests.post(
            f"{REPI_URL}/chat/chat",
            params={"query": query},
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ Routing Response:")
            print(json.dumps(result, indent=2))
            
            if result.get("type") == "routing":
                routing = result.get("routing", {})
                if isinstance(routing, str):
                    routing = json.loads(routing)
                
                print(f"\n🎯 Routed to: {routing.get('agent')}")
                print(f"   Client: {routing.get('client_name')}")
                print(f"   Wave: {routing.get('wave_number')}")
                return True
            else:
                print(f"\n⚠️  Got {result.get('type')} response instead of routing")
                return False
        else:
            print(f"\n❌ ERROR: Status {response.status_code}")
            print(response.text)
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        return False

if __name__ == "__main__":
    print("\n🚀 OPN-Agent Registration Script\n")
    
    # Step 1: Register agent
    if register_agent():
        # Step 2: Test routing
        print("\n⏳ Waiting 2 seconds for vector indexing...")
        import time
        time.sleep(2)
        
        if test_routing():
            print("\n" + "=" * 60)
            print("✅ ALL TESTS PASSED!")
            print("=" * 60)
            print("\n📌 Next Steps:")
            print("   1. Test calling OPN-Agent manually with the routing params")
            print("   2. Verify documents are generated correctly")
            print("\n💡 Example OPN-Agent call:")
            print('   curl -X POST http://localhost:8000/run-advanced-workflow \\')
            print('     -H "Content-Type: application/json" \\')
            print('     -d \'{"request_id": "test_001",')
            print('          "excel_path": "AI_open_negotiation/Data/Input/CEP W6 OPNNEG TEMPLATE.xlsx",')
            print('          "template_docx": "AI_open_negotiation/Data/Input/OpenNeg_CEP_Template.docx",')
            print('          "output_folder": "AI_open_negotiation/Data/Output/CEP W6"}\'')
        else:
            print("\n❌ Routing test failed")
    else:
        print("\n❌ Registration failed - cannot proceed with tests")
