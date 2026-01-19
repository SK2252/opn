
import os
import psycopg2
from dotenv import load_dotenv

# Load env from parent dir
load_dotenv(os.path.join(os.path.dirname(__file__), "../.env"))

def patch_database():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("❌ DATABASE_URL not found")
        return

    print(f"🔌 Connecting to database...")
    try:
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        cur = conn.cursor()
        
        # Add endpoint
        print("🛠️  Adding 'endpoint' column...")
        try:
            cur.execute("ALTER TABLE agents ADD COLUMN IF NOT EXISTS endpoint VARCHAR(512);")
            print("   ✅ Done")
        except Exception as e:
            print(f"   ⚠️  {e}")

        # Add payload_mapping
        print("🛠️  Adding 'payload_mapping' column...")
        try:
            cur.execute("ALTER TABLE agents ADD COLUMN IF NOT EXISTS payload_mapping JSON;")
            print("   ✅ Done")
        except Exception as e:
            print(f"   ⚠️  {e}")

        # Add timeout
        print("🛠️  Adding 'timeout' column...")
        try:
            cur.execute("ALTER TABLE agents ADD COLUMN IF NOT EXISTS timeout INTEGER DEFAULT 300;")
            print("   ✅ Done")
        except Exception as e:
            print(f"   ⚠️  {e}")

        conn.close()
        print("\n✅ Database patch complete!")

    except Exception as e:
        print(f"❌ Failed to connect or patch: {e}")

if __name__ == "__main__":
    patch_database()
