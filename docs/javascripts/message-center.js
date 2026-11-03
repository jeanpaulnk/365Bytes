// Message Center page: quick lookup and latest posts from mc.merill.net.
(function () {
  var root = document.getElementById("mc-latest");
  var form = document.getElementById("mc-go");
  if (!root || !form) return;

  var BASE = "https://mc.merill.net";
  var SHOW = 25;
  var all = [], src = "all";

  form.addEventListener("submit", function (e) {
    e.preventDefault();
    var v = document.getElementById("mc-go-input").value.trim();
    if (!v) return;
    var isId = /^(MC|RM|AZ)-?[\w-]+$/i.test(v) && /\d/.test(v);
    var url = isId ? BASE + "/message/" + encodeURIComponent(v.toUpperCase()) : BASE + "/?q=" + encodeURIComponent(v);
    window.open(url, "_blank", "noopener");
  });

  function f(r, names) {
    for (var i = 0; i < names.length; i++) {
      var n = names[i];
      if (r[n] != null && r[n] !== "") return r[n];
      var k = Object.keys(r).find(function (x) { return x.toLowerCase() === n.toLowerCase(); });
      if (k && r[k] != null && r[k] !== "") return r[k];
    }
    return null;
  }
  function norm(r) {
    var id = String(f(r, ["Id", "ID"]) || "");
    var services = f(r, ["Services", "Service"]);
    if (Array.isArray(services)) services = services.join(", ");
    var date = f(r, ["LastModifiedDateTime", "LastUpdated", "Modified", "StartDateTime", "Published", "Date"]);
    var s = String(f(r, ["Source"]) || "");
    if (!s) s = /^MC/i.test(id) ? "messageCenter" : /^RM/i.test(id) ? "roadmap" : /^AZ/i.test(id) ? "azure" : "";
    return {
      id: id,
      title: f(r, ["Title"]) || id,
      url: f(r, ["Url", "URL"]) || BASE + "/message/" + encodeURIComponent(id),
      services: services || "",
      date: date ? new Date(date) : null,
      source: s
    };
  }
  function esc(t) {
    return String(t).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;", "'": "&#39;" }[c];
    });
  }
  function render() {
    var q = document.getElementById("mc-filter").value.trim().toLowerCase();
    var list = all.filter(function (p) {
      if (src !== "all" && p.source.toLowerCase() !== src.toLowerCase()) return false;
      return !q || (p.title + " " + p.services + " " + p.id).toLowerCase().indexOf(q) >= 0;
    }).slice(0, SHOW);
    document.getElementById("mc-posts").innerHTML = list.map(function (p) {
      var idTag = /^AZ-/i.test(p.id) ? "" : '<span class="mc-id">' + esc(p.id) + "</span>";
      var d = p.date && !isNaN(p.date) ? p.date.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" }) : "";
      return "<li>" + idTag + '<a href="' + esc(p.url) + '" target="_blank" rel="noopener">' + esc(p.title) + "</a>" +
        '<div class="mc-meta">' + esc([p.services, d].filter(Boolean).join(" · ")) + "</div></li>";
    }).join("");
    document.getElementById("mc-status").textContent = list.length
      ? "Showing " + list.length + " of " + all.length + " posts, newest first."
      : "No posts match. Use the search box above to search the full archive.";
  }

  root.querySelectorAll(".mc-tabs button").forEach(function (b) {
    b.addEventListener("click", function () {
      src = b.getAttribute("data-src");
      root.querySelectorAll(".mc-tabs button").forEach(function (x) {
        x.setAttribute("aria-pressed", x === b ? "true" : "false");
      });
      render();
    });
  });
  document.getElementById("mc-filter").addEventListener("input", render);

  fetch(BASE + "/messages-index.json")
    .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
    .then(function (data) {
      var rows = Array.isArray(data) ? data : (data.messages || data.items || data.value || []);
      all = rows.map(norm).filter(function (p) { return p.id; });
      all.sort(function (a, b) { return (b.date || 0) - (a.date || 0); });
      render();
    })
    .catch(function () {
      document.getElementById("mc-status").innerHTML =
        'Could not load the latest posts here. <a href="' + BASE + '/" target="_blank" rel="noopener">Open the archive</a> instead.';
    });
})();
