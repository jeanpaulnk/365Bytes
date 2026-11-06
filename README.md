# 365Bytes

Hands-on lab notes on Exchange Online, Outlook, Security & Compliance and Cloud identity, plus short,
automatically updated summaries of Microsoft's product blogs.

**Site:** https://jeanpaulnk.github.io/365Bytes/

## What's on the site

| Section | What it is |
|---|---|
| Transport, Exchange Online, Outlook, Identity, Tools | Hand-written lab notes and how-tos. |
| Message Center | Search and read Microsoft 365 Message Center, Microsoft 365 Roadmap and Azure Updates posts, powered by [mc.merill.net](https://mc.merill.net/). |
| Bytes from … | AI summaries of every new article on seven Microsoft blogs, added automatically (see below). |

## How the site is built

- [MkDocs](https://www.mkdocs.org/) with the [Material](https://squidfunk.github.io/mkdocs-material/) theme;
  configuration in `mkdocs.yml`, pages in `docs/`, theme overrides in `overrides/`.
- Published to GitHub Pages by `.github/workflows/docs.yml` ("Deploy docs"), which runs on every push to
  `main`, every 3 hours, and on demand.
- The deploy step also runs `scripts/build_mc_data.py`, which downloads the public Message Center data from
  [github.com/merill/mc](https://github.com/merill/mc) (MIT) and writes one small JSON file per post into the
  site (`/mc-data/`). The Message Center pages read those files in the browser.

### Preview locally

```bash
pip install mkdocs-material mkdocs-rss-plugin
mkdocs serve
```

Then open http://127.0.0.1:8000/365Bytes/. (The Message Center list needs the deployed `/mc-data/` files,
so it only fills on the live site.)

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
| Microsoft Defender for Office 365 Blog | `…board.id=MicrosoftDefenderforOffice365Blog` |
| Microsoft Purview Blog | `…board.id=microsoft-purview-blog` |
| Outlook Blog | `…board.id=Outlook` |
| Microsoft 365 Blog | `…board.id=microsoft_365blog` |
| Microsoft Entra Blog | `…board.id=microsoft-entra-blog` |
| Microsoft Security Blog | `https://www.microsoft.com/en-us/security/blog/feed/` |

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

`GITHUB_TOKEN` is provided by GitHub Actions automatically.

### Feed alerts

`data/feed-health.json` counts failed runs per blog. When a feed fails (unreachable, not a feed, or no
articles) on **3 runs in a row** (about 9 hours), the job opens a GitHub issue, assigned to and
@mentioning the repository owner, with the feed address, the last error and how to fix it. The issue
closes itself when the feed works again.

### Files

| Path | Purpose |
|---|---|
| `scripts/exchange_blog.py` | The job: feeds, AI summaries, posts, list pages, alerts. |
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
