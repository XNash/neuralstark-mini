import logging
from pathlib import Path
from typing import List
import json
import csv
from io import StringIO

# PDF processing
import pdfplumber
from pdf2image import convert_from_path
import pytesseract
from PIL import Image

# Word processing
from docx import Document as DocxDocument

# Excel processing
from openpyxl import load_workbook

# ODT processing
from odf import text as odf_text, teletype
from odf.opendocument import load as odf_load

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Process various document formats and extract text"""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def process_document(self, file_path: str) -> List[str]:
        """Process a document and return text chunks"""
        path = Path(file_path)
        extension = path.suffix.lower()
        
        try:
            if extension == '.pdf':
                text = self._process_pdf(file_path)
            elif extension in ['.docx', '.doc']:
                text = self._process_word(file_path)
            elif extension in ['.xlsx', '.xls']:
                text = self._process_excel(file_path)
            elif extension == '.odt':
                text = self._process_odt(file_path)
            elif extension in ['.txt', '.md']:
                text = self._process_text(file_path)
            elif extension == '.json':
                text = self._process_json(file_path)
            elif extension == '.csv':
                text = self._process_csv(file_path)
            else:
                logger.warning(f"Unsupported file type: {extension}")
                return []
            
            # Split into chunks
            chunks = self._split_into_chunks(text)
            return chunks
        
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            return []
    
    def _process_pdf(self, file_path: str) -> str:
        """Extract text from PDF with OCR fallback"""
        text = ""
        
        try:
            # Try extracting text directly
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            
            # If no text extracted, use OCR
            if not text.strip():
                logger.info(f"No text found in PDF, using OCR: {file_path}")
                images = convert_from_path(file_path)
                for i, image in enumerate(images):
                    ocr_text = pytesseract.image_to_string(image, lang='eng+fra')
                    text += f"\n--- Page {i+1} ---\n{ocr_text}"
        
        except Exception as e:
            logger.error(f"Error processing PDF {file_path}: {e}")
        
        return text
    
    def _process_word(self, file_path: str) -> str:
        """Extract text from Word document"""
        text = ""
        
        try:
            doc = DocxDocument(file_path)
            
            # Extract text from paragraphs
            for para in doc.paragraphs:
                text += para.text + "\n"
            
            # Extract text from tables
            for table in doc.tables:
                for row in table.rows:
                    row_text = " | ".join([cell.text for cell in row.cells])
                    text += row_text + "\n"
            
            # Check for images and perform OCR if needed
            # Note: This is a basic implementation
            for rel in doc.part.rels.values():
                if "image" in rel.target_ref:
                    logger.info(f"Word document contains images: {file_path}")
        
        except Exception as e:
            logger.error(f"Error processing Word document {file_path}: {e}")
        
        return text
    
    def _process_excel(self, file_path: str) -> str:
        """Extract text from Excel file"""
        text = ""
        
        try:
            wb = load_workbook(file_path, read_only=True, data_only=True)
            
            for sheet_name in wb.sheetnames:
                sheet = wb[sheet_name]
                text += f"\n--- Sheet: {sheet_name} ---\n"
                
                for row in sheet.iter_rows(values_only=True):
                    row_text = " | ".join([str(cell) if cell is not None else "" for cell in row])
                    if row_text.strip():
                        text += row_text + "\n"
        
        except Exception as e:
            logger.error(f"Error processing Excel file {file_path}: {e}")
        
        return text
    
    def _process_odt(self, file_path: str) -> str:
        """Extract text from ODT file"""
        text = ""
        
        try:
            doc = odf_load(file_path)
            all_paras = doc.getElementsByType(odf_text.P)
            
            for para in all_paras:
                para_text = teletype.extractText(para)
                text += para_text + "\n"
        
        except Exception as e:
            logger.error(f"Error processing ODT file {file_path}: {e}")
        
        return text
    
    def _process_text(self, file_path: str) -> str:
        """Extract text from plain text or markdown file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error processing text file {file_path}: {e}")
            return ""
    
    def _process_json(self, file_path: str) -> str:
        """Extract text from JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return json.dumps(data, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error processing JSON file {file_path}: {e}")
            return ""
    
    def _process_csv(self, file_path: str) -> str:
        """Extract text from CSV file"""
        text = ""
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                csv_reader = csv.reader(f)
                for row in csv_reader:
                    text += " | ".join(row) + "\n"
        except Exception as e:
            logger.error(f"Error processing CSV file {file_path}: {e}")
        
        return text
    
    def _split_into_chunks(self, text: str) -> List[str]:
        """Split text into overlapping chunks"""
        if not text.strip():
            return []
        
        chunks = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            end = start + self.chunk_size
            
            # If not at the end, try to break at a sentence or word boundary
            if end < text_length:
                # Look for sentence boundary
                for delimiter in ['. ', '.\n', '! ', '!\n', '? ', '?\n']:
                    last_delim = text.rfind(delimiter, start, end)
                    if last_delim != -1:
                        end = last_delim + len(delimiter)
                        break
                else:
                    # Look for word boundary
                    last_space = text.rfind(' ', start, end)
                    if last_space != -1:
                        end = last_space
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end - self.chunk_overlap if end < text_length else text_length
        
        return chunks