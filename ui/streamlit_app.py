"""
Entrypoint for Streamlit UI. Optionally, place UI logic here for more modularity.
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import streamlit as st
import os
import json
from pathlib import Path
from pdf_utils import strip_ocr_layer
from ocr_utils import ocr_pdf, save_ocr_to_pdf

CONFIG_FILE = "config.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        return {"output_folder": "output_pdfs/"}

def save_config(cfg):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)

def main():
    st.set_page_config(page_title="Nibble OCR Processor", layout="centered")
    st.title("Nibble OCR Processor")

    # Load config
    config = load_config()

    # File picker for input PDF
    uploaded_pdf = st.file_uploader("Select PDF to process", type=["pdf"])

    # Output folder selector (text input)
    st.markdown("**Output folder** (relative to this app):")
    output_folder = st.text_input(
        "Output Folder",
        value=config.get("output_folder", "output_pdfs/"),
        help="Type the output folder path. Will be saved for next session.",
    )

    # Save config if changed
    if output_folder != config.get("output_folder", ""):
        config["output_folder"] = output_folder
        save_config(config)

    # Prepare output filename and ready state
    output_filename = None
    ready = uploaded_pdf is not None and output_folder.strip() != ""
    if uploaded_pdf and ready:
        input_name = Path(uploaded_pdf.name).stem
        output_filename = Path(output_folder) / f"{input_name}_ocr.pdf"

    # PROCESS button
    process_btn = st.button("Process PDF", disabled=not ready)

    # Progress bar & status
    progress_ph = st.empty()
    status_ph = st.empty()

    if process_btn and ready:
        # Ensure output folder exists
        Path(output_folder).mkdir(parents=True, exist_ok=True)
        # Save the uploaded PDF to a temp file
        temp_path = Path("static") / "temp_input.pdf"
        with open(temp_path, "wb") as f:
            f.write(uploaded_pdf.read())
        status_ph.info("Stripping old OCR/text layer from PDF...")
        progress_ph.progress(0.1)
        images = strip_ocr_layer(str(temp_path))
        status_ph.info("Running Tesseract OCR on each page...")
        progress_ph.progress(0.3)

        ocr_results = []
        total_pages = len(images)
        for i, img in enumerate(images):
            status_ph.info(f"Running OCR on page {i+1} of {total_pages}...")
            result = ocr_pdf([img])[0]
            ocr_results.append(result)
            progress_ph.progress(0.3 + 0.6 * (i+1)/total_pages)

        status_ph.info("Saving PDF with new OCR layer...")
        save_ocr_to_pdf(images, ocr_results, str(output_filename))
        progress_ph.progress(1.0)
        status_ph.success(f"Done! Saved to {output_filename}")

        # Clean up temp file
        os.remove(temp_path)

    # Footer
    st.markdown("---")
    st.caption("Nibble OCR – Streamlit UI prototype | [Your Name or GitHub]")

if __name__ == "__main__":
    main()

