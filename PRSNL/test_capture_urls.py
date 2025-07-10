#!/usr/bin/env python3
"""
Comprehensive URL Capture Test
Tests all 8 cognitive classifications with ASMRization on/off (16 combinations total)
"""

import requests
import json
import time
import sys
from typing import Dict, List

# Test configuration
BASE_URL = "http://localhost:3002"
API_URL = "http://localhost:8000/api"

# Test URLs for each cognitive classification
TEST_URLS = {
    "auto": "https://example.com/auto-detect",
    "document": "https://arxiv.org/pdf/2301.07041.pdf",
    "video": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", 
    "article": "https://techcrunch.com/2024/01/15/ai-breakthrough-announcement/",
    "tutorial": "https://docs.python.org/3/tutorial/",
    "image": "https://unsplash.com/photos/beautiful-landscape",
    "note": "https://gist.github.com/example/note",
    "link": "https://github.com/microsoft/vscode"
}

class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

def test_api_health():
    """Test if the API is responding"""
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def test_frontend_health():
    """Test if the frontend is responding"""
    try:
        response = requests.get(BASE_URL, timeout=5)
        return response.status_code == 200
    except:
        return False

def capture_url(url: str, content_type: str, enable_summarization: bool) -> Dict:
    """Capture a URL with specified parameters"""
    payload = {
        "url": url,
        "title": f"Test {content_type} - {'ASMRized' if enable_summarization else 'Standard'}",
        "highlight": f"Testing {content_type} classification with summarization {'enabled' if enable_summarization else 'disabled'}",
        "content_type": content_type,
        "enable_summarization": enable_summarization,
        "tags": [f"test-{content_type}", "automated-test"]
    }
    
    try:
        response = requests.post(
            f"{API_URL}/capture",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        return {
            "success": response.status_code in [200, 201],
            "status_code": response.status_code,
            "response": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text,
            "error": None
        }
        
    except requests.exceptions.Timeout:
        return {
            "success": False,
            "status_code": 408,
            "response": None,
            "error": "Request timeout"
        }
    except Exception as e:
        return {
            "success": False, 
            "status_code": 0,
            "response": None,
            "error": str(e)
        }

def run_comprehensive_test():
    """Run all 16 test combinations"""
    print(f"{Colors.BOLD}{Colors.CYAN}🧪 PRSNL Comprehensive Capture Test{Colors.END}")
    print("=" * 60)
    
    # Health checks
    print(f"\n{Colors.BOLD}🏥 Health Checks:{Colors.END}")
    
    frontend_ok = test_frontend_health()
    api_ok = test_api_health()
    
    print(f"Frontend (port 3002): {'✅' if frontend_ok else '❌'}")
    print(f"Backend API (port 8000): {'✅' if api_ok else '❌'}")
    
    if not api_ok:
        print(f"\n{Colors.RED}❌ API is not responding. Please check backend container.{Colors.END}")
        return
        
    # Run tests
    print(f"\n{Colors.BOLD}🎯 Running 16 Capture Tests:{Colors.END}")
    print("Testing each cognitive classification with ASMRization ON/OFF\n")
    
    results = []
    test_count = 0
    
    for content_type, test_url in TEST_URLS.items():
        for enable_asmr in [False, True]:
            test_count += 1
            asmr_status = "ASMRized" if enable_asmr else "Standard"
            
            print(f"{Colors.BLUE}Test {test_count}/16:{Colors.END} {content_type} ({asmr_status})")
            print(f"  URL: {test_url}")
            
            result = capture_url(test_url, content_type, enable_asmr)
            results.append({
                "test_number": test_count,
                "content_type": content_type,
                "enable_summarization": enable_asmr,
                "url": test_url,
                **result
            })
            
            if result["success"]:
                print(f"  {Colors.GREEN}✅ SUCCESS{Colors.END} (HTTP {result['status_code']})")
                if result["response"] and isinstance(result["response"], dict):
                    item_id = result["response"].get("id", "unknown")
                    print(f"     Created item ID: {item_id}")
            else:
                print(f"  {Colors.RED}❌ FAILED{Colors.END} (HTTP {result['status_code']})")
                if result["error"]:
                    print(f"     Error: {result['error']}")
                elif result["response"]:
                    print(f"     Response: {result['response']}")
            
            print()
            time.sleep(1)  # Avoid overwhelming the API
    
    # Summary
    print(f"{Colors.BOLD}📊 TEST SUMMARY:{Colors.END}")
    print("=" * 40)
    
    successful_tests = [r for r in results if r["success"]]
    failed_tests = [r for r in results if not r["success"]]
    
    print(f"Total Tests: {len(results)}")
    print(f"{Colors.GREEN}Successful: {len(successful_tests)}{Colors.END}")
    print(f"{Colors.RED}Failed: {len(failed_tests)}{Colors.END}")
    print(f"Success Rate: {len(successful_tests)/len(results)*100:.1f}%")
    
    if failed_tests:
        print(f"\n{Colors.RED}{Colors.BOLD}Failed Tests:{Colors.END}")
        for test in failed_tests:
            asmr = "ASMRized" if test["enable_summarization"] else "Standard"
            print(f"  ❌ {test['content_type']} ({asmr}) - HTTP {test['status_code']}")
            if test["error"]:
                print(f"     {test['error']}")
    
    # Content type breakdown
    print(f"\n{Colors.BOLD}📈 Results by Content Type:{Colors.END}")
    for content_type in TEST_URLS.keys():
        type_results = [r for r in results if r["content_type"] == content_type]
        type_success = [r for r in type_results if r["success"]]
        print(f"  {content_type}: {len(type_success)}/2 successful")
    
    # ASMRization breakdown
    asmr_on = [r for r in results if r["enable_summarization"] and r["success"]]
    asmr_off = [r for r in results if not r["enable_summarization"] and r["success"]]
    
    print(f"\n{Colors.BOLD}🔄 ASMRization Results:{Colors.END}")
    print(f"  Standard (no summarization): {len(asmr_off)}/8 successful")
    print(f"  ASMRized (with summarization): {len(asmr_on)}/8 successful")
    
    # Export detailed results
    with open("test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n{Colors.CYAN}📄 Detailed results saved to: test_results.json{Colors.END}")
    
    return len(failed_tests) == 0

if __name__ == "__main__":
    success = run_comprehensive_test()
    sys.exit(0 if success else 1)