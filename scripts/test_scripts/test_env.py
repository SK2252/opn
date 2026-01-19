
import os
import sys
import logging
from dotenv import load_dotenv
import psycopg2
from qdrant_client import QdrantClient
from groq import Groq
import requests

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_environment():
    print("\n" + "="*60)
    print("🧪 TESTING OPN ENVIRONMENT CREDENTIALS")
    print("="*60 + "\n")

    # 1. Load Environment Variables
    env_path = os.path.join(os.path.dirname(__file__), "../.env")
    print(f"📂 Loading .env from: {os.path.abspath(env_path)}")
    if os.path.exists(env_path):
        load_dotenv(env_path)
        print("✅ .env file found and loaded.")
    else:
        print("❌ .env file NOT found!")
        return

    # 2. Test Grok/Groq API
    print("\n[1/3] 🤖 Testing AI Service (Groq)...")
    api_key = os.getenv("GROK_API_KEY") or os.getenv("GROQ_API_KEY")
    if not api_key:
        print("❌ No API Key found (GROK_API_KEY or GROQ_API_KEY)")
    else:
        try:
            client = Groq(api_key=api_key)
            # Simple completion test
            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": "user", "content": "Say 'Connection Successful'"}
                ],
                model=os.getenv("GROK_MODEL", "llama-3.3-70b-versatile"),
            )
            print(f"✅ Connection Successful! Response: {chat_completion.choices[0].message.content}")
        except Exception as e:
            print(f"❌ AI Service Connection Failed: {e}")

    # 3. Test Database (Supabase/PostgreSQL)
    print("\n[2/3] 🗄️  Testing Database (PostgreSQL)...")
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("❌ DATABASE_URL not found.")
    else:
        try:
            conn = psycopg2.connect(db_url)
            cur = conn.cursor()
            cur.execute("SELECT version();")
            version = cur.fetchone()
            print(f"✅ Database Connected! Version: {version[0]}")
            conn.close()
        except Exception as e:
            print(f"❌ Database Connection Failed: {e}")

    # 4. Test Qdrant (Vector DB)
    print("\n[3/3] 🧠 Testing Qdrant (Vector DB)...")
    qdrant_path = os.getenv("QDRANT_PATH", "./qdrant_data")
    print(f"   Path: {qdrant_path}")
    
    # Ensure directory exists if it's a local path
    if not os.path.exists(qdrant_path) and ":memory:" not in qdrant_path:
         print(f"   Creating Qdrant directory...")
         os.makedirs(qdrant_path, exist_ok=True)

    try:
        client = QdrantClient(path=qdrant_path)
        collections = client.get_collections()
        print(f"✅ Qdrant Initialized! Collections: {len(collections.collections)}")
    except Exception as e:
        print(f"❌ Qdrant Connection Failed: {e}")

    print("\n" + "="*60)

if __name__ == "__main__":
    test_environment()
