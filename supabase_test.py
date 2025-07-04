import os
from supabase import create_client

def test_supabase():
    print("=== Supabase Connection Test ===")
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    
    print(f"URL: {url}")
    print(f"Key: {key[:5]}...{key[-5:] if key else ''}")
    
    try:
        client = create_client(url, key)
        print("Client created successfully")
        
        # Test simple query
        res = client.table('sources').select("*").limit(1).execute()
        print(f"Query successful. Found {len(res.data)} records")
        return True
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    if not test_supabase():
        exit(1)
