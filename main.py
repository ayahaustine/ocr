import os
import logging
import pandas as pd
from config import settings
from scripts import pdf_processor, table_parser

# Logging setup
os.makedirs(settings.LOG_FOLDER, exist_ok=True)
logging.basicConfig(
    filename=os.path.join(settings.LOG_FOLDER, "run.log"),
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def main():
    os.makedirs(settings.OUTPUT_FOLDER, exist_ok=True)

    # User input for pages
    page_spec = input("Enter pages to extract (e.g., '3', '5-7', '2,4,6-8'): ").strip()
    
    pdf_files = pdf_processor.get_pdf_files()
    if not pdf_files:
        logging.error("No PDF files found in input_pdfs/")
        print("No PDF files found.")
        return
    
    for pdf_path in pdf_files:
        try:
            ocr_results = pdf_processor.extract_text_from_pdf(pdf_path, page_spec)
            tables = []
            for page_num, text in ocr_results:
                df = table_parser.text_to_table(text)
                if not df.empty:
                    df.insert(0, "Page", page_num)
                    df.insert(0, "PDF_File", os.path.basename(pdf_path))
                    tables.append(df)
            if tables:
                final_df = pd.concat(tables, ignore_index=True)
                output_file = os.path.join(
                    settings.OUTPUT_FOLDER,
                    os.path.splitext(os.path.basename(pdf_path))[0] + ".csv"
                )
                final_df.to_csv(output_file, index=False)
                logging.info(f"Saved CSV: {output_file}")
                print(f"Processed {os.path.basename(pdf_path)} → {output_file}")
            else:
                logging.warning(f"No tables found in {os.path.basename(pdf_path)}")
        except Exception as e:
            logging.error(f"Error processing {pdf_path}: {e}")
            print(f"Error processing {os.path.basename(pdf_path)}: {e}")

if __name__ == "__main__":
    main()