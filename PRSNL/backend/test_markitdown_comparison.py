"""
Comparison test between MarkItDown and current image processing implementation.

This script demonstrates the differences between:
1. Current implementation (PyPDF2 + Tesseract OCR)
2. MarkItDown (Microsoft's unified document processing)
"""

import asyncio
import io
import json
import os
import tempfile
from pathlib import Path
from typing import Dict, Any

# Current implementation imports
try:
    import PyPDF2
    import pytesseract
    from PIL import Image
    CURRENT_AVAILABLE = True
except ImportError as e:
    print(f"Current implementation not available: {e}")
    CURRENT_AVAILABLE = False

# MarkItDown imports
try:
    from markitdown import MarkItDown
    MARKITDOWN_AVAILABLE = True
except ImportError as e:
    print(f"MarkItDown not available: {e}")
    MARKITDOWN_AVAILABLE = False


class DocumentProcessorComparison:
    """Compare current vs MarkItDown document processing."""
    
    def __init__(self):
        self.markitdown = MarkItDown() if MARKITDOWN_AVAILABLE else None
        
    def current_extract_pdf_content(self, file_content: bytes) -> Dict[str, Any]:
        """Current PyPDF2 implementation."""
        if not CURRENT_AVAILABLE:
            return {"error": "Current implementation not available"}
            
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
            
            text_content = []
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text.strip():
                        text_content.append(page_text)
                except Exception as e:
                    print(f"Failed to extract text from page {page_num}: {e}")
            
            full_text = '\n'.join(text_content)
            
            return {
                'text': full_text,
                'pages': len(pdf_reader.pages),
                'word_count': len(full_text.split()) if full_text else 0,
                'extraction_method': 'pypdf2',
                'metadata': {
                    'pages_with_text': len(text_content),
                    'total_pages': len(pdf_reader.pages)
                }
            }
        except Exception as e:
            return {
                'error': f"PyPDF2 extraction failed: {e}",
                'extraction_method': 'pypdf2'
            }
    
    def current_extract_image_content(self, file_content: bytes) -> Dict[str, Any]:
        """Current Tesseract OCR implementation."""
        if not CURRENT_AVAILABLE:
            return {"error": "Current implementation not available"}
            
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
                'extraction_method': 'tesseract_ocr',
                'metadata': {
                    'image_size': image.size,
                    'image_mode': image.mode,
                    'has_text': bool(extracted_text.strip())
                }
            }
        except Exception as e:
            return {
                'error': f"OCR extraction failed: {e}",
                'extraction_method': 'tesseract_ocr'
            }
    
    def markitdown_extract_content(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """MarkItDown implementation."""
        if not MARKITDOWN_AVAILABLE:
            return {"error": "MarkItDown not available"}
            
        try:
            # Create temporary file for MarkItDown
            with tempfile.NamedTemporaryFile(suffix=Path(filename).suffix, delete=False) as temp_file:
                temp_file.write(file_content)
                temp_file_path = temp_file.name
            
            try:
                # Process with MarkItDown
                result = self.markitdown.convert(temp_file_path)
                
                # Extract metadata
                metadata = {
                    'source_file': filename,
                    'content_type': getattr(result, 'content_type', 'unknown'),
                    'title': getattr(result, 'title', ''),
                }
                
                # Get text content
                text_content = result.text_content if hasattr(result, 'text_content') else str(result)
                
                return {
                    'text': text_content,
                    'word_count': len(text_content.split()) if text_content else 0,
                    'extraction_method': 'markitdown',
                    'metadata': metadata,
                    'markitdown_features': {
                        'preserves_formatting': True,
                        'handles_images': True,
                        'supports_multiple_formats': True,
                        'unified_api': True
                    }
                }
            finally:
                # Clean up temp file
                os.unlink(temp_file_path)
                
        except Exception as e:
            return {
                'error': f"MarkItDown extraction failed: {e}",
                'extraction_method': 'markitdown'
            }
    
    async def compare_pdf_processing(self, pdf_content: bytes, filename: str) -> Dict[str, Any]:
        """Compare PDF processing between current and MarkItDown."""
        
        print(f"Comparing PDF processing for: {filename}")
        
        # Current implementation
        current_result = self.current_extract_pdf_content(pdf_content)
        
        # MarkItDown implementation
        markitdown_result = self.markitdown_extract_content(pdf_content, filename)
        
        return {
            'filename': filename,
            'file_size': len(pdf_content),
            'current_implementation': current_result,
            'markitdown_implementation': markitdown_result,
            'comparison': {
                'current_word_count': current_result.get('word_count', 0),
                'markitdown_word_count': markitdown_result.get('word_count', 0),
                'current_has_error': 'error' in current_result,
                'markitdown_has_error': 'error' in markitdown_result,
                'text_length_difference': abs(
                    len(current_result.get('text', '')) - 
                    len(markitdown_result.get('text', ''))
                )
            }
        }
    
    async def compare_image_processing(self, image_content: bytes, filename: str) -> Dict[str, Any]:
        """Compare image processing between current and MarkItDown."""
        
        print(f"Comparing image processing for: {filename}")
        
        # Current implementation
        current_result = self.current_extract_image_content(image_content)
        
        # MarkItDown implementation
        markitdown_result = self.markitdown_extract_content(image_content, filename)
        
        return {
            'filename': filename,
            'file_size': len(image_content),
            'current_implementation': current_result,
            'markitdown_implementation': markitdown_result,
            'comparison': {
                'current_word_count': current_result.get('word_count', 0),
                'markitdown_word_count': markitdown_result.get('word_count', 0),
                'current_has_error': 'error' in current_result,
                'markitdown_has_error': 'error' in markitdown_result,
                'text_length_difference': abs(
                    len(current_result.get('text', '')) - 
                    len(markitdown_result.get('text', ''))
                )
            }
        }
    
    def feature_comparison(self) -> Dict[str, Any]:
        """Compare features between implementations."""
        
        return {
            'current_implementation': {
                'pdf_support': CURRENT_AVAILABLE,
                'image_ocr': CURRENT_AVAILABLE,
                'dependencies': ['PyPDF2', 'pytesseract', 'PIL'],
                'pros': [
                    'Separate specialized libraries',
                    'Fine-grained control',
                    'Well-established libraries'
                ],
                'cons': [
                    'Multiple dependencies',
                    'Inconsistent APIs',
                    'Manual integration needed',
                    'Limited format support'
                ]
            },
            'markitdown_implementation': {
                'pdf_support': MARKITDOWN_AVAILABLE,
                'image_ocr': MARKITDOWN_AVAILABLE,
                'dependencies': ['markitdown'],
                'pros': [
                    'Unified API for all formats',
                    'Microsoft-maintained',
                    'Handles complex documents',
                    'Preserves formatting better',
                    'Supports more formats out of box'
                ],
                'cons': [
                    'Newer library (less tested)',
                    'Single dependency risk',
                    'Less fine-grained control'
                ]
            },
            'recommendation': {
                'use_markitdown_for': [
                    'Complex documents with mixed content',
                    'Multiple file formats',
                    'Rapid prototyping',
                    'Simplified maintenance'
                ],
                'use_current_for': [
                    'Fine-grained control needed',
                    'Specific OCR customization',
                    'Legacy system integration'
                ]
            }
        }


async def main():
    """Run the comparison demonstration."""
    
    print("=== Document Processing Comparison: Current vs MarkItDown ===\n")
    
    comparison = DocumentProcessorComparison()
    
    # Feature comparison
    print("1. Feature Comparison:")
    features = comparison.feature_comparison()
    print(json.dumps(features, indent=2))
    
    print("\n" + "="*60 + "\n")
    
    # Test with sample data if available
    print("2. Implementation Status:")
    print(f"   Current (PyPDF2 + Tesseract): {'Available' if CURRENT_AVAILABLE else 'Not Available'}")
    print(f"   MarkItDown: {'Available' if MARKITDOWN_AVAILABLE else 'Not Available'}")
    
    if MARKITDOWN_AVAILABLE:
        print("\n3. MarkItDown Capabilities:")
        md = MarkItDown()
        print(f"   Supported formats: PDF, DOCX, PPTX, images, HTML, and more")
        print(f"   Unified API: Single convert() method")
        print(f"   Output format: Markdown (preserves structure)")
    
    print("\n" + "="*60 + "\n")
    
    print("4. Migration Recommendations:")
    print("   • Replace PyPDF2 with MarkItDown for PDF processing")
    print("   • Keep Tesseract as fallback for specialized OCR needs")
    print("   • Use MarkItDown for document type detection")
    print("   • Implement gradual migration with feature flags")
    
    print("\n5. Implementation Changes Needed:")
    print("   • Update document_processor.py to use MarkItDown")
    print("   • Add MarkItDown to requirements.txt (✓ Done)")
    print("   • Remove PyPDF2 from requirements.txt (✓ Done)")
    print("   • Update extraction methods to use unified API")
    print("   • Add error handling for format detection")


if __name__ == "__main__":
    asyncio.run(main())