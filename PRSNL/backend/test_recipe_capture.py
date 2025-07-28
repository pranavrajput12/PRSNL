#!/usr/bin/env python3
"""
Test script for recipe URL capture and processing
"""
import asyncio
import sys
import os
sys.path.append('.')

from app.core.capture_engine import CaptureEngine
from app.services.unified_ai_service import UnifiedAIService
from app.utils.url_classifier import URLClassifier
from app.services.smart_scraper import SmartScraperService


async def test_recipe_capture():
    """Test the complete recipe capture pipeline"""
    url = 'https://www.foodnetwork.com/recipes/sunny-anderson/easy-grilled-pork-chops-recipe-2106547'
    print(f'🧪 Testing recipe capture for: {url}')
    print('=' * 80)
    
    try:
        # Step 1: Test URL classification
        print('📋 Step 1: URL Classification')
        classification = URLClassifier.classify_url(url)
        print(f'✅ Classification result: {classification}')
        print()
        
        # Step 2: Test web scraping
        print('🌐 Step 2: Web Scraping')
        scraper = SmartScraperService()
        scraped_result = await scraper.scrape_url(url)
        
        # Create a simple data structure similar to what's expected
        class ScrapedData:
            def __init__(self, result_dict):
                self.content = result_dict.get('content', '')
                self.title = result_dict.get('title', 'Unknown Recipe')
                self.description = result_dict.get('description', None)
        
        scraped_data = ScrapedData(scraped_result)
        print(f'✅ Title: {scraped_data.title}')
        print(f'✅ Content length: {len(scraped_data.content)} characters')
        print(f'✅ Description: {scraped_data.description[:200] if scraped_data.description else "None"}...')
        print()
        
        # Step 3: Test recipe extraction
        print('🍳 Step 3: Recipe Data Extraction')
        unified_ai = UnifiedAIService()
        recipe_data = await unified_ai.extract_recipe_data(
            content=scraped_data.content,
            url=url,
            title=scraped_data.title
        )
        
        if recipe_data:
            print(f'✅ Recipe Title: {recipe_data.get("title", "N/A")}')
            print(f'✅ Description: {recipe_data.get("description", "N/A")[:100]}...')
            print(f'✅ Prep Time: {recipe_data.get("prep_time_minutes", "N/A")} minutes')
            print(f'✅ Cook Time: {recipe_data.get("cook_time_minutes", "N/A")} minutes')
            print(f'✅ Servings: {recipe_data.get("servings", "N/A")}')
            print(f'✅ Difficulty: {recipe_data.get("difficulty", "N/A")}')
            
            ingredients = recipe_data.get("ingredients", [])
            print(f'✅ Ingredients count: {len(ingredients)}')
            if ingredients:
                print('   Sample ingredients:')
                for i, ingredient in enumerate(ingredients[:3]):
                    print(f'   - {ingredient.get("quantity", "")} {ingredient.get("unit", "")} {ingredient.get("name", "Unknown")}')
            
            steps = recipe_data.get("steps", [])
            print(f'✅ Steps count: {len(steps)}')
            if steps:
                print('   Sample steps:')
                for i, step in enumerate(steps[:2]):
                    print(f'   {step.get("step_number", i+1)}. {step.get("instruction", "")[:100]}...')
                    
            dietary_info = recipe_data.get("dietary_info", [])
            if dietary_info:
                print(f'✅ Dietary info: {", ".join(dietary_info)}')
                
            tips = recipe_data.get("tips_and_notes", [])
            if tips:
                print(f'✅ Tips and notes: {len(tips)} items')
        else:
            print('❌ No recipe data extracted')
        
        print()
        print('🎉 Recipe capture test completed successfully!')
        
    except Exception as e:
        print(f'❌ Error during test: {str(e)}')
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    asyncio.run(test_recipe_capture())