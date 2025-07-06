from prometheus_client import Gauge, Counter, Histogram

# Define Prometheus metrics

# Counter for total video capture requests
VIDEO_CAPTURE_REQUESTS = Counter(
    'prsnl_video_capture_requests_total', 
    'Total number of video capture requests',
    ['status'] # success, validation_failed, internal_error
)

# Histogram for video download duration
VIDEO_DOWNLOAD_DURATION_SECONDS = Histogram(
    'prsnl_video_download_duration_seconds', 
    'Duration of video downloads in seconds',
    ['platform']
)

# Counter for video download outcomes
VIDEO_DOWNLOAD_OUTCOMES = Counter(
    'prsnl_video_download_outcomes_total', 
    'Total number of video download outcomes',
    ['platform', 'outcome'] # success, failed, skipped (e.g., too large)
)

# Histogram for video processing duration (compression, thumbnail generation)
VIDEO_PROCESSING_DURATION_SECONDS = Histogram(
    'prsnl_video_processing_duration_seconds', 
    'Duration of video processing (compression, thumbnail) in seconds',
    ['outcome'] # success, failed
)

# Gauge for current storage usage (managed files)
STORAGE_USAGE_BYTES = Gauge(
    'prsnl_storage_usage_bytes', 
    'Current storage usage for managed media files in bytes',
    ['type'] # videos, thumbnails, temp
)

# Counter for orphaned file cleanup operations
ORPHANED_FILE_CLEANUP_TOTAL = Counter(
    'prsnl_orphaned_file_cleanup_total', 
    'Total number of orphaned file cleanup operations',
    ['status'] # success, failed
)

# Counter for temporary file cleanup operations
TEMP_FILE_CLEANUP_TOTAL = Counter(
    'prsnl_temp_file_cleanup_total', 
    'Total number of temporary file cleanup operations',
    ['status'] # success, failed
)

# Gauge for video processing queue size (if using a separate queue system)
VIDEO_PROCESSING_QUEUE_SIZE = Gauge(
    'prsnl_video_processing_queue_size', 
    'Current size of the video processing queue'
)
