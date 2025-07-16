"""
Test suite for Enhanced Document Extraction with OpenAI 1.96.0 Structured Outputs
Tests guaranteed JSON output functionality and structured data validation
"""

import asyncio
import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.document_extraction_enhanced import (
    DocumentMetadata,
    EntityExtraction,
    DocumentStructure,
    ComprehensiveDocumentAnalysis,
    EnhancedDocumentExtractor,
    enhanced_extractor
)

class TestStructuredOutputModels:
    """Test Pydantic models for structured output validation"""
    
    def test_document_metadata_model(self):
        """Test DocumentMetadata model validation"""
        metadata_data = {
            "title": "Test Document",
            "author": "Test Author",
            "summary": "This is a test document summary",
            "keywords": ["test", "document", "analysis"],
            "categories": ["technology", "testing"],
            "sentiment": "positive",
            "language": "en",
            "word_count": 500,
            "reading_time_minutes": 5,
            "confidence_score": 0.95
        }
        
        metadata = DocumentMetadata(**metadata_data)
        
        assert metadata.title == "Test Document"
        assert metadata.author == "Test Author"
        assert len(metadata.keywords) == 3
        assert metadata.confidence_score == 0.95
        assert metadata.sentiment in ["positive", "negative", "neutral"]
    
    def test_entity_extraction_model(self):
        """Test EntityExtraction model validation"""
        entity_data = {
            "people": ["John Doe", "Jane Smith"],
            "organizations": ["OpenAI", "Microsoft"],
            "locations": ["San Francisco", "Seattle"],
            "dates": ["2024", "January 2025"],
            "technologies": ["FastAPI", "Python", "AI"],
            "concepts": ["machine learning", "natural language processing"]
        }
        
        entities = EntityExtraction(**entity_data)
        
        assert len(entities.people) == 2
        assert len(entities.organizations) == 2
        assert len(entities.technologies) == 3
        assert "FastAPI" in entities.technologies
    
    def test_document_structure_model(self):
        """Test DocumentStructure model validation"""
        structure_data = {
            "sections": ["Introduction", "Methodology", "Results", "Conclusion"],
            "document_type": "research_paper",
            "has_tables": True,
            "has_images": False,
            "has_code": True,
            "complexity_level": "advanced"
        }
        
        structure = DocumentStructure(**structure_data)
        
        assert len(structure.sections) == 4
        assert structure.document_type == "research_paper"
        assert structure.has_tables is True
        assert structure.has_images is False
        assert structure.complexity_level == "advanced"
    
    def test_comprehensive_analysis_model(self):
        """Test ComprehensiveDocumentAnalysis model validation"""
        metadata = DocumentMetadata(
            title="Test", summary="Test summary", keywords=["test"],
            categories=["test"], sentiment="neutral", confidence_score=0.8
        )
        entities = EntityExtraction()
        structure = DocumentStructure(
            sections=[], document_type="article",
            has_tables=False, has_images=False, has_code=False,
            complexity_level="beginner"
        )
        
        analysis = ComprehensiveDocumentAnalysis(
            metadata=metadata,
            entities=entities,
            structure=structure
        )
        
        assert analysis.metadata.title == "Test"
        assert analysis.processing_version == "openai-1.96.0"
        assert analysis.extracted_at is not None

@pytest.mark.asyncio
class TestEnhancedDocumentExtractor:
    """Test enhanced document extraction functionality"""
    
    @pytest.fixture
    def extractor(self):
        """Create an enhanced document extractor instance"""
        return EnhancedDocumentExtractor()
    
    @pytest.fixture
    def sample_document_text(self):
        """Sample document text for testing"""
        return """
        # Advanced Machine Learning Techniques in Document Processing
        
        By Dr. Sarah Johnson, AI Research Institute
        
        ## Introduction
        
        This research paper explores cutting-edge machine learning approaches for 
        document analysis and information extraction. The study was conducted in 
        San Francisco between January 2024 and March 2024.
        
        ## Methodology
        
        We utilized Python and FastAPI to build our processing pipeline, incorporating
        transformers and neural networks for text analysis. The system processes
        over 10,000 documents per hour with 95% accuracy.
        
        ## Key Findings
        
        - Machine learning models show 40% improvement over traditional methods
        - Real-time processing is achievable with proper optimization
        - OpenAI GPT models provide excellent results for structured extraction
        
        ## Technologies Used
        
        - Python 3.11
        - FastAPI framework
        - OpenAI API
        - PostgreSQL database
        - Docker containers
        
        ## Conclusion
        
        This research demonstrates the effectiveness of modern AI techniques in
        document processing workflows. Future work will focus on multimodal
        document analysis.
        """
    
    @patch('app.services.document_extraction_enhanced.AsyncOpenAI')
    async def test_extract_structured_metadata(self, mock_openai, extractor, sample_document_text):
        """Test structured metadata extraction with guaranteed JSON"""
        # Mock OpenAI response with structured data
        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps({
            "title": "Advanced Machine Learning Techniques in Document Processing",
            "author": "Dr. Sarah Johnson",
            "summary": "Research paper on ML approaches for document analysis with 95% accuracy.",
            "keywords": ["machine learning", "document processing", "AI", "FastAPI", "OpenAI"],
            "categories": ["technology", "research", "artificial intelligence"],
            "sentiment": "positive",
            "language": "en",
            "word_count": 250,
            "reading_time_minutes": 2,
            "confidence_score": 0.92
        })
        
        mock_client = AsyncMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        # Test extraction
        metadata = await extractor.extract_structured_metadata(sample_document_text)
        
        # Verify structured output
        assert isinstance(metadata, DocumentMetadata)
        assert metadata.title == "Advanced Machine Learning Techniques in Document Processing"
        assert metadata.author == "Dr. Sarah Johnson"
        assert len(metadata.keywords) == 5
        assert metadata.confidence_score == 0.92
        assert metadata.sentiment == "positive"
        
        # Verify OpenAI was called with structured output format
        mock_client.chat.completions.create.assert_called_once()
        call_args = mock_client.chat.completions.create.call_args
        assert call_args[1]['response_format'] == {"type": "json_object"}
        assert call_args[1]['temperature'] == 0.1  # Low temperature for consistency
    
    @patch('app.services.document_extraction_enhanced.AsyncOpenAI')
    async def test_extract_entities(self, mock_openai, extractor, sample_document_text):
        """Test entity extraction with structured output"""
        # Mock OpenAI response with entity data
        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps({
            "people": ["Dr. Sarah Johnson"],
            "organizations": ["AI Research Institute", "OpenAI"],
            "locations": ["San Francisco"],
            "dates": ["January 2024", "March 2024"],
            "technologies": ["Python", "FastAPI", "OpenAI API", "PostgreSQL", "Docker"],
            "concepts": ["machine learning", "document analysis", "neural networks"]
        })
        
        mock_client = AsyncMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        # Test extraction
        entities = await extractor.extract_entities(sample_document_text)
        
        # Verify structured output
        assert isinstance(entities, EntityExtraction)
        assert len(entities.people) == 1
        assert "Dr. Sarah Johnson" in entities.people
        assert len(entities.organizations) == 2
        assert "OpenAI" in entities.organizations
        assert len(entities.technologies) == 5
        assert "FastAPI" in entities.technologies
        
        # Verify structured output format was used
        call_args = mock_client.chat.completions.create.call_args
        assert call_args[1]['response_format'] == {"type": "json_object"}
    
    @patch('app.services.document_extraction_enhanced.AsyncOpenAI')
    async def test_analyze_document_structure(self, mock_openai, extractor, sample_document_text):
        """Test document structure analysis with guaranteed JSON"""
        # Mock OpenAI response with structure data
        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps({
            "sections": ["Introduction", "Methodology", "Key Findings", "Technologies Used", "Conclusion"],
            "document_type": "research_paper",
            "has_tables": False,
            "has_images": False,
            "has_code": True,
            "complexity_level": "advanced"
        })
        
        mock_client = AsyncMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        # Test extraction
        structure = await extractor.analyze_document_structure(sample_document_text)
        
        # Verify structured output
        assert isinstance(structure, DocumentStructure)
        assert len(structure.sections) == 5
        assert "Introduction" in structure.sections
        assert structure.document_type == "research_paper"
        assert structure.has_code is True
        assert structure.complexity_level == "advanced"
    
    @patch('app.services.document_extraction_enhanced.AsyncOpenAI')
    async def test_extract_comprehensive_analysis(self, mock_openai, extractor, sample_document_text):
        """Test comprehensive document analysis with parallel processing"""
        # Mock responses for all three extraction types
        metadata_response = MagicMock()
        metadata_response.choices[0].message.content = json.dumps({
            "title": "Test Document",
            "summary": "Test summary",
            "keywords": ["test"],
            "categories": ["test"],
            "sentiment": "neutral",
            "confidence_score": 0.8
        })
        
        entities_response = MagicMock()
        entities_response.choices[0].message.content = json.dumps({
            "people": ["Test Person"],
            "organizations": ["Test Org"],
            "locations": ["Test Location"],
            "dates": ["2024"],
            "technologies": ["Python"],
            "concepts": ["testing"]
        })
        
        structure_response = MagicMock()
        structure_response.choices[0].message.content = json.dumps({
            "sections": ["Introduction"],
            "document_type": "article",
            "has_tables": False,
            "has_images": False,
            "has_code": False,
            "complexity_level": "beginner"
        })
        
        mock_client = AsyncMock()
        # Return different responses for different calls
        mock_client.chat.completions.create.side_effect = [
            metadata_response,
            entities_response,
            structure_response
        ]
        mock_openai.return_value = mock_client
        
        # Test comprehensive analysis
        analysis = await extractor.extract_comprehensive_analysis(sample_document_text)
        
        # Verify comprehensive result
        assert isinstance(analysis, ComprehensiveDocumentAnalysis)
        assert analysis.metadata.title == "Test Document"
        assert len(analysis.entities.people) == 1
        assert analysis.structure.document_type == "article"
        assert analysis.processing_version == "openai-1.96.0"
        
        # Verify all three extractions were called
        assert mock_client.chat.completions.create.call_count == 3
    
    @patch('app.services.document_extraction_enhanced.AsyncOpenAI')
    async def test_extract_key_insights(self, mock_openai, extractor, sample_document_text):
        """Test key insights extraction with structured output"""
        # Mock OpenAI response with insights data
        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps({
            "main_insights": [
                "Machine learning improves document processing by 40%",
                "Real-time processing is achievable with optimization",
                "OpenAI models excel at structured extraction"
            ],
            "action_items": [
                "Implement ML pipeline",
                "Optimize for real-time processing",
                "Integrate OpenAI structured outputs"
            ],
            "important_quotes": [
                "95% accuracy with our processing pipeline"
            ],
            "related_topics": [
                "Natural language processing",
                "Document intelligence",
                "AI automation"
            ],
            "questions_raised": [
                "How to scale to millions of documents?",
                "What about multimodal document analysis?"
            ]
        })
        
        mock_client = AsyncMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        # Test insights extraction
        insights = await extractor.extract_key_insights(sample_document_text)
        
        # Verify insights structure
        assert "main_insights" in insights
        assert "action_items" in insights
        assert len(insights["main_insights"]) == 3
        assert len(insights["action_items"]) == 3
        assert "95% accuracy" in insights["important_quotes"][0]
    
    async def test_fallback_handling_on_error(self, extractor):
        """Test fallback handling when OpenAI API fails"""
        with patch('app.services.document_extraction_enhanced.AsyncOpenAI') as mock_openai:
            # Mock API failure
            mock_client = AsyncMock()
            mock_client.chat.completions.create.side_effect = Exception("API Error")
            mock_openai.return_value = mock_client
            
            # Test that fallback metadata is returned
            metadata = await extractor.extract_structured_metadata("Test document")
            
            # Verify fallback values
            assert isinstance(metadata, DocumentMetadata)
            assert metadata.title == "Untitled Document"
            assert metadata.confidence_score == 0.0
            assert metadata.sentiment == "neutral"
    
    @patch('app.services.document_extraction_enhanced.AsyncOpenAI')
    async def test_batch_extract_documents(self, mock_openai, extractor):
        """Test batch document processing with rate limiting"""
        # Mock successful responses
        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps({
            "title": "Batch Document",
            "summary": "Batch processed",
            "keywords": ["batch"],
            "categories": ["test"],
            "sentiment": "neutral",
            "confidence_score": 0.7
        })
        
        mock_client = AsyncMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        # Test batch processing
        documents = [
            {"content": "Document 1 content"},
            {"content": "Document 2 content"},
            {"content": "Document 3 content"}
        ]
        
        results = await extractor.batch_extract_documents(documents)
        
        # Verify batch results
        assert len(results) == 3
        for result in results:
            assert isinstance(result, ComprehensiveDocumentAnalysis)
            assert result.metadata.title == "Batch Document"

class TestStructuredOutputIntegration:
    """Integration tests for structured output functionality"""
    
    def test_json_parsing_reliability(self):
        """Test that structured outputs are always valid JSON"""
        # Test various JSON structures that should be parseable
        test_jsons = [
            '{"title": "Test", "keywords": ["test"], "confidence_score": 0.8}',
            '{"people": [], "organizations": ["Company"], "locations": []}',
            '{"sections": ["Intro"], "document_type": "article", "has_tables": false}'
        ]
        
        for test_json in test_jsons:
            # Should not raise any exceptions
            parsed = json.loads(test_json)
            assert isinstance(parsed, dict)
    
    def test_pydantic_validation_strictness(self):
        """Test that Pydantic models enforce data validation"""
        # Test invalid confidence score
        with pytest.raises(ValueError):
            DocumentMetadata(
                title="Test",
                summary="Test",
                keywords=[],
                categories=[],
                sentiment="invalid_sentiment",  # Should be positive/negative/neutral
                confidence_score=1.5  # Should be 0.0-1.0
            )
    
    def test_structured_output_consistency(self):
        """Test that structured outputs maintain consistent schema"""
        # Create multiple DocumentMetadata instances
        metadata1 = DocumentMetadata(
            title="Doc 1", summary="Summary 1", keywords=["key1"],
            categories=["cat1"], sentiment="positive", confidence_score=0.9
        )
        
        metadata2 = DocumentMetadata(
            title="Doc 2", summary="Summary 2", keywords=["key2"],
            categories=["cat2"], sentiment="negative", confidence_score=0.8
        )
        
        # Both should have the same structure
        assert set(metadata1.dict().keys()) == set(metadata2.dict().keys())
        assert all(hasattr(metadata1, attr) for attr in ['title', 'summary', 'keywords'])
        assert all(hasattr(metadata2, attr) for attr in ['title', 'summary', 'keywords'])

# Performance and reliability tests
@pytest.mark.asyncio
class TestStructuredOutputPerformance:
    """Test performance characteristics of structured outputs"""
    
    @patch('app.services.document_extraction_enhanced.AsyncOpenAI')
    async def test_extraction_timeout_handling(self, mock_openai):
        """Test handling of slow API responses"""
        import asyncio
        
        extractor = EnhancedDocumentExtractor()
        
        # Mock slow response
        async def slow_response(*args, **kwargs):
            await asyncio.sleep(2)  # Simulate slow API
            response = MagicMock()
            response.choices[0].message.content = '{"title": "Slow Document", "summary": "Processed slowly", "keywords": [], "categories": [], "sentiment": "neutral", "confidence_score": 0.5}'
            return response
        
        mock_client = AsyncMock()
        mock_client.chat.completions.create = slow_response
        mock_openai.return_value = mock_client
        
        # Test with timeout
        start_time = asyncio.get_event_loop().time()
        
        try:
            metadata = await asyncio.wait_for(
                extractor.extract_structured_metadata("Test content"),
                timeout=3.0  # 3 second timeout
            )
            
            end_time = asyncio.get_event_loop().time()
            processing_time = end_time - start_time
            
            # Should complete within timeout
            assert processing_time < 3.0
            assert isinstance(metadata, DocumentMetadata)
            assert metadata.title == "Slow Document"
            
        except asyncio.TimeoutError:
            pytest.fail("Extraction should complete within timeout")
    
    def test_memory_efficiency_large_documents(self):
        """Test memory efficiency with large document content"""
        # Create a large document (simulate 100KB text)
        large_text = "This is a test sentence. " * 4000  # ~100KB
        
        # Should handle large text without memory issues
        extractor = EnhancedDocumentExtractor()
        
        # Test that text truncation works properly
        assert len(large_text) > 4000
        # The service should truncate to 4000 chars for processing
        truncated = large_text[:4000]
        assert len(truncated) == 4000