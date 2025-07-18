"""
Bookmark Categorization Agent - Intelligent URL and content categorization

This agent specializes in analyzing URLs, titles, and content to automatically
categorize bookmarks into meaningful categories and tags.
"""

import logging
import re
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse
from crewai import Agent

from app.agents.base_agent import PRSNLBaseAgent
from app.services.unified_ai_service import UnifiedAIService

logger = logging.getLogger(__name__)


class BookmarkCategorizationAgent(PRSNLBaseAgent):
    """Agent specialized in categorizing bookmarks and URLs intelligently"""
    
    def __init__(
        self,
        role: str = "Bookmark Categorization Specialist",
        goal: str = "Intelligently categorize URLs and bookmarks based on content, domain, and context patterns",
        backstory: Optional[str] = None,
        **kwargs
    ):
        if backstory is None:
            backstory = (
                "You are an expert information curator with deep knowledge of web content, "
                "technology domains, and information organization. Your expertise lies in "
                "analyzing URLs, domain patterns, content types, and contextual clues to "
                "accurately categorize bookmarks. You understand the nuances of different "
                "websites, platforms, and content types, allowing you to create meaningful "
                "and consistent categorization schemes."
            )
        
        super().__init__(
            role=role,
            goal=goal,
            backstory=backstory,
            **kwargs
        )
        
        self.ai_service = UnifiedAIService()
        
        # Predefined category mappings based on domain patterns
        self.domain_categories = {
            # Technology & Programming
            'github.com': 'development',
            'stackoverflow.com': 'development',
            'dev.to': 'development',
            'medium.com': 'articles',
            'hackernoon.com': 'technology',
            'techcrunch.com': 'technology',
            'ycombinator.com': 'startup',
            
            # Documentation & Learning
            'docs.python.org': 'documentation',
            'developer.mozilla.org': 'documentation',
            'w3schools.com': 'learning',
            'freecodecamp.org': 'learning',
            'coursera.org': 'education',
            'udemy.com': 'education',
            'khan academy.org': 'education',
            
            # Social & Communication
            'twitter.com': 'social',
            'linkedin.com': 'professional',
            'youtube.com': 'video',
            'vimeo.com': 'video',
            'twitch.tv': 'video',
            
            # News & Media
            'nytimes.com': 'news',
            'bbc.com': 'news',
            'cnn.com': 'news',
            'reuters.com': 'news',
            'npr.org': 'news',
            
            # Tools & Productivity
            'notion.so': 'productivity',
            'trello.com': 'productivity',
            'slack.com': 'productivity',
            'figma.com': 'design',
            'canva.com': 'design',
            
            # Research & Reference
            'wikipedia.org': 'reference',
            'scholar.google.com': 'research',
            'arxiv.org': 'research',
            'pubmed.ncbi.nlm.nih.gov': 'research'
        }
        
        # URL patterns for specific content types
        self.url_patterns = {
            r'/blog/': 'blog',
            r'/article/': 'article',
            r'/tutorial/': 'tutorial',
            r'/docs?/': 'documentation',
            r'/api/': 'api-reference',
            r'/guide/': 'guide',
            r'/course/': 'course',
            r'/video/': 'video',
            r'/podcast/': 'podcast',
            r'/tools?/': 'tool',
            r'/news/': 'news',
            r'/product/': 'product',
            r'/shop/': 'shopping'
        }
    
    def get_agent(self) -> Agent:
        """Get the configured agent instance"""
        return Agent(
            role=self.role,
            goal=self.goal,
            backstory=self.backstory,
            tools=self.tools,
            llm=self.get_llm_config(),
            verbose=self.verbose,
            allow_delegation=self.allow_delegation,
            max_iter=self.max_iter,
            memory=self.memory
        )
    
    async def categorize_bookmark(
        self,
        url: str,
        title: str = "",
        content: str = "",
        folder_path: str = "",
        use_ai: bool = True
    ) -> Dict[str, Any]:
        """
        Categorize a bookmark using multiple analysis methods
        
        Args:
            url: The bookmark URL
            title: The bookmark title
            content: Page content (if available)
            folder_path: Original folder path from bookmarks file
            use_ai: Whether to use AI for enhanced categorization
            
        Returns:
            Dict containing category, tags, confidence, and reasoning
        """
        try:
            # Start with rule-based categorization
            domain_category = self._categorize_by_domain(url)
            pattern_category = self._categorize_by_url_patterns(url)
            folder_category = self._categorize_by_folder_path(folder_path)
            
            # Combine rule-based results
            rule_based_results = {
                'domain': domain_category,
                'pattern': pattern_category,
                'folder': folder_category
            }
            
            # If AI analysis is enabled and we have sufficient content
            if use_ai and (title or content):
                ai_results = await self._ai_categorize(url, title, content, rule_based_results)
                return ai_results
            else:
                # Fall back to rule-based categorization
                return self._finalize_rule_based_categorization(
                    url, title, rule_based_results, folder_path
                )
                
        except Exception as e:
            logger.error(f"Error categorizing bookmark {url}: {e}")
            return {
                'category': 'uncategorized',
                'tags': [],
                'confidence': 0.1,
                'reasoning': f'Error during categorization: {str(e)}',
                'method': 'error'
            }
    
    def _categorize_by_domain(self, url: str) -> Optional[str]:
        """Categorize based on domain matching"""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # Remove www. prefix
            if domain.startswith('www.'):
                domain = domain[4:]
            
            # Check exact domain matches
            if domain in self.domain_categories:
                return self.domain_categories[domain]
            
            # Check partial domain matches
            for known_domain, category in self.domain_categories.items():
                if known_domain in domain:
                    return category
            
            return None
            
        except Exception as e:
            logger.warning(f"Error parsing domain from {url}: {e}")
            return None
    
    def _categorize_by_url_patterns(self, url: str) -> Optional[str]:
        """Categorize based on URL path patterns"""
        try:
            for pattern, category in self.url_patterns.items():
                if re.search(pattern, url, re.IGNORECASE):
                    return category
            return None
        except Exception as e:
            logger.warning(f"Error matching URL patterns for {url}: {e}")
            return None
    
    def _categorize_by_folder_path(self, folder_path: str) -> Optional[str]:
        """Extract category from bookmark folder structure"""
        if not folder_path:
            return None
        
        # Normalize folder path
        folder_lower = folder_path.lower().strip()
        
        # Common folder name to category mappings
        folder_mappings = {
            'programming': 'development',
            'coding': 'development',
            'development': 'development',
            'tech': 'technology',
            'technology': 'technology',
            'tools': 'tools',
            'productivity': 'productivity',
            'design': 'design',
            'learning': 'learning',
            'education': 'education',
            'courses': 'education',
            'tutorials': 'tutorial',
            'documentation': 'documentation',
            'docs': 'documentation',
            'reference': 'reference',
            'news': 'news',
            'articles': 'articles',
            'blogs': 'blog',
            'social': 'social',
            'videos': 'video',
            'research': 'research',
            'work': 'professional',
            'business': 'business',
            'finance': 'finance',
            'health': 'health',
            'fitness': 'health',
            'travel': 'travel',
            'food': 'food',
            'recipes': 'food',
            'shopping': 'shopping',
            'entertainment': 'entertainment',
            'games': 'gaming',
            'gaming': 'gaming'
        }
        
        for folder_keyword, category in folder_mappings.items():
            if folder_keyword in folder_lower:
                return category
        
        return None
    
    async def _ai_categorize(
        self,
        url: str,
        title: str,
        content: str,
        rule_based_results: Dict[str, Optional[str]]
    ) -> Dict[str, Any]:
        """Use AI to enhance categorization with content analysis"""
        try:
            # Prepare context for AI analysis
            context_parts = []
            if url:
                context_parts.append(f"URL: {url}")
            if title:
                context_parts.append(f"Title: {title}")
            if content:
                # Limit content length for AI processing
                content_snippet = content[:1000] + ("..." if len(content) > 1000 else "")
                context_parts.append(f"Content snippet: {content_snippet}")
            
            # Include rule-based results as hints
            rule_hints = [cat for cat in rule_based_results.values() if cat]
            if rule_hints:
                context_parts.append(f"Initial categorization hints: {', '.join(rule_hints)}")
            
            context_text = "\n".join(context_parts)
            
            prompt = f"""Analyze this bookmark and provide intelligent categorization:

{context_text}

Please categorize this bookmark into ONE of these main categories:
- development (programming, coding, software development)
- technology (tech news, gadgets, innovations)
- education (courses, learning resources, tutorials)
- documentation (API docs, references, manuals)
- articles (blog posts, articles, written content)
- video (YouTube, video content, streaming)
- social (social media, networking, communities)
- productivity (tools, apps, workflow)
- design (UI/UX, graphics, creative tools)
- business (entrepreneurship, startups, business resources)
- news (current events, journalism, media)
- research (academic, scientific papers, studies)
- reference (wikis, dictionaries, quick reference)
- tools (utilities, software tools, services)
- entertainment (fun, games, leisure)
- health (wellness, fitness, medical)
- finance (money, investing, banking)
- travel (destinations, planning, guides)
- food (recipes, restaurants, cooking)
- shopping (e-commerce, products, deals)
- professional (career, networking, industry)
- uncategorized (if none fit well)

Also suggest 3-5 relevant tags that describe this bookmark's content or purpose.

Return as JSON with:
{{
  "category": "category_name",
  "tags": ["tag1", "tag2", "tag3"],
  "confidence": 0.95,
  "reasoning": "Brief explanation of categorization decision"
}}"""

            response = await self.ai_service.complete(
                prompt=prompt,
                system_prompt="You are an expert content curator. Provide accurate, consistent categorization.",
                temperature=0.1,  # Low temperature for consistent results
                response_format={"type": "json_object"}
            )
            
            try:
                import json
                ai_result = json.loads(response)
                
                # Validate and enhance the AI result
                category = ai_result.get('category', 'uncategorized')
                tags = ai_result.get('tags', [])
                confidence = min(float(ai_result.get('confidence', 0.8)), 1.0)
                reasoning = ai_result.get('reasoning', 'AI-based categorization')
                
                # Add rule-based tags if they provide value
                rule_categories = [cat for cat in rule_based_results.values() if cat and cat != category]
                for rule_cat in rule_categories:
                    if rule_cat not in tags and len(tags) < 7:  # Limit total tags
                        tags.append(rule_cat)
                
                return {
                    'category': category,
                    'tags': tags[:7],  # Limit to 7 tags
                    'confidence': confidence,
                    'reasoning': reasoning,
                    'method': 'ai_enhanced'
                }
                
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"Failed to parse AI categorization response: {e}")
                return self._finalize_rule_based_categorization(url, title, rule_based_results, "")
                
        except Exception as e:
            logger.error(f"AI categorization failed for {url}: {e}")
            return self._finalize_rule_based_categorization(url, title, rule_based_results, "")
    
    def _finalize_rule_based_categorization(
        self,
        url: str,
        title: str,
        rule_based_results: Dict[str, Optional[str]],
        folder_path: str
    ) -> Dict[str, Any]:
        """Finalize categorization using rule-based results only"""
        
        # Priority order: domain > pattern > folder
        category = None
        confidence = 0.6
        
        if rule_based_results['domain']:
            category = rule_based_results['domain']
            confidence = 0.8
        elif rule_based_results['pattern']:
            category = rule_based_results['pattern']
            confidence = 0.7
        elif rule_based_results['folder']:
            category = rule_based_results['folder']
            confidence = 0.6
        else:
            category = 'uncategorized'
            confidence = 0.3
        
        # Generate tags from available information
        tags = []
        
        # Add non-primary categories as tags
        for result_category in rule_based_results.values():
            if result_category and result_category != category:
                tags.append(result_category)
        
        # Add domain-based tag if available
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower().replace('www.', '')
            if domain and '.' in domain:
                domain_name = domain.split('.')[0]
                if len(domain_name) > 2 and domain_name not in tags:
                    tags.append(domain_name)
        except:
            pass
        
        # Add folder path as tag if different from category
        if folder_path and folder_path.lower() != category:
            folder_tag = folder_path.lower().replace(' ', '-')
            if folder_tag not in tags:
                tags.append(folder_tag)
        
        return {
            'category': category,
            'tags': tags[:5],  # Limit tags
            'confidence': confidence,
            'reasoning': f'Rule-based categorization: {category}',
            'method': 'rule_based'
        }
    
    async def categorize_bulk_bookmarks(
        self,
        bookmarks: List[Dict[str, str]],
        use_ai: bool = True,
        batch_size: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Categorize multiple bookmarks efficiently
        
        Args:
            bookmarks: List of bookmark dicts with url, title, content, folder_path
            use_ai: Whether to use AI for enhanced categorization
            batch_size: Number of bookmarks to process in each batch
            
        Returns:
            List of categorization results
        """
        results = []
        
        for i in range(0, len(bookmarks), batch_size):
            batch = bookmarks[i:i + batch_size]
            batch_results = []
            
            for bookmark in batch:
                result = await self.categorize_bookmark(
                    url=bookmark.get('url', ''),
                    title=bookmark.get('title', ''),
                    content=bookmark.get('content', ''),
                    folder_path=bookmark.get('folder_path', ''),
                    use_ai=use_ai
                )
                batch_results.append(result)
            
            results.extend(batch_results)
            logger.info(f"Processed bookmark batch {i//batch_size + 1}/{(len(bookmarks) + batch_size - 1)//batch_size}")
        
        return results