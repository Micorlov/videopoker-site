/* Hebrew salary-market prototype. Gross monthly NIS, client-side only.
 *
 * The anchor bands are the published 2026 tables named in salary/index.html.
 * Two adjustments are model weights, not extra surveys: a top-tier product
 * company is the high-tech band plus 12%, and a traditional company is 90% of
 * high-tech where the table has no traditional row. Skill percents other than
 * the GotFriends AI premium (~9%) are model weights too, capped at 20%.
 *
 *   base(role, years, company)
 *   × (1 + min(skill sum, 20%) + degree 2% + cert 2%)
 *   then rounded to the nearest 100 NIS.
 *
 * The USD remote view uses the published annual band (years move it by the
 * same ratio as the NIS median). Skills, degree and cert do not. Conversion
 * is a fixed 3.089 NIS per USD. It is not a geo-adjusted offer.
 */
(function (root, factory) {
  var api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.SalaryEstimate = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  "use strict";

  var NIS_PER_USD = 3.089;
  var SKILL_CAP = 0.2;
  var DEGREE_PCT = 0.02;
  var CERT_PCT = 0.02;
  var TOP_TIER_FACTOR = 1.12;
  var TRADITIONAL_FACTOR = 0.9;
  var GEO_USD_LOW = 105000;
  var GEO_USD_HIGH = 135000;
  var YEAR_MIN = 0;
  var YEAR_MAX = 40;

  var SKILLS = [
    { id: "python", label: "Python", pct: 0.03 },
    { id: "mobile", label: "אוטומציית מובייל", pct: 0.04 },
    { id: "embedded", label: "Embedded / IoT", pct: 0.05 },
    { id: "cicd", label: "CI/CD", pct: 0.03 },
    { id: "cloud", label: "ענן", pct: 0.04 },
    { id: "ai", label: "סוכני AI לבדיקות", pct: 0.09 },
  ];

  var COMPANIES = {
    traditional: { id: "traditional", label: "חברה מסורתית", inPhrase: "בחברה מסורתית" },
    hightech: { id: "hightech", label: "הייטק", inPhrase: "בהייטק" },
    toptier: { id: "toptier", label: "מוצר מוביל", inPhrase: "בחברת מוצר מוביל" },
  };

  var ROLES = {
    seniorQa: {
      id: "seniorQa",
      label: "אוטומציית QA בכיר/ה",
      traditionalCited: true,
      points: [
        { years: 7, hightech: [38000, 41000, 44000], traditional: [32000, 34000, 36000] },
      ],
      below: 0.045,
      above: 0.02,
      aboveCap: 0.12,
      floor: 0.62,
      usd: { kind: "survey", low: 128000, median: 155000, high: 191000 },
      usdBlurb: "העוגן הדולרי הוא Glassdoor ל-Senior SDET: 128–191 אלף דולר לשנה, חציון 155 אלף.",
    },
    qa: {
      id: "qa",
      label: "אוטומציית QA",
      traditionalCited: true,
      points: [
        { years: 4, hightech: [27000, 29500, 32000], traditional: [23000, 25000, 27000] },
      ],
      below: 0.08,
      above: 0.03,
      aboveCap: 0.15,
      floor: 0.62,
      usd: { kind: "scaled", from: "seniorQa", scale: 0.8 },
      usdBlurb: "אין סקר דולרי נפרד לאוטומציית QA שאינה בכירה. המודל לוקח 80% מרצועת ה-Senior SDET.",
    },
    lead: {
      id: "lead",
      label: "ראש צוות אוטומציית בדיקות",
      traditionalCited: false,
      points: [{ years: 8, hightech: [35000, 40000, 45000] }],
      below: 0.035,
      above: 0.02,
      aboveCap: 0.1,
      floor: 0.7,
      usd: { kind: "survey", low: 110000, median: 125000, high: 140000 },
      usdBlurb: "העוגן הדולרי לראש צוות בדיקות מרחוק הוא 110–140 אלף דולר לשנה.",
    },
    devops: {
      id: "devops",
      label: "DevOps",
      traditionalCited: false,
      points: [
        { years: 4, hightech: [24000, 27500, 31000] },
        { years: 7, hightech: [32000, 38000, 45000] },
      ],
      below: 0.06,
      above: 0.02,
      aboveCap: 0.12,
      floor: 0.62,
      usd: { kind: "spread", median: 161000, spread: 0.18 },
      usdBlurb: "הנתון המפורסם ל-DevOps מרחוק הוא ממוצע של כ־161 אלף דולר. הרצועה כאן היא 18% מתחת ומעל הממוצע, לא טווח מסקר.",
    },
    sre: {
      id: "sre",
      label: "SRE",
      traditionalCited: false,
      points: [
        { years: 4, hightech: [26000, 30000, 34000] },
        { years: 7, hightech: [35000, 40000, 45000] },
      ],
      below: 0.06,
      above: 0.02,
      aboveCap: 0.12,
      floor: 0.62,
      usd: { kind: "proxy", of: "devops" },
      usdBlurb: "אין סקר דולרי נפרד ל-SRE. המודל משתמש באותו עוגן של DevOps מרחוק, ממוצע של כ־161 אלף דולר.",
    },
    network: {
      id: "network",
      label: "מהנדס/ת אוטומציית רשתות",
      traditionalCited: false,
      points: [{ years: 6, hightech: [23000, 29250, 35500] }],
      below: 0.045,
      above: 0.02,
      aboveCap: 0.1,
      floor: 0.65,
      usd: { kind: "survey", low: 106000, median: 135000, high: 164000 },
      usdBlurb: "העוגן הדולרי לאוטומציית רשתות הוא 106–164 אלף דולר לשנה, חציון 135 אלף.",
    },
  };

  var ROLE_ORDER = ["seniorQa", "qa", "lead", "devops", "sre", "network"];

  function clamp(n, lo, hi) {
    return Math.min(hi, Math.max(lo, n));
  }

  function round100(n) {
    return Math.round(n / 100) * 100;
  }

  function round1000(n) {
    return Math.round(n / 1000) * 1000;
  }

  function grouped(n) {
    return String(Math.round(n)).replace(/\B(?=(\d{3})+(?!\d))/g, ",");
  }

  function pctText(p) {
    var n = Math.round(p * 1000) / 10;
    return (n % 1 === 0 ? String(n) : n.toFixed(1)) + "%";
  }

  function yearsWord(n) {
    return n === 1 ? "שנת ניסיון אחת" : n + " שנות ניסיון";
  }

  function rawColumn(role, years, column) {
    var pts = role.points;
    if (years <= pts[0].years) {
      var factor = Math.max(role.floor, 1 - (pts[0].years - years) * role.below);
      return {
        triple: pts[0][column].map(function (n) { return n * factor; }),
        effect: factor < 1 - 1e-9 ? "down" : "flat",
        anchor: pts[0].years,
      };
    }
    var last = pts[pts.length - 1];
    if (years >= last.years) {
      var extra = Math.min((years - last.years) * role.above, role.aboveCap);
      return {
        triple: last[column].map(function (n) { return n * (1 + extra); }),
        effect: extra > 1e-9 ? "up" : "flat",
        anchor: last.years,
      };
    }
    var i = 0;
    while (pts[i + 1].years < years) i += 1;
    var a = pts[i];
    var b = pts[i + 1];
    var t = (years - a.years) / (b.years - a.years);
    return {
      triple: [0, 1, 2].map(function (k) { return a[column][k] + (b[column][k] - a[column][k]) * t; }),
      effect: "between",
      anchor: b.years,
      fromYears: a.years,
      toYears: b.years,
    };
  }

  function companyBand(role, years, company) {
    var ht = rawColumn(role, years, "hightech");
    if (company === "hightech") return ht;
    if (company === "toptier") {
      return {
        triple: ht.triple.map(function (n) { return n * TOP_TIER_FACTOR; }),
        effect: ht.effect,
        anchor: ht.anchor,
        fromYears: ht.fromYears,
        toYears: ht.toYears,
      };
    }
    if (role.traditionalCited) return rawColumn(role, years, "traditional");
    return {
      triple: ht.triple.map(function (n) { return n * TRADITIONAL_FACTOR; }),
      effect: ht.effect,
      anchor: ht.anchor,
      fromYears: ht.fromYears,
      toYears: ht.toYears,
    };
  }

  function skillModifier(ids) {
    var wanted = {};
    (ids || []).forEach(function (id) { wanted[id] = true; });
    var picked = SKILLS.filter(function (s) { return wanted[s.id]; });
    var sum = picked.reduce(function (acc, s) { return acc + s.pct; }, 0);
    return { picked: picked, sum: sum, applied: Math.min(sum, SKILL_CAP), capped: sum > SKILL_CAP + 1e-9 };
  }

  function usdAnchorYears(role) {
    return role.usd.anchorYears != null ? role.usd.anchorYears : role.points[role.points.length - 1].years;
  }

  function publishedUsd(roleId) {
    var role = ROLES[roleId];
    var u = role.usd;
    if (u.kind === "survey") return { low: u.low, median: u.median, high: u.high, kind: u.kind };
    if (u.kind === "scaled") {
      var base = publishedUsd(u.from);
      return {
        low: round1000(base.low * u.scale),
        median: round1000(base.median * u.scale),
        high: round1000(base.high * u.scale),
        kind: "scaled",
      };
    }
    if (u.kind === "spread") {
      return {
        low: round1000(u.median * (1 - u.spread)),
        median: u.median,
        high: round1000(u.median * (1 + u.spread)),
        kind: "spread",
      };
    }
    var other = publishedUsd(u.of);
    return { low: other.low, median: other.median, high: other.high, kind: "proxy" };
  }

  function usdView(role, years) {
    var anchor = usdAnchorYears(role);
    var atYears = rawColumn(role, years, "hightech").triple[1];
    var atAnchor = rawColumn(role, anchor, "hightech").triple[1];
    var factor = atYears / atAnchor;
    var band = publishedUsd(role.id);
    var annual = {
      low: round1000(band.low * factor),
      median: round1000(band.median * factor),
      high: round1000(band.high * factor),
    };
    function monthly(usd) { return Math.round((usd * NIS_PER_USD) / 12); }
    var lines = [role.usdBlurb];
    if (Math.abs(factor - 1) < 1e-9) {
      lines.push("בוותק של העוגן הדולרי (" + anchor + " שנים) הרצועה היא הרצועה המפורסמת, בלי תיקון.");
    } else {
      lines.push("הרצועה הדולרית זזה עם הוותק באותו יחס כמו החציון בשקלים. העוגן הדולרי הוא " + anchor + " שנים.");
    }
    lines.push("מיומנויות, תואר והסמכה לא נכנסים לדולר.");
    lines.push("ההמרה היא שער " + NIS_PER_USD + " שקלים לדולר בלבד, בלי מס אמריקאי או ישראלי.");
    lines.push("רוב החברות האמריקאיות לא משלמות את הרצועה המלאה למי שגר בישראל, אלא שכר מותאם גיאוגרפית. מישראל זה לרוב " + grouped(GEO_USD_LOW) + "–" + grouped(GEO_USD_HIGH) + " דולר לשנה.");
    return {
      low: annual.low,
      median: annual.median,
      high: annual.high,
      nisLow: monthly(annual.low),
      nisMedian: monthly(annual.median),
      nisHigh: monthly(annual.high),
      geoLow: GEO_USD_LOW,
      geoHigh: GEO_USD_HIGH,
      geoNisLow: monthly(GEO_USD_LOW),
      geoNisHigh: monthly(GEO_USD_HIGH),
      factor: factor,
      kind: band.kind,
      lines: lines,
    };
  }

  function explain(role, company, years, band, skills, degree, cert) {
    var lines = [];
    lines.push("הבסיס הוא רצועת " + role.label + " " + COMPANIES[company].inPhrase + ".");
    if (band.effect === "down") {
      lines.push("הוותק שהוזן, " + yearsWord(years) + ", נמוך מהעוגן (" + band.anchor + " שנים) ומוריד את הרצועה.");
    } else if (band.effect === "up") {
      lines.push("הוותק גבוה מהעוגן (" + band.anchor + " שנים) ומעלה את הרצועה, עד תקרה.");
    } else if (band.effect === "between") {
      lines.push("הוותק נמצא בין נקודת הביניים (" + band.fromYears + " שנים) לנקודת הבכירות (" + band.toYears + " שנים).");
    } else {
      lines.push("הוותק יושב על עוגן הטבלה (" + band.anchor + " שנים), בלי תיקון נוסף.");
    }
    if (company === "toptier") {
      lines.push("חברת מוצר מוביל אינה שורה נפרדת בטבלאות. המודל מוסיף 12% על רצועת ההייטק.");
    } else if (company === "traditional" && role.traditionalCited) {
      lines.push("הרצועה המסורתית היא שורת נישה לחברות מסורתיות, לא הנחה של 90%.");
    } else if (company === "traditional") {
      lines.push("אין בטבלאות פיצול לחברה מסורתית בתפקיד הזה, אז המודל לוקח 90% מרצועת ההייטק.");
    }
    if (!skills.picked.length) {
      lines.push("לא סומנה מיומנות, אז אין תוספת. הבסיס מייצג פרופיל טיפוסי מהטבלאות.");
    } else {
      skills.picked.forEach(function (s) {
        var note = s.id === "ai" ? " (פרמיית AI של GotFriends)" : "";
        lines.push("תוספת מיומנות: " + s.label + ", " + pctText(s.pct) + note + ".");
      });
    }
    if (skills.capped) lines.push("סך המיומנויות נחתך בתקרה של 20%.");
    if (degree) lines.push("תואר רלוונטי מוסיף 2%. זה משקל של המודל, לא שורה מסקר.");
    if (cert) lines.push("הסמכה רלוונטית מוסיפה 2%. גם זה משקל של המודל.");
    return lines;
  }

  function estimate(input) {
    var role = ROLES[input && input.role];
    if (!role) throw new Error("unknown role");
    var company = input.company;
    if (!COMPANIES[company]) throw new Error("unknown company");
    var yearsIn = Number(input.years);
    if (!isFinite(yearsIn)) yearsIn = role.points[role.points.length - 1].years;
    var years = Math.round(clamp(yearsIn, YEAR_MIN, YEAR_MAX));
    var skills = skillModifier(input.skills);
    var degree = !!input.degree;
    var cert = !!input.cert;
    var band = companyBand(role, years, company);
    var extra = skills.applied + (degree ? DEGREE_PCT : 0) + (cert ? CERT_PCT : 0);
    var base = band.triple.map(round100);
    var finalTriple = band.triple.map(function (n) { return round100(n * (1 + extra)); });
    return {
      role: role.id,
      company: company,
      years: years,
      low: finalTriple[0],
      median: finalTriple[1],
      high: finalTriple[2],
      baseLow: base[0],
      baseMedian: base[1],
      baseHigh: base[2],
      skillPct: skills.applied,
      skillCapped: skills.capped,
      lines: explain(role, company, years, band, skills, degree, cert),
      remote: input.remote ? usdView(role, years) : null,
    };
  }

  return {
    estimate: estimate,
    NIS_PER_USD: NIS_PER_USD,
    SKILL_CAP: SKILL_CAP,
    DEGREE_PCT: DEGREE_PCT,
    CERT_PCT: CERT_PCT,
    TOP_TIER_FACTOR: TOP_TIER_FACTOR,
    TRADITIONAL_FACTOR: TRADITIONAL_FACTOR,
    GEO_USD_LOW: GEO_USD_LOW,
    GEO_USD_HIGH: GEO_USD_HIGH,
    SKILLS: SKILLS,
    COMPANIES: COMPANIES,
    ROLES: ROLES,
    ROLE_ORDER: ROLE_ORDER,
    grouped: grouped,
    pctText: pctText,
  };
});
