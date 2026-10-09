/* AtirMagaz — sahifa interaktivligi (kutubxonalarsiz) */
(function () {
  "use strict";

  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));
  const fmt = (n) => Math.round(n).toLocaleString("ru-RU").replace(/,/g, " ") + " so'm";
  const csrf = () => ($("#csrf-holder input[name=csrfmiddlewaretoken]") || {}).value || "";
  const desktop = () => window.matchMedia("(min-width: 1081px)").matches;

  /* ---------- Bildirishnomalar ---------- */
  const toasts = $("#toasts");
  function dismiss(el, delay) {
    setTimeout(() => {
      el.classList.add("is-leaving");
      el.addEventListener("animationend", () => el.remove(), { once: true });
    }, delay);
  }
  function toast(text, type = "success") {
    const el = document.createElement("div");
    el.className = "toast toast--" + type;
    el.innerHTML = '<svg class="ic"><use href="#i-check"/></svg><span></span>';
    el.querySelector("span").textContent = text;
    toasts.appendChild(el);
    dismiss(el, 3800);
  }
  $$(".toast", toasts).forEach((el, i) => dismiss(el, 4200 + i * 400));

  /* ---------- Sarlavha soyasi va «yuqoriga» ---------- */
  const header = $("#header");
  const toTop = $(".to-top");
  const onScroll = () => {
    const y = window.scrollY;
    header && header.classList.toggle("is-scrolled", y > 8);
    toTop && toTop.classList.toggle("is-visible", y > 900);
  };
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();

  /* ---------- Mobil menyu ---------- */
  function openDrawer(name) {
    const d = $("#drawer-" + name);
    if (!d) return;
    d.classList.add("is-open");
    d.setAttribute("aria-hidden", "false");
    document.body.classList.add("no-scroll");
  }
  function closeDrawers() {
    $$(".drawer.is-open").forEach((d) => { d.classList.remove("is-open"); d.setAttribute("aria-hidden", "true"); });
    closeFilters();
    document.body.classList.remove("no-scroll");
  }
  $$("[data-drawer-open]").forEach((b) => b.addEventListener("click", () => openDrawer(b.dataset.drawerOpen)));
  $$("[data-drawer-close]").forEach((b) => b.addEventListener("click", closeDrawers));

  /* ---------- Qidiruv ---------- */
  const panel = $("#search-panel");
  const searchInput = panel && $("input[name=q]", panel);
  const box = panel && $("[data-suggest-box]", panel);
  function toggleSearch(force) {
    const show = force !== undefined ? force : panel.hidden;
    panel.hidden = !show;
    if (show) setTimeout(() => searchInput.focus(), 30);
  }
  $$("[data-search-toggle]").forEach((b) => b.addEventListener("click", () => toggleSearch()));
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") { panel && toggleSearch(false); closeDrawers(); }
    if (e.key === "/" && !/input|textarea|select/i.test(document.activeElement.tagName)) {
      e.preventDefault(); toggleSearch(true);
    }
  });
  document.addEventListener("click", (e) => {
    if (panel && !panel.hidden && !header.contains(e.target)) toggleSearch(false);
  });

  let suggestTimer, suggestCtrl;
  searchInput && searchInput.addEventListener("input", () => {
    clearTimeout(suggestTimer);
    const q = searchInput.value.trim();
    if (q.length < 2) { box.innerHTML = ""; return; }
    suggestTimer = setTimeout(async () => {
      suggestCtrl && suggestCtrl.abort();
      suggestCtrl = new AbortController();
      try {
        const url = searchInput.dataset.suggestUrl + "?q=" + encodeURIComponent(q);
        const data = await (await fetch(url, { signal: suggestCtrl.signal })).json();
        renderSuggest(data, q);
      } catch (_) { /* bekor qilingan so'rov */ }
    }, 180);
  });
  function renderSuggest(data, q) {
    box.innerHTML = "";
    if (!data.results.length && !data.brands.length) {
      box.innerHTML = '<p class="suggest__empty"></p>';
      box.firstChild.textContent = "«" + q + "» bo'yicha hech narsa topilmadi";
      return;
    }
    data.brands.forEach((b) => {
      const a = document.createElement("a");
      a.href = b.url;
      a.innerHTML = '<span class="suggest__dot" style="background:var(--ink)"></span><span><span class="suggest__title"></span><br><span class="suggest__brand">Brend</span></span>';
      a.querySelector(".suggest__title").textContent = b.title;
      box.appendChild(a);
    });
    data.results.forEach((r) => {
      const a = document.createElement("a");
      a.href = r.url;
      a.innerHTML = '<span class="suggest__dot"></span><span><span class="suggest__title"></span><br><span class="suggest__brand"></span></span><span class="suggest__price"></span>';
      a.querySelector(".suggest__dot").style.background = r.color;
      a.querySelector(".suggest__title").textContent = r.title;
      a.querySelector(".suggest__brand").textContent = r.brand;
      a.querySelector(".suggest__price").textContent = r.price;
      box.appendChild(a);
    });
    const all = document.createElement("a");
    all.href = data.all_url;
    all.className = "suggest__all";
    all.textContent = "Barcha natijalarni ko'rish →";
    box.appendChild(all);
  }

  /* ---------- AJAX: savatcha va sevimlilar ---------- */
  function bump(el, value) {
    if (!el) return;
    el.textContent = value;
    el.hidden = !value;
    el.classList.remove("bump"); void el.offsetWidth; el.classList.add("bump");
  }
  async function post(form) {
    const res = await fetch(form.action, {
      method: "POST",
      body: new FormData(form),
      headers: { "X-Requested-With": "XMLHttpRequest", "X-CSRFToken": csrf() },
    });
    if (!res.ok) throw new Error(res.status);
    return res.json();
  }
  document.addEventListener("submit", async (e) => {
    const form = e.target;
    if (form.matches("[data-cart-form]")) {
      e.preventDefault();
      const btn = form.querySelector("button[type=submit]");
      try {
        const data = await post(form);
        bump($("[data-cart-count]"), data.count);
        toast(data.message, data.ok ? "success" : "warning");
        if (btn && data.ok) {
          btn.classList.add("is-done");
          setTimeout(() => btn.classList.remove("is-done"), 1400);
        }
      } catch (_) { form.submit(); }
    }
    if (form.matches("[data-wishlist-form]")) {
      e.preventDefault();
      try {
        const data = await post(form);
        form.querySelector(".wish-btn").classList.toggle("is-active", data.added);
        bump($("[data-wishlist-count]"), data.count);
        toast(data.added ? "Sevimlilarga qo'shildi" : "Sevimlilardan olib tashlandi");
        const card = form.closest("[data-remove-on-unwish]");
        if (card && !data.added) {
          card.style.transition = "opacity .3s"; card.style.opacity = "0";
          setTimeout(() => { card.remove(); if (!$("[data-remove-on-unwish]")) location.reload(); }, 300);
        }
      } catch (_) { form.submit(); }
    }
  });

  /* ---------- Gorizontal lentalar ---------- */
  $$("[data-rail]").forEach((nav) => {
    const rail = document.getElementById(nav.dataset.rail);
    if (!rail) return;
    const step = () => rail.clientWidth * 0.8;
    $("[data-prev]", nav).addEventListener("click", () => rail.scrollBy({ left: -step(), behavior: "smooth" }));
    $("[data-next]", nav).addEventListener("click", () => rail.scrollBy({ left: step(), behavior: "smooth" }));
  });

  /* ---------- Ko'rinishga chiqish animatsiyasi ---------- */
  const revealEls = $$(".reveal");
  if ("IntersectionObserver" in window && revealEls.length) {
    const io = new IntersectionObserver((entries) => entries.forEach((en) => {
      if (en.isIntersecting) { en.target.classList.add("is-in"); io.unobserve(en.target); }
    }), { rootMargin: "0px 0px -60px 0px" });
    revealEls.forEach((el) => io.observe(el));
  } else revealEls.forEach((el) => el.classList.add("is-in"));

  /* ---------- Promokodni nusxalash ---------- */
  $$("[data-copy]").forEach((b) => b.addEventListener("click", async () => {
    try { await navigator.clipboard.writeText(b.dataset.copy); toast("Promokod nusxalandi: " + b.dataset.copy); }
    catch (_) { toast("Promokod: " + b.dataset.copy); }
  }));

  /* ---------- Son tanlash (−/+) ---------- */
  $$("[data-qty]").forEach((wrap) => {
    const input = $("input", wrap);
    const max = () => parseInt(input.max || "99", 10);
    const set = (v) => {
      const val = Math.max(parseInt(input.min || "1", 10), Math.min(max(), v));
      if (val === parseInt(input.value, 10)) return;
      input.value = val;
      if (wrap.dataset.qty === "submit") input.form.submit();
    };
    $("[data-minus]", wrap).addEventListener("click", () => set(parseInt(input.value, 10) - 1));
    $("[data-plus]", wrap).addEventListener("click", () => set(parseInt(input.value, 10) + 1));
    input.addEventListener("change", () => wrap.dataset.qty === "submit" && input.form.submit());
  });

  /* ---------- Atir sahifasi: hajm tanlash ---------- */
  const buyForm = $("[data-buy]");
  if (buyForm) {
    const priceNow = $("[data-price-now]");
    const priceOld = $("[data-price-old]");
    const badge = $("[data-price-badge]");
    const stockNote = $("[data-stock-note]");
    const submit = $("[data-buy-submit]", buyForm);
    const qty = $("input[name=quantity]", buyForm);
    const update = () => {
      const r = $("input[name=variant]:checked", buyForm);
      if (!r) return;
      const d = r.dataset;
      const stock = parseInt(d.stock, 10);
      priceNow.textContent = fmt(+d.price);
      priceOld.textContent = d.old ? fmt(+d.old) : "";
      priceOld.hidden = !d.old;
      badge.textContent = d.discount ? "−" + d.discount + "%" : "";
      badge.hidden = !d.discount;
      qty.max = Math.max(stock, 1);
      if (+qty.value > stock) qty.value = Math.max(1, stock);
      submit.disabled = stock === 0;
      submit.querySelector("span").textContent = stock === 0 ? "Tugagan" : "Savatga qo'shish";
      stockNote.classList.toggle("stock-note--low", stock <= 3);
      stockNote.textContent = stock === 0 ? "Hozircha mavjud emas" : stock <= 3 ? "Oz qoldi: " + stock + " dona" : "Omborda bor — bugun jo'natamiz";
      $("[data-vol-label]").textContent = r.closest(".vol").querySelector("b").textContent;
    };
    $$("input[name=variant]", buyForm).forEach((r) => r.addEventListener("change", update));
    update();
  }

  /* ---------- Tablar ---------- */
  $$("[data-tabs]").forEach((tabs) => {
    const buttons = $$("[data-tab]", tabs);
    const show = (id, scroll) => {
      buttons.forEach((b) => b.classList.toggle("is-active", b.dataset.tab === id));
      $$("[data-panel]", tabs).forEach((p) => { p.hidden = p.dataset.panel !== id; });
      if (scroll) tabs.scrollIntoView({ behavior: "smooth", block: "start" });
    };
    buttons.forEach((b) => b.addEventListener("click", () => show(b.dataset.tab)));
    const fromHash = () => {
      const id = location.hash.slice(1);
      if (buttons.some((b) => b.dataset.tab === id)) show(id, true);
    };
    $$("a[href^='#']").forEach((a) => a.addEventListener("click", () => setTimeout(fromHash, 0)));
    fromHash();
  });

  /* ---------- Katalog filtrlari ---------- */
  const filters = $("#filters");
  let overlay;
  function closeFilters() {
    if (!filters) return;
    filters.classList.remove("is-open");
    overlay && overlay.remove();
    overlay = null;
  }
  if (filters) {
    $$("[data-filters-open]").forEach((b) => b.addEventListener("click", () => {
      filters.classList.add("is-open");
      overlay = document.createElement("div");
      overlay.className = "filters-overlay";
      overlay.addEventListener("click", closeDrawers);
      document.body.appendChild(overlay);
      document.body.classList.add("no-scroll");
    }));
    $$("[data-filters-close]").forEach((b) => b.addEventListener("click", closeDrawers));
    filters.addEventListener("change", (e) => {
      if (desktop() && e.target.matches("input[type=checkbox], input[type=radio]")) filters.requestSubmit();
    });
  }
  $$("[data-autosubmit]").forEach((el) => el.addEventListener("change", () => el.form.requestSubmit()));

  /* ---------- Atir tanlash testi ---------- */
  const quiz = $("[data-quiz]");
  if (quiz) {
    const steps = $$(".quiz__step", quiz);
    const bars = $$(".quiz__progress i", quiz);
    let i = 0;
    const go = (n) => {
      i = Math.max(0, Math.min(steps.length - 1, n));
      steps.forEach((s, k) => s.classList.toggle("is-active", k === i));
      bars.forEach((b, k) => b.classList.toggle("on", k <= i));
      $("[data-quiz-back]", quiz).style.visibility = i ? "visible" : "hidden";
      const last = i === steps.length - 1;
      $("[data-quiz-next]", quiz).hidden = last;
      $("[data-quiz-submit]", quiz).hidden = !last;
    };
    const answered = () => !!$("input:checked", steps[i]);
    $("[data-quiz-back]", quiz).addEventListener("click", () => go(i - 1));
    $("[data-quiz-next]", quiz).addEventListener("click", () => answered() ? go(i + 1) : toast("Variantlardan birini tanlang", "warning"));
    quiz.addEventListener("change", () => {
      if (i < steps.length - 1) setTimeout(() => go(i + 1), 260);
    });
    quiz.addEventListener("submit", (e) => {
      if (!steps.every((s) => $("input:checked", s))) { e.preventDefault(); toast("Barcha savollarga javob bering", "warning"); }
    });
    go(0);
  }

  /* ---------- Rasmiylashtirish: jonli hisob ---------- */
  const co = $("[data-checkout]");
  if (co) {
    const d = co.dataset;
    const addressField = $("[data-address-field]");
    const giftNote = $("[data-gift-note]");
    const recalc = () => {
      const delivery = ($("input[name=delivery]:checked", co) || {}).value || "courier";
      const region = $("select[name=region]", co).value;
      const gift = $("input[name=gift_wrap]", co).checked;
      const after = +d.subtotal - +d.discount;
      let cost = 0;
      if (delivery !== "pickup" && after < +d.freeFrom) cost = region === "tashkent" ? +d.tashkent : +d.regions;
      const wrap = gift ? +d.wrap : 0;
      $("[data-sum-delivery]").textContent = cost ? fmt(cost) : "Bepul";
      $("[data-sum-wrap-row]").hidden = !gift;
      $("[data-sum-wrap]").textContent = fmt(wrap);
      $("[data-sum-total]").textContent = fmt(after + cost + wrap);
      addressField.hidden = delivery === "pickup";
      giftNote.hidden = !gift;
    };
    co.addEventListener("change", recalc);
    recalc();
  }

  /* ---------- Telefon raqamini chiroyli yozish ---------- */
  $$("input[inputmode=tel]").forEach((input) => input.addEventListener("blur", () => {
    let digits = input.value.replace(/\D/g, "");
    if (digits.length === 9) digits = "998" + digits;
    if (digits.length === 12 && digits.startsWith("998")) {
      input.value = "+998 " + digits.slice(3, 5) + " " + digits.slice(5, 8) + " " + digits.slice(8, 10) + " " + digits.slice(10);
    }
  }));
})();
