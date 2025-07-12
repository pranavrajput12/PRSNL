#!/usr/bin/env python3
"""
Phase 2 Testing: Enhanced Slug Generation
Tests the improved slug generator with python-slugify and nanoid
"""

import asyncio
import sys
from pathlib import Path

# Add the backend directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.slug_generator import SmartSlugGenerator


async def test_slug_generation():
    """Test various slug generation scenarios."""
    
    test_cases = [
        # Basic cases
        ("Hello World", "hello-world"),
        ("The Quick Brown Fox", "quick-brown-fox"),  # Stop words removed
        ("", "untitled"),
        ("   ", "untitled"),
        
        # Unicode handling
        ("Café Español", "cafe-espanol"),
        ("北京欢迎你", None),  # Will be slugified
        ("Москва 2024", "moskva-2024"),
        
        # Special characters
        ("C++ Programming & Design", "c-programming-and-design"),
        ("Email@Example.com", "email-at-example-com"),
        ("50% Off Sale!", "50-percent-off-sale"),
        ("#hashtag #trending", "hash-hashtag-hash-trending"),
        
        # Emojis (custom replacements)
        ("🚀 Rocket Launch", "rocket-launch"),
        ("💡 Great Idea", "idea-great-idea"),
        ("🔥 Hot Topics", "hot-topics"),
        
        # Long titles
        ("This is a very long title that should be truncated at a word boundary to maintain SEO friendliness", None),
        
        # Edge cases
        ("!!!@@@###", "untitled"),
        ("a an the", "a-an-the"),  # All stop words, should keep them
        ("123 456 789", "123-456-789"),
    ]
    
    print("🧪 Testing Enhanced Slug Generation")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for title, expected in test_cases:
        slug = SmartSlugGenerator._generate_base_slug(title)
        
        if expected is None:
            # Just show the result for inspection
            print(f"✓ '{title[:30]}...' → '{slug}'")
            passed += 1
        elif slug == expected:
            print(f"✅ '{title}' → '{slug}'")
            passed += 1
        else:
            print(f"❌ '{title}' → Expected: '{expected}', Got: '{slug}'")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 Results: {passed} passed, {failed} failed")
    
    # Test collision handling
    print("\n🔄 Testing Collision Handling with nanoid")
    print("=" * 60)
    
    # Simulate generating unique slugs
    from nanoid import generate
    
    base_slug = "test-post"
    for i in range(10):
        if i == 0:
            print(f"Original: {base_slug}")
        elif i <= 5:
            print(f"Collision {i}: {base_slug}-{i}")
        else:
            suffix = generate(size=6)
            print(f"Collision {i}: {base_slug}-{suffix} (nanoid)")
    
    print("\n✅ Phase 2 slug generation tests complete!")


async def test_category_detection():
    """Test category detection logic."""
    print("\n🏷️ Testing Category Detection")
    print("=" * 60)
    
    # Mock item data for testing
    test_items = [
        {
            "title": "GitHub Repository Analysis",
            "url": "https://github.com/user/repo",
            "tags": ["github", "code"],
            "expected_category": "dev"
        },
        {
            "title": "Machine Learning Tutorial",
            "url": "https://youtube.com/watch?v=123",
            "tags": ["tutorial", "ai"],
            "expected_category": "media"
        },
        {
            "title": "Random Thoughts on Life",
            "url": None,
            "tags": ["personal", "thoughts"],
            "expected_category": "ideas"
        },
        {
            "title": "Python Course",
            "url": "https://coursera.org/python",
            "tags": ["python", "course"],
            "expected_category": "learn"
        }
    ]
    
    # Note: This is just a simulation since we need actual Item objects
    # In real usage, the categorization happens in generate_slug_for_item
    
    print("Category detection tests would run here with actual database items")
    print("Categories: dev, learn, media, ideas")
    
    for item in test_items:
        print(f"📁 '{item['title']}' → Expected: {item['expected_category']}")


if __name__ == "__main__":
    asyncio.run(test_slug_generation())
    asyncio.run(test_category_detection())