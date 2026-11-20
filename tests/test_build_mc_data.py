import io
import json
import os
import sys
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import build_mc_data as b  # noqa: E402


def http_error(code, body=""):
    return urllib.error.HTTPError("https://example.test", code, "x", {}, io.BytesIO(body.encode()))


def msg(i, modified="2026-01-01", title="Post"):
    return {"id": i, "title": title, "lastModifiedDateTime": modified,
            "body": {"contentType": "html", "content": "<p>x</p>"}}


class Base(unittest.TestCase):
    def setUp(self):
        patcher = mock.patch.dict(os.environ)
        patcher.start()
        self.addCleanup(patcher.stop)
        for k in ("MC_TENANTS", "MC_TENANT_ID", "MC_CLIENT_ID", "MC_REDACT"):
            os.environ.pop(k, None)
        b.PROBLEMS.clear()
        b.LOOKED_UP.clear()


class RoadmapIds(Base):
    def test_platform_suffix_order_and_unknown(self):
        self.assertEqual(b.platform_suffix(["iOS", "Web", "Mac"]), "WMI")
        self.assertEqual(b.platform_suffix(["Mystery"]), "X")
        self.assertEqual(b.platform_suffix([]), "")

    def test_official_roadmap_id(self):
        rec = b.from_roadmap({"id": "564615", "platforms": ["Desktop", "Web"], "title": "t"})
        self.assertEqual(rec["Id"], "RM564615-WD")

    def test_archive_record_gets_the_same_suffix(self):
        rec = {"Id": "RM1", "Details": [{"Name": "Platforms", "Value": "Desktop, Mac"}]}
        self.assertEqual(b.platform_id(rec)["Id"], "RM1-DM")
        self.assertEqual(b.platform_id({"Id": "RM2"})["Id"], "RM2")
        self.assertEqual(b.platform_id({"Id": "MC3"})["Id"], "MC3")


class Redaction(Base):
    def test_terms_include_tenants_lookup_and_extras(self):
        os.environ.update(MC_TENANTS="alpha.example:app-a", MC_REDACT="alpha, extra-term")
        b.LOOKED_UP.add("11111111-2222-3333-4444-555555555555")
        terms = b.redact_terms()
        for t in ("alpha.example", "app-a", "alpha", "extra-term", "11111111-2222-3333-4444-555555555555"):
            self.assertIn(t, terms)

    def test_scrub_is_case_insensitive(self):
        out = b.scrub({"t": "see ALPHA.example now"}, ["alpha.example"])
        self.assertEqual(out["t"], "see [redacted] now")

    def test_scrub_pii_removes_emails_and_guids(self):
        rec = b.scrub_pii({"t": "mail a.b@contoso.com id 11111111-2222-3333-4444-555555555555"})
        self.assertEqual(rec["t"], "mail [email] id [id]")


class Retry(Base):
    def test_retries_busy_answers_then_succeeds(self):
        calls = []

        def fake_urlopen(req, timeout):
            calls.append(1)
            if len(calls) < 3:
                raise http_error(503)
            return io.BytesIO(b'{"ok": true}')

        with mock.patch("urllib.request.urlopen", fake_urlopen):
            self.assertEqual(b.open_json("x", sleep=lambda s: None), {"ok": True})
        self.assertEqual(len(calls), 3)

    def test_does_not_retry_client_errors(self):
        calls = []

        def fake_urlopen(req, timeout):
            calls.append(1)
            raise http_error(401)

        with mock.patch("urllib.request.urlopen", fake_urlopen), self.assertRaises(urllib.error.HTTPError):
            b.open_json("x", sleep=lambda s: None)
        self.assertEqual(len(calls), 1)

    def test_describe_error_has_codes_but_not_the_response_text(self):
        e = http_error(401, '{"error":"invalid_client","error_codes":[700213],"error_description":"secret"}')
        text = b.describe_error(e)
        self.assertEqual(text, "HTTP 401 invalid_client AADSTS700213")
        self.assertNotIn("secret", text)


class Graph(Base):
    def run_graph(self, data, lookups, tenants):
        def lookup(t):
            if lookups.get(t) is None:
                raise ValueError("tenant not found")
            return {"id": lookups[t], "token_endpoint": "x", "graph_host": "graph.test", "audience": "a"}

        def pages(token, path, fetch=None, host=None):
            kind = "issues" if path.startswith("issues") else "messages"
            return iter(data[token][kind])

        with mock.patch.object(b, "graph_pages", pages):
            return b.graph_records(tenants=tenants, fetch=True, lookup=lookup,
                                   token_for=lambda info, client: info["id"])

    def test_merges_tenants_and_health_comes_from_the_primary_only(self):
        data = {"t1": {"messages": [msg("MC1", "2026-01-02"), msg("MC2")],
                       "issues": [{"id": "EX1", "title": "Incident", "impactDescription": "mail a@b.com"}]},
                "t2": {"messages": [msg("MC1", "2026-01-03", "newer")],
                       "issues": [{"id": "EX9", "title": "Other tenant"}]}}
        recs = self.run_graph(data, {"a": "t1", "b": "t2"}, [("a", "c"), ("b", "c")])
        ids = sorted(r["Id"] for r in recs)
        self.assertEqual(ids, ["EX1", "MC1", "MC2"])
        mc1 = next(r for r in recs if r["Id"] == "MC1")
        self.assertEqual(mc1["Title"], "newer")
        self.assertIn({"Name": "SeenIn", "Value": "2 of 2 tenants checked"}, mc1["Details"])
        ex1 = next(r for r in recs if r["Id"] == "EX1")
        self.assertNotIn("a@b.com", json.dumps(ex1))

    def test_unreachable_tenant_is_skipped_and_recorded(self):
        data = {"t1": {"messages": [msg("MC1")], "issues": []}}
        recs = self.run_graph(data, {"a": "t1", "b": None}, [("a", "c"), ("b", "c")])
        self.assertEqual([r["Id"] for r in recs], ["MC1"])
        self.assertEqual(list(b.PROBLEMS), ["Graph tenant 2 of 2"])
        self.assertTrue(b.PROBLEMS["Graph tenant 2 of 2"].startswith("lookup:"))

    def test_no_tenants_configured_does_nothing(self):
        self.assertEqual(b.graph_records(), [])
        self.assertEqual(b.PROBLEMS, {})


class Build(Base):
    def test_official_overrides_archive_and_alias_and_no_leak(self):
        os.environ.update(MC_REDACT="contoso")
        archive = {"roadmap.json": [{"Id": "RM564615", "Title": "old",
                                     "Details": [{"Name": "Platforms", "Value": "Web"}]},
                                    {"Id": "RM999", "Title": "kept"}],
                   "messages.json": [], "azure.json": []}
        official = lambda fetch: [b.from_roadmap({"id": "564615", "title": "new contoso",
                                                  "platforms": ["Web", "iOS"]})]
        with tempfile.TemporaryDirectory() as d:
            b.build(d, fetch=lambda url: archive[url.rsplit("/", 1)[1]],
                    graph=lambda: [], official=official)
            names = sorted(p.name for p in (Path(d) / "posts").iterdir())
            self.assertEqual(names, ["RM564615-WI.json", "RM564615.json", "RM999.json"])
            text = (Path(d) / "posts" / "RM564615.json").read_text()
            self.assertIn("new [redacted]", text)
            self.assertNotIn("contoso", " ".join(p.read_text() for p in Path(d).rglob("*.json")).lower())

    def test_archive_keeps_old_posts_and_seeds_only_once(self):
        seed = {"messages.json": [{"Id": "MC1", "Title": "old"}], "roadmap.json": [], "azure.json": []}
        calls = []

        def fetch(url):
            calls.append(url)
            return seed[url.rsplit("/", 1)[1]]

        with tempfile.TemporaryDirectory() as d:
            archive = os.path.join(d, "mc-archive", "archive.json.gz")
            b.build(os.path.join(d, "a"), fetch=fetch, graph=lambda: [], official=lambda f: [],
                    archive_path=archive)
            self.assertEqual(len(calls), 3)
            b.build(os.path.join(d, "b"), fetch=fetch, graph=lambda: [{"Id": "MC2", "Title": "new"}],
                    official=lambda f: [], archive_path=archive)
            self.assertEqual(len(calls), 3)  # the archive exists, so merill is not read again
            names = sorted(p.name for p in (Path(d) / "b" / "posts").iterdir())
            self.assertEqual(names, ["MC1.json", "MC2.json"])

    def test_failed_official_feed_keeps_archive_and_records_problem(self):
        archive = {"roadmap.json": [{"Id": "RM5", "Title": "kept"}], "messages.json": [], "azure.json": []}

        def boom(url):
            raise http_error(500)

        with tempfile.TemporaryDirectory() as d:
            b.build(d, fetch=lambda url: archive[url.rsplit("/", 1)[1]], graph=lambda: [],
                    official=lambda fetch: b.official_records(boom))
            self.assertTrue((Path(d) / "posts" / "RM5.json").exists())
        self.assertEqual(sorted(b.PROBLEMS), ["Microsoft azure feed", "Microsoft m365 feed"])


class Alerts(Base):
    def make_api(self, issues):
        calls = []

        def api(method, path, data=None):
            calls.append((method, path, data))
            return issues if method == "GET" else {}

        return api, calls

    def test_opens_an_issue_when_a_source_fails(self):
        api, calls = self.make_api([])
        b.report_problems({"Microsoft azure feed": "HTTP 500"}, api=api)
        self.assertEqual([c[0] for c in calls], ["GET", "POST"])
        self.assertIn("Microsoft azure feed", calls[1][2]["body"])

    def test_updates_the_existing_issue_instead_of_adding_another(self):
        api, calls = self.make_api([{"title": b.ISSUE_TITLE, "number": 7, "body": "old"}])
        b.report_problems({"x": "HTTP 500"}, api=api)
        self.assertEqual([c[0] for c in calls], ["GET", "PATCH"])

    def test_closes_the_issue_when_everything_works(self):
        api, calls = self.make_api([{"title": b.ISSUE_TITLE, "number": 7, "body": "old"}])
        b.report_problems({}, api=api)
        self.assertEqual([c[0] for c in calls], ["GET", "POST", "PATCH"])
        self.assertEqual(calls[2][2]["state"], "closed")

    def test_pull_requests_never_touch_issues(self):
        os.environ.update(GITHUB_TOKEN="t", GITHUB_REPOSITORY="o/r", GITHUB_EVENT_NAME="pull_request")
        with mock.patch("urllib.request.urlopen") as urlopen:
            b.report_problems({"x": "y"})
        urlopen.assert_not_called()

    def test_api_failure_does_not_raise(self):
        def api(method, path, data=None):
            raise http_error(403)

        b.report_problems({"x": "y"}, api=api)


if __name__ == "__main__":
    unittest.main()
