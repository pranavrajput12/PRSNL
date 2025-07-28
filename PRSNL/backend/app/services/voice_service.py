"""
Voice Service for PRSNL - Speech-to-Text and Text-to-Speech with Cortex personality
"""

import ssl
# Fix SSL certificate issues for model downloads
ssl._create_default_https_context = ssl._create_unverified_context

import os
import shutil

# Set ffmpeg path explicitly for Whisper
FFMPEG_PATH = '/opt/homebrew/bin/ffmpeg'

# Check if ffmpeg exists at the expected location
if os.path.exists(FFMPEG_PATH):
    os.environ['PATH'] = f"/opt/homebrew/bin:{os.environ.get('PATH', '')}"
    os.environ['FFMPEG_BINARY'] = FFMPEG_PATH
    # Note: ffmpeg found at expected location (logged at debug level only)
else:
    # Try to find ffmpeg in system PATH
    ffmpeg_in_path = shutil.which('ffmpeg')
    if ffmpeg_in_path:
        os.environ['FFMPEG_BINARY'] = ffmpeg_in_path
        # Note: ffmpeg found in PATH (logged at debug level only)
    else:
        raise RuntimeError(
            "ffmpeg not found. Please install ffmpeg:\n"
            "  - macOS: brew install ffmpeg\n"
            "  - Ubuntu/Debian: sudo apt-get install ffmpeg\n"
            "  - Or set FFMPEG_BINARY environment variable to ffmpeg location"
        )

import whisper
from faster_whisper import WhisperModel
import asyncio
from edge_tts import Communicate
import tempfile
import logging
from typing import Optional, Dict, Any
import random
import json

from app.core.langfuse_wrapper import observe  # Safe wrapper to handle get_tracer error
from app.services.ai_service import AIService
from app.services.chat_service import ChatService
from app.services.tts_manager import get_tts_manager
# from app.crews.voice_crew import VoiceCrew, VoiceSimpleCrew  # Temporarily disabled due to OpenTelemetry conflicts
from app.config import settings

logger = logging.getLogger(__name__)


class CortexPersonality:
    """Defines Cortex's personality and speaking patterns"""
    
    PERSONALITY_TRAITS = {
        "base": {
            "name": "Cortex",
            "role": "Prefrontal Cortex - Executive thinking & decision making",
            "traits": ["thoughtful", "analytical", "supportive", "occasionally_witty"],
            "speaking_style": "clear and insightful with moments of warmth"
        },
        
        "phrases": {
            "greeting": [
                "Hey! Cortex here.",
                "Hello! Your prefrontal cortex at your service.",
                "Hi there! Ready to explore some ideas?"
            ],
            "thinking": [
                "Hmm, let me think about that...",
                "Interesting question...",
                "Let me process that for you..."
            ],
            "discovering": [
                "Oh, this is fascinating!",
                "I just noticed something interesting...",
                "Your thought patterns suggest...",
                "I found something in your knowledge base!"
            ],
            "encouraging": [
                "You're making great neural connections!",
                "Your thinking has evolved since last time.",
                "I love how your mind works!",
                "That's a brilliant insight!"
            ]
        },
        
        "moods": {
            "discovering": {
                "phrases": ["Oh, this is fascinating!", "I just noticed something interesting..."],
                "voice_settings": {"rate": "+5%", "pitch": "+5Hz"}
            },
            "explaining": {
                "phrases": ["Let me break this down...", "Think of it this way:"],
                "voice_settings": {"rate": "-5%", "pitch": "+0Hz"}
            },
            "encouraging": {
                "phrases": ["You're making great neural connections!", "I love how your mind works!"],
                "voice_settings": {"rate": "+0%", "pitch": "+3Hz"}
            }
        }
    }
    
    def __init__(self):
        self.conversation_history = []
        
    def detect_context(self, user_message: str, ai_response: str) -> Dict[str, Any]:
        """Detect the context and mood for the response"""
        context = {
            "mood": "primary",
            "should_add_personality": True,
            "complexity": len(ai_response.split()) > 50
        }
        
        # Detect mood based on content
        lower_response = ai_response.lower()
        if any(word in lower_response for word in ["discovered", "found", "interesting", "fascinating"]):
            context["mood"] = "discovering"
        elif any(word in lower_response for word in ["let me explain", "here's how", "the reason"]):
            context["mood"] = "explaining"
        elif any(word in lower_response for word in ["great", "excellent", "well done"]):
            context["mood"] = "encouraging"
            
        # Check if this is first interaction
        if len(self.conversation_history) == 0:
            context["first_interaction"] = True
            
        return context
    
    def add_personality(self, text: str, context: Dict[str, Any]) -> str:
        """Add Cortex's personality to the response"""
        
        # Add greeting for first interaction
        if context.get("first_interaction"):
            greeting = random.choice(self.PERSONALITY_TRAITS["phrases"]["greeting"])
            text = f"{greeting} {text}"
            
        # Add mood-based phrases occasionally
        mood = context.get("mood", "primary")
        if mood in self.PERSONALITY_TRAITS["moods"] and random.random() < 0.3:
            prefix = random.choice(self.PERSONALITY_TRAITS["moods"][mood]["phrases"])
            text = f"{prefix} {text}"
            
        # Add thinking pauses for complex responses
        if context.get("complexity") and random.random() < 0.5:
            text = f"Hmm... {text}"
            
        return text
    
    def get_voice_settings(self, mood: str) -> Dict[str, str]:
        """Get voice settings for the current mood"""
        default = {"rate": "-5%", "pitch": "+2Hz"}
        
        if mood in self.PERSONALITY_TRAITS["moods"]:
            return self.PERSONALITY_TRAITS["moods"][mood].get("voice_settings", default)
        
        return default


class VoiceService:
    """Voice service with STT, TTS, and Cortex personality"""
    
    VOICE_OPTIONS = {
        "female": {
            "primary": "en-US-AriaNeural",      # Warm, friendly
            "thoughtful": "en-US-JennyNeural",  # Professional
            "excited": "en-US-SaraNeural"       # Enthusiastic
        },
        "male": {
            "primary": "en-US-GuyNeural",       # Conversational
            "thoughtful": "en-US-DavisNeural",  # Calm, wise
            "excited": "en-US-TonyNeural"       # Energetic
        }
    }
    
    def __init__(self):
        # Load Whisper model (small = 39M, good accuracy/speed balance)
        logger.info("Loading Whisper model...")
        logger.info(f"FFMPEG_BINARY env var: {os.environ.get('FFMPEG_BINARY', 'Not set')}")
        logger.info(f"PATH env var includes /opt/homebrew/bin: {'/opt/homebrew/bin' in os.environ.get('PATH', '')}")
        
        try:
            # Use memory-optimized faster-whisper instead of regular whisper
            model_name = getattr(settings, 'VOICE_STT_MODEL', 'small')
            
            # Map regular whisper model names to faster-whisper equivalents
            # Use tiny.en for maximum memory efficiency (39MB vs 244MB)
            model_map = {
                'tiny': 'tiny.en',
                'base': 'base.en', 
                'small': 'tiny.en',  # Use tiny.en instead of small for memory savings
                'medium': 'base.en', # Use base.en instead of medium for memory savings
                'large': 'base.en'   # Use base.en instead of large for memory savings
            }
            
            faster_model_name = model_map.get(model_name, 'tiny.en')
            
            # Initialize faster-whisper with memory optimizations
            self.whisper_model = WhisperModel(
                faster_model_name,
                device="cpu",  # Use CPU for compatibility (ARM64 Mac)
                compute_type="int8",  # Use INT8 quantization for 50% memory reduction
                cpu_threads=4,  # Limit CPU threads for memory efficiency
                num_workers=1   # Single worker to minimize memory usage
            )
            logger.info(f"✅ faster-whisper '{faster_model_name}' model loaded successfully (memory-optimized)")
            logger.info(f"   Memory saved: ~200MB compared to regular Whisper '{model_name}'")
            
        except Exception as e:
            logger.warning(f"Failed to load faster-whisper '{faster_model_name}': {e}, falling back to tiny.en")
            try:
                # Ultimate fallback to tiny.en with maximum memory efficiency
                self.whisper_model = WhisperModel(
                    "tiny.en",
                    device="cpu",
                    compute_type="int8",
                    cpu_threads=2,
                    num_workers=1
                )
                logger.info("✅ faster-whisper 'tiny.en' model loaded as fallback (ultra memory-efficient)")
            except Exception as fallback_error:
                logger.error(f"❌ Failed to load any faster-whisper model: {fallback_error}")
                # Final fallback to regular whisper base model
                try:
                    self.whisper_model = whisper.load_model("base")
                    logger.warning("⚠️ Using regular Whisper 'base' as final fallback (higher memory usage)")
                except Exception as final_error:
                    logger.error(f"❌ Complete failure to load any Whisper model: {final_error}")
                    raise
        
        # Initialize services
        self.ai_service = AIService()
        self.chat_service = ChatService(self.ai_service)
        self.personality = CortexPersonality()
        
        # Initialize TTS manager with configured backend
        from app.services.tts_manager import TTSManager
        self.tts_manager = TTSManager(primary_backend=settings.VOICE_TTS_ENGINE)
        logger.info(f"TTS Manager initialized with primary backend: {settings.VOICE_TTS_ENGINE}")
        
        # Initialize voice crew for enhanced responses - temporarily disabled
        # self.voice_crew = VoiceCrew()
        # self.simple_crew = VoiceSimpleCrew()
        self.use_crew = False  # Disabled due to OpenTelemetry conflicts
        
        # Voice settings
        self.voice_gender = settings.VOICE_DEFAULT_GENDER
        self.voices = self.VOICE_OPTIONS[self.voice_gender]
        
        logger.info("Voice service initialized with Cortex personality and CrewAI")
        
    # @observe(name="process_voice_message")
    async def process_voice_message(self, audio_data: bytes, user_id: str) -> Dict[str, Any]:
        """Complete voice chat pipeline"""
        
        # 1. Save audio temporarily
        # Try multiple formats in case ffmpeg has issues
        audio_suffix = ".webm"
        with tempfile.NamedTemporaryFile(suffix=audio_suffix, delete=False) as tmp:
            tmp.write(audio_data)
            audio_path = tmp.name
        
        try:
            # 2. Speech to Text
            logger.info("Converting speech to text...")
            user_text = await self.speech_to_text(audio_path)
            logger.info(f"User said: {user_text}")
            
            # 3. Get AI response - use CrewAI or chat service
            logger.info("Getting AI response...")
            
            # Always use regular chat service (CrewAI disabled)
            chat_response = await self.chat_service.process_message(
                message=user_text,
                user_id=user_id,
                context_type="voice"
            )
            context = self.personality.detect_context(user_text, chat_response["content"])
            
            # 4. Add personality
            personalized_response = self.personality.add_personality(
                chat_response["content"], 
                context
            )
            
            # 5. Text to Speech with personality
            logger.info("Converting response to speech...")
            audio_response = await self.text_to_speech(personalized_response, context)
            
            # 6. Update conversation history
            self.personality.conversation_history.append({
                "user": user_text,
                "cortex": chat_response["content"],
                "mood": context["mood"]
            })
            
            return {
                "user_text": user_text,
                "ai_text": chat_response["content"],
                "personalized_text": personalized_response,
                "audio_data": audio_response,
                "audio_format": "mp3",
                "mood": context["mood"],
                "context": chat_response.get("context", {})
            }
            
        finally:
            # Clean up temp file
            if os.path.exists(audio_path):
                os.unlink(audio_path)
    
    # @observe(name="speech_to_text_faster_whisper")
    async def speech_to_text(self, audio_path: str) -> str:
        """Convert speech to text using faster-whisper (memory-optimized)"""
        try:
            # Ensure ffmpeg is available for Whisper
            if not os.environ.get('FFMPEG_BINARY'):
                logger.warning("FFMPEG_BINARY not set, attempting to set it...")
                ffmpeg_path = shutil.which('ffmpeg') or '/opt/homebrew/bin/ffmpeg'
                if os.path.exists(ffmpeg_path):
                    os.environ['FFMPEG_BINARY'] = ffmpeg_path
            
            # Check if we're using faster-whisper or regular whisper
            is_faster_whisper = hasattr(self.whisper_model, 'transcribe') and callable(getattr(self.whisper_model, 'transcribe'))
            
            if isinstance(self.whisper_model, WhisperModel):
                # Use faster-whisper API (returns segments and info)
                loop = asyncio.get_event_loop()
                segments, info = await loop.run_in_executor(
                    None,
                    lambda: self.whisper_model.transcribe(
                        audio_path,
                        language="en",
                        beam_size=1,  # Faster inference with slight accuracy trade-off
                        best_of=1,    # Use single beam for speed
                        temperature=0.0,  # Deterministic output
                        compression_ratio_threshold=2.4,  # Default compression threshold
                        log_prob_threshold=-1.0,  # Default log prob threshold
                        no_speech_threshold=0.6,  # Default no speech threshold
                        condition_on_previous_text=False,  # Don't condition on previous text for memory efficiency
                        initial_prompt=None,  # No initial prompt for speed
                        word_timestamps=False,  # Disable word timestamps for speed
                        prepend_punctuations="\"'([{-",
                        append_punctuations="\"'.。,，!！?？:：\")]}、"
                    )
                )
                
                # Combine all segments into single text
                text = " ".join(segment.text for segment in segments).strip()
                logger.info(f"faster-whisper transcription completed. Language: {info.language}, Duration: {info.duration:.2f}s")
                
            else:
                # Fallback to regular whisper API
                logger.info("Using regular Whisper API (fallback)")
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None, 
                    lambda: self.whisper_model.transcribe(
                        audio_path, 
                        language="en",
                        fp16=False  # Disable FP16 for better compatibility
                    )
                )
                text = result["text"].strip()
            
            # Clean up common speech artifacts
            text = text.replace(" umm ", " ")
            text = text.replace(" uh ", " ")
            text = text.replace("  ", " ")  # Remove double spaces
            
            logger.info(f"STT completed: '{text[:100]}{'...' if len(text) > 100 else ''}'")
            return text
            
        except Exception as e:
            logger.error(f"Error in speech to text: {e}")
            logger.error(f"Audio path: {audio_path}")
            logger.error(f"FFMPEG_BINARY: {os.environ.get('FFMPEG_BINARY', 'Not set')}")
            logger.error(f"Model type: {type(self.whisper_model)}")
            raise
    
    # @observe(name="process_text_message_voice")
    async def process_text_message(self, text: str, user_id: str) -> Dict[str, Any]:
        """Process text message and generate AI response with Cortex personality"""
        try:
            # Get AI response - use CrewAI or chat service
            logger.info(f"Processing text message: {text[:50]}...")
            
            # Always use direct chat service (CrewAI disabled)
            from app.services.chat_service import ChatService
            chat_service = ChatService(self.ai_service)
            
            # Process message with voice context
            chat_response = await chat_service.process_message(
                message=text,
                user_id=user_id,
                context_type="voice"
            )
            
            ai_text = chat_response["content"]
            
            # Apply Cortex personality using detect_context
            context = self.personality.detect_context(text, ai_text)
            personalized_text = self.personality.add_personality(ai_text, context)
            
            # Update conversation history
            self.personality.conversation_history.append({
                "user": text,
                "cortex": ai_text,
                "mood": context["mood"]
            })
            
            return {
                "user_text": text,
                "ai_text": ai_text,
                "personalized_text": personalized_text,
                "mood": context["mood"],
                "emotion": "neutral"
            }
            
        except Exception as e:
            logger.error(f"Error processing text message: {e}")
            raise
    
    # @observe(name="text_to_speech")
    async def text_to_speech(self, text: str, context: Dict[str, Any] = None) -> bytes:
        """Convert text to speech using modern TTS with Cortex personality"""
        try:
            # Handle optional context
            if context is None:
                context = {}
            
            # Select voice based on mood
            mood = context.get("mood", "primary")
            
            # Clean text - remove any markup
            import re
            logger.info(f"Original text for TTS: {text}")
            clean_text = re.sub(r'<[^>]+>', '', text)
            clean_text = clean_text.replace("<", "").replace(">", "")
            clean_text = ' '.join(clean_text.split())
            logger.info(f"Cleaned text for TTS: {clean_text}")
            
            # Map Cortex moods to emotions for TTS
            emotion_map = {
                "discovering": "excited",
                "explaining": "thoughtful",
                "encouraging": "cheerful",
                "primary": "neutral",
                "curious": "interested"
            }
            
            emotion = emotion_map.get(mood, "neutral")
            
            # Check if primary backend supports emotion
            if self.tts_manager.supports_emotion():
                # Use emotion-aware TTS (Chatterbox)
                logger.info(f"Using emotion-aware TTS with emotion: {emotion}")
                
                # Adjust emotion strength based on context and settings
                base_strength = settings.VOICE_EMOTION_STRENGTH
                emotion_strength = base_strength * 1.2 if context.get("excitement_level", 0) > 0.7 else base_strength
                
                audio_data = await self.tts_manager.synthesize(
                    text=clean_text,
                    emotion=emotion,
                    emotion_strength=emotion_strength
                )
            else:
                # Use non-emotion TTS with enhanced voice selection and rate control
                backend = self.tts_manager.primary_backend
                logger.info(f"Using {backend} TTS with natural voice settings")
                
                voice = self._select_voice(mood)
                voice_settings = self.personality.get_voice_settings(mood)
                
                # Add speaking rate for more natural speech (slower = more natural)
                speech_rate = 0.85  # Slightly slower than default for better clarity
                if mood == "explaining":
                    speech_rate = 0.75  # Even slower for explanations
                elif mood == "exciting" or mood == "discovering":
                    speech_rate = 0.95  # Slightly faster for excitement
                
                audio_data = await self.tts_manager.synthesize(
                    text=clean_text,
                    backend=backend,
                    voice=voice,
                    rate=speech_rate
                )
            
            return audio_data
            
        except Exception as e:
            logger.error(f"Error in text to speech: {e}")
            # Try fallback to Edge-TTS
            try:
                logger.info("Primary TTS failed, trying Edge-TTS fallback")
                voice = self._select_voice(context.get("mood", "primary"))
                
                from edge_tts import Communicate
                communicate = Communicate(clean_text, voice)
                
                with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                    await communicate.save(tmp.name)
                    with open(tmp.name, 'rb') as f:
                        audio_data = f.read()
                    os.unlink(tmp.name)
                    
                return audio_data
            except Exception as fallback_error:
                logger.error(f"All TTS options failed: {fallback_error}")
                raise
    
    def _select_voice(self, mood: str) -> str:
        """Select appropriate voice for mood"""
        voice_map = {
            "discovering": "excited",
            "explaining": "thoughtful",
            "encouraging": "primary",
            "primary": "primary"
        }
        
        voice_type = voice_map.get(mood, "primary")
        return self.voices.get(voice_type, self.voices["primary"])
    
    def _enhance_with_ssml(self, text: str) -> str:
        """Clean text for TTS (Edge-TTS doesn't need SSML)"""
        # Just return clean text - Edge-TTS handles pauses naturally
        return text
    
    def set_voice_gender(self, gender: str):
        """Change voice gender preference"""
        if gender in self.VOICE_OPTIONS:
            self.voice_gender = gender
            self.voices = self.VOICE_OPTIONS[gender]
            logger.info(f"Voice gender set to: {gender}")


# Singleton instance
_voice_service_instance = None

def get_voice_service() -> VoiceService:
    """Get singleton voice service instance"""
    global _voice_service_instance
    if _voice_service_instance is None:
        _voice_service_instance = VoiceService()
    return _voice_service_instance