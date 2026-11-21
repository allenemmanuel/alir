// ALIR Shelter: progressive enhancements. The site works fully without this file.
(() => {
  "use strict";

  // ----- Mobile navigation -----
  const toggle = document.querySelector(".nav-toggle");
  const menu = document.getElementById("nav-links");
  if (toggle && menu) {
    const setOpen = (open) => {
      menu.classList.toggle("open", open);
      toggle.setAttribute("aria-expanded", String(open));
      toggle.setAttribute("aria-label", open ? "Close menu" : "Open menu");
    };
    toggle.addEventListener("click", () => setOpen(!menu.classList.contains("open")));
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && menu.classList.contains("open")) { setOpen(false); toggle.focus(); }
    });
    document.addEventListener("click", (e) => {
      if (menu.classList.contains("open") && !e.target.closest(".nav-bar")) setOpen(false);
    });
  }

  // ----- Hero: deal the case cards once -----
  const pile = document.querySelector(".pile");
  if (pile) requestAnimationFrame(() => requestAnimationFrame(() => pile.classList.add("dealt")));

  // ----- Footer year -----
  document.querySelectorAll("[data-year]").forEach((el) => { el.textContent = String(new Date().getFullYear()); });

  // ----- Toast (announced to screen readers) -----
  const toast = document.createElement("div");
  toast.className = "toast";
  toast.setAttribute("role", "status");
  toast.setAttribute("aria-live", "polite");
  document.body.appendChild(toast);
  let toastTimer;
  const showToast = (msg) => {
    toast.textContent = msg;
    toast.classList.add("show");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => toast.classList.remove("show"), 2400);
  };

  // ----- Copy account number -----
  const copyText = async (text) => {
    try {
      await navigator.clipboard.writeText(text);
      return true;
    } catch {
      const ta = Object.assign(document.createElement("textarea"), { value: text });
      ta.style.cssText = "position:fixed;opacity:0";
      document.body.appendChild(ta);
      ta.select();
      const ok = document.execCommand("copy");
      ta.remove();
      return ok;
    }
  };
  document.querySelectorAll("[data-copy]").forEach((btn) => {
    const label = btn.textContent;
    btn.addEventListener("click", async () => {
      const ok = await copyText(btn.dataset.copy);
      if (!ok) { showToast("Couldn’t copy. Please select the number and copy it manually."); return; }
      btn.dataset.copied = "true";
      btn.textContent = "Copied";
      showToast("Account number copied");
      setTimeout(() => { btn.dataset.copied = "false"; btn.textContent = label; }, 2000);
    });
  });

  // ----- Gallery lightbox -----
  const gallery = document.querySelector(".gallery");
  if (gallery) {
    const items = [...gallery.querySelectorAll("button[data-full]")];
    const lb = document.createElement("div");
    lb.className = "lightbox";
    lb.setAttribute("role", "dialog");
    lb.setAttribute("aria-modal", "true");
    lb.setAttribute("aria-label", "Photo viewer");
    lb.innerHTML = `
      <img alt="" decoding="async">
      <button type="button" class="lb-close" aria-label="Close photo viewer">&times;</button>
      <button type="button" class="lb-prev" aria-label="Previous photo">&#8249;</button>
      <button type="button" class="lb-next" aria-label="Next photo">&#8250;</button>
      <p class="lb-count" aria-live="polite"></p>`;
    document.body.appendChild(lb);
    const img = lb.querySelector("img");
    const count = lb.querySelector(".lb-count");
    const closeBtn = lb.querySelector(".lb-close");
    let current = 0;
    let lastFocus = null;

    const show = (i) => {
      current = (i + items.length) % items.length;
      const btn = items[current];
      img.src = btn.dataset.full;
      img.alt = btn.querySelector("img").alt;
      count.textContent = `${current + 1} of ${items.length}`;
      // Preload neighbour for instant next
      new Image().src = items[(current + 1) % items.length].dataset.full;
    };
    const open = (i) => {
      lastFocus = document.activeElement;
      show(i);
      lb.classList.add("open");
      document.documentElement.style.overflow = "hidden";
      closeBtn.focus();
    };
    const close = () => {
      lb.classList.remove("open");
      document.documentElement.style.overflow = "";
      lastFocus?.focus();
    };

    items.forEach((btn, i) => btn.addEventListener("click", () => open(i)));
    closeBtn.addEventListener("click", close);
    lb.querySelector(".lb-prev").addEventListener("click", () => show(current - 1));
    lb.querySelector(".lb-next").addEventListener("click", () => show(current + 1));
    lb.addEventListener("click", (e) => { if (e.target === lb) close(); });

    // Swipe on touch devices
    let startX = null;
    lb.addEventListener("touchstart", (e) => { startX = e.touches[0].clientX; }, { passive: true });
    lb.addEventListener("touchend", (e) => {
      if (startX === null) return;
      const dx = e.changedTouches[0].clientX - startX;
      if (Math.abs(dx) > 50) show(current + (dx < 0 ? 1 : -1));
      startX = null;
    });

    document.addEventListener("keydown", (e) => {
      if (!lb.classList.contains("open")) return;
      if (e.key === "Escape") close();
      else if (e.key === "ArrowLeft") show(current - 1);
      else if (e.key === "ArrowRight") show(current + 1);
      else if (e.key === "Tab") {
        // keep focus inside the dialog
        const f = [...lb.querySelectorAll("button")];
        const idx = f.indexOf(document.activeElement);
        e.preventDefault();
        f[(idx + (e.shiftKey ? -1 : 1) + f.length) % f.length].focus();
      }
    });
  }
})();
