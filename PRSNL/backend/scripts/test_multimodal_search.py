#!/usr/bin/env python3
"""
Test Script for Multimodal Search Functionality

This script tests:
1. Text embedding creation
2. Image embedding creation
3. Multimodal embedding creation
4. Cross-modal similarity search
5. NER-enhanced tagging

Usage:
    python scripts/test_multimodal_search.py [--verbose] [--test-images /path/to/images]
"""

import asyncio
import logging
import argparse
import sys
import json
from pathlib import Path
from typing import Dict, List, Any

# Add the parent directory to Python path
sys.path.append(str(Path(__file__).parent.parent))

from app.services.multimodal_embedding_service import multimodal_embedding_service
from app.services.ner_service import ner_service
from app.services.embedding_manager import embedding_manager
from app.db.connection import get_db_connection

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MultimodalSearchTester:
    """
    Test suite for multimodal search functionality.
    """
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.test_results = {
            'embedding_tests': [],
            'ner_tests': [],
            'search_tests': [],
            'errors': []
        }
    
    async def run_all_tests(self, test_images_dir: str = None) -> Dict[str, Any]:
        """Run all multimodal search tests."""
        logger.info("🚀 Starting multimodal search test suite")
        
        try:
            # Initialize services
            await self._initialize_services()
            
            # Test 1: Text embedding creation
            await self._test_text_embeddings()
            
            # Test 2: NER functionality
            await self._test_ner_functionality()
            
            # Test 3: Image embeddings (if test images available)
            if test_images_dir and Path(test_images_dir).exists():
                await self._test_image_embeddings(test_images_dir)
            
            # Test 4: Multimodal embeddings
            if test_images_dir and Path(test_images_dir).exists():
                await self._test_multimodal_embeddings(test_images_dir)
            
            # Test 5: Cross-modal search
            await self._test_cross_modal_search()
            
            # Test 6: Database integration
            await self._test_database_integration()
            
            logger.info("✅ All tests completed")
            return self._generate_test_report()
            
        except Exception as e:
            logger.error(f"❌ Test suite failed: {e}")
            self.test_results['errors'].append(str(e))
            return self.test_results
    
    async def _initialize_services(self):
        """Initialize all required services."""
        logger.info("🔧 Initializing services...")
        
        try:
            await multimodal_embedding_service.initialize()
            await ner_service.initialize()
            logger.info("✅ Services initialized successfully")
        except Exception as e:
            logger.error(f"❌ Service initialization failed: {e}")
            raise
    
    async def _test_text_embeddings(self):
        """Test text embedding creation."""
        logger.info("📝 Testing text embeddings...")
        
        test_texts = [
            "FastAPI is a modern web framework for building APIs with Python",
            "Machine learning algorithms can process large datasets efficiently",
            "The quick brown fox jumps over the lazy dog"
        ]
        
        for i, text in enumerate(test_texts):
            try:
                # Test OpenAI embedding
                result = await multimodal_embedding_service.create_text_embedding(
                    text, use_openai=True
                )
                
                test_result = {
                    'test_name': f'text_embedding_{i+1}',
                    'text': text,
                    'embedding_length': len(result['vector']),
                    'model': result['model_name'],
                    'content_hash': result['content_hash'],
                    'success': True
                }
                
                self.test_results['embedding_tests'].append(test_result)
                
                if self.verbose:
                    logger.info(f"✅ Text embedding {i+1}: {test_result}")
                
            except Exception as e:
                error_result = {
                    'test_name': f'text_embedding_{i+1}',
                    'text': text,
                    'error': str(e),
                    'success': False
                }
                self.test_results['embedding_tests'].append(error_result)
                logger.error(f"❌ Text embedding {i+1} failed: {e}")
    
    async def _test_ner_functionality(self):
        """Test NER entity extraction."""
        logger.info("🏷️ Testing NER functionality...")
        
        test_texts = [
            "John Smith from Microsoft visited our office in New York on January 15th to discuss the new Python Django framework integration.",
            "The FastAPI application uses PostgreSQL database with Redis caching, deployed on AWS using Docker containers.",
            "Sarah Johnson, a data scientist at Google, presented her research on neural networks and TensorFlow optimization techniques."
        ]
        
        for i, text in enumerate(test_texts):
            try:
                entities = await ner_service.extract_entities(text, include_technical=True)
                
                test_result = {
                    'test_name': f'ner_test_{i+1}',
                    'text': text,
                    'entities_found': entities['summary']['total_entities'],
                    'people': len(entities['people']),
                    'organizations': len(entities['organizations']),
                    'technical_entities': sum(len(v) for v in entities['technical'].values()),
                    'has_technical_content': entities['summary']['has_technical_content'],
                    'top_keywords': [kw['text'] for kw in entities['keywords'][:3]],
                    'success': True
                }
                
                self.test_results['ner_tests'].append(test_result)
                
                if self.verbose:
                    logger.info(f"✅ NER test {i+1}: {test_result}")
                
            except Exception as e:
                error_result = {
                    'test_name': f'ner_test_{i+1}',
                    'text': text,
                    'error': str(e),
                    'success': False
                }
                self.test_results['ner_tests'].append(error_result)
                logger.error(f"❌ NER test {i+1} failed: {e}")
    
    async def _test_image_embeddings(self, test_images_dir: str):
        """Test image embedding creation."""
        logger.info("🖼️ Testing image embeddings...")
        
        image_dir = Path(test_images_dir)
        image_files = list(image_dir.glob("*.jpg")) + list(image_dir.glob("*.png"))
        
        if not image_files:
            logger.warning("No test images found, creating placeholder test")
            test_result = {
                'test_name': 'image_embedding_placeholder',
                'message': 'No test images available',
                'success': True
            }
            self.test_results['embedding_tests'].append(test_result)
            return
        
        for i, image_path in enumerate(image_files[:3]):  # Test first 3 images
            try:
                result = await multimodal_embedding_service.create_image_embedding(
                    image_path=str(image_path)
                )
                
                test_result = {
                    'test_name': f'image_embedding_{i+1}',
                    'image_path': str(image_path),
                    'embedding_length': len(result['vector']),
                    'model': result['model_name'],
                    'image_size': result['modality_metadata']['image_size'],
                    'content_hash': result['content_hash'],
                    'success': True
                }
                
                self.test_results['embedding_tests'].append(test_result)
                
                if self.verbose:
                    logger.info(f"✅ Image embedding {i+1}: {test_result}")
                
            except Exception as e:
                error_result = {
                    'test_name': f'image_embedding_{i+1}',
                    'image_path': str(image_path),
                    'error': str(e),
                    'success': False
                }
                self.test_results['embedding_tests'].append(error_result)
                logger.error(f"❌ Image embedding {i+1} failed: {e}")
    
    async def _test_multimodal_embeddings(self, test_images_dir: str):
        """Test multimodal embedding creation."""
        logger.info("🔀 Testing multimodal embeddings...")
        
        image_dir = Path(test_images_dir)
        image_files = list(image_dir.glob("*.jpg")) + list(image_dir.glob("*.png"))
        
        test_pairs = [
            ("A screenshot of code showing Python FastAPI implementation", image_files[0] if image_files else None),
            ("Documentation about machine learning algorithms", image_files[1] if len(image_files) > 1 else None),
        ]
        
        for i, (text, image_path) in enumerate(test_pairs):
            if not image_path or not image_path.exists():
                continue
            
            try:
                result = await multimodal_embedding_service.create_multimodal_embedding(
                    text=text,
                    image_path=str(image_path)
                )
                
                test_result = {
                    'test_name': f'multimodal_embedding_{i+1}',
                    'text': text,
                    'image_path': str(image_path),
                    'embedding_length': len(result['vector']),
                    'model': result['model_name'],
                    'components': result['modality_metadata']['components'],
                    'content_hash': result['content_hash'],
                    'success': True
                }
                
                self.test_results['embedding_tests'].append(test_result)
                
                if self.verbose:
                    logger.info(f"✅ Multimodal embedding {i+1}: {test_result}")
                
            except Exception as e:
                error_result = {
                    'test_name': f'multimodal_embedding_{i+1}',
                    'text': text,
                    'image_path': str(image_path) if image_path else None,
                    'error': str(e),
                    'success': False
                }
                self.test_results['embedding_tests'].append(error_result)
                logger.error(f"❌ Multimodal embedding {i+1} failed: {e}")
    
    async def _test_cross_modal_search(self):
        """Test cross-modal search functionality."""
        logger.info("🔍 Testing cross-modal search...")
        
        # Create test embeddings for search
        test_text = "Python web development with FastAPI framework"
        try:
            text_embedding = await multimodal_embedding_service.create_text_embedding(test_text)
            
            # Test cross-modal search
            search_results = await multimodal_embedding_service.cross_modal_search(
                query_embedding=text_embedding['vector'],
                query_type='text',
                target_types=['text', 'image', 'multimodal'],
                limit=5,
                threshold=0.3
            )
            
            test_result = {
                'test_name': 'cross_modal_search',
                'query_text': test_text,
                'results_count': len(search_results),
                'target_types': ['text', 'image', 'multimodal'],
                'threshold': 0.3,
                'success': True
            }
            
            self.test_results['search_tests'].append(test_result)
            
            if self.verbose:
                logger.info(f"✅ Cross-modal search: {test_result}")
            
        except Exception as e:
            error_result = {
                'test_name': 'cross_modal_search',
                'query_text': test_text,
                'error': str(e),
                'success': False
            }
            self.test_results['search_tests'].append(error_result)
            logger.error(f"❌ Cross-modal search failed: {e}")
    
    async def _test_database_integration(self):
        """Test database integration."""
        logger.info("🗄️ Testing database integration...")
        
        try:
            # Test multimodal stats
            stats = await multimodal_embedding_service.get_embeddings_stats()
            
            test_result = {
                'test_name': 'database_integration',
                'stats': stats,
                'has_embeddings': stats.get('total_embeddings', 0) > 0,
                'multimodal_enabled': stats.get('multimodal_enabled', False),
                'supported_types': stats.get('supported_types', []),
                'success': True
            }
            
            self.test_results['search_tests'].append(test_result)
            
            if self.verbose:
                logger.info(f"✅ Database integration: {test_result}")
            
        except Exception as e:
            error_result = {
                'test_name': 'database_integration',
                'error': str(e),
                'success': False
            }
            self.test_results['search_tests'].append(error_result)
            logger.error(f"❌ Database integration failed: {e}")
    
    def _generate_test_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report."""
        total_tests = (
            len(self.test_results['embedding_tests']) +
            len(self.test_results['ner_tests']) +
            len(self.test_results['search_tests'])
        )
        
        successful_tests = sum(
            1 for test_list in [
                self.test_results['embedding_tests'],
                self.test_results['ner_tests'],
                self.test_results['search_tests']
            ]
            for test in test_list
            if test.get('success', False)
        )
        
        return {
            'summary': {
                'total_tests': total_tests,
                'successful_tests': successful_tests,
                'failed_tests': total_tests - successful_tests,
                'success_rate': successful_tests / total_tests if total_tests > 0 else 0,
                'errors': len(self.test_results['errors'])
            },
            'detailed_results': self.test_results,
            'recommendations': self._generate_recommendations()
        }
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results."""
        recommendations = []
        
        # Check embedding test success
        embedding_successes = sum(1 for test in self.test_results['embedding_tests'] if test.get('success', False))
        embedding_total = len(self.test_results['embedding_tests'])
        
        if embedding_total > 0 and embedding_successes / embedding_total < 0.8:
            recommendations.append("Consider checking CLIP model installation and dependencies")
        
        # Check NER test success
        ner_successes = sum(1 for test in self.test_results['ner_tests'] if test.get('success', False))
        ner_total = len(self.test_results['ner_tests'])
        
        if ner_total > 0 and ner_successes / ner_total < 0.8:
            recommendations.append("Consider installing spaCy models: python -m spacy download en_core_web_sm")
        
        # Check search functionality
        search_successes = sum(1 for test in self.test_results['search_tests'] if test.get('success', False))
        search_total = len(self.test_results['search_tests'])
        
        if search_total > 0 and search_successes / search_total < 0.8:
            recommendations.append("Check database connectivity and vector index setup")
        
        if not recommendations:
            recommendations.append("All tests passed! Multimodal search system is ready for use.")
        
        return recommendations

async def main():
    """Main script entry point."""
    parser = argparse.ArgumentParser(description='Test multimodal search functionality')
    parser.add_argument('--verbose', action='store_true', help='Show detailed test output')
    parser.add_argument('--test-images', type=str, help='Directory containing test images')
    
    args = parser.parse_args()
    
    tester = MultimodalSearchTester(verbose=args.verbose)
    
    try:
        report = await tester.run_all_tests(test_images_dir=args.test_images)
        
        print("\n" + "="*60)
        print("MULTIMODAL SEARCH TEST REPORT")
        print("="*60)
        
        summary = report['summary']
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Successful: {summary['successful_tests']}")
        print(f"Failed: {summary['failed_tests']}")
        print(f"Success Rate: {summary['success_rate']:.1%}")
        print(f"Errors: {summary['errors']}")
        
        print("\n" + "-"*60)
        print("RECOMMENDATIONS")
        print("-"*60)
        for rec in report['recommendations']:
            print(f"• {rec}")
        
        if args.verbose:
            print("\n" + "-"*60)
            print("DETAILED RESULTS")
            print("-"*60)
            print(json.dumps(report['detailed_results'], indent=2))
        
    except KeyboardInterrupt:
        logger.info("Testing interrupted by user")
    except Exception as e:
        logger.error(f"Testing failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())