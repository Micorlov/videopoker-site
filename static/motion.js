/* Motion for the studio pages. Content stays visible if this file never runs.
   Transforms and opacity only. Reduced motion drops the travel. */
(function () {
  var reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  if (!reduce && "IntersectionObserver" in window) {
    var nodes = document.querySelectorAll("[data-reveal]");
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        entry.target.classList.add("in");
        io.unobserve(entry.target);
      });
    }, { rootMargin: "0px 0px -8% 0px", threshold: 0.12 });
    nodes.forEach(function (el) {
      el.classList.add("wait");
      io.observe(el);
    });
  }

  var stage = document.querySelector("[data-stage]");
  if (!stage) return;
  var cards = document.querySelectorAll("#apps a.card[data-shot]");
  if (!cards.length) return;
  var current = stage.getAttribute("src");
  var timer = 0;

  function arm(card) {
    cards.forEach(function (c) { c.classList.toggle("is-on", c === card); });
    var src = card.getAttribute("data-shot");
    if (!src || src === current) return;
    current = src;
    if (reduce) {
      stage.setAttribute("src", src);
      return;
    }
    stage.classList.add("swap");
    window.clearTimeout(timer);
    timer = window.setTimeout(function () {
      stage.setAttribute("src", src);
      stage.classList.remove("swap");
    }, 140);
  }

  var fine = window.matchMedia("(hover: hover) and (pointer: fine)").matches;
  cards.forEach(function (card) {
    if (fine) card.addEventListener("pointerenter", function () { arm(card); });
    card.addEventListener("focus", function () { arm(card); });
  });

  if ("IntersectionObserver" in window) {
    var listIO = new IntersectionObserver(function (entries) {
      var best = null;
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        if (!best || entry.intersectionRatio > best.intersectionRatio) best = entry;
      });
      if (best) arm(best.target);
    }, { rootMargin: "-42% 0px -42% 0px", threshold: [0.2, 0.55] });
    cards.forEach(function (card) { listIO.observe(card); });
  }
})();
