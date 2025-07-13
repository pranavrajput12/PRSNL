"""
Named Entity Recognition Service for Enhanced Content Tagging

This service provides intelligent content analysis using NER to extract:
- People, organizations, locations
- Technical terms and concepts
- Dates, times, quantities
- Custom domain entities

Integrates with spaCy for robust NLP capabilities.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Set, Any, Tuple
from datetime import datetime
import json
import re

# NLP dependencies
import spacy
from spacy import displacy
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.tag import pos_tag
from nltk.chunk import ne_chunk
from collections import Counter, defaultdict

# PRSNL imports
from app.core.config import settings

logger = logging.getLogger(__name__)

class NERService:
    """
    Named Entity Recognition service with multi-model support.
    
    Features:
    - Person, organization, location extraction
    - Technical domain entity recognition
    - Confidence scoring
    - Custom entity patterns
    - Bulk processing capabilities
    """
    
    def __init__(self):
        self.nlp = None
        self.technical_patterns = None
        self.domain_entities = None
        self._initialized = False
        
        # Technical domain patterns
        self.tech_patterns = {
            'programming_languages': [
                'python', 'javascript', 'typescript', 'java', 'c++', 'c#', 'rust', 'go', 'swift',
                'kotlin', 'php', 'ruby', 'scala', 'r', 'matlab', 'sql', 'html', 'css', 'bash'
            ],
            'frameworks': [
                'react', 'vue', 'angular', 'fastapi', 'django', 'flask', 'express', 'spring',
                'rails', 'laravel', 'tensorflow', 'pytorch', 'scikit-learn', 'pandas', 'numpy'
            ],
            'tools_platforms': [
                'docker', 'kubernetes', 'aws', 'azure', 'gcp', 'github', 'gitlab', 'jenkins',
                'terraform', 'ansible', 'nginx', 'apache', 'redis', 'postgresql', 'mongodb'
            ],
            'concepts': [
                'api', 'rest', 'graphql', 'microservices', 'devops', 'ci/cd', 'machine learning',
                'artificial intelligence', 'neural network', 'blockchain', 'cryptocurrency'
            ]
        }
    
    async def initialize(self):
        """Initialize NLP models and patterns."""
        if self._initialized:
            return
        
        try:
            # Load spaCy model
            logger.info("Loading spaCy model for NER...")
            try:
                self.nlp = spacy.load("en_core_web_sm")
            except OSError:
                logger.warning("en_core_web_sm not found, using blank English model")
                self.nlp = spacy.blank("en")
                
            # Download NLTK data if needed
            try:
                nltk.data.find('tokenizers/punkt')
            except LookupError:
                nltk.download('punkt', quiet=True)
                
            try:
                nltk.data.find('taggers/averaged_perceptron_tagger')
            except LookupError:
                nltk.download('averaged_perceptron_tagger', quiet=True)
                
            try:
                nltk.data.find('chunkers/maxent_ne_chunker')
            except LookupError:
                nltk.download('maxent_ne_chunker', quiet=True)
                
            try:
                nltk.data.find('corpora/words')
            except LookupError:
                nltk.download('words', quiet=True)
                
            try:
                nltk.data.find('corpora/stopwords')
            except LookupError:
                nltk.download('stopwords', quiet=True)
            
            # Compile technical patterns
            self._compile_technical_patterns()
            
            self._initialized = True
            logger.info("NER service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize NER service: {e}")
            raise
    
    def _compile_technical_patterns(self):
        """Compile regex patterns for technical term detection."""
        self.technical_patterns = {}
        
        for category, terms in self.tech_patterns.items():
            # Create case-insensitive patterns
            patterns = []
            for term in terms:
                # Escape special regex characters and create word boundary patterns
                escaped_term = re.escape(term)
                pattern = rf'\b{escaped_term}\b'
                patterns.append(pattern)
            
            self.technical_patterns[category] = re.compile(
                '|'.join(patterns), 
                re.IGNORECASE
            )
    
    async def extract_entities(
        self, 
        text: str, 
        include_technical: bool = True,
        confidence_threshold: float = 0.5
    ) -> Dict[str, Any]:
        """
        Extract named entities from text.
        
        Args:
            text: Text to analyze
            include_technical: Whether to include technical domain entities
            confidence_threshold: Minimum confidence for entity inclusion
            
        Returns:
            Dict with extracted entities by category
        """
        await self.initialize()
        
        if not text or len(text.strip()) < 3:
            return self._empty_result()
        
        try:
            # Process with spaCy
            doc = self.nlp(text)
            
            # Extract standard entities
            entities = {
                'people': [],
                'organizations': [],
                'locations': [],
                'dates': [],
                'money': [],
                'technical': defaultdict(list),
                'keywords': [],
                'summary': {}
            }
            
            # Extract spaCy entities
            for ent in doc.ents:
                confidence = self._calculate_confidence(ent)
                if confidence < confidence_threshold:
                    continue
                
                entity_data = {
                    'text': ent.text,
                    'label': ent.label_,
                    'start': ent.start_char,
                    'end': ent.end_char,
                    'confidence': confidence
                }
                
                # Categorize entities
                if ent.label_ in ['PERSON']:
                    entities['people'].append(entity_data)
                elif ent.label_ in ['ORG']:
                    entities['organizations'].append(entity_data)
                elif ent.label_ in ['GPE', 'LOC']:
                    entities['locations'].append(entity_data)
                elif ent.label_ in ['DATE', 'TIME']:
                    entities['dates'].append(entity_data)
                elif ent.label_ in ['MONEY']:
                    entities['money'].append(entity_data)
            
            # Extract technical entities if requested
            if include_technical:
                tech_entities = self._extract_technical_entities(text)
                entities['technical'].update(tech_entities)
            
            # Extract keywords using NLTK
            keywords = self._extract_keywords(text)
            entities['keywords'] = keywords
            
            # Generate summary
            entities['summary'] = self._generate_summary(entities)
            
            return entities
            
        except Exception as e:
            logger.error(f"Error extracting entities: {e}")
            return self._empty_result()
    
    def _extract_technical_entities(self, text: str) -> Dict[str, List[Dict[str, Any]]]:
        """Extract technical domain entities using patterns."""
        technical_entities = defaultdict(list)
        
        for category, pattern in self.technical_patterns.items():
            matches = pattern.finditer(text)
            for match in matches:
                entity_data = {
                    'text': match.group(),
                    'category': category,
                    'start': match.start(),
                    'end': match.end(),
                    'confidence': 0.8  # Pattern-based confidence
                }
                technical_entities[category].append(entity_data)
        
        return dict(technical_entities)
    
    def _extract_keywords(self, text: str, max_keywords: int = 10) -> List[Dict[str, Any]]:
        """Extract important keywords using NLTK."""
        try:
            # Tokenize and tag
            tokens = word_tokenize(text.lower())
            
            # Remove stopwords and non-alphabetic tokens
            stop_words = set(stopwords.words('english'))
            filtered_tokens = [
                token for token in tokens 
                if token.isalpha() and len(token) > 2 and token not in stop_words
            ]
            
            # Count frequency
            word_freq = Counter(filtered_tokens)
            
            # Get top keywords
            top_keywords = word_freq.most_common(max_keywords)
            
            keywords = []
            for word, freq in top_keywords:
                keywords.append({
                    'text': word,
                    'frequency': freq,
                    'confidence': min(1.0, freq / len(filtered_tokens) * 10)
                })
            
            return keywords
            
        except Exception as e:
            logger.error(f"Error extracting keywords: {e}")
            return []
    
    def _calculate_confidence(self, entity) -> float:
        """Calculate confidence score for an entity."""
        # Basic confidence based on entity properties
        base_confidence = 0.7
        
        # Adjust based on entity length
        if len(entity.text) > 15:
            base_confidence += 0.1
        elif len(entity.text) < 3:
            base_confidence -= 0.2
        
        # Adjust based on entity type reliability
        reliable_types = ['PERSON', 'ORG', 'GPE', 'MONEY']
        if entity.label_ in reliable_types:
            base_confidence += 0.1
        
        return min(1.0, max(0.1, base_confidence))
    
    def _generate_summary(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary statistics of extracted entities."""
        summary = {
            'total_entities': 0,
            'entity_counts': {},
            'top_categories': [],
            'confidence_avg': 0.0,
            'has_technical_content': False
        }
        
        all_entities = []
        
        # Collect all entities
        for category in ['people', 'organizations', 'locations', 'dates', 'money']:
            count = len(entities.get(category, []))
            if count > 0:
                summary['entity_counts'][category] = count
                all_entities.extend(entities[category])
        
        # Add technical entities
        for tech_category, tech_entities in entities.get('technical', {}).items():
            if tech_entities:
                summary['has_technical_content'] = True
                tech_count = len(tech_entities)
                summary['entity_counts'][f'tech_{tech_category}'] = tech_count
                all_entities.extend(tech_entities)
        
        # Calculate totals
        summary['total_entities'] = len(all_entities)
        
        if all_entities:
            # Calculate average confidence
            confidences = [e.get('confidence', 0.5) for e in all_entities]
            summary['confidence_avg'] = sum(confidences) / len(confidences)
            
            # Top categories by count
            sorted_counts = sorted(
                summary['entity_counts'].items(), 
                key=lambda x: x[1], 
                reverse=True
            )
            summary['top_categories'] = [cat for cat, count in sorted_counts[:3]]
        
        return summary
    
    def _empty_result(self) -> Dict[str, Any]:
        """Return empty result structure."""
        return {
            'people': [],
            'organizations': [],
            'locations': [],
            'dates': [],
            'money': [],
            'technical': {},
            'keywords': [],
            'summary': {
                'total_entities': 0,
                'entity_counts': {},
                'top_categories': [],
                'confidence_avg': 0.0,
                'has_technical_content': False
            }
        }
    
    async def bulk_extract_entities(
        self, 
        texts: List[str], 
        batch_size: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Extract entities from multiple texts in batches.
        
        Args:
            texts: List of texts to process
            batch_size: Number of texts to process concurrently
            
        Returns:
            List of entity extraction results
        """
        await self.initialize()
        
        results = []
        
        # Process in batches
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            
            # Process batch concurrently
            batch_tasks = [
                self.extract_entities(text) for text in batch
            ]
            batch_results = await asyncio.gather(*batch_tasks)
            results.extend(batch_results)
            
            # Small delay to prevent overwhelming the system
            if len(batch_results) == batch_size:
                await asyncio.sleep(0.1)
        
        return results
    
    async def enhance_tags(
        self, 
        existing_tags: List[str], 
        entities: Dict[str, Any],
        max_new_tags: int = 10
    ) -> List[str]:
        """
        Enhance existing tags with NER-derived tags.
        
        Args:
            existing_tags: Current tags
            entities: Extracted entities
            max_new_tags: Maximum new tags to add
            
        Returns:
            Enhanced tag list
        """
        new_tags = set(existing_tags)
        
        # Add entity-based tags
        for person in entities.get('people', []):
            if person['confidence'] > 0.7:
                new_tags.add(f"person:{person['text'].lower()}")
        
        for org in entities.get('organizations', []):
            if org['confidence'] > 0.7:
                new_tags.add(f"org:{org['text'].lower()}")
        
        # Add technical tags
        for tech_category, tech_entities in entities.get('technical', {}).items():
            for tech_entity in tech_entities[:3]:  # Limit to top 3 per category
                new_tags.add(tech_entity['text'].lower())
        
        # Add top keywords as tags
        for keyword in entities.get('keywords', [])[:5]:
            if keyword['confidence'] > 0.6:
                new_tags.add(keyword['text'])
        
        # Convert back to list and limit
        enhanced_tags = list(new_tags)
        if len(enhanced_tags) > len(existing_tags) + max_new_tags:
            # Keep original tags and add best new ones
            original_set = set(existing_tags)
            new_only = [tag for tag in enhanced_tags if tag not in original_set]
            
            # Sort new tags by relevance (you could implement more sophisticated ranking)
            new_only.sort()
            enhanced_tags = existing_tags + new_only[:max_new_tags]
        
        return enhanced_tags

# Global instance
ner_service = NERService()