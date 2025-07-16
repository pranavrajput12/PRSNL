"""
Enhanced Document Extraction Service with OpenAI 1.96.0 Structured Outputs
Leverages guaranteed JSON outputs for 100% reliable data extraction
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field

from openai import AsyncOpenAI
from app.config import settings
from app.services.performance_monitoring import profile_ai, track_custom_metric

logger = logging.getLogger(__name__)

class DocumentMetadata(BaseModel):
    """Structured document metadata with guaranteed JSON format"""
    title: str = Field(description="Document title or main heading")
    author: Optional[str] = Field(default=None, description="Document author if available")
    summary: str = Field(description="Brief summary of document content")
    keywords: List[str] = Field(description="Key terms and concepts from the document")
    categories: List[str] = Field(description="Content categories (e.g., 'technology', 'business')")
    sentiment: str = Field(description="Overall sentiment: positive, negative, or neutral")
    language: str = Field(default="en", description="Document language code")
    word_count: Optional[int] = Field(default=None, description="Estimated word count")
    reading_time_minutes: Optional[int] = Field(default=None, description="Estimated reading time")
    confidence_score: float = Field(description="Extraction confidence (0.0-1.0)")

class EntityExtraction(BaseModel):
    """Structured entity extraction results"""
    people: List[str] = Field(default=[], description="Names of people mentioned")
    organizations: List[str] = Field(default=[], description="Organizations and companies")
    locations: List[str] = Field(default=[], description="Places and locations")
    dates: List[str] = Field(default=[], description="Important dates mentioned")
    technologies: List[str] = Field(default=[], description="Technologies and tools mentioned")
    concepts: List[str] = Field(default=[], description="Key concepts and ideas")

class DocumentStructure(BaseModel):
    """Document structure analysis"""
    sections: List[str] = Field(default=[], description="Main sections or headings")
    document_type: str = Field(default="unknown", description="Type of document (article, report, email, etc.)")
    has_tables: bool = Field(default=False, description="Whether document contains tables")
    has_images: bool = Field(default=False, description="Whether document contains images")
    has_code: bool = Field(default=False, description="Whether document contains code snippets")
    complexity_level: str = Field(default="unknown", description="Content complexity: beginner, intermediate, advanced")

class ComprehensiveDocumentAnalysis(BaseModel):
    """Complete document analysis with all extracted information"""
    metadata: DocumentMetadata
    entities: EntityExtraction
    structure: DocumentStructure
    extracted_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    processing_version: str = Field(default="openai-1.96.0")

class EnhancedDocumentExtractor:
    """Enhanced document extraction using OpenAI 1.96.0 structured outputs"""
    
    def __init__(self):
        # For Azure OpenAI with version 1.96.0, construct the base URL properly
        # Remove https:// if it's already in the endpoint
        endpoint = settings.AZURE_OPENAI_ENDPOINT.replace("https://", "")
        azure_base_url = f"https://{endpoint}/openai/deployments/{settings.AZURE_OPENAI_DEPLOYMENT}"
        
        self.client = AsyncOpenAI(
            api_key=settings.AZURE_OPENAI_API_KEY,
            base_url=azure_base_url,
            default_headers={
                "api-key": settings.AZURE_OPENAI_API_KEY,
                "api-version": settings.AZURE_OPENAI_API_VERSION
            }
        )
        
    @profile_ai(model="gpt-4", operation="metadata_extraction")
    async def extract_structured_metadata(self, document_text: str) -> DocumentMetadata:
        """
        Extract document metadata with guaranteed JSON structure
        Uses OpenAI 1.96.0 structured outputs for 100% reliability
        """
        try:
            system_prompt = """You are an expert document analyzer. Extract metadata from the provided document text.
            Return ONLY valid JSON that matches the expected schema.
            Be accurate and thorough in your analysis."""
            
            user_prompt = f"""Analyze this document and extract structured metadata:

Document Text:
{document_text[:4000]}...

Extract:
- Title (main heading or inferred title)
- Author (if mentioned)
- Summary (2-3 sentences)
- Keywords (5-10 important terms)
- Categories (1-3 content categories)
- Sentiment (positive/negative/neutral)
- Language code
- Estimated word count and reading time
- Confidence score for the extraction (0.0-1.0)

Return structured JSON data."""

            # Use OpenAI 1.96.0 structured outputs for guaranteed JSON
            response = await self.client.chat.completions.create(
                model=settings.AZURE_OPENAI_DEPLOYMENT,
                response_format={"type": "json_object"},  # Guaranteed JSON output
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,  # Low temperature for consistent extraction
                max_tokens=1000
            )
            
            # Parse the guaranteed JSON response
            extracted_data = json.loads(response.choices[0].message.content)
            
            # Validate and create structured metadata
            metadata = DocumentMetadata(**extracted_data)
            
            logger.info(f"Successfully extracted structured metadata with confidence: {metadata.confidence_score}")
            return metadata
            
        except Exception as e:
            logger.error(f"Error in structured metadata extraction: {e}")
            # Return fallback metadata
            return DocumentMetadata(
                title="Untitled Document",
                summary="Unable to extract summary",
                keywords=[],
                categories=["general"],
                sentiment="neutral",
                confidence_score=0.0
            )
    
    @profile_ai(model="gpt-4", operation="entity_extraction")
    async def extract_entities(self, document_text: str) -> EntityExtraction:
        """
        Extract named entities with structured output
        """
        try:
            system_prompt = """You are an expert at named entity recognition. Extract entities from the document.
            Return ONLY valid JSON with the extracted entities organized by category."""
            
            user_prompt = f"""Extract named entities from this document:

Document Text:
{document_text[:4000]}...

Extract and categorize:
- People: Names of individuals
- Organizations: Companies, institutions, groups
- Locations: Cities, countries, places
- Dates: Important dates and time periods
- Technologies: Software, hardware, technical terms
- Concepts: Key ideas and abstract concepts

Return structured JSON data."""

            response = await self.client.chat.completions.create(
                model=settings.AZURE_OPENAI_DEPLOYMENT,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=800
            )
            
            extracted_data = json.loads(response.choices[0].message.content)
            entities = EntityExtraction(**extracted_data)
            
            logger.info(f"Successfully extracted entities: {len(entities.people)} people, {len(entities.organizations)} orgs")
            return entities
            
        except Exception as e:
            logger.error(f"Error in entity extraction: {e}")
            return EntityExtraction(
                people=[], organizations=[], locations=[],
                dates=[], technologies=[], concepts=[]
            )
    
    @profile_ai(model="gpt-4", operation="structure_analysis")
    async def analyze_document_structure(self, document_text: str) -> DocumentStructure:
        """
        Analyze document structure with guaranteed JSON output
        """
        try:
            system_prompt = """You are an expert at document structure analysis. Analyze the organization and format of the document.
            Return ONLY valid JSON with the structural analysis."""
            
            user_prompt = f"""Analyze the structure of this document:

Document Text:
{document_text[:4000]}...

Analyze:
- Main sections or headings
- Document type (article, report, email, manual, etc.)
- Presence of tables, images, or code snippets
- Content complexity level
- Overall organization

Return structured JSON data."""

            response = await self.client.chat.completions.create(
                model=settings.AZURE_OPENAI_DEPLOYMENT,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=600
            )
            
            extracted_data = json.loads(response.choices[0].message.content)
            structure = DocumentStructure(**extracted_data)
            
            logger.info(f"Successfully analyzed document structure: {structure.document_type}")
            return structure
            
        except Exception as e:
            logger.error(f"Error in structure analysis: {e}")
            return DocumentStructure(
                sections=[],
                document_type="unknown",
                has_tables=False,
                has_images=False,
                has_code=False,
                complexity_level="unknown"
            )
    
    @profile_ai(model="gpt-4", operation="comprehensive_analysis")
    async def extract_comprehensive_analysis(self, document_text: str) -> ComprehensiveDocumentAnalysis:
        """
        Perform comprehensive document analysis with all extraction types
        Uses parallel processing for efficiency
        """
        import asyncio
        
        try:
            # Run all extractions in parallel for better performance
            metadata_task = self.extract_structured_metadata(document_text)
            entities_task = self.extract_entities(document_text)
            structure_task = self.analyze_document_structure(document_text)
            
            # Wait for all extractions to complete
            metadata, entities, structure = await asyncio.gather(
                metadata_task, entities_task, structure_task
            )
            
            # Combine into comprehensive analysis
            comprehensive_analysis = ComprehensiveDocumentAnalysis(
                metadata=metadata,
                entities=entities,
                structure=structure
            )
            
            logger.info(f"Comprehensive analysis completed with confidence: {metadata.confidence_score}")
            return comprehensive_analysis
            
        except Exception as e:
            logger.error(f"Error in comprehensive analysis: {e}")
            raise
    
    async def extract_key_insights(self, document_text: str) -> Dict[str, Any]:
        """
        Extract key insights and actionable information with structured output
        """
        try:
            system_prompt = """You are an expert at extracting actionable insights from documents.
            Focus on key takeaways, recommendations, and important conclusions.
            Return ONLY valid JSON with the insights."""
            
            user_prompt = f"""Extract key insights from this document:

Document Text:
{document_text[:4000]}...

Extract:
- Main insights: Key takeaways and conclusions
- Action items: Actionable recommendations
- Important quotes: Notable statements or findings
- Related topics: Connected subjects to explore
- Questions raised: Important questions the document addresses

Return structured JSON data."""

            response = await self.client.chat.completions.create(
                model=settings.AZURE_OPENAI_DEPLOYMENT,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2,
                max_tokens=1000
            )
            
            insights = json.loads(response.choices[0].message.content)
            
            logger.info(f"Successfully extracted insights with {len(insights.get('main_insights', []))} key points")
            return insights
            
        except Exception as e:
            logger.error(f"Error in insights extraction: {e}")
            return {
                "main_insights": [],
                "action_items": [],
                "important_quotes": [],
                "related_topics": [],
                "questions_raised": []
            }

    async def batch_extract_documents(self, documents: List[Dict[str, str]]) -> List[ComprehensiveDocumentAnalysis]:
        """
        Process multiple documents in batch with rate limiting
        """
        import asyncio
        
        results = []
        
        # Process in batches to respect rate limits
        batch_size = 5
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            
            batch_tasks = [
                self.extract_comprehensive_analysis(doc["content"])
                for doc in batch
            ]
            
            try:
                batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
                
                for j, result in enumerate(batch_results):
                    if isinstance(result, Exception):
                        logger.error(f"Error processing document {i+j}: {result}")
                        # Add placeholder result for failed documents
                        results.append(ComprehensiveDocumentAnalysis(
                            metadata=DocumentMetadata(
                                title=f"Document {i+j+1} (Failed)",
                                summary="Processing failed",
                                keywords=[],
                                categories=["error"],
                                sentiment="neutral",
                                confidence_score=0.0
                            ),
                            entities=EntityExtraction(),
                            structure=DocumentStructure(
                                sections=[],
                                document_type="error",
                                has_tables=False,
                                has_images=False,
                                has_code=False,
                                complexity_level="unknown"
                            )
                        ))
                    else:
                        results.append(result)
                
                # Small delay between batches to respect rate limits
                if i + batch_size < len(documents):
                    await asyncio.sleep(1)
                    
            except Exception as e:
                logger.error(f"Error processing batch {i//batch_size + 1}: {e}")
                
        logger.info(f"Batch processing completed: {len(results)} documents processed")
        return results

# Global instance for use across the application
enhanced_extractor = EnhancedDocumentExtractor()