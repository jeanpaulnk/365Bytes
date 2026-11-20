"""Build per-post JSON for the Message Center reader.

Downloads the public data from github.com/merill/mc (MIT) and writes:
  <out>/posts/<ID>.json  one file per active Message Center, Roadmap and Azure post
  <out>/latest.json      the newest posts, for the list on the Message Center page

When MC_TENANT_ID and MC_CLIENT_ID are set and the job has an OIDC token
(permissions: id-token: write), Message Center posts and Service health issues
are read directly from Microsoft Graph (admin/serviceAnnouncement) and replace
the archive copies. Roadmap and Azure posts still come from the archive.

Runs after `mkdocs build` in the deploy workflow. A download failure never
fails the deploy: the reader falls back to the source site.
"""
import html
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

RAW = "https://raw.githubusercontent.com/merill/mc/main/@data/"
GRAPH = "https://graph.microsoft.com/v1.0/admin/serviceAnnouncement/"
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


def graph_token():
    """App-only Graph token via the GitHub OIDC federated credential (no stored secret)."""
    tenant = os.environ.get("MC_TENANT_ID")
    client = os.environ.get("MC_CLIENT_ID")
    req_url = os.environ.get("ACTIONS_ID_TOKEN_REQUEST_URL")
    req_token = os.environ.get("ACTIONS_ID_TOKEN_REQUEST_TOKEN")
    if not (tenant and client and req_url and req_token):
        return None
    req = urllib.request.Request(
        req_url + "&audience=api://AzureADTokenExchange",
        headers={"Authorization": f"Bearer {req_token}", "User-Agent": "365Bytes-build"})
    with urllib.request.urlopen(req, timeout=60) as r:
        assertion = json.load(r)["value"]
    body = urllib.parse.urlencode({
        "grant_type": "client_credentials",
        "client_id": client,
        "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
        "client_assertion": assertion,
        "scope": "https://graph.microsoft.com/.default",
    }).encode()
    req = urllib.request.Request(
        f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token", data=body,
        headers={"User-Agent": "365Bytes-build"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)["access_token"]


def graph_pages(token, path, fetch=None):
    url = GRAPH + path
    while url:
        if fetch:
            data = fetch(url)
        else:
            req = urllib.request.Request(url, headers={
                "Authorization": f"Bearer {token}", "User-Agent": "365Bytes-build"})
            with urllib.request.urlopen(req, timeout=120) as r:
                data = json.load(r)
        yield from data.get("value", [])
        url = data.get("@odata.nextLink")


def from_message(m):
    body = (m.get("body") or {})
    content = body.get("content") or ""
    if body.get("contentType") == "text":
        content = "<p>" + html.escape(content).replace("\n", "<br>") + "</p>"
    return {
        "Id": m.get("id"), "Title": m.get("title"), "Source": "messageCenter",
        "Category": m.get("category"), "Severity": m.get("severity"),
        "IsMajorChange": m.get("isMajorChange"), "StartDateTime": m.get("startDateTime"),
        "LastModifiedDateTime": m.get("lastModifiedDateTime"), "EndDateTime": m.get("endDateTime"),
        "ActionRequiredByDateTime": m.get("actionRequiredByDateTime"),
        "Services": m.get("services"), "Tags": m.get("tags"),
        "Details": [{"Name": d.get("name"), "Value": d.get("value")} for d in m.get("details") or []],
        "Body": {"Content": content},
    }


def from_issue(i):
    parts = []
    if i.get("impactDescription"):
        parts.append("<p>" + html.escape(i["impactDescription"]).replace("\n", "<br>") + "</p>")
    for p in i.get("posts") or []:
        d = p.get("description") or {}
        text = d.get("content") or ""
        if d.get("contentType") == "text":
            text = "<p>" + html.escape(text).replace("\n", "<br>") + "</p>"
        parts.append(f"<h4>{html.escape(p.get('createdDateTime') or '')}</h4>{text}")
    return {
        "Id": i.get("id"), "Title": i.get("title"), "Source": "serviceHealth",
        "Category": i.get("classification"), "StartDateTime": i.get("startDateTime"),
        "LastModifiedDateTime": i.get("lastModifiedDateTime"), "EndDateTime": i.get("endDateTime"),
        "Services": [i["service"]] if i.get("service") else [],
        "Tags": [t for t in (i.get("status"), i.get("feature")) if t],
        "Body": {"Content": "".join(parts)},
    }


def graph_records(token=None, fetch=None):
    """Message Center posts and Service health issues straight from Microsoft Graph."""
    try:
        token = token or graph_token()
        if not token and not fetch:
            return []
        out = [from_message(m) for m in graph_pages(token, "messages?$top=100", fetch)]
        out += [from_issue(i) for i in graph_pages(token, "issues?$top=100", fetch)]
        print(f"mc-data: read {len(out)} records from Microsoft Graph")
        return out
    except Exception as e:  # fall back to the archive copy
        print(f"warning: Microsoft Graph unavailable, using archive data: {e}", file=sys.stderr)
        return []


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


def build(out_dir, fetch=http_json, graph=graph_records):
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
    for rec in graph():  # Microsoft's own data wins over the archive copy
        i = str(rec.get("Id") or "")
        if ID_RE.match(i):
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
