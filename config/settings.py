import os

# Base directory of project
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# folders
INPUT_FOLDER = os.path.join(BASE_DIR, "input_pdfs")
OUTPUT_FOLDER = os.path.join(BASE_DIR, "output_csv")
LOG_FOLDER = os.path.join(BASE_DIR, "logs")

# OCR settings
TESSERACT_CMD = "tesseract"
POPPLER_PATH = None