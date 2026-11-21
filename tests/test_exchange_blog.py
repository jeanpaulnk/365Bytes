import html
import json
import re
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import exchange_blog as e  # noqa: E402

ATTACK = '0;url=https://evil.example/" http-equiv="refresh'


class Description(unittest.TestCase):
    def write(self, ai):
        item = {"title": "Post", "published": datetime(2026, 11, 21, tzinfo=timezone.utc),
                "author": "", "link": "https://techcommunity.microsoft.com/a"}
        with tempfile.TemporaryDirectory() as d, mock.patch.object(e, "POSTS", Path(d)):
            text = e.write_post(item, ai).read_text(encoding="utf-8")
        return json.loads(re.search(r"^description: (.*)$", text, re.M).group(1))

    def test_quotes_cannot_break_out_of_the_meta_description(self):
        for ai in ({"summary": ATTACK}, {"excerpt": ATTACK}, {"summary": "it's " + ATTACK}):
            with self.subTest(ai=ai):
                description = self.write(ai)
                self.assertNotIn('"', description)
                self.assertNotIn("'", description)
                self.assertIn(html.unescape(description), (ATTACK, "it's " + ATTACK))

    def test_markdown_body_text_is_unchanged(self):
        self.assertEqual(e.md('say "hi"'), 'say "hi"')


if __name__ == "__main__":
    unittest.main()
