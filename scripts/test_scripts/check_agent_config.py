"""
Check Agent Payload Mapping in Database
"""

import os
import psycopg2
import json
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "../.env"))

def check_agent():
    db_url = os.getenv("DATABASE_URL")
    print(f"🔌 Connecting to database...")
    
    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        
        agent_name = "Open Negotiation AI Agent"
        
        cur.execute("""
            SELECT id, name, endpoint, payload_mapping, timeout 
            FROM agents 
            WHERE name = %s
        """, (agent_name,))
        
        result = cur.fetchone()
        
        if result:
            agent_id, name, endpoint, payload_mapping, timeout = result
            print(f"\n✅ Agent Found:")
            print(f"   ID: {agent_id}")
            print(f"   Name: {name}")
            print(f"   Endpoint: {endpoint}")
            print(f"   Timeout: {timeout}")
            print(f"\n📦 Payload Mapping:")
            if payload_mapping:
                print(json.dumps(payload_mapping, indent=2))
            else:
                print("   ❌ NULL")
        else:
            print(f"\n❌ Agent '{agent_name}' not found")
            
        conn.close()

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_agent()
