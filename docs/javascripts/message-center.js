// Message Center pages: latest-posts list, ID lookup, and an on-site reader.
// Post data is built into /mc-data/ at deploy time (scripts/build_mc_data.py)
// from Microsoft Graph and the public release communications feed, merged into our own archive.
(function () {
  var SOURCE_LABEL = { messageCenter: "Message Center", roadmap: "Microsoft 365 Roadmap", azure: "Azure Updates" };

  var me = document.querySelector('script[src*="javascripts/message-center.js"]');
  var SITE = me ? new URL("../", me.src).href : location.origin + "/";
  var DATA = SITE + "mc-data/";
  var READER = SITE + "Message-Center/post/";

  function readerUrl(id) { return READER + "?id=" + encodeURIComponent(id); }
  function isId(v) { return /^(MC|RM|AZ)-?[\w-]+$/i.test(v) && /\d/.test(v); }
  function esc(t) {
    return String(t == null ? "" : t).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;", "'": "&#39;" }[c];
    });
  }
  function fmtDate(v) {
    var d = v ? new Date(v) : null;
    return d && !isNaN(d) ? d.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" }) : "";
  }
  function getJson(url) {
    return fetch(url).then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); });
  }

  // ---------- Go box ----------
  var form = document.getElementById("mc-go");
  if (form) {
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var v = document.getElementById("mc-go-input").value.trim();
      if (!v) return;
      if (isId(v)) location.href = readerUrl(v.toUpperCase().indexOf("AZ-") === 0 ? "AZ-" + v.slice(3) : v.toUpperCase());
      else {
        var f = document.getElementById("mc-filter");
        if (f) { f.value = v; f.dispatchEvent(new Event("input")); f.scrollIntoView({ behavior: "smooth", block: "center" }); }
      }
    });
  }

  // ---------- Latest posts list ----------
  var list = document.getElementById("mc-latest");
  if (list) {
    var all = [], full = null, src = "all";
    var render = function () {
      var pool = full || all;
      var q = document.getElementById("mc-filter").value.trim().toLowerCase();
      var rows = pool.filter(function (p) {
        if (src !== "all" && p.Source !== src) return false;
        return !q || (p.Title + " " + (p.Services || []).join(" ") + " " + p.Id).toLowerCase().indexOf(q) >= 0;
      }).slice(0, 30);
      document.getElementById("mc-posts").innerHTML = rows.map(function (p) {
        var tag = /^AZ-/i.test(p.Id) ? "" : '<span class="mc-id">' + esc(p.Id) + "</span>";
        var meta = [(p.Services || []).join(", "), fmtDate(p.Updated)].filter(Boolean).join(" · ");
        return "<li>" + tag + '<a href="' + esc(readerUrl(p.Id)) + '">' + esc(p.Title) + "</a>" +
          '<div class="mc-meta">' + esc(meta) + "</div></li>";
      }).join("");
      document.getElementById("mc-status").textContent = rows.length
        ? "Showing " + rows.length + " of the " + pool.length + (full ? " posts in the archive." : " most recently updated posts.")
        : "No posts match.";
    };
    list.querySelectorAll(".mc-tabs button").forEach(function (b) {
      b.addEventListener("click", function () {
        src = b.getAttribute("data-src");
        list.querySelectorAll(".mc-tabs button").forEach(function (x) { x.setAttribute("aria-pressed", x === b ? "true" : "false"); });
        render();
      });
    });
    var loadFull = function () {
      if (full) return;
      full = [];
      getJson(DATA + "index.json").then(function (d) { full = Array.isArray(d) ? d : []; render(); })
        .catch(function () { full = null; });
    };
    document.getElementById("mc-filter").addEventListener("input", function () {
      if (this.value.trim()) loadFull();
      render();
    });
    getJson(DATA + "latest.json")
      .then(function (d) { all = Array.isArray(d) ? d : []; render(); })
      .catch(function () {
        document.getElementById("mc-status").textContent = "Could not load the latest posts. Try again later.";
      });
  }

  // ---------- Reader ----------
  var box = document.getElementById("mc-post");
  if (!box) return;
  var id = (new URLSearchParams(location.search).get("id") || "").trim();
  if (id && !/^AZ-/i.test(id)) id = id.toUpperCase();
  var titleEl = document.getElementById("mc-title");
  var back = '<p><a href="' + esc(SITE + "Message-Center/") + '">&larr; All Message Center posts</a></p>';

  if (!id || !/^[A-Za-z0-9][A-Za-z0-9-]{1,120}$/.test(id)) {
    box.innerHTML = back + '<p>No post selected. Pick one from the <a href="' + esc(SITE + "Message-Center/") +
      '">Message Center page</a>, or open a link like <code>?id=MC1234567</code>.</p>';
    return;
  }

  getJson(DATA + "posts/" + id + ".json").then(show).catch(function () {
    if (titleEl) titleEl.textContent = id;
    box.innerHTML = back + '<div class="admonition warning"><p class="admonition-title">Not available here</p>' +
      "<p>This post could not be loaded on this site. It may be new, or older than the posts kept here.</p></div>";
  });

  function detail(m, name) {
    var d = (m.Details || []).filter(function (x) { return x && x.Name === name && x.Value; })[0];
    return d ? String(d.Value) : "";
  }
  function safeHref(u) { return /^https?:\/\//i.test(u || "") ? u : ""; }

  function show(m) {
    var source = m.Source || (/^RM/.test(id) ? "roadmap" : /^AZ/.test(id) ? "azure" : "messageCenter");
    var title = m.Title || id;
    if (titleEl) titleEl.textContent = title;
    document.title = title + " - " + (document.title.split(" - ").pop() || "JPN365Labs");

    var facts = [];
    var add = function (k, v) { if (v) facts.push("<tr><th>" + esc(k) + "</th><td>" + v + "</td></tr>"); };
    add("ID", /^AZ-/i.test(id) ? "" : "<code>" + esc(id) + "</code>");
    add("Source", esc(SOURCE_LABEL[source] || source));
    add("Services", esc((m.Services || []).join(", ")));
    add("Tags", esc((m.Tags || []).join(", ")));
    add("Status", esc([detail(m, "Status"), detail(m, "ReleasePhase")].filter(Boolean).join(" · ")));
    add("Platforms", esc(detail(m, "Platforms")));
    add("Seen in", esc(detail(m, "SeenIn")));
    add("Published", esc(fmtDate(m.StartDateTime)));
    add("Last updated", esc(fmtDate(m.LastModifiedDateTime)));
    add("Act by", esc(fmtDate(m.ActionRequiredByDateTime)));
    if (m.IsMajorChange) add("Major change", "Yes");
    var rm = detail(m, "RoadmapIds");
    if (rm) add("Roadmap", rm.split(/[,\s]+/).filter(Boolean).map(function (n) {
      return '<a href="' + esc(readerUrl("RM" + n.replace(/\D/g, ""))) + '">RM' + esc(n.replace(/\D/g, "")) + "</a>";
    }).join(", "));

    var summary = detail(m, "Summary");
    var rawBody = typeof m.Body === "string" ? m.Body : (m.Body && m.Body.Content) || "";
    var bodyHtml = sanitize(rawBody);
    if (!bodyHtml && summary) bodyHtml = sanitize(summary);

    // Source links: Microsoft's own page where there is one.
    var links = [];
    if (source === "messageCenter") links.push('<a class="md-button md-button--primary" href="https://admin.microsoft.com/#/MessageCenter/:/messages/' +
      encodeURIComponent(id) + '" target="_blank" rel="noopener">Open in your Microsoft 365 admin center</a>');
    if (source === "roadmap") links.push('<a class="md-button md-button--primary" href="https://www.microsoft.com/microsoft-365/roadmap?id=' +
      encodeURIComponent(id.replace(/\D/g, "")) + '" target="_blank" rel="noopener">Microsoft 365 Roadmap</a>');
    var azure = safeHref(detail(m, "AzureLink"));
    if (azure) links.push('<a class="md-button" href="' + esc(azure) + '" target="_blank" rel="noopener">Azure Updates</a>');
    var LINKS = { ExternalLink: "More information", HelpLink: "Help article", BlogLink: "Blog post" };
    Object.keys(LINKS).forEach(function (k) {
      var u = safeHref(detail(m, k));
      if (u) links.push('<a class="md-button" href="' + esc(u) + '" target="_blank" rel="noopener">' + LINKS[k] + "</a>");
    });

    box.innerHTML = back +
      (m.SeenOnlyIn ? '<p class="mc-hint">Seen only in ' + esc(String(m.SeenOnlyIn).toUpperCase()) + " tenants.</p>" : "") +
      '<table class="mc-facts">' + facts.join("") + "</table>" +
      '<div class="mc-body">' + (bodyHtml || "<p><em>This post has no body text.</em></p>") + "</div>" +
      '<div class="mc-buttons">' + links.join("") + "</div>" +
      '<div class="admonition warning"><p class="admonition-title">Tenant-specific</p><p>' +
      (source === "messageCenter" ? "Message Center posts differ between tenants. Check applicability and timing in your own Microsoft 365 admin center."
        : "Check the source for the latest status before you plan around it.") + "</p></div>" +
      '<p class="mc-hint">Content: Microsoft, kept in this site\'s own archive.</p>';
  }

  // Images load only from Microsoft-owned hosts, so reading a post never sends the visitor's
  // address to a third party; anything else is shown as its alt text.
  var IMAGE_HOSTS = /(^|\.)(microsoft\.com|office\.com|office\.net|office365\.com|microsoftonline\.com|sharepoint\.com|azureedge\.net|azure\.com|msecnd\.net|windows\.net|onestore\.ms|aka\.ms)$/i;
  function imageAllowed(src) {
    try { var u = new URL(src); return u.protocol === "https:" && IMAGE_HOSTS.test(u.hostname); }
    catch (e) { return false; }
  }

  // Allow-list HTML sanitizer: keeps text formatting, lists, tables, links and
  // https images; drops scripts, styles, event handlers and everything else.
  function sanitize(html) {
    if (!html) return "";
    var ALLOWED = /^(P|BR|UL|OL|LI|A|STRONG|B|EM|I|U|H2|H3|H4|H5|H6|TABLE|THEAD|TBODY|TR|TH|TD|CODE|PRE|BLOCKQUOTE|IMG|SPAN|DIV|HR|SUB|SUP)$/;
    var DROP = /^(SCRIPT|STYLE|IFRAME|OBJECT|EMBED|FORM|INPUT|BUTTON|TEXTAREA|SELECT|LINK|META|SVG|MATH|NOSCRIPT|TEMPLATE|FRAME|FRAMESET|BASE)$/;
    var doc = new DOMParser().parseFromString("<div>" + html + "</div>", "text/html");
    var root = doc.body.firstChild;
    (function walk(node) {
      Array.prototype.slice.call(node.childNodes).forEach(function (n) {
        if (n.nodeType === 3) return;
        if (n.nodeType !== 1) { n.remove(); return; }
        var tag = n.tagName;
        if (DROP.test(tag)) { n.remove(); return; }
        walk(n);
        if (tag === "H1") {  // keep a single page title
          var h = doc.createElement("h2"); while (n.firstChild) h.appendChild(n.firstChild); n.replaceWith(h); return;
        }
        if (!ALLOWED.test(tag)) { while (n.firstChild) n.parentNode.insertBefore(n.firstChild, n); n.remove(); return; }
        Array.prototype.slice.call(n.attributes).forEach(function (a) {
          var name = a.name.toLowerCase(), keep = false;
          if (tag === "A" && name === "href") keep = /^(https?:|mailto:)/i.test(a.value.trim());
          else if (tag === "IMG" && name === "src") keep = imageAllowed(a.value.trim());
          else if (/^(alt|title|colspan|rowspan)$/.test(name)) keep = true;
          if (!keep) n.removeAttribute(a.name);
        });
        if (tag === "A") {
          var href = n.getAttribute("href") || "";
          var m = href.match(/^https:\/\/mc\.merill\.net\/message\/([A-Za-z0-9-]+)\/?$/);
          if (m) { n.setAttribute("href", readerUrl(m[1])); }
          else if (href) { n.setAttribute("target", "_blank"); n.setAttribute("rel", "noopener"); }
        }
        if (tag === "IMG") {
          if (n.getAttribute("src")) { n.setAttribute("loading", "lazy"); n.setAttribute("referrerpolicy", "no-referrer"); }
          else if (n.getAttribute("alt")) n.replaceWith(doc.createTextNode("[" + n.getAttribute("alt") + "]"));
          else n.remove();
        }
      });
    })(root);
    return root.innerHTML;
  }
})();
