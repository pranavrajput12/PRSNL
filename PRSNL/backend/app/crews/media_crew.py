"""
Media Processing Crew - Orchestrates multimedia content processing

This crew handles comprehensive media processing workflows including images,
audio, and video content with integrated analysis and knowledge extraction.
"""

import logging
from typing import Any, Dict, List, Optional
from crewai import Agent, Crew, Task, Process
from crewai.project import CrewBase, agent, crew, task

from app.crews.base_crew import PRSNLBaseCrew
from app.crews import register_crew
from app.agents.media import (
    OCRImageAgent,
    VideoProcessorAgent,
    AudioJournalAgent,
    MediaCoordinatorAgent
)

logger = logging.getLogger(__name__)


@register_crew("media_processing")
class MediaProcessingCrew(PRSNLBaseCrew):
    """Crew for comprehensive media processing workflows"""
    
    @agent
    def media_coordinator(self) -> Agent:
        """Media Coordinator agent"""
        agent_instance = MediaCoordinatorAgent()
        return agent_instance.get_agent()
    
    @agent
    def ocr_image_analyst(self) -> Agent:
        """OCR Image Analysis agent"""
        agent_instance = OCRImageAgent()
        return agent_instance.get_agent()
    
    @agent
    def video_processor(self) -> Agent:
        """Video Processor agent"""
        agent_instance = VideoProcessorAgent()
        return agent_instance.get_agent()
    
    @agent
    def audio_journal_processor(self) -> Agent:
        """Audio Journal Processor agent"""
        agent_instance = AudioJournalAgent()
        return agent_instance.get_agent()
    
    @task
    def coordinate_media_workflow_task(self) -> Task:
        """Task for coordinating media processing workflow"""
        return Task(
            description=(
                "Coordinate the processing of multiple media files including images, "
                "audio, and video content. Plan the workflow, manage dependencies, "
                "and ensure optimal processing sequence. Media files: {media_files}"
            ),
            expected_output=(
                "A comprehensive workflow plan including:\n"
                "1. Processing sequence and dependencies\n"
                "2. Resource allocation and timing\n"
                "3. Quality checkpoints and validation\n"
                "4. Integration strategy for results\n"
                "5. Risk assessment and mitigation"
            ),
            agent=self.media_coordinator()
        )
    
    @task
    def process_images_task(self) -> Task:
        """Task for processing image files"""
        return Task(
            description=(
                "Process all image files using OCR and computer vision analysis. "
                "Extract text, identify objects, generate descriptions, and create "
                "accessibility metadata. Images: {image_files}"
            ),
            expected_output=(
                "Complete image analysis including:\n"
                "1. OCR text extraction with confidence scores\n"
                "2. Object detection and scene analysis\n"
                "3. Accessibility descriptions and alt text\n"
                "4. Extracted entities and tags\n"
                "5. Quality assessment and recommendations"
            ),
            agent=self.ocr_image_analyst()
        )
    
    @task
    def process_video_task(self) -> Task:
        """Task for processing video files"""
        return Task(
            description=(
                "Process video files to extract frames, transcribe audio, and "
                "analyze visual content. Create timestamped summaries and "
                "accessibility features. Videos: {video_files}"
            ),
            expected_output=(
                "Comprehensive video analysis including:\n"
                "1. Key frame extraction and analysis\n"
                "2. Audio transcription with timestamps\n"
                "3. Visual content analysis\n"
                "4. Accessibility captions and descriptions\n"
                "5. Learning objectives and study materials"
            ),
            agent=self.video_processor()
        )
    
    @task
    def process_audio_task(self) -> Task:
        """Task for processing audio files"""
        return Task(
            description=(
                "Process audio files including journal entries, recordings, and "
                "voice notes. Extract insights, emotions, and create structured "
                "personal knowledge. Audio files: {audio_files}"
            ),
            expected_output=(
                "Detailed audio analysis including:\n"
                "1. High-accuracy transcription\n"
                "2. Emotional content and sentiment analysis\n"
                "3. Personal insights and reflections\n"
                "4. Recurring themes and patterns\n"
                "5. Reflection prompts and action items"
            ),
            agent=self.audio_journal_processor()
        )
    
    @task
    def integrate_results_task(self) -> Task:
        """Task for integrating results from all media processing"""
        return Task(
            description=(
                "Integrate and synthesize results from all media processing agents. "
                "Create unified knowledge structures, identify cross-references, "
                "and generate comprehensive summaries."
            ),
            expected_output=(
                "Integrated multimedia analysis including:\n"
                "1. Unified entity consolidation\n"
                "2. Cross-media references and connections\n"
                "3. Timeline reconstruction\n"
                "4. Knowledge graph representation\n"
                "5. Quality assessment and recommendations"
            ),
            agent=self.media_coordinator()
        )
    
    @crew
    def crew(self) -> Crew:
        """Creates the Media Processing crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
            memory=True,
            embedder={
                "provider": "azure_openai",
                "config": {
                    "model": settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
                    "api_key": settings.AZURE_OPENAI_API_KEY,
                    "api_base": settings.AZURE_OPENAI_ENDPOINT,
                    "api_version": settings.AZURE_OPENAI_API_VERSION
                }
            }
        )


@register_crew("educational_media_processing")
class EducationalMediaProcessingCrew(MediaProcessingCrew):
    """Specialized crew for processing educational media content"""
    
    @agent
    def educational_video_processor(self) -> Agent:
        """Educational Video Processor agent"""
        from app.agents.media.video_processor_agent import EducationalVideoProcessorAgent
        agent_instance = EducationalVideoProcessorAgent()
        return agent_instance.get_agent()
    
    @task
    def create_learning_materials_task(self) -> Task:
        """Task for creating educational materials from media"""
        return Task(
            description=(
                "Create comprehensive learning materials from processed media content. "
                "Generate study guides, practice questions, and assessment materials "
                "suitable for educational use."
            ),
            expected_output=(
                "Educational materials package including:\n"
                "1. Study guides and notes\n"
                "2. Practice questions and assessments\n"
                "3. Flashcards and review materials\n"
                "4. Learning objectives and outcomes\n"
                "5. Accessibility accommodations"
            ),
            agent=self.educational_video_processor()
        )
    
    @crew
    def crew(self) -> Crew:
        """Creates the Educational Media Processing crew"""
        # Replace video processor with educational version
        agents = [
            self.media_coordinator(),
            self.ocr_image_analyst(),
            self.educational_video_processor(),
            self.audio_journal_processor()
        ]
        
        tasks = self.tasks + [self.create_learning_materials_task()]
        
        return Crew(
            agents=agents,
            tasks=tasks,
            process=Process.sequential,
            verbose=True,
            memory=True
        )


@register_crew("personal_media_processing")
class PersonalMediaProcessingCrew(MediaProcessingCrew):
    """Specialized crew for processing personal media content"""
    
    @agent
    def therapeutic_audio_processor(self) -> Agent:
        """Therapeutic Audio Processor agent"""
        from app.agents.media.audio_journal_agent import TherapeuticAudioProcessorAgent
        agent_instance = TherapeuticAudioProcessorAgent()
        return agent_instance.get_agent()
    
    @task
    def analyze_personal_growth_task(self) -> Task:
        """Task for analyzing personal growth patterns"""
        return Task(
            description=(
                "Analyze personal media content to identify growth patterns, "
                "emotional trends, and development opportunities. Focus on "
                "therapeutic insights and personal development indicators."
            ),
            expected_output=(
                "Personal growth analysis including:\n"
                "1. Emotional trend analysis\n"
                "2. Growth pattern identification\n"
                "3. Therapeutic progress indicators\n"
                "4. Personal development recommendations\n"
                "5. Goal achievement tracking"
            ),
            agent=self.therapeutic_audio_processor()
        )
    
    def get_process_type(self) -> str:
        """Use hierarchical process for personal content"""
        return "hierarchical"
    
    @crew
    def crew(self) -> Crew:
        """Creates the Personal Media Processing crew"""
        # Replace audio processor with therapeutic version
        agents = [
            self.media_coordinator(),
            self.ocr_image_analyst(),
            self.video_processor(),
            self.therapeutic_audio_processor()
        ]
        
        tasks = self.tasks + [self.analyze_personal_growth_task()]
        
        return Crew(
            agents=agents,
            tasks=tasks,
            process=Process.hierarchical,
            manager_llm=self.get_llm_config(),
            verbose=True,
            memory=True
        )


@register_crew("rapid_media_processing")
class RapidMediaProcessingCrew(PRSNLBaseCrew):
    """Lightweight crew for rapid media processing"""
    
    @agent
    def quick_media_processor(self) -> Agent:
        """Quick Media Processor for rapid processing"""
        return Agent(
            role="Quick Media Processor",
            goal="Process media files rapidly with basic analysis",
            backstory="Efficient processor focused on speed over depth",
            tools=[],
            llm=self.get_llm_config(),
            memory=False  # Disable memory for speed
        )
    
    @task
    def rapid_process_task(self) -> Task:
        """Task for rapid media processing"""
        return Task(
            description=(
                "Quickly process media files with basic analysis. "
                "Focus on essential information extraction. Files: {media_files}"
            ),
            expected_output=(
                "Basic media analysis including:\n"
                "1. File type and metadata\n"
                "2. Basic content extraction\n"
                "3. Simple tagging and categorization\n"
                "4. Quality assessment"
            ),
            agent=self.quick_media_processor()
        )
    
    @crew
    def crew(self) -> Crew:
        """Creates the Rapid Media Processing crew"""
        return Crew(
            agents=[self.quick_media_processor()],
            tasks=[self.rapid_process_task()],
            process=Process.sequential,
            verbose=False,
            memory=False
        )