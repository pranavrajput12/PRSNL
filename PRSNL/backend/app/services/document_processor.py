"""Document processing service for handling uploaded files"""
import asyncio
import csv
import hashlib
import io
import logging
import mimetypes
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

import aiofiles
import aiofiles.os
import docx

# For text extraction
from markitdown import MarkItDown
import pytesseract
from PIL import Image
import tempfile
import os

# For file type detection
try:
    import magic
    HAS_MAGIC = True
except ImportError:
    HAS_MAGIC = False
    magic = None

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """Service for processing uploaded documents and extracting content"""
    
    def __init__(self, storage_root: str = "storage"):
        self.storage_root = Path(storage_root)
        self.markitdown = MarkItDown()  # Initialize MarkItDown processor
        self.supported_types = {
            'document': ['.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt', '.csv'],
            'image': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp', '.tiff'],
            'text': ['.txt', '.md', '.rtf'],
            'office': ['.doc', '.docx', '.odt'],
            'pdf': ['.pdf'],
            'spreadsheet': ['.csv', '.xls', '.xlsx']
        }
        
        # Create storage directories
        self._ensure_storage_directories()
    
    def _ensure_storage_directories(self):
        """Create storage directory structure"""
        directories = [
            self.storage_root / "documents",
            self.storage_root / "images", 
            self.storage_root / "extracted_text",
            self.storage_root / "thumbnails",
            self.storage_root / "temp"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def _get_file_hash(self, file_content: bytes) -> str:
        """Generate SHA-256 hash for file content"""
        return hashlib.sha256(file_content).hexdigest()
    
    def _detect_file_type(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """Detect file type using multiple methods"""
        # Get file extension
        file_extension = Path(filename).suffix.lower()
        
        # Use python-magic for MIME type detection if available
        if HAS_MAGIC:
            try:
                mime_type = magic.from_buffer(file_content, mime=True)
            except Exception as e:
                logger.warning(f"Failed to detect MIME type with magic: {e}")
                mime_type = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
        else:
            # Fallback to mimetypes module
            mime_type = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
        
        # Categorize file type
        category = self._categorize_file_type(file_extension, mime_type)
        
        return {
            'extension': file_extension,
            'mime_type': mime_type,
            'category': category,
            'size': len(file_content)
        }
    
    def _categorize_file_type(self, extension: str, mime_type: str) -> str:
        """Categorize file based on extension and MIME type"""
        # All document-like files should be categorized as 'document'
        if extension in ['.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt', '.csv']:
            return 'document'
        elif extension in self.supported_types['image']:
            return 'image'
        elif extension in self.supported_types['document']:
            return 'document'
        else:
            return 'unknown'
    
    def _generate_file_path(self, item_id: UUID, file_hash: str, extension: str, category: str) -> Path:
        """Generate organized file path"""
        # Create date-based subdirectory
        date_dir = datetime.now().strftime("%Y/%m")
        
        # Base directory based on category
        if category == 'image':
            base_dir = self.storage_root / "images" / date_dir
        else:
            base_dir = self.storage_root / "documents" / date_dir
        
        base_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate filename with hash to prevent duplicates
        filename = f"{item_id}_{file_hash[:8]}{extension}"
        return base_dir / filename
    
    async def process_file(self, file_content: bytes, filename: str, item_id: UUID) -> Dict[str, Any]:
        """Main file processing pipeline"""
        logger.info(f"Processing file: {filename} for item {item_id}")
        
        # Detect file type
        file_info = self._detect_file_type(file_content, filename)
        file_hash = self._get_file_hash(file_content)
        
        # Generate storage path
        file_path = self._generate_file_path(
            item_id, file_hash, file_info['extension'], file_info['category']
        )
        
        # Save file to storage
        await self._save_file(file_content, file_path)
        
        # Extract content based on file type
        extracted_content = await self._extract_content(file_content, file_info, filename)
        
        # Generate thumbnail for images
        thumbnail_path = None
        if file_info['category'] == 'image':
            thumbnail_path = await self._generate_thumbnail(file_content, item_id, file_hash)
        
        # Save extracted text
        text_file_path = None
        if extracted_content.get('text'):
            text_file_path = await self._save_extracted_text(
                extracted_content['text'], item_id, file_hash
            )
        
        return {
            'file_path': str(file_path),
            'file_hash': file_hash,
            'file_info': file_info,
            'extracted_content': extracted_content,
            'thumbnail_path': str(thumbnail_path) if thumbnail_path else None,
            'text_file_path': str(text_file_path) if text_file_path else None,
            'original_filename': filename,
            'processed_at': datetime.now().isoformat()
        }
    
    async def _save_file(self, file_content: bytes, file_path: Path):
        """Save file to storage"""
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(file_content)
        logger.info(f"Saved file to: {file_path}")
    
    async def _extract_content(self, file_content: bytes, file_info: Dict, filename: str) -> Dict[str, Any]:
        """Extract content from file based on type"""
        category = file_info['category']
        extension = file_info['extension']
        
        try:
            # Handle 'document' category by checking specific extensions
            if category == 'document':
                if extension == '.pdf':
                    return await self._extract_pdf_content(file_content)
                elif extension in ['.doc', '.docx', '.odt']:
                    return await self._extract_office_content(file_content, extension)
                elif extension == '.csv':
                    return await self._extract_csv_content(file_content)
                elif extension in ['.txt', '.rtf']:
                    return await self._extract_text_content(file_content)
                else:
                    return await self._extract_text_content(file_content)
            elif category == 'pdf':
                return await self._extract_pdf_content(file_content)
            elif category == 'office':
                return await self._extract_office_content(file_content, file_info['extension'])
            elif category == 'text':
                return await self._extract_text_content(file_content)
            elif category == 'image':
                return await self._extract_image_content(file_content)
            else:
                logger.warning(f"Unsupported file type: {category}")
                return {
                    'text': f"Unsupported file type: {filename}",
                    'pages': 0,
                    'word_count': 0,
                    'extraction_method': 'unsupported'
                }
        except Exception as e:
            logger.error(f"Content extraction failed for {filename}: {e}")
            return {
                'text': f"Failed to extract content from: {filename}",
                'pages': 0,
                'word_count': 0,
                'extraction_method': 'failed',
                'error': str(e)
            }
    
    async def _extract_pdf_content(self, file_content: bytes) -> Dict[str, Any]:
        """Extract text from PDF file using MarkItDown"""
        try:
            # Create temporary file for MarkItDown processing
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                temp_file.write(file_content)
                temp_file_path = temp_file.name
            
            try:
                # Process with MarkItDown
                result = self.markitdown.convert(temp_file_path)
                
                # Extract text content
                text_content = result.text_content if hasattr(result, 'text_content') else str(result)
                
                # Estimate page count from content length (rough approximation)
                estimated_pages = max(1, len(text_content) // 2000)  # ~2000 chars per page
                
                return {
                    'text': text_content,
                    'pages': estimated_pages,
                    'word_count': len(text_content.split()) if text_content else 0,
                    'extraction_method': 'markitdown',
                    'metadata': {
                        'source_type': 'pdf',
                        'content_type': getattr(result, 'content_type', 'application/pdf'),
                        'title': getattr(result, 'title', ''),
                        'preserves_formatting': True
                    }
                }
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_file_path)
                except OSError:
                    pass
                    
        except Exception as e:
            logger.error(f"MarkItDown PDF extraction failed: {e}")
            # Fallback to basic text extraction if MarkItDown fails
            return {
                'text': f"Failed to extract PDF content: {str(e)}",
                'pages': 0,
                'word_count': 0,
                'extraction_method': 'markitdown_failed',
                'error': str(e)
            }
    
    async def _extract_office_content(self, file_content: bytes, extension: str) -> Dict[str, Any]:
        """Extract text from Office documents using MarkItDown"""
        try:
            # Create temporary file for MarkItDown processing
            with tempfile.NamedTemporaryFile(suffix=extension, delete=False) as temp_file:
                temp_file.write(file_content)
                temp_file_path = temp_file.name
            
            try:
                # Process with MarkItDown
                result = self.markitdown.convert(temp_file_path)
                
                # Extract text content
                text_content = result.text_content if hasattr(result, 'text_content') else str(result)
                
                return {
                    'text': text_content,
                    'pages': 1,  # Office documents are typically single "page" from text perspective
                    'word_count': len(text_content.split()) if text_content else 0,
                    'extraction_method': 'markitdown',
                    'metadata': {
                        'source_type': 'office',
                        'format': extension,
                        'content_type': getattr(result, 'content_type', 'application/octet-stream'),
                        'title': getattr(result, 'title', ''),
                        'preserves_formatting': True
                    }
                }
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_file_path)
                except OSError:
                    pass
                    
        except Exception as e:
            logger.error(f"MarkItDown office extraction failed: {e}")
            # Fallback for .docx files
            if extension == '.docx':
                try:
                    doc = docx.Document(io.BytesIO(file_content))
                    text_content = []
                    
                    for paragraph in doc.paragraphs:
                        if paragraph.text.strip():
                            text_content.append(paragraph.text)
                    
                    full_text = '\n'.join(text_content)
                    
                    return {
                        'text': full_text,
                        'pages': len(doc.paragraphs),
                        'word_count': len(full_text.split()) if full_text else 0,
                        'extraction_method': 'python-docx_fallback',
                        'metadata': {
                            'paragraphs': len(doc.paragraphs),
                            'tables': len(doc.tables)
                        }
                    }
                except Exception as docx_error:
                    logger.error(f"Both MarkItDown and docx extraction failed: {docx_error}")
            
            return {
                'text': f"Failed to extract office content: {str(e)}",
                'pages': 1,
                'word_count': 0,
                'extraction_method': 'markitdown_failed',
                'error': str(e)
            }
    
    async def _extract_text_content(self, file_content: bytes) -> Dict[str, Any]:
        """Extract content from plain text files"""
        try:
            # Try UTF-8 first
            text = file_content.decode('utf-8')
        except UnicodeDecodeError:
            # Fallback to latin-1
            try:
                text = file_content.decode('latin-1')
            except UnicodeDecodeError:
                text = file_content.decode('utf-8', errors='replace')
        
        return {
            'text': text,
            'pages': 1,
            'word_count': len(text.split()) if text else 0,
            'extraction_method': 'text_decode',
            'metadata': {
                'encoding': 'utf-8',
                'characters': len(text)
            }
        }
    
    async def _extract_csv_content(self, file_content: bytes) -> Dict[str, Any]:
        """Extract content from CSV files"""
        try:
            # Decode CSV content
            text = file_content.decode('utf-8')
            
            # Parse CSV to create a readable text representation
            csv_reader = csv.reader(io.StringIO(text))
            rows = list(csv_reader)
            
            # Create a text representation of the CSV
            text_lines = []
            if rows:
                # Add headers if present
                headers = rows[0]
                text_lines.append("CSV Data with columns: " + ", ".join(headers))
                text_lines.append("")
                
                # Add data rows
                for row in rows[1:]:
                    text_lines.append(" | ".join(row))
            
            extracted_text = "\n".join(text_lines)
            
            return {
                'text': extracted_text,
                'pages': 1,
                'word_count': len(extracted_text.split()) if extracted_text else 0,
                'extraction_method': 'csv_parse',
                'metadata': {
                    'row_count': len(rows),
                    'column_count': len(rows[0]) if rows else 0,
                    'encoding': 'utf-8'
                }
            }
        except Exception as e:
            logger.error(f"CSV extraction failed: {e}")
            # Fallback to plain text extraction
            return await self._extract_text_content(file_content)
    
    async def _extract_image_content(self, file_content: bytes) -> Dict[str, Any]:
        """Extract text from images using MarkItDown with Tesseract fallback"""
        # Try MarkItDown first for better image handling
        try:
            # Detect image format
            image_format = self._detect_image_format(file_content)
            
            # Create temporary file for MarkItDown processing
            with tempfile.NamedTemporaryFile(suffix=image_format, delete=False) as temp_file:
                temp_file.write(file_content)
                temp_file_path = temp_file.name
            
            try:
                # Process with MarkItDown
                result = self.markitdown.convert(temp_file_path)
                
                # Extract text content
                text_content = result.text_content if hasattr(result, 'text_content') else str(result)
                
                # Get image metadata
                image = Image.open(io.BytesIO(file_content))
                
                return {
                    'text': text_content,
                    'pages': 1,
                    'word_count': len(text_content.split()) if text_content else 0,
                    'extraction_method': 'markitdown_ocr',
                    'metadata': {
                        'image_size': image.size,
                        'image_mode': image.mode,
                        'has_text': bool(text_content.strip()),
                        'source_type': 'image',
                        'format': image_format
                    }
                }
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_file_path)
                except OSError:
                    pass
                    
        except Exception as markitdown_error:
            logger.warning(f"MarkItDown image extraction failed, falling back to Tesseract: {markitdown_error}")
            
            # Fallback to Tesseract OCR
            try:
                # Open image
                image = Image.open(io.BytesIO(file_content))
                
                # Convert to RGB if necessary
                if image.mode != 'RGB':
                    image = image.convert('RGB')
                
                # Perform OCR
                extracted_text = pytesseract.image_to_string(image)
                
                return {
                    'text': extracted_text,
                    'pages': 1,
                    'word_count': len(extracted_text.split()) if extracted_text else 0,
                    'extraction_method': 'tesseract_ocr_fallback',
                    'metadata': {
                        'image_size': image.size,
                        'image_mode': image.mode,
                        'has_text': bool(extracted_text.strip()),
                        'markitdown_error': str(markitdown_error)
                    }
                }
            except Exception as e:
                logger.error(f"Both MarkItDown and Tesseract OCR failed: {e}")
                return {
                    'text': "Image content (OCR not available)",
                    'pages': 1,
                    'word_count': 0,
                    'extraction_method': 'ocr_failed',
                    'error': str(e)
                }
    
    def _detect_image_format(self, file_content: bytes) -> str:
        """Detect image format from file content"""
        try:
            image = Image.open(io.BytesIO(file_content))
            format_map = {
                'JPEG': '.jpg',
                'PNG': '.png',
                'GIF': '.gif',
                'BMP': '.bmp',
                'TIFF': '.tiff',
                'WEBP': '.webp'
            }
            return format_map.get(image.format, '.jpg')
        except Exception:
            return '.jpg'  # Default fallback
    
    async def _generate_thumbnail(self, file_content: bytes, item_id: UUID, file_hash: str) -> Optional[Path]:
        """Generate thumbnail for image files"""
        try:
            image = Image.open(io.BytesIO(file_content))
            
            # Create thumbnail
            thumbnail_size = (300, 300)
            image.thumbnail(thumbnail_size, Image.Resampling.LANCZOS)
            
            # Save thumbnail
            thumbnail_dir = self.storage_root / "thumbnails" / datetime.now().strftime("%Y/%m")
            thumbnail_dir.mkdir(parents=True, exist_ok=True)
            
            thumbnail_path = thumbnail_dir / f"{item_id}_{file_hash[:8]}_thumb.jpg"
            image.save(thumbnail_path, 'JPEG', quality=85)
            
            return thumbnail_path
        except Exception as e:
            logger.error(f"Thumbnail generation failed: {e}")
            return None
    
    async def _save_extracted_text(self, text: str, item_id: UUID, file_hash: str) -> Path:
        """Save extracted text to file"""
        text_dir = self.storage_root / "extracted_text" / datetime.now().strftime("%Y/%m")
        text_dir.mkdir(parents=True, exist_ok=True)
        
        text_file_path = text_dir / f"{item_id}_{file_hash[:8]}.txt"
        
        async with aiofiles.open(text_file_path, 'w', encoding='utf-8') as f:
            await f.write(text)
        
        return text_file_path
    
    async def get_file_content(self, file_path: str) -> Optional[bytes]:
        """Retrieve file content from storage"""
        try:
            async with aiofiles.open(file_path, 'rb') as f:
                return await f.read()
        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
            return None
        except Exception as e:
            logger.error(f"Failed to read file {file_path}: {e}")
            return None
    
    async def delete_file(self, file_path: str) -> bool:
        """Delete file from storage"""
        try:
            await aiofiles.os.remove(file_path)
            logger.info(f"Deleted file: {file_path}")
            return True
        except FileNotFoundError:
            logger.warning(f"File not found for deletion: {file_path}")
            return False
        except Exception as e:
            logger.error(f"Failed to delete file {file_path}: {e}")
            return False
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage usage statistics"""
        stats = {
            'total_files': 0,
            'total_size_bytes': 0,
            'by_category': {}
        }
        
        for category_dir in ['documents', 'images', 'thumbnails', 'extracted_text']:
            category_path = self.storage_root / category_dir
            if category_path.exists():
                category_stats = self._get_directory_stats(category_path)
                stats['by_category'][category_dir] = category_stats
                stats['total_files'] += category_stats['files']
                stats['total_size_bytes'] += category_stats['size_bytes']
        
        return stats
    
    def _get_directory_stats(self, directory: Path) -> Dict[str, Any]:
        """Get statistics for a directory"""
        total_size = 0
        file_count = 0
        
        for file_path in directory.rglob('*'):
            if file_path.is_file():
                file_count += 1
                total_size += file_path.stat().st_size
        
        return {
            'files': file_count,
            'size_bytes': total_size,
            'size_mb': round(total_size / (1024 * 1024), 2)
        }