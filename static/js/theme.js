const THEME_STORAGE_KEY = "nanpa2-ui-theme";

document.addEventListener("DOMContentLoaded", () => {
  const select = document.getElementById("theme-select");
  const saved = localStorage.getItem(THEME_STORAGE_KEY) || "basic";
  setTheme(saved, false);
  select?.addEventListener("change", (event) => {
    setTheme(event.target.value, true);
  });
});

function setTheme(theme, persist) {
  const name = theme === "nanpa" ? "nanpa" : "basic";
  document.documentElement.setAttribute("data-theme", name);
  const select = document.getElementById("theme-select");
  if (select) {
    select.value = name;
  }
  if (persist) {
    localStorage.setItem(THEME_STORAGE_KEY, name);
  }
}
