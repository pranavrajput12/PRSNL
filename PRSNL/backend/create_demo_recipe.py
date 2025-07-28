#!/usr/bin/env python3
"""
Create a demo recipe entry for testing the recipe template
"""
import asyncio
import sys
import uuid
import json
from datetime import datetime
sys.path.append('.')

import asyncpg
from app.config import settings


async def create_demo_recipe():
    """Create a demo recipe entry in the database"""
    
    # Sample recipe data - Sunny Anderson's Easy Grilled Pork Chops
    recipe_data = {
        "title": "Easy Grilled Pork Chops",
        "description": "These perfectly seasoned pork chops are grilled to juicy perfection with a simple rub and quick cooking technique.",
        "ingredients": [
            {
                "name": "bone-in pork chops",
                "quantity": "4",
                "unit": "pieces",
                "notes": "1-inch thick",
                "category": "meat"
            },
            {
                "name": "olive oil",
                "quantity": "2",
                "unit": "tablespoons",
                "notes": "for coating",
                "category": "oil"
            },
            {
                "name": "garlic powder",
                "quantity": "1",
                "unit": "teaspoon",
                "notes": "",
                "category": "spice"
            },
            {
                "name": "onion powder",
                "quantity": "1",
                "unit": "teaspoon",
                "notes": "",
                "category": "spice"
            },
            {
                "name": "paprika",
                "quantity": "1",
                "unit": "teaspoon",
                "notes": "",
                "category": "spice"
            },
            {
                "name": "salt",
                "quantity": "1",
                "unit": "teaspoon",
                "notes": "",
                "category": "seasoning"
            },
            {
                "name": "black pepper",
                "quantity": "1/2",
                "unit": "teaspoon",
                "notes": "freshly ground",
                "category": "seasoning"
            }
        ],
        "steps": [
            {
                "step_number": 1,
                "instruction": "Preheat your grill to medium-high heat, about 400°F.",
                "time_minutes": 10,
                "temperature": "400°F",
                "equipment": "grill",
                "tips": "Make sure grill grates are clean for best results"
            },
            {
                "step_number": 2,
                "instruction": "Pat pork chops dry with paper towels and brush both sides with olive oil.",
                "time_minutes": 2,
                "temperature": None,
                "equipment": "paper towels",
                "tips": "Dry chops sear better and hold seasoning"
            },
            {
                "step_number": 3,
                "instruction": "In a small bowl, mix together garlic powder, onion powder, paprika, salt, and pepper.",
                "time_minutes": 1,
                "temperature": None,
                "equipment": "small bowl",
                "tips": "Mix spices thoroughly for even distribution"
            },
            {
                "step_number": 4,
                "instruction": "Season both sides of the pork chops generously with the spice mixture.",
                "time_minutes": 2,
                "temperature": None,
                "equipment": None,
                "tips": "Press seasoning into meat gently to help it adhere"
            },
            {
                "step_number": 5,
                "instruction": "Grill pork chops for 4-5 minutes on the first side without moving them.",
                "time_minutes": 5,
                "temperature": "400°F",
                "equipment": "grill",
                "tips": "Don't flip too early - let them develop a good sear"
            },
            {
                "step_number": 6,
                "instruction": "Flip and grill for another 4-5 minutes until internal temperature reaches 145°F.",
                "time_minutes": 5,
                "temperature": "145°F internal",
                "equipment": "meat thermometer",
                "tips": "Use a meat thermometer for best results"
            },
            {
                "step_number": 7,
                "instruction": "Remove from grill and let rest for 3 minutes before serving.",
                "time_minutes": 3,
                "temperature": None,
                "equipment": None,
                "tips": "Resting allows juices to redistribute for tender meat"
            }
        ],
        "prep_time_minutes": 5,
        "cook_time_minutes": 20,
        "total_time_minutes": 25,
        "servings": 4,
        "difficulty": "easy",
        "cuisine_type": "American",
        "dietary_info": ["gluten-free", "dairy-free"],
        "nutritional_info": {
            "calories": "320",
            "protein": "28g",
            "fat": "22g",
            "carbs": "1g",
            "fiber": "0g"
        },
        "voice_friendly_summary": "Season four pork chops with a simple spice rub, then grill for about 5 minutes per side until they reach 145 degrees internal temperature. Let them rest for 3 minutes before serving.",
        "tips_and_notes": [
            "Choose chops that are at least 1-inch thick to prevent overcooking",
            "Don't skip the resting period - it makes a big difference in juiciness",
            "These chops pair perfectly with grilled vegetables or a fresh salad",
            "Leftover chops can be sliced and used in sandwiches or salads"
        ]
    }
    
    item_id = str(uuid.uuid4())
    user_id = "demo-user-123"
    url = "https://www.foodnetwork.com/recipes/sunny-anderson/easy-grilled-pork-chops-recipe-2106547"
    
    try:
        # Connect to database
        conn = await asyncpg.connect(settings.DATABASE_URL)
        
        # Insert the recipe item
        await conn.execute("""
            INSERT INTO items (
                id, user_id, url, title, content, content_type, type,
                status, metadata, created_at, updated_at
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11
            )
        """, 
        item_id,
        user_id,
        url,
        recipe_data["title"],
        "Recipe content processed and structured for cooking interface",
        "recipe",
        "article",  # Set type to article for recipe content
        "completed",
        json.dumps({"recipe_data": recipe_data}),
        datetime.utcnow(),
        datetime.utcnow()
        )
        
        # Create a permalink for the recipe (skip if table doesn't exist)
        permalink = f"easy-grilled-pork-chops-{item_id[:8]}"
        
        try:
            await conn.execute("""
                INSERT INTO permalinks (id, item_id, slug, created_at)
                VALUES ($1, $2, $3, $4)
            """,
            str(uuid.uuid4()),
            item_id,
            permalink,
            datetime.utcnow()
            )
        except asyncpg.UndefinedTableError:
            print("⚠️ Permalinks table doesn't exist, skipping permalink creation")
            permalink = None
        
        await conn.close()
        
        print(f"✅ Demo recipe created successfully!")
        print(f"📋 Item ID: {item_id}")
        print(f"🔗 URL: {url}")
        print(f"📌 Permalink: /thoughts/{permalink}")
        print(f"🍽️ Recipe: {recipe_data['title']}")
        print(f"⏱️ Total time: {recipe_data['total_time_minutes']} minutes")
        print(f"👥 Serves: {recipe_data['servings']} people")
        print()
        print(f"🌐 View in browser:")
        if permalink:
            print(f"   http://localhost:3004/thoughts/{permalink}")
        print(f"   http://localhost:3004/recipe/{item_id}")
        
    except Exception as e:
        print(f"❌ Error creating demo recipe: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    asyncio.run(create_demo_recipe())