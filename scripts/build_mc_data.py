"""Build per-post JSON for the Message Center reader.

Keeps our own archive of every post seen (MC_ARCHIVE, a gzipped JSON file restored from the
workflow cache and saved back after each run) and writes:
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
O=Mobile, T=Teams and Surface Devices). Fresh data is merged into the archive, so posts that age out of Microsoft's feeds stay
available. If there is no archive yet (first run or an evicted cache) it is seeded once from
github.com/merill/mc (MIT); after that nothing is read from it.

The tenant ID, app ID and any terms in MC_REDACT (comma separated) are scrubbed from
everything written to the site.

Runs after `mkdocs build` in the deploy workflow. A download failure never
fails the deploy: the reader falls back to the source site.
"""
import gzip
import html
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

SEED = "https://raw.githubusercontent.com/merill/mc/main/@data/"  # one-time seed only
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


PROBLEMS = {}  # source -> short error, reported as a GitHub issue by report_problems()


def load(name, fetch):
    """One source file of the seed archive."""
    try:
        data = fetch(SEED + name)
        return data if isinstance(data, list) else []
    except Exception as e:  # keep deploying with what we have
        PROBLEMS[f"seed {name}"] = describe_error(e)
        print(f"warning: could not load {name}: {describe_error(e)}", file=sys.stderr)
        return []


RETRY_CODES = (429, 500, 502, 503, 504)


def open_json(req, timeout=120, attempts=3, sleep=time.sleep):
    """urlopen + JSON, retrying busy answers and network errors after 2 s, then 4 s."""
    for attempt in range(1, attempts + 1):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code not in RETRY_CODES or attempt == attempts:
                raise
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            if attempt == attempts:
                raise
        sleep(2 ** attempt)


def http_json(url):
    return open_json(urllib.request.Request(
        url, headers={"User-Agent": "365Bytes-build", "Accept": "application/json"}))


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
        except Exception as e:  # the archive keeps its copy for this source
            PROBLEMS[f"Microsoft {kind} feed"] = describe_error(e)
            print(f"warning: Microsoft {kind} feed unavailable, keeping archived data: {describe_error(e)}",
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


EMAIL_RE = re.compile(r"[\w.+'-]+@[\w-]+(?:\.[\w-]+)+")
GUID_RE = re.compile(r"\b[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}\b", re.I)


def scrub_pii(rec):
    """Service health text is free-form and tenant specific: drop email addresses and GUIDs."""
    text = json.dumps(rec, ensure_ascii=False)
    text = EMAIL_RE.sub("[email]", text)
    text = GUID_RE.sub("[id]", text)
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
    assertion = open_json(req, timeout=60)["value"]
    body = urllib.parse.urlencode({
        "grant_type": "client_credentials",
        "client_id": client,
        "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
        "client_assertion": assertion,
        "scope": f"https://{info['graph_host']}/.default",
    }).encode()
    req = urllib.request.Request(info["token_endpoint"], data=body,
                                 headers={"User-Agent": "365Bytes-build"})
    return open_json(req, timeout=60)["access_token"]


def graph_pages(token, path, fetch=None, host="graph.microsoft.com"):
    url = f"https://{host}/v1.0/admin/serviceAnnouncement/" + path
    while url:
        if fetch:
            data = fetch(url)
        else:
            req = urllib.request.Request(url, headers={
                "Authorization": f"Bearer {token}", "User-Agent": "365Bytes-build"})
            data = open_json(req)
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
                health = [scrub_pii(from_issue(i))
                          for i in graph_pages(token, "issues?$top=100", fetch, info["graph_host"])]
        except Exception as e:  # skip this tenant; the archive still covers the posts
            PROBLEMS[f"Graph tenant {n} of {len(tenants)}"] = f"{stage}: {describe_error(e)}"
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


def platform_id(rec):
    """Give an archive roadmap record the same platform-suffixed ID the official feed uses,
    so an item keeps its ID when it ages out of the official feed's time window."""
    m = re.fullmatch(r"RM(\d+)", str(rec.get("Id") or ""))
    if not m:
        return rec
    names = next((d.get("Value") for d in rec.get("Details") or [] if d.get("Name") == "Platforms"), "")
    suffix = platform_suffix([p.strip() for p in str(names or "").split(",") if p.strip()])
    return {**rec, "Id": f"RM{m.group(1)}-{suffix}"} if suffix else rec


ISSUE_TITLE = "Message Center data: a source is failing"


def report_problems(problems, api=None):
    """Keep one GitHub issue in step with the failing sources: open or update it while any
    source fails, close it once everything works. Skipped outside Actions and on pull requests."""
    token, repo = os.environ.get("GITHUB_TOKEN"), os.environ.get("GITHUB_REPOSITORY")
    if api is None:
        if not (token and repo) or os.environ.get("GITHUB_EVENT_NAME") == "pull_request":
            return
        def api(method, path, data=None):
            req = urllib.request.Request(
                f"https://api.github.com/repos/{repo}/{path}", method=method,
                data=json.dumps(data).encode() if data is not None else None,
                headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json",
                         "User-Agent": "365Bytes-build"})
            return open_json(req, timeout=30)
    try:
        existing = next((i for i in api("GET", "issues?state=open&per_page=100")
                         if i.get("title") == ISSUE_TITLE and "pull_request" not in i), None)
        if problems:
            lines = "\n".join(f"- **{k}**: `{v}`" for k, v in sorted(problems.items()))
            body = ("The Message Center page is keeping archived data (or has missing data) for these sources "
                    f"on the latest deploy:\n\n{lines}\n\nThis issue updates itself and closes when "
                    "every source works again. Details are in the \"Deploy docs\" run log.")
            if existing:
                if existing.get("body") != body:
                    api("PATCH", f"issues/{existing['number']}", {"body": body})
            else:
                api("POST", "issues", {"title": ISSUE_TITLE, "body": body})
        elif existing:
            api("POST", f"issues/{existing['number']}/comments", {"body": "All sources work again."})
            api("PATCH", f"issues/{existing['number']}", {"state": "closed", "state_reason": "completed"})
    except Exception as e:  # alerting must never fail the deploy
        print(f"warning: could not update the status issue: {describe_error(e)}", file=sys.stderr)


def read_archive(path):
    try:
        with gzip.open(path, "rt", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (OSError, ValueError):
        return []


def write_archive(path, records):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".tmp")
    with gzip.open(tmp, "wt", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False)
    tmp.replace(p)


def build(out_dir, fetch=http_json, graph=graph_records, official=official_records, archive_path=None):
    out = Path(out_dir)
    posts = out / "posts"
    posts.mkdir(parents=True, exist_ok=True)
    PROBLEMS.clear()
    records = {}
    stored = read_archive(archive_path) if archive_path else []
    if stored:
        batches = [stored]
    else:
        print("mc-data: no archive yet, seeding it once from github.com/merill/mc")
        batches = [load(name, fetch) for name in SOURCES]
    for batch in batches:
        for rec in map(platform_id, batch):
            i = str(rec.get("Id") or "")
            if not ID_RE.match(i):
                continue
            old = records.get(i)
            if not old or (rec.get("LastModifiedDateTime") or "") >= (old.get("LastModifiedDateTime") or ""):
                records[i] = rec
    # Fresh Microsoft data wins over the archived copy.
    microsoft = list(official(fetch)) + list(graph())
    fresh_roadmap = {m.group(1) for r in microsoft
                     if (m := re.match(r"RM(\d+)", str(r.get("Id") or "")))}
    for i in [i for i in records if (m := re.fullmatch(r"RM(\d+)(?:-[A-Z]+)?", i)) and m.group(1) in fresh_roadmap]:
        del records[i]  # the official copy replaces it, even if its platforms changed
    for rec in microsoft:
        i = str(rec.get("Id") or "")
        if ID_RE.match(i):
            records[i] = rec
    terms = redact_terms()
    records = {i: scrub(rec, terms) for i, rec in records.items()}
    if archive_path:
        write_archive(archive_path, list(records.values()))
    for i, rec in records.items():
        text = json.dumps(slim(rec), ensure_ascii=False)
        (posts / f"{i}.json").write_text(text, encoding="utf-8")
        plain = re.fullmatch(r"(RM\d+)-[A-Z]+", i)
        if plain:  # Message Center posts link to the bare roadmap ID
            (posts / f"{plain.group(1)}.json").write_text(text, encoding="utf-8")

    def when(r):
        return r.get("LastModifiedDateTime") or r.get("StartDateTime") or ""

    newest = sorted(records.values(), key=when, reverse=True)[:LATEST]
    def entry(r):
        return {"Id": r["Id"], "Title": r.get("Title") or r["Id"], "Source": source_of(r),
                "Services": r.get("Services") or [], "Updated": when(r)}

    latest = [entry(r) for r in newest]
    everything = [entry(r) for r in sorted(records.values(), key=when, reverse=True)]
    (out / "latest.json").write_text(json.dumps(latest, ensure_ascii=False), encoding="utf-8")
    (out / "index.json").write_text(json.dumps(everything, ensure_ascii=False), encoding="utf-8")  # search
    print(f"mc-data: wrote {len(records)} posts, {len(latest)} in latest.json")
    return len(records)


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else "site/mc-data",
          archive_path=os.environ.get("MC_ARCHIVE") or None)
    report_problems(dict(PROBLEMS))
