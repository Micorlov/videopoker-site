/* Locks the salary prototype to the published 2026 anchors and the modifiers. */
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const est = require("../../salary/estimate.js");

const estimate = est.estimate;

function at(partial) {
  return estimate(Object.assign({
    role: "seniorQa",
    years: 7,
    company: "hightech",
    skills: [],
    degree: false,
    cert: false,
    remote: false,
  }, partial));
}

function sameRange(result, low, median, high) {
  assert.deepEqual([result.low, result.median, result.high], [low, median, high]);
}

const senior = at({});
sameRange(senior, 38000, 41000, 44000);
assert.equal(senior.remote, null);
assert.ok(senior.lines.some((line) => line.includes("בלי תיקון נוסף")));
assert.ok(senior.lines.some((line) => line.includes("אין תוספת")));

sameRange(at({ company: "traditional" }), 32000, 34000, 36000);
assert.ok(at({ company: "traditional" }).lines.some((line) => line.includes("נישה")));

sameRange(at({ company: "toptier" }), 42600, 45900, 49300);
assert.ok(at({ company: "toptier" }).lines.some((line) => line.includes("12%")));

sameRange(at({ skills: ["ai"] }), 41400, 44700, 48000);
assert.ok(at({ skills: ["ai"] }).lines.some((line) => line.includes("9%") && line.includes("GotFriends")));

sameRange(at({ degree: true, cert: true, skills: ["ai"] }), 42900, 46300, 49700);

const allSkills = est.SKILLS.map((s) => s.id);
assert.ok(Math.abs(est.SKILLS.reduce((sum, s) => sum + s.pct, 0) - 0.28) < 1e-9);
const capped = at({ skills: allSkills });
sameRange(capped, 45600, 49200, 52800);
assert.equal(capped.skillCapped, true);
assert.equal(capped.skillPct, 0.2);

sameRange(at({ years: 4 }), 32900, 35500, 38100);
assert.ok(at({ years: 4 }).lines.some((line) => line.includes("מוריד")));
sameRange(at({ years: 13 }), 42600, 45900, 49300);
sameRange(at({ years: 40 }), 42600, 45900, 49300);
assert.equal(at({ years: 80 }).years, 40);
assert.equal(at({ years: -4 }).years, 0);

sameRange(at({ role: "qa", years: 4 }), 27000, 29500, 32000);
sameRange(at({ role: "lead", years: 8 }), 35000, 40000, 45000);
sameRange(at({ role: "devops", years: 4 }), 24000, 27500, 31000);
sameRange(at({ role: "devops", years: 7 }), 32000, 38000, 45000);
sameRange(at({ role: "devops", years: 7, company: "traditional" }), 28800, 34200, 40500);
sameRange(at({ role: "devops", years: 5 }), 26700, 31000, 35700);
sameRange(at({ role: "sre", years: 4 }), 26000, 30000, 34000);
sameRange(at({ role: "sre", years: 7 }), 35000, 40000, 45000);
sameRange(at({ role: "network", years: 6 }), 23000, 29300, 35500);

const remote = at({ remote: true });
const local = at({ remote: false, skills: ["ai"], degree: true });
assert.equal(remote.low, senior.low);
assert.deepEqual(
  [remote.remote.low, remote.remote.median, remote.remote.high],
  [128000, 155000, 191000],
);
assert.equal(remote.remote.nisMedian, Math.round((155000 * est.NIS_PER_USD) / 12));
assert.equal(remote.remote.nisMedian, 39900);
assert.equal(remote.remote.geoLow, 105000);
assert.equal(remote.remote.geoHigh, 135000);
assert.equal(remote.remote.geoNisLow, 27029);
assert.equal(remote.remote.geoNisHigh, 34751);
assert.equal(est.NIS_PER_USD, 3.089);
assert.ok(remote.remote.lines.some((line) => line.includes("3.089")));
assert.ok(remote.remote.lines.some((line) => line.includes("מותאם גיאוגרפית")));
assert.equal(local.remote, null);
assert.notEqual(local.median, senior.median);

const qaUsd = at({ role: "qa", years: 4, remote: true }).remote;
assert.deepEqual([qaUsd.low, qaUsd.median, qaUsd.high], [102000, 124000, 153000]);
const leadUsd = at({ role: "lead", years: 8, remote: true }).remote;
assert.deepEqual([leadUsd.low, leadUsd.median, leadUsd.high], [110000, 125000, 140000]);
const devopsUsd = at({ role: "devops", years: 7, remote: true }).remote;
assert.deepEqual([devopsUsd.low, devopsUsd.median, devopsUsd.high], [132000, 161000, 190000]);
const sreUsd = at({ role: "sre", years: 7, remote: true }).remote;
assert.deepEqual([sreUsd.low, sreUsd.median, sreUsd.high], [132000, 161000, 190000]);
const netUsd = at({ role: "network", years: 6, remote: true }).remote;
assert.deepEqual([netUsd.low, netUsd.median, netUsd.high], [106000, 135000, 164000]);

const usdTrad = at({ role: "devops", years: 4, company: "traditional", remote: true }).remote;
const usdHt = at({ role: "devops", years: 4, company: "hightech", remote: true }).remote;
assert.equal(usdTrad.median, usdHt.median);
assert.ok(usdHt.median < 161000);

assert.throws(() => at({ role: "ceo" }), /unknown role/);
assert.throws(() => at({ company: "startup" }), /unknown company/);
sameRange(at({ skills: ["ai", "nope"] }), 41400, 44700, 48000);

const roles = est.ROLE_ORDER;
const companies = Object.keys(est.COMPANIES);
for (const role of roles) {
  for (const years of [0, 1, 4, 6, 7, 8, 12, 40]) {
    for (const company of companies) {
      for (const remoteFlag of [false, true]) {
        const row = at({
          role,
          years,
          company,
          skills: years % 2 ? ["python", "ai"] : [],
          degree: years > 10,
          cert: company === "toptier",
          remote: remoteFlag,
        });
        assert.ok(row.low <= row.median && row.median <= row.high, `${role} ${years} ${company}`);
        assert.ok(row.low > 0);
        if (remoteFlag) {
          assert.ok(row.remote.low <= row.remote.median && row.remote.median <= row.remote.high);
          assert.equal(row.remote.geoLow, 105000);
          assert.ok(row.lines.length > 0 && row.remote.lines.length > 0);
        }
      }
    }
  }
}

const page = fs.readFileSync(path.join(__dirname, "../../salary/index.html"), "utf8");
assert.match(page, /<html lang="he" dir="rtl">/);
assert.doesNotMatch(page, /<html lang="en"/);
assert.match(page, /hreflang="he"/);
assert.doesNotMatch(page, /hreflang="iw"|lang="iw"/);
assert.match(page, /לא ייעוץ/);
assert.match(page, /3\.089/);
assert.match(page, /תקרה של 20%/);
assert.match(page, /12%/);
assert.match(page, /90%/);
assert.match(page, /105–135/);
assert.match(page, /38–44/);
assert.match(page, /32–36/);
assert.match(page, /35–45/);
assert.match(page, /23,000–35,500|23–35\.5/);
assert.match(page, /G-NS1LGN6P3Y/);
assert.equal(page.split("googletagmanager.com/gtag/js?id=G-NS1LGN6P3Y").length - 1, 1);

console.log("salary estimate: ok");
