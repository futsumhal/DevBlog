(function () {
  var root = document.documentElement;
  var toggle = document.getElementById("themeToggle");
  var storageKey = "blog-theme";

  function applyTheme(theme) {
    root.setAttribute("data-bs-theme", theme);
    if (!toggle) return;
    var icon = toggle.querySelector(".theme-icon");
    if (icon) icon.textContent = theme === "dark" ? "☀️" : "🌙";
  }

  var saved = localStorage.getItem(storageKey);
  var initial = saved || "light";
  applyTheme(initial);

  if (toggle) {
    toggle.addEventListener("click", function () {
      var next = root.getAttribute("data-bs-theme") === "dark" ? "light" : "dark";
      localStorage.setItem(storageKey, next);
      applyTheme(next);
    });
  }
})();
