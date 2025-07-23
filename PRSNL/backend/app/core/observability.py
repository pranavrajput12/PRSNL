"""
OpenTelemetry Observability Setup for PRSNL

Provides comprehensive monitoring with traces, metrics, and logs.
Two-line drop-in instrumentation for FastAPI application.
"""

import logging
import os
from contextlib import asynccontextmanager
from typing import Optional

# OpenTelemetry imports
from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.instrumentation.aiohttp_client import AioHttpClientInstrumentor
from opentelemetry.instrumentation.asyncpg import AsyncPGInstrumentor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# Prometheus FastAPI instrumentator
from prometheus_fastapi_instrumentator import Instrumentator

logger = logging.getLogger(__name__)


class ObservabilityManager:
    """
    Manages OpenTelemetry observability setup for PRSNL.
    
    Provides traces, metrics, and structured logging with minimal configuration.
    """
    
    def __init__(self):
        self.service_name = "prsnl-knowledge-management"
        self.service_version = "2.1.0"
        self.environment = os.getenv("ENVIRONMENT", "development")
        
        # OTLP endpoints (for Grafana/Loki integration)
        self.otlp_traces_endpoint = os.getenv("OTLP_TRACES_ENDPOINT", "http://localhost:4317")
        self.otlp_metrics_endpoint = os.getenv("OTLP_METRICS_ENDPOINT", "http://localhost:4317")
        
        # Prometheus metrics endpoint
        self.prometheus_port = int(os.getenv("PROMETHEUS_PORT", "8001"))
        
        self.instrumentator = None
        self.tracer = None
        self.meter = None
        
    def setup_resource(self) -> Resource:
        """Create OpenTelemetry resource with service information."""
        return Resource.create({
            SERVICE_NAME: self.service_name,
            SERVICE_VERSION: self.service_version,
            "environment": self.environment,
            "service.namespace": "prsnl",
            "service.instance.id": os.getenv("POD_NAME", "local-instance"),
            "deployment.environment": self.environment
        })
    
    def setup_tracing(self, resource: Resource):
        """Configure OpenTelemetry tracing."""
        try:
            # Create tracer provider
            tracer_provider = TracerProvider(resource=resource)
            trace.set_tracer_provider(tracer_provider)
            
            # Add OTLP exporter for traces (to Grafana Tempo via Loki)
            if self.otlp_traces_endpoint:
                otlp_exporter = OTLPSpanExporter(
                    endpoint=self.otlp_traces_endpoint,
                    insecure=True  # Use TLS in production
                )
                span_processor = BatchSpanProcessor(otlp_exporter)
                tracer_provider.add_span_processor(span_processor)
                logger.info(f"✅ OTLP traces configured: {self.otlp_traces_endpoint}")
            
            # Get tracer for manual instrumentation
            self.tracer = trace.get_tracer(__name__)
            logger.info("✅ OpenTelemetry tracing initialized")
            
        except Exception as e:
            logger.error(f"Failed to setup tracing: {e}")
    
    def setup_metrics(self, resource: Resource):
        """Configure OpenTelemetry metrics."""
        try:
            readers = []
            
            # Prometheus metrics reader (for Grafana)
            prometheus_reader = PrometheusMetricReader()
            readers.append(prometheus_reader)
            
            # OTLP metrics exporter (optional)
            if self.otlp_metrics_endpoint:
                otlp_metric_exporter = OTLPMetricExporter(
                    endpoint=self.otlp_metrics_endpoint,
                    insecure=True
                )
                otlp_reader = PeriodicExportingMetricReader(
                    exporter=otlp_metric_exporter,
                    export_interval_millis=30000  # Export every 30 seconds
                )
                readers.append(otlp_reader)
                logger.info(f"✅ OTLP metrics configured: {self.otlp_metrics_endpoint}")
            
            # Create meter provider
            meter_provider = MeterProvider(
                resource=resource,
                metric_readers=readers
            )
            metrics.set_meter_provider(meter_provider)
            
            # Get meter for custom metrics
            self.meter = metrics.get_meter(__name__)
            logger.info("✅ OpenTelemetry metrics initialized")
            
        except Exception as e:
            logger.error(f"Failed to setup metrics: {e}")
    
    def setup_auto_instrumentation(self):
        """Configure automatic instrumentation for common libraries."""
        try:
            # FastAPI instrumentation
            FastAPIInstrumentor.instrument()
            logger.info("✅ FastAPI auto-instrumentation enabled")
            
            # Database instrumentation
            AsyncPGInstrumentor().instrument()
            logger.info("✅ AsyncPG auto-instrumentation enabled")
            
            # HTTP client instrumentation
            AioHttpClientInstrumentor().instrument()
            RequestsInstrumentor().instrument()
            logger.info("✅ HTTP client auto-instrumentation enabled")
            
        except Exception as e:
            logger.error(f"Failed to setup auto-instrumentation: {e}")
    
    def setup_prometheus_fastapi(self, app):
        """Setup Prometheus FastAPI instrumentator for detailed metrics."""
        try:
            self.instrumentator = Instrumentator(
                should_group_status_codes=False,
                should_ignore_untemplated=True,
                should_respect_env_var=True,
                should_instrument_requests_inprogress=True,
                excluded_handlers=["/health", "/metrics", "/docs", "/openapi.json"],
                env_var_name="ENABLE_METRICS",
                inprogress_name="prsnl_requests_inprogress",
                inprogress_labels=True,
            )
            
            # Add custom metrics
            self.instrumentator.add(
                self._track_response_size_by_endpoint()
            ).add(
                self._track_database_queries()
            ).add(
                self._track_ai_processing_time()
            )
            
            # Instrument the app
            self.instrumentator.instrument(app)
            logger.info("✅ Prometheus FastAPI instrumentator configured")
            
        except Exception as e:
            logger.error(f"Failed to setup Prometheus FastAPI instrumentator: {e}")
    
    def _track_response_size_by_endpoint(self):
        """Custom metric: Track response sizes by endpoint."""
        from prometheus_client import Histogram
        
        histogram = Histogram(
            "prsnl_response_size_bytes",
            "Response size in bytes by endpoint",
            ["method", "endpoint", "status_code"]
        )
        
        def instrumentation(info):
            if hasattr(info.response, "headers"):
                content_length = info.response.headers.get("content-length")
                if content_length:
                    histogram.labels(
                        method=info.method,
                        endpoint=info.modified_handler,
                        status_code=info.modified_status
                    ).observe(int(content_length))
        
        return instrumentation
    
    def _track_database_queries(self):
        """Custom metric: Track database query performance."""
        from prometheus_client import Counter, Histogram
        
        query_counter = Counter(
            "prsnl_database_queries_total",
            "Total database queries",
            ["query_type", "status"]
        )
        
        query_duration = Histogram(
            "prsnl_database_query_duration_seconds",
            "Database query duration",
            ["query_type"]
        )
        
        def instrumentation(info):
            # This would be enhanced to track actual DB queries
            # For now, it's a placeholder for the pattern
            pass
        
        return instrumentation
    
    def _track_ai_processing_time(self):
        """Custom metric: Basic AI endpoint tracking - detailed metrics handled by Langfuse."""
        from prometheus_client import Counter
        
        # Simplified AI tracking - Langfuse handles detailed metrics
        ai_counter = Counter(
            "prsnl_ai_requests_total",
            "Total AI requests (detailed metrics in Langfuse)",
            ["endpoint", "status"]
        )
        
        def instrumentation(info):
            # Basic endpoint tracking only
            if any(path in info.modified_handler for path in ["/ai", "/transcribe", "/summarize"]):
                ai_counter.labels(
                    endpoint=info.modified_handler,
                    status="success" if info.modified_status < 400 else "error"
                ).inc()
        
        return instrumentation
    
    def create_custom_metrics(self):
        """Create custom business metrics for PRSNL."""
        if not self.meter:
            return
        
        try:
            # Content processing metrics
            self.content_processed_counter = self.meter.create_counter(
                name="prsnl_content_processed_total",
                description="Total content items processed",
                unit="1"
            )
            
            self.processing_duration = self.meter.create_histogram(
                name="prsnl_processing_duration",
                description="Content processing duration",
                unit="s"
            )
            
            # Knowledge graph metrics
            self.relationships_created = self.meter.create_counter(
                name="prsnl_relationships_created_total",
                description="Total relationships created",
                unit="1"
            )
            
            # Search metrics
            self.search_queries = self.meter.create_counter(
                name="prsnl_search_queries_total",
                description="Total search queries",
                unit="1"
            )
            
            self.search_latency = self.meter.create_histogram(
                name="prsnl_search_latency",
                description="Search query latency",
                unit="s"
            )
            
            logger.info("✅ Custom metrics created")
            
        except Exception as e:
            logger.error(f"Failed to create custom metrics: {e}")
    
    def expose_metrics_endpoint(self, app):
        """Expose metrics endpoint for Prometheus scraping."""
        try:
            self.instrumentator.expose(app, endpoint="/metrics")
            logger.info("✅ Metrics endpoint exposed at /metrics")
        except Exception as e:
            logger.error(f"Failed to expose metrics endpoint: {e}")
    
    def initialize_observability(self, app):
        """
        Complete observability setup - the "two-line drop-in" function.
        
        Call this from your FastAPI app initialization.
        """
        logger.info("🔍 Initializing PRSNL observability...")
        
        # Create resource
        resource = self.setup_resource()
        
        # Setup tracing
        self.setup_tracing(resource)
        
        # Setup metrics
        self.setup_metrics(resource)
        
        # Setup auto-instrumentation
        self.setup_auto_instrumentation()
        
        # Setup Prometheus FastAPI instrumentator
        self.setup_prometheus_fastapi(app)
        
        # Create custom metrics
        self.create_custom_metrics()
        
        # Expose metrics endpoint
        self.expose_metrics_endpoint(app)
        
        logger.info("✅ PRSNL observability fully initialized")
        logger.info(f"  🔍 Traces: {self.otlp_traces_endpoint}")
        logger.info(f"  📊 Metrics: /metrics endpoint")
        logger.info(f"  🏷️ Service: {self.service_name} v{self.service_version}")
    
    @asynccontextmanager
    async def trace_operation(self, operation_name: str, **attributes):
        """Context manager for manual tracing of operations."""
        if not self.tracer:
            yield None
            return
        
        with self.tracer.start_as_current_span(operation_name) as span:
            # Add attributes
            for key, value in attributes.items():
                span.set_attribute(key, value)
            
            try:
                yield span
            except Exception as e:
                span.record_exception(e)
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                raise
    
    def record_content_processed(self, content_type: str, processing_time: float):
        """Record content processing metrics."""
        if hasattr(self, 'content_processed_counter'):
            self.content_processed_counter.add(1, {"content_type": content_type})
        
        if hasattr(self, 'processing_duration'):
            self.processing_duration.record(processing_time, {"content_type": content_type})
    
    def record_search_query(self, query_type: str, latency: float, results_count: int):
        """Record search metrics."""
        if hasattr(self, 'search_queries'):
            self.search_queries.add(1, {"query_type": query_type})
        
        if hasattr(self, 'search_latency'):
            self.search_latency.record(latency, {
                "query_type": query_type,
                "results_count_bucket": self._get_results_bucket(results_count)
            })
    
    def _get_results_bucket(self, count: int) -> str:
        """Categorize search results count into buckets."""
        if count == 0:
            return "zero"
        elif count <= 10:
            return "1-10"
        elif count <= 50:
            return "11-50"
        elif count <= 100:
            return "51-100"
        else:
            return "100+"


# Global observability manager instance
observability = ObservabilityManager()


def instrument_fastapi_app(app):
    """
    Two-line drop-in function to instrument FastAPI app with observability.
    
    Usage:
        from app.core.observability import instrument_fastapi_app
        instrument_fastapi_app(app)
    """
    observability.initialize_observability(app)
    return app