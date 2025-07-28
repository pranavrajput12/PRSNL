#!/usr/bin/env python3
"""
Test the enhanced URL classification system with domain cache
"""
import sys
sys.path.append('.')

from app.utils.url_classifier import URLClassifier
from app.utils.domain_classification_cache import domain_cache
from time import time


def test_classification_speed():
    """Test classification speed and accuracy"""
    
    test_urls = [
        "https://www.foodnetwork.com/recipes/sunny-anderson/easy-grilled-pork-chops-recipe-2106547",
        "https://allrecipes.com/recipe/231506/simple-macaroni-and-cheese/",
        "https://github.com/microsoft/typescript",
        "https://stackoverflow.com/questions/python/async-await",
        "https://youtube.com/watch?v=abc123",
        "https://epicurious.com/recipes/food/views/chocolate-chip-cookies",
        "https://seriouseats.com/the-best-pizza-dough-recipe",
        "https://docs.python.org/3/library/asyncio.html",
    ]
    
    print("🧪 Testing Enhanced URL Classification System")
    print("=" * 60)
    
    total_time = 0
    for url in test_urls:
        start_time = time()
        result = URLClassifier.classify_url(url)
        end_time = time()
        
        duration_ms = (end_time - start_time) * 1000
        total_time += duration_ms
        
        print(f"🔗 {url}")
        print(f"   ⚡ Time: {duration_ms:.2f}ms")
        print(f"   📋 Type: {result['content_type']}")
        print(f"   🏷️  Platform: {result['platform']}")
        print(f"   📊 Confidence: {result['metadata'].get('classification_confidence', 'N/A')}")
        print(f"   🔍 Method: {result['metadata'].get('classification_method', 'pattern_match')}")
        if result['content_type'] == 'recipe':
            recipe_meta = result['metadata'].get('recipe', {})
            print(f"   🍳 Recipe Name: {recipe_meta.get('recipe_name_from_url', 'N/A')}")
        print()
    
    avg_time = total_time / len(test_urls)
    print(f"📈 Performance Summary:")
    print(f"   Average time per URL: {avg_time:.2f}ms")
    print(f"   Total time: {total_time:.2f}ms")
    print()
    
    # Show cache statistics
    stats = domain_cache.get_stats()
    print(f"📊 Cache Statistics:")
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"   {key}: {value:.2%}" if 'rate' in key else f"   {key}: {value:.2f}")
        else:
            print(f"   {key}: {value}")
    
    print()
    print(f"🎯 Supported Recipe Domains ({len(domain_cache.get_supported_domains('recipe'))}):")
    for domain in sorted(domain_cache.get_supported_domains('recipe')):
        confidence = domain_cache.get_confidence_for_domain(domain)
        print(f"   • {domain} ({confidence:.0%})")


if __name__ == '__main__':
    test_classification_speed()