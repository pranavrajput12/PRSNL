"""
AutoAgent Repository Services

Specialized AutoAgent agents for repository analysis and project assistance.
Integrates with existing AutoAgent infrastructure for repository intelligence.
"""

import json
import logging
from typing import Any, Dict, List, Optional

from app.services.repository_analyzer import repository_analyzer
from app.services.unified_ai_service import UnifiedAIService

logger = logging.getLogger(__name__)


class RepositoryAnalyzerAgent:
    """AutoAgent for analyzing and categorizing repositories"""
    
    def __init__(self):
        self.ai_service = UnifiedAIService()
        self.agent_name = "Repository Analyzer"
        
    async def analyze_repository_deep(self, repo_url: str, context: Optional[str] = None) -> Dict[str, Any]:
        """
        Perform deep repository analysis with contextual understanding
        
        Args:
            repo_url: Repository URL to analyze
            context: Optional context about why this repository is being analyzed
            
        Returns:
            Comprehensive repository analysis with recommendations
        """
        try:
            # Get basic repository analysis
            repo_metadata = await repository_analyzer.analyze_repository(repo_url)
            
            # Enhance analysis with contextual AI understanding
            enhanced_analysis = await self._enhance_with_context(repo_metadata, context)
            
            return {
                "agent": self.agent_name,
                "repository": {
                    "url": repo_url,
                    "name": repo_metadata.repo_name,
                    "owner": repo_metadata.owner,
                    "description": repo_metadata.description
                },
                "analysis": {
                    "tech_stack": repo_metadata.tech_stack,
                    "category": repo_metadata.category,
                    "use_case": repo_metadata.use_case,
                    "difficulty": repo_metadata.difficulty,
                    "ai_insights": repo_metadata.ai_analysis
                },
                "enhanced_insights": enhanced_analysis,
                "recommendations": await self._generate_recommendations(repo_metadata, context),
                "confidence": repo_metadata.ai_analysis.get("confidence", 0.8)
            }
            
        except Exception as e:
            logger.error(f"Repository analysis failed: {e}")
            return {
                "agent": self.agent_name,
                "error": str(e),
                "recommendation": "Manual analysis required"
            }
    
    async def _enhance_with_context(self, repo_metadata, context: Optional[str]) -> Dict[str, Any]:
        """Enhance repository analysis with contextual understanding"""
        if not context:
            return {}
        
        try:
            prompt = f"""
            Analyze this repository in the context of: {context}
            
            Repository: {repo_metadata.repo_name}
            Description: {repo_metadata.description}
            Tech Stack: {repo_metadata.tech_stack}
            Category: {repo_metadata.category}
            AI Analysis: {json.dumps(repo_metadata.ai_analysis, indent=2)}
            
            Provide contextual insights about:
            1. How well this repository fits the given context
            2. Specific advantages for this use case
            3. Potential limitations or challenges
            4. Integration complexity with existing tech stack
            5. Learning resources needed
            
            Return JSON format with these insights.
            """
            
            response = await self.ai_service.complete(
                prompt=prompt,
                system_prompt="You are a repository analysis expert. Provide detailed contextual analysis in JSON format.",
                max_tokens=800,
                temperature=0.3
            )
            
            return json.loads(response)
        except Exception as e:
            logger.error(f"Context enhancement failed: {e}")
            return {"context_analysis": "Analysis failed"}
    
    async def _generate_recommendations(self, repo_metadata, context: Optional[str]) -> List[str]:
        """Generate specific recommendations for repository usage"""
        recommendations = []
        
        # Basic recommendations based on metadata
        if repo_metadata.difficulty == "beginner":
            recommendations.append("Good starting point for learning")
        elif repo_metadata.difficulty == "advanced":
            recommendations.append("Consider reviewing documentation thoroughly before implementation")
        
        if repo_metadata.stars > 10000:
            recommendations.append("Well-established project with strong community support")
        elif repo_metadata.stars < 100:
            recommendations.append("Newer project - evaluate stability and long-term support")
        
        # Security and maintenance recommendations
        if repo_metadata.ai_analysis.get("maintenance_status") == "active":
            recommendations.append("Actively maintained - good for production use")
        else:
            recommendations.append("Check recent commit activity before using in production")
        
        return recommendations


class ProjectResourceAgent:
    """AutoAgent for finding project-relevant resources across all knowledge sources"""
    
    def __init__(self):
        self.ai_service = UnifiedAIService()
        self.agent_name = "Project Resource Agent"
        
    async def find_project_resources(
        self, 
        project_description: str,
        tech_requirements: List[str] = None,
        difficulty_preference: str = None
    ) -> Dict[str, Any]:
        """
        Find comprehensive resources for a project across all knowledge sources
        
        Args:
            project_description: Description of the project to build
            tech_requirements: Preferred technologies or constraints
            difficulty_preference: Preferred difficulty level
            
        Returns:
            Comprehensive resource list with repositories, docs, and guidance
        """
        try:
            # Search repositories
            repository_matches = await self._search_repositories(
                project_description, tech_requirements, difficulty_preference
            )
            
            # Search related content (this would integrate with existing search)
            related_content = await self._search_related_content(project_description)
            
            # Generate implementation guidance
            implementation_guide = await self._generate_implementation_guide(
                project_description, repository_matches, tech_requirements
            )
            
            return {
                "agent": self.agent_name,
                "project": {
                    "description": project_description,
                    "tech_requirements": tech_requirements or [],
                    "difficulty_preference": difficulty_preference
                },
                "resources": {
                    "repositories": repository_matches,
                    "related_content": related_content,
                    "total_resources": len(repository_matches) + len(related_content)
                },
                "implementation_guide": implementation_guide,
                "next_steps": await self._suggest_next_steps(project_description, repository_matches)
            }
            
        except Exception as e:
            logger.error(f"Project resource search failed: {e}")
            return {
                "agent": self.agent_name,
                "error": str(e),
                "suggestion": "Try breaking down the project into smaller components"
            }
    
    async def _search_repositories(
        self, 
        project_description: str, 
        tech_requirements: List[str] = None,
        difficulty_preference: str = None
    ) -> List[Dict[str, Any]]:
        """Search for relevant repositories in the knowledge base"""
        from app.db.database import get_db_connection
        
        try:
            async for conn in get_db_connection():
                # Build search conditions
                tech_conditions = []
                params = [f"%{project_description}%"]
                param_idx = 2
                
                if tech_requirements:
                    for tech in tech_requirements:
                        tech_conditions.append(f"repository_metadata->'tech_stack' ? ${param_idx}")
                        params.append(tech.lower())
                        param_idx += 1
                
                tech_filter = " OR " + " OR ".join(tech_conditions) if tech_conditions else ""
                
                difficulty_filter = ""
                if difficulty_preference:
                    difficulty_filter = f" OR repository_metadata->>'difficulty' = ${param_idx}"
                    params.append(difficulty_preference)
                
                # Search repositories with relevance scoring
                search_query = f"""
                    SELECT 
                        id, title, url, repository_metadata,
                        CASE 
                            WHEN repository_metadata->>'description' ILIKE $1 THEN 0.9
                            WHEN repository_metadata->>'use_case' ILIKE $1 THEN 0.8
                            WHEN repository_metadata->>'category' ILIKE $1 THEN 0.7
                            ELSE 0.6
                        END as relevance_score
                    FROM items 
                    WHERE repository_metadata IS NOT NULL
                      AND (
                          repository_metadata->>'description' ILIKE $1
                          OR repository_metadata->>'use_case' ILIKE $1
                          OR repository_metadata->>'category' ILIKE $1
                          {tech_filter}
                          {difficulty_filter}
                      )
                    ORDER BY relevance_score DESC, repository_metadata->>'stars' DESC
                    LIMIT 10
                """
                
                rows = await conn.fetch(search_query, *params)
                
                repositories = []
                for row in rows:
                    repo_meta = row['repository_metadata']
                    repositories.append({
                        "type": "repository",
                        "item_id": str(row['id']),
                        "relevance_score": float(row['relevance_score']),
                        "repo_name": repo_meta.get('repo_name', 'Unknown'),
                        "owner": repo_meta.get('owner', 'Unknown'),
                        "description": repo_meta.get('description', ''),
                        "url": row['url'],
                        "tech_stack": repo_meta.get('tech_stack', []),
                        "category": repo_meta.get('category', 'Unknown'),
                        "difficulty": repo_meta.get('difficulty', 'Unknown'),
                        "stars": repo_meta.get('stars', 0),
                        "match_reason": self._determine_match_reason(repo_meta, project_description, tech_requirements)
                    })
                
                return repositories
                
        except Exception as e:
            logger.error(f"Repository search failed: {e}")
            return []
    
    def _determine_match_reason(self, repo_meta: Dict, project_desc: str, tech_reqs: List[str] = None) -> str:
        """Determine why this repository matches the project"""
        reasons = []
        
        if repo_meta.get('description', '').lower() in project_desc.lower():
            reasons.append("Description match")
        
        if tech_reqs:
            tech_stack = repo_meta.get('tech_stack', [])
            matching_tech = [tech for tech in tech_reqs if tech.lower() in [t.lower() for t in tech_stack]]
            if matching_tech:
                reasons.append(f"Tech stack: {', '.join(matching_tech)}")
        
        if repo_meta.get('use_case', '').lower() in project_desc.lower():
            reasons.append("Use case alignment")
        
        return "; ".join(reasons) if reasons else "General relevance"
    
    async def _search_related_content(self, project_description: str) -> List[Dict[str, Any]]:
        """Search for related content (docs, tutorials, etc.) in knowledge base"""
        from app.db.database import get_db_connection
        
        try:
            async for conn in get_db_connection():
                # Search for non-repository content that matches project description
                search_query = """
                    SELECT 
                        id, title, summary, content, url, type,
                        ts_rank(search_vector, plainto_tsquery($1)) as relevance_score
                    FROM items 
                    WHERE repository_metadata IS NULL
                      AND (
                          search_vector @@ plainto_tsquery($1)
                          OR summary ILIKE $2
                          OR content ILIKE $2
                      )
                    ORDER BY relevance_score DESC
                    LIMIT 5
                """
                
                search_pattern = f"%{project_description}%"
                rows = await conn.fetch(search_query, project_description, search_pattern)
                
                content = []
                for row in rows:
                    content.append({
                        "type": row['type'] or "documentation",
                        "item_id": str(row['id']),
                        "title": row['title'],
                        "relevance_score": float(row['relevance_score']) if row['relevance_score'] else 0.5,
                        "description": row['summary'] or row['content'][:200] + "..." if row['content'] else "",
                        "url": row['url']
                    })
                
                return content
                
        except Exception as e:
            logger.error(f"Content search failed: {e}")
            return []
    
    async def _generate_implementation_guide(
        self, 
        project_description: str, 
        repositories: List[Dict[str, Any]],
        tech_requirements: List[str] = None
    ) -> Dict[str, Any]:
        """Generate step-by-step implementation guidance"""
        try:
            prompt = f"""
            Generate an implementation guide for this project:
            
            Project: {project_description}
            Tech Requirements: {tech_requirements or ['Not specified']}
            Available Repositories: {len(repositories)} relevant repositories found
            
            Create a step-by-step implementation plan including:
            1. Project setup and initialization
            2. Key components to build
            3. Integration points for found repositories
            4. Testing strategy
            5. Deployment considerations
            
            Format as JSON with clear steps and timelines.
            """
            
            response = await self.ai_service.complete(
                prompt=prompt,
                system_prompt="You are a project planning expert. Create detailed, actionable implementation guides.",
                max_tokens=1000,
                temperature=0.3
            )
            
            return json.loads(response)
        except Exception as e:
            logger.error(f"Implementation guide generation failed: {e}")
            return {"error": "Could not generate implementation guide"}
    
    async def _suggest_next_steps(
        self, 
        project_description: str, 
        repositories: List[Dict[str, Any]]
    ) -> List[str]:
        """Suggest immediate next steps for the project"""
        next_steps = []
        
        if repositories:
            next_steps.append("Review the suggested repositories and their documentation")
            next_steps.append("Set up a development environment with the chosen tech stack")
        else:
            next_steps.append("Refine project requirements to find more specific resources")
        
        next_steps.extend([
            "Create a project roadmap with milestones",
            "Set up version control and basic project structure",
            "Start with a minimal viable prototype"
        ])
        
        return next_steps


# Global instances for use in AutoAgent integration
repository_analyzer_agent = RepositoryAnalyzerAgent()
project_resource_agent = ProjectResourceAgent()