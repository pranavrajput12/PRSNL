#!/usr/bin/env python3
"""Test how httpx handles base_url=None"""
import httpx

# Test what happens with None base_url
print("Testing httpx.AsyncClient with base_url=None...")
try:
    client = httpx.AsyncClient(base_url=None)
    print("✓ Success with base_url=None")
except Exception as e:
    print(f"✗ Error with base_url=None: {e}")

# Test what happens without base_url argument
print("\nTesting httpx.AsyncClient without base_url argument...")
try:
    client = httpx.AsyncClient()
    print("✓ Success without base_url argument")
    print(f"  base_url: {client.base_url}")
except Exception as e:
    print(f"✗ Error without base_url argument: {e}")