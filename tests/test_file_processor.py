import base64
from file_processor import (
    get_file_type,
    process_file,
    FileType,
    get_mime_type_from_ext,
)


def test_get_file_type_and_mime():
    assert get_file_type("image.png", "image/png") == FileType.IMAGE
    assert (
        get_file_type(
            "doc.docx",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
        == FileType.DOCX
    )
    assert (
        get_file_type(
            "sheet.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        == FileType.XLSX
    )
    assert get_file_type("readme.md", "text/markdown") == FileType.TEXT
    assert get_mime_type_from_ext("picture.jpg") == "image/jpeg"


def test_process_text_file():
    content = b"Bonjour\nCeci est un test."
    att = process_file(content, "test.txt", "text/plain")
    assert att is not None
    assert att.file_type == FileType.TEXT
    assert "Bonjour" in att.text_content


def test_process_unsupported_file():
    # random binary should be unknown and return None
    content = b"\x00\x01\x02\x03"
    att = process_file(content, "raw.bin", "application/octet-stream")
    assert att is None

def test_process_pdf_generates_images_and_text():
    # Créer un PDF minimal avec fitz
    from file_processor import process_file, FileType, attachment_to_content_blocks
    import fitz
    import os
    
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "Test PDF Content")
    pdf_bytes = doc.tobytes()
    doc.close()

    result = process_file(pdf_bytes, "test.pdf")
    assert result is not None
    assert result.file_type == FileType.PDF
    assert len(result.pages) == 1
    assert "Test PDF Content" in result.text_content
    
    # Vérifier que le format envoyé à Mistral contient les deux
    blocks = attachment_to_content_blocks(result)
    assert any(b["type"] == "text" for b in blocks)
    assert any(b["type"] == "image_url" for b in blocks)
