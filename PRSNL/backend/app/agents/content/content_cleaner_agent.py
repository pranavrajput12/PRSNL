"""
Content Cleaner Agent - Clean and structure scraped content

This agent specializes in cleaning and structuring scraped web content by:
- Removing redundant elements (ads, navigation, footers)
- Improving content structure and spacing
- Preserving semantic meaning while cleaning
- Handling different content types (articles, documentation, tutorials)
- Producing clean, well-formatted content ready for storage and display
"""

import logging
import re
import json
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from bs4 import BeautifulSoup, NavigableString
from crewai import Agent

from app.agents.base_agent import PRSNLBaseAgent
from app.services.unified_ai_service import UnifiedAIService
from app.agents import register_agent

logger = logging.getLogger(__name__)


@dataclass
class CleanedContent:
    """Represents cleaned and structured content"""
    content: str
    title: Optional[str] = None
    sections: List[Dict[str, str]] = None
    metadata: Dict[str, Any] = None
    cleaning_stats: Dict[str, int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "title": self.title,
            "sections": self.sections or [],
            "metadata": self.metadata or {},
            "cleaning_stats": self.cleaning_stats or {}
        }


@register_agent("content_cleaner")
class ContentCleanerAgent(PRSNLBaseAgent):
    """Agent specialized in cleaning and structuring scraped content"""
    
    def __init__(
        self,
        role: str = "Content Cleaning Specialist",
        goal: str = "Clean and structure scraped content by removing redundant elements while preserving semantic meaning",
        backstory: Optional[str] = None,
        **kwargs
    ):
        if backstory is None:
            backstory = (
                "You are an expert content curator with deep knowledge of web structures and "
                "content patterns. Your expertise lies in identifying and removing unnecessary "
                "elements like advertisements, navigation menus, and boilerplate text while "
                "preserving the core content and its semantic structure. You understand various "
                "content types - from technical documentation to blog posts - and know how to "
                "clean each appropriately. You excel at improving readability through proper "
                "spacing, formatting, and structure while maintaining the author's original intent."
            )
        
        super().__init__(
            role=role,
            goal=goal,
            backstory=backstory,
            **kwargs
        )
        
        self.ai_service = UnifiedAIService()
        
        # Common patterns to remove
        self.removal_patterns = [
            # Navigation and UI elements
            r'<nav[^>]*>.*?</nav>',
            r'<header[^>]*>.*?</header>',
            r'<footer[^>]*>.*?</footer>',
            r'<aside[^>]*>.*?</aside>',
            
            # Social media and sharing
            r'(?i)(share|tweet|follow|subscribe).*?(twitter|facebook|linkedin|instagram)',
            r'(?i)share\s+this\s+(article|post|page)',
            
            # Newsletter and subscription
            r'(?i)(subscribe|sign up).*?newsletter',
            r'(?i)get.*?email.*?updates',
            
            # Comments and ads
            r'<div[^>]*class="[^"]*comment[^"]*"[^>]*>.*?</div>',
            r'<div[^>]*class="[^"]*ad[^"]*"[^>]*>.*?</div>',
            
            # Cookie notices
            r'(?i)we use cookies.*?accept',
            r'(?i)this site uses cookies',
        ]
        
        # Patterns to preserve
        self.preserve_patterns = [
            r'<pre[^>]*>.*?</pre>',
            r'<code[^>]*>.*?</code>',
            r'<blockquote[^>]*>.*?</blockquote>',
            r'<table[^>]*>.*?</table>',
        ]
    
    async def clean_content(
        self,
        content: str,
        content_type: Optional[str] = None,
        preserve_structure: bool = True,
        aggressive_cleaning: bool = False
    ) -> CleanedContent:
        """
        Clean and structure content
        
        Args:
            content: Raw content to clean
            content_type: Type of content (article, documentation, tutorial, etc.)
            preserve_structure: Whether to preserve heading structure
            aggressive_cleaning: Use more aggressive cleaning (may remove some content)
            
        Returns:
            CleanedContent object with cleaned content and metadata
        """
        try:
            cleaning_stats = {
                "original_length": len(content),
                "removed_elements": 0,
                "preserved_blocks": 0,
                "sections_created": 0
            }
            
            # Determine if content is HTML or plain text
            is_html = bool(re.search(r'<[^>]+>', content))
            
            if is_html:
                cleaned_content, stats = await self._clean_html_content(
                    content,
                    content_type,
                    preserve_structure,
                    aggressive_cleaning
                )
                cleaning_stats.update(stats)
            else:
                cleaned_content = await self._clean_text_content(
                    content,
                    content_type,
                    aggressive_cleaning
                )
            
            # Extract sections if structure is preserved
            sections = []
            if preserve_structure:
                sections = self._extract_sections(cleaned_content)
                cleaning_stats["sections_created"] = len(sections)
            
            # Final formatting pass
            final_content = self._format_content(cleaned_content, content_type)
            
            # Calculate cleaning effectiveness
            cleaning_stats["final_length"] = len(final_content)
            cleaning_stats["reduction_percent"] = round(
                (1 - cleaning_stats["final_length"] / cleaning_stats["original_length"]) * 100, 2
            )
            
            return CleanedContent(
                content=final_content,
                sections=sections,
                cleaning_stats=cleaning_stats,
                metadata={
                    "content_type": content_type,
                    "is_html": is_html,
                    "preserve_structure": preserve_structure,
                    "aggressive_cleaning": aggressive_cleaning
                }
            )
            
        except Exception as e:
            logger.error(f"Error cleaning content: {e}")
            # Return minimally cleaned content on error
            return CleanedContent(
                content=self._basic_clean(content),
                cleaning_stats={"error": str(e)}
            )
    
    async def _clean_html_content(
        self,
        html_content: str,
        content_type: Optional[str],
        preserve_structure: bool,
        aggressive_cleaning: bool
    ) -> Tuple[str, Dict[str, int]]:
        """Clean HTML content using BeautifulSoup and patterns"""
        stats = {
            "removed_elements": 0,
            "preserved_blocks": 0
        }
        
        # Parse HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove script and style elements
        for element in soup(['script', 'style', 'meta', 'link']):
            element.decompose()
            stats["removed_elements"] += 1
        
        # Remove elements by class/id patterns
        removal_keywords = [
            'nav', 'navigation', 'menu', 'header', 'footer', 'sidebar',
            'ad', 'advertisement', 'banner', 'popup', 'modal',
            'social', 'share', 'comment', 'related', 'suggested',
            'newsletter', 'subscribe', 'cookie'
        ]
        
        if aggressive_cleaning:
            removal_keywords.extend(['widget', 'module', 'component', 'aside'])
        
        for keyword in removal_keywords:
            # Remove by class
            for element in soup.find_all(class_=re.compile(keyword, re.I)):
                element.decompose()
                stats["removed_elements"] += 1
            
            # Remove by id
            for element in soup.find_all(id=re.compile(keyword, re.I)):
                element.decompose()
                stats["removed_elements"] += 1
        
        # Preserve important content blocks
        preserved_content = []
        
        # Preserve code blocks
        for code_block in soup.find_all(['pre', 'code']):
            preserved_content.append(str(code_block))
            stats["preserved_blocks"] += 1
        
        # Preserve tables if they contain useful data
        for table in soup.find_all('table'):
            if self._is_useful_table(table):
                preserved_content.append(str(table))
                stats["preserved_blocks"] += 1
            else:
                table.decompose()
                stats["removed_elements"] += 1
        
        # Convert to text while preserving structure
        if preserve_structure:
            cleaned_text = self._html_to_structured_text(soup)
        else:
            cleaned_text = soup.get_text(separator='\n', strip=True)
        
        # Apply text-based cleaning patterns
        for pattern in self.removal_patterns:
            cleaned_text = re.sub(pattern, '', cleaned_text, flags=re.IGNORECASE | re.DOTALL)
        
        # Re-insert preserved content
        for preserved in preserved_content:
            cleaned_text += f"\n\n{preserved}\n\n"
        
        return cleaned_text, stats
    
    async def _clean_text_content(
        self,
        text_content: str,
        content_type: Optional[str],
        aggressive_cleaning: bool
    ) -> str:
        """Clean plain text content"""
        
        # Remove excessive whitespace
        cleaned = re.sub(r'\n{3,}', '\n\n', text_content)
        cleaned = re.sub(r'[ \t]+', ' ', cleaned)
        
        # Remove common boilerplate patterns
        boilerplate_patterns = [
            r'(?i)^.*?cookie.*?policy.*?$',
            r'(?i)^.*?subscribe.*?newsletter.*?$',
            r'(?i)^.*?follow us on.*?$',
            r'(?i)^.*?share this.*?$',
            r'(?i)^.*?related articles.*?$',
            r'(?i)^.*?advertisement.*?$',
        ]
        
        for pattern in boilerplate_patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.MULTILINE)
        
        if aggressive_cleaning:
            # Remove short lines that might be UI elements
            lines = cleaned.split('\n')
            cleaned_lines = []
            for line in lines:
                if len(line.strip()) > 20 or not line.strip():
                    cleaned_lines.append(line)
            cleaned = '\n'.join(cleaned_lines)
        
        # Use AI for intelligent cleaning if content is substantial
        if len(cleaned) > 500 and content_type:
            cleaned = await self._ai_clean_text(cleaned, content_type)
        
        return cleaned
    
    async def _ai_clean_text(self, text: str, content_type: str) -> str:
        """Use AI to intelligently clean text content"""
        try:
            prompt = f"""Clean this {content_type} content by removing boilerplate and redundant elements:

Content:
{text[:3000]}

Rules:
1. Remove navigation text, social media prompts, and advertisements
2. Remove newsletter signup prompts and cookie notices
3. Remove "Related articles" or "You might also like" sections
4. Keep the main content, including all examples, code, and important details
5. Preserve the logical flow and structure
6. Do not add any new content or commentary

Return only the cleaned content without any explanation."""

            cleaned = await self.ai_service.complete(
                prompt=prompt,
                system_prompt="You are a content cleaning expert. Remove only redundant elements while preserving all meaningful content.",
                temperature=0.1
            )
            
            return cleaned.strip()
            
        except Exception as e:
            logger.warning(f"AI cleaning failed, using original: {e}")
            return text
    
    def _html_to_structured_text(self, soup: BeautifulSoup) -> str:
        """Convert HTML to structured text while preserving headings and paragraphs"""
        structured_text = []
        
        for element in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'li', 'div']):
            if element.name.startswith('h'):
                # Add spacing before headings
                level = int(element.name[1])
                prefix = '\n\n' + '#' * level + ' '
                structured_text.append(prefix + element.get_text(strip=True))
            elif element.name == 'p':
                text = element.get_text(strip=True)
                if text:  # Only add non-empty paragraphs
                    structured_text.append('\n\n' + text)
            elif element.name == 'li':
                text = element.get_text(strip=True)
                if text:
                    structured_text.append('\n• ' + text)
            elif element.name == 'div':
                # Only process divs that contain substantial text
                text = element.get_text(strip=True)
                if len(text) > 50 and not any(kw in text.lower() for kw in ['cookie', 'subscribe', 'share']):
                    structured_text.append('\n\n' + text)
        
        return ''.join(structured_text).strip()
    
    def _is_useful_table(self, table) -> bool:
        """Determine if a table contains useful data"""
        # Count cells with content
        cells_with_content = 0
        total_cells = 0
        
        for cell in table.find_all(['td', 'th']):
            total_cells += 1
            if cell.get_text(strip=True):
                cells_with_content += 1
        
        # Table is useful if it has content and reasonable structure
        return total_cells > 0 and cells_with_content / total_cells > 0.5 and total_cells > 4
    
    def _extract_sections(self, content: str) -> List[Dict[str, str]]:
        """Extract sections based on headings"""
        sections = []
        
        # Match markdown-style headings
        heading_pattern = r'^(#{1,6})\s+(.+)$'
        
        lines = content.split('\n')
        current_section = None
        
        for i, line in enumerate(lines):
            heading_match = re.match(heading_pattern, line, re.MULTILINE)
            
            if heading_match:
                # Save previous section
                if current_section:
                    sections.append(current_section)
                
                # Start new section
                level = len(heading_match.group(1))
                title = heading_match.group(2).strip()
                current_section = {
                    "level": level,
                    "title": title,
                    "content": "",
                    "line_start": i
                }
            elif current_section:
                current_section["content"] += line + '\n'
        
        # Save last section
        if current_section:
            sections.append(current_section)
        
        # Clean section content
        for section in sections:
            section["content"] = section["content"].strip()
        
        return sections
    
    def _format_content(self, content: str, content_type: Optional[str]) -> str:
        """Apply final formatting to content"""
        
        # Normalize line breaks
        content = re.sub(r'\r\n', '\n', content)
        content = re.sub(r'\n{3,}', '\n\n', content)
        
        # Format code blocks properly
        content = re.sub(r'```(\w*)\n', r'```\1\n', content)
        
        # Ensure proper spacing around headings
        content = re.sub(r'(^|\n)(#{1,6}\s+.+)(\n)(?!\n)', r'\1\n\2\n\n', content)
        
        # Format lists properly
        content = re.sub(r'(\n)([•\-*]\s+)', r'\n\2', content)
        
        # Remove trailing whitespace
        lines = content.split('\n')
        content = '\n'.join(line.rstrip() for line in lines)
        
        return content.strip()
    
    def _basic_clean(self, content: str) -> str:
        """Basic cleaning fallback"""
        # Remove excessive whitespace
        cleaned = re.sub(r'\s+', ' ', content)
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
        
        # Remove obvious junk
        cleaned = re.sub(r'(?i)(cookie|subscribe|newsletter|share this)', '', cleaned)
        
        return cleaned.strip()
    
    async def extract_main_content(self, html: str) -> str:
        """Extract main content from HTML using heuristics"""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Look for main content containers
        main_selectors = [
            'main', 'article', '[role="main"]', '.main-content',
            '#main-content', '.content', '#content', '.post-content'
        ]
        
        for selector in main_selectors:
            main_content = soup.select_one(selector)
            if main_content:
                return self._html_to_structured_text(main_content)
        
        # Fallback: find the element with the most text
        text_elements = []
        for element in soup.find_all(['div', 'article', 'section']):
            text_length = len(element.get_text(strip=True))
            if text_length > 200:  # Minimum content threshold
                text_elements.append((text_length, element))
        
        if text_elements:
            text_elements.sort(reverse=True)
            return self._html_to_structured_text(text_elements[0][1])
        
        # Last resort: return all text
        return soup.get_text(separator='\n', strip=True)
    
    def get_agent(self) -> Agent:
        """Get the configured CrewAI agent instance"""
        return Agent(
            role=self.role,
            goal=self.goal,
            backstory=self.backstory,
            tools=self.tools,
            llm=self._get_llm_config(),
            verbose=self.verbose,
            max_iter=self.max_iter,
            memory=self.memory
        )