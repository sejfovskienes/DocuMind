import unittest

from app.base.extensions.document_extension import (
    chunk_document_text,
    clean_document_text,
)


class DocumentExtensionTests(unittest.TestCase):
    def test_clean_text_normalizes_unicode_and_whitespace(self) -> None:
        self.assertEqual(clean_document_text("  café\n  line  "), "caf line")

    def test_chunking_stops_when_final_chunk_reaches_end(self) -> None:
        words = [f"word{index}" for index in range(150)]
        chunks = chunk_document_text(" ".join(words), chunk_size=100, overlap=90)

        self.assertEqual(len(chunks), 6)
        self.assertEqual(chunks[0].split(), words[:100])
        self.assertEqual(chunks[1].split(), words[10:110])
        self.assertEqual(chunks[-1].split(), words[50:])

    def test_empty_text_and_invalid_overlap(self) -> None:
        self.assertEqual(chunk_document_text("", chunk_size=10, overlap=2), [])
        with self.assertRaises(ValueError):
            chunk_document_text("words", chunk_size=2, overlap=2)


if __name__ == "__main__":
    unittest.main()
