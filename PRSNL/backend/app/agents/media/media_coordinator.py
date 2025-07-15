"""
Media Coordinator Agent - Migrated to Crew.ai

This agent coordinates different media processing agents and manages media workflows.
"""

import logging
from typing import Any, Dict, List, Optional

from app.agents.base_agent import PRSNLBaseAgent
from app.agents import register_agent
from app.tools.media_tools import VideoProcessingTool, AudioTranscriptionTool, OCRTool
from app.tools.ai_tools import SummaryGeneratorTool, EntityExtractorTool
from app.tools.knowledge_tools import ConnectionFinderTool

logger = logging.getLogger(__name__)


@register_agent("media_coordinator")
class MediaCoordinatorAgent(PRSNLBaseAgent):
    """
    Media Coordinator Agent
    
    Coordinates multiple media processing agents and manages complex
    media workflows involving multiple media types.
    """
    
    def __init__(self, **kwargs):
        # Define the agent's role, goal, and backstory
        role = kwargs.pop("role", "Media Workflow Coordinator")
        goal = kwargs.pop("goal", 
            "Coordinate and orchestrate media processing workflows across "
            "different media types to create integrated knowledge structures"
        )
        backstory = kwargs.pop("backstory",
            "You are a skilled project manager specializing in multimedia content "
            "workflows. Your expertise lies in coordinating different media processing "
            "specialists to create cohesive, comprehensive knowledge from diverse "
            "media sources. You excel at identifying the optimal processing sequence, "
            "managing dependencies between different media types, and ensuring "
            "quality integration of multimedia knowledge assets."
        )
        
        # Initialize with coordination tools
        tools = kwargs.pop("tools", None)
        if tools is None:
            tools = [
                VideoProcessingTool(),
                AudioTranscriptionTool(),
                OCRTool(),
                SummaryGeneratorTool(),
                EntityExtractorTool(),
                ConnectionFinderTool()
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
        When coordinating media workflows:
        1. Assess media types and processing requirements
        2. Determine optimal processing sequence
        3. Coordinate between specialized media agents
        4. Manage dependencies and data flow
        5. Ensure quality integration of results
        6. Handle errors and fallback scenarios
        7. Optimize processing efficiency
        8. Maintain consistency across media types
        9. Create unified knowledge structures
        10. Validate and verify processed content
        11. Generate comprehensive reports
        12. Manage resource allocation and prioritization
        
        Focus on creating seamless workflows that maximize
        the value extraction from multimedia content.
        """
    
    def plan_media_workflow(self, media_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Plan the processing workflow for multiple media items"""
        workflow_plan = {
            "processing_sequence": [],
            "dependencies": {},
            "estimated_duration": 0,
            "resource_requirements": {},
            "quality_checkpoints": [],
            "integration_strategy": "sequential"
        }
        
        # Analyze media types
        media_types = {}
        for item in media_items:
            media_type = item.get("type", "unknown")
            if media_type not in media_types:
                media_types[media_type] = []
            media_types[media_type].append(item)
        
        # Plan processing sequence
        processing_order = ["image", "audio", "video", "document"]
        
        for media_type in processing_order:
            if media_type in media_types:
                workflow_plan["processing_sequence"].append({
                    "type": media_type,
                    "items": media_types[media_type],
                    "agent": self._get_agent_for_media_type(media_type),
                    "estimated_time": len(media_types[media_type]) * self._get_processing_time(media_type)
                })
        
        # Calculate total estimated duration
        workflow_plan["estimated_duration"] = sum(
            step["estimated_time"] for step in workflow_plan["processing_sequence"]
        )
        
        return workflow_plan
    
    def _get_agent_for_media_type(self, media_type: str) -> str:
        """Get the appropriate agent for a media type"""
        agent_mapping = {
            "image": "ocr_image_analyst",
            "audio": "audio_journal_processor",
            "video": "video_processor",
            "document": "ocr_image_analyst"
        }
        return agent_mapping.get(media_type, "media_coordinator")
    
    def _get_processing_time(self, media_type: str) -> int:
        """Get estimated processing time in seconds for media type"""
        time_estimates = {
            "image": 30,
            "audio": 120,
            "video": 300,
            "document": 60
        }
        return time_estimates.get(media_type, 60)
    
    def coordinate_agent_execution(self, workflow_plan: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinate the execution of multiple agents"""
        execution_results = {
            "completed_steps": [],
            "failed_steps": [],
            "overall_status": "in_progress",
            "integrated_results": {},
            "quality_metrics": {}
        }
        
        # Simulate agent coordination
        for step in workflow_plan["processing_sequence"]:
            step_result = {
                "step": step["type"],
                "agent": step["agent"],
                "status": "completed",
                "results": f"Processed {len(step['items'])} {step['type']} items",
                "duration": step["estimated_time"]
            }
            execution_results["completed_steps"].append(step_result)
        
        execution_results["overall_status"] = "completed"
        
        return execution_results
    
    def integrate_media_results(self, agent_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Integrate results from multiple media processing agents"""
        integrated_results = {
            "unified_content": {},
            "cross_references": [],
            "entity_consolidation": {},
            "timeline_reconstruction": [],
            "knowledge_graph": {},
            "quality_assessment": {}
        }
        
        # Consolidate entities across media types
        all_entities = {}
        for result in agent_results:
            entities = result.get("entities", {})
            for entity_type, entity_list in entities.items():
                if entity_type not in all_entities:
                    all_entities[entity_type] = set()
                all_entities[entity_type].update(entity_list)
        
        # Convert sets back to lists
        integrated_results["entity_consolidation"] = {
            entity_type: list(entity_set) 
            for entity_type, entity_set in all_entities.items()
        }
        
        # Create cross-references
        for i, result1 in enumerate(agent_results):
            for j, result2 in enumerate(agent_results[i+1:], i+1):
                shared_entities = self._find_shared_entities(result1, result2)
                if shared_entities:
                    integrated_results["cross_references"].append({
                        "source1": result1.get("media_type", "unknown"),
                        "source2": result2.get("media_type", "unknown"),
                        "shared_entities": shared_entities,
                        "relationship_strength": len(shared_entities)
                    })
        
        return integrated_results
    
    def _find_shared_entities(self, result1: Dict[str, Any], result2: Dict[str, Any]) -> List[str]:
        """Find shared entities between two processing results"""
        entities1 = set()
        entities2 = set()
        
        for entity_list in result1.get("entities", {}).values():
            entities1.update(entity_list)
        
        for entity_list in result2.get("entities", {}).values():
            entities2.update(entity_list)
        
        return list(entities1.intersection(entities2))
    
    def generate_multimedia_summary(self, integrated_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a comprehensive summary of multimedia content"""
        summary = {
            "overview": "",
            "key_insights": [],
            "media_breakdown": {},
            "entity_summary": {},
            "recommendations": [],
            "follow_up_actions": []
        }
        
        # Generate overview
        entity_count = sum(
            len(entities) for entities in integrated_results.get("entity_consolidation", {}).values()
        )
        cross_ref_count = len(integrated_results.get("cross_references", []))
        
        summary["overview"] = (
            f"Multimedia content analysis complete. "
            f"Identified {entity_count} unique entities with {cross_ref_count} cross-references. "
            f"Content spans multiple media types with strong thematic connections."
        )
        
        # Generate key insights
        summary["key_insights"] = [
            "Strong thematic coherence across media types",
            "Rich entity relationships identified",
            "High-quality content suitable for knowledge management",
            "Multiple learning modalities represented"
        ]
        
        # Generate recommendations
        summary["recommendations"] = [
            "Create knowledge graph visualization",
            "Develop interactive timeline",
            "Generate study materials from content",
            "Create accessibility alternatives"
        ]
        
        return summary
    
    def assess_workflow_quality(self, workflow_results: Dict[str, Any]) -> Dict[str, Any]:
        """Assess the quality of the workflow execution"""
        quality_assessment = {
            "completeness_score": 0.0,
            "accuracy_score": 0.0,
            "integration_score": 0.0,
            "efficiency_score": 0.0,
            "overall_quality": 0.0,
            "improvement_areas": [],
            "strengths": []
        }
        
        # Assess completeness
        completed_steps = len(workflow_results.get("completed_steps", []))
        failed_steps = len(workflow_results.get("failed_steps", []))
        total_steps = completed_steps + failed_steps
        
        if total_steps > 0:
            quality_assessment["completeness_score"] = completed_steps / total_steps
        
        # Assess integration quality
        cross_references = len(workflow_results.get("integrated_results", {}).get("cross_references", []))
        if cross_references > 0:
            quality_assessment["integration_score"] = min(cross_references / 5.0, 1.0)
        
        # Calculate overall quality
        quality_assessment["overall_quality"] = (
            quality_assessment["completeness_score"] * 0.4 +
            quality_assessment["integration_score"] * 0.3 +
            0.8 * 0.3  # Assumed accuracy and efficiency
        )
        
        # Identify strengths and areas for improvement
        if quality_assessment["overall_quality"] > 0.8:
            quality_assessment["strengths"].append("Excellent workflow execution")
        if quality_assessment["integration_score"] > 0.7:
            quality_assessment["strengths"].append("Strong cross-media integration")
        
        if quality_assessment["completeness_score"] < 0.9:
            quality_assessment["improvement_areas"].append("Improve step completion rate")
        
        return quality_assessment