// Shared by / and /latest: fetch latest.md and render it.
(function () {
  var target = document.getElementById("issue");

  function empty() {
    target.innerHTML = '<p class="empty">First issue lands Sunday.</p>';
  }

  fetch("latest.md", { cache: "no-cache" })
    .then(function (r) { return r.ok ? r.text() : ""; })
    .then(function (md) {
      if (!md.trim() || /<!--\s*placeholder/i.test(md)) return empty();
      target.innerHTML = marked.parse(md, { breaks: true });
      var title = target.querySelector("h1");
      if (title) document.title = title.textContent;
      target.querySelectorAll("a").forEach(function (a) {
        a.target = "_blank";
        a.rel = "noopener";
      });
    })
    .catch(empty);
})();
