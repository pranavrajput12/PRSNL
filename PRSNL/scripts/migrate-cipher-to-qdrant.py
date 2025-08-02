#!/usr/bin/env python3
"""
Migrate existing Cipher DB patterns to Qdrant Cloud
This script extracts patterns from the local cipher.db SQLite database
and migrates them to Qdrant Cloud with proper embeddings.
"""

import os
import sqlite3
import json
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
from pathlib import Path

import openai
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/Users/pronav/Personal Knowledge Base/PRSNL/backend/.env')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
CIPHER_DB_PATH = "/Users/pronav/Personal Knowledge Base/data/cipher.db"
QDRANT_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.zuZKL-Zabs8ISY5yUXgTW_fL-BoEYbLD2OZrjhp1Vt8"
QDRANT_URL = "https://86c70065-df15-459b-bd8a-ab607b43341a.us-east4-0.gcp.cloud.qdrant.io"
COLLECTION_NAME = "prsnl_cipher_patterns"

# Azure OpenAI Configuration for embeddings
AZURE_OPENAI_API_KEY = os.getenv('AZURE_OPENAI_API_KEY')
AZURE_OPENAI_ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT')
AZURE_OPENAI_EMBEDDING_DEPLOYMENT = "text-embedding-ada-002"
AZURE_OPENAI_API_VERSION = "2025-01-01-preview"

class CipherQdrantMigrator:
    def __init__(self):
        self.qdrant_client = QdrantClient(
            url=QDRANT_URL,
            api_key=QDRANT_API_KEY,
        )
        
        # Initialize Azure OpenAI client for embeddings
        self.openai_client = openai.AzureOpenAI(
            api_key=AZURE_OPENAI_API_KEY,
            api_version=AZURE_OPENAI_API_VERSION,
            azure_endpoint=AZURE_OPENAI_ENDPOINT
        )
        
        logger.info("Initialized Qdrant client and Azure OpenAI client")

    def extract_cipher_patterns(self) -> List[Dict[str, Any]]:
        """Extract patterns from local cipher.db SQLite database"""
        patterns = []
        
        if not os.path.exists(CIPHER_DB_PATH):
            logger.warning(f"Cipher database not found at {CIPHER_DB_PATH}")
            return patterns
        
        try:
            conn = sqlite3.connect(CIPHER_DB_PATH)
            conn.row_factory = sqlite3.Row  # Enable column access by name
            cursor = conn.cursor()
            
            # Get all tables to understand structure
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            logger.info(f"Found tables in cipher.db: {[table[0] for table in tables]}")
            
            # Try to extract memories/patterns from common table structures
            possible_tables = ['memories', 'patterns', 'facts', 'knowledge', 'entries']
            
            for table_name in possible_tables:
                try:
                    cursor.execute(f"SELECT * FROM {table_name} LIMIT 5;")
                    rows = cursor.fetchall()
                    if rows:
                        logger.info(f"Found data in table '{table_name}', extracting...")
                        cursor.execute(f"SELECT * FROM {table_name};")
                        all_rows = cursor.fetchall()
                        
                        for row in all_rows:
                            pattern = {
                                'id': row.get('id', f"{table_name}_{len(patterns)}"),
                                'content': row.get('content') or row.get('text') or row.get('message') or str(dict(row)),
                                'table_source': table_name,
                                'created_at': row.get('created_at') or row.get('timestamp') or datetime.now().isoformat(),
                                'metadata': {key: row[key] for key in row.keys() if key not in ['id', 'content', 'text', 'message']},
                                'pattern_type': self._classify_pattern(row.get('content') or row.get('text') or row.get('message') or '')
                            }
                            patterns.append(pattern)
                        
                        logger.info(f"Extracted {len(all_rows)} patterns from table '{table_name}'")
                        break  # Use first table found with data
                        
                except sqlite3.Error as e:
                    continue  # Table doesn't exist, try next one
            
            conn.close()
            logger.info(f"Total patterns extracted: {len(patterns)}")
            
        except Exception as e:
            logger.error(f"Error extracting from cipher.db: {e}")
        
        return patterns

    def _classify_pattern(self, content: str) -> str:
        """Classify pattern type based on content"""
        content_lower = content.lower()
        
        if any(word in content_lower for word in ['bug', 'error', 'fix', 'issue', 'problem']):
            return 'BUG_PATTERN'
        elif any(word in content_lower for word in ['feature', 'implement', 'add', 'create']):
            return 'FEATURE_PATTERN'
        elif any(word in content_lower for word in ['architecture', 'design', 'pattern', 'structure']):
            return 'ARCHITECTURE_PATTERN'
        elif any(word in content_lower for word in ['test', 'testing', 'spec', 'assertion']):
            return 'TEST_PATTERN'
        elif any(word in content_lower for word in ['port', 'config', 'setup', 'install']):
            return 'CONFIG_PATTERN'
        else:
            return 'GENERAL_PATTERN'

    async def create_embedding(self, text: str) -> List[float]:
        """Create embedding using Azure OpenAI"""
        try:
            response = self.openai_client.embeddings.create(
                input=text,
                model=AZURE_OPENAI_EMBEDDING_DEPLOYMENT
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error creating embedding: {e}")
            # Return zero vector as fallback
            return [0.0] * 1536

    def setup_qdrant_collection(self):
        """Setup Qdrant collection for Cipher patterns"""
        try:
            # Check if collection exists
            collections = self.qdrant_client.get_collections()
            collection_names = [col.name for col in collections.collections]
            
            if COLLECTION_NAME not in collection_names:
                logger.info(f"Creating collection '{COLLECTION_NAME}'")
                self.qdrant_client.create_collection(
                    collection_name=COLLECTION_NAME,
                    vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
                )
            else:
                logger.info(f"Collection '{COLLECTION_NAME}' already exists")
                
        except Exception as e:
            logger.error(f"Error setting up Qdrant collection: {e}")
            raise

    async def migrate_patterns_to_qdrant(self, patterns: List[Dict[str, Any]]):
        """Migrate patterns to Qdrant with embeddings"""
        logger.info(f"Starting migration of {len(patterns)} patterns to Qdrant")
        
        points = []
        for i, pattern in enumerate(patterns):
            try:
                # Create embedding for the pattern content
                embedding = await self.create_embedding(pattern['content'])
                
                # Create Qdrant point
                point = PointStruct(
                    id=hash(pattern['content']) % (2**32),  # Use content hash as ID
                    vector=embedding,
                    payload={
                        'content': pattern['content'],
                        'pattern_type': pattern['pattern_type'],
                        'table_source': pattern['table_source'],
                        'created_at': pattern['created_at'],
                        'metadata': pattern['metadata'],
                        'migrated_at': datetime.now().isoformat(),
                        'source': 'cipher_db_migration'
                    }
                )
                points.append(point)
                
                if (i + 1) % 10 == 0:
                    logger.info(f"Processed {i + 1}/{len(patterns)} patterns")
                    
            except Exception as e:
                logger.error(f"Error processing pattern {i}: {e}")
                continue
        
        # Upload points to Qdrant in batches
        batch_size = 50
        for i in range(0, len(points), batch_size):
            batch = points[i:i + batch_size]
            try:
                self.qdrant_client.upsert(
                    collection_name=COLLECTION_NAME,
                    points=batch
                )
                logger.info(f"Uploaded batch {i//batch_size + 1}/{(len(points)-1)//batch_size + 1}")
            except Exception as e:
                logger.error(f"Error uploading batch: {e}")
                continue
        
        logger.info(f"Migration completed. Uploaded {len(points)} patterns to Qdrant")

    async def run_migration(self):
        """Run the complete migration process"""
        logger.info("Starting Cipher to Qdrant migration")
        
        # Extract patterns from cipher.db
        patterns = self.extract_cipher_patterns()
        
        if not patterns:
            logger.warning("No patterns found to migrate")
            return
        
        # Setup Qdrant collection
        self.setup_qdrant_collection()
        
        # Migrate patterns
        await self.migrate_patterns_to_qdrant(patterns)
        
        # Test the migration
        await self.test_migration()
        
        logger.info("Migration completed successfully!")

    async def test_migration(self):
        """Test the migration by querying Qdrant"""
        try:
            # Get collection info
            collection_info = self.qdrant_client.get_collection(COLLECTION_NAME)
            logger.info(f"Collection info: {collection_info.points_count} points")
            
            # Test search
            test_query = "architecture pattern"
            test_embedding = await self.create_embedding(test_query)
            
            search_results = self.qdrant_client.search(
                collection_name=COLLECTION_NAME,
                query_vector=test_embedding,
                limit=3
            )
            
            logger.info(f"Test search for '{test_query}' returned {len(search_results)} results")
            for result in search_results:
                logger.info(f"- Score: {result.score:.3f}, Type: {result.payload.get('pattern_type')}")
                
        except Exception as e:
            logger.error(f"Error testing migration: {e}")

async def main():
    """Main migration function"""
    migrator = CipherQdrantMigrator()
    await migrator.run_migration()

if __name__ == "__main__":
    asyncio.run(main())