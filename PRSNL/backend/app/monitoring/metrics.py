from prometheus_client import Counter, Gauge, Histogram

# Define metrics for video operations
VIDEO_CAPTURE_REQUESTS = Counter(
    'video_capture_requests_total', 
    'Total number of video capture requests',
    ['status'] # success, validation_failed, internal_error
)

VIDEO_DOWNLOAD_DURATION_SECONDS = Histogram(
    'video_download_duration_seconds',
    'Duration of video downloads in seconds',
    ['platform', 'outcome'] # success, failed
)

VIDEO_DOWNLOAD_OUTCOMES = Counter(
    'video_download_outcomes_total',
    'Total number of video download outcomes',
    ['platform', 'outcome'] # success, failed
)

VIDEO_PROCESSING_DURATION_SECONDS = Histogram(
    'video_processing_duration_seconds',
    'Duration of video processing (compression, thumbnail) in seconds',
    ['outcome'] # success, failed
)

STORAGE_USAGE_BYTES = Gauge(
    'storage_usage_bytes',
    'Current storage usage in bytes',
    ['type'] # total, videos, thumbnails, temp
)

# Health check metric (example)
HEALTH_CHECK_STATUS = Gauge(
    'health_check_status',
    'Status of the application health check (1=up, 0=down)'
)