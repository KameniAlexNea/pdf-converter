from __future__ import annotations

import argparse
import atexit
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Sequence

import gradio as gr
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

_PERSISTENT_TEMP_DIRS: list[Path] = []


def _register_persistent_temp_dir(directory: Path) -> None:
    _PERSISTENT_TEMP_DIRS.append(directory)


def _cleanup_persistent_temp_dirs() -> None:
    for directory in _PERSISTENT_TEMP_DIRS:
        shutil.rmtree(directory, ignore_errors=True)


atexit.register(_cleanup_persistent_temp_dirs)


def collect_documents(folder: Path, *, exclude: Path | None = None) -> list[Path]:
    folder = Path(folder)
    if not folder.exists():
        raise FileNotFoundError(f"Folder does not exist: {folder}")

    documents: list[Path] = []
    for candidate in sorted(folder.iterdir(), key=lambda item: item.name.lower()):
        if not candidate.is_file():
            continue
        if exclude is not None and candidate.resolve() == exclude.resolve():
            continue
        if candidate.suffix.lower() in SUPPORTED_DOCUMENT_EXTENSIONS:
            documents.append(candidate)
    return documents


def convert_image_to_pdf(image_path: Path, output_pdf_path: Path) -> Path:
    output_pdf_path.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(image_path) as image:
        image.convert("RGB").save(output_pdf_path, format="PDF")
    return output_pdf_path


def merge_pdf_files(pdf_paths: Sequence[Path], output_pdf_path: Path) -> Path:
    if not pdf_paths:
        raise ValueError("No PDF files to merge.")

    output_pdf_path.parent.mkdir(parents=True, exist_ok=True)

    writer = PdfWriter()
    try:
        for pdf_path in pdf_paths:
            with PdfReader(str(pdf_path)) as reader:
                for page in reader.pages:
                    writer.add_page(page)
        with output_pdf_path.open("wb") as output_file:
            writer.write(output_file)
    finally:
        writer.close()

    return output_pdf_path


def scan_folder_and_merge(folder: Path, output_path: Path | str = "merged_document.pdf") -> Path:
    folder = Path(folder)
    output_path = Path(output_path)
    target_output = output_path if output_path.is_absolute() else folder / output_path

    documents = collect_documents(folder, exclude=target_output)
    if not documents:
        raise ValueError(f"No PDF or image files found in: {folder}")

    temp_dir = Path(tempfile.mkdtemp(prefix="pdf-converter-"))
    converted_pdfs: list[Path] = []
    try:
        for index, document in enumerate(documents):
            if document.suffix.lower() == ".pdf":
                converted_pdfs.append(document)
                continue
            temp_pdf = temp_dir / f"{document.stem}_{index}.pdf"
            convert_image_to_pdf(document, temp_pdf)
            converted_pdfs.append(temp_pdf)

        return merge_pdf_files(converted_pdfs, target_output)
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def _normalize_uploaded_files(files):
    if files is None:
        return []

    if isinstance(files, (str, Path)):
        files = [files]
    elif not isinstance(files, list):
        files = [files]

    normalized: list[Path] = []
    for item in files:
        if item is None:
            continue

        if isinstance(item, (str, Path)):
            candidate = Path(item)
        elif hasattr(item, "name"):
            candidate = Path(str(item.name))
        elif isinstance(item, dict) and "name" in item:
            candidate = Path(str(item["name"]))
        else:
            continue

        if candidate.exists():
            normalized.append(candidate)

    return normalized


def merge_uploaded_documents(files):
    uploaded_paths = _normalize_uploaded_files(files)
    if not uploaded_paths:
        raise ValueError("Please upload at least one image or PDF file.")

    supported_files = [path for path in uploaded_paths if path.suffix.lower() in SUPPORTED_DOCUMENT_EXTENSIONS]
    if not supported_files:
        raise ValueError("Unsupported file type. Please upload one or more images or PDFs.")

    source_dir = Path(tempfile.mkdtemp(prefix="pdf-converter-upload-"))
    _register_persistent_temp_dir(source_dir)
    output_pdf = source_dir / "merged_document.pdf"

    for index, source_path in enumerate(supported_files):
        destination = source_dir / f"{index:02d}_{source_path.name}"
        shutil.copy2(source_path, destination)

    scan_folder_and_merge(source_dir, output_pdf)
    return str(output_pdf)


def merge_paths(paths: Sequence[Path], output_path: Path) -> Path:
    if not paths:
        raise ValueError("No input paths provided.")

    if len(paths) == 1 and paths[0].is_dir():
        return scan_folder_and_merge(paths[0], output_path)

    missing_paths = [path for path in paths if not path.exists()]
    if missing_paths:
        missing = ", ".join(str(path) for path in missing_paths)
        raise FileNotFoundError(f"Input path(s) do not exist: {missing}")

    files = [path for path in paths if path.is_file()]
    unsupported = [path for path in files if path.suffix.lower() not in SUPPORTED_DOCUMENT_EXTENSIONS]
    if unsupported:
        names = ", ".join(str(path) for path in unsupported)
        raise ValueError(f"Unsupported input file type(s): {names}")

    temp_input_dir = Path(tempfile.mkdtemp(prefix="pdf-converter-cli-"))
    try:
        for index, file_path in enumerate(files):
            destination = temp_input_dir / f"{index:04d}_{file_path.name}"
            shutil.copy2(file_path, destination)
        return scan_folder_and_merge(temp_input_dir, output_path)
    finally:
        shutil.rmtree(temp_input_dir, ignore_errors=True)


def build_interface() -> gr.Blocks:
    return gr.Interface(
        fn=merge_uploaded_documents,
        inputs=gr.File(
            label="Upload images and PDFs",
            file_count="multiple",
            file_types=[
                ".png",
                ".jpg",
                ".jpeg",
                ".bmp",
                ".gif",
                ".tif",
                ".tiff",
                ".webp",
                ".pdf",
            ],
        ),
        outputs=gr.File(label="Merged PDF"),
        title="PDF Converter",
        description="Upload any number of images and PDFs to create a single merged PDF document.",
    )


def launch_gradio_interface() -> int:
    demo = build_interface()
    demo.launch()
    return 0


def run_cli(argv: Sequence[str]) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Merge images and PDF files into one PDF. "
            "By default (no input paths), this script launches the Gradio app."
        ),
    )
    parser.add_argument(
        "inputs",
        nargs="*",
        type=Path,
        help="Either one folder path to scan, or one/more files to merge in the given order.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("merged_document.pdf"),
        help="Destination PDF path. Relative paths are resolved against the current working directory.",
    )
    parser.add_argument(
        "--gradio",
        action="store_true",
        help="Launch the Gradio web app explicitly.",
    )
    args = parser.parse_args(argv)

    if args.gradio or not args.inputs:
        return launch_gradio_interface()

    try:
        output = merge_paths(args.inputs, args.output)
    except (FileNotFoundError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    print(f"Merged document created at: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_cli(sys.argv[1:]))
