# PDF Converter

A small Python utility that scans a folder for images and PDF files, converts supported image files to PDF, and merges everything into a single PDF document.

## Features

- Scans a target folder for supported image types and existing PDFs
- Converts common image formats such as PNG, JPG, JPEG, BMP, GIF, TIFF, and WebP to PDF
- Merges all input files into one output PDF in filename order
- Keeps the generated temporary files cleanly isolated while processing
- Provides both a CLI entry point and Python function usage

## Supported input files

- PDF: `.pdf`
- Images: `.png`, `.jpg`, `.jpeg`, `.bmp`, `.gif`, `.tif`, `.tiff`, `.webp`

## Installation

1. Clone the repository.
2. Create and activate a virtual environment if desired.
3. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Command line

Run the converter against a folder and optionally specify an output PDF path:

```bash
python main.py /path/to/folder
python main.py /path/to/folder -o /path/to/output.pdf
```

If `-o` is omitted, the output file defaults to `merged_document.pdf` in the scanned folder.

### Python API

```python
from pathlib import Path
from pdf_converter import scan_folder_and_merge

output = scan_folder_and_merge(Path("/path/to/folder"), Path("/path/to/output.pdf"))
print(f"Created: {output}")
```

## Example

If a folder contains:

- `page1.png`
- `page2.jpg`
- `existing.pdf`

The script will convert `page1.png` and `page2.jpg` to temporary PDFs, include `existing.pdf`, and merge them into a single PDF document.

## Project files

- `main.py`: command-line entry point
- `pdf_converter.py`: conversion and merge logic
- `tests/test_pdf_converter.py`: validation tests

## Running tests

```bash
pytest
```
