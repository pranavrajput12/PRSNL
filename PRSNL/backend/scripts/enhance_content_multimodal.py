#!/usr/bin/env python3
"""
Bulk Content Enhancement Script - Multimodal & NER

This script enhances existing content with:
1. Multimodal embeddings (text + image when available)
2. Enhanced NER-based tagging
3. Cross-modal content analysis
4. Metadata enrichment

Usage:
    python scripts/enhance_content_multimodal.py [--dry-run] [--batch-size 10] [--content-types image,video]
"""

import asyncio
import logging
import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

# Add the parent directory to Python path
sys.path.append(str(Path(__file__).parent.parent))

from app.db.connection import get_db_connection
from app.services.multimodal_embedding_service import multimodal_embedding_service
from app.services.ner_service import ner_service
from app.services.embedding_manager import embedding_manager
from app.services.job_persistence_service import job_persistence_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ContentEnhancer:
    """
    Bulk content enhancement with multimodal and NER capabilities.
    """
    
    def __init__(self, dry_run: bool = False, batch_size: int = 10):
        self.dry_run = dry_run
        self.batch_size = batch_size
        self.stats = {
            'processed': 0,
            'enhanced_embeddings': 0,
            'enhanced_tags': 0,
            'failed': 0,
            'skipped': 0
        }
    
    async def enhance_all_content(
        self, 
        content_types: Optional[List[str]] = None,
        force_reprocess: bool = False
    ) -> Dict[str, Any]:
        """
        Enhance all content items with multimodal embeddings and NER tags.
        
        Args:
            content_types: List of content types to process (None = all)
            force_reprocess: Whether to reprocess items that already have embeddings
            
        Returns:
            Enhancement statistics
        """
        logger.info(f"Starting bulk content enhancement (dry_run={self.dry_run})")
        logger.info(f"Content types: {content_types or 'all'}")
        
        # Initialize services
        await multimodal_embedding_service.initialize()
        await ner_service.initialize()
        
        # Get items to process
        items = await self._get_items_to_process(content_types, force_reprocess)
        logger.info(f"Found {len(items)} items to process")
        
        if not items:
            logger.info("No items to process")
            return self.stats
        
        # Process in batches
        for i in range(0, len(items), self.batch_size):
            batch = items[i:i + self.batch_size]
            await self._process_batch(batch)
            
            # Progress update
            progress = min(100, (i + len(batch)) * 100 // len(items))
            logger.info(f"Progress: {progress}% ({i + len(batch)}/{len(items)})")
        
        logger.info("Enhancement complete")
        logger.info(f"Stats: {self.stats}")
        return self.stats
    
    async def _get_items_to_process(
        self, 
        content_types: Optional[List[str]], 
        force_reprocess: bool
    ) -> List[Dict[str, Any]]:
        """Get items that need enhancement."""
        async with get_db_connection() as conn:
            # Build query conditions
            conditions = ["1=1"]
            params = []
            param_count = 1
            
            if content_types:
                conditions.append(f"type = ANY(${param_count}::text[])")
                params.append(content_types)
                param_count += 1
            
            if not force_reprocess:
                # Skip items that already have multimodal embeddings
                conditions.append("""
                    NOT EXISTS (
                        SELECT 1 FROM embeddings e 
                        WHERE e.item_id = items.id 
                        AND e.embedding_type IN ('image', 'multimodal')
                    )
                """)
            
            # Ensure we have content to work with
            conditions.append("(raw_content IS NOT NULL OR processed_content IS NOT NULL)")
            
            query = f"""
                SELECT 
                    id,
                    title,
                    raw_content,
                    processed_content,
                    type,
                    file_path,
                    thumbnail_url,
                    url,
                    tags,
                    created_at
                FROM items
                WHERE {' AND '.join(conditions)}
                ORDER BY created_at DESC
            """
            
            return await conn.fetch(query, *params)
    
    async def _process_batch(self, batch: List[Dict[str, Any]]):
        """Process a batch of items."""
        tasks = [self._process_item(item) for item in batch]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Batch processing error: {result}")
                self.stats['failed'] += 1
    
    async def _process_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single item."""
        item_id = str(item['id'])
        logger.debug(f"Processing item {item_id}: {item['title']}")
        
        try:
            # Create job for tracking
            job_id = None
            if not self.dry_run:
                job_id = await job_persistence_service.create_job(
                    job_type="content_enhancement",
                    input_data={
                        "item_id": item_id,
                        "enhancement_type": "multimodal_ner"
                    },
                    metadata={"script": "enhance_content_multimodal.py"}
                )
                
                await job_persistence_service.update_job_status(
                    job_id, "processing", progress=0, stage="analysis"
                )
            
            enhancement_result = {
                'item_id': item_id,
                'enhanced_embeddings': False,
                'enhanced_tags': False,
                'new_embeddings': [],
                'new_tags': []
            }
            
            # Get content text
            content_text = item['processed_content'] or item['raw_content'] or ""
            
            # 1. Create text embedding if not exists
            if content_text:
                text_embedding_result = await embedding_manager.create_embedding(
                    item_id, 
                    f"{item['title']} {content_text[:1000]}"
                )
                if text_embedding_result and not self.dry_run:
                    enhancement_result['new_embeddings'].append('text')
                    enhancement_result['enhanced_embeddings'] = True
            
            # 2. Create image embedding if image available
            if item['file_path'] or item['thumbnail_url']:
                image_path = item['file_path'] or item['thumbnail_url']
                if image_path and Path(image_path).exists():
                    image_embedding_result = await embedding_manager.create_image_embedding(
                        item_id, 
                        image_path=image_path
                    )
                    if image_embedding_result and not self.dry_run:
                        enhancement_result['new_embeddings'].append('image')
                        enhancement_result['enhanced_embeddings'] = True
            
            # 3. Create multimodal embedding if both text and image
            if content_text and (item['file_path'] or item['thumbnail_url']):
                image_path = item['file_path'] or item['thumbnail_url']
                if image_path and Path(image_path).exists():
                    multimodal_result = await embedding_manager.create_multimodal_embedding(
                        item_id,
                        text=content_text[:500],  # Limit text for multimodal
                        image_path=image_path
                    )
                    if multimodal_result and not self.dry_run:
                        enhancement_result['new_embeddings'].append('multimodal')
                        enhancement_result['enhanced_embeddings'] = True
            
            if job_id:
                await job_persistence_service.update_job_status(
                    job_id, "processing", progress=50, stage="ner_analysis"
                )
            
            # 4. Enhance tags with NER
            if content_text:
                entities = await ner_service.extract_entities(
                    content_text, 
                    include_technical=True
                )
                
                current_tags = item.get('tags', []) or []
                enhanced_tags = await ner_service.enhance_tags(
                    current_tags, 
                    entities, 
                    max_new_tags=8
                )
                
                # Update tags if enhanced
                if len(enhanced_tags) > len(current_tags):
                    if not self.dry_run:
                        await self._update_item_tags(item_id, enhanced_tags)
                    
                    enhancement_result['enhanced_tags'] = True
                    enhancement_result['new_tags'] = [
                        tag for tag in enhanced_tags if tag not in current_tags
                    ]
            
            if job_id:
                await job_persistence_service.update_job_status(
                    job_id, "processing", progress=90, stage="finalization"
                )
            
            # 5. Update metadata
            if not self.dry_run and (enhancement_result['enhanced_embeddings'] or enhancement_result['enhanced_tags']):
                await self._update_item_metadata(item_id, enhancement_result)
            
            # Complete job
            if job_id:
                await job_persistence_service.save_job_result(
                    job_id, enhancement_result, "completed"
                )
            
            # Update stats
            self.stats['processed'] += 1
            if enhancement_result['enhanced_embeddings']:
                self.stats['enhanced_embeddings'] += 1
            if enhancement_result['enhanced_tags']:
                self.stats['enhanced_tags'] += 1
            
            logger.debug(f"Enhanced item {item_id}: {enhancement_result}")
            return enhancement_result
            
        except Exception as e:
            logger.error(f"Error processing item {item_id}: {e}")
            self.stats['failed'] += 1
            
            # Fail job if exists
            if job_id:
                await job_persistence_service.update_job_status(
                    job_id, "failed", error_message=str(e)
                )
            
            return {'item_id': item_id, 'error': str(e)}
    
    async def _update_item_tags(self, item_id: str, tags: List[str]):
        """Update item tags in database."""
        async with get_db_connection() as conn:
            await conn.execute("""
                UPDATE items 
                SET tags = $1, updated_at = NOW()
                WHERE id = $2
            """, tags, item_id)
    
    async def _update_item_metadata(self, item_id: str, enhancement_result: Dict[str, Any]):
        """Update item metadata with enhancement info."""
        metadata = {
            'enhanced_at': datetime.utcnow().isoformat(),
            'enhancement_version': '1.0',
            'embeddings_created': enhancement_result['new_embeddings'],
            'tags_enhanced': enhancement_result['enhanced_tags'],
            'new_tag_count': len(enhancement_result['new_tags'])
        }
        
        async with get_db_connection() as conn:
            await conn.execute("""
                UPDATE items 
                SET metadata = metadata || $1::jsonb, updated_at = NOW()
                WHERE id = $2
            """, json.dumps(metadata), item_id)

async def main():
    """Main script entry point."""
    parser = argparse.ArgumentParser(description='Enhance content with multimodal embeddings and NER')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without making changes')
    parser.add_argument('--batch-size', type=int, default=10, help='Number of items to process concurrently')
    parser.add_argument('--content-types', type=str, help='Comma-separated list of content types to process')
    parser.add_argument('--force', action='store_true', help='Reprocess items that already have embeddings')
    
    args = parser.parse_args()
    
    # Parse content types
    content_types = None
    if args.content_types:
        content_types = [t.strip() for t in args.content_types.split(',')]
    
    enhancer = ContentEnhancer(dry_run=args.dry_run, batch_size=args.batch_size)
    
    try:
        stats = await enhancer.enhance_all_content(
            content_types=content_types,
            force_reprocess=args.force
        )
        
        print("\n" + "="*50)
        print("ENHANCEMENT COMPLETE")
        print("="*50)
        print(f"Processed: {stats['processed']}")
        print(f"Enhanced embeddings: {stats['enhanced_embeddings']}")
        print(f"Enhanced tags: {stats['enhanced_tags']}")
        print(f"Failed: {stats['failed']}")
        print(f"Skipped: {stats['skipped']}")
        
        if args.dry_run:
            print("\n⚠️  DRY RUN MODE - No changes were made")
        
    except KeyboardInterrupt:
        logger.info("Enhancement interrupted by user")
    except Exception as e:
        logger.error(f"Enhancement failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())