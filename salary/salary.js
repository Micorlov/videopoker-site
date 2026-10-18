/* Binds the Hebrew salary form. Numbers stay in the browser. */
(function () {
  "use strict";

  var E = window.SalaryEstimate;
  var form = document.getElementById("calc");
  var years = document.getElementById("years");
  var yearsRange = document.getElementById("years-range");
  var anchorHint = document.getElementById("anchor-hint");

  function money(n) {
    return E.grouped(n);
  }

  function checked(name) {
    var el = form.querySelector('input[name="' + name + '"]:checked');
    return el ? el.value : "";
  }

  function read() {
    var skills = [];
    form.querySelectorAll('input[name="skill"]:checked').forEach(function (box) {
      skills.push(box.value);
    });
    return E.estimate({
      role: document.getElementById("role").value,
      years: years.value,
      company: checked("company"),
      skills: skills,
      degree: checked("degree") === "yes",
      cert: checked("cert") === "yes",
      remote: document.getElementById("remote").checked,
    });
  }

  function fillStats(prefix, low, median, high) {
    document.getElementById(prefix + "-low").textContent = money(low);
    document.getElementById(prefix + "-mid").textContent = money(median);
    document.getElementById(prefix + "-high").textContent = money(high);
  }

  function fillList(id, lines) {
    var list = document.getElementById(id);
    list.replaceChildren();
    lines.forEach(function (line) {
      var item = document.createElement("li");
      item.textContent = line;
      list.appendChild(item);
    });
  }

  function render() {
    var result = read();
    var role = E.ROLES[result.role];
    anchorHint.textContent = "עוגן הטבלה: " + role.points.map(function (p) { return p.years; }).join(" ו-") + " שנים";
    fillStats("nis", result.low, result.median, result.high);
    fillStats("dock", result.low, result.median, result.high);
    fillList("why", result.lines);
    var remote = document.getElementById("remote-view");
    if (!result.remote) {
      remote.hidden = true;
      return;
    }
    remote.hidden = false;
    fillStats("usd", result.remote.low, result.remote.median, result.remote.high);
    fillStats("usd-nis", result.remote.nisLow, result.remote.nisMedian, result.remote.nisHigh);
    document.getElementById("geo-usd").textContent = money(result.remote.geoLow) + "–" + money(result.remote.geoHigh);
    document.getElementById("geo-nis").textContent = money(result.remote.geoNisLow) + "–" + money(result.remote.geoNisHigh);
    fillList("remote-why", result.remote.lines);
  }

  function syncYears(fromRange) {
    var value = fromRange ? yearsRange.value : years.value;
    years.value = value;
    yearsRange.value = value;
    render();
  }

  years.addEventListener("input", function () { syncYears(false); });
  yearsRange.addEventListener("input", function () { syncYears(true); });
  form.addEventListener("input", render);
  form.addEventListener("change", render);
  form.addEventListener("submit", function (event) {
    event.preventDefault();
    render();
  });

  var anchors = document.getElementById("anchors");
  E.ROLE_ORDER.forEach(function (id) {
    var role = E.ROLES[id];
    var card = document.createElement("article");
    card.className = "anchor";
    var title = document.createElement("h3");
    title.textContent = role.label;
    card.appendChild(title);
    role.points.forEach(function (point) {
      var row = document.createElement("p");
      var bits = ["עוגן " + point.years + " שנים"];
      ["traditional", "hightech", "toptier"].forEach(function (company) {
        var sample = E.estimate({
          role: id,
          years: point.years,
          company: company,
          skills: [],
          degree: false,
          cert: false,
          remote: false,
        });
        bits.push(E.COMPANIES[company].label + " " + money(sample.low) + "–" + money(sample.high));
      });
      row.textContent = bits.join(" · ");
      card.appendChild(row);
    });
    var rates = document.createElement("p");
    rates.className = "rates";
    var below = "מתחת לנקודה הראשונה: " + E.pctText(role.below) + " לשנה";
    var above = "מעל האחרונה: " + E.pctText(role.above) + " לשנה, תקרה " + E.pctText(role.aboveCap);
    rates.textContent = role.points.length > 1
      ? "בין הנקודות הרצועה מתיישרת. " + below + ". " + above + "."
      : below + ". " + above + ".";
    card.appendChild(rates);
    anchors.appendChild(card);
  });

  render();
})();
