#!/usr/bin/env python3
import psycopg2
import sys

try:
    # Connect to the database
    conn = psycopg2.connect(
        host="localhost",
        database="prsnl",
        user="pronav",
        password="",
        port=5432
    )
    
    cur = conn.cursor()
    
    # Get all tables
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        ORDER BY table_name;
    """)
    
    tables = cur.fetchall()
    
    print("=== Database Tables ===")
    if not tables:
        print("No tables found in the database.")
    else:
        for table in tables:
            table_name = table[0]
            print(f"\nTable: {table_name}")
            
            # Get row count for each table
            try:
                cur.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cur.fetchone()[0]
                print(f"  Row count: {count}")
            except Exception as e:
                print(f"  Could not count rows: {e}")
    
    # Check if pgvector extension is installed
    cur.execute("SELECT * FROM pg_extension WHERE extname = 'vector';")
    vector_ext = cur.fetchone()
    
    print("\n=== pgvector Extension ===")
    if vector_ext:
        print(f"pgvector is installed (version: {vector_ext[5]})")
    else:
        print("pgvector is NOT installed")
    
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"Error connecting to database: {e}")
    sys.exit(1)