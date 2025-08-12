# PDF OCR Table Extractor

A Python tool that processes PDFs, extracts specified pages, performs OCR, converts text into structured tables, and saves them as CSV files. Supports batch processing of all PDFs in a folder with parallel execution.

## Features

- Extracts single pages or page ranges from PDFs
- OCR via Tesseract
- Converts detected tables into CSV format
- Handles multi-line table cells
- Processes all PDFs in `input_pdfs/` in parallel
- Saves raw text and structured CSV outputs
- Graceful error handling and logging

## Setup

1. Install dependencies:
   pip install -r requirements.txt

2. Install Tesseract:

   - Linux: sudo apt install tesseract-ocr
   - Mac: brew install tesseract

3. Install Poppler:

   - Linux: sudo apt install poppler-utils
   - Mac: brew install poppler

4. Place PDFs in `input_pdfs/`.

5. Run:
   python main.py

6. Outputs are saved in `output_csv/`.
