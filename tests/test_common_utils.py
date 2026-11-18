import os
import tempfile
import unittest

from utils.common_utils import load_md_file


class LoadMarkdownEncodingTests(unittest.TestCase):
    def test_reads_persian_utf8_markdown(self):
        expected = "عنوان پژوهش: رابطه سبک فرزندپروری با کیفیت رابطه زوجی"
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "idea.md")
            with open(path, "w", encoding="utf-8") as stream:
                stream.write(expected)
            self.assertEqual(load_md_file(path), expected)

    def test_reads_utf8_bom_markdown(self):
        expected = "ایده پژوهش"
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "idea.md")
            with open(path, "w", encoding="utf-8-sig") as stream:
                stream.write(expected)
            self.assertEqual(load_md_file(path), expected)

    def test_missing_markdown_returns_empty_string(self):
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "missing.md")
            self.assertEqual(load_md_file(path), "")


if __name__ == "__main__":
    unittest.main()
