console.log("DOJO App (Bootstrap) Loaded");

document.addEventListener("DOMContentLoaded", () => {
  const toggle = document.getElementById("themeToggle");
  const body = document.body;
  const themeIcon = document.getElementById("themeIcon");

  // Helper function to apply theme
  function applyTheme(theme) {
    body.classList.remove("light-theme", "dark-theme");
    body.classList.add(theme + "-theme");

    if (theme === "dark") {
      themeIcon.textContent = "🌙";
    } else {
      themeIcon.textContent = "🌞";
    }

    localStorage.setItem("theme", theme);
  }

  // Load saved theme (default: light)
  const savedTheme = localStorage.getItem("theme") || "light";
  applyTheme(savedTheme);

  // Set toggle checked state
  toggle.checked = savedTheme === "dark";

  // Toggle event
  toggle.addEventListener("change", () => {
    if (toggle.checked) {
      applyTheme("dark");
    } else {
      applyTheme("light");
    }
  });
});
