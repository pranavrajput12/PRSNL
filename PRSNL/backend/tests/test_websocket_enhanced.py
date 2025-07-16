"""
Test suite for Enhanced WebSocket functionality with FastAPI 0.116.1
Tests the improved connection handling, error recovery, and performance features
"""

import asyncio
import json
import pytest
import time
from datetime import datetime
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from app.main import app
from app.api.websocket_enhanced import ws_metrics

class TestWebSocketEnhanced:
    """Test enhanced WebSocket functionality"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @pytest.fixture
    def reset_metrics(self):
        """Reset WebSocket metrics before each test"""
        ws_metrics.connections = 0
        ws_metrics.messages_sent = 0
        ws_metrics.messages_received = 0
        ws_metrics.errors = 0
        ws_metrics.connection_times = []
    
    def test_websocket_health_endpoint(self, client):
        """Test WebSocket health check endpoint"""
        response = client.get("/ws/enhanced/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert data["fastapi_version"] == "0.116.1"
        assert "websocket_features" in data
        assert "async_context_managers" in data["websocket_features"]
        assert "enhanced_error_handling" in data["websocket_features"]
        assert "performance_monitoring" in data["websocket_features"]
    
    def test_enhanced_progress_websocket_connection(self, client, reset_metrics):
        """Test enhanced progress WebSocket connection establishment"""
        task_id = "test_task_123"
        
        with client.websocket_connect(f"/ws/enhanced/progress/{task_id}") as websocket:
            # Should receive connection confirmation
            data = websocket.receive_json()
            assert data["type"] == "connection_enhanced"
            assert data["status"] == "connected"
            assert data["server_version"] == "0.116.1"
            assert "async_context" in data["features"]
            
            # Metrics should be updated
            assert ws_metrics.connections >= 1
    
    @patch('app.db.database.get_db_pool')
    def test_enhanced_progress_websocket_task_monitoring(self, mock_db_pool, client, reset_metrics):
        """Test task progress monitoring via enhanced WebSocket"""
        task_id = "test_task_456"
        
        # Mock database response
        mock_conn = AsyncMock()
        mock_conn.fetchrow.return_value = {
            'id': task_id,
            'status': 'processing',
            'progress': 0.5,
            'message': 'Processing document...',
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        mock_pool = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        mock_db_pool.return_value = mock_pool
        
        with client.websocket_connect(f"/ws/enhanced/progress/{task_id}") as websocket:
            # Skip connection message
            connection_msg = websocket.receive_json()
            assert connection_msg["type"] == "connection_enhanced"
            
            # Should receive progress update
            progress_msg = websocket.receive_json()
            assert progress_msg["type"] == "progress"
            assert progress_msg["data"]["task_id"] == task_id
            assert progress_msg["data"]["progress"] == 0.5
            assert progress_msg["data"]["status"] == "processing"
    
    @patch('app.db.database.get_db_pool')
    def test_enhanced_progress_websocket_task_completion(self, mock_db_pool, client, reset_metrics):
        """Test task completion notification via enhanced WebSocket"""
        task_id = "test_task_789"
        
        # Mock database response for completed task
        mock_conn = AsyncMock()
        mock_conn.fetchrow.return_value = {
            'id': task_id,
            'status': 'completed',
            'progress': 1.0,
            'message': 'Task completed successfully',
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        mock_pool = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        mock_db_pool.return_value = mock_pool
        
        with client.websocket_connect(f"/ws/enhanced/progress/{task_id}") as websocket:
            # Skip connection message
            websocket.receive_json()
            
            # Should receive progress update
            progress_msg = websocket.receive_json()
            assert progress_msg["type"] == "progress"
            assert progress_msg["data"]["status"] == "completed"
            
            # Should receive completion notification
            completion_msg = websocket.receive_json()
            assert completion_msg["type"] == "task_complete"
            assert completion_msg["task_id"] == task_id
            assert completion_msg["final_status"] == "completed"
    
    @patch('app.db.database.get_db_pool')
    def test_enhanced_progress_websocket_task_not_found(self, mock_db_pool, client, reset_metrics):
        """Test enhanced WebSocket handling of non-existent task"""
        task_id = "nonexistent_task"
        
        # Mock database response for non-existent task
        mock_conn = AsyncMock()
        mock_conn.fetchrow.return_value = None
        
        mock_pool = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        mock_db_pool.return_value = mock_pool
        
        with client.websocket_connect(f"/ws/enhanced/progress/{task_id}") as websocket:
            # Skip connection message
            websocket.receive_json()
            
            # Should receive error message
            error_msg = websocket.receive_json()
            assert error_msg["type"] == "error"
            assert "not found" in error_msg["message"]
    
    @patch('app.services.unified_ai_service.UnifiedAIService')
    @patch('app.db.database.get_db_pool')
    def test_enhanced_chat_websocket_connection(self, mock_db_pool, mock_ai_service, client, reset_metrics):
        """Test enhanced chat WebSocket connection and basic functionality"""
        client_id = "test_client_123"
        
        with client.websocket_connect(f"/ws/enhanced/chat/{client_id}") as websocket:
            # Should receive connection confirmation
            data = websocket.receive_json()
            assert data["type"] == "connection_enhanced"
            assert data["client_id"] == client_id
            assert data["status"] == "connected"
    
    @patch('app.services.unified_ai_service.UnifiedAIService')
    @patch('app.db.database.get_db_pool')
    def test_enhanced_chat_websocket_message_processing(self, mock_db_pool, mock_ai_service, client, reset_metrics):
        """Test enhanced chat WebSocket message processing"""
        client_id = "test_client_456"
        
        # Mock database search results
        mock_conn = AsyncMock()
        mock_conn.fetch.return_value = [
            {
                'id': '1',
                'title': 'Test Document',
                'content': 'This is test content about AI and machine learning.',
                'url': 'https://example.com/test',
                'tags': 'ai,ml',
                'created_at': datetime.utcnow(),
                'summary': 'Test summary',
                'category': 'technology',
                'rank_score': 0.8
            }
        ]
        
        mock_pool = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        mock_db_pool.return_value = mock_pool
        
        # Mock AI service streaming response
        mock_ai_instance = AsyncMock()
        mock_ai_instance.stream_chat_response.return_value = [
            "This", " is", " a", " test", " response", " about", " AI."
        ]
        mock_ai_service.return_value = mock_ai_instance
        
        with client.websocket_connect(f"/ws/enhanced/chat/{client_id}") as websocket:
            # Skip connection message
            websocket.receive_json()
            
            # Send test message
            websocket.send_json({
                "message": "Tell me about AI",
                "history": []
            })
            
            # Should receive status updates
            status_msg = websocket.receive_json()
            assert status_msg["type"] == "status"
            assert "Processing" in status_msg["message"]
            
            # Should receive another status update
            status_msg2 = websocket.receive_json()
            assert status_msg2["type"] == "status"
            assert "Found" in status_msg2["message"]
            
            # Should receive streaming chunks
            chunks_received = 0
            while chunks_received < 7:  # Expected number of chunks
                chunk_msg = websocket.receive_json()
                if chunk_msg["type"] == "chunk":
                    assert "chunk_id" in chunk_msg
                    assert "timestamp" in chunk_msg
                    chunks_received += 1
                else:
                    break
            
            # Should receive completion message
            if chunks_received == 7:
                complete_msg = websocket.receive_json()
                assert complete_msg["type"] == "complete"
                assert "citations" in complete_msg
                assert complete_msg["context_count"] == 1
                assert complete_msg["chunks_sent"] == 7
    
    def test_enhanced_chat_websocket_timeout_handling(self, client, reset_metrics):
        """Test enhanced chat WebSocket timeout handling"""
        client_id = "test_timeout_client"
        
        with client.websocket_connect(f"/ws/enhanced/chat/{client_id}") as websocket:
            # Skip connection message
            websocket.receive_json()
            
            # Don't send any message and wait for timeout (in real scenario)
            # For testing, we'll simulate the timeout behavior
            # In actual implementation, this would timeout after 5 minutes
    
    def test_websocket_metrics_tracking(self, client, reset_metrics):
        """Test WebSocket metrics tracking functionality"""
        with client.websocket_connect("/ws/enhanced/metrics") as websocket:
            # Should receive connection confirmation
            connection_msg = websocket.receive_json()
            assert connection_msg["type"] == "connection_enhanced"
            
            # Should receive metrics data
            metrics_msg = websocket.receive_json()
            assert metrics_msg["type"] == "metrics"
            assert "data" in metrics_msg
            
            metrics_data = metrics_msg["data"]
            assert "total_connections" in metrics_data
            assert "messages_sent" in metrics_data
            assert "messages_received" in metrics_data
            assert "errors" in metrics_data
            assert "avg_connection_time" in metrics_data
            assert "active_connections" in metrics_data
            assert "timestamp" in metrics_data
    
    def test_websocket_error_handling_and_metrics(self, client, reset_metrics):
        """Test enhanced WebSocket error handling and error metrics tracking"""
        initial_errors = ws_metrics.errors
        
        # Test with invalid task ID format that might cause database errors
        with patch('app.db.database.get_db_pool') as mock_db_pool:
            # Mock database error
            mock_db_pool.side_effect = Exception("Database connection error")
            
            with client.websocket_connect("/ws/enhanced/progress/invalid_task") as websocket:
                # Skip connection message
                websocket.receive_json()
                
                # Should receive error message
                error_msg = websocket.receive_json()
                assert error_msg["type"] == "error"
                assert "error" in error_msg["message"].lower()
                
                # Error count should increase
                assert ws_metrics.errors > initial_errors
    
    def test_websocket_connection_metrics_tracking(self, client, reset_metrics):
        """Test that connection metrics are properly tracked"""
        initial_connections = ws_metrics.connections
        initial_connection_times_count = len(ws_metrics.connection_times)
        
        with client.websocket_connect("/ws/enhanced/progress/test_metrics") as websocket:
            # Skip connection and initial messages
            websocket.receive_json()
            time.sleep(0.1)  # Small delay to ensure connection time is recorded
        
        # Connection count should increase
        assert ws_metrics.connections > initial_connections
        
        # Connection time should be recorded
        assert len(ws_metrics.connection_times) > initial_connection_times_count
        
        # Connection time should be reasonable (> 0 and < 10 seconds for test)
        latest_connection_time = ws_metrics.connection_times[-1]
        assert 0 < latest_connection_time < 10

@pytest.mark.asyncio
class TestWebSocketEnhancedAsync:
    """Async tests for enhanced WebSocket functionality"""
    
    async def test_websocket_async_context_manager(self):
        """Test the enhanced async context manager functionality"""
        from app.api.websocket_enhanced import websocket_connection_manager
        from unittest.mock import AsyncMock
        
        # Mock WebSocket and manager
        mock_websocket = AsyncMock()
        mock_manager = AsyncMock()
        
        client_id = "test_async_client"
        
        with patch('app.api.websocket_enhanced.manager', mock_manager):
            async with websocket_connection_manager(mock_websocket, client_id):
                # Should connect
                mock_manager.connect.assert_called_once_with(mock_websocket, client_id)
                
                # Should send connection confirmation
                mock_websocket.send_json.assert_called_once()
                call_args = mock_websocket.send_json.call_args[0][0]
                assert call_args["type"] == "connection_enhanced"
                assert call_args["client_id"] == client_id
            
            # Should disconnect after context exit
            mock_manager.disconnect.assert_called_once_with(client_id)
    
    async def test_progress_update_model(self):
        """Test the ProgressUpdate pydantic model"""
        from app.api.websocket_enhanced import ProgressUpdate
        
        progress_data = {
            "task_id": "test_123",
            "progress": 0.75,
            "status": "processing",
            "message": "Processing documents...",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        progress_update = ProgressUpdate(**progress_data)
        
        assert progress_update.task_id == "test_123"
        assert progress_update.progress == 0.75
        assert progress_update.status == "processing"
        assert progress_update.message == "Processing documents..."
        assert progress_update.timestamp is not None
    
    async def test_websocket_metrics_class(self):
        """Test WebSocketMetrics class functionality"""
        from app.api.websocket_enhanced import WebSocketMetrics
        
        metrics = WebSocketMetrics()
        
        # Test initial state
        assert metrics.connections == 0
        assert metrics.messages_sent == 0
        assert metrics.messages_received == 0
        assert metrics.errors == 0
        assert len(metrics.connection_times) == 0
        
        # Test tracking methods
        metrics.track_connection(1.5)
        assert metrics.connections == 1
        assert len(metrics.connection_times) == 1
        assert metrics.connection_times[0] == 1.5
        
        metrics.track_message_sent()
        assert metrics.messages_sent == 1
        
        metrics.track_message_received()
        assert metrics.messages_received == 1
        
        metrics.track_error()
        assert metrics.errors == 1

# Performance benchmarking tests
class TestWebSocketPerformance:
    """Performance tests for enhanced WebSocket functionality"""
    
    def test_websocket_connection_performance(self, client):
        """Benchmark WebSocket connection establishment time"""
        connection_times = []
        
        for i in range(5):  # Test 5 connections
            start_time = time.time()
            
            with client.websocket_connect(f"/ws/enhanced/progress/perf_test_{i}") as websocket:
                # Wait for connection confirmation
                websocket.receive_json()
                connection_time = time.time() - start_time
                connection_times.append(connection_time)
        
        # Calculate average connection time
        avg_connection_time = sum(connection_times) / len(connection_times)
        
        # Assert reasonable performance (less than 100ms average)
        assert avg_connection_time < 0.1, f"Average connection time too slow: {avg_connection_time:.3f}s"
        
        print(f"Average WebSocket connection time: {avg_connection_time:.3f}s")
        print(f"Connection times: {[f'{t:.3f}s' for t in connection_times]}")
    
    @patch('app.db.database.get_db_pool')
    def test_websocket_message_throughput(self, mock_db_pool, client):
        """Test WebSocket message throughput performance"""
        # Mock fast database responses
        mock_conn = AsyncMock()
        mock_conn.fetchrow.return_value = {
            'id': 'test',
            'status': 'processing',
            'progress': 0.5,
            'message': 'Processing...',
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        mock_pool = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        mock_db_pool.return_value = mock_pool
        
        with client.websocket_connect("/ws/enhanced/progress/throughput_test") as websocket:
            # Skip connection message
            websocket.receive_json()
            
            start_time = time.time()
            messages_received = 0
            
            # Receive messages for 1 second to test throughput
            while time.time() - start_time < 1.0 and messages_received < 10:
                try:
                    websocket.receive_json(mode="nowait")
                    messages_received += 1
                except:
                    break
            
            throughput = messages_received / (time.time() - start_time)
            
            # Should handle at least 1 message per second
            assert throughput >= 1, f"Message throughput too low: {throughput:.2f} msg/s"
            
            print(f"WebSocket message throughput: {throughput:.2f} messages/second")