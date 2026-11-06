"""Build per-post JSON for the Message Center reader.

Downloads the public data from github.com/merill/mc (MIT) and writes:
  <out>/posts/<ID>.json  one file per active Message Center, Roadmap and Azure post
  <out>/latest.json      the newest posts, for the list on the Message Center page

Runs after `mkdocs build` in the deploy workflow. A download failure never
fails the deploy: the reader falls back to the source site.
"""
import json
import re
import sys
import urllib.request
from pathlib import Path

RAW = "https://raw.githubusercontent.com/merill/mc/main/@data/"
SOURCES = ["messages.json", "roadmap.json", "azure.json"]
LATEST = 400
ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9-]{1,120}$")
KEEP = ["Id", "Title", "Source", "Category", "Severity", "IsMajorChange", "StartDateTime",
        "LastModifiedDateTime", "EndDateTime", "ActionRequiredByDateTime", "Services", "Tags",
        "SeenOnlyIn", "Details"]


def load(name, fetch):
    try:
        data = fetch(RAW + name)
        return data if isinstance(data, list) else []
    except Exception as e:  # keep deploying with what we have
        print(f"warning: could not load {name}: {e}", file=sys.stderr)
        return []


def http_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "365Bytes-build"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.load(r)


def source_of(rec):
    s = (rec.get("Source") or "").strip()
    if s:
        return s
    i = rec.get("Id", "")
    return "roadmap" if i.startswith("RM") else "azure" if i.startswith("AZ") else "messageCenter"


def slim(rec):
    out = {k: rec[k] for k in KEEP if rec.get(k) not in (None, "", [])}
    out["Source"] = source_of(rec)
    body = rec.get("Body") or {}
    if body.get("Content"):
        out["Body"] = body["Content"]
    return out


def summary(rec):
    for d in rec.get("Details") or []:
        if d.get("Name") == "Summary" and d.get("Value"):
            return str(d["Value"])
    return ""


def build(out_dir, fetch=http_json):
    out = Path(out_dir)
    posts = out / "posts"
    posts.mkdir(parents=True, exist_ok=True)
    records = {}
    for name in SOURCES:
        for rec in load(name, fetch):
            i = str(rec.get("Id") or "")
            if not ID_RE.match(i):
                continue
            old = records.get(i)
            if not old or (rec.get("LastModifiedDateTime") or "") >= (old.get("LastModifiedDateTime") or ""):
                records[i] = rec
    for i, rec in records.items():
        (posts / f"{i}.json").write_text(json.dumps(slim(rec), ensure_ascii=False), encoding="utf-8")

    def when(r):
        return r.get("LastModifiedDateTime") or r.get("StartDateTime") or ""

    newest = sorted(records.values(), key=when, reverse=True)[:LATEST]
    latest = [{"Id": r["Id"], "Title": r.get("Title") or r["Id"], "Source": source_of(r),
               "Services": r.get("Services") or [], "Updated": when(r)} for r in newest]
    (out / "latest.json").write_text(json.dumps(latest, ensure_ascii=False), encoding="utf-8")
    print(f"mc-data: wrote {len(records)} posts, {len(latest)} in latest.json")
    return len(records)


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else "site/mc-data")
