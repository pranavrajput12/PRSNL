import logging
import time
from typing import Any, Dict

logger = logging.getLogger(__name__)

class MetricsService:
    def __init__(self):
        self.api_latencies = {}
        self.db_query_latencies = {}
        self.ai_service_latencies = {}
        self.resource_usage = {}

    def record_api_latency(self, endpoint: str, duration: float):
        self.api_latencies.setdefault(endpoint, []).append(duration)
        logger.debug(f"Recorded API latency for {endpoint}: {duration:.4f}s")

    def record_db_query_latency(self, query_name: str, duration: float):
        self.db_query_latencies.setdefault(query_name, []).append(duration)
        logger.debug(f"Recorded DB query latency for {query_name}: {duration:.4f}s")

    def record_ai_service_latency(self, service_name: str, duration: float):
        self.ai_service_latencies.setdefault(service_name, []).append(duration)
        logger.debug(f"Recorded AI service latency for {service_name}: {duration:.4f}s")

    def update_resource_usage(self, cpu_percent: float, memory_percent: float):
        self.resource_usage["cpu_percent"] = cpu_percent
        self.resource_usage["memory_percent"] = memory_percent
        logger.debug(f"Updated resource usage: CPU={cpu_percent}%, Memory={memory_percent}%")

    def get_metrics_summary(self) -> Dict[str, Any]:
        summary = {
            "api_latencies": {},
            "db_query_latencies": {},
            "ai_service_latencies": {},
            "resource_usage": self.resource_usage
        }

        for endpoint, latencies in self.api_latencies.items():
            if latencies:
                summary["api_latencies"][endpoint] = {
                    "avg_latency": sum(latencies) / len(latencies),
                    "min_latency": min(latencies),
                    "max_latency": max(latencies),
                    "count": len(latencies)
                }

        for query_name, latencies in self.db_query_latencies.items():
            if latencies:
                summary["db_query_latencies"][query_name] = {
                    "avg_latency": sum(latencies) / len(latencies),
                    "min_latency": min(latencies),
                    "max_latency": max(latencies),
                    "count": len(latencies)
                }
        
        for service_name, latencies in self.ai_service_latencies.items():
            if latencies:
                summary["ai_service_latencies"][service_name] = {
                    "avg_latency": sum(latencies) / len(latencies),
                    "min_latency": min(latencies),
                    "max_latency": max(latencies),
                    "count": len(latencies)
                }

        return summary

# Global instance
metrics_service = MetricsService()
