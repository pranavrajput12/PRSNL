#!/usr/bin/env python3
"""
Real-time monitor for Azure OpenAI model data flow
Shows live data as it flows from models through backend to frontend
"""

import asyncio
import aiohttp
import json
import sys
from datetime import datetime
import websockets
from collections import deque

# Configuration
API_BASE = "http://localhost:8000/api"
WS_BASE = "ws://localhost:8000/ws"

# Terminal colors and control
CLEAR_SCREEN = "\033[2J\033[H"
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
CYAN = "\033[96m"
MAGENTA = "\033[95m"
RESET = "\033[0m"
BOLD = "\033[1m"


class AIModelMonitor:
    def __init__(self):
        self.events = deque(maxlen=20)  # Keep last 20 events
        self.model_status = {
            "whisper": {"status": "idle", "last_activity": None, "count": 0},
            "vision": {"status": "idle", "last_activity": None, "count": 0},
            "embedding": {"status": "idle", "last_activity": None, "count": 0},
            "websocket": {"status": "disconnected", "messages": 0}
        }
        self.running = True
        
    def add_event(self, model, event_type, message):
        """Add an event to the monitor"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.events.append({
            "time": timestamp,
            "model": model,
            "type": event_type,
            "message": message
        })
        
        # Update model status
        if model in self.model_status:
            self.model_status[model]["last_activity"] = timestamp
            self.model_status[model]["count"] += 1
    
    def display(self):
        """Display the monitoring dashboard"""
        print(CLEAR_SCREEN)
        
        # Header
        print(f"{BOLD}{CYAN}PRSNL AI Model Monitor - Real-time Data Flow{RESET}")
        print(f"{CYAN}{'='*60}{RESET}")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Model Status
        print(f"{BOLD}Model Status:{RESET}")
        for model, info in self.model_status.items():
            status_color = GREEN if info["status"] == "active" else YELLOW if info["status"] == "idle" else RED
            status_icon = "●" if info["status"] == "active" else "○" if info["status"] == "idle" else "✗"
            
            print(f"  {status_color}{status_icon}{RESET} {model.upper():12} "
                  f"Status: {info['status']:12} "
                  f"Events: {info['count']:4} "
                  f"Last: {info['last_activity'] or 'Never'}")
        
        # Recent Events
        print(f"\n{BOLD}Recent Activity:{RESET}")
        print(f"{'-'*60}")
        
        for event in self.events:
            # Color based on model
            if event["model"] == "whisper":
                color = BLUE
            elif event["model"] == "vision":
                color = MAGENTA
            elif event["model"] == "embedding":
                color = GREEN
            else:
                color = YELLOW
            
            print(f"{event['time']} {color}[{event['model'].upper():8}]{RESET} "
                  f"{event['type']:12} {event['message'][:40]}...")
        
        # Instructions
        print(f"\n{CYAN}Press Ctrl+C to stop monitoring{RESET}")
    
    async def monitor_api_calls(self, session):
        """Monitor API calls for model activity"""
        while self.running:
            try:
                # Check recent items for processing status
                async with session.get(f"{API_BASE}/items?limit=5") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        items = data.get('items', [])
                        
                        for item in items:
                            metadata = item.get('metadata', {})
                            
                            # Check for Whisper activity
                            if 'transcription' in metadata or \
                               'transcription' in metadata.get('video_metadata', {}):
                                self.model_status["whisper"]["status"] = "active"
                                self.add_event("whisper", "transcribed", 
                                             f"Video: {item.get('title', 'Unknown')[:30]}")
                            
                            # Check for Vision activity
                            if 'vision_analysis' in metadata:
                                self.model_status["vision"]["status"] = "active"
                                self.add_event("vision", "analyzed", 
                                             f"Image: {item.get('title', 'Unknown')[:30]}")
                            
                            # Check for Embedding activity
                            if 'embedding_generated' in metadata or \
                               item.get('embedding') is not None:
                                self.model_status["embedding"]["status"] = "active"
                                self.add_event("embedding", "generated", 
                                             f"Item: {item.get('title', 'Unknown')[:30]}")
                
                # Monitor search endpoint for embedding usage
                async with session.get(f"{API_BASE}/search?query=test&semantic=true&limit=1") as resp:
                    if resp.status == 200:
                        results = await resp.json()
                        if results and any('relevance_score' in r for r in results):
                            self.add_event("embedding", "search", "Semantic search active")
                
                await asyncio.sleep(2)  # Check every 2 seconds
                
            except Exception as e:
                self.add_event("system", "error", str(e))
                await asyncio.sleep(5)
    
    async def monitor_websocket(self):
        """Monitor WebSocket for real-time updates"""
        while self.running:
            try:
                uri = f"{WS_BASE}/chat/monitor-client"
                async with websockets.connect(uri) as websocket:
                    self.model_status["websocket"]["status"] = "connected"
                    self.add_event("websocket", "connected", "WebSocket connection established")
                    
                    while self.running:
                        try:
                            message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                            data = json.loads(message)
                            
                            self.model_status["websocket"]["messages"] += 1
                            
                            # Analyze message for model activity
                            if "transcription" in str(data):
                                self.add_event("whisper", "ws_update", "Transcription data flowing")
                            if "vision" in str(data) or "image_analysis" in str(data):
                                self.add_event("vision", "ws_update", "Vision data flowing")
                            if "embedding" in str(data) or "similarity" in str(data):
                                self.add_event("embedding", "ws_update", "Embedding data flowing")
                            
                            self.add_event("websocket", "message", f"Type: {data.get('type', 'unknown')}")
                            
                        except asyncio.TimeoutError:
                            continue
                            
            except Exception as e:
                self.model_status["websocket"]["status"] = "disconnected"
                self.add_event("websocket", "error", str(e))
                await asyncio.sleep(5)
    
    async def trigger_test_activities(self, session):
        """Periodically trigger test activities to see data flow"""
        test_cycle = 0
        
        while self.running:
            try:
                test_cycle += 1
                
                # Every 30 seconds, trigger a different test
                if test_cycle % 3 == 1:
                    # Test Vision
                    self.add_event("test", "trigger", "Testing vision analysis...")
                    # Small test image
                    test_image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
                    
                    async with session.post(f"{API_BASE}/vision/analyze", 
                                          json={"image_base64": test_image, "image_path": "test.png"}) as resp:
                        if resp.status == 200:
                            self.add_event("vision", "test_success", "Vision test completed")
                
                elif test_cycle % 3 == 2:
                    # Test Embedding/Search
                    self.add_event("test", "trigger", "Testing semantic search...")
                    
                    async with session.get(f"{API_BASE}/search", 
                                         params={"query": "AI technology", "semantic": "true"}) as resp:
                        if resp.status == 200:
                            results = await resp.json()
                            self.add_event("embedding", "test_success", 
                                         f"Found {len(results)} semantic results")
                
                await asyncio.sleep(30)  # Wait 30 seconds between tests
                
            except Exception as e:
                self.add_event("test", "error", str(e))
                await asyncio.sleep(30)
    
    async def update_display(self):
        """Update the display periodically"""
        while self.running:
            self.display()
            await asyncio.sleep(1)  # Update every second
    
    async def run(self):
        """Run the monitor"""
        try:
            # Create HTTP session
            async with aiohttp.ClientSession() as session:
                # Start all monitoring tasks
                tasks = [
                    self.monitor_api_calls(session),
                    self.monitor_websocket(),
                    self.trigger_test_activities(session),
                    self.update_display()
                ]
                
                await asyncio.gather(*tasks)
                
        except KeyboardInterrupt:
            print(f"\n{YELLOW}Monitoring stopped by user{RESET}")
            self.running = False


async def main():
    """Main entry point"""
    monitor = AIModelMonitor()
    
    print(f"{CYAN}Starting AI Model Monitor...{RESET}")
    print(f"{YELLOW}This will show real-time data flow from Azure OpenAI models{RESET}")
    print(f"{YELLOW}The monitor will also trigger periodic tests{RESET}")
    print()
    
    # Check backend health first
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{API_BASE}/stats") as resp:
                if resp.status != 200:
                    print(f"{RED}Backend is not responding. Please start it first:{RESET}")
                    print("cd PRSNL && docker-compose up -d")
                    return
    except:
        print(f"{RED}Cannot connect to backend at {API_BASE}{RESET}")
        return
    
    try:
        await monitor.run()
    except KeyboardInterrupt:
        print(f"\n{GREEN}Monitor stopped{RESET}")


if __name__ == "__main__":
    asyncio.run(main())