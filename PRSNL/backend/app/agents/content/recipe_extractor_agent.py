"""
Recipe Extractor Agent for parsing cooking content
Specialized CrewAI agent for extracting structured recipe information
"""

import logging
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
import re
from crewai import Agent, Task, Crew
from app.config import settings

logger = logging.getLogger(__name__)

@dataclass
class Ingredient:
    """Structured ingredient with quantity and unit"""
    name: str
    quantity: Optional[str] = None
    unit: Optional[str] = None
    notes: Optional[str] = None  # e.g., "finely chopped", "room temperature"
    category: Optional[str] = None  # e.g., "produce", "protein", "dairy"

@dataclass
class CookingStep:
    """Individual cooking step with timing and equipment"""
    step_number: int
    instruction: str
    time_minutes: Optional[int] = None
    temperature: Optional[str] = None
    equipment: Optional[str] = None
    tips: Optional[str] = None

@dataclass
class RecipeData:
    """Complete structured recipe information"""
    title: str
    description: Optional[str] = None
    ingredients: List[Ingredient] = None
    steps: List[CookingStep] = None
    prep_time_minutes: Optional[int] = None
    cook_time_minutes: Optional[int] = None
    total_time_minutes: Optional[int] = None
    servings: Optional[int] = None
    difficulty: Optional[str] = None  # easy, medium, hard
    cuisine_type: Optional[str] = None
    dietary_info: List[str] = None  # vegetarian, vegan, gluten-free, etc.
    nutritional_info: Optional[Dict[str, str]] = None
    voice_friendly_summary: Optional[str] = None
    tips_and_notes: List[str] = None

class RecipeExtractorAgent:
    """CrewAI agent specialized in extracting structured recipe information"""
    
    def __init__(self):
        self.agent = Agent(
            role="Recipe Content Extractor",
            goal="Extract structured recipe information including ingredients, steps, timing, and cooking details",
            backstory="""You are a professional culinary assistant with expertise in parsing 
            recipe content. You excel at identifying ingredients with precise quantities, 
            organizing cooking steps logically, and extracting timing information for 
            perfect meal preparation. You understand cooking techniques, ingredient 
            substitutions, and can create voice-friendly summaries for hands-free cooking.""",
            verbose=True,
            allow_delegation=False
        )
    
    async def extract_recipe(
        self,
        content: str,
        url: Optional[str] = None,
        title: Optional[str] = None
    ) -> RecipeData:
        """
        Extract structured recipe information from content
        
        Args:
            content: Raw recipe content (HTML or text)
            url: Source URL for context
            title: Page title if available
            
        Returns:
            RecipeData object with structured recipe information
        """
        try:
            # Create extraction task
            extraction_task = Task(
                description=f"""
                Analyze the following recipe content and extract structured information:
                
                Content: {content[:3000]}...
                URL: {url or 'Not provided'}
                Title: {title or 'Not provided'}
                
                Extract and structure the following information:
                1. Recipe title and description
                2. Complete ingredients list with quantities, units, and preparation notes
                3. Step-by-step cooking instructions with timing and equipment
                4. Prep time, cook time, and total time
                5. Number of servings
                6. Difficulty level (easy/medium/hard)
                7. Cuisine type if identifiable
                8. Dietary information (vegetarian, vegan, gluten-free, etc.)
                9. Nutritional information if available
                10. Helpful tips and notes
                11. Create a voice-friendly summary for hands-free cooking
                
                Focus on accuracy and completeness. If timing isn't explicit, make reasonable estimates.
                """,
                agent=self.agent,
                expected_output="""
                A comprehensive recipe analysis with all available information structured clearly.
                Include specific quantities, units, and detailed cooking instructions.
                """
            )
            
            # Execute extraction
            crew = Crew(
                agents=[self.agent],
                tasks=[extraction_task],
                verbose=True
            )
            
            result = crew.kickoff()
            
            # Parse the result into structured format
            recipe_data = self._parse_extraction_result(result, content, title)
            
            logger.info(f"Successfully extracted recipe: {recipe_data.title}")
            return recipe_data
            
        except Exception as e:
            logger.error(f"Error extracting recipe: {str(e)}")
            # Return basic recipe with minimal parsing
            return self._fallback_recipe_extraction(content, title)
    
    def _parse_extraction_result(
        self, 
        result: str, 
        original_content: str, 
        title: Optional[str]
    ) -> RecipeData:
        """Parse the AI extraction result into structured RecipeData"""
        
        # Initialize recipe data
        recipe = RecipeData(
            title=title or "Recipe",
            ingredients=[],
            steps=[],
            dietary_info=[],
            tips_and_notes=[]
        )
        
        try:
            # Extract basic information with regex patterns
            result_lower = result.lower()
            
            # Extract timing information
            prep_match = re.search(r'prep(?:\s+time)?[:\s]*(\d+)(?:\s*(?:min|minutes))?', result_lower)
            if prep_match:
                recipe.prep_time_minutes = int(prep_match.group(1))
            
            cook_match = re.search(r'cook(?:\s+time)?[:\s]*(\d+)(?:\s*(?:min|minutes))?', result_lower)
            if cook_match:
                recipe.cook_time_minutes = int(cook_match.group(1))
            
            total_match = re.search(r'total(?:\s+time)?[:\s]*(\d+)(?:\s*(?:min|minutes))?', result_lower)
            if total_match:
                recipe.total_time_minutes = int(total_match.group(1))
            
            # Extract servings
            servings_match = re.search(r'(?:serves?|servings?)[:\s]*(\d+)', result_lower)
            if servings_match:
                recipe.servings = int(servings_match.group(1))
            
            # Extract ingredients (basic parsing)
            ingredients_section = self._extract_section(result, "ingredients")
            if ingredients_section:
                recipe.ingredients = self._parse_ingredients(ingredients_section)
            
            # Extract steps
            steps_section = self._extract_section(result, "(?:instructions|steps|method)")
            if steps_section:
                recipe.steps = self._parse_steps(steps_section)
            
            # Extract dietary info
            dietary_keywords = ['vegetarian', 'vegan', 'gluten-free', 'dairy-free', 'keto', 'paleo']
            for keyword in dietary_keywords:
                if keyword in result_lower:
                    recipe.dietary_info.append(keyword)
            
            # Extract difficulty
            if 'easy' in result_lower:
                recipe.difficulty = 'easy'
            elif 'hard' in result_lower or 'difficult' in result_lower:
                recipe.difficulty = 'hard'
            else:
                recipe.difficulty = 'medium'
            
            # Create voice-friendly summary
            recipe.voice_friendly_summary = self._create_voice_summary(recipe)
            
        except Exception as e:
            logger.warning(f"Error parsing extraction result: {e}")
        
        return recipe
    
    def _extract_section(self, text: str, section_pattern: str) -> Optional[str]:
        """Extract a specific section from the text"""
        pattern = rf'{section_pattern}[:\s]*\n(.*?)(?:\n[A-Z][a-z]+:|$)'
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        return match.group(1).strip() if match else None
    
    def _parse_ingredients(self, ingredients_text: str) -> List[Ingredient]:
        """Parse ingredients from text into structured format"""
        ingredients = []
        lines = ingredients_text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith(('-', '•', '*')):
                line = line.lstrip('-•* ').strip()
            
            if line:
                ingredient = self._parse_single_ingredient(line)
                if ingredient:
                    ingredients.append(ingredient)
        
        return ingredients
    
    def _parse_single_ingredient(self, line: str) -> Optional[Ingredient]:
        """Parse a single ingredient line"""
        if not line.strip():
            return None
            
        # Basic ingredient parsing with regex
        # Pattern: quantity unit ingredient (notes)
        pattern = r'^\s*(\d+(?:\.\d+)?(?:/\d+)?)\s*(\w+)?\s+(.+?)(?:\s*\(([^)]+)\))?\s*$'
        match = re.match(pattern, line)
        
        if match:
            quantity, unit, name, notes = match.groups()
            return Ingredient(
                name=name.strip(),
                quantity=quantity,
                unit=unit,
                notes=notes
            )
        else:
            # If no pattern match, treat as ingredient name only
            return Ingredient(name=line.strip())
    
    def _parse_steps(self, steps_text: str) -> List[CookingStep]:
        """Parse cooking steps from text"""
        steps = []
        lines = steps_text.split('\n')
        step_number = 1
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Remove step numbering if present
            line = re.sub(r'^\d+\.?\s*', '', line)
            
            if line:
                # Extract timing from step
                time_match = re.search(r'(\d+)(?:\s*(?:min|minutes))', line.lower())
                time_minutes = int(time_match.group(1)) if time_match else None
                
                # Extract temperature
                temp_match = re.search(r'(\d+)°?[CF]', line)
                temperature = temp_match.group(0) if temp_match else None
                
                step = CookingStep(
                    step_number=step_number,
                    instruction=line,
                    time_minutes=time_minutes,
                    temperature=temperature
                )
                steps.append(step)
                step_number += 1
        
        return steps
    
    def _create_voice_summary(self, recipe: RecipeData) -> str:
        """Create a voice-friendly summary for hands-free cooking"""
        summary_parts = []
        
        # Basic info
        if recipe.servings:
            summary_parts.append(f"This recipe serves {recipe.servings} people")
        
        if recipe.total_time_minutes:
            summary_parts.append(f"and takes about {recipe.total_time_minutes} minutes total")
        elif recipe.prep_time_minutes and recipe.cook_time_minutes:
            total = recipe.prep_time_minutes + recipe.cook_time_minutes
            summary_parts.append(f"and takes about {total} minutes total")
        
        # Difficulty
        if recipe.difficulty:
            summary_parts.append(f"This is an {recipe.difficulty} recipe")
        
        # Key ingredients
        if recipe.ingredients and len(recipe.ingredients) > 0:
            key_ingredients = [ing.name for ing in recipe.ingredients[:3]]
            summary_parts.append(f"Main ingredients include {', '.join(key_ingredients)}")
        
        return ". ".join(summary_parts) + "."
    
    def _fallback_recipe_extraction(
        self, 
        content: str, 
        title: Optional[str]
    ) -> RecipeData:
        """Fallback recipe extraction using basic text parsing"""
        
        recipe = RecipeData(
            title=title or "Recipe",
            description="Recipe extracted with basic parsing",
            ingredients=[],
            steps=[],
            difficulty="medium"
        )
        
        # Basic ingredient detection
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if line and any(keyword in line.lower() for keyword in ['cup', 'tbsp', 'tsp', 'pound', 'oz']):
                ingredient = Ingredient(name=line)
                recipe.ingredients.append(ingredient)
        
        # Basic step detection
        step_num = 1
        for line in lines:
            line = line.strip()
            if line and len(line) > 20 and any(verb in line.lower() for verb in ['mix', 'cook', 'bake', 'add', 'heat']):
                step = CookingStep(
                    step_number=step_num,
                    instruction=line
                )
                recipe.steps.append(step)
                step_num += 1
        
        recipe.voice_friendly_summary = "Recipe extracted with basic text parsing. Please review for accuracy."
        
        return recipe