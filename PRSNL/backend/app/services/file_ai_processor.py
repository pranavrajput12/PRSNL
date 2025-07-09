"""AI processing pipeline for file content"""
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from uuid import UUID
import asyncio
import re

from app.services.llm_processor import LLMProcessor
from app.services.document_processor import DocumentProcessor

logger = logging.getLogger(__name__)

@dataclass
class FileAIAnalysis:
    """Container for AI analysis results of file content"""
    title: str
    summary: str
    content: str
    tags: List[str]
    key_points: List[str]
    sentiment: Optional[str] = None
    reading_time: Optional[int] = None
    entities: Optional[Dict[str, List[str]]] = None
    questions: Optional[List[str]] = None
    category_confidence: Optional[float] = None
    language: Optional[str] = None
    content_type_detected: Optional[str] = None

class FileAIProcessor:
    """AI processing service for file content analysis"""
    
    def __init__(self):
        self.llm_processor = LLMProcessor()
        self.document_processor = DocumentProcessor()
    
    async def process_file_content(
        self, 
        extracted_content: Dict[str, Any],
        file_info: Dict[str, Any],
        original_filename: str,
        user_content_type: str = "auto"
    ) -> FileAIAnalysis:
        """
        Process file content with AI analysis
        
        Args:
            extracted_content: Content extracted from file
            file_info: File metadata (extension, mime_type, category, etc.)
            original_filename: Original filename
            user_content_type: User-selected content type
        """
        logger.info(f"Processing file content for: {original_filename}")
        
        # Get extracted text
        text_content = extracted_content.get('text', '')
        
        # If no text content, create minimal analysis
        if not text_content or not text_content.strip():
            return await self._create_minimal_analysis(original_filename, file_info)
        
        # Prepare content for AI analysis
        processed_content = await self._prepare_content_for_ai(
            text_content, file_info, original_filename, user_content_type
        )
        
        # Process with LLM
        ai_result = await self.llm_processor.process_content(
            content=processed_content,
            title=self._generate_title_from_filename(original_filename),
            url=None  # Files don't have URLs
        )
        
        # Enhance with file-specific analysis
        enhanced_analysis = await self._enhance_file_analysis(
            ai_result, extracted_content, file_info, original_filename
        )
        
        return enhanced_analysis
    
    async def _prepare_content_for_ai(
        self, 
        text_content: str, 
        file_info: Dict[str, Any], 
        filename: str,
        user_content_type: str
    ) -> str:
        """Prepare file content for AI analysis with context"""
        
        # Add file context header
        context_header = f"""
FILE ANALYSIS CONTEXT:
- Filename: {filename}
- File Type: {file_info.get('category', 'unknown')}
- File Extension: {file_info.get('extension', 'unknown')}
- MIME Type: {file_info.get('mime_type', 'unknown')}
- User Content Type: {user_content_type}
- File Size: {self._format_file_size(file_info.get('size', 0))}

EXTRACTED CONTENT:
"""
        
        # Clean and prepare text content
        cleaned_content = self._clean_extracted_text(text_content)
        
        # Truncate if too long (keep most relevant parts)
        if len(cleaned_content) > 8000:  # Adjust based on LLM context limits
            cleaned_content = self._intelligently_truncate_content(cleaned_content)
        
        return context_header + cleaned_content
    
    def _clean_extracted_text(self, text: str) -> str:
        """Clean extracted text for better AI processing"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove common OCR artifacts
        text = re.sub(r'[|]{2,}', '', text)  # Remove multiple pipe characters
        text = re.sub(r'_{3,}', '', text)    # Remove multiple underscores
        text = re.sub(r'-{3,}', '', text)    # Remove multiple dashes
        
        # Remove page numbers and headers/footers patterns
        text = re.sub(r'\n\d+\s*\n', '\n', text)  # Standalone page numbers
        text = re.sub(r'\n\d+\s*$', '', text)     # Page numbers at end
        
        # Clean up common PDF artifacts
        text = re.sub(r'\x0c', '\n', text)  # Form feed characters
        text = re.sub(r'\u00a0', ' ', text)  # Non-breaking spaces
        
        return text.strip()
    
    def _intelligently_truncate_content(self, text: str, max_length: int = 8000) -> str:
        """Intelligently truncate content keeping most important parts"""
        if len(text) <= max_length:
            return text
        
        # Try to keep the beginning and end
        beginning_chars = max_length // 2
        ending_chars = max_length - beginning_chars - 100  # Leave space for separator
        
        beginning = text[:beginning_chars]
        ending = text[-ending_chars:]
        
        # Find sentence boundaries to avoid cutting mid-sentence
        beginning = self._find_sentence_boundary(beginning, from_end=True)
        ending = self._find_sentence_boundary(ending, from_end=False)
        
        separator = "\n\n[... CONTENT TRUNCATED ...]\n\n"
        
        return beginning + separator + ending
    
    def _find_sentence_boundary(self, text: str, from_end: bool = True) -> str:
        """Find sentence boundary to avoid cutting mid-sentence"""
        sentence_endings = ['.', '!', '?', '\n']
        
        if from_end:
            # Find last sentence ending
            for i in range(len(text) - 1, -1, -1):
                if text[i] in sentence_endings:
                    return text[:i + 1]
        else:
            # Find first sentence ending
            for i, char in enumerate(text):
                if char in sentence_endings:
                    return text[i:]
        
        return text
    
    def _generate_title_from_filename(self, filename: str) -> str:
        """Generate a readable title from filename"""
        # Remove extension
        name_without_ext = filename.rsplit('.', 1)[0]
        
        # Replace underscores and hyphens with spaces
        name_without_ext = name_without_ext.replace('_', ' ').replace('-', ' ')
        
        # Capitalize words
        return ' '.join(word.capitalize() for word in name_without_ext.split())
    
    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human readable format"""
        if size_bytes == 0:
            return "0 bytes"
        
        size_names = ["bytes", "KB", "MB", "GB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.1f} {size_names[i]}"
    
    async def _enhance_file_analysis(
        self, 
        ai_result: Any, 
        extracted_content: Dict[str, Any], 
        file_info: Dict[str, Any],
        filename: str
    ) -> FileAIAnalysis:
        """Enhance AI analysis with file-specific insights"""
        
        # Extract content type confidence
        content_type_confidence = self._detect_content_type_confidence(
            ai_result.content, file_info
        )
        
        # Detect language
        language = self._detect_language(ai_result.content)
        
        # Generate file-specific tags
        file_tags = self._generate_file_specific_tags(file_info, filename)
        
        # Combine AI tags with file-specific tags
        all_tags = list(set(ai_result.tags + file_tags))
        
        # Generate reading time based on word count
        reading_time = self._calculate_reading_time(
            extracted_content.get('word_count', 0)
        )
        
        # Enhance title if AI title is generic
        enhanced_title = self._enhance_title(ai_result.title, filename)
        
        return FileAIAnalysis(
            title=enhanced_title,
            summary=ai_result.summary,
            content=ai_result.content,
            tags=all_tags,
            key_points=ai_result.key_points,
            sentiment=ai_result.sentiment,
            reading_time=reading_time,
            entities=ai_result.entities,
            questions=ai_result.questions,
            category_confidence=content_type_confidence,
            language=language,
            content_type_detected=self._detect_content_type(ai_result.content)
        )
    
    def _detect_content_type_confidence(self, content: str, file_info: Dict[str, Any]) -> float:
        """Detect confidence in content type classification"""
        # Simple heuristic based on content and file type
        file_category = file_info.get('category', 'unknown')
        
        # Higher confidence for known file types
        if file_category in ['pdf', 'office', 'text']:
            return 0.9
        elif file_category == 'image':
            # OCR confidence depends on text length
            word_count = len(content.split()) if content else 0
            if word_count > 50:
                return 0.8
            elif word_count > 10:
                return 0.6
            else:
                return 0.3
        else:
            return 0.5
    
    def _detect_language(self, content: str) -> str:
        """Simple language detection"""
        # This is a simplified version - in production, use a proper language detection library
        if not content:
            return "unknown"
        
        # Simple heuristics
        common_english_words = ["the", "and", "is", "in", "to", "of", "a", "that", "it", "with"]
        content_lower = content.lower()
        
        english_count = sum(1 for word in common_english_words if word in content_lower)
        
        if english_count >= 3:
            return "english"
        else:
            return "unknown"
    
    def _generate_file_specific_tags(self, file_info: Dict[str, Any], filename: str) -> List[str]:
        """Generate tags specific to file type and content"""
        tags = []
        
        # Add file type tags
        category = file_info.get('category', 'unknown')
        extension = file_info.get('extension', '').lower()
        
        tags.append(f"file-{category}")
        
        if extension:
            tags.append(f"format-{extension[1:]}")  # Remove dot
        
        # Add size-based tags
        size = file_info.get('size', 0)
        if size > 10 * 1024 * 1024:  # 10MB
            tags.append("large-file")
        elif size < 50 * 1024:  # 50KB
            tags.append("small-file")
        
        # Add filename-based tags
        filename_lower = filename.lower()
        if any(word in filename_lower for word in ['report', 'summary', 'analysis']):
            tags.append("report")
        if any(word in filename_lower for word in ['manual', 'guide', 'instructions']):
            tags.append("documentation")
        if any(word in filename_lower for word in ['presentation', 'slides']):
            tags.append("presentation")
        
        return tags
    
    def _calculate_reading_time(self, word_count: int) -> int:
        """Calculate estimated reading time in minutes"""
        if word_count <= 0:
            return 0
        
        # Average reading speed: 200-250 words per minute
        words_per_minute = 225
        reading_time = max(1, round(word_count / words_per_minute))
        
        return reading_time
    
    def _enhance_title(self, ai_title: str, filename: str) -> str:
        """Enhance title if AI title is too generic"""
        generic_titles = [
            "document", "file", "text", "content", "untitled", 
            "image", "picture", "photo", "scan"
        ]
        
        ai_title_lower = ai_title.lower()
        
        # If AI title is generic, use filename-based title
        if any(generic in ai_title_lower for generic in generic_titles):
            return self._generate_title_from_filename(filename)
        
        return ai_title
    
    def _detect_content_type(self, content: str) -> str:
        """Detect content type from analyzed content"""
        if not content:
            return "unknown"
        
        content_lower = content.lower()
        
        # Academic/research indicators
        if any(term in content_lower for term in ['abstract', 'methodology', 'references', 'bibliography']):
            return "academic"
        
        # Technical documentation
        if any(term in content_lower for term in ['api', 'function', 'parameter', 'configuration']):
            return "technical"
        
        # Business document
        if any(term in content_lower for term in ['quarterly', 'revenue', 'profit', 'strategy']):
            return "business"
        
        # Personal note
        if any(term in content_lower for term in ['note', 'reminder', 'todo', 'ideas']):
            return "personal"
        
        return "general"
    
    async def _create_minimal_analysis(self, filename: str, file_info: Dict[str, Any]) -> FileAIAnalysis:
        """Create minimal analysis for files with no extractable text"""
        title = self._generate_title_from_filename(filename)
        
        file_category = file_info.get('category', 'unknown')
        file_size = self._format_file_size(file_info.get('size', 0))
        
        summary = f"File: {filename} ({file_category}, {file_size})"
        
        if file_category == 'image':
            summary += " - Image file with no extractable text"
        else:
            summary += " - Document with no extractable text content"
        
        tags = [f"file-{file_category}", "no-text-content"]
        
        return FileAIAnalysis(
            title=title,
            summary=summary,
            content=summary,
            tags=tags,
            key_points=[],
            sentiment=None,
            reading_time=0,
            entities=None,
            questions=None,
            category_confidence=0.5,
            language="unknown",
            content_type_detected="file"
        )