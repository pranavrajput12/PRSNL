#!/usr/bin/env python3
"""
Video Data Corruption Analysis Script

This script runs the SQL investigation queries and provides analysis
of video data corruption issues in the database.
"""

import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime
import json

# Add the parent directory to the path to import app modules
sys.path.append(str(Path(__file__).parent))

import asyncpg
from app.config import settings


class VideoCorruptionAnalyzer:
    def __init__(self):
        self.db_url = settings.DATABASE_URL
        self.results = {}
        
    async def connect(self):
        """Connect to the database"""
        self.conn = await asyncpg.connect(self.db_url)
        
    async def disconnect(self):
        """Disconnect from the database"""
        if hasattr(self, 'conn'):
            await self.conn.close()
            
    async def run_analysis(self):
        """Run the complete video corruption analysis"""
        print("🔍 Starting Video Data Corruption Analysis")
        print("=" * 50)
        
        # Read the SQL file
        sql_file = Path(__file__).parent / "investigate_video_corruption.sql"
        
        if not sql_file.exists():
            print(f"❌ SQL file not found: {sql_file}")
            return
            
        with open(sql_file, 'r') as f:
            sql_content = f.read()
            
        # Split queries by double line breaks and filter out comments
        queries = []
        current_query = []
        
        for line in sql_content.split('\n'):
            line = line.strip()
            
            # Skip empty lines and pure comment lines at start
            if not line or line.startswith('--'):
                if current_query:
                    current_query.append(line)
                continue
                
            current_query.append(line)
            
            # If line ends with semicolon, we have a complete query
            if line.endswith(';'):
                query_text = '\n'.join(current_query)
                if 'SELECT' in query_text.upper():
                    queries.append(query_text)
                current_query = []
                
        print(f"📊 Found {len(queries)} analysis queries to execute")
        print()
        
        try:
            await self.connect()
            
            for i, query in enumerate(queries, 1):
                try:
                    print(f"🔍 Running Analysis {i}/{len(queries)}...")
                    
                    # Execute query
                    rows = await self.conn.fetch(query)
                    
                    if rows:
                        # Get the analysis type from the first row
                        analysis_type = rows[0].get('analysis_type', f'Analysis {i}')
                        print(f"📋 {analysis_type}")
                        print("-" * 40)
                        
                        # Store results
                        self.results[analysis_type] = []
                        
                        if len(rows) > 0:
                            # Print results
                            for row in rows[:10]:  # Limit to first 10 results
                                row_dict = dict(row)
                                self.results[analysis_type].append(row_dict)
                                
                                # Format output based on analysis type
                                if 'analysis_type' in row_dict:
                                    del row_dict['analysis_type']
                                    
                                if analysis_type == 'Video Count by Type and Status':
                                    print(f"  • {row_dict['type']:<15} {row_dict['status']:<10} Count: {row_dict['count']}")
                                    
                                elif 'Suspicious Title/URL Mismatches' in analysis_type:
                                    print(f"  • ID: {row_dict['id']}")
                                    print(f"    Title: {row_dict['title'][:80]}...")
                                    print(f"    URL: {row_dict['url'][:80]}...")
                                    print(f"    Mismatch: {row_dict['mismatch_type']}")
                                    print()
                                    
                                elif 'Duplicate Videos' in analysis_type:
                                    if 'duplicate_count' in row_dict:
                                        print(f"  • Found {row_dict['duplicate_count']} duplicates:")
                                        if 'titles' in row_dict:
                                            titles = row_dict['titles'].split(' | ')
                                            for j, title in enumerate(titles[:3]):
                                                print(f"    {j+1}. {title[:60]}...")
                                        print()
                                        
                                elif 'Missing Thumbnails' in analysis_type:
                                    print(f"  • {row_dict['title'][:50]}...")
                                    print(f"    Platform: {row_dict['platform']}, Status: {row_dict['status']}")
                                    print(f"    URL: {row_dict['url'][:60]}...")
                                    print()
                                    
                                elif 'Rick Astley' in analysis_type:
                                    print(f"  • ID: {row_dict['id']}")
                                    print(f"    Title: {row_dict['title']}")
                                    print(f"    URL: {row_dict['url'][:80]}...")
                                    print(f"    Indicator: {row_dict['rick_astley_indicator']}")
                                    print()
                                    
                                elif 'Summary' in analysis_type:
                                    for key, value in row_dict.items():
                                        print(f"  • {key.replace('_', ' ').title()}: {value}")
                                        
                                else:
                                    # Generic output for other analyses
                                    print(f"  • {json.dumps(row_dict, indent=4, default=str)}")
                                    
                            if len(rows) > 10:
                                print(f"  ... and {len(rows) - 10} more results")
                                
                        else:
                            print("  ✅ No issues found")
                            
                    else:
                        print("  ✅ No results returned")
                        
                    print()
                    
                except Exception as e:
                    print(f"❌ Error running query {i}: {e}")
                    print()
                    
        except Exception as e:
            print(f"❌ Database connection error: {e}")
            
        finally:
            await self.disconnect()
            
    def generate_cleanup_recommendations(self):
        """Generate recommendations for cleaning up the corrupted data"""
        print("\n🛠️  DATA CLEANUP RECOMMENDATIONS")
        print("=" * 50)
        
        # Analyze results and provide recommendations
        recommendations = []
        
        # Check for duplicates
        duplicate_analyses = [k for k in self.results.keys() if 'Duplicate' in k]
        if any(self.results.get(k) for k in duplicate_analyses):
            recommendations.append(
                "1. REMOVE DUPLICATES: Run deduplication queries to merge or remove duplicate video entries"
            )
            
        # Check for mismatches
        mismatch_analyses = [k for k in self.results.keys() if 'Mismatch' in k]
        if any(self.results.get(k) for k in mismatch_analyses):
            recommendations.append(
                "2. FIX MISMATCHES: Update platform, title, and thumbnail_url fields to match actual video content"
            )
            
        # Check for missing thumbnails
        thumbnail_analyses = [k for k in self.results.keys() if 'Thumbnail' in k]
        if any(self.results.get(k) for k in thumbnail_analyses):
            recommendations.append(
                "3. REGENERATE THUMBNAILS: Re-process videos to generate proper thumbnails"
            )
            
        # Check for Rick Astley issue
        rick_analyses = [k for k in self.results.keys() if 'Rick Astley' in k]
        if any(self.results.get(k) for k in rick_analyses):
            recommendations.append(
                "4. FIX RICK ASTLEY CORRUPTION: Specifically address the Rick Astley video with wrong title"
            )
            
        if recommendations:
            for rec in recommendations:
                print(f"  {rec}")
                print()
        else:
            print("  ✅ No major corruption issues detected!")
            
        # Provide SQL cleanup queries
        print("\n🔧 CLEANUP SQL QUERIES")
        print("=" * 30)
        
        cleanup_queries = [
            "-- Remove exact duplicates (same URL and title)",
            """DELETE FROM items a USING items b 
WHERE a.id > b.id 
  AND a.url = b.url 
  AND a.title = b.title 
  AND a.url IS NOT NULL;""",
  
            "\n-- Fix platform field based on URL",
            """UPDATE items SET platform = CASE
    WHEN url LIKE '%youtube%' OR url LIKE '%youtu.be%' THEN 'youtube'
    WHEN url LIKE '%instagram%' THEN 'instagram'  
    WHEN url LIKE '%tiktok%' THEN 'tiktok'
    WHEN url LIKE '%twitter%' OR url LIKE '%x.com%' THEN 'twitter'
    ELSE platform
END
WHERE platform IS NULL AND url IS NOT NULL;""",

            "\n-- Mark corrupted entries for reprocessing", 
            """UPDATE items SET status = 'pending'
WHERE id IN (
    SELECT id FROM items 
    WHERE (url LIKE '%rick%astley%' OR url LIKE '%never%gonna%give%you%up%')
      AND title LIKE '%Building AI Applications Tutorial%'
);""",

            "\n-- Remove entries with NULL URLs and titles",
            """DELETE FROM items 
WHERE (url IS NULL OR url = '') 
  AND (title IS NULL OR title = '')
  AND type IN ('video', 'youtube', 'instagram', 'tiktok', 'twitter');"""
        ]
        
        for query in cleanup_queries:
            print(query)
            
    async def save_results(self):
        """Save analysis results to a file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = Path(__file__).parent / f"video_corruption_analysis_{timestamp}.json"
        
        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
            
        print(f"\n📁 Results saved to: {output_file}")


async def main():
    analyzer = VideoCorruptionAnalyzer()
    
    try:
        await analyzer.run_analysis()
        analyzer.generate_cleanup_recommendations()
        await analyzer.save_results()
        
    except KeyboardInterrupt:
        print("\n⏹️  Analysis interrupted by user")
    except Exception as e:
        print(f"\n❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())