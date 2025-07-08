#!/usr/bin/env python3
"""
Test real-time data flow from Azure OpenAI models to frontend
Monitors WebSocket connections and API responses
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime
import websockets

# Configuration
API_BASE = "http://localhost:8000/api"
WS_BASE = "ws://localhost:8000/ws"
FRONTEND_URL = "http://localhost:3002"

# ANSI colors
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
CYAN = "\033[96m"
RESET = "\033[0m"


class ModelDataFlowTester:
    def __init__(self):
        self.results = {
            "whisper": {"status": "pending", "data": None, "latency": None},
            "vision": {"status": "pending", "data": None, "latency": None},
            "embedding": {"status": "pending", "data": None, "latency": None},
            "websocket": {"status": "pending", "messages": []}
        }
    
    def print_status(self, model, status, message=""):
        """Print colored status for a model"""
        color = GREEN if status == "success" else RED if status == "error" else YELLOW
        symbol = "✓" if status == "success" else "✗" if status == "error" else "⟳"
        print(f"{color}{symbol} {model.upper()}: {message}{RESET}")
    
    async def monitor_websocket(self, duration=30):
        """Monitor WebSocket for real-time updates"""
        print(f"\n{CYAN}Monitoring WebSocket for {duration} seconds...{RESET}")
        
        try:
            # Connect to WebSocket
            uri = f"{WS_BASE}/chat/test-client"
            async with websockets.connect(uri) as websocket:
                self.results["websocket"]["status"] = "connected"
                print(f"{GREEN}✓ WebSocket connected{RESET}")
                
                # Send a test message
                test_message = {
                    "type": "chat",
                    "content": "Test message to verify AI model integration"
                }
                await websocket.send(json.dumps(test_message))
                
                # Listen for messages
                start_time = time.time()
                while time.time() - start_time < duration:
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                        data = json.loads(message)
                        self.results["websocket"]["messages"].append(data)
                        
                        # Display message type and content
                        msg_type = data.get("type", "unknown")
                        print(f"{BLUE}WS Message ({msg_type}):{RESET} {str(data)[:100]}...")
                        
                        # Check for model-specific data
                        if "model" in data:
                            print(f"  {YELLOW}Model: {data['model']}{RESET}")
                        if "embedding" in data:
                            print(f"  {GREEN}✓ Embedding data received{RESET}")
                        if "transcription" in data:
                            print(f"  {GREEN}✓ Transcription data received{RESET}")
                        if "vision_analysis" in data:
                            print(f"  {GREEN}✓ Vision analysis received{RESET}")
                            
                    except asyncio.TimeoutError:
                        continue
                    except Exception as e:
                        print(f"{RED}WebSocket error: {e}{RESET}")
                        
                self.results["websocket"]["status"] = "success"
                
        except Exception as e:
            self.results["websocket"]["status"] = "error"
            print(f"{RED}✗ WebSocket connection failed: {e}{RESET}")
    
    async def test_whisper_flow(self, session):
        """Test Whisper model data flow"""
        print(f"\n{BLUE}=== Testing Whisper Data Flow ==={RESET}")
        
        start_time = time.time()
        
        # Test video transcription endpoint
        video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        
        try:
            # Capture video to trigger transcription
            capture_data = {"url": video_url, "title": "Whisper Test Video"}
            
            async with session.post(f"{API_BASE}/capture", json=capture_data) as resp:
                if resp.status == 201:
                    result = await resp.json()
                    item_id = result['id']
                    
                    # Poll for transcription
                    for _ in range(10):  # Try for 10 seconds
                        await asyncio.sleep(1)
                        
                        async with session.get(f"{API_BASE}/items/{item_id}") as item_resp:
                            if item_resp.status == 200:
                                item = await item_resp.json()
                                
                                # Check for transcription
                                metadata = item.get('metadata', {})
                                if 'transcription' in metadata or \
                                   'transcription' in metadata.get('video_metadata', {}):
                                    self.results["whisper"]["status"] = "success"
                                    self.results["whisper"]["data"] = item
                                    self.results["whisper"]["latency"] = time.time() - start_time
                                    self.print_status("whisper", "success", 
                                                    f"Transcription received in {self.results['whisper']['latency']:.2f}s")
                                    return
                    
                    self.print_status("whisper", "error", "No transcription received after 10s")
                    self.results["whisper"]["status"] = "timeout"
                else:
                    self.print_status("whisper", "error", f"Capture failed: {resp.status}")
                    self.results["whisper"]["status"] = "error"
                    
        except Exception as e:
            self.print_status("whisper", "error", str(e))
            self.results["whisper"]["status"] = "error"
    
    async def test_vision_flow(self, session):
        """Test Vision model data flow"""
        print(f"\n{BLUE}=== Testing Vision Data Flow ==={RESET}")
        
        start_time = time.time()
        
        # Create a simple test image data
        test_image_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
        
        try:
            vision_data = {
                "image_base64": test_image_base64,
                "image_path": "test.png"
            }
            
            async with session.post(f"{API_BASE}/vision/analyze", json=vision_data) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    self.results["vision"]["status"] = "success"
                    self.results["vision"]["data"] = result
                    self.results["vision"]["latency"] = time.time() - start_time
                    
                    self.print_status("vision", "success", 
                                    f"Analysis received in {self.results['vision']['latency']:.2f}s")
                    
                    # Display key results
                    if 'tags' in result:
                        print(f"  Tags: {', '.join(result['tags'][:5])}")
                    if 'description' in result:
                        print(f"  Description: {result['description'][:100]}...")
                else:
                    error_text = await resp.text()
                    self.print_status("vision", "error", f"Failed: {resp.status} - {error_text[:50]}")
                    self.results["vision"]["status"] = "error"
                    
        except Exception as e:
            self.print_status("vision", "error", str(e))
            self.results["vision"]["status"] = "error"
    
    async def test_embedding_flow(self, session):
        """Test Embedding model data flow"""
        print(f"\n{BLUE}=== Testing Embedding Data Flow ==={RESET}")
        
        start_time = time.time()
        
        try:
            # Test semantic search
            search_params = {
                "query": "artificial intelligence",
                "semantic": "true",
                "limit": 5
            }
            
            async with session.get(f"{API_BASE}/search", params=search_params) as resp:
                if resp.status == 200:
                    results = await resp.json()
                    self.results["embedding"]["status"] = "success"
                    self.results["embedding"]["data"] = results
                    self.results["embedding"]["latency"] = time.time() - start_time
                    
                    self.print_status("embedding", "success", 
                                    f"Search completed in {self.results['embedding']['latency']:.2f}s")
                    
                    # Check if embeddings are being used
                    if results and len(results) > 0:
                        if 'relevance_score' in results[0]:
                            print(f"  {GREEN}✓ Semantic relevance scores present{RESET}")
                        print(f"  Found {len(results)} results")
                    else:
                        print(f"  {YELLOW}⚠ No results found (embeddings might not be generated){RESET}")
                else:
                    self.print_status("embedding", "error", f"Search failed: {resp.status}")
                    self.results["embedding"]["status"] = "error"
                    
        except Exception as e:
            self.print_status("embedding", "error", str(e))
            self.results["embedding"]["status"] = "error"
    
    async def test_frontend_endpoints(self, session):
        """Test frontend-specific endpoints"""
        print(f"\n{BLUE}=== Testing Frontend Data Endpoints ==={RESET}")
        
        endpoints = [
            ("/timeline", "Timeline"),
            ("/analytics", "Analytics"),
            ("/ai/insights", "AI Insights"),
            ("/items?limit=5", "Recent Items"),
            ("/tags", "Tags"),
        ]
        
        for endpoint, name in endpoints:
            try:
                async with session.get(f"{API_BASE}{endpoint}") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        print(f"{GREEN}✓ {name}:{RESET} OK (size: {len(json.dumps(data))} bytes)")
                    else:
                        print(f"{RED}✗ {name}:{RESET} Failed ({resp.status})")
            except Exception as e:
                print(f"{RED}✗ {name}:{RESET} Error - {str(e)}")
    
    def generate_report(self):
        """Generate final test report"""
        print(f"\n{CYAN}{'='*60}{RESET}")
        print(f"{CYAN}DATA FLOW TEST REPORT{RESET}")
        print(f"{CYAN}{'='*60}{RESET}\n")
        
        # Model status summary
        print(f"{BLUE}Model Integration Status:{RESET}")
        for model in ["whisper", "vision", "embedding"]:
            status = self.results[model]["status"]
            latency = self.results[model]["latency"]
            
            if status == "success":
                print(f"  {GREEN}✓ {model.upper()}: Working{RESET} (latency: {latency:.2f}s)" 
                      if latency else f"  {GREEN}✓ {model.upper()}: Working{RESET}")
            elif status == "timeout":
                print(f"  {YELLOW}⚠ {model.upper()}: Timeout (check model deployment){RESET}")
            else:
                print(f"  {RED}✗ {model.upper()}: Failed{RESET}")
        
        # WebSocket status
        ws_status = self.results["websocket"]["status"]
        ws_msgs = len(self.results["websocket"]["messages"])
        if ws_status == "success":
            print(f"  {GREEN}✓ WebSocket: Connected ({ws_msgs} messages received){RESET}")
        else:
            print(f"  {RED}✗ WebSocket: {ws_status}{RESET}")
        
        # Recommendations
        print(f"\n{BLUE}Recommendations:{RESET}")
        
        if self.results["whisper"]["status"] != "success":
            print(f"  • Check Whisper deployment: {YELLOW}AZURE_OPENAI_WHISPER_DEPLOYMENT{RESET}")
            print(f"    Verify in Azure Portal and update .env file")
        
        if self.results["vision"]["status"] != "success":
            print(f"  • Check GPT-4.1 deployment supports vision")
            print(f"    Deployment: {YELLOW}AZURE_OPENAI_DEPLOYMENT{RESET}")
        
        if self.results["embedding"]["status"] != "success":
            print(f"  • Check embedding deployment: {YELLOW}AZURE_OPENAI_EMBEDDING_DEPLOYMENT{RESET}")
            print(f"    Required for semantic search and similarity features")
        
        if ws_msgs == 0:
            print(f"  • WebSocket not receiving messages - check backend logs")
        
        print(f"\n{CYAN}Test completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{RESET}")


async def main():
    """Run the data flow tests"""
    tester = ModelDataFlowTester()
    
    print(f"{CYAN}PRSNL v2.0 - Model Data Flow Test{RESET}")
    print(f"{CYAN}{'='*40}{RESET}\n")
    
    # Create HTTP session
    timeout = aiohttp.ClientTimeout(total=60)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        # Run model tests
        await tester.test_vision_flow(session)
        await tester.test_embedding_flow(session)
        await tester.test_whisper_flow(session)
        await tester.test_frontend_endpoints(session)
    
    # Monitor WebSocket (runs separately)
    await tester.monitor_websocket(duration=10)
    
    # Generate report
    tester.generate_report()


if __name__ == "__main__":
    asyncio.run(main())