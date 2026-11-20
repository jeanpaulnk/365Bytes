"""Build per-post JSON for the Message Center reader.

Downloads the public data from github.com/merill/mc (MIT) and writes:
  <out>/posts/<ID>.json  one file per active Message Center, Roadmap and Azure post
  <out>/latest.json      the newest posts, for the list on the Message Center page

When MC_TENANTS (or MC_TENANT_ID) and MC_CLIENT_ID are set and the job has an OIDC
token (permissions: id-token: write), Message Center posts and Service health issues
are read directly from Microsoft Graph (admin/serviceAnnouncement) and replace the
archive copies. MC_TENANTS is "tenant[:clientId],..." where a tenant is a GUID or a
domain; each is resolved (GUID and cloud endpoints) from its public OpenID discovery
document. Message Center posts are merged across all tenants, Service health comes only
from the first one, and tenants are never named in the published data. Roadmap and Azure Updates posts are read from Microsoft's public
release-communications API (no credentials); roadmap IDs carry a platform suffix, for
example RM564615-WDI (W=Web, D=Desktop, M=Mac, I=iOS, A=Android, L=Linux, V=Developer,
O=Mobile, T=Teams and Surface Devices). The archive stays as the fallback for every source.

The tenant ID, app ID and any terms in MC_REDACT (comma separated) are scrubbed from
everything written to the site.

Runs after `mkdocs build` in the deploy workflow. A download failure never
fails the deploy: the reader falls back to the source site.
"""
import html
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

RAW = "https://raw.githubusercontent.com/merill/mc/main/@data/"
AUDIENCES = {"microsoftonline.com": "api://AzureADTokenExchange",
             "microsoftonline.us": "api://AzureADTokenExchangeUSGov",
             "partner.microsoftonline.cn": "api://AzureADTokenExchangeChina"}
OFFICIAL = "https://www.microsoft.com/releasecommunications/api/v2/"
RECENT_DAYS = 180
PAGE = 100
MAX_PAGES = 60
PLATFORM_LETTERS = {"Web": "W", "Desktop": "D", "Mac": "M", "iOS": "I", "Android": "A",
                    "Linux": "L", "Developer": "V", "Mobile": "O",
                    "Teams and Surface Devices": "T"}
LETTER_ORDER = "WDMIALVOTX"
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
    req = urllib.request.Request(url, headers={"User-Agent": "365Bytes-build",
                                               "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.load(r)


def official_pages(kind, fetch):
    since = (datetime.now(timezone.utc) - timedelta(days=RECENT_DAYS)).strftime("%Y-%m-%dT%H:%M:%SZ")
    for page in range(MAX_PAGES):
        query = urllib.parse.urlencode(
            {"$top": PAGE, "$skip": page * PAGE, "$orderby": "modified desc",
             "$filter": f"modified gt {since}"}, quote_via=urllib.parse.quote)
        items = fetch(f"{OFFICIAL}{kind}?{query}").get("value", [])
        yield from items
        if len(items) < PAGE:
            return


def platform_suffix(platforms):
    letters = {PLATFORM_LETTERS.get(p, "X") for p in platforms or []}
    return "".join(c for c in LETTER_ORDER if c in letters)


def from_roadmap(i):
    platforms = i.get("platforms") or []
    suffix = platform_suffix(platforms)
    details = [{"Name": "Platforms", "Value": ", ".join(platforms)}] if platforms else []
    for name, key in (("GeneralAvailabilityDate", "generalAvailabilityDate"),
                      ("PreviewAvailabilityDate", "previewAvailabilityDate")):
        if i.get(key):
            details.append({"Name": name, "Value": i[key]})
    tags = [t for t in (i.get("tags") or []) + [i.get("status")] + (i.get("releaseRings") or []) if t]
    return {
        "Id": f"RM{i['id']}" + (f"-{suffix}" if suffix else ""), "Title": i.get("title"),
        "Source": "roadmap", "StartDateTime": i.get("created"),
        "LastModifiedDateTime": i.get("modified"), "Services": i.get("products") or [],
        "Tags": tags, "Details": details, "Body": {"Content": i.get("description") or ""},
    }


def from_azure(u):
    tags = [t for t in (u.get("tags") or []) + [u.get("status")] if t]
    return {
        "Id": f"AZ{u['id']}", "Title": u.get("title"), "Source": "azure",
        "StartDateTime": u.get("created"), "LastModifiedDateTime": u.get("modified"),
        "Services": u.get("products") or [], "Tags": tags,
        "Details": [{"Name": "AzureLink",
                     "Value": f"https://azure.microsoft.com/updates?id={u['id']}"}],
        "Body": {"Content": u.get("description") or ""},
    }


def official_records(fetch=http_json):
    """Roadmap and Azure Updates straight from Microsoft; a failed source is skipped."""
    out = []
    for kind, convert in (("m365", from_roadmap), ("azure", from_azure)):
        try:
            recs = [convert(i) for i in official_pages(kind, fetch) if str(i.get("id") or "").isdigit()]
            print(f"mc-data: read {len(recs)} {kind} records from Microsoft")
            out += recs
        except Exception as e:  # keep the archive copy for this source
            print(f"warning: Microsoft {kind} feed unavailable, using archive data: {e}",
                  file=sys.stderr)
    return out


LOOKED_UP = set()  # tenant IDs/domains found by lookup_tenant; scrubbed from the output


def parse_tenants():
    """MC_TENANTS="tenant[:clientId],..." (falls back to MC_TENANT_ID); the first is primary."""
    raw = os.environ.get("MC_TENANTS") or os.environ.get("MC_TENANT_ID") or ""
    default_client = os.environ.get("MC_CLIENT_ID")
    out = []
    for item in raw.split(","):
        tenant, _, client = item.strip().partition(":")
        tenant, client = tenant.strip(), client.strip() or default_client
        if tenant and client:
            out.append((tenant, client))
    return out


def redact_terms():
    terms = [os.environ.get("MC_TENANT_ID"), os.environ.get("MC_CLIENT_ID")]
    terms += [x for pair in parse_tenants() for x in pair]
    terms += LOOKED_UP
    terms += (os.environ.get("MC_REDACT") or "").split(",")
    return sorted({t.strip() for t in terms if t and len(t.strip()) >= 3}, key=len, reverse=True)


def scrub(rec, terms):
    if not terms:
        return rec
    text = json.dumps(rec, ensure_ascii=False)
    for t in terms:
        text = re.sub(re.escape(json.dumps(t)[1:-1]), "[redacted]", text, flags=re.I)
    return json.loads(text)


def lookup_tenant(tenant, fetch=http_json):
    """Tenant GUID and cloud endpoints from the public OpenID discovery document."""
    cfg = fetch(f"https://login.microsoftonline.com/{tenant}/v2.0/.well-known/openid-configuration")
    m = re.search(r"/([0-9a-fA-F-]{36})/", cfg.get("issuer") or "")
    if not m:
        raise ValueError("tenant not found")
    cloud = cfg.get("cloud_instance_name") or "microsoftonline.com"
    info = {"id": m.group(1), "token_endpoint": cfg["token_endpoint"],
            "graph_host": cfg.get("msgraph_host") or "graph.microsoft.com",
            "audience": AUDIENCES.get(cloud, AUDIENCES["microsoftonline.com"])}
    LOOKED_UP.update({tenant, info["id"]})
    return info


def graph_token(info, client):
    """App-only Graph token via the GitHub OIDC federated credential (no stored secret)."""
    req_url = os.environ.get("ACTIONS_ID_TOKEN_REQUEST_URL")
    req_token = os.environ.get("ACTIONS_ID_TOKEN_REQUEST_TOKEN")
    if not (client and req_url and req_token):
        return None
    req = urllib.request.Request(
        req_url + "&audience=" + urllib.parse.quote(info["audience"], safe=""),
        headers={"Authorization": f"Bearer {req_token}", "User-Agent": "365Bytes-build"})
    with urllib.request.urlopen(req, timeout=60) as r:
        assertion = json.load(r)["value"]
    body = urllib.parse.urlencode({
        "grant_type": "client_credentials",
        "client_id": client,
        "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
        "client_assertion": assertion,
        "scope": f"https://{info['graph_host']}/.default",
    }).encode()
    req = urllib.request.Request(info["token_endpoint"], data=body,
                                 headers={"User-Agent": "365Bytes-build"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)["access_token"]


def graph_pages(token, path, fetch=None, host="graph.microsoft.com"):
    url = f"https://{host}/v1.0/admin/serviceAnnouncement/" + path
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


def describe_error(e):
    """The error and AADSTS/Graph codes only; the response text can name tenants, so it is not logged."""
    if not isinstance(e, urllib.error.HTTPError):
        return f"{type(e).__name__}: {e}"
    detail = ""
    try:
        body = json.loads(e.read().decode("utf-8", "replace"))
        err = body.get("error")
        code = (err.get("code") if isinstance(err, dict) else err) or ""
        codes = ",".join(f"AADSTS{c}" for c in body.get("error_codes") or [])
        detail = " ".join(x for x in (code, codes) if x)
    except Exception:
        pass
    return f"HTTP {e.code} {detail}".strip()


def graph_records(tenants=None, fetch=None, lookup=lookup_tenant, token_for=graph_token):
    """Message Center posts from every configured tenant and Service health from the primary one.

    Tenants are only ever referred to by number: the published data says how many of the
    tenants checked saw a post, never which ones.
    """
    tenants = parse_tenants() if tenants is None else tenants
    merged, seen, health, reached = {}, {}, [], 0
    for n, (tenant, client) in enumerate(tenants, 1):
        stage = "lookup"
        try:
            info = lookup(tenant)
            stage = "token"
            token = token_for(info, client)
            if not token and not fetch:
                raise RuntimeError("no OIDC token (id-token permission or credential missing)")
            stage = "messages"
            posts = [from_message(m) for m in graph_pages(token, "messages?$top=100", fetch, info["graph_host"])]
            if n == 1:  # incidents are tenant specific, so only the primary tenant contributes
                stage = "issues"
                health = [from_issue(i) for i in graph_pages(token, "issues?$top=100", fetch, info["graph_host"])]
        except Exception as e:  # skip this tenant; the archive still covers the posts
            print(f"warning: tenant {n} of {len(tenants)} unavailable at {stage}: {describe_error(e)}",
                  file=sys.stderr)
            continue
        reached += 1
        for rec in posts:
            i = rec["Id"]
            seen[i] = seen.get(i, 0) + 1
            old = merged.get(i)
            if not old or (rec.get("LastModifiedDateTime") or "") >= (old.get("LastModifiedDateTime") or ""):
                merged[i] = rec
    if reached > 1:
        for i, rec in merged.items():
            rec["Details"] = (rec.get("Details") or []) + [
                {"Name": "SeenIn", "Value": f"{seen[i]} of {reached} tenants checked"}]
    out = list(merged.values()) + health
    if reached:
        print(f"mc-data: read {len(out)} records from Microsoft Graph ({reached} of {len(tenants)} tenants)")
    return out


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


def build(out_dir, fetch=http_json, graph=graph_records, official=official_records):
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
    # Microsoft's own data wins over the archive copy.
    microsoft = list(official(fetch)) + list(graph())
    fresh_roadmap = {m.group(1) for r in microsoft
                     if (m := re.match(r"RM(\d+)", str(r.get("Id") or "")))}
    for i in [i for i in records if (m := re.fullmatch(r"RM(\d+)", i)) and m.group(1) in fresh_roadmap]:
        del records[i]  # the archive copy has no platform suffix
    for rec in microsoft:
        i = str(rec.get("Id") or "")
        if ID_RE.match(i):
            records[i] = rec
    terms = redact_terms()
    for i, rec in records.items():
        text = json.dumps(slim(scrub(rec, terms)), ensure_ascii=False)
        (posts / f"{i}.json").write_text(text, encoding="utf-8")
        plain = re.fullmatch(r"(RM\d+)-[A-Z]+", i)
        if plain:  # Message Center posts link to the bare roadmap ID
            (posts / f"{plain.group(1)}.json").write_text(text, encoding="utf-8")

    def when(r):
        return r.get("LastModifiedDateTime") or r.get("StartDateTime") or ""

    newest = sorted(records.values(), key=when, reverse=True)[:LATEST]
    latest = [scrub({"Id": r["Id"], "Title": r.get("Title") or r["Id"], "Source": source_of(r),
                     "Services": r.get("Services") or [], "Updated": when(r)}, terms)
              for r in newest]
    (out / "latest.json").write_text(json.dumps(latest, ensure_ascii=False), encoding="utf-8")
    print(f"mc-data: wrote {len(records)} posts, {len(latest)} in latest.json")
    return len(records)


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else "site/mc-data")
