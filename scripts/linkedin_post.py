"""Publish a LinkedIn post for every summary added by the latest commit.

Reads the new docs/Bytes-from-*/<post>.md files from `git diff HEAD~1 HEAD`,
and posts each one to the LinkedIn Posts API with a link to the site page.

Needs LINKEDIN_ACCESS_TOKEN and LINKEDIN_PERSON_URN (e.g. urn:li:person:abc123).
Without them it does nothing. A LinkedIn failure never fails the workflow.
"""
import datetime
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request

SITE = "https://jeanpaulnk.github.io/365Bytes/"
API = "https://api.linkedin.com/rest/posts"


def candidate_versions():
    """LinkedIn API versions (YYYYMM) expire after ~12 months: try this month, then earlier ones."""
    if os.environ.get("LINKEDIN_API_VERSION"):
        return [os.environ["LINKEDIN_API_VERSION"]]
    now = datetime.date.today()
    y, m = now.year, now.month
    out = []
    for _ in range(11):
        out.append(f"{y}{m:02d}")
        y, m = (y, m - 1) if m > 1 else (y - 1, 12)
    return out


MAX_COMMENTARY = 2900
# Characters LinkedIn's "little text" format treats as markup.
RESERVED = re.compile(r"([\\|{}@\[\]()<>#*_~])")


def esc(text):
    return RESERVED.sub(r"\\\1", text)


def new_posts():
    out = subprocess.run(
        ["git", "diff", "--name-only", "--diff-filter=A", "HEAD~1", "HEAD", "--", "docs/Bytes-from-*"],
        capture_output=True, text=True, check=True).stdout.split()
    return [p for p in out if p.endswith(".md") and not p.endswith("/index.md")]


def parse(path):
    text = open(path, encoding="utf-8").read()
    meta = {}
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    for line in (m.group(1).splitlines() if m else []):
        k, _, v = line.partition(":")
        meta[k.strip()] = v.strip().strip('"')
    summary = re.search(r"## Summary\s+(.*?)\n\s*\n##", text, re.S)
    points = re.search(r"## Key points\s+(.*?)\n\s*\n", text, re.S)
    meta["summary"] = summary.group(1).strip() if summary else ""
    meta["points"] = [l[2:].strip() for l in (points.group(1).splitlines() if points else []) if l.startswith("- ")][:3]
    return meta


def page_url(path):
    rel = path.removeprefix("docs/").removesuffix(".md")
    return SITE + rel + "/"


def commentary(meta, url):
    parts = [esc(meta.get("title", "")), "", esc(meta["summary"])]
    if meta["points"]:
        parts += ["", *["• " + esc(p) for p in meta["points"]]]
    parts += ["", "Original article: " + esc(meta.get("source", url))]
    text = "\n".join(parts)
    return text if len(text) <= MAX_COMMENTARY else text[:MAX_COMMENTARY - 1] + "…"


def publish(token, author, meta, url):
    body = {
        "author": author,
        "commentary": commentary(meta, url),
        "visibility": "PUBLIC",
        "distribution": {"feedDistribution": "MAIN_FEED", "targetEntities": [], "thirdPartyDistributionChannels": []},
        "content": {"article": {"source": url, "title": meta.get("title", "")[:200],
                                "description": meta.get("description", "")[:250]}},
        "lifecycleState": "PUBLISHED",
        "isReshareDisabledByAuthor": False,
    }
    data = json.dumps(body).encode()
    versions = candidate_versions()
    for i, version in enumerate(versions):
        req = urllib.request.Request(API, data=data, method="POST", headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0",
            "LinkedIn-Version": version,
        })
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.status
        except urllib.error.HTTPError as e:
            if e.code != 426 or i == len(versions) - 1:  # 426 = version not active
                raise


def main():
    token = os.environ.get("LINKEDIN_ACCESS_TOKEN")
    author = os.environ.get("LINKEDIN_PERSON_URN")
    if not token or not author:
        print("No LinkedIn secrets: skipping")
        return
    try:
        posts = os.environ.get("LINKEDIN_FILES", "").split() or new_posts()
    except subprocess.CalledProcessError as e:
        print(f"warning: could not list new posts: {e}", file=sys.stderr)
        return
    for path in posts:
        meta = parse(path)
        try:
            status = publish(token, author, meta, page_url(path))
            print(f"linkedin {status}: {meta.get('title')}")
        except urllib.error.HTTPError as e:
            print(f"warning: LinkedIn rejected {path}: {e.code} {e.read().decode()[:300]}", file=sys.stderr)
        except Exception as e:
            print(f"warning: LinkedIn post failed for {path}: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
