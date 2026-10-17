// Shared by / and /latest: fetch latest.md, split it into ideas, render the report.
(function () {
  var target = document.getElementById("issue");
  var meta = document.getElementById("meta");
  var MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

  function esc(s) {
    return s.replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; });
  }
  function inline(s) { return marked.parseInline(s); }
  function pad(n) { return String(n).padStart(2, "0"); }

  function fmtDate(iso) {
    var p = iso.split("-").map(Number);
    return MONTHS[p[1] - 1] + " " + p[2] + ", " + p[0];
  }

  // Slightly different wobble and tilt per idea, so nothing looks stamped out.
  var TILT = [-3, 2, -1.5, 2.5, -2, 1.5];
  var WOBBLE = [
    "M2 6 C 20 1, 35 10, 55 5 S 90 2, 110 6 S 150 9, 170 4 S 200 6, 218 5",
    "M2 5 C 25 9, 40 1, 62 6 S 95 9, 120 4 S 160 2, 182 7 S 206 4, 218 6",
    "M2 7 C 15 2, 38 8, 58 4 S 88 9, 115 5 S 148 1, 172 6 S 204 8, 218 4"
  ];
  function squiggle(i, cls) {
    return '<svg class="squiggle ' + (cls || "") + '" viewBox="0 0 220 10" preserveAspectRatio="none" aria-hidden="true">' +
      '<path d="' + WOBBLE[i % WOBBLE.length] + '" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>';
  }
  function tilt(i, extra) { return ' style="transform:rotate(' + (TILT[i % TILT.length] + (extra || 0)) + 'deg)"'; }

  var ABOUT = "Every Sunday I send 5 short ideas from psychology, marketing, business, and the people worth studying. " +
    "Each one is surprising, true, and something you can actually use.";

  function head() {
    return '<header class="issue-head">' +
      '<h1 class="issue-title">5 ideas worth <span class="under">stealing' + squiggle(0) + "</span></h1>" +
      '<p class="deck">' + ABOUT + "</p>" +
      "</header>";
  }

  function setMeta(issueNo, date) {
    meta.textContent = issueNo ? "no. " + issueNo + (date ? " · " + fmtDate(date).toLowerCase() : "") : "every sunday";
  }

  function empty() {
    setMeta(null, null);
    target.innerHTML = head() + '<p class="hand soon">First issue lands Sunday.</p>';
  }

  // Issue markdown → { issueNo, ideas: [{ n, hook, starred, body, steal, video }], signoff }
  function parse(md) {
    var blocks = md.trim().split(/\n\s*\n/).map(function (b) {
      return b.split("\n").map(function (l) { return l.trim(); }).filter(Boolean);
    }).filter(function (b) { return b.length; });

    var out = { issueNo: null, ideas: [], signoff: [] };
    blocks.forEach(function (lines) {
      var head = lines[0].match(/^\*\*(\d+)\.\s+(.+?)\*\*\s*(.*)$/);
      if (/^#\s/.test(lines[0])) {
        var no = lines[0].match(/#(\d+)/);
        out.issueNo = no ? no[1] : null;
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
    var html = head();

    issue.ideas.forEach(function (idea, i) {
      html +=
        '<div class="divider">' + squiggle(i + 1) + "</div>" +
        '<section class="idea">' +
        '<div class="idea-top"><span class="hand idea-num"' + tilt(i) + ">" + (i + 1) + ".</span>" +
        (idea.starred ? '<span class="hand idea-pick"' + tilt(i + 1) + ">← my pick</span>" : "") + "</div>" +
        '<h2 class="idea-hook">' + inline(idea.hook) + "</h2>" +
        '<p class="idea-body">' + inline(idea.body.join(" ")) + "</p>" +
        (idea.steal ? '<div class="steal"><span class="hand steal-label"' + tilt(i + 2, 1) + ">steal this →</span><p><mark>" + inline(idea.steal) + "</mark></p></div>" : "") +
        (idea.video ? '<a class="video" href="' + esc(idea.video) + '">I made a video on this →</a>' : "") +
        "</section>";
    });

    var sign = issue.signoff.length ? issue.signoff : ["see you sunday", "Huzaifa"];
    html += '<footer class="signoff"><p>' + inline(sign[0]) + "</p>" +
      (sign[1] ? '<span class="hand">' + inline(sign[1].replace(/^[—-]\s*/, "")) + "</span>" : "") + "</footer>";
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
