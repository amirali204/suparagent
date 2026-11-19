"""Regression checks for XML supplied inside untrusted PowerPoint uploads."""

import io
import zipfile

import pytest

from app.services.attachments import AttachmentError, extract_document_text


def _pptx(slide_xml: bytes) -> bytes:
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("ppt/slides/slide1.xml", slide_xml)
    return stream.getvalue()


def test_valid_pptx_slide_text_is_extracted():
    xml = (
        b'<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" '
        b'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
        b'<p:sp><a:t>Safe slide</a:t></p:sp></p:sld>'
    )
    assert "--- Slide 1 ---\nSafe slide" in extract_document_text(_pptx(xml), ".pptx", "safe.pptx")


@pytest.mark.parametrize("xml", [
    b'<!DOCTYPE root [<!ENTITY ex "EXPANDED">]><root><t>&ex;</t></root>',
    b'<!DOCTYPE root SYSTEM "file:///etc/passwd"><root/>',
])
def test_pptx_rejects_doctype_and_entities(xml):
    with pytest.raises(AttachmentError) as error:
        extract_document_text(_pptx(xml), ".pptx", "unsafe.pptx")
    assert error.value.status == 422
    assert error.value.code == "corrupt_document"
