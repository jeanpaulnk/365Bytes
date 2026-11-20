# 365Bytes

Hands-on lab notes on Exchange Online, Outlook, Security & Compliance and Cloud identity, plus short,
automatically updated summaries of Microsoft's product blogs.

**Site:** https://jeanpaulnk.github.io/365Bytes/

## What's on the site

| Section | What it is |
|---|---|
| Transport, Exchange Online, Outlook, Identity, Tools | Hand-written lab notes and how-tos. |
| Message Center | Search and read Microsoft 365 Message Center, Service health, Microsoft 365 Roadmap and Azure Updates posts, read directly from Microsoft (see [Message Center data](#message-center-data)). [mc.merill.net](https://mc.merill.net/) is the fallback. |
| Bytes from … | AI summaries of every new article on seven Microsoft blogs, added automatically (see below). |

## How the site is built

- [MkDocs](https://www.mkdocs.org/) with the [Material](https://squidfunk.github.io/mkdocs-material/) theme;
  configuration in `mkdocs.yml`, pages in `docs/`, theme overrides in `overrides/`.
- Published to GitHub Pages by `.github/workflows/docs.yml` ("Deploy docs"), which runs on every push to
  `main`, every 3 hours, and on demand.
- The deploy step also runs `scripts/build_mc_data.py`, which collects Message Center, Service health,
  Roadmap and Azure Updates posts and writes one small JSON file per post into the site (`/mc-data/`).
  The Message Center pages read those files in the browser. Details are in
  [Message Center data](#message-center-data).

### Preview locally

```bash
pip install mkdocs-material mkdocs-rss-plugin
mkdocs serve
```

Then open http://127.0.0.1:8000/365Bytes/. (The Message Center list needs the deployed `/mc-data/` files,
so it only fills on the live site.)

## Message Center data

`scripts/build_mc_data.py` runs in the deploy workflow (every 3 hours and on every push to `main`).

| Content | Source | Credentials |
|---|---|---|
| Message Center posts (`MC…`) from one or more tenants, and Service health issues from the first tenant | Microsoft Graph `admin/serviceAnnouncement` (`messages`, `issues`) | Entra app with a GitHub OIDC federated credential; no client secret |
| Microsoft 365 Roadmap (`RM…`) | `microsoft.com/releasecommunications/api/v2/m365` | None (public) |
| Azure Updates (`AZ…`) | `microsoft.com/releasecommunications/api/v2/azure` | None (public) |
| Fallback for all of the above | [github.com/merill/mc](https://github.com/merill/mc) (MIT) | None |

Roadmap and Azure data is limited to items modified in the last 180 days; older archive roadmap items get the
same platform suffix from the archive's own `Platforms` field, so an ID never changes when an item ages out.
A source that fails or isn't configured falls back to the archive, so the deploy never fails because of it.

Busy answers (429, 5xx) and network errors are retried twice (after 2 s and 4 s). If a source still fails, the
deploy opens a single issue, "Message Center data: a source is failing", listing the failing sources and the
HTTP or AAD error code. The issue updates itself and closes when everything works again. Pull-request builds
never touch issues and never receive the Graph secrets.

### Roadmap IDs

Roadmap IDs end with the platforms the feature ships on, for example `RM564615-WDI`:

| Letter | Platform | Letter | Platform |
|---|---|---|---|
| W | Web | L | Linux |
| D | Desktop | V | Developer |
| M | Mac | O | Mobile |
| I | iOS | T | Teams and Surface Devices |
| A | Android | X | Any other platform |

Letters always appear in the order `W D M I A L V O T X`. The bare ID (`RM564615`) still opens the same post.

### Microsoft Graph setup

1. Register an Entra app (single tenant, or multi-tenant if you add [more tenants](#several-tenants)) with the **application** permissions `ServiceMessage.Read.All` and
   `ServiceHealth.Read.All`, and grant admin consent.
2. Add a federated credential: issuer `https://token.actions.githubusercontent.com`, audience
   `api://AzureADTokenExchange`, subject `repo:jeanpaulnk@165971893/365Bytes@1437785275:ref:refs/heads/main`.
   This repository uses GitHub's immutable OIDC subject (owner and repository IDs instead of names); check
   yours with `gh api repos/jeanpaulnk/365Bytes/actions/oidc/customization/sub`. A name-based subject fails
   with `AADSTS700213`. Pull-request builds don't match the credential, so they use the archive.
3. Add the repository secrets below. Without them the Graph source is simply skipped.

### Several tenants

Message Center posts differ between tenants (license, region, features). To collect more of them, set
`MC_TENANTS` to a comma-separated list of `tenant[:clientId]`, where a tenant is a GUID or a domain such as
`contoso.onmicrosoft.com`, for example `dev.onmicrosoft.com,other.onmicrosoft.com:<its-app-id>`.

- Each tenant is resolved from its public OpenID discovery document
  (`login.microsoftonline.com/<tenant>/v2.0/.well-known/openid-configuration`), which gives its GUID, token
  endpoint and Graph host. This is the same information as the
  [Tenant Lookup tool](https://gettenantpartitionweb.azurewebsites.net/).
- The app must be multi-tenant and an admin of every extra tenant must grant consent to the two permissions.
  Only add tenants you control or have permission to read; the app can read their announcements only.
- A tenant without a `:clientId` uses `MC_CLIENT_ID`. Use a per-tenant client ID for a tenant in another cloud.
- Message Center posts are merged across tenants and show "Seen in N of M tenants checked". Service health
  issues come only from the first (primary) tenant, because incidents are tenant specific.
- A tenant that can't be reached is skipped with a numbered warning; the rest still work.
- US Government and China tenants use their own Graph host and token audience (taken from the lookup), but this
  path has not been tested.

### Privacy

The tenant IDs, domains, app IDs (including the GUIDs found by the lookup) and any terms listed in
`MC_REDACT` are scrubbed from everything written to the published site. Tenants are only ever shown as
counts, never named, and logs refer to them by number. The identifiers are stored as secrets (masked in
Actions logs) and are never committed. Service health text can still contain tenant-specific wording, so
review what appears on the Message Center page.

## "Bytes from Microsoft blogs" automation

`.github/workflows/exchange-blog.yml` runs `scripts/exchange_blog.py` every 3 hours. For each blog it:

1. Reads the blog's RSS feed.
2. Takes articles published in the last 14 days that it hasn't handled before (at most 3 per blog per run).
3. Skips conference and event announcements (titles with words like conference, ESPC, Ignite, webinar, AMA,
   summit, RSAC; the AI also flags event posts whose titles don't give it away).
4. Writes a post to `docs/Bytes-from-<Blog>/`: title, publication date, summary, key points, an
   "Action required" box when relevant, a link to the original article and an AI disclaimer.
5. Rebuilds that section's list page, commits, and starts "Deploy docs".

### Blogs followed

| Section | Feed |
|---|---|
| Exchange Team Blog | `techcommunity.microsoft.com/…/rss/board?board.id=exchange` |
| Microsoft Defender Blog | `…board.id=MicrosoftThreatProtectionBlog` (replaces the Defender for Office 365 blog, whose feed Microsoft emptied; its earlier posts stay on the site) |
| Microsoft Purview Blog | `…board.id=microsoft-purview-blog` |
| Outlook Blog | `…board.id=Outlook` |
| Microsoft 365 Blog | `…board.id=microsoft_365blog` |
| Microsoft Entra Blog | `…board.id=microsoft-entra-blog` |
| Microsoft Security Blog | `https://www.microsoft.com/en-us/security/blog/feed/` |
| Microsoft Copilot Blog | `https://www.microsoft.com/en-us/copilot/blog/wp-json/wp/v2/posts` (WordPress API, because its RSS feed is out of date) |
The list lives in `SOURCES` at the top of `scripts/exchange_blog.py`.

### Who writes the summaries

The first one that works is used:

1. **Google Gemini** (free Gemini API tier): `gemini-flash-lite-latest`, then `gemini-flash-latest`, then
   `gemini-3.5-flash-lite`. Busy answers (429/5xx) are retried once.
2. **GitHub Copilot** (Copilot CLI, works with Copilot Free) as the backup.
3. If both fail, the post shows the article's opening lines instead.

The model used for each post is recorded in `data/exchange-blog-state.json`; it is not shown on the site.

### Secrets

Set in **Settings → Secrets and variables → Actions → Repository secrets**. Never commit them.

| Secret | Used for | How to get it |
|---|---|---|
| `BYTES365_GEMINI_API_KEY` (or `GEMINI_API_KEY`) | Gemini summaries | [aistudio.google.com/apikey](https://aistudio.google.com/apikey) |
| `COPILOT_GITHUB_TOKEN` | Copilot backup summaries | Fine-grained personal access token with the **Copilot Requests** account permission. Expires: renew it under the same name. |
| `AI_API_KEY` + variables `AI_ENDPOINT`, `AI_MODEL` | Optional: any other OpenAI-compatible model instead of Gemini | Your provider |
| `MC_TENANT_ID`, `MC_CLIENT_ID` | Optional: read Message Center and Service health from Microsoft Graph | Entra tenant ID and the app (client) ID from [Microsoft Graph setup](#microsoft-graph-setup) |
| `MC_TENANTS` | Optional: several tenants, `tenant[:clientId],...` (replaces `MC_TENANT_ID`; first is primary) | See [Several tenants](#several-tenants) |
| `MC_REDACT` | Optional: comma-separated terms (for example a tenant name) removed from the published data | Your choice |

`GITHUB_TOKEN` is provided by GitHub Actions automatically.

### LinkedIn posts

After each run, `scripts/linkedin_post.py` shares the new summaries on LinkedIn (needs the `LINKEDIN_*`
secrets; without them it does nothing). Every summary is still published on the site; LinkedIn is selective:

- **Priority topics always go, first:** posts in the Exchange Team and Outlook sections, and any post whose
  title, summary or key points mention Exchange (Online, Server, hybrid), Outlook, EWS, OWA or mailboxes.
- **Everything else is limited** to `LINKEDIN_OTHER_LIMIT` posts per run (default 2; set it as a repository
  variable, `0` means none); the rest stay site-only and are listed as "skipped" in the run log.
- Posting a file by hand (the `linkedin_file` input) always posts it.

The keyword list is `PRIORITY_TOPICS` and the sections are `PRIORITY_SECTIONS` in the script.

### Feed alerts

`data/feed-health.json` counts failed runs per blog. When a feed fails (unreachable, not a feed, or no
articles) on **3 runs in a row** (about 9 hours), the job opens a GitHub issue, assigned to and
@mentioning the repository owner, with the feed address, the last error and how to fix it. The issue
closes itself when the feed works again.

### Files

| Path | Purpose |
|---|---|
| `scripts/exchange_blog.py` | The job: feeds, AI summaries, posts, list pages, alerts. |
| `scripts/build_mc_data.py` | Builds the Message Center post files at deploy time (Graph, Microsoft feeds, archive fallback, redaction). |
| `data/exchange-blog-state.json` | Every article already handled (posted or skipped), so nothing is posted twice. |
| `data/feed-health.json` | Consecutive failures per blog and any open alert issue. |
| `docs/Bytes-from-*/` | The generated posts and each section's `index.md` list. |

### Running it by hand

**Actions → Bytes from Microsoft blogs → Run workflow** does a normal run.

Special runs are started with a `repository_dispatch` event of type `exchange-blog`, for example with the
[GitHub CLI](https://cli.github.com/):

```bash
# Summarise the newest article with each AI and report it in the run log; publishes nothing
echo '{"event_type":"exchange-blog","client_payload":{"test":"true"}}' | gh api repos/jeanpaulnk/365Bytes/dispatches --input -
```

| `client_payload` | What it does |
|---|---|
| `{"test": "true"}` | Test the AI summaries without publishing. |
| `{"alert_test": "true"}` | Open and immediately close a test alert issue. |
| `{"backfill_days": "60", "source": "Entra"}` | One-off catch-up: post the newest 3 articles from the last 60 days for one blog. |
| `{"rewrite": "true"}` | Rewrite posts that only show opening lines with AI summaries. |

### Common changes

- **Add a blog:** add an entry to `SOURCES` (`name`, plus `board` for a Tech Community blog or `feed` for any
  other RSS feed, and `home`), and add a section to `docs/index.md`. The job creates the folder and list page.
- **A blog moved (alert issue opened):** find the blog's new RSS feed and update its entry in `SOURCES`.
- **Remove a post:** delete its file under `docs/Bytes-from-…/` and remove its row from that folder's
  `index.md`. Leave its entry in `data/exchange-blog-state.json` so it is not posted again.
- **Change what counts as an event:** edit `EVENT_TITLE` in `scripts/exchange_blog.py`.

### Keep in mind

- GitHub pauses scheduled workflows after 60 days without repository activity. The job's own commits
  normally prevent that; if posts stop, check the **Actions** tab.
- Summaries are AI-generated. Each post links to the original; check it before acting.
- Some feeds give an article's last-updated date rather than its first-published date.

## License

- **Code** (scripts, workflows, JavaScript, stylesheets, theme overrides and configuration): MIT, see
  [`LICENSE`](LICENSE).
- **Written content** (lab notes and other pages I wrote): CC BY 4.0, see
  [`LICENSE-CONTENT.md`](LICENSE-CONTENT.md).
- **Not covered:** the `Bytes from …` summaries and Message Center content, which come from Microsoft's
  articles and data; third-party images and trademarks.
- **Third-party work** used here, including the Message Center data by Merill Fernando (MIT): see
  [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).
