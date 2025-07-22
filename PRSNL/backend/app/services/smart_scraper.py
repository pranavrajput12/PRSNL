"""
Smart Scraper Service - Uses Jina Reader first, Firecrawl as fallback
This saves Firecrawl credits while maintaining high success rates
"""
import asyncio
import logging
from typing import Dict, Any, Optional

from app.services.jina_reader import JinaReaderService
from app.services.firecrawl_service import FirecrawlService

logger = logging.getLogger(__name__)

class SmartScraperService:
    """Smart web scraper that optimizes cost by using free Jina first"""
    
    def __init__(self):
        self.jina = JinaReaderService()
        self.firecrawl = FirecrawlService()
        self.stats = {
            'jina_success': 0,
            'jina_failure': 0,
            'firecrawl_success': 0,
            'firecrawl_failure': 0,
            'total_requests': 0,
            'credits_saved': 0  # Estimated Firecrawl credits saved
        }
        
    async def scrape_url(self, url: str, force_firecrawl: bool = False) -> Dict[str, Any]:
        """
        Scrape URL using smart fallback strategy
        
        Args:
            url: URL to scrape
            force_firecrawl: Skip Jina and go directly to Firecrawl
            
        Returns:
            Dict with scraped content and metadata
        """
        self.stats['total_requests'] += 1
        
        # Skip Jina if forced to use Firecrawl
        if force_firecrawl:
            logger.info(f"🔥 Forced Firecrawl scraping: {url}")
            return await self._scrape_with_firecrawl(url)
        
        # Strategy 1: Try Jina Reader first (free)
        logger.info(f"📖 Attempting Jina Reader scraping: {url}")
        jina_result = await self._scrape_with_jina(url)
        
        if self._is_good_result(jina_result):
            self.stats['jina_success'] += 1
            self.stats['credits_saved'] += 1  # Saved 1 Firecrawl credit
            logger.info(f"✅ Jina success - saved 1 Firecrawl credit! ({len(jina_result['data']['content'])} chars)")
            # Ensure scraper_used is set correctly
            jina_result['scraper_used'] = 'jina'
            if 'data' in jina_result:
                jina_result['data']['scraper_used'] = 'jina'
            return jina_result
        
        # Strategy 2: Fallback to Firecrawl (costs credits)
        logger.warning(f"⚠️ Jina failed, falling back to Firecrawl: {url}")
        self.stats['jina_failure'] += 1
        return await self._scrape_with_firecrawl(url)
    
    async def _scrape_with_jina(self, url: str) -> Dict[str, Any]:
        """Try scraping with Jina Reader"""
        try:
            return await self.jina.scrape_url(url)
        except Exception as e:
            logger.error(f"Jina Reader error for {url}: {e}")
            return {
                "success": False,
                "error": f"Jina error: {str(e)}",
                "scraper_used": "jina"
            }
    
    async def _scrape_with_firecrawl(self, url: str) -> Dict[str, Any]:
        """Scrape with Firecrawl (costs credits)"""
        try:
            if not self.firecrawl.enabled:
                return {
                    "success": False,
                    "error": "Firecrawl not enabled",
                    "scraper_used": "firecrawl"
                }
            
            result = await self.firecrawl.scrape_url(url)
            
            if result.get('success'):
                self.stats['firecrawl_success'] += 1
                logger.info(f"🔥 Firecrawl success ({len(result['data']['content'])} chars)")
            else:
                self.stats['firecrawl_failure'] += 1
                logger.error(f"Firecrawl failed for {url}: {result.get('error')}")
            
            # Add scraper info to result
            if 'data' in result:
                result['data']['scraper_used'] = 'firecrawl'
            result['scraper_used'] = 'firecrawl'
            
            return result
            
        except Exception as e:
            self.stats['firecrawl_failure'] += 1
            logger.error(f"Firecrawl error for {url}: {e}")
            return {
                "success": False,
                "error": f"Firecrawl error: {str(e)}",
                "scraper_used": "firecrawl"
            }
    
    def _is_good_result(self, result: Dict[str, Any]) -> bool:
        """
        Determine if Jina result is good enough to avoid Firecrawl
        
        Criteria:
        - Success = True
        - Content length > 100 chars
        - Content is not just error messages
        """
        if not result.get('success'):
            return False
        
        data = result.get('data', {})
        content = data.get('content', '')
        
        # Check content quality
        if len(content) < 100:
            logger.debug(f"Jina content too short: {len(content)} chars")
            return False
        
        # Check for common error indicators
        error_indicators = [
            'access denied',
            'page not found',
            '404',
            'forbidden',
            'blocked',
            'captcha',
            'please enable javascript',
            'bot detected'
        ]
        
        content_lower = content.lower()
        for indicator in error_indicators:
            if indicator in content_lower:
                logger.debug(f"Jina content contains error indicator: {indicator}")
                return False
        
        logger.debug(f"Jina result quality check passed: {len(content)} chars")
        return True
    
    def get_stats(self) -> Dict[str, Any]:
        """Get scraping statistics"""
        total_success = self.stats['jina_success'] + self.stats['firecrawl_success']
        total_attempts = self.stats['total_requests']
        
        return {
            **self.stats,
            'success_rate': (total_success / total_attempts * 100) if total_attempts > 0 else 0,
            'jina_success_rate': (self.stats['jina_success'] / total_attempts * 100) if total_attempts > 0 else 0,
            'cost_savings': f"{self.stats['credits_saved']} Firecrawl credits saved"
        }
    
    def log_stats(self):
        """Log current statistics"""
        stats = self.get_stats()
        logger.info("📊 Smart Scraper Statistics:")
        logger.info(f"  Total requests: {stats['total_requests']}")
        logger.info(f"  Success rate: {stats['success_rate']:.1f}%")
        logger.info(f"  Jina success: {stats['jina_success']} ({stats['jina_success_rate']:.1f}%)")
        logger.info(f"  Firecrawl success: {stats['firecrawl_success']}")
        logger.info(f"  💰 Credits saved: {stats['credits_saved']}")

# Global instance
smart_scraper = SmartScraperService()