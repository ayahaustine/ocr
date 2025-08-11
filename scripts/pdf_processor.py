import os
import logging
from PyPDF2 import PdfReader
from pdf2image import convert_from_path
import pytesseract
from config import settings

def get_pdf_files():
    """
    Return list of PDF file paths in the input folder.
    """
    files = [f for f in os.listdir(settings.INPUT_FOLDER) if f.lower().endswith(".pdf")]
    return [os.path.join(settings.INPUT_FOLDER, f) for f in files]

def validate_pages(page_spec, total_pages):
    """
    Parse page range like '3', '5-7', or '2,4,6-8' into a list.
    """
    pages = set()
    parts = page_spec.split(",")
    for part in parts:
        if "-" in part:
            start, end = part.split("-")
            start, end = int(start), int(end)
            if start < 1 or end > total_pages or start > end:
                raise ValueError(f"Invalid range: {part}")
            pages.update(range(start, end + 1))
        else:
            p = int(part)
            if p < 1 or p > total_pages:
                raise ValueError(f"Invalid page: {p}")
            pages.add(p)
    return sorted(pages)

def pdf_to_images(pdf_path, pages):
    """
    Convert given pages of a PDF to images.
    """
    images = convert_from_path(
        pdf_path,
        first_page=min(pages),
        last_page=max(pages),
        poppler_path=settings.POPPLER_PATH
    )
    # Adjust indexing if pages are non-contiguous
    images_dict = dict(zip(range(min(pages), max(pages)+1), images))
    return [images_dict[p] for p in pages if p in images_dict]

def ocr_image(image):
    """
    Run OCR on an image.
    """
    pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD
    return pytesseract.image_to_string(image)

def extract_text_from_pdf(pdf_path, page_spec):
    """
    OCR specified pages from a PDF.
    """
    reader = PdfReader(pdf_path)
    total_pages = len(reader.pages)
    pages = validate_pages(page_spec, total_pages)
    logging.info(f"Processing {os.path.basename(pdf_path)}, pages {pages}")

    images = pdf_to_images(pdf_path, pages)
    results = []
    for idx, page_num in enumerate(pages):
        text = ocr_image(images[idx])
        results.append((page_num, text))
    return results
