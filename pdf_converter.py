from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Iterable, Sequence

from PIL import Image
from pypdf import PdfReader, PdfWriter

SUPPORTED_IMAGE_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".bmp",
    ".gif",
    ".tif",
    ".tiff",
    ".webp",
}
SUPPORTED_DOCUMENT_EXTENSIONS = {".pdf"} | SUPPORTED_IMAGE_EXTENSIONS


def _normalize_file_list(paths: Iterable[Path]) -> list[Path]:
    return sorted({Path(path) for path in paths}, key=lambda item: item.name.lower())


def collect_documents(folder: Path, *, exclude: Path | None = None) -> list[Path]:
    """Return pdf and image files in the folder, sorted by filename."""
    folder = Path(folder)
    if not folder.exists():
        raise FileNotFoundError(f"Folder does not exist: {folder}")

    documents: list[Path] = []
    for candidate in sorted(folder.iterdir(), key=lambda item: item.name.lower()):
        if not candidate.is_file():
            continue
        if exclude is not None and candidate.resolve() == exclude.resolve():
            continue
        suffix = candidate.suffix.lower()
        if suffix in SUPPORTED_DOCUMENT_EXTENSIONS:
            documents.append(candidate)
    return documents


def convert_image_to_pdf(image_path: Path, output_pdf_path: Path) -> Path:
    image_path = Path(image_path)
    output_pdf_path = Path(output_pdf_path)
    output_pdf_path.parent.mkdir(parents=True, exist_ok=True)

    with Image.open(image_path) as image:
        rgb_image = image.convert("RGB") if image.mode not in {"RGB", "L"} else image
        rgb_image.save(output_pdf_path, format="PDF")

    return output_pdf_path


def merge_pdf_files(pdf_paths: Sequence[Path], output_pdf_path: Path) -> Path:
    output_pdf_path = Path(output_pdf_path)
    output_pdf_path.parent.mkdir(parents=True, exist_ok=True)

    if not pdf_paths:
        raise ValueError("No PDF files to merge.")

    writer = PdfWriter()
    for pdf_path in pdf_paths:
        reader = PdfReader(str(pdf_path))
        for page in reader.pages:
            writer.add_page(page)

    with output_pdf_path.open("wb") as output_file:
        writer.write(output_file)

    return output_pdf_path


def scan_folder_and_merge(folder: Path, output_path: Path | str = "merged_document.pdf") -> Path:
    folder = Path(folder)
    output_path = Path(output_path)

    if output_path.is_absolute():
        target_output = output_path
    else:
        target_output = folder / output_path

    documents = collect_documents(folder, exclude=target_output)
    if not documents:
        raise ValueError(f"No PDF or image files found in: {folder}")

    temp_dir = Path(tempfile.mkdtemp(prefix="pdf-converter-"))
    converted_pdfs: list[Path] = []
    try:
        for document in documents:
            if document.suffix.lower() == ".pdf":
                converted_pdfs.append(document)
                continue

            temp_pdf = temp_dir / f"{document.stem}.pdf"
            convert_image_to_pdf(document, temp_pdf)
            converted_pdfs.append(temp_pdf)

        merge_pdf_files(converted_pdfs, target_output)
        return target_output
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Scan a folder for images and PDFs, convert images to PDF, and merge them into one document.")
    parser.add_argument("folder", type=Path, help="Folder to scan for images and PDFs.")
    parser.add_argument("-o", "--output", type=Path, default=Path("merged_document.pdf"), help="Destination PDF path.")
    args = parser.parse_args(argv)

    try:
        output = scan_folder_and_merge(args.folder, args.output)
    except (FileNotFoundError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    print(f"Merged document created at: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
