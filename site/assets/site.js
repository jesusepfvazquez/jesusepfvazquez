// Small helpers: publication filters and a spam-resistant email link.
(function () {
  document.querySelectorAll("a.mail").forEach(function (a) {
    var addr = a.dataset.u + "@" + a.dataset.d;
    a.href = "mailto:" + addr;
    if (a.textContent.indexOf("[at]") !== -1) a.textContent = addr;
  });

  var pills = document.querySelectorAll(".pill");
  if (!pills.length) return;
  var items = document.querySelectorAll(".paper[data-type]");
  var groups = document.querySelectorAll(".pub-group");
  var search = document.querySelector(".search");
  var empty = document.querySelector(".empty");
  var type = "all";

  function apply() {
    var q = (search.value || "").trim().toLowerCase();
    var shown = 0;
    items.forEach(function (li) {
      var ok = (type === "all" || li.dataset.type === type) &&
               (!q || li.dataset.text.indexOf(q) !== -1);
      li.hidden = !ok;
      if (ok) shown++;
    });
    groups.forEach(function (g) {
      g.hidden = !g.querySelector(".paper:not([hidden])");
    });
    empty.hidden = shown !== 0;
  }

  pills.forEach(function (b) {
    b.addEventListener("click", function () {
      pills.forEach(function (x) { x.classList.remove("active"); });
      b.classList.add("active");
      type = b.dataset.filter;
      history.replaceState(null, "", type === "all" ? location.pathname : "#" + type);
      apply();
    });
  });
  search.addEventListener("input", apply);

  var want = location.hash.replace("#", "");
  pills.forEach(function (b) { if (b.dataset.filter === want) b.click(); });
})();
