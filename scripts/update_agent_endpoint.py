
import os
import psycopg2
import json
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "../.env"))

def update_agent():
    db_url = os.getenv("DATABASE_URL")
    print(f"🔌 Connecting to database...")
    
    try:
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        cur = conn.cursor()
        
        agent_name = "Open Negotiation AI Agent"
        endpoint = "http://localhost:8000/run-advanced-workflow" # Correct endpoint
        
        # Mapping from register_opn_agent.py
        payload_mapping = {
            "request_id": "orch_{client_name}_{wave_number}",
            "excel_path": "resolved_excel_path",
            "template_docx": "resolved_template_path",
            "output_folder": "AI_open_negotiation/Data/Output/{client_name}_W{wave_number}",
            "use_ai": True,
            "user_instructions": "Auto-triggered from Repo: Client {client_name}, Wave {wave_number}"
        }
        
        print(f"🛠️  Updating agent '{agent_name}'...")
        
        # Check if agent exists
        cur.execute("SELECT id FROM agents WHERE name = %s", (agent_name,))
        result = cur.fetchone()
        
        if result:
            print(f"   found agent id: {result[0]}")
            
            sql = """
                UPDATE agents 
                SET endpoint = %s, 
                    payload_mapping = %s,
                    timeout = 300
                WHERE name = %s
            """
            cur.execute(sql, (endpoint, json.dumps(payload_mapping), agent_name))
            print("   ✅ Updated endpoint and payload_mapping")
        else:
            print("   ❌ Agent not found! You may need to run register_opn_agent.py")
            
        conn.close()

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    update_agent()
