from pathlib import Path

from translate import read_docx, translate_long_text, save_pdf
from ner import rebel_on_long_text
import time

INPUT_FOLDER = "documents"
OUTPUT_FOLDER = "translated_pdf"
Path(OUTPUT_FOLDER).mkdir(exist_ok=True)

def process_file(file_path):
    print(f"\nProcessing: {file_path.name}")

    total_start = time.time()

    t0 = time.time()
    paragraphs = read_docx(file_path)
    print(f"Read DOCX: {time.time() - t0:.2f}s")

    t0 = time.time()

    translated_paragraphs = [
        translate_long_text(p) for p in paragraphs if p.strip()
    ]

    translated_text = "\n".join(translated_paragraphs)

    print(f"Translation: {time.time() - t0:.2f}s")

    output_path = Path(OUTPUT_FOLDER) / f"{file_path.stem}.pdf"

    save_pdf(translated_paragraphs, str(output_path))

    print(f"Saved PDF: {output_path}")
    t0 = time.time()

    kb = rebel_on_long_text(translated_text)

    print(f"NER + REBEL: {time.time() - t0:.2f}s")

    print(f"\nTOTAL TIME: {time.time() - total_start:.2f}s")

    print("\n--- ENTITIES ---")
    print(kb.entities)

    print("\n--- RELATIONS ---")
    for r in kb.relations:
        print(r)

# if __name__ == "__main__":
#     files = sorted(Path(INPUT_FOLDER).glob("*.docx"))
#
#     for file in files:
#         process_file(file)