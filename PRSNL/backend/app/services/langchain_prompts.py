"""
LangChain Prompt Templates - Centralized prompt management
Replaces hardcoded prompts with versioned, reusable templates
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

try:
    from langchain.prompts import (
        ChatPromptTemplate,
        SystemMessagePromptTemplate,
        HumanMessagePromptTemplate,
        PromptTemplate,
        FewShotPromptTemplate
    )
    from langchain_core.messages import SystemMessage, HumanMessage
    from langchain.prompts.example_selector import LengthBasedExampleSelector
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    ChatPromptTemplate = None
    PromptTemplate = None

logger = logging.getLogger(__name__)


class PromptTemplateManager:
    """
    Centralized prompt template management using LangChain
    
    Features:
    - Versioned prompt templates
    - Variable substitution
    - Few-shot examples
    - Template composition
    - Prompt optimization tracking
    """
    
    def __init__(self):
        self.enabled = LANGCHAIN_AVAILABLE
        self.templates = {}
        self.examples = {}
        self.template_versions = {}
        
        if self.enabled:
            self._initialize_templates()
        else:
            logger.warning("LangChain prompts disabled. Using fallback strings.")
    
    def _initialize_templates(self):
        """Initialize all prompt templates"""
        try:
            # Content Analysis Templates
            self._create_content_analysis_templates()
            
            # Summarization Templates
            self._create_summarization_templates()
            
            # Tag Generation Templates
            self._create_tag_generation_templates()
            
            # Relationship Discovery Templates
            self._create_relationship_templates()
            
            # Insights Generation Templates
            self._create_insights_templates()
            
            # Categorization Templates
            self._create_categorization_templates()
            
            # Learning Path Templates
            self._create_learning_path_templates()
            
            logger.info("Prompt templates initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize prompt templates: {e}")
            self.enabled = False
    
    def _create_content_analysis_templates(self):
        """Create templates for content analysis"""
        # System prompt for content analysis
        system_template = SystemMessagePromptTemplate.from_template(
            "You are an expert content analyst with {expertise_areas}. "
            "Analyze the given content and provide a comprehensive analysis in JSON format. "
            "Focus on {analysis_focus} and ensure high accuracy."
        )
        
        # Human prompt for content analysis
        human_template = HumanMessagePromptTemplate.from_template(
            """Analyze this content and provide a detailed analysis:

URL: {url}
Content Type: {content_type}
Content: {content}

Provide analysis in this exact JSON format:
{{
    "title": "{title_guidance}",
    "summary": "{summary_guidance}",
    "detailed_summary": "A comprehensive paragraph summary",
    "category": "One of: {categories}",
    "tags": [{tag_guidance}],
    "key_points": [{key_points_guidance}],
    "entities": {{
        "people": ["mentioned people"],
        "organizations": ["mentioned orgs"],
        "technologies": ["mentioned tech/tools"],
        "concepts": ["key concepts discussed"]
    }},
    "sentiment": "{sentiment_options}",
    "difficulty_level": "{difficulty_options}",
    "estimated_reading_time": {time_calculation}
}}

{additional_instructions}"""
        )
        
        # Compose the chat template
        self.templates['content_analysis'] = ChatPromptTemplate.from_messages([
            system_template,
            human_template
        ])
        
        # Set default variables
        self.templates['content_analysis_defaults'] = {
            'expertise_areas': 'knowledge management, content classification, and information extraction',
            'analysis_focus': 'accuracy, comprehensiveness, and actionable insights',
            'title_guidance': 'The original title or a clear, descriptive title based on the content (max 100 chars)',
            'summary_guidance': 'A concise 2-3 sentence summary',
            'categories': 'article, tutorial, reference, news, discussion, video, other',
            'tag_guidance': '"up to 10 relevant tags", "lowercase", "specific"',
            'key_points_guidance': '"3-5 main takeaways", "actionable insights"',
            'sentiment_options': 'positive|neutral|negative|mixed',
            'difficulty_options': 'beginner|intermediate|advanced',
            'time_calculation': '5',
            'additional_instructions': ''
        }
        
        # Version tracking
        self.template_versions['content_analysis'] = {
            'version': '1.0.0',
            'created': datetime.utcnow().isoformat(),
            'changes': ['Initial version with comprehensive analysis']
        }
    
    def _create_summarization_templates(self):
        """Create templates for different types of summaries"""
        # Brief summary template
        self.templates['summary_brief'] = PromptTemplate(
            input_variables=['content', 'max_sentences'],
            template="Summarize this in {max_sentences} sentences:\n\n{content}"
        )
        
        # Detailed summary template
        self.templates['summary_detailed'] = PromptTemplate(
            input_variables=['content', 'focus_areas'],
            template="""Provide a comprehensive summary with main themes:

Content: {content}

Focus on these areas: {focus_areas}

Include:
1. Main thesis or central idea
2. Supporting arguments or key points
3. Important details and examples
4. Conclusion or outcomes"""
        )
        
        # Key points extraction template
        self.templates['summary_key_points'] = PromptTemplate(
            input_variables=['content', 'num_points'],
            template="""Extract {num_points} key points as a bulleted list:

Content: {content}

Format each point as:
• Clear, actionable insight
• Self-contained and meaningful
• Specific rather than general"""
        )
        
        # Technical summary template
        self.templates['summary_technical'] = PromptTemplate(
            input_variables=['content', 'technical_level'],
            template="""Summarize the technical aspects and implications:

Content: {content}
Technical Level: {technical_level}

Focus on:
- Technical concepts and methodologies
- Implementation details
- Performance implications
- Best practices mentioned
- Potential challenges or limitations"""
        )
        
        # ELI5 (Explain Like I'm 5) template
        self.templates['summary_eli5'] = PromptTemplate(
            input_variables=['content', 'target_audience'],
            template="""Explain this in simple terms a {target_audience} would understand:

Content: {content}

Rules:
- Use simple, everyday language
- Avoid jargon and technical terms
- Use analogies and examples
- Keep sentences short and clear"""
        )
        
        # Set defaults
        self.templates['summarization_defaults'] = {
            'max_sentences': '2-3',
            'focus_areas': 'main ideas, key insights, and practical applications',
            'num_points': '5-7',
            'technical_level': 'intermediate',
            'target_audience': 'beginner'
        }
    
    def _create_tag_generation_templates(self):
        """Create templates for tag generation"""
        # Main tag generation template
        self.templates['generate_tags'] = ChatPromptTemplate.from_template(
            """You are an expert at generating relevant, searchable tags for content.

Content: {content}
Content Type: {content_type}
Existing tags in system: {existing_tags}

Generate {num_tags} relevant tags for this content.

Rules:
1. Tags should be lowercase, single or compound words
2. Be specific rather than generic
3. Include technical terms if relevant
4. Consider the content type and domain
5. Prefer existing tags when appropriate

Respond in JSON format:
{{
    "tags": ["tag1", "tag2", "tag3", ...],
    "confidence_scores": {{"tag1": 0.9, "tag2": 0.8, ...}},
    "reasoning": "Brief explanation of tag choices"
}}"""
        )
        
        # Few-shot examples for tag generation
        tag_examples = [
            {
                "content": "Building RESTful APIs with FastAPI and PostgreSQL",
                "output": '{"tags": ["fastapi", "rest-api", "postgresql", "python", "web-development", "backend"], "confidence_scores": {"fastapi": 0.95, "rest-api": 0.9, "postgresql": 0.9, "python": 0.85, "web-development": 0.8, "backend": 0.8}}'
            },
            {
                "content": "Machine Learning model deployment using Docker and Kubernetes",
                "output": '{"tags": ["machine-learning", "docker", "kubernetes", "deployment", "devops", "containerization"], "confidence_scores": {"machine-learning": 0.9, "docker": 0.95, "kubernetes": 0.95, "deployment": 0.85, "devops": 0.8, "containerization": 0.85}}'
            }
        ]
        
        # Create few-shot template
        example_prompt = PromptTemplate(
            input_variables=["content", "output"],
            template="Content: {content}\nOutput: {output}"
        )
        
        self.templates['generate_tags_fewshot'] = FewShotPromptTemplate(
            examples=tag_examples,
            example_prompt=example_prompt,
            prefix="Generate tags based on these examples:",
            suffix="Content: {content}\nOutput:",
            input_variables=["content"]
        )
    
    def _create_relationship_templates(self):
        """Create templates for discovering relationships"""
        self.templates['discover_relationships'] = ChatPromptTemplate.from_template(
            """You are an expert at identifying relationships between content.

Content 1: {content1}
Metadata 1: {metadata1}

Content 2: {content2}
Metadata 2: {metadata2}

Analyze the relationship between these two pieces of content.

Provide analysis in JSON format:
{{
    "relationship_type": "{relationship_types}",
    "confidence": 0.0-1.0,
    "direction": "1->2|2->1|bidirectional",
    "explanation": "Clear explanation of the relationship",
    "shared_concepts": ["list of shared concepts"],
    "learning_path_order": "1->2|2->1|parallel|independent",
    "complementary_aspects": ["how they complement each other"],
    "potential_conflicts": ["any contradictions or conflicts"],
    "integration_suggestions": ["how to use them together"]
}}

Consider these relationship types: {relationship_types}"""
        )
        
        self.templates['relationship_defaults'] = {
            'relationship_types': 'prerequisite|extends|related|contradicts|implements|references|part_of|alternative'
        }
    
    def _create_insights_templates(self):
        """Create templates for generating insights"""
        self.templates['generate_insights'] = ChatPromptTemplate.from_template(
            """You are a knowledge management insights analyst.

Analyze these items from the past {timeframe} and generate insights:

Items Summary:
{items_summary}

Total Items: {total_items}
Date Range: {date_range}

Generate comprehensive insights in JSON format:
{{
    "trending_topics": [
        {{"topic": "name", "count": 0, "growth": "+X%", "context": "why it's trending"}}
    ],
    "content_patterns": {{
        "most_captured_type": "article|video|etc",
        "peak_capture_times": ["time patterns"],
        "content_diversity_score": 0.0-1.0,
        "explanation": "pattern analysis"
    }},
    "learning_velocity": {{
        "items_per_day": 0.0,
        "knowledge_depth": "expanding|deepening|stagnant",
        "recommended_focus": "suggestion for learning"
    }},
    "knowledge_gaps": [
        {{"area": "topic", "suggestion": "what to explore", "reason": "why it matters"}}
    ],
    "connections_discovered": 0,
    "recommended_reviews": ["Items that should be reviewed based on patterns"],
    "emerging_themes": [
        {{"theme": "name", "evidence": ["supporting items"], "potential": "future direction"}}
    ],
    "actionable_recommendations": [
        {{"action": "specific action", "priority": "high|medium|low", "expected_outcome": "benefit"}}
    ]
}}

Focus on: {analysis_focus}"""
        )
    
    def _create_categorization_templates(self):
        """Create templates for content categorization"""
        self.templates['categorize_content'] = ChatPromptTemplate.from_template(
            """You are an expert content categorizer.

Content: {content}
Content Type: {content_type}

Existing categories: {existing_categories}

Categorize this content following these rules:
1. Prefer existing categories when appropriate
2. Suggest new categories only when necessary
3. Provide confidence scores for each category
4. Can assign multiple categories if relevant
5. Consider the content domain and technical level

Respond in JSON format:
{{
    "primary_category": {{"name": "category", "confidence": 0.0-1.0}},
    "secondary_categories": [
        {{"name": "category", "confidence": 0.0-1.0}}
    ],
    "suggested_new_category": {{"name": "new_category", "reason": "why needed", "confidence": 0.0-1.0}},
    "reasoning": "explanation of categorization",
    "domain_classification": "technical|business|general|academic",
    "audience_level": "beginner|intermediate|advanced|expert"
}}

Confidence threshold: {confidence_threshold}"""
        )
    
    def _create_learning_path_templates(self):
        """Create templates for learning path generation"""
        self.templates['generate_learning_path'] = ChatPromptTemplate.from_template(
            """You are an expert learning path designer.

Topic: {topic}
Current skill level: {skill_level}
Learning style: {learning_style}
Time commitment: {time_commitment}

Existing knowledge:
{knowledge_summary}

Design a personalized learning path in JSON format:
{{
    "learning_objectives": ["clear, measurable objectives"],
    "prerequisites": ["required knowledge before starting"],
    "learning_path": [
        {{
            "phase": "Foundation|Core|Advanced|Mastery",
            "topics": ["specific topics to learn"],
            "estimated_time": "X hours/days",
            "resources_needed": ["types of resources"],
            "practice_projects": ["hands-on projects"],
            "milestones": ["checkpoints to validate learning"],
            "assessment_criteria": ["how to measure understanding"]
        }}
    ],
    "knowledge_gaps": ["what's missing from current knowledge"],
    "recommended_pace": "intensive|regular|relaxed",
    "success_metrics": ["how to measure overall progress"],
    "potential_challenges": ["common difficulties and solutions"],
    "next_steps": ["what to explore after completion"],
    "alternative_paths": ["other ways to learn this topic"]
}}

Additional considerations: {additional_requirements}"""
        )
    
    # Public API methods
    def get_prompt(
        self,
        template_name: str,
        variables: Optional[Dict[str, Any]] = None,
        use_defaults: bool = True
    ) -> str:
        """
        Get a formatted prompt from a template
        
        Args:
            template_name: Name of the template
            variables: Variables to substitute
            use_defaults: Whether to use default values
            
        Returns:
            Formatted prompt string
        """
        if not self.enabled or template_name not in self.templates:
            logger.warning(f"Template {template_name} not available, using fallback")
            return self._get_fallback_prompt(template_name, variables)
        
        try:
            template = self.templates[template_name]
            
            # Merge defaults with provided variables
            if use_defaults and f"{template_name}_defaults" in self.templates:
                defaults = self.templates[f"{template_name}_defaults"].copy()
                if variables:
                    defaults.update(variables)
                variables = defaults
            
            # Format the template
            if hasattr(template, 'format'):
                return template.format(**variables)
            elif hasattr(template, 'format_messages'):
                # For ChatPromptTemplate
                messages = template.format_messages(**variables)
                # Convert to string representation
                return "\n".join([f"{msg.type}: {msg.content}" for msg in messages])
            else:
                return str(template)
                
        except Exception as e:
            logger.error(f"Error formatting template {template_name}: {e}")
            return self._get_fallback_prompt(template_name, variables)
    
    def get_chat_prompt(
        self,
        template_name: str,
        variables: Optional[Dict[str, Any]] = None,
        use_defaults: bool = True
    ) -> List[Dict[str, str]]:
        """
        Get a chat prompt as message list
        
        Args:
            template_name: Name of the template
            variables: Variables to substitute
            use_defaults: Whether to use default values
            
        Returns:
            List of message dictionaries
        """
        if not self.enabled or template_name not in self.templates:
            return [{"role": "user", "content": self._get_fallback_prompt(template_name, variables)}]
        
        try:
            template = self.templates[template_name]
            
            # Merge defaults with provided variables
            if use_defaults and f"{template_name}_defaults" in self.templates:
                defaults = self.templates[f"{template_name}_defaults"].copy()
                if variables:
                    defaults.update(variables)
                variables = defaults
            
            # Format as messages
            if hasattr(template, 'format_messages'):
                messages = template.format_messages(**variables)
                return [
                    {"role": "system" if msg.type == "system" else "user", "content": msg.content}
                    for msg in messages
                ]
            else:
                # Fallback for non-chat templates
                return [{"role": "user", "content": self.get_prompt(template_name, variables, use_defaults)}]
                
        except Exception as e:
            logger.error(f"Error formatting chat template {template_name}: {e}")
            return [{"role": "user", "content": self._get_fallback_prompt(template_name, variables)}]
    
    def _get_fallback_prompt(self, template_name: str, variables: Optional[Dict[str, Any]] = None) -> str:
        """Get fallback prompt when templates aren't available"""
        fallbacks = {
            'content_analysis': "Analyze this content and provide title, summary, category, and tags.",
            'summary_brief': "Summarize this content briefly.",
            'generate_tags': "Generate relevant tags for this content.",
            'discover_relationships': "Analyze the relationship between these two pieces of content.",
            'generate_insights': "Generate insights from these items.",
            'categorize_content': "Categorize this content.",
            'generate_learning_path': "Create a learning path for this topic."
        }
        
        base_prompt = fallbacks.get(template_name, "Process this content.")
        
        if variables:
            # Add some key variables to fallback
            if 'content' in variables:
                base_prompt += f"\n\nContent: {variables['content'][:500]}..."
            if 'url' in variables:
                base_prompt += f"\n\nURL: {variables['url']}"
        
        return base_prompt
    
    def add_custom_template(
        self,
        name: str,
        template: Any,
        defaults: Optional[Dict[str, Any]] = None,
        version: str = "1.0.0"
    ):
        """Add a custom template"""
        self.templates[name] = template
        if defaults:
            self.templates[f"{name}_defaults"] = defaults
        self.template_versions[name] = {
            'version': version,
            'created': datetime.utcnow().isoformat(),
            'changes': ['Custom template added']
        }
    
    def get_template_info(self, template_name: str) -> Dict[str, Any]:
        """Get information about a template"""
        if template_name not in self.templates:
            return {"exists": False}
        
        return {
            "exists": True,
            "version": self.template_versions.get(template_name, {}).get('version', 'unknown'),
            "has_defaults": f"{template_name}_defaults" in self.templates,
            "type": type(self.templates[template_name]).__name__
        }
    
    def list_templates(self) -> List[str]:
        """List all available templates"""
        return [
            name for name in self.templates.keys()
            if not name.endswith('_defaults')
        ]


# Singleton instance
prompt_template_manager = PromptTemplateManager()