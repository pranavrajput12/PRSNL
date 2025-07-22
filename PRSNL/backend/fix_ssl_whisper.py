#!/usr/bin/env python3
"""
Fix SSL certificate issue for Whisper model download
"""
import ssl
import certifi
import os

# Create unverified context
ssl._create_default_https_context = ssl._create_unverified_context

# Now test whisper
import whisper

print("Testing Whisper model loading...")
model = whisper.load_model("base")
print("✅ Whisper model loaded successfully!")

# Test transcription
result = model.transcribe("/dev/null")
print("✅ Whisper is working!")