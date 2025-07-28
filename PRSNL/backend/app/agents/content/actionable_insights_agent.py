"""
Actionable Insights Extraction Agent - Extract practical, actionable knowledge from content

This agent specializes in identifying and extracting actionable insights such as:
- Step-by-step instructions
- Practical tips and tricks
- Methods and techniques
- Key takeaways and learnings
- How-to information

Optimized for chatbot/voice bot consumption with structured, easy-to-understand output.
"""

import logging
import json
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from crewai import Agent, Task, Crew

from app.agents.base_agent import PRSNLBaseAgent
from app.services.unified_ai_service import UnifiedAIService
from app.agents import register_agent

logger = logging.getLogger(__name__)


@dataclass
class ActionableInsight:
    """Represents a single actionable insight"""
    type: str  # 'tip', 'step', 'method', 'takeaway'
    content: str
    context: Optional[str] = None
    importance: str = "medium"  # 'high', 'medium', 'low'
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "content": self.content,
            "context": self.context,
            "importance": self.importance
        }


@dataclass
class InsightsCollection:
    """Collection of categorized insights"""
    tips: List[ActionableInsight] = field(default_factory=list)
    steps: List[ActionableInsight] = field(default_factory=list)
    methods: List[ActionableInsight] = field(default_factory=list)
    takeaways: List[ActionableInsight] = field(default_factory=list)
    summary: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "tips": [tip.to_dict() for tip in self.tips],
            "steps": [step.to_dict() for step in self.steps],
            "methods": [method.to_dict() for method in self.methods],
            "takeaways": [takeaway.to_dict() for takeaway in self.takeaways],
            "summary": self.summary,
            "total_insights": len(self.tips) + len(self.steps) + len(self.methods) + len(self.takeaways)
        }


@register_agent("actionable_insights")
class ActionableInsightsAgent(PRSNLBaseAgent):
    """Agent specialized in extracting actionable insights from content"""
    
    def __init__(
        self,
        role: str = "Actionable Insights Specialist",
        goal: str = "Extract practical, actionable knowledge from content for easy consumption by chatbots and voice assistants",
        backstory: Optional[str] = None,
        **kwargs
    ):
        if backstory is None:
            backstory = (
                "You are an expert knowledge curator with a talent for identifying practical, "
                "actionable information within any content. Your expertise lies in extracting "
                "step-by-step instructions, useful tips, effective methods, and key takeaways "
                "that users can immediately apply. You understand how chatbots and voice assistants "
                "work, so you structure information in clear, conversational chunks that are easy "
                "to understand and act upon. You focus on the 'how' rather than just the 'what', "
                "making knowledge immediately useful and implementable."
            )
        
        super().__init__(
            role=role,
            goal=goal,
            backstory=backstory,
            **kwargs
        )
        
        self.ai_service = UnifiedAIService()
    
    async def extract_insights(
        self,
        content: str,
        content_type: Optional[str] = None,
        url: Optional[str] = None,
        title: Optional[str] = None,
        focus_areas: Optional[List[str]] = None
    ) -> InsightsCollection:
        """
        Extract actionable insights from content
        
        Args:
            content: The content to analyze
            content_type: Type of content (article, tutorial, documentation, etc.)
            url: Source URL if available
            title: Content title
            focus_areas: Specific areas to focus on (e.g., ['setup', 'configuration'])
            
        Returns:
            InsightsCollection with categorized actionable insights
        """
        try:
            # Prepare context for analysis
            context_info = []
            if title:
                context_info.append(f"Title: {title}")
            if content_type:
                context_info.append(f"Content Type: {content_type}")
            if url:
                context_info.append(f"Source: {url}")
            if focus_areas:
                context_info.append(f"Focus Areas: {', '.join(focus_areas)}")
            
            context_text = "\n".join(context_info) if context_info else ""
            
            # Limit content length for processing
            content_to_analyze = content[:8000] if len(content) > 8000 else content
            
            prompt = f"""Analyze this content and extract ALL actionable insights that users can apply:

{context_text}

Content:
{content_to_analyze}

Extract and categorize insights into these types:

1. TIPS: Practical advice, best practices, shortcuts, or recommendations
   - Quick wins and time-savers
   - Warnings about common mistakes
   - Pro tips and expert advice

2. STEPS: Sequential instructions or procedures
   - How-to guides
   - Setup instructions
   - Process workflows
   - Implementation steps

3. METHODS: Techniques, approaches, or strategies
   - Problem-solving techniques
   - Methodologies and frameworks
   - Alternative approaches
   - Decision-making criteria

4. TAKEAWAYS: Key learnings and important points
   - Core concepts to remember
   - Important facts or findings
   - Lessons learned
   - Summary points

For each insight:
- Make it self-contained and actionable
- Keep it concise (1-2 sentences)
- Use clear, simple language
- Include specific details when helpful
- Prioritize practical application

Return as JSON with this structure:
{{
    "tips": [
        {{"content": "Tip text", "context": "When/where to apply", "importance": "high|medium|low"}},
        ...
    ],
    "steps": [
        {{"content": "Step description", "context": "Part of process", "importance": "high|medium|low"}},
        ...
    ],
    "methods": [
        {{"content": "Method description", "context": "Use case", "importance": "high|medium|low"}},
        ...
    ],
    "takeaways": [
        {{"content": "Key point", "context": "Why it matters", "importance": "high|medium|low"}},
        ...
    ],
    "summary": "One paragraph summary focusing on the most actionable insights"
}}"""

            response = await self.ai_service.complete(
                prompt=prompt,
                system_prompt=(
                    "You are an expert at extracting actionable insights from content. "
                    "Focus on practical, implementable knowledge that users can immediately apply. "
                    "Structure insights for easy consumption by chatbots and voice assistants."
                ),
                temperature=0.2,  # Low temperature for consistent extraction
                response_format={"type": "json_object"}
            )
            
            try:
                insights_data = json.loads(response)
                
                # Create InsightsCollection
                collection = InsightsCollection()
                
                # Process tips
                for tip_data in insights_data.get('tips', []):
                    collection.tips.append(ActionableInsight(
                        type='tip',
                        content=tip_data.get('content', ''),
                        context=tip_data.get('context'),
                        importance=tip_data.get('importance', 'medium')
                    ))
                
                # Process steps
                for step_data in insights_data.get('steps', []):
                    collection.steps.append(ActionableInsight(
                        type='step',
                        content=step_data.get('content', ''),
                        context=step_data.get('context'),
                        importance=step_data.get('importance', 'medium')
                    ))
                
                # Process methods
                for method_data in insights_data.get('methods', []):
                    collection.methods.append(ActionableInsight(
                        type='method',
                        content=method_data.get('content', ''),
                        context=method_data.get('context'),
                        importance=method_data.get('importance', 'medium')
                    ))
                
                # Process takeaways
                for takeaway_data in insights_data.get('takeaways', []):
                    collection.takeaways.append(ActionableInsight(
                        type='takeaway',
                        content=takeaway_data.get('content', ''),
                        context=takeaway_data.get('context'),
                        importance=takeaway_data.get('importance', 'medium')
                    ))
                
                # Set summary
                collection.summary = insights_data.get('summary', '')
                
                # Post-process to ensure quality
                collection = self._post_process_insights(collection)
                
                logger.info(f"Extracted {collection.to_dict()['total_insights']} actionable insights")
                return collection
                
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"Failed to parse AI response for insights: {e}")
                # Return minimal insights based on simple extraction
                return self._extract_basic_insights(content, title)
                
        except Exception as e:
            logger.error(f"Error extracting actionable insights: {e}")
            return self._extract_basic_insights(content, title)
    
    def _post_process_insights(self, collection: InsightsCollection) -> InsightsCollection:
        """Post-process insights to ensure quality and remove duplicates"""
        
        # Remove empty insights
        collection.tips = [t for t in collection.tips if t.content.strip()]
        collection.steps = [s for s in collection.steps if s.content.strip()]
        collection.methods = [m for m in collection.methods if m.content.strip()]
        collection.takeaways = [t for t in collection.takeaways if t.content.strip()]
        
        # Remove duplicates within each category
        collection.tips = self._deduplicate_insights(collection.tips)
        collection.steps = self._deduplicate_insights(collection.steps)
        collection.methods = self._deduplicate_insights(collection.methods)
        collection.takeaways = self._deduplicate_insights(collection.takeaways)
        
        # Ensure steps are properly ordered if they contain numbers
        collection.steps = self._order_steps(collection.steps)
        
        return collection
    
    def _deduplicate_insights(self, insights: List[ActionableInsight]) -> List[ActionableInsight]:
        """Remove duplicate insights based on content similarity"""
        unique_insights = []
        seen_content = set()
        
        for insight in insights:
            # Normalize content for comparison
            normalized = re.sub(r'\s+', ' ', insight.content.lower().strip())
            
            if normalized not in seen_content:
                seen_content.add(normalized)
                unique_insights.append(insight)
        
        return unique_insights
    
    def _order_steps(self, steps: List[ActionableInsight]) -> List[ActionableInsight]:
        """Order steps if they contain numeric indicators"""
        
        def extract_step_number(step: ActionableInsight) -> tuple:
            # Look for patterns like "Step 1:", "1.", "1)", etc.
            match = re.match(r'(?:step\s+)?(\d+)[\.:)\s]', step.content.lower())
            if match:
                return (int(match.group(1)), step.content)
            return (999, step.content)  # Put unnumbered steps at the end
        
        # Sort by extracted number
        sorted_steps = sorted(steps, key=extract_step_number)
        return sorted_steps
    
    def _extract_basic_insights(self, content: str, title: Optional[str] = None) -> InsightsCollection:
        """Fallback method to extract basic insights using patterns"""
        collection = InsightsCollection()
        
        # Simple pattern-based extraction
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Look for tips (keywords: tip, hint, note, remember)
            if re.search(r'\b(tip|hint|note|remember|pro tip)s?\b', line, re.I):
                collection.tips.append(ActionableInsight(
                    type='tip',
                    content=line,
                    importance='medium'
                ))
            
            # Look for steps (numbered lists, step keywords)
            elif re.match(r'^(\d+[\.:)]|\bstep\s+\d+)', line, re.I):
                collection.steps.append(ActionableInsight(
                    type='step',
                    content=line,
                    importance='medium'
                ))
            
            # Look for methods (how to, approach, technique)
            elif re.search(r'\b(how to|approach|technique|method|strategy)\b', line, re.I):
                collection.methods.append(ActionableInsight(
                    type='method',
                    content=line,
                    importance='medium'
                ))
        
        # Create a basic summary
        if title:
            collection.summary = f"Key insights from '{title}'"
        else:
            collection.summary = "Content processed for actionable insights"
        
        return collection
    
    async def generate_voice_friendly_summary(
        self,
        insights: InsightsCollection,
        max_length: int = 300
    ) -> str:
        """
        Generate a voice-friendly summary from insights
        
        Args:
            insights: The insights collection
            max_length: Maximum character length for voice output
            
        Returns:
            Voice-optimized summary string
        """
        # Prioritize high-importance insights
        high_priority = []
        
        for tip in insights.tips:
            if tip.importance == 'high':
                high_priority.append(f"Tip: {tip.content}")
        
        for step in insights.steps[:3]:  # Limit steps for voice
            high_priority.append(f"Step: {step.content}")
        
        for method in insights.methods:
            if method.importance == 'high':
                high_priority.append(f"Method: {method.content}")
        
        for takeaway in insights.takeaways[:2]:  # Key takeaways
            high_priority.append(f"Key point: {takeaway.content}")
        
        # Construct voice-friendly summary
        if high_priority:
            summary_parts = ["Here are the key insights:"]
            
            current_length = len(summary_parts[0])
            for item in high_priority:
                if current_length + len(item) + 2 < max_length:
                    summary_parts.append(item)
                    current_length += len(item) + 2
                else:
                    break
            
            return " ".join(summary_parts)
        else:
            return insights.summary[:max_length] if insights.summary else "No specific actionable insights found."
    
    def get_agent(self) -> Agent:
        """Get the configured CrewAI agent instance"""
        return Agent(
            role=self.role,
            goal=self.goal,
            backstory=self.backstory,
            tools=self.tools,
            llm=self._get_llm_config(),
            verbose=self.verbose,
            max_iter=self.max_iter,
            memory=self.memory
        )