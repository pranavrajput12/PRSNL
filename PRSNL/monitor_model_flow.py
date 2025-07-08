#!/usr/bin/env python3
"""
Real-time monitoring of Azure OpenAI model data flow
Shows how data flows from backend models to frontend via WebSocket
"""

import asyncio
import aiohttp
import json
from datetime import datetime
import websockets
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text
import uuid

console = Console()

class ModelFlowMonitor:
    def __init__(self):
        self.api_base = "http://localhost:8000/api"
        self.ws_url = "ws://localhost:8000/ws"
        self.events = []
        self.model_stats = {
            "whisper": {"calls": 0, "last_used": None, "status": "idle"},
            "vision": {"calls": 0, "last_used": None, "status": "idle"},
            "embeddings": {"calls": 0, "last_used": None, "status": "idle"}
        }
        self.active_items = {}
        
    async def connect_websocket(self):
        """Connect to WebSocket for real-time updates"""
        try:
            async with websockets.connect(self.ws_url) as websocket:
                console.print("[green]✅ Connected to WebSocket[/green]")
                
                while True:
                    try:
                        message = await websocket.recv()
                        data = json.loads(message)
                        self.process_websocket_message(data)
                    except websockets.exceptions.ConnectionClosed:
                        console.print("[red]❌ WebSocket connection closed[/red]")
                        break
                    except json.JSONDecodeError:
                        console.print(f"[yellow]⚠️ Invalid JSON: {message}[/yellow]")
                        
        except Exception as e:
            console.print(f"[red]❌ WebSocket error: {e}[/red]")
    
    def process_websocket_message(self, data):
        """Process WebSocket messages to track model usage"""
        event = {
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "type": data.get("type", "unknown"),
            "data": data
        }
        
        self.events.insert(0, event)
        if len(self.events) > 20:  # Keep last 20 events
            self.events.pop()
        
        # Track model-specific events
        message = data.get("message", "")
        if "transcrib" in message.lower():
            self.model_stats["whisper"]["status"] = "active"
            self.model_stats["whisper"]["last_used"] = datetime.now()
            self.model_stats["whisper"]["calls"] += 1
        elif "vision" in message.lower() or "image" in message.lower():
            self.model_stats["vision"]["status"] = "active"
            self.model_stats["vision"]["last_used"] = datetime.now()
            self.model_stats["vision"]["calls"] += 1
        elif "embedding" in message.lower() or "semantic" in message.lower():
            self.model_stats["embeddings"]["status"] = "active"
            self.model_stats["embeddings"]["last_used"] = datetime.now()
            self.model_stats["embeddings"]["calls"] += 1
    
    async def monitor_api_calls(self):
        """Monitor API calls to track model usage"""
        async with aiohttp.ClientSession() as session:
            while True:
                try:
                    # Check recent items
                    async with session.get(f"{self.api_base}/items?limit=10") as resp:
                        if resp.status == 200:
                            items = await resp.json()
                            for item in items.get("items", []):
                                item_id = item["id"]
                                if item_id not in self.active_items:
                                    self.active_items[item_id] = item
                                    
                                    # Detect which model was used
                                    metadata = item.get("metadata", {})
                                    if metadata.get("ai_analysis"):
                                        self.model_stats["embeddings"]["status"] = "completed"
                                    if item.get("transcription"):
                                        self.model_stats["whisper"]["status"] = "completed"
                                    if metadata.get("vision_analysis"):
                                        self.model_stats["vision"]["status"] = "completed"
                    
                    # Reset idle models
                    for model in self.model_stats.values():
                        if model["last_used"]:
                            elapsed = (datetime.now() - model["last_used"]).seconds
                            if elapsed > 30:
                                model["status"] = "idle"
                    
                except Exception as e:
                    console.print(f"[red]API monitoring error: {e}[/red]")
                
                await asyncio.sleep(2)
    
    def create_display(self):
        """Create the monitoring display"""
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main", size=20),
            Layout(name="events", size=15)
        )
        
        # Header
        header_text = Text("🔍 PRSNL Model Flow Monitor", style="bold white on blue")
        layout["header"].update(Panel(header_text, border_style="blue"))
        
        # Model stats table
        table = Table(title="Azure OpenAI Model Status", box="ROUNDED")
        table.add_column("Model", style="cyan", width=20)
        table.add_column("Status", width=15)
        table.add_column("Calls", justify="right", width=10)
        table.add_column("Last Used", width=20)
        table.add_column("Data Flow", width=40)
        
        for model_name, stats in self.model_stats.items():
            status_style = {
                "idle": "dim",
                "active": "yellow",
                "completed": "green"
            }.get(stats["status"], "white")
            
            status_text = {
                "idle": "⚪ Idle",
                "active": "🟡 Processing",
                "completed": "🟢 Completed"
            }.get(stats["status"], stats["status"])
            
            last_used = stats["last_used"].strftime("%H:%M:%S") if stats["last_used"] else "Never"
            
            # Data flow visualization
            if model_name == "whisper":
                flow = "Video → [yellow]Whisper[/] → Transcription → Frontend"
            elif model_name == "vision":
                flow = "Image → [yellow]Vision[/] → Analysis → Frontend"
            else:
                flow = "Text → [yellow]Embedding[/] → Vector → Search"
            
            table.add_row(
                model_name.capitalize(),
                Text(status_text, style=status_style),
                str(stats["calls"]),
                last_used,
                flow
            )
        
        layout["main"].update(Panel(table, border_style="green"))
        
        # Recent events
        events_text = ""
        for event in self.events[:10]:
            events_text += f"[dim]{event['timestamp']}[/] {event['type']}: {event['data'].get('message', '')[:80]}\n"
        
        layout["events"].update(
            Panel(
                events_text or "No events yet...",
                title="Recent WebSocket Events",
                border_style="yellow"
            )
        )
        
        return layout
    
    async def test_model_flow(self):
        """Trigger test actions to demonstrate model flow"""
        async with aiohttp.ClientSession() as session:
            console.print("\n[cyan]🧪 Running model flow tests...[/cyan]")
            
            # Test 1: Vision flow
            console.print("[yellow]Testing Vision flow...[/yellow]")
            # Would trigger vision test here
            
            # Test 2: Embedding flow
            console.print("[yellow]Testing Embedding flow...[/yellow]")
            test_content = {
                "content": f"Model flow test at {datetime.now()}",
                "title": "Flow Test Document",
                "tags": ["test", "monitoring"]
            }
            
            try:
                async with session.post(
                    f"{self.api_base}/capture",
                    json=test_content,
                    headers={"Content-Type": "application/json"}
                ) as resp:
                    if resp.status == 201:
                        result = await resp.json()
                        console.print(f"[green]✅ Test item created: {result['id']}[/green]")
            except Exception as e:
                console.print(f"[red]❌ Test failed: {e}[/red]")
    
    async def run(self):
        """Run the monitor"""
        # Start background tasks
        ws_task = asyncio.create_task(self.connect_websocket())
        api_task = asyncio.create_task(self.monitor_api_calls())
        
        # Run test after a delay
        asyncio.create_task(self.run_test_after_delay())
        
        # Display loop
        with Live(self.create_display(), refresh_per_second=2) as live:
            try:
                while True:
                    live.update(self.create_display())
                    await asyncio.sleep(0.5)
            except KeyboardInterrupt:
                console.print("\n[yellow]Monitor stopped by user[/yellow]")
                ws_task.cancel()
                api_task.cancel()
    
    async def run_test_after_delay(self):
        """Run test after initial setup"""
        await asyncio.sleep(3)
        await self.test_model_flow()

async def main():
    """Main entry point"""
    console.print("[bold cyan]🚀 Starting PRSNL Model Flow Monitor[/bold cyan]")
    console.print("[dim]Press Ctrl+C to stop[/dim]\n")
    
    monitor = ModelFlowMonitor()
    await monitor.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[yellow]👋 Monitor stopped[/yellow]")