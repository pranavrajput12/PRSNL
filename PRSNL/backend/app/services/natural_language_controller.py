"""
Natural Language System Control Interface for PRSNL Phase 5
==========================================================

Advanced natural language interface for controlling PRSNL system functions.

Features:
- Voice-driven content navigation
- Natural language search and filtering
- System configuration via conversational commands
- Hands-free knowledge management workflows
- Intelligent command interpretation
- Context-aware action execution
- Multi-modal command processing

Examples:
- "Show me all Python files modified this week"
- "Analyze the security of my latest repository"
- "Create a new bookmark with tags 'machine learning' and 'research'"
- "Find similar content to this image"
- "Start a voice note about my meeting insights"
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union, Tuple
import json
import re
from enum import Enum
from dataclasses import dataclass

# NLP and AI imports
from app.services.unified_ai_service import unified_ai_service
from app.services.ai_router_enhanced import enhanced_ai_router
from app.services.multimodal_ai_orchestrator import multimodal_orchestrator
from app.services.advanced_code_intelligence import advanced_code_intelligence
from app.services.voice_service import VoiceService

# Database and core services
from app.db.database import get_db_connection
from app.config import settings

logger = logging.getLogger(__name__)

class CommandType(Enum):
    """Types of natural language commands"""
    SEARCH = "search"
    ANALYZE = "analyze"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    NAVIGATE = "navigate"
    CONFIGURE = "configure"
    EXPORT = "export"
    MULTIMODAL = "multimodal"
    VOICE_CONTROL = "voice_control"

class EntityType(Enum):
    """Types of entities that can be controlled"""
    CONTENT = "content"
    REPOSITORY = "repository"
    BOOKMARK = "bookmark"
    TAG = "tag"
    ANALYSIS = "analysis"
    SEARCH_QUERY = "search_query"
    USER_SETTING = "user_setting"
    VOICE_NOTE = "voice_note"

@dataclass
class ParsedCommand:
    """Structured representation of a parsed natural language command"""
    command_type: CommandType
    entity_type: EntityType
    action: str
    parameters: Dict[str, Any]
    entities: List[str]
    confidence: float
    original_text: str
    context: Optional[Dict[str, Any]] = None

class NaturalLanguageController:
    """
    Advanced natural language interface for system control.
    
    Interprets natural language commands and executes corresponding system actions.
    """
    
    def __init__(self):
        self.voice_service = VoiceService()
        
        # Command patterns for intent recognition
        self.command_patterns = {
            CommandType.SEARCH: [
                r"(?:find|search|show|get|retrieve|look for|locate)\s+(.+)",
                r"(?:what|where|which|how many)\s+(.+)",
                r"(?:list|display)\s+(?:all|my)?\s*(.+)"
            ],
            CommandType.ANALYZE: [
                r"(?:analyze|check|examine|review|assess|evaluate)\s+(.+)",
                r"(?:what(?:'s| is) the|how is the)\s+(.+?)(?:\s+(?:of|for|in)\s+(.+))?",
                r"(?:run|perform|execute)\s+(?:an?\s+)?analysis\s+(?:on|of)\s+(.+)"
            ],
            CommandType.CREATE: [
                r"(?:create|make|add|new)\s+(?:a\s+)?(.+)",
                r"(?:start|begin|initiate)\s+(?:a\s+)?(.+)",
                r"(?:save|store|bookmark)\s+(.+)"
            ],
            CommandType.UPDATE: [
                r"(?:update|modify|change|edit|alter)\s+(.+)",
                r"(?:set|configure|adjust)\s+(.+)\s+to\s+(.+)",
                r"(?:tag|label|categorize)\s+(.+)\s+(?:as|with)\s+(.+)"
            ],
            CommandType.DELETE: [
                r"(?:delete|remove|clear|eliminate)\s+(.+)",
                r"(?:uninstall|disable)\s+(.+)"
            ],
            CommandType.NAVIGATE: [
                r"(?:go to|navigate to|open|show me)\s+(.+)",
                r"(?:switch to|move to)\s+(.+)"
            ],
            CommandType.CONFIGURE: [
                r"(?:configure|setup|set up|customize)\s+(.+)",
                r"(?:enable|disable|turn on|turn off)\s+(.+)",
                r"(?:preferences|settings|options)\s+(.+)"
            ],
            CommandType.EXPORT: [
                r"(?:export|download|save as|generate)\s+(.+)",
                r"(?:convert|transform)\s+(.+)\s+to\s+(.+)"
            ]
        }
        
        # Entity patterns for parameter extraction
        self.entity_patterns = {
            EntityType.CONTENT: [
                r"(?:content|items?|posts?|articles?|documents?|files?)",
                r"(?:bookmarks?|saved items?)",
                r"(?:notes?|thoughts?|ideas?)"
            ],
            EntityType.REPOSITORY: [
                r"(?:repos?|repositories?|projects?|codebases?)",
                r"(?:github repos?|code projects?)"
            ],
            EntityType.TAG: [
                r"(?:tags?|labels?|categories?)",
                r"(?:tagged with|labeled as|categorized as)"
            ],
            EntityType.ANALYSIS: [
                r"(?:analysis|analyses|reports?|insights?)",
                r"(?:code analysis|security analysis|performance analysis)"
            ]
        }
        
        # Context keywords for parameter extraction
        self.context_keywords = {
            'time_filters': {
                'today': timedelta(days=1),
                'yesterday': timedelta(days=2), 
                'this week': timedelta(days=7),
                'last week': timedelta(days=14),
                'this month': timedelta(days=30),
                'last month': timedelta(days=60),
                'this year': timedelta(days=365)
            },
            'languages': [
                'python', 'javascript', 'typescript', 'java', 'c++', 'c#',
                'go', 'rust', 'php', 'ruby', 'swift', 'kotlin', 'scala'
            ],
            'content_types': [
                'image', 'video', 'audio', 'text', 'document', 'code',
                'bookmark', 'note', 'idea', 'research'
            ],
            'analysis_types': [
                'security', 'performance', 'quality', 'architecture', 'comprehensive'
            ]
        }
    
    async def process_natural_language_command(
        self,
        command_text: str,
        user_context: Optional[Dict[str, Any]] = None,
        multimodal_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a natural language command and execute the corresponding action.
        
        Args:
            command_text: Natural language command from user
            user_context: User preferences and context
            multimodal_context: Additional context from voice/image/other modalities
            
        Returns:
            Result of command execution with structured response
        """
        command_id = str(datetime.utcnow().timestamp())
        start_time = datetime.utcnow()
        
        logger.info(f"🎙️ Processing NL command [ID: {command_id}]: '{command_text[:100]}...'")
        
        try:
            # Parse the natural language command
            parsed_command = await self._parse_command(command_text, user_context, multimodal_context)
            
            if parsed_command.confidence < 0.5:
                return await self._handle_unclear_command(command_text, parsed_command)
            
            # Execute the parsed command
            execution_result = await self._execute_command(parsed_command, user_context)
            
            # Generate natural language response
            nl_response = await self._generate_natural_response(
                parsed_command, execution_result, command_text
            )
            
            # Calculate processing stats
            end_time = datetime.utcnow()
            processing_stats = {
                "command_id": command_id,
                "processing_time_ms": int((end_time - start_time).total_seconds() * 1000),
                "confidence": parsed_command.confidence,
                "command_type": parsed_command.command_type.value,
                "entity_type": parsed_command.entity_type.value
            }
            
            result = {
                "command_id": command_id,
                "original_command": command_text,
                "parsed_command": {
                    "action": parsed_command.action,
                    "command_type": parsed_command.command_type.value,
                    "entity_type": parsed_command.entity_type.value,
                    "parameters": parsed_command.parameters,
                    "entities": parsed_command.entities,
                    "confidence": parsed_command.confidence
                },
                "execution_result": execution_result,
                "natural_response": nl_response,
                "processing_stats": processing_stats,
                "status": "success",
                "timestamp": start_time.isoformat()
            }
            
            logger.info(f"✅ NL command processed [ID: {command_id}] - {processing_stats['processing_time_ms']}ms")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ NL command processing failed [ID: {command_id}]: {e}")
            return {
                "command_id": command_id,
                "original_command": command_text,
                "error": str(e),
                "status": "failed",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _parse_command(
        self,
        command_text: str,
        user_context: Optional[Dict[str, Any]],
        multimodal_context: Optional[Dict[str, Any]]
    ) -> ParsedCommand:
        """Parse natural language command into structured format"""
        try:
            # Clean and normalize command text
            cleaned_text = self._clean_command_text(command_text)
            
            # Use AI for intelligent command parsing
            parse_prompt = f"""
            Parse this natural language command into a structured format:
            
            Command: "{cleaned_text}"
            
            Identify:
            1. Command type: search, analyze, create, update, delete, navigate, configure, export, multimodal, voice_control
            2. Entity type: content, repository, bookmark, tag, analysis, search_query, user_setting, voice_note
            3. Action: specific action to take
            4. Parameters: extracted parameters and filters
            5. Entities: specific entities mentioned
            6. Confidence: how confident you are in this parsing (0.0-1.0)
            
            Context available:
            - User context: {json.dumps(user_context or {}, indent=2)}
            - Multimodal context: {json.dumps(multimodal_context or {}, indent=2)}
            
            Return JSON format:
            {{
                "command_type": "...",
                "entity_type": "...", 
                "action": "...",
                "parameters": {{}},
                "entities": [],
                "confidence": 0.0-1.0
            }}
            """
            
            ai_response = await enhanced_ai_router.route_request({
                "prompt": parse_prompt,
                "task_type": "command_parsing",
                "priority": 8,
                "metadata": {
                    "command_length": len(cleaned_text),
                    "has_user_context": user_context is not None,
                    "has_multimodal_context": multimodal_context is not None
                }
            })
            
            # Parse AI response
            parsed_data = ai_response.get("response", {})
            
            # Fallback to pattern matching if AI parsing fails
            if not parsed_data or parsed_data.get("confidence", 0) < 0.3:
                parsed_data = self._fallback_pattern_parsing(cleaned_text)
            
            # Create ParsedCommand object
            parsed_command = ParsedCommand(
                command_type=CommandType(parsed_data.get("command_type", "search")),
                entity_type=EntityType(parsed_data.get("entity_type", "content")),
                action=parsed_data.get("action", "search"),
                parameters=parsed_data.get("parameters", {}),
                entities=parsed_data.get("entities", []),
                confidence=parsed_data.get("confidence", 0.5),
                original_text=command_text,
                context={"user_context": user_context, "multimodal_context": multimodal_context}
            )
            
            # Enhance parameters with context-aware extraction
            parsed_command.parameters = await self._enhance_parameters(
                parsed_command.parameters, cleaned_text, user_context
            )
            
            return parsed_command
            
        except Exception as e:
            logger.error(f"Command parsing failed: {e}")
            # Return default parsing with low confidence
            return ParsedCommand(
                command_type=CommandType.SEARCH,
                entity_type=EntityType.CONTENT,
                action="search",
                parameters={"query": command_text},
                entities=[],
                confidence=0.2,
                original_text=command_text
            )
    
    async def _execute_command(
        self,
        parsed_command: ParsedCommand,
        user_context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Execute the parsed command and return results"""
        try:
            # Route to appropriate handler based on command type
            if parsed_command.command_type == CommandType.SEARCH:
                return await self._handle_search_command(parsed_command, user_context)
            
            elif parsed_command.command_type == CommandType.ANALYZE:
                return await self._handle_analyze_command(parsed_command, user_context)
            
            elif parsed_command.command_type == CommandType.CREATE:
                return await self._handle_create_command(parsed_command, user_context)
            
            elif parsed_command.command_type == CommandType.UPDATE:
                return await self._handle_update_command(parsed_command, user_context)
            
            elif parsed_command.command_type == CommandType.DELETE:
                return await self._handle_delete_command(parsed_command, user_context)
            
            elif parsed_command.command_type == CommandType.NAVIGATE:
                return await self._handle_navigate_command(parsed_command, user_context)
            
            elif parsed_command.command_type == CommandType.CONFIGURE:
                return await self._handle_configure_command(parsed_command, user_context)
            
            elif parsed_command.command_type == CommandType.EXPORT:
                return await self._handle_export_command(parsed_command, user_context)
            
            elif parsed_command.command_type == CommandType.MULTIMODAL:
                return await self._handle_multimodal_command(parsed_command, user_context)
            
            elif parsed_command.command_type == CommandType.VOICE_CONTROL:
                return await self._handle_voice_control_command(parsed_command, user_context)
            
            else:
                return {
                    "status": "error",
                    "message": f"Unsupported command type: {parsed_command.command_type.value}"
                }
                
        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            return {
                "status": "error",
                "message": f"Execution failed: {str(e)}"
            }
    
    async def _handle_search_command(
        self,
        parsed_command: ParsedCommand,
        user_context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Handle search-related natural language commands"""
        try:
            # Extract search parameters
            query = parsed_command.parameters.get("query", "")
            if not query and parsed_command.entities:
                query = " ".join(parsed_command.entities)
            
            filters = parsed_command.parameters.get("filters", {})
            limit = parsed_command.parameters.get("limit", 20)
            
            # Determine search type based on entity type
            if parsed_command.entity_type == EntityType.REPOSITORY:
                # Search repositories
                async with get_db_connection() as conn:
                    repos = await conn.fetch("""
                        SELECT id, full_name, description, language, updated_at
                        FROM github_repos 
                        WHERE full_name ILIKE $1 OR description ILIKE $1
                        ORDER BY updated_at DESC
                        LIMIT $2
                    """, f"%{query}%", limit)
                    
                    results = [dict(repo) for repo in repos]
                    
                return {
                    "search_type": "repositories",
                    "query": query,
                    "results": results,
                    "total_found": len(results),
                    "status": "success"
                }
            
            elif parsed_command.entity_type == EntityType.CONTENT:
                # Search content/bookmarks  
                async with get_db_connection() as conn:
                    items = await conn.fetch("""
                        SELECT id, title, url, summary, type, created_at
                        FROM items
                        WHERE title ILIKE $1 OR summary ILIKE $1 OR processed_content ILIKE $1
                        ORDER BY created_at DESC
                        LIMIT $2
                    """, f"%{query}%", limit)
                    
                    results = [dict(item) for item in items]
                    
                return {
                    "search_type": "content",
                    "query": query,
                    "results": results,
                    "total_found": len(results),
                    "status": "success"
                }
            
            else:
                # General search
                return {
                    "search_type": "general",
                    "query": query,
                    "message": f"Searching for '{query}' across all content types",
                    "status": "placeholder"
                }
                
        except Exception as e:
            return {"status": "error", "message": f"Search failed: {str(e)}"}
    
    async def _handle_analyze_command(
        self,
        parsed_command: ParsedCommand,
        user_context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Handle analysis-related natural language commands"""
        try:
            # Extract analysis parameters
            target = parsed_command.parameters.get("target", "")
            analysis_type = parsed_command.parameters.get("analysis_type", "comprehensive")
            
            if parsed_command.entity_type == EntityType.REPOSITORY:
                # Find repository to analyze
                if not target and parsed_command.entities:
                    target = parsed_command.entities[0]
                
                # Get repository ID
                async with get_db_connection() as conn:
                    repo = await conn.fetchrow("""
                        SELECT id FROM github_repos 
                        WHERE full_name ILIKE $1 OR name ILIKE $1
                        LIMIT 1
                    """, f"%{target}%")
                    
                    if not repo:
                        return {
                            "status": "error",
                            "message": f"Repository '{target}' not found"
                        }
                    
                    # Start analysis
                    analysis_result = await advanced_code_intelligence.perform_advanced_analysis(
                        repo_id=str(repo['id']),
                        analysis_type=analysis_type
                    )
                    
                    return {
                        "analysis_type": "repository",
                        "target": target,
                        "analysis_id": analysis_result.get("analysis_id"),
                        "quality_scores": analysis_result.get("quality_scores", {}),
                        "recommendations_count": len(analysis_result.get("recommendations", [])),
                        "status": "success"
                    }
            
            else:
                return {
                    "status": "placeholder",
                    "message": f"Analysis of {parsed_command.entity_type.value} not yet implemented"
                }
                
        except Exception as e:
            return {"status": "error", "message": f"Analysis failed: {str(e)}"}
    
    async def _handle_create_command(
        self,
        parsed_command: ParsedCommand,
        user_context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Handle creation-related natural language commands"""
        try:
            # Extract creation parameters
            item_type = parsed_command.parameters.get("type", "bookmark")
            title = parsed_command.parameters.get("title", "")
            content = parsed_command.parameters.get("content", "")
            tags = parsed_command.parameters.get("tags", [])
            
            if parsed_command.entity_type == EntityType.BOOKMARK:
                # Create bookmark
                url = parsed_command.parameters.get("url", "")
                
                if not title and parsed_command.entities:
                    title = " ".join(parsed_command.entities)
                
                # Placeholder for bookmark creation
                return {
                    "action": "create_bookmark",
                    "title": title,
                    "url": url,
                    "tags": tags,
                    "status": "placeholder",
                    "message": f"Would create bookmark '{title}' with tags: {tags}"
                }
            
            elif parsed_command.entity_type == EntityType.VOICE_NOTE:
                # Create voice note
                return {
                    "action": "create_voice_note",
                    "title": title,
                    "content": content,
                    "status": "placeholder",
                    "message": f"Would create voice note: '{title}'"
                }
            
            else:
                return {
                    "status": "placeholder",
                    "message": f"Creation of {parsed_command.entity_type.value} not yet implemented"
                }
                
        except Exception as e:
            return {"status": "error", "message": f"Creation failed: {str(e)}"}
    
    async def _handle_multimodal_command(
        self,
        parsed_command: ParsedCommand,
        user_context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Handle multi-modal analysis commands"""
        try:
            # Extract multimodal context
            multimodal_context = parsed_command.context.get("multimodal_context", {})
            
            if not multimodal_context:
                return {
                    "status": "error",
                    "message": "No multimodal context provided for multimodal command"
                }
            
            # Use multimodal orchestrator
            analysis_result = await multimodal_orchestrator.process_multimodal_content(
                content_data=multimodal_context,
                analysis_depth=parsed_command.parameters.get("depth", "standard")
            )
            
            return {
                "action": "multimodal_analysis",
                "session_id": analysis_result.get("session_id"),
                "modalities_processed": analysis_result.get("modalities_processed", []),
                "insights_count": len(analysis_result.get("cross_modal_insights", {})),
                "recommendations_count": len(analysis_result.get("recommendations", [])),
                "status": "success"
            }
            
        except Exception as e:
            return {"status": "error", "message": f"Multimodal processing failed: {str(e)}"}
    
    # Placeholder handlers for other command types
    async def _handle_update_command(self, parsed_command: ParsedCommand, user_context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        return {"status": "placeholder", "message": "Update commands coming soon"}
    
    async def _handle_delete_command(self, parsed_command: ParsedCommand, user_context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        return {"status": "placeholder", "message": "Delete commands coming soon"}
    
    async def _handle_navigate_command(self, parsed_command: ParsedCommand, user_context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        return {"status": "placeholder", "message": "Navigation commands coming soon"}
    
    async def _handle_configure_command(self, parsed_command: ParsedCommand, user_context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        return {"status": "placeholder", "message": "Configuration commands coming soon"}
    
    async def _handle_export_command(self, parsed_command: ParsedCommand, user_context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        return {"status": "placeholder", "message": "Export commands coming soon"}
    
    async def _handle_voice_control_command(self, parsed_command: ParsedCommand, user_context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        return {"status": "placeholder", "message": "Voice control commands coming soon"}
    
    async def _generate_natural_response(
        self,
        parsed_command: ParsedCommand,
        execution_result: Dict[str, Any],
        original_command: str
    ) -> Dict[str, Any]:
        """Generate a natural language response to the user"""
        try:
            response_prompt = f"""
            Generate a natural, conversational response for this command execution:
            
            Original command: "{original_command}"
            Command type: {parsed_command.command_type.value}
            Execution result: {json.dumps(execution_result, indent=2)}
            
            Create a response that:
            1. Acknowledges what the user requested
            2. Summarizes the results clearly
            3. Uses conversational, friendly tone
            4. Suggests next steps if appropriate
            5. Is concise but informative
            
            Return just the response text, no JSON wrapper.
            """
            
            ai_response = await enhanced_ai_router.route_request({
                "prompt": response_prompt,
                "task_type": "response_generation",
                "priority": 6,
                "metadata": {
                    "command_type": parsed_command.command_type.value,
                    "has_results": execution_result.get("status") == "success"
                }
            })
            
            response_text = ai_response.get("response", "I've processed your request.")
            
            return {
                "text": response_text,
                "tone": "conversational",
                "includes_suggestions": "next" in response_text.lower() or "also" in response_text.lower(),
                "confidence": parsed_command.confidence
            }
            
        except Exception as e:
            logger.error(f"Response generation failed: {e}")
            return {
                "text": "I've processed your request, though I had some trouble generating a detailed response.",
                "tone": "fallback",
                "confidence": 0.5
            }
    
    async def _handle_unclear_command(
        self,
        command_text: str,
        parsed_command: ParsedCommand
    ) -> Dict[str, Any]:
        """Handle commands that couldn't be parsed with high confidence"""
        clarification_prompt = f"""
        The user said: "{command_text}"
        
        I'm not entirely sure what they want to do. Generate a helpful clarification question that:
        1. Acknowledges their request
        2. Asks for specific clarification
        3. Provides examples of what they might mean
        4. Is friendly and helpful
        
        Best guess of intent: {parsed_command.command_type.value} {parsed_command.entity_type.value}
        """
        
        try:
            ai_response = await enhanced_ai_router.route_request({
                "prompt": clarification_prompt,
                "task_type": "clarification",
                "priority": 7
            })
            
            clarification_text = ai_response.get("response", 
                "I'm not sure exactly what you'd like me to do. Could you please rephrase your request?"
            )
            
            return {
                "status": "needs_clarification",
                "original_command": command_text,
                "clarification_request": clarification_text,
                "confidence": parsed_command.confidence,
                "suggestions": [
                    "Try being more specific about what you want to search for",
                    "Include specific file types or time ranges",
                    "Use action words like 'find', 'analyze', or 'create'"
                ]
            }
            
        except Exception as e:
            return {
                "status": "needs_clarification",
                "original_command": command_text,
                "clarification_request": "I'm not sure what you'd like me to do. Could you please be more specific?",
                "error": str(e)
            }
    
    # Helper methods
    def _clean_command_text(self, text: str) -> str:
        """Clean and normalize command text"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Convert to lowercase for processing (but preserve original case in entities)
        return text.lower()
    
    def _fallback_pattern_parsing(self, text: str) -> Dict[str, Any]:
        """Fallback pattern-based parsing when AI parsing fails"""
        # Simple pattern matching for basic commands
        for command_type, patterns in self.command_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    return {
                        "command_type": command_type.value,
                        "entity_type": "content",  # Default
                        "action": command_type.value,
                        "parameters": {"query": match.group(1) if match.groups() else text},
                        "entities": [match.group(1)] if match.groups() else [],
                        "confidence": 0.4
                    }
        
        # Default fallback
        return {
            "command_type": "search",
            "entity_type": "content",
            "action": "search",
            "parameters": {"query": text},
            "entities": [],
            "confidence": 0.3
        }
    
    async def _enhance_parameters(
        self,
        parameters: Dict[str, Any],
        command_text: str,
        user_context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Enhance parameters with context-aware extraction"""
        enhanced = parameters.copy()
        
        # Extract time filters
        for time_phrase, delta in self.context_keywords['time_filters'].items():
            if time_phrase in command_text:
                enhanced['time_filter'] = {
                    'phrase': time_phrase,
                    'since': (datetime.utcnow() - delta).isoformat()
                }
                break
        
        # Extract language filters
        for language in self.context_keywords['languages']:
            if language in command_text.lower():
                enhanced.setdefault('filters', {})['language'] = language
                break
        
        # Extract content type filters
        for content_type in self.context_keywords['content_types']:
            if content_type in command_text.lower():
                enhanced.setdefault('filters', {})['type'] = content_type
                break
        
        # Extract analysis type
        for analysis_type in self.context_keywords['analysis_types']:
            if analysis_type in command_text.lower():
                enhanced['analysis_type'] = analysis_type
                break
        
        return enhanced


# Create singleton instance
natural_language_controller = NaturalLanguageController()