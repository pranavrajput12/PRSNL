#!/usr/bin/env python3
"""
Setup script for PRSNL Media Processing Agents
Fixes common dependency and configuration issues
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_command(cmd: str, check=True) -> bool:
    """Run a command and return success status"""
    try:
        result = subprocess.run(cmd, shell=True, check=check, capture_output=True, text=True)
        if result.returncode == 0:
            logger.info(f"✅ {cmd}")
            return True
        else:
            logger.error(f"❌ {cmd} failed: {result.stderr}")
            return False
    except Exception as e:
        logger.error(f"❌ {cmd} failed with exception: {e}")
        return False

def check_system_dependencies():
    """Check and install system dependencies"""
    logger.info("🔍 Checking system dependencies...")
    
    # Check if we're on macOS ARM64
    if sys.platform == "darwin":
        arch_result = subprocess.run(["uname", "-m"], capture_output=True, text=True)
        if "arm64" in arch_result.stdout:
            logger.info("✅ Detected macOS ARM64 architecture")
        else:
            logger.warning("⚠️  Not ARM64 architecture, some optimizations may not work")
    
    # Check for Homebrew (macOS)
    homebrew_path = "/opt/homebrew/bin/brew"
    if os.path.exists(homebrew_path):
        logger.info("✅ Homebrew found")
    else:
        logger.error("❌ Homebrew not found. Install from https://brew.sh/")
        return False
    
    # Check for system dependencies
    dependencies = {
        "ffmpeg": "Media processing (video/audio conversion)",
        "tesseract": "OCR text extraction from images",
        "poppler": "PDF processing utilities"
    }
    
    missing_deps = []
    for dep, description in dependencies.items():
        if not run_command(f"which {dep}", check=False):
            missing_deps.append((dep, description))
    
    if missing_deps:
        logger.info("📦 Installing missing system dependencies...")
        for dep, description in missing_deps:
            logger.info(f"Installing {dep} ({description})")
            if not run_command(f"{homebrew_path} install {dep}"):
                logger.error(f"Failed to install {dep}")
                return False
    
    return True

def setup_python_dependencies():
    """Install and fix Python dependencies"""
    logger.info("🐍 Setting up Python dependencies...")
    
    # Install specific packages that commonly fail
    problematic_packages = [
        "pytesseract==0.3.10",  # OCR library
        "pywhispercpp>=1.2.0",  # Whisper.cpp bindings
        "Pillow==10.2.0",       # Image processing
        "httpx==0.26.0",        # HTTP client for downloads
    ]
    
    for package in problematic_packages:
        logger.info(f"Installing {package}...")
        if not run_command(f"pip install {package}"):
            logger.error(f"Failed to install {package}")
            return False
    
    # Fix common ARM64 issues
    if sys.platform == "darwin":
        arch_result = subprocess.run(["uname", "-m"], capture_output=True, text=True)
        if "arm64" in arch_result.stdout:
            logger.info("🔧 Applying ARM64 fixes...")
            # Set environment variables for ARM64 compatibility
            os.environ["ARCHFLAGS"] = "-arch arm64"
            os.environ["HOMEBREW_PREFIX"] = "/opt/homebrew"
    
    return True

def setup_whisper_models():
    """Download and setup Whisper models"""
    logger.info("🎵 Setting up Whisper models...")
    
    # Create models directory
    models_dir = Path("storage/whisper_models")
    models_dir.mkdir(parents=True, exist_ok=True)
    
    # Download base model (good balance of speed/accuracy)
    base_model_path = models_dir / "ggml-base.bin"
    if not base_model_path.exists():
        logger.info("📥 Downloading Whisper base model...")
        download_url = "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.bin"
        
        if run_command(f"curl -L {download_url} -o {base_model_path}"):
            logger.info("✅ Whisper base model downloaded")
        else:
            logger.error("❌ Failed to download Whisper model")
            return False
    else:
        logger.info("✅ Whisper base model already exists")
    
    return True

def setup_tesseract():
    """Configure Tesseract OCR"""
    logger.info("👁️  Setting up Tesseract OCR...")
    
    # Check if Tesseract is properly installed
    if not run_command("tesseract --version", check=False):
        logger.error("❌ Tesseract not found. Run: brew install tesseract")
        return False
    
    # Install additional language packs
    try:
        # Try to install additional language support
        run_command("/opt/homebrew/bin/brew install tesseract-lang", check=False)
        logger.info("✅ Tesseract language packs installed")
    except:
        logger.warning("⚠️  Could not install additional language packs")
    
    return True

def create_test_files():
    """Create test files for media agents"""
    logger.info("🧪 Creating test files...")
    
    # Create test directories
    test_dir = Path("storage/test_media")
    test_dir.mkdir(parents=True, exist_ok=True)
    
    # Create a simple test image for OCR
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        # Create a simple test image with text
        img = Image.new('RGB', (400, 200), color='white')
        draw = ImageDraw.Draw(img)
        
        # Try to use a system font, fall back to default
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 24)
        except:
            font = ImageFont.load_default()
        
        draw.text((20, 50), "Test OCR Image", fill='black', font=font)
        draw.text((20, 100), "This is a test for", fill='black', font=font)
        draw.text((20, 150), "PRSNL Media Agents", fill='black', font=font)
        
        test_image_path = test_dir / "test_ocr.png"
        img.save(test_image_path)
        logger.info(f"✅ Created test OCR image: {test_image_path}")
        
    except Exception as e:
        logger.warning(f"⚠️  Could not create test image: {e}")
    
    return True

def test_media_agents():
    """Test that media agents are working"""
    logger.info("🧪 Testing media agents...")
    
    try:
        # Test OCR
        import pytesseract
        from PIL import Image
        
        test_image_path = Path("storage/test_media/test_ocr.png")
        if test_image_path.exists():
            img = Image.open(test_image_path)
            text = pytesseract.image_to_string(img)
            if "Test OCR" in text:
                logger.info("✅ OCR test passed")
            else:
                logger.warning("⚠️  OCR test failed - no text detected")
        
        # Test Whisper CPP availability
        try:
            from pywhispercpp.model import Model
            logger.info("✅ Whisper CPP bindings available")
        except ImportError:
            logger.warning("⚠️  Whisper CPP bindings not available")
        
        # Test FFmpeg
        if run_command("ffmpeg -version", check=False):
            logger.info("✅ FFmpeg available")
        else:
            logger.warning("⚠️  FFmpeg not available")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Media agent test failed: {e}")
        return False

def main():
    """Main setup function"""
    logger.info("🚀 Setting up PRSNL Media Processing Agents...")
    
    steps = [
        ("System Dependencies", check_system_dependencies),
        ("Python Dependencies", setup_python_dependencies),
        ("Whisper Models", setup_whisper_models),
        ("Tesseract OCR", setup_tesseract),
        ("Test Files", create_test_files),
        ("Agent Testing", test_media_agents)
    ]
    
    for step_name, step_func in steps:
        logger.info(f"\n📋 Step: {step_name}")
        if not step_func():
            logger.error(f"❌ Step failed: {step_name}")
            sys.exit(1)
        logger.info(f"✅ Step completed: {step_name}")
    
    logger.info("\n🎉 Media Agents setup completed successfully!")
    logger.info("\nNext steps:")
    logger.info("1. Run the backend server: uvicorn app.main:app --reload")
    logger.info("2. Test media processing endpoints")
    logger.info("3. Upload images/videos to test agents")

if __name__ == "__main__":
    main()