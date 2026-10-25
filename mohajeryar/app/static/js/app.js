/* مهاجریار — رفتار رابط */
(function () {
  "use strict";

  const $ = (selector, scope) => (scope || document).querySelector(selector);
  const $$ = (selector, scope) => Array.from((scope || document).querySelectorAll(selector));

  /* ------------------------------------------------------------ theme */
  const root = document.documentElement;
  const themeButton = $("#theme-toggle");
  if (themeButton) {
    themeButton.addEventListener("click", () => {
      const next = root.dataset.theme === "dark" ? "light" : "dark";
      root.dataset.theme = next;
      try {
        localStorage.setItem("mohajeryar-theme", next);
      } catch (error) {
        /* حالت خصوصی مرورگر */
      }
    });
  }

  /* ------------------------------------------------------------ mobile nav */
  const navToggle = $("#nav-toggle");
  const nav = $("#main-nav");
  if (navToggle && nav) {
    navToggle.addEventListener("click", () => {
      const open = nav.classList.toggle("is-open");
      navToggle.setAttribute("aria-expanded", String(open));
    });
    document.addEventListener("click", (event) => {
      if (!nav.classList.contains("is-open")) return;
      if (nav.contains(event.target) || navToggle.contains(event.target)) return;
      nav.classList.remove("is-open");
      navToggle.setAttribute("aria-expanded", "false");
    });
  }

  /* ------------------------------------------------------------ toast */
  const toastEl = $("#toast");
  let toastTimer = null;
  function toast(message) {
    if (!toastEl) return;
    toastEl.textContent = message;
    toastEl.hidden = false;
    window.clearTimeout(toastTimer);
    toastTimer = window.setTimeout(() => {
      toastEl.hidden = true;
    }, 3200);
  }

  /* ------------------------------------------------------------ PWA install */
  let deferredPrompt = null;
  const installButton = $("#install-app");
  window.addEventListener("beforeinstallprompt", (event) => {
    event.preventDefault();
    deferredPrompt = event;
    if (installButton) installButton.hidden = false;
  });
  if (installButton) {
    installButton.addEventListener("click", async () => {
      if (!deferredPrompt) {
        toast("برای نصب، از منوی مرورگر «افزودن به صفحه اصلی» را بزنید.");
        return;
      }
      deferredPrompt.prompt();
      const result = await deferredPrompt.userChoice;
      if (result.outcome === "accepted") toast("اپلیکیشن نصب شد.");
      deferredPrompt = null;
      installButton.hidden = true;
    });
  }
  window.addEventListener("appinstalled", () => {
    if (installButton) installButton.hidden = true;
  });
  if (window.matchMedia("(display-mode: standalone)").matches && installButton) {
    installButton.hidden = true;
  }

  /* ------------------------------------------------------------ service worker */
  if ("serviceWorker" in navigator && location.protocol.startsWith("http")) {
    window.addEventListener("load", () => {
      navigator.serviceWorker.register("/sw.js").catch(() => {
        /* آفلاین یا محیط بدون پشتیبانی */
      });
    });
  }

  /* ------------------------------------------------------------ chat */
  const chatPanel = $("#chat-panel");
  const chatLauncher = $("#chat-launcher");
  const chatClose = $("#chat-close");
  const chatForm = $("#chat-form");
  const chatBody = $("#chat-body");
  const chatInput = $("#chat-input");
  const assessmentId = document.body.dataset.assessmentId || "";
  let chatBusy = false;

  function openChat() {
    if (!chatPanel) return;
    chatPanel.hidden = false;
    if (chatLauncher) chatLauncher.setAttribute("aria-expanded", "true");
    window.setTimeout(() => chatInput && chatInput.focus(), 60);
  }
  function closeChat() {
    if (!chatPanel) return;
    chatPanel.hidden = true;
    if (chatLauncher) chatLauncher.setAttribute("aria-expanded", "false");
  }
  if (chatLauncher) {
    chatLauncher.addEventListener("click", () => {
      if (chatPanel && chatPanel.hidden) openChat();
      else closeChat();
    });
  }
  if (chatClose) chatClose.addEventListener("click", closeChat);
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && chatPanel && !chatPanel.hidden) closeChat();
  });

  function addMessage(text, kind) {
    if (!chatBody) return null;
    const bubble = document.createElement("div");
    bubble.className = "chat-message chat-message--" + (kind || "bot");
    bubble.textContent = text;
    chatBody.appendChild(bubble);
    chatBody.scrollTop = chatBody.scrollHeight;
    return bubble;
  }

  if (chatForm) {
    chatForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      const question = (chatInput.value || "").trim();
      if (!question || chatBusy) return;
      chatBusy = true;
      addMessage(question, "user");
      chatInput.value = "";
      const typing = addMessage("در حال بررسی داده‌های ارزیابی…", "bot chat-message--typing");
      try {
        const response = await fetch("/api/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ question, assessment_id: assessmentId || null }),
        });
        if (!response.ok) throw new Error("request failed");
        const data = await response.json();
        if (typing) typing.remove();
        addMessage(data.answer || "پاسخی دریافت نشد.", "bot");
      } catch (error) {
        if (typing) typing.remove();
        addMessage("ارتباط با سرور برقرار نشد. اتصال اینترنت و اجرای سرور را بررسی کنید.", "bot");
      } finally {
        chatBusy = false;
        if (chatInput) chatInput.focus();
      }
    });
    if (chatInput) {
      chatInput.addEventListener("keydown", (event) => {
        if (event.key === "Enter" && !event.shiftKey) {
          event.preventDefault();
          chatForm.requestSubmit();
        }
      });
    }
  }

  /* ------------------------------------------------------------ results filters */
  const filterButtons = $$("[data-filter]");
  const programCards = $$("[data-status]");
  if (filterButtons.length && programCards.length) {
    filterButtons.forEach((button) => {
      button.addEventListener("click", () => {
        const filter = button.dataset.filter;
        filterButtons.forEach((item) => item.classList.toggle("is-active", item === button));
        let visible = 0;
        programCards.forEach((card) => {
          const show = filter === "all" || card.dataset.status === filter;
          card.hidden = !show;
          if (show) visible += 1;
        });
        const empty = $("#empty-filter");
        if (empty) empty.hidden = visible > 0;
      });
    });
  }

  /* ------------------------------------------------------------ print */
  $$("[data-print]").forEach((button) => button.addEventListener("click", () => window.print()));
  window.addEventListener("beforeprint", () => {
    $$("details").forEach((item) => {
      if (!item.open) {
        item.dataset.wasClosed = "1";
        item.open = true;
      }
    });
  });
  window.addEventListener("afterprint", () => {
    $$("details[data-was-closed]").forEach((item) => {
      item.open = false;
      delete item.dataset.wasClosed;
    });
  });

  /* ------------------------------------------------------------ wizard */
  const form = $("#wizard-form");
  if (form) initWizard(form);

  function initWizard(wizard) {
    const steps = $$(".wizard-step", wizard);
    const total = steps.length;
    const progressBar = $("#progress-bar");
    const progressItems = $$("[data-progress-step]");
    const prev = $("#wizard-prev");
    const next = $("#wizard-next");
    const submit = $("#wizard-submit");
    const status = $("#wizard-status");
    let current = 1;

    const stepForField = (name) => {
      const clean = (name || "").replace("[]", "");
      if (/^(name|birth_date|nationality|residence|marital_status|dependents|spouse_)/.test(clean)) return 1;
      if (/^(education_|graduation_year|eca|recognition|nz_qualification_level)/.test(clean)) return 2;
      if (/^(english_|german_|french_)/.test(clean)) return 3;
      if (/^(occupation_|experience_|canadian_|australian_|nz_experience|skills_assessment|registration_)/.test(clean)) return 4;
      if (/^(has_job_offer|job_offer_|savings_|monthly_income_|passive_income_|remote_work)/.test(clean)) return 5;
      if (/^(target_countries|priorities|max_budget_|priorities|prior_|relatives_|willing_|notes|passport_|birth_certificate|education_transcripts|language_certificate|employment_letters|police_clearance|medical|proof_of_funds|doc_eca|marriage_)/.test(clean)) return 6;
      return 1;
    };

    function showStep(index, scroll) {
      current = Math.min(total, Math.max(1, index));
      steps.forEach((step) => step.classList.toggle("is-active", Number(step.dataset.step) === current));
      progressItems.forEach((item) => {
        const value = Number(item.dataset.progressStep);
        item.classList.toggle("is-active", value === current);
        item.classList.toggle("is-done", value < current);
      });
      if (progressBar) progressBar.style.width = (current / total) * 100 + "%";
      if (prev) prev.disabled = current === 1;
      if (next) next.hidden = current === total;
      if (submit) submit.hidden = current !== total;
      if (status) status.textContent = "گام " + toFa(current) + " از " + toFa(total);
      if (scroll !== false) {
        const head = $(".wizard-progress");
        if (head) head.scrollIntoView({ behavior: "smooth", block: "start" });
      }
    }

    function toFa(value) {
      return String(value).replace(/\d/g, (digit) => "۰۱۲۳۴۵۶۷۸۹"[Number(digit)]);
    }

    function validateStep() {
      const active = steps.find((step) => Number(step.dataset.step) === current);
      if (!active) return true;
      let firstInvalid = null;
      $$("input, select, textarea", active).forEach((field) => {
        if (!field.willValidate || field.disabled) return;
        field.classList.remove("is-invalid");
        if (!field.checkValidity()) {
          field.classList.add("is-invalid");
          if (!firstInvalid) firstInvalid = field;
        }
      });
      if (firstInvalid) {
        firstInvalid.reportValidity();
        firstInvalid.focus();
        toast("لطفاً فیلدهای مشخص‌شده را کامل کنید.");
        return false;
      }
      return true;
    }

    if (next) {
      next.addEventListener("click", () => {
        if (!validateStep()) return;
        showStep(current + 1);
        persistDraft();
      });
    }
    if (prev) {
      prev.addEventListener("click", () => {
        showStep(current - 1);
        persistDraft();
      });
    }
    progressItems.forEach((item) => {
      item.addEventListener("click", () => {
        const target = Number(item.dataset.progressStep);
        if (target < current) showStep(target);
      });
    });

    /* --- فیلدهای شرطی --- */
    const spouseToggle = $("[data-spouse-toggle]", wizard);
    const spouseFields = $("[data-spouse-fields]", wizard);
    function syncSpouse() {
      if (!spouseFields || !spouseToggle) return;
      spouseFields.hidden = !spouseToggle.checked;
    }
    if (spouseToggle) {
      spouseToggle.addEventListener("change", syncSpouse);
      syncSpouse();
    }

    const jobToggle = $("[data-job-toggle]", wizard);
    const jobFields = $$("[data-job-fields]", wizard);
    function syncJob() {
      jobFields.forEach((group) => {
        group.hidden = !(jobToggle && jobToggle.checked);
      });
    }
    if (jobToggle) {
      jobToggle.addEventListener("change", syncJob);
      syncJob();
    }

    const englishTest = $('[data-test-select="english"]', wizard);
    const englishScores = $('[data-test-scores="english"]', wizard);
    function syncScores() {
      if (!englishScores || !englishTest) return;
      englishScores.hidden = !englishTest.value;
    }
    if (englishTest) {
      englishTest.addEventListener("change", syncScores);
      syncScores();
    }

    /* --- پیش‌نویس در مرورگر --- */
    const DRAFT_KEY = "mohajeryar-draft-v1";
    function persistDraft() {
      if (!wizard.dataset.persist) return;
      try {
        const payload = { step: current, fields: [], checks: {} };
        $$("input, select, textarea", wizard).forEach((field) => {
          if (!field.name) return;
          if (field.type === "checkbox") {
            if (!payload.checks[field.name]) payload.checks[field.name] = [];
            if (field.checked) {
              if (field.value && field.value !== "on") payload.checks[field.name].push(field.value);
              else payload.checks[field.name].push("__on__");
            }
          } else if (field.type !== "file") {
            payload.fields.push([field.name, field.value]);
          }
        });
        localStorage.setItem(DRAFT_KEY, JSON.stringify(payload));
      } catch (error) {
        /* ignore quota/private mode */
      }
    }

    function restoreDraft() {
      if (!wizard.dataset.persist) return;
      try {
        const raw = localStorage.getItem(DRAFT_KEY);
        if (!raw) return;
        const payload = JSON.parse(raw);
        (payload.fields || []).forEach(([name, value]) => {
          const field = wizard.elements.namedItem(name);
          if (field && !field.value && value) field.value = value;
        });
        Object.entries(payload.checks || {}).forEach(([name, values]) => {
          const list = wizard.querySelectorAll('[name="' + name + '"]');
          list.forEach((field) => {
            if (field.type !== "checkbox") return;
            field.checked = field.value && field.value !== "on"
              ? values.indexOf(field.value) !== -1
              : values.indexOf("__on__") !== -1;
          });
        });
        if (payload.step) showStep(payload.step, false);
        syncSpouse();
        syncJob();
        syncScores();
        toast("پیش‌نویس ذخیره‌شده بازیابی شد.");
      } catch (error) {
        /* ignore */
      }
    }

    // پیش‌نویس فقط برای فرم تازه (نه ویرایش پروفایل یا فرم دارای خطا)
    wizard.dataset.persist = wizard.querySelector('[name="profile_id"]')?.value ? "0" : "1";
    if (wizard.dataset.persist === "1") {
      wizard.addEventListener("input", persistDraft);
      wizard.addEventListener("change", persistDraft);
      if (!wizard.querySelector('[name="birth_date"]').value && !document.querySelector(".alert--error")) {
        restoreDraft();
      }
    }

    /* --- پرش به گام دارای خطا --- */
    const errorFields = (wizard.dataset.errorFields || "").split(",").filter(Boolean);
    if (errorFields.length) {
      const stepNumbers = errorFields.map(stepForField).filter(Boolean);
      const first = Math.min.apply(null, stepNumbers);
      if (isFinite(first)) showStep(first, false);
    }

    /* --- تمرکز اولیه روی کشور هدف --- */
    const focus = new URLSearchParams(location.search).get("focus");
    if (focus) {
      const box = wizard.querySelector('input[name="target_countries"][value="' + focus.toUpperCase() + '"]');
      if (box) box.checked = true;
    }

    wizard.addEventListener("submit", () => {
      if (submit) {
        submit.disabled = true;
        submit.textContent = "در حال محاسبه…";
      }
    });

    showStep(current, false);
  }
})();
