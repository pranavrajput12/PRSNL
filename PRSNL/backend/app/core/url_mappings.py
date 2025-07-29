"""
Centralized URL Mappings for PRSNL Backend
Mirrors the frontend urlMappings.ts for consistency
"""

# Type to route mapping (singular -> plural)
TYPE_TO_ROUTE = {
    # Core content types
    'article': 'articles',
    'video': 'videos',
    'recipe': 'recipes',
    'bookmark': 'bookmarks',
    'code': 'code',
    'document': 'documents',
    'conversation': 'conversations',
    'repository': 'repositories',
    'screenshot': 'screenshots',
    'item': 'items',
    
    # Common aliases
    'link': 'bookmarks',
    'url': 'bookmarks',
    'repo': 'repositories',
    'doc': 'documents',
    'docs': 'documents',
    'convo': 'conversations',
    'chat': 'conversations',
    'screen': 'screenshots',
    'capture': 'screenshots',
    'snippet': 'code',
    'script': 'code',
    'vid': 'videos',
    'movie': 'videos',
    'clip': 'videos',
    
    # Plurals map to themselves
    'articles': 'articles',
    'videos': 'videos',
    'recipes': 'recipes',
    'bookmarks': 'bookmarks',
    'documents': 'documents',
    'conversations': 'conversations',
    'repositories': 'repositories',
    'screenshots': 'screenshots',
    'items': 'items'
}

# Route to canonical type mapping
ROUTE_TO_TYPE = {
    'articles': 'article',
    'videos': 'video',
    'recipes': 'recipe',
    'bookmarks': 'bookmark',
    'code': 'code',
    'documents': 'document',
    'conversations': 'conversation',
    'repositories': 'repository',
    'screenshots': 'screenshot',
    'items': 'item'
}

def get_route_for_type(item_type: str = None) -> str:
    """Get the route path for a given content type"""
    if not item_type:
        return 'items'
    
    normalized_type = item_type.lower().strip()
    return TYPE_TO_ROUTE.get(normalized_type, 'items')

def get_type_for_route(route: str) -> str:
    """Get the canonical type for a route path"""
    return ROUTE_TO_TYPE.get(route, 'item')

def generate_permalink(item_type: str, item_id: str) -> str:
    """
    Generate a permalink for an item
    Simple pattern: /[type]/[id] (no /library prefix)
    """
    route = get_route_for_type(item_type)
    return f"/{route}/{item_id}"

def generate_permalink_sql() -> str:
    """
    Generate SQL CASE statement for permalink generation
    Used in database queries for consistent URL generation
    """
    cases = []
    for canonical_type, route in ROUTE_TO_TYPE.items():
        if canonical_type != 'item':  # Skip generic item type
            cases.append(f"WHEN i.type = '{route}' THEN '/{canonical_type}/' || i.id")
    
    # Default case
    cases.append("ELSE '/items/' || i.id")
    
    return "CASE " + " ".join(cases) + " END"