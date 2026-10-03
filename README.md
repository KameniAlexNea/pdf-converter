# PDF Converter

A small Python utility that scans a folder for images and PDF files, converts supported image files to PDF, and merges everything into a single PDF document.

## Features

- Scans a target folder for supported image types and existing PDFs
- Converts common image formats such as PNG, JPG, JPEG, BMP, GIF, TIFF, and WebP to PDF
- Merges all input files into one output PDF in filename order
- Keeps the generated temporary files cleanly isolated while processing
- Provides both Gradio UI and command-line usage from one file

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

### Single-file app (Gradio by default)

The [app.py](/home/eak/Documents/AI/Packages/pdf-converter/pdf-converter/app.py) script is self-contained and can be run in two modes:

- **No arguments**: launches the Gradio web app
- **With input paths**: runs in command-line mode and creates a merged PDF

```bash
python app.py
python app.py /path/to/folder -o /path/to/output.pdf
python app.py page1.png page2.jpg existing.pdf -o merged.pdf
```

If `-o` is omitted, the output file defaults to `merged_document.pdf` in the scanned folder.

## Example

If a folder contains:

- `page1.png`
- `page2.jpg`
- `existing.pdf`

The script will convert `page1.png` and `page2.jpg` to temporary PDFs, include `existing.pdf`, and merge them into a single PDF document.

## Project files

- `app.py`: self-contained Gradio + CLI entry point

## Running tests

```bash
pytest -q
```
