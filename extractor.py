"""
PDF Extraction Module using Qwen3-VL-8B-Instruct
Extracts date, amount from PDF receipts/invoices
"""

import re
import torch
from pathlib import Path
from PIL import Image
from pdf2image import convert_from_path
from transformers import AutoProcessor, BitsAndBytesConfig
from qwen_vl_utils import process_vision_info


class PDFExtractor:
    """Extracts structured data from PDF receipts/invoices using Qwen3-VL"""
    
    def __init__(self):
        self.model = None
        self.processor = None
        
    def load_model(self):
        """Load Qwen3-VL-4B-Instruct in fp16"""
        if self.model is not None:
            return
            
        print("Loading Qwen3-VL-4B-Instruct model in fp16...")
        
        model_name = "Qwen/Qwen3-VL-4B-Instruct"
        
        # Use correct class for Qwen3-VL
        from transformers import Qwen3VLForConditionalGeneration
        
        self.model = Qwen3VLForConditionalGeneration.from_pretrained(
            model_name,
            device_map="cuda:0",
            torch_dtype=torch.float16,
            trust_remote_code=True
        )
        
        self.processor = AutoProcessor.from_pretrained(
            model_name,
            trust_remote_code=True
        )
        
        print("Model loaded successfully!")
        
    def pdf_to_images(self, pdf_path: str) -> list[Image.Image]:
        """Convert PDF pages to PIL Images"""
        images = convert_from_path(pdf_path, dpi=200)
        return images
    
    def extract_from_image(self, image: Image.Image) -> dict:
        """Extract date and amount from image using simple list format"""
        
        # Very explicit prompt asking for numbered list
        prompt = """You are analyzing a receipt or invoice. Look at this image and find:

1. DOCUMENT DATE - When was this receipt/invoice created? Look for dates near the top, header, or labeled as "Date", "Invoice Date", "Transaction Date", etc.

2. TOTAL AMOUNT - What is the final total to pay? Look for "Total", "Grand Total", "Amount Due", "Sum", or the largest/bottom number.

Reply with EXACTLY this format (fill in the blanks):
---
1. DATE: ___
2. TOTAL: ___
---

Examples of good answers:
- DATE: 2024-01-15
- DATE: 15/01/2024  
- DATE: January 15, 2024
- TOTAL: €125.50
- TOTAL: $99.99
- TOTAL: 1,234.56 EUR

If you truly cannot find something, write "NOT_FOUND" but try hard to find it first."""

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": image},
                    {"type": "text", "text": prompt}
                ]
            }
        ]
        
        text = self.processor.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        
        image_inputs, video_inputs = process_vision_info(messages)
        
        inputs = self.processor(
            text=[text],
            images=image_inputs,
            videos=video_inputs,
            padding=True,
            return_tensors="pt"
        ).to("cuda:0")
        
        # Generate - removed invalid params for this model
        with torch.no_grad():
            generated_ids = self.model.generate(
                **inputs,
                max_new_tokens=256
            )
        
        generated_ids_trimmed = [
            out_ids[len(in_ids):] 
            for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
        ]
        
        output_text = self.processor.batch_decode(
            generated_ids_trimmed,
            skip_special_tokens=True,
            clean_up_tokenization_spaces=False
        )[0]
        
        print(f"=== MODEL OUTPUT ===\n{output_text}\n====================")
        return self._parse_output(output_text)
    
    def _parse_output(self, text: str) -> dict:
        """Parse model output - look for date and total in various formats"""
        result = {"date": "N/A", "amount": "N/A"}
        
        # Try to find DATE
        date_patterns = [
            r'(?:1\.\s*)?DATE[:\s]+([^\n]+)',
            r'date[:\s]+([0-9]{4}[-/][0-9]{2}[-/][0-9]{2})',
            r'date[:\s]+([0-9]{1,2}[-/][0-9]{1,2}[-/][0-9]{2,4})',
            r'(\d{4}-\d{2}-\d{2})',
            r'(\d{1,2}/\d{1,2}/\d{2,4})',
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                val = match.group(1).strip()
                val = re.sub(r'[\*\[\]_]', '', val).strip()
                if val.lower() not in ['not_found', 'n/a', 'na', '___', '']:
                    result["date"] = val
                    break
        
        # Try to find TOTAL/AMOUNT
        amount_patterns = [
            r'(?:2\.\s*)?TOTAL[:\s]+([^\n]+)',
            r'(?:2\.\s*)?AMOUNT[:\s]+([^\n]+)',
            r'TOTAL[:\s]*([€$£¥]?\s*[\d,]+[.,]\d{2})',
            r'([€$£¥]\s*[\d,]+[.,]\d{2})',
            r'([\d,]+[.,]\d{2}\s*(?:EUR|USD|GBP|€|\$|£))',
        ]
        
        for pattern in amount_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                val = match.group(1).strip()
                val = re.sub(r'[\*\[\]_]', '', val).strip()
                if val.lower() not in ['not_found', 'n/a', 'na', '___', '']:
                    result["amount"] = val
                    break
                
        return result
    
    def extract_from_pdf(self, pdf_path: str) -> dict:
        """Extract date and amount from a PDF file."""
        self.load_model()
        
        pdf_path = Path(pdf_path)
        filename = pdf_path.name
        
        try:
            images = self.pdf_to_images(str(pdf_path))
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to convert PDF: {str(e)}",
                "data": None
            }
        
        best_result = {"date": "N/A", "amount": "N/A"}
        
        for i, image in enumerate(images):
            print(f"Processing page {i + 1}/{len(images)}...")
            
            try:
                result = self.extract_from_image(image)
                
                if result["date"] != "N/A" and best_result["date"] == "N/A":
                    best_result["date"] = result["date"]
                if result["amount"] != "N/A" and best_result["amount"] == "N/A":
                    best_result["amount"] = result["amount"]
                
                if best_result["date"] != "N/A" and best_result["amount"] != "N/A":
                    break
                    
            except Exception as e:
                print(f"Error processing page {i + 1}: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        return {
            "success": True,
            "data": {
                "date": best_result["date"],
                "docname": filename,
                "amount": best_result["amount"]
            }
        }


_extractor = None

def get_extractor() -> PDFExtractor:
    global _extractor
    if _extractor is None:
        _extractor = PDFExtractor()
    return _extractor
