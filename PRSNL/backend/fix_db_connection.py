import asyncio
import asyncpg
import psycopg2

print("Testing database connections...\n")

# Test with psycopg2 (sync)
try:
    conn = psycopg2.connect(
        host='127.0.0.1',
        port=5432,
        database='prsnl',
        user='prsnl',
        password='prsnl123'
    )
    print("✅ psycopg2 connection successful!")
    
    # Create user if needed
    cur = conn.cursor()
    cur.execute("SELECT current_user")
    print(f"Connected as: {cur.fetchone()[0]}")
    cur.close()
    conn.close()
except Exception as e:
    print(f"❌ psycopg2 error: {e}")

# Test with asyncpg
async def test_asyncpg():
    # Try different connection strings
    connection_strings = [
        'postgresql://prsnl:prsnl123@127.0.0.1:5432/prsnl',
        'postgresql://prsnl:prsnl123@localhost:5432/prsnl',
        'postgresql://prsnl:prsnl123@host.docker.internal:5432/prsnl',
    ]
    
    for conn_str in connection_strings:
        try:
            print(f"\nTrying: {conn_str}")
            conn = await asyncpg.connect(conn_str)
            print(f"✅ Connected with: {conn_str}")
            await conn.close()
            return conn_str
        except Exception as e:
            print(f"❌ Failed: {e}")
    
    return None

# Run async test
result = asyncio.run(test_asyncpg())

if result:
    print(f"\n\nSUCCESS! Use this connection string:")
    print(f"DATABASE_URL={result}")
else:
    print("\n\nAll connection attempts failed. Checking Docker networking...")
    import subprocess
    result = subprocess.run(['docker', 'port', 'prsnl_db'], capture_output=True, text=True)
    print(f"Port mapping: {result.stdout}")