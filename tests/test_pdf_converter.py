from pathlib import Path

import pytest
from PIL import Image
from pypdf import PdfReader

from pdf_converter import scan_folder_and_merge


def _make_valid_pdf(path: Path) -> None:
    Image.new("RGB", (10, 10), color="green").save(path, "PDF")


def test_scan_folder_and_merge_images_and_pdf(tmp_path):
    source_dir = tmp_path / "input"
    source_dir.mkdir()

    image_one = source_dir / "first.png"
    image_two = source_dir / "second.jpg"
    existing_pdf = source_dir / "existing.pdf"

    Image.new("RGB", (50, 50), color="red").save(image_one)
    Image.new("RGB", (50, 50), color="blue").save(image_two)
    _make_valid_pdf(existing_pdf)

    output_pdf = source_dir / "merged_document.pdf"
    result = scan_folder_and_merge(source_dir, output_pdf)

    assert result == output_pdf
    assert output_pdf.exists()

    reader = PdfReader(str(output_pdf))
    assert len(reader.pages) == 3


def test_scan_folder_and_merge_handles_same_stem_different_extensions(tmp_path):
    source_dir = tmp_path / "input"
    source_dir.mkdir()

    Image.new("RGB", (10, 10), color="red").save(source_dir / "photo.png")
    Image.new("RGB", (10, 10), color="blue").save(source_dir / "photo.jpg")

    output_pdf = source_dir / "merged_document.pdf"
    result = scan_folder_and_merge(source_dir, output_pdf)

    assert result == output_pdf
    assert len(PdfReader(str(output_pdf)).pages) == 2


def test_scan_folder_and_merge_raises_for_empty_folder(tmp_path):
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()

    with pytest.raises(ValueError):
        scan_folder_and_merge(empty_dir, tmp_path / "merged.pdf")


def test_scan_folder_and_merge_raises_for_missing_folder(tmp_path):
    missing_dir = tmp_path / "missing"

    with pytest.raises(FileNotFoundError):
        scan_folder_and_merge(missing_dir, tmp_path / "merged.pdf")


def test_scan_folder_and_merge_resolves_relative_output_path(tmp_path):
    source_dir = tmp_path / "input"
    source_dir.mkdir()

    Image.new("RGB", (10, 10), color="red").save(source_dir / "image.png")

    merged = scan_folder_and_merge(source_dir, "nested/relative_merge.pdf")

    assert merged == source_dir / "nested/relative_merge.pdf"
    assert merged.exists()
    assert len(PdfReader(str(merged)).pages) == 1
