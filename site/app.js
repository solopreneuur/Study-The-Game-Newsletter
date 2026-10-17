// Shared by / and /latest: fetch latest.md, split it into ideas, render the report.
(function () {
  var target = document.getElementById("issue");
  var meta = document.getElementById("meta");
  var MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  var DAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

  function esc(s) {
    return s.replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; });
  }
  function inline(s) { return marked.parseInline(s); }
  function pad(n) { return String(n).padStart(2, "0"); }

  function fmtDate(iso) {
    var p = iso.split("-").map(Number);
    var d = new Date(p[0], p[1] - 1, p[2]);
    return DAYS[d.getDay()] + " · " + MONTHS[d.getMonth()] + " " + d.getDate() + ", " + d.getFullYear();
  }

  function setMeta(issueNo, date) {
    meta.innerHTML =
      "<span>Issue <b>No. " + esc(issueNo || "00") + "</b></span>" +
      "<span>" + (date ? esc(fmtDate(date)) : "Every Sunday") + "</span>" +
      "<span>5 ideas</span>";
  }

  function empty() {
    setMeta("00", null);
    target.innerHTML =
      '<div class="empty">' +
      '<span class="mono kicker">Scouting report pending</span>' +
      "<h2>First issue lands Sunday.</h2>" +
      "<p>Five ideas worth stealing, hand-picked every week.</p>" +
      "</div>";
  }

  // Issue markdown → { issueNo, deck, ideas: [{ n, hook, starred, body, steal, video }], signoff }
  function parse(md) {
    var blocks = md.trim().split(/\n\s*\n/).map(function (b) {
      return b.split("\n").map(function (l) { return l.trim(); }).filter(Boolean);
    }).filter(function (b) { return b.length; });

    var out = { issueNo: null, deck: "", ideas: [], signoff: [] };
    blocks.forEach(function (lines) {
      var head = lines[0].match(/^\*\*(\d+)\.\s+(.+?)\*\*\s*(.*)$/);
      if (/^#\s/.test(lines[0])) {
        var no = lines[0].match(/#(\d+)/);
        out.issueNo = no ? no[1] : null;
        out.deck = (lines[1] || "").replace(/^_(.*)_$/, "$1");
        return;
      }
      if (head) {
        var idea = { n: +head[1], hook: head[2], starred: /★|my pick/i.test(head[3]), body: [], steal: "", video: null };
        lines.slice(1).forEach(function (l) {
          var steal = l.match(/^\*\*How I.m stealing it:\*\*\s*(.*)$/i);
          var video = l.match(/I made a video on this.*?(https?:\/\/\S+)/i);
          if (steal) idea.steal = steal[1];
          else if (video) idea.video = video[1];
          else idea.body.push(l);
        });
        out.ideas.push(idea);
        return;
      }
      if (out.ideas.length) out.signoff = out.signoff.concat(lines);
    });
    return out;
  }

  function render(issue) {
    var total = issue.ideas.length;
    var html =
      '<header class="issue-head">' +
      '<span class="mono kicker">This week’s playbook</span>' +
      '<h1 class="issue-title">5 Ideas Worth <em>Stealing</em></h1>' +
      (issue.deck ? '<p class="deck">' + inline(issue.deck) + "</p>" : "") +
      "</header>";

    issue.ideas.forEach(function (idea, i) {
      html +=
        '<section class="idea">' +
        '<div class="idea-top"><span class="idea-num">' + pad(i + 1) + "</span>" +
        '<span class="mono idea-count">' + pad(i + 1) + " / " + pad(total) + "</span></div>" +
        (idea.starred ? '<span class="mono stamp">★ My pick</span>' : "") +
        '<h2 class="idea-hook">' + inline(idea.hook) + "</h2>" +
        '<p class="idea-body">' + inline(idea.body.join(" ")) + "</p>" +
        (idea.steal ? '<div class="steal"><span class="mono steal-label">Steal this</span><p>' + inline(idea.steal) + "</p></div>" : "") +
        (idea.video ? '<a class="mono video" href="' + esc(idea.video) + '">I made a video on this</a>' : "") +
        "</section>";
    });

    var sign = issue.signoff.length ? issue.signoff : ["see you sunday", "Huzaifa"];
    html += '<footer class="signoff">' + inline(sign[0]) + (sign[1] ? "<span>— " + inline(sign[1].replace(/^[—-]\s*/, "")) + "</span>" : "") + "</footer>";
    return html;
  }

  fetch("latest.md", { cache: "no-cache" })
    .then(function (r) { return r.ok ? r.text() : ""; })
    .then(function (md) {
      if (!md.trim() || /<!--\s*placeholder/i.test(md)) return empty();
      var date = (md.match(/<!--\s*date:\s*(\d{4}-\d{2}-\d{2})\s*-->/) || [])[1] || null;
      md = md.replace(/<!--[\s\S]*?-->/g, "");
      var issue = parse(md);
      setMeta(issue.issueNo, date);
      if (issue.ideas.length) {
        target.innerHTML = render(issue);
        document.title = "Study the Game — No. " + (issue.issueNo || "");
      } else {
        target.innerHTML = '<div class="raw">' + marked.parse(md, { breaks: true }) + "</div>";
      }
      target.querySelectorAll("a").forEach(function (a) { a.target = "_blank"; a.rel = "noopener"; });
    })
    .catch(empty);
})();
