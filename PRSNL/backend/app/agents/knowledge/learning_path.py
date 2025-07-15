"""
Learning Path Agent - Migrated to Crew.ai

This agent creates personalized learning paths based on content and user needs.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

from app.agents.base_agent import PRSNLBaseAgent
from app.agents import register_agent
from app.tools.knowledge_tools import KnowledgeGraphTool, ConnectionFinderTool
from app.tools.ai_tools import (
    SummaryGeneratorTool, 
    QuestionGeneratorTool,
    EnhancementSuggestionTool
)

logger = logging.getLogger(__name__)


@register_agent("learning_path")
class LearningPathAgent(PRSNLBaseAgent):
    """
    Learning Path Agent
    
    Specializes in creating structured learning paths that guide
    learners from basics to mastery in any subject.
    """
    
    def __init__(self, **kwargs):
        # Define the agent's role, goal, and backstory
        role = kwargs.pop("role", "Learning Path Creator")
        goal = kwargs.pop("goal", 
            "Design personalized, effective learning paths that guide learners "
            "from their current knowledge level to their desired expertise"
        )
        backstory = kwargs.pop("backstory",
            "You are a master educator and curriculum designer with decades of "
            "experience in adult learning and educational psychology. Your deep "
            "understanding of how people learn, combined with expertise in "
            "instructional design, allows you to create learning journeys that "
            "are both engaging and effective. You excel at breaking down complex "
            "topics into manageable steps and identifying the optimal sequence "
            "for knowledge acquisition."
        )
        
        # Initialize with specialized tools
        tools = kwargs.pop("tools", None)
        if tools is None:
            tools = [
                KnowledgeGraphTool(),
                ConnectionFinderTool(),
                SummaryGeneratorTool(),
                QuestionGeneratorTool(),
                EnhancementSuggestionTool()
            ]
        
        # Call parent constructor
        super().__init__(
            role=role,
            goal=goal,
            backstory=backstory,
            tools=tools,
            **kwargs
        )
    
    def get_specialized_instructions(self) -> str:
        """Get specialized instructions for this agent"""
        return """
        When creating learning paths:
        1. Assess prerequisite knowledge requirements
        2. Define clear learning objectives and outcomes
        3. Break down complex topics into digestible modules
        4. Sequence content for optimal knowledge building
        5. Identify key concepts and skills at each stage
        6. Include practical exercises and applications
        7. Add assessment checkpoints for progress tracking
        8. Provide multiple learning modalities (text, video, practice)
        9. Include real-world examples and case studies
        10. Design review and reinforcement activities
        11. Suggest time estimates for each module
        12. Offer alternative paths for different learning styles
        
        Focus on creating paths that are challenging yet achievable,
        with clear progression and measurable outcomes.
        """
    
    def assess_complexity_level(self, content: str) -> str:
        """Assess the complexity level of content"""
        # Simplified assessment based on indicators
        complexity_indicators = {
            "beginner": ["basic", "introduction", "fundamental", "overview", "getting started"],
            "intermediate": ["advanced", "detailed", "in-depth", "practical", "implementation"],
            "expert": ["expert", "mastery", "complex", "research", "cutting-edge", "theoretical"]
        }
        
        content_lower = content.lower()
        scores = {level: 0 for level in complexity_indicators}
        
        for level, indicators in complexity_indicators.items():
            for indicator in indicators:
                if indicator in content_lower:
                    scores[level] += 1
        
        # Return the level with highest score
        return max(scores, key=scores.get) if any(scores.values()) else "intermediate"
    
    def identify_prerequisites(self, topic: str, complexity: str) -> List[str]:
        """Identify prerequisite knowledge for a topic"""
        # This would ideally query the knowledge graph
        # For now, return general prerequisites based on complexity
        prerequisites = []
        
        if complexity == "intermediate":
            prerequisites.append(f"Basic understanding of {topic}")
            prerequisites.append("Familiarity with fundamental concepts")
        elif complexity == "expert":
            prerequisites.append(f"Intermediate knowledge of {topic}")
            prerequisites.append("Hands-on experience with practical applications")
            prerequisites.append("Understanding of theoretical foundations")
        
        return prerequisites
    
    def create_module_structure(self, 
                              topic: str,
                              learning_objectives: List[str],
                              duration_weeks: int = 8) -> List[Dict[str, Any]]:
        """Create a modular structure for the learning path"""
        modules = []
        
        # Calculate time per objective
        time_per_module = duration_weeks / len(learning_objectives) if learning_objectives else 1
        
        for i, objective in enumerate(learning_objectives):
            module = {
                "module_number": i + 1,
                "title": f"Module {i+1}: {objective}",
                "objective": objective,
                "duration_weeks": max(1, int(time_per_module)),
                "components": {
                    "theory": "Conceptual understanding",
                    "practice": "Hands-on exercises",
                    "project": "Real-world application",
                    "assessment": "Knowledge check"
                },
                "resources": [],
                "milestones": []
            }
            
            # Add progression milestones
            if i == 0:
                module["milestones"].append("Foundation established")
            elif i == len(learning_objectives) - 1:
                module["milestones"].append("Mastery achieved")
            else:
                module["milestones"].append("Intermediate competency")
            
            modules.append(module)
        
        return modules
    
    def design_assessment_strategy(self, modules: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Design assessment strategy for the learning path"""
        assessment_strategy = {
            "formative_assessments": [],
            "summative_assessments": [],
            "self_assessments": [],
            "practical_projects": []
        }
        
        for i, module in enumerate(modules):
            # Formative assessments (during learning)
            assessment_strategy["formative_assessments"].append({
                "module": module["module_number"],
                "type": "quiz",
                "purpose": "Check understanding of key concepts",
                "frequency": "End of each week"
            })
            
            # Self-assessments
            assessment_strategy["self_assessments"].append({
                "module": module["module_number"],
                "type": "reflection",
                "questions": [
                    "What key concepts did you learn?",
                    "How confident are you in applying these concepts?",
                    "What areas need more practice?"
                ]
            })
            
            # Summative assessments (end of module)
            if i % 2 == 1 or i == len(modules) - 1:  # Every 2 modules or at end
                assessment_strategy["summative_assessments"].append({
                    "after_module": module["module_number"],
                    "type": "comprehensive test",
                    "coverage": f"Modules {max(1, i-1)} to {i+1}"
                })
            
            # Practical projects
            if i >= len(modules) // 2:  # Second half of course
                assessment_strategy["practical_projects"].append({
                    "module": module["module_number"],
                    "type": "hands-on project",
                    "description": f"Apply concepts from module {module['module_number']}"
                })
        
        return assessment_strategy
    
    def recommend_learning_resources(self, 
                                   topic: str,
                                   level: str,
                                   learning_style: str = "mixed") -> Dict[str, List[str]]:
        """Recommend resources based on topic, level, and learning style"""
        resources = {
            "books": [],
            "online_courses": [],
            "videos": [],
            "interactive": [],
            "communities": [],
            "tools": []
        }
        
        # Resource recommendations based on level
        if level == "beginner":
            resources["books"].append(f"{topic} for Beginners")
            resources["online_courses"].append(f"Introduction to {topic}")
            resources["videos"].append(f"{topic} Crash Course")
            resources["interactive"].append(f"{topic} Interactive Tutorial")
        elif level == "intermediate":
            resources["books"].append(f"Practical {topic}")
            resources["online_courses"].append(f"{topic} in Practice")
            resources["videos"].append(f"Advanced {topic} Techniques")
            resources["tools"].append(f"{topic} Development Tools")
        else:  # expert
            resources["books"].append(f"Mastering {topic}")
            resources["communities"].append(f"{topic} Expert Forum")
            resources["tools"].append(f"Professional {topic} Suite")
        
        # Add learning style specific resources
        if learning_style == "visual":
            resources["videos"].append(f"{topic} Visual Guide")
            resources["interactive"].append(f"{topic} Infographics")
        elif learning_style == "hands-on":
            resources["interactive"].append(f"{topic} Sandbox")
            resources["tools"].append(f"{topic} Practice Environment")
        
        return resources


@register_agent("adaptive_learning_path")
class AdaptiveLearningPathAgent(LearningPathAgent):
    """
    Enhanced version that adapts based on learner progress and preferences
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Add adaptive learning tools
        from app.tools.learning_tools import (
            ProgressTrackerTool, 
            LearningStyleAnalyzerTool,
            DifficultyAdjusterTool
        )
        self.add_tool(ProgressTrackerTool())
        self.add_tool(LearningStyleAnalyzerTool())
        self.add_tool(DifficultyAdjusterTool())
    
    def get_specialized_instructions(self) -> str:
        """Enhanced instructions for adaptive learning"""
        base_instructions = super().get_specialized_instructions()
        return base_instructions + """
        
        Additional adaptive learning tasks:
        13. Monitor learner progress and adjust difficulty
        14. Identify learning style preferences
        15. Recommend personalized content based on performance
        16. Adjust pacing based on comprehension speed
        17. Provide remedial content for struggling areas
        18. Offer advanced challenges for quick learners
        19. Track engagement and motivation levels
        20. Suggest optimal study schedules
        """
    
    def adapt_path_to_learner(self, 
                            original_path: List[Dict[str, Any]],
                            learner_profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Adapt the learning path based on learner profile"""
        adapted_path = original_path.copy()
        
        # Adjust based on learning pace
        if learner_profile.get("pace") == "fast":
            # Compress timeline
            for module in adapted_path:
                module["duration_weeks"] = max(1, int(module["duration_weeks"] * 0.75))
        elif learner_profile.get("pace") == "slow":
            # Extend timeline
            for module in adapted_path:
                module["duration_weeks"] = int(module["duration_weeks"] * 1.5)
        
        # Adjust based on learning style
        style = learner_profile.get("learning_style", "mixed")
        for module in adapted_path:
            if style == "visual":
                module["components"]["video_content"] = "Primary learning mode"
                module["components"]["infographics"] = "Visual summaries"
            elif style == "hands-on":
                module["components"]["labs"] = "Practical exercises"
                module["components"]["simulations"] = "Interactive learning"
        
        # Add support based on struggle areas
        if "struggle_areas" in learner_profile:
            for area in learner_profile["struggle_areas"]:
                # Insert remedial module
                remedial_module = {
                    "module_number": "R",
                    "title": f"Remedial: {area}",
                    "objective": f"Strengthen understanding of {area}",
                    "duration_weeks": 1,
                    "components": {
                        "review": "Concept review",
                        "practice": "Extra exercises",
                        "tutoring": "One-on-one support"
                    }
                }
                adapted_path.insert(0, remedial_module)
        
        return adapted_path