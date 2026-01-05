import fitz  # PyMuPDF
import pytesseract
from pdf2image import convert_from_path
from pathlib import Path
from typing import Optional
import tempfile
import os


class PDFHandler:
    def __init__(self, min_text_threshold: int = 50):
        """
        Initialize PDF handler.
        
        Args:
            min_text_threshold: Minimum characters to consider text extraction successful
        """
        self.min_text_threshold = min_text_threshold
    
    def extract_text_pymupdf(self, pdf_path: str) -> str:
        """
        Extract text from PDF using PyMuPDF.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            str: Extracted text
        """
        text = ""
        try:
            doc = fitz.open(pdf_path)
            for page in doc:
                text += page.get_text()
            doc.close()
        except Exception as e:
            print(f"PyMuPDF extraction error: {e}")
        return text.strip()
    
    def extract_text_ocr(self, pdf_path: str) -> str:
        """
        Extract text from PDF using OCR (pytesseract).
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            str: Extracted text
        """
        text = ""
        try:
            # Convert PDF to images
            images = convert_from_path(pdf_path)
            
            # OCR each page
            for i, image in enumerate(images):
                page_text = pytesseract.image_to_string(image)
                text += f"\n--- Page {i+1} ---\n{page_text}"
        except Exception as e:
            print(f"OCR extraction error: {e}")
        return text.strip()
    
    def extract_text(self, pdf_path: str) -> str:
        """
        Extract text from PDF with fallback strategy.
        First tries PyMuPDF, falls back to OCR if insufficient text.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            str: Extracted text
        """
        # Try PyMuPDF first
        text = self.extract_text_pymupdf(pdf_path)
        
        # If insufficient text, fallback to OCR
        if len(text) < self.min_text_threshold:
            print(f"PyMuPDF extracted only {len(text)} chars. Falling back to OCR...")
            text = self.extract_text_ocr(pdf_path)
        
        return text


# Singleton instance
pdf_handler = PDFHandler()
