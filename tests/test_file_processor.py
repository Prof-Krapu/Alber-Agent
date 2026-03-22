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
