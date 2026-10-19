(function () {
  "use strict";

  function initShell() {
    var toggle = document.querySelector(".nav-toggle");
    var nav = document.getElementById("primary-nav");
    if (!toggle || !nav) return;

    function closeNav() {
      nav.classList.remove("is-open");
      toggle.setAttribute("aria-expanded", "false");
    }

    toggle.addEventListener("click", function () {
      var isOpen = nav.classList.toggle("is-open");
      toggle.setAttribute("aria-expanded", String(isOpen));
    });

    nav.querySelectorAll("a").forEach(function (link) {
      link.addEventListener("click", closeNav);
    });

    document.addEventListener("click", function (event) {
      if (!nav.contains(event.target) && event.target !== toggle) closeNav();
    });

    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape") closeNav();
    });
  }

  function initSearch() {
    var trigger = document.querySelector("[data-search-trigger]");
    var dialog = document.getElementById("search-dialog");
    if (!trigger || !dialog) return;

    var input = dialog.querySelector(".search-dialog__input");
    var results = Array.prototype.slice.call(
      dialog.querySelectorAll("[data-search-result]")
    );
    var activeIndex = -1;

    function visibleResults() {
      return results.filter(function (result) {
        return !result.closest("li").hidden;
      });
    }

    function setActive(index) {
      var visible = visibleResults();
      activeIndex = visible.length ? (index + visible.length) % visible.length : -1;
      results.forEach(function (result) {
        result.setAttribute("aria-selected", "false");
      });
      if (activeIndex >= 0) {
        visible[activeIndex].setAttribute("aria-selected", "true");
      }
    }

    function filterResults() {
      var query = (input ? input.value : "").trim().toLowerCase();
      results.forEach(function (result) {
        var matches = !query || result.textContent.toLowerCase().indexOf(query) !== -1;
        result.closest("li").hidden = !matches;
      });
      setActive(0);
    }

    function openSearch() {
      if (typeof dialog.showModal === "function") {
        dialog.showModal();
      } else {
        dialog.setAttribute("open", "");
      }
      trigger.setAttribute("aria-expanded", "true");
      filterResults();
      window.requestAnimationFrame(function () {
        if (input) input.focus();
      });
    }

    function closeSearch() {
      if (typeof dialog.close === "function" && dialog.open) {
        dialog.close();
      } else {
        dialog.removeAttribute("open");
      }
      trigger.setAttribute("aria-expanded", "false");
      trigger.focus();
    }

    trigger.addEventListener("click", openSearch);
    dialog.querySelectorAll("[data-close-search]").forEach(function (closeButton) {
      closeButton.addEventListener("click", closeSearch);
    });
    dialog.addEventListener("click", function (event) {
      if (event.target === dialog) closeSearch();
    });
    dialog.addEventListener("close", function () {
      trigger.setAttribute("aria-expanded", "false");
    });
    if (input) input.addEventListener("input", filterResults);
    if (input) {
      input.addEventListener("keydown", function (event) {
        var visible = visibleResults();
        if (event.key === "ArrowDown") {
          event.preventDefault();
          setActive(activeIndex + 1);
        } else if (event.key === "ArrowUp") {
          event.preventDefault();
          setActive(activeIndex - 1);
        } else if (event.key === "Enter" && activeIndex >= 0 && visible.length) {
          event.preventDefault();
          visible[activeIndex].click();
        }
      });
    }
    document.addEventListener("keydown", function (event) {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        if (dialog.open) {
          closeSearch();
        } else {
          openSearch();
        }
      }
      if (event.key === "Escape" && dialog.open) {
        event.preventDefault();
        closeSearch();
      }
    });
  }

  function initReadingProgress() {
    var progress = document.querySelector(".reading-progress");
    if (!progress) return;

    function updateProgress() {
      var maxScroll = document.documentElement.scrollHeight - window.innerHeight;
      var ratio = maxScroll > 0 ? window.scrollY / maxScroll : 1;
      progress.style.transform = "scaleX(" + Math.max(0, Math.min(1, ratio)) + ")";
    }

    window.addEventListener("scroll", updateProgress, { passive: true });
    window.addEventListener("resize", updateProgress);
    updateProgress();
  }

  function initMaterial() {
    document.querySelectorAll(".collapsible__toggle").forEach(function (toggle) {
      var targetId = toggle.getAttribute("aria-controls");
      var target = targetId && document.getElementById(targetId);
      if (!target) return;

      toggle.addEventListener("click", function () {
        var willOpen = target.hidden;
        target.hidden = !willOpen;
        toggle.setAttribute("aria-expanded", String(willOpen));
        toggle.textContent = willOpen ? "Свернуть" : "Развернуть";
      });
    });
  }

  function initLogin() {
    var form = document.querySelector("[data-login]");
    if (!form) return;

    var email = document.getElementById("email");
    var password = document.getElementById("password");

    function setError(field, message) {
      var helper = document.getElementById(field.id + "-help");
      field.setAttribute("aria-invalid", message ? "true" : "false");
      if (helper) {
        helper.classList.toggle("field__helper--error", Boolean(message));
        helper.textContent = message || (field.id === "email"
          ? "Только @sberbank.ru или @omega.sbrf.ru"
          : "");
      }
    }

    function validateField(field) {
      if (!field.value.trim()) {
        setError(field, "Заполните это поле.");
        return false;
      }
      if (field === email && !/@(?:sberbank\.ru|omega\.sbrf\.ru)$/i.test(field.value.trim())) {
        setError(field, "Используйте корпоративный домен @sberbank.ru или @omega.sbrf.ru.");
        return false;
      }
      setError(field, "");
      return true;
    }

    [email, password].forEach(function (field) {
      if (!field) return;
      field.addEventListener("blur", function () {
        validateField(field);
      });
      field.addEventListener("input", function () {
        if (field.getAttribute("aria-invalid") === "true") validateField(field);
      });
    });

    form.addEventListener("submit", function (event) {
      var emailValid = validateField(email);
      var passwordValid = validateField(password);
      var valid = emailValid && passwordValid;
      if (!valid) event.preventDefault();
    });
  }

  function showToast(message) {
    var existing = document.querySelector(".toast");
    if (existing) existing.remove();
    var el = document.createElement("div");
    el.className = "toast";
    el.setAttribute("role", "status");
    el.textContent = message;
    document.body.appendChild(el);
    requestAnimationFrame(function () {
      el.classList.add("toast--visible");
    });
    setTimeout(function () {
      el.classList.remove("toast--visible");
      setTimeout(function () {
        el.remove();
      }, 200);
    }, 2800);
  }

  function initVoting() {
    var ballot = document.querySelector("[data-voting]");
    if (!ballot) return;

    var status = document.getElementById("vote-status");
    var confirmBtn = document.getElementById("confirm-vote");
    var selectedTopic = null;
    var savedTopic = null;
    try {
      savedTopic = sessionStorage.getItem("digest-cds-vote");
    } catch (error) {
      savedTopic = null;
    }

    if (savedTopic) {
      var savedRow = Array.prototype.slice.call(
        ballot.querySelectorAll(".topic-ballot__row")
      ).find(function (row) {
        return row.getAttribute("data-topic") === savedTopic;
      });
      if (savedRow) {
        selectedTopic = savedTopic;
        savedRow.classList.add("topic-ballot__row--selected");
        savedRow.setAttribute("aria-checked", "true");
        if (status) status.textContent = "Ваш голос: " + savedTopic;
      }
    }

    function selectRow(row) {
      ballot.querySelectorAll(".topic-ballot__row").forEach(function (r) {
        r.classList.remove("topic-ballot__row--selected");
        r.setAttribute("aria-checked", "false");
      });
      row.classList.add("topic-ballot__row--selected");
      row.setAttribute("aria-checked", "true");
      selectedTopic = row.getAttribute("data-topic");
      if (status) {
        status.textContent = "Выбор: «" + selectedTopic + "» (нажмите «Подтвердить голос»)";
      }
    }

    ballot.querySelectorAll(".topic-ballot__row").forEach(function (row) {
      row.addEventListener("click", function () {
        selectRow(row);
      });
      row.addEventListener("keydown", function (e) {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          selectRow(row);
        }
        if (e.key === "ArrowDown" || e.key === "ArrowUp") {
          e.preventDefault();
          var allRows = Array.prototype.slice.call(
            ballot.querySelectorAll(".topic-ballot__row")
          );
          var index = allRows.indexOf(row);
          var nextIndex = e.key === "ArrowDown"
            ? (index + 1) % allRows.length
            : (index - 1 + allRows.length) % allRows.length;
          allRows[nextIndex].focus();
        }
      });
    });

    if (confirmBtn) {
      confirmBtn.addEventListener("click", function () {
        if (!selectedTopic) {
          showToast("Сначала выберите тему");
          return;
        }
        if (status) {
          status.textContent = "Ваш голос: " + selectedTopic;
        }
        try {
          sessionStorage.setItem("digest-cds-vote", selectedTopic);
        } catch (error) {
          /* Storage is optional in the static prototype. */
        }
      });
    }
  }

  function initKnowledge() {
    var root = document.querySelector("[data-knowledge]");
    if (!root) return;

    var search = document.getElementById("kb-search");
    var role = document.getElementById("filter-role");
    var tag = document.getElementById("filter-tag");
    var format = document.getElementById("filter-format");
    var topic = document.getElementById("filter-topic");
    var countEl = document.getElementById("kb-count");
    var emptyEl = document.getElementById("kb-empty");
    var loadMore = document.getElementById("kb-load-more");
    var skeleton = document.getElementById("kb-skeleton");
    var rows = Array.prototype.slice.call(root.querySelectorAll(".material-list-row"));
    var extrasExpanded = false;

    function tokens(str) {
      return (str || "")
        .toLowerCase()
        .split(/[\s,.#]+/)
        .filter(Boolean);
    }

    function rowMatches(row) {
      var q = tokens(search && search.value);
      var roleVal = role ? role.value : "";
      var tagVal = tag ? tag.value : "";
      var formatVal = format ? format.value : "";
      var topicVal = topic ? topic.value : "";

      var rowRole = (row.getAttribute("data-role") || "").split(/\s+/);
      var rowTags = (row.getAttribute("data-tags") || "").split(/\s+/);
      var rowFormat = row.getAttribute("data-format") || "";
      var rowTopic = row.getAttribute("data-topic") || "";
      var keywords = (row.getAttribute("data-keywords") || "") + " " + (row.getAttribute("data-tags") || "");

      if (roleVal && rowRole.indexOf(roleVal) === -1) return false;
      if (tagVal && rowTags.indexOf(tagVal) === -1) return false;
      if (formatVal && rowFormat !== formatVal) return false;
      if (topicVal && rowTopic !== topicVal) return false;

      if (q.length) {
        var hay = keywords.toLowerCase();
        var hit = q.some(function (t) {
          return hay.indexOf(t) !== -1;
        });
        if (!hit) return false;
      }
      return true;
    }

    function applyFilters() {
      var matched = [];
      rows.forEach(function (row) {
        var ok = rowMatches(row);
        var isExtra = row.classList.contains("is-extra");
        if (!ok) {
          row.hidden = true;
          return;
        }
        matched.push(row);
        if (isExtra && !extrasExpanded) {
          row.hidden = true;
        } else {
          row.hidden = false;
        }
      });

      var visible = matched.filter(function (r) {
        return !r.hidden;
      });
      var totalMatched = matched.length;

      if (emptyEl) emptyEl.hidden = totalMatched > 0;
      if (countEl) {
        countEl.textContent =
          totalMatched === 0
            ? "Найдено 0 материалов"
            : "Показано " + visible.length + " из " + totalMatched;
      }
      if (loadMore) {
        var hasHiddenExtras = matched.some(function (r) {
          return r.classList.contains("is-extra") && r.hidden;
        });
        loadMore.hidden = !hasHiddenExtras || totalMatched === 0;
        loadMore.disabled = false;
      }
    }

    function resetFilters() {
      if (search) search.value = "";
      if (role) role.value = "";
      if (tag) tag.value = "";
      if (format) format.value = "";
      if (topic) topic.value = "";
      extrasExpanded = false;
      applyFilters();
    }

    [search, role, tag, format, topic].forEach(function (el) {
      if (!el) return;
      el.addEventListener("input", applyFilters);
      el.addEventListener("change", applyFilters);
    });

    var resetBtn = document.getElementById("kb-reset");
    var emptyReset = document.getElementById("kb-empty-reset");
    if (resetBtn) resetBtn.addEventListener("click", resetFilters);
    if (emptyReset) emptyReset.addEventListener("click", resetFilters);

    if (loadMore) {
      loadMore.addEventListener("click", function () {
        if (skeleton) skeleton.hidden = false;
        loadMore.disabled = true;
        setTimeout(function () {
          extrasExpanded = true;
          if (skeleton) skeleton.hidden = true;
          applyFilters();
        }, 350);
      });
    }

    applyFilters();
  }

  function initAdmin() {
    var root = document.querySelector("[data-admin]");
    if (!root) return;

    var rows = Array.prototype.slice.call(root.querySelectorAll(".admin-row"));
    var sendBtn = document.getElementById("admin-send");
    var sendHint = document.getElementById("admin-send-hint");
    var emailPreviewed = false;
    var itemModal = document.getElementById("item-preview-modal");
    var emailModal = document.getElementById("email-preview-modal");
    var contextInput = document.getElementById("digest-context");
    var schemaInput = document.getElementById("digest-schema");
    var contextPreview = document.getElementById("email-preview-context");
    var schemaPreview = document.getElementById("email-preview-schema");
    var contextKey = "digest-cds-c3-admin-context";
    var schemaKey = "digest-cds-c3-admin-schema";
    var previousFocus = null;
    var pageShell = document.querySelector(".app-shell");

    try {
      var savedContext = localStorage.getItem(contextKey);
      var savedSchema = localStorage.getItem(schemaKey);
      if (savedContext !== null && contextInput) contextInput.value = savedContext;
      if (savedSchema !== null && schemaInput) schemaInput.value = savedSchema;
    } catch (error) {
      /* Storage is optional in the static prototype. */
    }

    function selectedRows() {
      return rows.filter(function (row) {
        var cb = row.querySelector('input[type="checkbox"]');
        return cb && cb.checked;
      });
    }

    function renderEmailPreview() {
      if (!schemaPreview) return;
      if (contextPreview) contextPreview.textContent = contextInput ? contextInput.value.trim() : "";
      schemaPreview.innerHTML = "";
      var selectedReady = selectedRows().filter(function (row) {
        return row.getAttribute("data-status") === "ready";
      });
      var schema = schemaInput && schemaInput.value.trim()
        ? schemaInput.value.trim()
        : "{{articles}}";
      var inserted = false;

      function appendArticles() {
        var label = document.createElement("p");
        label.className = "email-preview-schema__label";
        label.textContent = "Материалы";
        schemaPreview.appendChild(label);
        var list = document.createElement("ol");
        list.className = "email-preview-schema__articles";
        if (!selectedReady.length) {
          var empty = document.createElement("li");
          empty.textContent = "Нет выбранных ready-материалов";
          list.appendChild(empty);
        } else {
          selectedReady.forEach(function (row) {
            var item = document.createElement("li");
            item.textContent = row.getAttribute("data-title") || "Материал";
            list.appendChild(item);
          });
        }
        schemaPreview.appendChild(list);
      }

      schema.split(/\r?\n/).forEach(function (line) {
        var value = line.trim();
        if (!value) return;
        if (value.toLowerCase().replace(/\s+/g, "") === "{{articles}}") {
          inserted = true;
          appendArticles();
          return;
        }
        var block = document.createElement("p");
        block.className = "email-preview-schema__line";
        block.textContent = value;
        schemaPreview.appendChild(block);
      });

      if (!inserted) appendArticles();
    }

    [contextInput, schemaInput].forEach(function (input) {
      if (!input) return;
      input.addEventListener("input", function () {
        try {
          localStorage.setItem(input === contextInput ? contextKey : schemaKey, input.value);
        } catch (error) {
          /* Storage is optional in the static prototype. */
        }
        if (emailModal && !emailModal.hidden) renderEmailPreview();
      });
    });

    function updateSendState() {
      var selected = selectedRows();
      var hasDraft = selected.some(function (row) {
        return row.getAttribute("data-status") === "draft";
      });
      var canSend = emailPreviewed && selected.length > 0 && !hasDraft;
      if (sendBtn) sendBtn.disabled = !canSend;
      if (sendHint) {
        if (!emailPreviewed) {
          sendHint.textContent = "Сначала откройте превью письма. Send недоступен, пока в selection есть draft.";
        } else if (hasDraft) {
          sendHint.textContent = "Уберите черновики из selection или дождитесь статуса ready.";
        } else if (selected.length === 0) {
          sendHint.textContent = "Выберите хотя бы один ready-материал.";
        } else {
          sendHint.textContent = "Готово к отправке (прототип).";
        }
      }
    }

    function openModal(modal) {
      if (!modal) return;
      previousFocus = document.activeElement;
      modal.hidden = false;
      document.body.classList.add("modal-open");
      if (pageShell) pageShell.setAttribute("inert", "");
      var firstFocusable = modal.querySelector(
        "button:not([disabled]), a[href], input:not([disabled]), [tabindex]:not([tabindex='-1'])"
      );
      if (firstFocusable) firstFocusable.focus();
    }

    function closeModal(modal) {
      if (!modal) return;
      modal.hidden = true;
      if (!document.querySelector(".modal:not([hidden])")) {
        document.body.classList.remove("modal-open");
        if (pageShell) pageShell.removeAttribute("inert");
        if (previousFocus && typeof previousFocus.focus === "function") {
          previousFocus.focus();
        }
      }
    }

    document.querySelectorAll("[data-close-modal]").forEach(function (el) {
      el.addEventListener("click", function () {
        var modal = el.closest(".modal");
        closeModal(modal);
      });
    });

    document.addEventListener("keydown", function (event) {
      var open = document.querySelector(".modal:not([hidden])");
      if (!open) return;
      if (event.key === "Escape") {
        closeModal(open);
        return;
      }
      if (event.key !== "Tab") return;
      var focusable = Array.prototype.slice.call(open.querySelectorAll(
        "button:not([disabled]), a[href], input:not([disabled]), [tabindex]:not([tabindex='-1'])"
      ));
      if (!focusable.length) return;
      var first = focusable[0];
      var last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    });

    document.getElementById("admin-select-all") &&
      document.getElementById("admin-select-all").addEventListener("click", function () {
        rows.forEach(function (row) {
          var cb = row.querySelector('input[type="checkbox"]');
          if (cb) cb.checked = true;
          row.classList.remove("admin-row--excluded");
          var excl = row.querySelector(".admin-row__exclusion");
          if (excl) {
            excl.hidden = true;
            excl.textContent = "";
          }
        });
        emailPreviewed = false;
        updateSendState();
      });

    document.getElementById("admin-approve") &&
      document.getElementById("admin-approve").addEventListener("click", function () {
        selectedRows().forEach(function (row) {
          row.classList.remove("admin-row--excluded");
          var excl = row.querySelector(".admin-row__exclusion");
          if (excl) {
            excl.hidden = true;
            excl.textContent = "";
          }
        });
        emailPreviewed = false;
        updateSendState();
      });

    document.getElementById("admin-reject") &&
      document.getElementById("admin-reject").addEventListener("click", function () {
        selectedRows().forEach(function (row) {
          var cb = row.querySelector('input[type="checkbox"]');
          if (cb) cb.checked = false;
          row.classList.add("admin-row--excluded");
          var excl = row.querySelector(".admin-row__exclusion");
          if (excl) {
            excl.hidden = false;
            excl.textContent = "исключён админом";
          }
        });
        emailPreviewed = false;
        updateSendState();
      });

    rows.forEach(function (row) {
      var cb = row.querySelector('input[type="checkbox"]');
      if (cb) {
        cb.addEventListener("change", function () {
          emailPreviewed = false;
          if (cb.checked) {
            row.classList.remove("admin-row--excluded");
            var excl = row.querySelector(".admin-row__exclusion");
            if (excl && excl.textContent === "исключён админом") {
              excl.hidden = true;
              excl.textContent = "";
            }
          }
          updateSendState();
        });
      }

      var previewBtn = row.querySelector("[data-preview]");
      if (previewBtn) {
        previewBtn.addEventListener("click", function () {
          if (!itemModal) return;
          document.getElementById("item-preview-heading").textContent =
            row.getAttribute("data-title") || "";
          document.getElementById("item-preview-dek").textContent =
            row.getAttribute("data-dek") || "";
          document.getElementById("item-preview-status").textContent =
            "Статус: " + (row.getAttribute("data-status") || "—");
          openModal(itemModal);
        });
      }
    });

    document.getElementById("admin-email-preview") &&
      document.getElementById("admin-email-preview").addEventListener("click", function () {
        renderEmailPreview();
        emailPreviewed = true;
        openModal(emailModal);
        updateSendState();
      });

    if (sendBtn) {
      sendBtn.addEventListener("click", function () {
        if (sendBtn.disabled) return;
        sendBtn.disabled = true;
        sendBtn.dataset.state = "success";
        sendBtn.textContent = "Отправлено";
        if (sendHint) {
          sendHint.textContent = "Отправка смоделирована в прототипе. Selection готов к фиксации в архиве.";
        }
      });
    }

    updateSendState();
  }

  initShell();
  initSearch();
  initReadingProgress();
  initMaterial();
  initLogin();
  initVoting();
  initKnowledge();
  initAdmin();
})();
