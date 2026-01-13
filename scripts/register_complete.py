"""
Complete OPN-Agent Registration with Repi Router
Registers both the main agent and the Document Creation subagent
"""
import requests
import json

REPI_URL = "http://localhost:8001"

def register_main_agent():
    """Register the main Open Negotiation AI Agent."""
    agent_data = {
        "name": "Open Negotiation AI Agent",
        "description": "AI-powered Open Negotiation document processing system. Master orchestrator that coordinates validation, document generation, and file merging for healthcare providers.",
        "capabilities": [
            "document_orchestration",
            "excel_processing", 
            "word_processing",
            "pdf_creation",
            "file_organization",
            "open_negotiation",
            "multi_agent_coordination"
        ]
    }
    
    print("=" * 60)
    print("Step 1: Registering Main Agent")
    print("=" * 60)
    print(f"Agent: {agent_data['name']}")
    
    try:
        response = requests.post(
            f"{REPI_URL}/ingest/agent",
            json=agent_data
        )
        
        if response.status_code == 200:
            result = response.json()
            agent_id = result.get('agent_id')
            print(f"✅ Main agent registered! ID: {agent_id}")
            return agent_id
        else:
            print(f"❌ Failed: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def register_subagent(agent_id):
    """Register the Document Creation subagent."""
    subagent_data = {
        "agent_id": agent_id,
        "name": "Document Creation Agent",
        "description": "Creates Open Negotiation documents including group files, notices, and merged outputs. Processes Excel templates and Word documents for healthcare provider negotiations.",
        "capabilities": [
            "document_creation",
            "document_generation",
            "group_generation",
            "notice_generation",
            "file_merging",
            "template_processing"
        ]
    }
    
    print("\n" + "=" * 60)
    print("Step 2: Registering Document Creation Subagent")
    print("=" * 60)
    print(f"Subagent: {subagent_data['name']}")
    print(f"Parent Agent ID: {agent_id}")
    
    try:
        response = requests.post(
            f"{REPI_URL}/ingest/subagent",
            json=subagent_data
        )
        
        if response.status_code == 200:
            print(f"✅ Subagent registered!")
            return True
        else:
            print(f"❌ Failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_routing():
    """Test routing to the newly registered agent."""
    print("\n" + "=" * 60)
    print("Step 3: Testing Routing")
    print("=" * 60)
    
    query = "Create open negotiation document for client CEP wave 6"
    print(f"Query: {query}")
    
    try:
        response = requests.post(
            f"{REPI_URL}/chat/chat",
            params={"query": query}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ Response Type: {result.get('type')}")
            print(f"Message: {result.get('response', result.get('message', 'N/A'))[:200]}")
            return True
        else:
            print(f"❌ Failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("OPN-AGENT COMPLETE REGISTRATION")
    print("=" * 60)
    
    # Step 1: Register main agent
    agent_id = register_main_agent()
    
    if agent_id:
        # Step 2: Register subagent  
        if register_subagent(agent_id):
            import time
            print("\n⏳ Waiting for indexing...")
            time.sleep(3)
            
            # Step 3: Test
            test_routing()
            
            print("\n" + "=" * 60)
            print("REGISTRATION COMPLETE")
            print("=" * 60)
            print(f"\nAgent ID: {agent_id}")
            print("Subagent: Document Creation Agent")
            print("\nThe orchestrator can now route to:")
            print("  - Open Negotiation AI Agent")
            print("  - Document Creation Agent (subagent)")
        else:
            print("\n❌ Subagent registration failed")
    else:
        print("\n❌ Main agent registration failed")
