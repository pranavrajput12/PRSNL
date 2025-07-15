#!/usr/bin/env python3
"""
Safe dependency update script for PRSNL
Updates dependencies in phases with testing between each phase
"""

import subprocess
import sys
from typing import List, Dict
import json
from datetime import datetime

# Phase 1: Critical Security & Performance Updates
PHASE_1_UPDATES = {
    "fastapi": ">=0.116.1",
    "openai": ">=1.96.0", 
    "sqlalchemy": ">=2.0.41",
    "sentry-sdk[fastapi]": ">=2.33.0",
    "uvicorn[standard]": ">=0.35.0"
}

# Phase 2: AI & Processing Enhancements
PHASE_2_UPDATES = {
    "langgraph": ">=0.5.3",
    "haystack-ai": ">=2.15.2",
    "langchain-community": ">=0.3.27",
    "langchain-openai": ">=0.3.28",
    "sentence-transformers": ">=5.0.0",
    "crawl4ai": ">=0.7.0"
}

# Phase 3: Infrastructure & Tools
PHASE_3_UPDATES = {
    "redis": ">=6.2.0",
    "celery": ">=5.5.3",
    "httpx": ">=0.28.1",
    "pytest": ">=8.4.1",
    "black": ">=25.1.0",
    "Pillow": ">=11.3.0",
    "aiohttp": ">=3.12.14"
}

def run_command(cmd: List[str]) -> tuple[int, str, str]:
    """Run a command and return exit code, stdout, stderr"""
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr

def test_basic_functionality():
    """Run basic tests to ensure system still works"""
    print("🧪 Running basic functionality tests...")
    
    tests = [
        # Test backend health
        ["curl", "-s", "http://localhost:8000/health"],
        # Test database connection
        ["python3", "-c", "import asyncpg; print('DB import OK')"],
        # Test AI services
        ["python3", "-c", "import openai; print('OpenAI import OK')"],
    ]
    
    for test in tests:
        code, stdout, stderr = run_command(test)
        if code != 0:
            print(f"❌ Test failed: {' '.join(test)}")
            print(f"Error: {stderr}")
            return False
        print(f"✅ Test passed: {' '.join(test[:2])}...")
    
    return True

def update_packages(packages: Dict[str, str], phase_name: str):
    """Update a set of packages"""
    print(f"\n📦 Starting {phase_name} updates...")
    
    results = {}
    
    for package, version in packages.items():
        print(f"\n🔄 Updating {package} to {version}...")
        
        # Create pip install command
        cmd = [sys.executable, "-m", "pip", "install", f"{package}{version}"]
        
        # Run update
        code, stdout, stderr = run_command(cmd)
        
        if code == 0:
            print(f"✅ Successfully updated {package}")
            results[package] = "success"
        else:
            print(f"❌ Failed to update {package}")
            print(f"Error: {stderr}")
            results[package] = "failed"
            
            # Ask if should continue
            response = input("Continue with other updates? (y/n): ")
            if response.lower() != 'y':
                return results
    
    return results

def create_backup():
    """Create backup of current requirements"""
    print("💾 Creating backup of current requirements...")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"requirements.backup.{timestamp}.txt"
    
    cmd = [sys.executable, "-m", "pip", "freeze", ">", backup_file]
    subprocess.run(" ".join(cmd), shell=True)
    
    print(f"✅ Backup created: {backup_file}")
    return backup_file

def main():
    """Main update process"""
    print("🚀 PRSNL Dependency Update Script")
    print("=================================")
    
    # Create backup
    backup_file = create_backup()
    
    # Test current functionality
    if not test_basic_functionality():
        print("❌ Basic tests failed. Aborting update.")
        return
    
    all_results = {}
    
    # Phase 1
    if input("\n🔸 Proceed with Phase 1 (Critical Updates)? (y/n): ").lower() == 'y':
        results = update_packages(PHASE_1_UPDATES, "Phase 1")
        all_results["phase_1"] = results
        
        if not test_basic_functionality():
            print("⚠️ Tests failed after Phase 1. Consider reverting.")
            print(f"To revert: pip install -r {backup_file}")
    
    # Phase 2
    if input("\n🔸 Proceed with Phase 2 (AI Enhancements)? (y/n): ").lower() == 'y':
        results = update_packages(PHASE_2_UPDATES, "Phase 2")
        all_results["phase_2"] = results
        
        if not test_basic_functionality():
            print("⚠️ Tests failed after Phase 2. Consider reverting.")
    
    # Phase 3
    if input("\n🔸 Proceed with Phase 3 (Infrastructure)? (y/n): ").lower() == 'y':
        results = update_packages(PHASE_3_UPDATES, "Phase 3")
        all_results["phase_3"] = results
        
        if not test_basic_functionality():
            print("⚠️ Tests failed after Phase 3. Consider reverting.")
    
    # Save results
    with open("update_results.json", "w") as f:
        json.dump(all_results, f, indent=2)
    
    print("\n📊 Update Summary")
    print("================")
    for phase, results in all_results.items():
        success = sum(1 for r in results.values() if r == "success")
        total = len(results)
        print(f"{phase}: {success}/{total} successful")
    
    print(f"\n💡 To revert all changes: pip install -r {backup_file}")
    print("📄 Results saved to: update_results.json")

if __name__ == "__main__":
    main()