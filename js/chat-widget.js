(function () {
  // ── Config ──────────────────────────────────────────────────
  var isLocal = ["localhost", "127.0.0.1", "::1"].indexOf(window.location.hostname) !== -1;
  var API_ENDPOINT = (isLocal
    ? "http://127.0.0.1:8000"
    : "phishguard-do8t.onrender.com") + "/api/chat";
  var SESSION_KEY = "phishguard_chat_session_id";
  var THEME_KEY = "phishguard-theme";

  // ── Session ID ───────────────────────────────────────────────
  function getSessionId() {
    try {
      var existing = localStorage.getItem(SESSION_KEY);
      if (existing) return existing;
      var generated = "sess_" + Math.random().toString(36).slice(2, 12) + "_" + Date.now().toString(36);
      localStorage.setItem(SESSION_KEY, generated);
      return generated;
    } catch (_) {
      return "sess_" + Date.now().toString(36);
    }
  }
  var sessionId = getSessionId();

  // ── Inject CSS ───────────────────────────────────────────────
  var style = document.createElement("style");
  style.textContent = `
    .pg-fab {
      position: fixed;
      bottom: 28px;
      right: 28px;
      z-index: 9999;
      width: 56px;
      height: 56px;
      border-radius: 50%;
      background: linear-gradient(135deg, #0ea5e9, #22d3ee);
      border: none;
      box-shadow: 0 4px 18px rgba(14,165,233,0.45);
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: transform 0.2s ease, box-shadow 0.2s ease;
      flex-shrink: 0;
    }
    .pg-fab:hover {
      transform: translateY(-3px) scale(1.06);
      box-shadow: 0 8px 24px rgba(14,165,233,0.55);
    }
    .pg-fab svg {
      width: 26px;
      height: 26px;
      fill: #fff;
      pointer-events: none;
    }
    .pg-fab-badge {
      position: absolute;
      top: -3px;
      right: -3px;
      width: 13px;
      height: 13px;
      background: #ef4444;
      border-radius: 50%;
      border: 2px solid #020617;
      animation: pgBadgePulse 2s infinite;
    }
    @keyframes pgBadgePulse {
      0%, 100% { transform: scale(1); }
      50%       { transform: scale(1.25); }
    }

    /* Widget box */
    .pg-widget {
      position: fixed;
      bottom: 96px;
      right: 28px;
      z-index: 9998;
      width: 360px;
      max-height: 520px;
      border-radius: 16px;
      border: 1px solid rgba(56,189,248,0.3);
      background: linear-gradient(180deg, rgba(11,18,34,0.98), rgba(3,8,24,0.98));
      box-shadow: 0 20px 45px rgba(2,6,23,0.65);
      display: flex;
      flex-direction: column;
      overflow: hidden;
      font-family: "Poppins", sans-serif;
      font-size: 14px;
      color: #e2e8f0;

      /* hidden by default */
      opacity: 0;
      pointer-events: none;
      transform: translateY(14px) scale(0.97);
      transition: opacity 0.22s ease, transform 0.22s ease;
    }
    .pg-widget.pg-open {
      opacity: 1;
      pointer-events: all;
      transform: translateY(0) scale(1);
    }
    body.light-mode .pg-widget {
      background: linear-gradient(180deg, #ffffff, #f8fbff);
      border-color: rgba(14,116,144,0.28);
      color: #0f172a;
      box-shadow: 0 20px 45px rgba(15,23,42,0.14);
    }

    /* Header */
    .pg-widget-head {
      padding: 12px 14px;
      border-bottom: 1px solid rgba(56,189,248,0.3);
      display: flex;
      align-items: center;
      justify-content: space-between;
      flex-shrink: 0;
    }
    body.light-mode .pg-widget-head {
      border-color: rgba(14,116,144,0.28);
    }
    .pg-widget-brand {
      display: flex;
      flex-direction: column;
      line-height: 1;
    }
    .pg-widget-logo {
      font-family: "Montserrat", "Poppins", sans-serif;
      font-size: 18px;
      font-weight: 800;
      letter-spacing: 0.05em;
      text-transform: uppercase;
      background: linear-gradient(90deg,#a5f3fc 0%,#67e8f9 30%,#22d3ee 62%,#0ea5e9 82%,#0369a1 100%);
      -webkit-background-clip: text;
      background-clip: text;
      -webkit-text-fill-color: transparent;
    }
    .pg-widget-sub {
      font-size: 10px;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      color: #93c5fd;
      margin-top: 2px;
    }
    body.light-mode .pg-widget-sub { color: #0c4a6e; }
    .pg-widget-close {
      background: transparent;
      border: none;
      color: #93c5fd;
      font-size: 20px;
      line-height: 1;
      cursor: pointer;
      padding: 2px 6px;
      border-radius: 6px;
      transition: color 0.15s, background 0.15s;
    }
    .pg-widget-close:hover { color: #e0f2fe; background: rgba(56,189,248,0.1); }
    body.light-mode .pg-widget-close { color: #0c4a6e; }
    body.light-mode .pg-widget-close:hover { color: #0f172a; background: rgba(14,116,144,0.1); }

    /* Log */
    .pg-widget-log {
      flex: 1;
      overflow-y: auto;
      padding: 12px;
      display: flex;
      flex-direction: column;
      gap: 8px;
      scroll-behavior: smooth;
    }
    body.light-mode .pg-widget-log { background: rgba(248,250,252,0.8); }

    .pg-msg {
      max-width: 88%;
      padding: 9px 11px;
      border-radius: 12px;
      line-height: 1.45;
      white-space: pre-wrap;
      word-break: break-word;
      font-size: 13px;
    }
    .pg-msg.bot {
      background: #1e293b;
      align-self: flex-start;
    }
    body.light-mode .pg-msg.bot {
      background: #e2e8f0;
      color: #0f172a;
      border: 1px solid rgba(148,163,184,0.45);
    }
    .pg-msg.user {
      background: #0369a1;
      color: #e0f2fe;
      align-self: flex-end;
    }
    body.light-mode .pg-msg.user { background: #0284c7; color: #f8fafc; }

    /* Form */
    .pg-widget-form {
      border-top: 1px solid rgba(56,189,248,0.3);
      padding: 10px;
      flex-shrink: 0;
    }
    body.light-mode .pg-widget-form { border-color: rgba(14,116,144,0.28); }
    .pg-widget-row {
      display: flex;
      gap: 8px;
    }
    .pg-widget-input {
      flex: 1;
      min-height: 42px;
      max-height: 100px;
      resize: none;
      border: 1px solid rgba(148,163,184,0.45);
      border-radius: 10px;
      padding: 10px;
      font: inherit;
      font-size: 13px;
      background: #f8fafc;
      color: #0f172a;
    }
    .pg-widget-input:focus {
      outline: none;
      border-color: rgba(14,165,233,0.8);
      box-shadow: 0 0 0 3px rgba(14,165,233,0.2);
    }
    .pg-widget-send {
      border: none;
      background: #0ea5e9;
      color: #fff;
      font-weight: 700;
      font-size: 12px;
      letter-spacing: 0.1em;
      border-radius: 10px;
      padding: 0 14px;
      cursor: pointer;
      transition: background 0.2s, transform 0.2s;
      white-space: nowrap;
    }
    .pg-widget-send:hover { background: #0284c7; transform: translateY(-1px); }
    .pg-widget-send:disabled { opacity: 0.6; cursor: not-allowed; transform: none; }
    body.light-mode .pg-widget-send { background: #0284c7; }
    body.light-mode .pg-widget-send:hover { background: #0369a1; }

    .pg-widget-status {
      font-size: 12px;
      min-height: 18px;
      color: #93c5fd;
      margin: 6px 2px 0;
    }
    body.light-mode .pg-widget-status { color: #0c4a6e; }
    .pg-widget-status.is-error { color: #fca5a5; }
    body.light-mode .pg-widget-status.is-error { color: #b91c1c; }

    .pg-widget-note {
      font-size: 11px;
      color: #93c5fd;
      padding: 0 10px 8px;
      margin: 0;
      flex-shrink: 0;
    }
    body.light-mode .pg-widget-note { color: #0c4a6e; }
    .pg-widget-note a { color: #ef4444; font-weight: 600; text-decoration: none; }
    .pg-widget-note a:hover { color: #b91c1c; }

    @media (max-width: 420px) {
      .pg-widget { width: calc(100vw - 24px); right: 12px; bottom: 88px; }
      .pg-fab { right: 16px; bottom: 16px; }
    }
  `;
  document.head.appendChild(style);

  // ── Build HTML ───────────────────────────────────────────────
  var wrapper = document.createElement("div");
  wrapper.innerHTML = `
    <!-- Floating button -->
    <button class="pg-fab" id="pg-fab" aria-label="Open AI Support Chat">
      <svg viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.03 2 11c0 2.7 1.24 5.12 3.2 6.8L4 22l4.51-1.5C9.61 20.83 10.78 21 12 21c5.52 0 10-4.03 10-9S17.52 2 12 2zm1 13H7v-2h6v2zm2-4H7V9h8v2z"/></svg>
      <span class="pg-fab-badge"></span>
    </button>

    <!-- Chat widget -->
    <div class="pg-widget" id="pg-widget" role="dialog" aria-label="PhishGuard AI Support Chat">
      <div class="pg-widget-head">
        <div class="pg-widget-brand">
          <span class="pg-widget-logo">PhishGuard</span>
          <span class="pg-widget-sub">AI Support Chat</span>
        </div>
        <button class="pg-widget-close" id="pg-widget-close" aria-label="Close chat">&times;</button>
      </div>

      <div class="pg-widget-log" id="pg-widget-log">
        <div class="pg-msg bot">Hello! I am your PhishGuard AI assistant. Ask me about suspicious links, phishing emails, and safe next steps.</div>
      </div>

      <form class="pg-widget-form" id="pg-widget-form">
        <div class="pg-widget-row">
          <textarea class="pg-widget-input" id="pg-widget-input" placeholder="Type your question..." maxlength="800" rows="1"></textarea>
          <button type="submit" class="pg-widget-send" id="pg-widget-send">SEND</button>
        </div>
        <p class="pg-widget-status" id="pg-widget-status"></p>
      </form>
      <p class="pg-widget-note">Need human support? <a href="mailto:phishguardsupport@gmail.com">phishguardsupport@gmail.com</a></p>
    </div>
  `;
  document.body.appendChild(wrapper);

  // ── Elements ─────────────────────────────────────────────────
  var fab = document.getElementById("pg-fab");
  var widget = document.getElementById("pg-widget");
  var closeBtn = document.getElementById("pg-widget-close");
  var form = document.getElementById("pg-widget-form");
  var input = document.getElementById("pg-widget-input");
  var sendBtn = document.getElementById("pg-widget-send");
  var statusEl = document.getElementById("pg-widget-status");
  var log = document.getElementById("pg-widget-log");

  // ── Open / Close ─────────────────────────────────────────────
  function openWidget() {
    widget.classList.add("pg-open");
    input.focus();
  }
  function closeWidget() {
    widget.classList.remove("pg-open");
    fab.focus();
  }

  fab.addEventListener("click", function () {
    widget.classList.contains("pg-open") ? closeWidget() : openWidget();
  });
  closeBtn.addEventListener("click", closeWidget);

  // Close on Escape key
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && widget.classList.contains("pg-open")) closeWidget();
  });

  // ── Helpers ──────────────────────────────────────────────────
  function appendMsg(role, text) {
    var el = document.createElement("div");
    el.className = "pg-msg " + (role === "user" ? "user" : "bot");
    el.textContent = text;
    log.appendChild(el);
    log.scrollTop = log.scrollHeight;
  }

  function setStatus(msg, isError) {
    statusEl.textContent = msg || "";
    statusEl.classList.toggle("is-error", !!isError);
  }

  // ── Send message ─────────────────────────────────────────────
  form.addEventListener("submit", function (e) {
    e.preventDefault();
    var message = (input.value || "").trim();
    if (!message) { setStatus("Please type a question first.", true); return; }

    appendMsg("user", message);
    input.value = "";
    sendBtn.disabled = true;
    setStatus("Assistant is thinking...", false);

    fetch(API_ENDPOINT, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ sessionId: sessionId, message: message })
    })
      .then(function (res) {
        return res.json().catch(function () { return {}; }).then(function (data) {
          if (!res.ok) throw new Error((data && data.error) || "Request failed.");
          return data;
        });
      })
      .then(function (data) {
        appendMsg("bot", (data && data.reply) || "No response received.");
        setStatus("", false);
      })
      .catch(function (err) {
        appendMsg("bot", "I could not answer right now. Please contact phishguardsupport@gmail.com.");
        setStatus((err && err.message) || "Could not reach chat service.", true);
      })
      .finally(function () {
        sendBtn.disabled = false;
        input.focus();
      });
  });

  // Auto-grow textarea
  input.addEventListener("input", function () {
    this.style.height = "auto";
    this.style.height = Math.min(this.scrollHeight, 100) + "px";
  });

  // Send on Enter (Shift+Enter for new line)
  input.addEventListener("keydown", function (e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      form.dispatchEvent(new Event("submit"));
    }
  });
})();
