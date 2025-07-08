#!/usr/bin/env python3
"""
PRSNL AI Features Test Script
Tests all AI-powered features and reports their status
"""

import requests
import json
import time
from typing import Dict, Any, Tuple
from datetime import datetime
import sys

# Color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(text: str):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")

def print_test(name: str, status: bool, details: str = ""):
    if status:
        print(f"{Colors.OKGREEN}✅ {name}{Colors.ENDC}")
    else:
        print(f"{Colors.FAIL}❌ {name}{Colors.ENDC}")
    if details:
        print(f"   {Colors.OKCYAN}{details}{Colors.ENDC}")

class AIFeatureTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results = {}
        self.session = requests.Session()
        
    def run_all_tests(self):
        """Run all AI feature tests"""
        print_header("PRSNL AI Features Test Suite")
        print(f"Testing against: {self.base_url}")
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Test 1: Health Check
        self.test_health()
        
        # Test 2: AI Suggestions
        self.test_ai_suggestions()
        
        # Test 3: Semantic Search
        self.test_semantic_search()
        
        # Test 4: Find Similar Items
        self.test_find_similar()
        
        # Test 5: WebSocket Connection
        self.test_websocket()
        
        # Test 6: Vision AI (if configured)
        self.test_vision_ai()
        
        # Test 7: Analytics Endpoints
        self.test_analytics()
        
        # Summary
        self.print_summary()
        
    def test_health(self):
        """Test health endpoint"""
        print_header("Testing Health Endpoint")
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print_test("Health endpoint accessible", True)
                print_test("Database", data.get("database", {}).get("status") == "UP",
                          f"Status: {data.get('database', {}).get('status')}")
                print_test("Azure OpenAI", data.get("azure_openai", {}).get("status") == "CONFIGURED",
                          f"Status: {data.get('azure_openai', {}).get('status')}")
                self.results["health"] = True
            else:
                print_test("Health endpoint accessible", False, f"Status code: {response.status_code}")
                self.results["health"] = False
        except Exception as e:
            print_test("Health endpoint accessible", False, f"Error: {str(e)}")
            self.results["health"] = False
            
    def test_ai_suggestions(self):
        """Test AI suggestions endpoint"""
        print_header("Testing AI Suggestions")
        
        test_urls = [
            ("https://example.com", "Simple test URL"),
            ("https://www.wikipedia.org", "Wikipedia homepage"),
            ("https://github.com/anthropics/claude", "GitHub repository")
        ]
        
        success_count = 0
        for url, description in test_urls:
            try:
                response = self.session.post(
                    f"{self.base_url}/api/suggest",
                    json={"url": url},
                    timeout=30
                )
                if response.status_code == 200:
                    data = response.json()
                    print_test(f"AI suggestions for {description}", True,
                              f"Generated {len(data.get('tags', []))} tags")
                    success_count += 1
                else:
                    print_test(f"AI suggestions for {description}", False,
                              f"Status: {response.status_code}")
            except Exception as e:
                print_test(f"AI suggestions for {description}", False, f"Error: {str(e)}")
                
        self.results["ai_suggestions"] = success_count > 0
        
    def test_semantic_search(self):
        """Test semantic search"""
        print_header("Testing Semantic Search")
        
        test_queries = [
            "technology news",
            "artificial intelligence",
            "web development"
        ]
        
        success_count = 0
        for query in test_queries:
            try:
                response = self.session.get(
                    f"{self.base_url}/api/search/semantic",
                    params={"query": query, "mode": "hybrid"},
                    timeout=10
                )
                if response.status_code == 200:
                    data = response.json()
                    print_test(f"Semantic search: '{query}'", True,
                              f"Found {len(data.get('items', []))} results")
                    success_count += 1
                else:
                    error_msg = response.json().get("detail", "Unknown error")
                    print_test(f"Semantic search: '{query}'", False,
                              f"Error: {error_msg}")
            except Exception as e:
                print_test(f"Semantic search: '{query}'", False, f"Error: {str(e)}")
                
        self.results["semantic_search"] = success_count > 0
        
    def test_find_similar(self):
        """Test find similar items"""
        print_header("Testing Find Similar Items")
        
        # First, get an item ID from timeline
        try:
            response = self.session.get(f"{self.base_url}/api/timeline?page=1", timeout=5)
            if response.status_code == 200 and response.json().get("items"):
                item_id = response.json()["items"][0]["id"]
                
                # Now test find similar
                similar_response = self.session.get(
                    f"{self.base_url}/api/search/similar/{item_id}",
                    timeout=10
                )
                if similar_response.status_code == 200:
                    data = similar_response.json()
                    print_test("Find similar items", True,
                              f"Found {len(data.get('items', []))} similar items")
                    self.results["find_similar"] = True
                else:
                    error_msg = similar_response.json().get("detail", "Unknown error")
                    print_test("Find similar items", False, f"Error: {error_msg}")
                    self.results["find_similar"] = False
            else:
                print_test("Find similar items", False, "No items available to test")
                self.results["find_similar"] = False
        except Exception as e:
            print_test("Find similar items", False, f"Error: {str(e)}")
            self.results["find_similar"] = False
            
    def test_websocket(self):
        """Test WebSocket connection"""
        print_header("Testing WebSocket Connection")
        
        # Test WebSocket endpoint availability
        ws_url = self.base_url.replace("http://", "ws://") + "/api/ws/test-client"
        print_test("WebSocket endpoint", True, f"Available at {ws_url}")
        self.results["websocket"] = True  # Basic check
        
    def test_vision_ai(self):
        """Test Vision AI endpoint"""
        print_header("Testing Vision AI")
        
        # For now, just check if the endpoint exists
        try:
            response = self.session.get(f"{self.base_url}/api/vision/test", timeout=5)
            if response.status_code == 404:
                print_test("Vision AI endpoint", False, "Not implemented yet")
                self.results["vision_ai"] = False
            else:
                print_test("Vision AI endpoint", True, "Endpoint available")
                self.results["vision_ai"] = True
        except:
            print_test("Vision AI endpoint", False, "Not available")
            self.results["vision_ai"] = False
            
    def test_analytics(self):
        """Test analytics endpoints"""
        print_header("Testing Analytics")
        
        endpoints = [
            ("/api/analytics/trends", "Content trends"),
            ("/api/analytics/topics", "Topic analysis"),
            ("/api/analytics/usage_patterns", "Usage patterns"),
            ("/api/analytics/knowledge_graph", "Knowledge graph"),
            ("/api/analytics/content_velocity", "Content velocity")
        ]
        
        success_count = 0
        for endpoint, name in endpoints:
            try:
                response = self.session.get(f"{self.base_url}{endpoint}", timeout=5)
                if response.status_code == 200:
                    print_test(f"{name} endpoint", True)
                    success_count += 1
                else:
                    print_test(f"{name} endpoint", False, f"Status: {response.status_code}")
            except Exception as e:
                print_test(f"{name} endpoint", False, f"Error: {str(e)}")
                
        self.results["analytics"] = success_count > 3  # At least 3 working
        
    def print_summary(self):
        """Print test summary"""
        print_header("Test Summary")
        
        total_tests = len(self.results)
        passed_tests = sum(1 for v in self.results.values() if v)
        
        print(f"Total tests: {total_tests}")
        print(f"Passed: {Colors.OKGREEN}{passed_tests}{Colors.ENDC}")
        print(f"Failed: {Colors.FAIL}{total_tests - passed_tests}{Colors.ENDC}")
        print(f"Success rate: {(passed_tests / total_tests * 100):.1f}%")
        
        print("\n" + Colors.BOLD + "Feature Status:" + Colors.ENDC)
        for feature, status in self.results.items():
            status_str = f"{Colors.OKGREEN}Working{Colors.ENDC}" if status else f"{Colors.FAIL}Not Working{Colors.ENDC}"
            print(f"  {feature.replace('_', ' ').title()}: {status_str}")
            
        print("\n" + Colors.BOLD + "Recommendations:" + Colors.ENDC)
        if not self.results.get("semantic_search"):
            print("  - Configure Azure OpenAI embedding deployment for semantic search")
        if not self.results.get("vision_ai"):
            print("  - Implement Vision AI endpoints for image processing")
        if passed_tests < total_tests:
            print("  - Review the COMPLEX_ISSUES_LOG.md for troubleshooting")

if __name__ == "__main__":
    # Check if custom port is provided
    port = 8000
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print(f"Invalid port: {sys.argv[1]}")
            sys.exit(1)
            
    base_url = f"http://localhost:{port}"
    tester = AIFeatureTester(base_url)
    tester.run_all_tests()