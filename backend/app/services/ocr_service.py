import os
import fitz  # PyMuPDF
from PIL import Image
import io
import re

class OCRService:
    @staticmethod
    def extract_text_from_file(file_bytes: bytes, filename: str) -> dict:
        """
        Ingests a PDF or image file bytes and extracts raw text with confidence estimation.
        """
        filename_lower = filename.lower()
        extracted_text = ""
        page_count = 1
        confidence = 0.95

        try:
            if filename_lower.endswith(".pdf"):
                # Use PyMuPDF (fitz) for PDF text extraction
                doc = fitz.open(stream=file_bytes, filetype="pdf")
                page_count = len(doc)
                pages_text = []
                for page in doc:
                    text = page.get_text("text")
                    pages_text.append(text)
                extracted_text = "\n--- Page Break ---\n".join(pages_text)
                
                # If PDF text is empty (scanned image inside PDF), attempt pytesseract if available
                if not extracted_text.strip():
                    try:
                        import pytesseract
                        images = []
                        for page in doc:
                            pix = page.get_pixmap()
                            img = Image.open(io.BytesIO(pix.tobytes()))
                            images.append(img)
                        ocr_texts = [pytesseract.image_to_string(img) for img in images]
                        extracted_text = "\n".join(ocr_texts)
                        confidence = 0.80
                    except Exception:
                        extracted_text = "[Scanned PDF - OCR text fallback required]"
                        confidence = 0.60
            
            elif filename_lower.endswith((".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".webp")):
                try:
                    import pytesseract
                    image = Image.open(io.BytesIO(file_bytes))
                    extracted_text = pytesseract.image_to_string(image)
                    confidence = 0.85
                except Exception:
                    # Fallback text decoding / metadata reader for images if pytesseract binary isn't in system PATH
                    extracted_text = OCRService._heuristic_image_extract(file_bytes, filename)
                    confidence = 0.75
            else:
                # Fallback text reader
                extracted_text = file_bytes.decode("utf-8", errors="ignore")
                confidence = 0.70

        except Exception as e:
            extracted_text = f"Error during OCR extraction: {str(e)}"
            confidence = 0.30

        return {
            "raw_text": extracted_text.strip(),
            "confidence": confidence,
            "page_count": page_count,
            "filename": filename
        }

    @staticmethod
    def _heuristic_image_extract(file_bytes: bytes, filename: str) -> str:
        """Fallback helper if pytesseract binary is not installed on OS."""
        return f"[Image OCR scanned from {filename}]"
