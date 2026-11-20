import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import linkedin_post as li  # noqa: E402


def meta(title="", summary="", points=()):
    return {"title": title, "description": "", "summary": summary, "points": list(points)}


EXCHANGE = "docs/Bytes-from-Exchange-Team-Blog/a.md"
OUTLOOK = "docs/Bytes-from-Outlook-Blog/b.md"
ENTRA = "docs/Bytes-from-Microsoft-Entra-Blog/c.md"
SECURITY = "docs/Bytes-from-Microsoft-Security-Blog/d.md"


class Priority(unittest.TestCase):
    def test_priority_sections_always_count(self):
        self.assertTrue(li.is_priority(EXCHANGE, meta("Anything")))
        self.assertTrue(li.is_priority(OUTLOOK, meta("Anything")))

    def test_topics_in_other_sections(self):
        self.assertTrue(li.is_priority(SECURITY, meta("Reject Direct Send in Exchange Online")))
        self.assertTrue(li.is_priority(ENTRA, meta("Conditional Access", "Applies to Outlook on the web.")))
        self.assertTrue(li.is_priority(SECURITY, meta("Phishing", points=["Targets shared mailboxes"])))
        self.assertTrue(li.is_priority(SECURITY, meta("EWS retirement")))

    def test_other_topics_and_look_alikes(self):
        self.assertFalse(li.is_priority(ENTRA, meta("Global Secure Access", "Zero Trust networking.")))
        self.assertFalse(li.is_priority(SECURITY, meta("Outlooks for 2027 budgets are bleak")))
        self.assertFalse(li.is_priority(SECURITY, meta("Exchanges of crypto assets")))


class Choose(unittest.TestCase):
    def setUp(self):
        self.metas = {EXCHANGE: meta("e"), OUTLOOK: meta("o"), ENTRA: meta("n"), SECURITY: meta("s"),
                      "docs/Bytes-from-Microsoft-Purview-Blog/p.md": meta("p"),
                      "docs/Bytes-from-Microsoft-Copilot-Blog/q.md": meta("q")}

    def test_priority_first_then_limited_rest(self):
        order = [ENTRA, EXCHANGE, SECURITY, OUTLOOK, "docs/Bytes-from-Microsoft-Purview-Blog/p.md",
                 "docs/Bytes-from-Microsoft-Copilot-Blog/q.md"]
        posts, skipped = li.choose(order, self.metas, limit=2)
        self.assertEqual(posts, [EXCHANGE, OUTLOOK, ENTRA, SECURITY])
        self.assertEqual(skipped, ["docs/Bytes-from-Microsoft-Purview-Blog/p.md",
                                   "docs/Bytes-from-Microsoft-Copilot-Blog/q.md"])

    def test_priority_posts_are_never_limited(self):
        posts, skipped = li.choose([EXCHANGE, OUTLOOK], self.metas, limit=0)
        self.assertEqual(posts, [EXCHANGE, OUTLOOK])
        self.assertEqual(skipped, [])

    def test_zero_limit_skips_every_other_topic(self):
        posts, skipped = li.choose([ENTRA, SECURITY], self.metas, limit=0)
        self.assertEqual((posts, skipped), ([], [ENTRA, SECURITY]))


if __name__ == "__main__":
    unittest.main()
