#!/usr/bin/env python3
"""
Video Processing Pipeline Analysis

This script analyzes the video processing pipeline to identify potential
causes of video data corruption and suggest improvements.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta
import json

# Add the parent directory to the path to import app modules
sys.path.append(str(Path(__file__).parent))

import asyncpg
from app.config import settings


class VideoPipelineAnalyzer:
    def __init__(self):
        self.db_url = settings.DATABASE_URL
        self.issues = []
        
    async def connect(self):
        """Connect to the database"""
        self.conn = await asyncpg.connect(self.db_url)
        
    async def disconnect(self):
        """Disconnect from the database"""
        if hasattr(self, 'conn'):
            await self.conn.close()
            
    async def analyze_processing_patterns(self):
        """Analyze video processing patterns to identify potential issues"""
        print("🔍 Analyzing Video Processing Patterns...")
        
        # Check for timing patterns in corrupted data
        timing_analysis = await self.conn.fetch("""
            SELECT 
                DATE_TRUNC('hour', created_at) as hour_bucket,
                COUNT(*) as total_videos,
                COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_videos,
                COUNT(CASE WHEN title LIKE '%Building AI Applications%' THEN 1 END) as suspicious_titles,
                AVG(EXTRACT(EPOCH FROM (updated_at - created_at))) as avg_processing_time_seconds
            FROM items 
            WHERE (type IN ('video', 'youtube', 'instagram', 'tiktok', 'twitter') 
                   OR url LIKE '%youtube%' 
                   OR platform IS NOT NULL)
              AND created_at > NOW() - INTERVAL '30 days'
            GROUP BY DATE_TRUNC('hour', created_at)
            ORDER BY hour_bucket DESC;
        """)
        
        print(f"📊 Processing patterns over last 30 days ({len(timing_analysis)} hours):")
        
        corruption_hours = 0
        for period in timing_analysis[:10]:  # Show last 10 hours
            if period['suspicious_titles'] > 0:
                corruption_hours += 1
                print(f"  ⚠️  {period['hour_bucket']}: {period['total_videos']} videos, "
                      f"{period['suspicious_titles']} suspicious, "
                      f"{period['failed_videos']} failed")
            else:
                print(f"  ✅ {period['hour_bucket']}: {period['total_videos']} videos, "
                      f"{period['failed_videos']} failed")
                      
        if corruption_hours > 0:
            self.issues.append(f"Data corruption detected in {corruption_hours} time periods")
            
    async def analyze_video_metadata_consistency(self):
        """Check consistency between video URLs and metadata"""
        print("🔍 Analyzing Video Metadata Consistency...")
        
        # Check for metadata mismatches
        metadata_issues = await self.conn.fetch("""
            SELECT 
                id,
                title,
                url,
                platform,
                metadata,
                CASE 
                    WHEN url LIKE '%youtube.com/watch?v=%' THEN 
                        SUBSTRING(url FROM 'v=([^&]+)')
                    WHEN url LIKE '%youtu.be/%' THEN 
                        SUBSTRING(url FROM 'youtu\.be/([^?&]+)')
                    ELSE 'unknown'
                END as extracted_video_id
            FROM items 
            WHERE (url LIKE '%youtube%' OR url LIKE '%youtu.be%')
              AND created_at > NOW() - INTERVAL '7 days'
            ORDER BY created_at DESC;
        """)
        
        print(f"📋 Recent YouTube videos metadata check ({len(metadata_issues)} videos):")
        
        consistency_issues = 0
        for video in metadata_issues:
            video_id = video['extracted_video_id']
            title = video['title']
            
            # Check for known problematic video IDs
            known_issues = {
                'dQw4w9WgXcQ': 'Rick Astley - Never Gonna Give You Up',
                'oHg5SJYRHA0': 'RickRoll',
                'L_jWHffIx5E': 'Sandstorm'
            }
            
            if video_id in known_issues:
                expected_content = known_issues[video_id]
                if expected_content.lower() not in title.lower():
                    consistency_issues += 1
                    print(f"  ⚠️  Video ID {video_id} has unexpected title: {title[:50]}...")
                    print(f"      Expected content related to: {expected_content}")
                else:
                    print(f"  ✅ Video ID {video_id}: Title matches expected content")
                    
        if consistency_issues > 0:
            self.issues.append(f"{consistency_issues} videos have metadata inconsistencies")
            
    async def check_processing_queue_integrity(self):
        """Check the integrity of the processing queue"""
        print("🔍 Checking Processing Queue Integrity...")
        
        # Check for stuck processing jobs
        stuck_jobs = await self.conn.fetch("""
            SELECT 
                id,
                title,
                url,
                status,
                created_at,
                updated_at,
                EXTRACT(EPOCH FROM (NOW() - updated_at)) / 3600 as hours_since_update
            FROM items 
            WHERE status IN ('processing', 'pending')
              AND (type IN ('video', 'youtube', 'instagram', 'tiktok', 'twitter') 
                   OR url LIKE '%youtube%' 
                   OR platform IS NOT NULL)
              AND updated_at < NOW() - INTERVAL '2 hours'
            ORDER BY updated_at ASC;
        """)
        
        if stuck_jobs:
            print(f"⚠️  Found {len(stuck_jobs)} potentially stuck processing jobs:")
            for job in stuck_jobs[:5]:  # Show first 5
                print(f"  • {job['title'][:40]}... (stuck for {job['hours_since_update']:.1f} hours)")
                
            self.issues.append(f"{len(stuck_jobs)} videos stuck in processing queue")
        else:
            print("✅ No stuck processing jobs found")
            
    async def analyze_error_patterns(self):
        """Analyze error patterns in video processing"""
        print("🔍 Analyzing Error Patterns...")
        
        # Check for systematic errors in backup table if it exists
        try:
            backup_analysis = await self.conn.fetch("""
                SELECT 
                    corruption_type,
                    COUNT(*) as count,
                    MIN(backup_created_at) as first_occurrence,
                    MAX(backup_created_at) as last_occurrence
                FROM corrupted_video_backup 
                GROUP BY corruption_type
                ORDER BY count DESC;
            """)
            
            if backup_analysis:
                print("📊 Corruption patterns from backup data:")
                for pattern in backup_analysis:
                    print(f"  • {pattern['corruption_type']}: {pattern['count']} occurrences")
                    print(f"    First: {pattern['first_occurrence']}, Last: {pattern['last_occurrence']}")
            else:
                print("✅ No corruption patterns in backup data")
                
        except Exception:
            print("ℹ️  No backup table found (expected for clean systems)")
            
    async def check_video_processing_service_health(self):
        """Analyze potential issues in video processing services"""
        print("🔍 Checking Video Processing Service Health...")
        
        # Look for patterns that might indicate service issues
        service_health = await self.conn.fetch("""
            WITH processing_stats AS (
                SELECT 
                    DATE(created_at) as process_date,
                    COUNT(*) as total_videos,
                    COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed,
                    COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed,
                    COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending,
                    AVG(CASE 
                        WHEN updated_at > created_at 
                        THEN EXTRACT(EPOCH FROM (updated_at - created_at))
                        ELSE NULL 
                    END) as avg_processing_time
                FROM items 
                WHERE (type IN ('video', 'youtube', 'instagram', 'tiktok', 'twitter') 
                       OR url LIKE '%youtube%' 
                       OR platform IS NOT NULL)
                  AND created_at > NOW() - INTERVAL '14 days'
                GROUP BY DATE(created_at)
            )
            SELECT 
                process_date,
                total_videos,
                completed,
                failed,
                pending,
                ROUND(avg_processing_time, 2) as avg_processing_seconds,
                ROUND(100.0 * failed / total_videos, 1) as failure_rate_percent
            FROM processing_stats
            ORDER BY process_date DESC;
        """)
        
        print("📊 Daily processing statistics (last 14 days):")
        high_failure_days = 0
        
        for day in service_health[:7]:  # Show last 7 days
            failure_rate = day['failure_rate_percent'] or 0
            if failure_rate > 20:  # More than 20% failure rate
                high_failure_days += 1
                print(f"  ⚠️  {day['process_date']}: {day['total_videos']} videos, "
                      f"{failure_rate}% failed, avg {day['avg_processing_seconds']}s")
            else:
                print(f"  ✅ {day['process_date']}: {day['total_videos']} videos, "
                      f"{failure_rate}% failed, avg {day['avg_processing_seconds']}s")
                      
        if high_failure_days > 0:
            self.issues.append(f"{high_failure_days} days had high failure rates (>20%)")
            
    async def generate_pipeline_recommendations(self):
        """Generate recommendations for improving the video processing pipeline"""
        print("\n🛠️  PIPELINE IMPROVEMENT RECOMMENDATIONS")
        print("=" * 50)
        
        recommendations = [
            "1. DATA VALIDATION: Add stricter validation when extracting video metadata",
            "2. RETRY LOGIC: Implement exponential backoff for failed video processing",
            "3. MONITORING: Add alerts for when video titles don't match URL patterns",
            "4. CACHING: Cache video metadata to avoid re-fetching corrupt data",
            "5. VERIFICATION: Add post-processing verification to catch mismatches",
            "6. ROLLBACK: Implement transaction rollback for failed processing"
        ]
        
        if self.issues:
            print("⚠️  Issues detected in pipeline:")
            for i, issue in enumerate(self.issues, 1):
                print(f"  {i}. {issue}")
            print()
            
        print("🔧 Recommended improvements:")
        for rec in recommendations:
            print(f"  {rec}")
            
        # Code-level recommendations
        print("\n💻 CODE-LEVEL FIXES:")
        code_fixes = [
            "- Add video_id validation in VideoProcessor.download_video()",
            "- Implement title/URL consistency checks before saving to database", 
            "- Add logging for all video metadata extraction steps",
            "- Create video processing transaction boundaries",
            "- Add retry mechanism for corrupted metadata extraction",
            "- Implement video content fingerprinting to detect mismatches"
        ]
        
        for fix in code_fixes:
            print(f"  {fix}")
            
    async def run_pipeline_analysis(self):
        """Run the complete pipeline analysis"""
        print("🔍 Starting Video Processing Pipeline Analysis")
        print("=" * 60)
        
        try:
            await self.connect()
            
            await self.analyze_processing_patterns()
            print()
            
            await self.analyze_video_metadata_consistency() 
            print()
            
            await self.check_processing_queue_integrity()
            print()
            
            await self.analyze_error_patterns()
            print()
            
            await self.check_video_processing_service_health()
            print()
            
            await self.generate_pipeline_recommendations()
            
        except Exception as e:
            print(f"❌ Pipeline analysis failed: {e}")
            import traceback
            traceback.print_exc()
            
        finally:
            await self.disconnect()


async def main():
    analyzer = VideoPipelineAnalyzer()
    
    try:
        await analyzer.run_pipeline_analysis()
        
    except KeyboardInterrupt:
        print("\n⏹️  Pipeline analysis interrupted by user")
    except Exception as e:
        print(f"\n❌ Pipeline analysis failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())