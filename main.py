import os
import logging
from concurrent.futures import ProcessPoolExecutor, as_completed
from config import settings
from scripts import pdf_processor, table_parser, utils

def setup_folders():
    for folder in [settings.OUTPUT_CSV_FOLDER, settings.OUTPUT_TEXT_FOLDER, settings.LOG_FOLDER]:
        os.makedirs(folder, exist_ok=True)

def process_single_pdf(pdf_path, page_spec):
    try:
        total_pages = pdf_processor.get_pdf_page_count(pdf_path)
        pages = pdf_processor.parse_page_spec(page_spec, total_pages)

        images = pdf_processor.pdf_to_images(pdf_path, pages)
        tables = []
        for page_num in pages:
            img = images.get(page_num)
            if img is None:
                logging.warning(f"Page {page_num} not found in image conversion for {pdf_path}")
                continue

            df, raw_text = table_parser.parse_image_table(img)

            # save raw text for debugging
            text_file = os.path.join(
                settings.OUTPUT_TEXT_FOLDER,
                f"{os.path.splitext(os.path.basename(pdf_path))[0]}_page{page_num}.txt"
            )
            with open(text_file, "w", encoding="utf-8") as f:
                f.write(raw_text)

            if not df.empty:
                df.insert(0, "Page", page_num)
                df.insert(0, "PDF_File", os.path.basename(pdf_path))
                tables.append(df)
            else:
                logging.info(f"No table detected on {os.path.basename(pdf_path)} page {page_num}")

        if tables:
            final_df = tables[0] if len(tables) == 1 else (tables[0].append(tables[1:], ignore_index=True) if False else None)
            # safer concat
            final_df = __import__("pandas").concat(tables, ignore_index=True)
            csv_file = os.path.join(
                settings.OUTPUT_CSV_FOLDER,
                f"{os.path.splitext(os.path.basename(pdf_path))[0]}.csv"
            )
            final_df.to_csv(csv_file, index=False)
            return f"Processed {os.path.basename(pdf_path)} → {csv_file}"
        else:
            return f"No tables extracted from {os.path.basename(pdf_path)}"

    except Exception as e:
        logging.exception(f"Error processing {pdf_path}")
        return f"Error processing {os.path.basename(pdf_path)}: {e}"

def main():
    utils.check_dependencies()
    setup_folders()

    logging.basicConfig(
        filename=os.path.join(settings.LOG_FOLDER, "run.log"),
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )

    page_spec = input("Enter pages to extract (e.g., '3', '5-7', '2,4,6-8'): ").strip()

    pdf_files = pdf_processor.get_pdf_files()
    if not pdf_files:
        print("No PDF files found in input_pdfs/")
        return

    print(f"Starting parallel processing on {len(pdf_files)} PDF(s)...")
    results = []
    with ProcessPoolExecutor() as executor:
        future_map = {executor.submit(process_single_pdf, pdf, page_spec): pdf for pdf in pdf_files}
        for fut in as_completed(future_map):
            res = fut.result()
            results.append(res)
            print(res)

    print("\nSummary:")
    for r in results:
        print(r)

if __name__ == "__main__":
    main()
