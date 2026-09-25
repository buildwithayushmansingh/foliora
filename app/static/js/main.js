(() => {
  // Mobile menu
  const toggle = document.querySelector(".nav__toggle");
  const menu = document.getElementById("menu");
  if (toggle && menu) {
    const set = (open) => {
      menu.classList.toggle("is-open", open);
      toggle.setAttribute("aria-expanded", String(open));
      toggle.textContent = open ? "Close" : "Menu";
    };
    toggle.addEventListener("click", () => set(!menu.classList.contains("is-open")));
    menu.addEventListener("click", (e) => { if (e.target.closest("a")) set(false); });
    document.addEventListener("keydown", (e) => { if (e.key === "Escape") set(false); });
  }

  // Scale the inline thumbnail so the whole desktop page fits the card
  const thumb = document.querySelector(".thumb__screen");
  const thumbFrame = thumb && thumb.querySelector("iframe");
  if (thumbFrame) {
    const fit = () => { thumbFrame.style.transform = "scale(" + thumb.clientWidth / 1280 + ")"; };
    fit();
    window.addEventListener("resize", fit);
    if ("ResizeObserver" in window) new ResizeObserver(fit).observe(thumb);
  }
  // Full-screen viewer with desktop / mobile modes
  const viewer = document.getElementById("viewer");
  if (viewer) {
    const stage = viewer.querySelector(".viewer__stage");
    const frame = viewer.querySelector("iframe");
    const modes = viewer.querySelectorAll("[data-mode]");
    const setMode = (mode) => {
      stage.dataset.mode = mode;
      modes.forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.mode === mode)));
    };
    const close = () => { viewer.close(); };
    document.querySelectorAll("[data-open]").forEach((btn) =>
      btn.addEventListener("click", () => {
        if (!frame.getAttribute("src")) frame.src = viewer.dataset.url; // load only when opened
        setMode(btn.dataset.open);
        viewer.showModal();
        document.documentElement.style.overflow = "hidden";
      })
    );
    modes.forEach((b) => b.addEventListener("click", () => setMode(b.dataset.mode)));
    viewer.querySelector("[data-close]").addEventListener("click", close);
    viewer.addEventListener("close", () => { document.documentElement.style.overflow = ""; });
  }

  const year = document.getElementById("year");
  if (year) year.textContent = new Date().getFullYear();
})();
