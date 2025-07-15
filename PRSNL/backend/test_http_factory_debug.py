#!/usr/bin/env python3
"""Debug script to reproduce the HTTP client factory error"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.http_client_factory import http_client_factory, ClientType

async def test_http_client_creation():
    """Test HTTP client factory creation"""
    print("Testing HTTP Client Factory...")
    
    try:
        # Test health check
        health = await http_client_factory.health_check()
        print(f"Health check: {health}")
        
        # Test client creation for each type
        for client_type in [ClientType.GENERAL, ClientType.GITHUB, ClientType.AZURE_OPENAI]:
            print(f"\nTesting {client_type.value} client...")
            try:
                client = await http_client_factory.get_client(client_type)
                print(f"✓ Successfully created {client_type.value} client")
                print(f"  Base URL: {client.base_url}")
                print(f"  Is closed: {client.is_closed}")
                
                # Test with client session
                async with http_client_factory.client_session(client_type) as session_client:
                    print(f"  Session client base_url: {session_client.base_url}")
                    
            except Exception as e:
                print(f"✗ Error creating {client_type.value} client: {e}")
                import traceback
                traceback.print_exc()
                
    except Exception as e:
        print(f"Error in health check: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        await http_client_factory.close_all_clients()

if __name__ == "__main__":
    asyncio.run(test_http_client_creation())