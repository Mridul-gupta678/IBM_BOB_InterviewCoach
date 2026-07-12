/* ============================================================
   InterviewCoach — App JavaScript
   Handles: Chat, Mock Interview, Resume Analysis,
            Prep Strategy, Progress Tracking, Dark Mode
   ============================================================ */

"use strict";

// ── State ─────────────────────────────────────────────────────────────────────
const STATE = {
  profile:         {},
  chatHistory:     [],
  mockQuestions:   [],
  currentQIndex:   0,
  sessionScores:   [],
  sessionMode:     "behavioral",
  progress: {
    sessions: [],        // { date, mode, scores:[], avgScore }
    totalQuestions: 0,
  },
};

// ── DOM refs ──────────────────────────────────────────────────────────────────
const $ = id => document.getElementById(id);

// ── Markdown renderer (lightweight) ──────────────────────────────────────────
function renderMarkdown(text) {
  if (!text) return "";
  let html = text
    // Escape HTML entities first
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    // Headings
    .replace(/^##### (.+)$/gm,  "<h5>$1</h5>")
    .replace(/^#### (.+)$/gm,   "<h5>$1</h5>")
    .replace(/^### (.+)$/gm,    "<h4>$1</h4>")
    .replace(/^## (.+)$/gm,     "<h3>$1</h3>")
    .replace(/^# (.+)$/gm,      "<h2>$1</h2>")
    // Bold & italic
    .replace(/\*\*\*(.+?)\*\*\*/g, "<strong><em>$1</em></strong>")
    .replace(/\*\*(.+?)\*\*/g,     "<strong>$1</strong>")
    .replace(/\*(.+?)\*/g,         "<em>$1</em>")
    // Inline code
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    // Horizontal rule
    .replace(/^---$/gm, "<hr>")
    // Blockquote
    .replace(/^&gt; (.+)$/gm, "<blockquote>$1</blockquote>")
    // Unordered list items
    .replace(/^[-*•] (.+)$/gm, "<li>$1</li>")
    // Ordered list items
    .replace(/^\d+\. (.+)$/gm, "<li>$1</li>")
    // Line breaks → paragraphs
    .split(/\n\n+/)
    .map(block => {
      block = block.trim();
      if (!block) return "";
      if (block.startsWith("<h") || block.startsWith("<hr") || block.startsWith("<blockquote")) return block;
      if (block.includes("<li>")) return `<ul>${block}</ul>`;
      return `<p>${block.replace(/\n/g, "<br>")}</p>`;
    })
    .join("\n");
  return `<div class="md-content">${html}</div>`;
}

// ── API helpers ───────────────────────────────────────────────────────────────
async function apiPost(endpoint, body) {
  const settings = JSON.parse(localStorage.getItem("itc-settings") || "{}");
  const extendedBody = { ...body, ...settings };
  const res = await fetch(endpoint, {
    method:  "POST",
    headers: { "Content-Type": "application/json" },
    body:    JSON.stringify(extendedBody),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.error || `HTTP ${res.status}`);
  }
  return res.json();
}

async function apiGet(endpoint) {
  const res = await fetch(endpoint);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

// ── Loading overlay ────────────────────────────────────────────────────────────
function showLoading(text = "Thinking…") {
  $("loadingText").textContent = text;
  $("loadingOverlay").classList.remove("d-none");
}
function hideLoading() { $("loadingOverlay").classList.add("d-none"); }

// ═════════════════════════════════════════════════════════════════════════════
//  DARK MODE
// ═════════════════════════════════════════════════════════════════════════════
function initDarkMode() {
  const saved = localStorage.getItem("itc-theme") || "light";
  applyTheme(saved);

  $("darkModeToggle").addEventListener("click", () => {
    const current = document.documentElement.getAttribute("data-theme");
    applyTheme(current === "dark" ? "light" : "dark");
  });
}

function applyTheme(theme) {
  document.documentElement.setAttribute("data-theme", theme);
  localStorage.setItem("itc-theme", theme);
  const icon = $("darkIcon");
  if (theme === "dark") {
    icon.className = "bi bi-sun-fill";
  } else {
    icon.className = "bi bi-moon-stars-fill";
  }
  // Update charts if they exist
  updateChartTheme();
}

// ═════════════════════════════════════════════════════════════════════════════
//  TABS
// ═════════════════════════════════════════════════════════════════════════════
function initTabs() {
  document.querySelectorAll(".tab-btn").forEach(btn => {
    btn.addEventListener("click", () => switchTab(btn.dataset.tab));
  });
}

function switchTab(id) {
  document.querySelectorAll(".tab-section").forEach(s => s.classList.remove("active"));
  document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
  const section = $(id);
  if (section) section.classList.add("active");
  const btn = document.querySelector(`.tab-btn[data-tab="${id}"]`);
  if (btn) btn.classList.add("active");
  // Scroll to tabs
  $("tabsNav").scrollIntoView({ behavior: "smooth", block: "start" });

  if (id === "progressSection") renderProgress();
}

// ═════════════════════════════════════════════════════════════════════════════
//  PROFILE
// ═════════════════════════════════════════════════════════════════════════════
function initProfile() {
  const saved = localStorage.getItem("itc-profile");
  if (saved) {
    STATE.profile = JSON.parse(saved);
    populateProfileModal();
    updateProfileBar();
  }

  $("saveProfileBtn").addEventListener("click", () => {
    STATE.profile = {
      name:       $("profileName").value.trim()      || "Candidate",
      role:       $("profileRole").value.trim()      || "Professional",
      domain:     $("profileDomain").value,
      experience: $("profileExperience").value.trim()|| "Not specified",
      difficulty: $("profileDifficulty").value,
      mode:       $("profileMode").value,
      company:    $("profileCompany").value.trim()   || "Not specified",
      round:      $("profileRound").value,
    };
    localStorage.setItem("itc-profile", JSON.stringify(STATE.profile));
    updateProfileBar();
  });
}

function populateProfileModal() {
  const p = STATE.profile;
  if (p.name)       $("profileName").value       = p.name;
  if (p.role)       $("profileRole").value       = p.role;
  if (p.domain)     $("profileDomain").value     = p.domain;
  if (p.experience) $("profileExperience").value = p.experience;
  if (p.difficulty) $("profileDifficulty").value = p.difficulty;
  if (p.mode)       $("profileMode").value       = p.mode;
  if (p.company)    $("profileCompany").value    = p.company;
  if (p.round)      $("profileRound").value      = p.round;
}

function updateProfileBar() {
  const p = STATE.profile;
  if (!p.name) return;
  $("profileDisplayName").textContent = `${p.name} — Ready to Practice`;
  $("profileDisplaySub").textContent  = `${p.role || "Role not set"} · ${p.company || "Company not set"}`;
  $("profileAvatar").textContent      = p.name.charAt(0).toUpperCase();
  $("tagRole").querySelector("span").textContent       = p.role       || "Role not set";
  $("tagDomain").querySelector("span").textContent     = (p.domain || "general").replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase());
  $("tagDifficulty").querySelector("span").textContent = (p.difficulty || "mid_level").replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase());
  $("tagMode").querySelector("span").textContent       = (p.mode || "behavioral").replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase());
  $("tagCompany").querySelector("span").textContent    = p.company || "Company not set";
}

// ═════════════════════════════════════════════════════════════════════════════
//  HEALTH CHECK
// ═════════════════════════════════════════════════════════════════════════════
async function checkHealth() {
  try {
    const settings = JSON.parse(localStorage.getItem("itc-settings") || "{}");
    const data = await apiPost("/api/health", settings);
    const dot  = $("statusDot");
    if (data.watsonx === "connected") {
      dot.className   = "status-dot connected";
      let providerName = "Watsonx";
      if (data.active_provider === "huggingface") providerName = "Hugging Face";
      
      dot.title       = `${providerName} connected`;
      $("infoStatus").textContent = `${providerName} ✓`;

      const labelText = `Active LLM: ${providerName} (${data.active_model})`;
      if ($("chatActiveModel")) $("chatActiveModel").textContent = labelText;
      if ($("mockActiveModel")) $("mockActiveModel").textContent = labelText;
      if ($("resumeActiveModel")) $("resumeActiveModel").textContent = labelText;
      if ($("prepActiveModel")) $("prepActiveModel").textContent = labelText;
      if ($("infoModel")) $("infoModel").textContent = data.active_model;
    } else {
      dot.className   = "status-dot demo-mode";
      dot.title       = "Demo mode (configure settings)";
      $("infoStatus").textContent = "Demo Mode";

      const labelText = `Active LLM: Static Demo Mode`;
      if ($("chatActiveModel")) $("chatActiveModel").textContent = labelText;
      if ($("mockActiveModel")) $("mockActiveModel").textContent = labelText;
      if ($("resumeActiveModel")) $("resumeActiveModel").textContent = labelText;
      if ($("prepActiveModel")) $("prepActiveModel").textContent = labelText;
      if ($("infoModel")) $("infoModel").textContent = "Static Demo";
    }
  } catch (err) {
    console.error("Health check error:", err);
    $("statusDot").className = "status-dot error-state";
    $("statusDot").title     = "Connection error";

    const labelText = `Active LLM: Connection Error`;
    if ($("chatActiveModel")) $("chatActiveModel").textContent = labelText;
    if ($("mockActiveModel")) $("mockActiveModel").textContent = labelText;
    if ($("resumeActiveModel")) $("resumeActiveModel").textContent = labelText;
    if ($("prepActiveModel")) $("prepActiveModel").textContent = labelText;
    if ($("infoModel")) $("infoModel").textContent = "Error";
  }
}

// ═════════════════════════════════════════════════════════════════════════════
//  CHAT
// ═════════════════════════════════════════════════════════════════════════════
function initChat() {
  $("sendBtn").addEventListener("click", sendChatMessage);
  $("chatInput").addEventListener("keydown", e => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendChatMessage();
    }
  });
  $("chatInput").addEventListener("input", autoResizeTextarea);
  $("clearChat").addEventListener("click", clearChat);

  // Quick prompt buttons
  document.querySelectorAll(".quick-prompt-btn").forEach(btn => {
    btn.addEventListener("click", () => sendQuick(btn.dataset.prompt));
  });
}

function autoResizeTextarea() {
  const ta = $("chatInput");
  ta.style.height = "auto";
  const newHeight = Math.min(ta.scrollHeight, 120);
  ta.style.height = newHeight + "px";
  if (ta.scrollHeight > 120) {
    ta.style.overflowY = "auto";
  } else {
    ta.style.overflowY = "hidden";
  }
}

async function sendChatMessage() {
  const input = $("chatInput");
  const msg   = input.value.trim();
  if (!msg) return;

  input.value = "";
  input.style.height = "42px";
  input.style.overflowY = "hidden";
  appendChatMsg("user", msg);
  STATE.chatHistory.push({ role: "user", content: msg });
  updateMsgCount();

  const typing = appendTyping();
  $("sendBtn").disabled = true;

  try {
    const data = await apiPost("/api/chat", {
      message: msg,
      history: STATE.chatHistory.slice(-10),
      profile: STATE.profile,
    });
    typing.remove();
    const botText = data.response || "I didn't get a response. Please try again.";
    appendChatMsg("bot", botText);
    STATE.chatHistory.push({ role: "assistant", content: botText });
    updateMsgCount();
  } catch (err) {
    typing.remove();
    appendChatMsg("bot", `⚠️ Error: ${err.message}`);
  } finally {
    $("sendBtn").disabled = false;
    $("chatInput").focus();
  }
}

function sendQuick(text) {
  $("chatInput").value = text;
  sendChatMessage();
  switchTab("chatSection");
}
window.sendQuick = sendQuick;  // expose for inline HTML buttons

function appendChatMsg(role, text) {
  const win = $("chatWindow");

  // Remove welcome state on first message
  const welcome = win.querySelector(".chat-welcome");
  if (welcome) welcome.remove();

  const isUser  = role === "user";
  const initial = isUser
    ? (STATE.profile.name ? STATE.profile.name.charAt(0).toUpperCase() : "U")
    : "🤖";
  const time = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

  const wrap = document.createElement("div");
  wrap.className = `chat-msg ${isUser ? "user" : "bot"}`;
  wrap.innerHTML = `
    <div class="msg-avatar">${initial}</div>
    <div class="msg-content-wrap">
      <div class="msg-bubble">${isUser ? escapeHtml(text) : renderMarkdown(text)}</div>
      <div class="msg-meta">${time} ${isUser ? "" : "· InterviewCoach"}</div>
    </div>`;
  win.appendChild(wrap);
  win.scrollTop = win.scrollHeight;
  return wrap;
}

function appendTyping() {
  const win = $("chatWindow");
  const welcome = win.querySelector(".chat-welcome");
  if (welcome) welcome.remove();

  const wrap = document.createElement("div");
  wrap.className = "chat-msg bot";
  wrap.innerHTML = `
    <div class="msg-avatar">🤖</div>
    <div class="msg-content-wrap">
      <div class="msg-bubble typing-bubble">
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
      </div>
    </div>`;
  win.appendChild(wrap);
  win.scrollTop = win.scrollHeight;
  return wrap;
}

function updateMsgCount() {
  $("msgCount").textContent = STATE.chatHistory.filter(m => m.role === "user").length;
}

function clearChat() {
  STATE.chatHistory = [];
  updateMsgCount();
  const win = $("chatWindow");
  win.innerHTML = `
    <div class="chat-welcome">
      <div class="welcome-icon">🎯</div>
      <h5>Welcome to InterviewCoach!</h5>
      <p>I'm your AI-powered interview trainer. Ask me to start a mock interview, review your answers, or give you tips for your target role.</p>
      <div class="quick-prompts">
        <button class="quick-prompt-btn" data-prompt="Start a mock behavioral interview for a Software Engineer role">🎭 Mock Behavioral Interview</button>
        <button class="quick-prompt-btn" data-prompt="What are the top 10 interview tips I should know?">💡 Top Interview Tips</button>
        <button class="quick-prompt-btn" data-prompt="How do I use the STAR method effectively?">⭐ STAR Method Guide</button>
        <button class="quick-prompt-btn" data-prompt="What questions should I ask the interviewer?">❓ Questions to Ask</button>
      </div>
    </div>`;
  document.querySelectorAll(".quick-prompt-btn").forEach(btn => {
    btn.addEventListener("click", () => sendQuick(btn.dataset.prompt));
  });
}

// ═════════════════════════════════════════════════════════════════════════════
//  MOCK INTERVIEW
// ═════════════════════════════════════════════════════════════════════════════
function initMockInterview() {
  $("startMockBtn").addEventListener("click",   startMockSession);
  $("submitAnswerBtn").addEventListener("click", submitAnswer);
  $("skipQuestionBtn").addEventListener("click", skipQuestion);
  $("nextQuestionBtn").addEventListener("click", nextQuestion);
  $("retryAnswerBtn").addEventListener("click",  retryAnswer);
  $("newSessionBtn").addEventListener("click",   resetMockSession);
}

async function startMockSession() {
  const mode  = $("mockMode").value;
  const count = parseInt($("mockCount").value);
  STATE.sessionMode   = mode;
  STATE.sessionScores = [];
  STATE.currentQIndex = 0;

  showLoading("Generating interview questions…");
  try {
    const data = await apiPost("/api/generate-questions", {
      profile: STATE.profile,
      mode,
      count,
    });
    hideLoading();

    // Parse questions from text (split on numbered lines)
    const rawText = data.questions || "";
    STATE.mockQuestions = parseQuestions(rawText, count);

    $("mockSetup").classList.add("d-none");
    $("sessionComplete").classList.add("d-none");
    $("evalResult").classList.add("d-none");
    $("mockSession").classList.remove("d-none");

    renderQuestionsList();
    loadQuestion(0);
  } catch (err) {
    hideLoading();
    showToast(`Error: ${err.message}`, "danger");
  }
}

function parseQuestions(text, expectedCount) {
  // Try to split on numbered patterns: "1.", "1)", etc.
  const lines  = text.split("\n").filter(l => l.trim());
  const qLines = [];
  let   current = "";

  for (const line of lines) {
    const trimmed = line.trim();
    if (/^\d+[\.\)]\s/.test(trimmed)) {
      if (current) qLines.push(current.trim());
      current = trimmed.replace(/^\d+[\.\)]\s/, "");
    } else if (current) {
      // Continuation line (e.g. the follow-up hint)
      current += " " + trimmed;
    }
  }
  if (current) qLines.push(current.trim());

  // Fallback: if we couldn't parse properly, split by double newline
  if (qLines.length < 2) {
    return text.split(/\n\n+/).filter(s => s.trim().length > 10).slice(0, expectedCount);
  }
  return qLines.slice(0, expectedCount);
}

function loadQuestion(index) {
  const questions = STATE.mockQuestions;
  if (index >= questions.length) {
    showSessionComplete();
    return;
  }

  STATE.currentQIndex = index;
  const total = questions.length;
  const pct   = Math.round(((index + 1) / total) * 100);

  $("questionCounter").textContent      = `Question ${index + 1} of ${total}`;
  $("sessionMode").textContent          = STATE.sessionMode.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase());
  $("interviewProgress").style.width    = `${pct}%`;
  $("questionText").textContent         = questions[index];
  $("answerInput").value                = "";
  $("evalResult").classList.add("d-none");
  $("mockSession").querySelector(".answer-area").classList.remove("d-none");

  const qNumEl = $("currentQuestion").querySelector(".q-number");
  if (qNumEl) qNumEl.textContent = `Q${index + 1}`;

  // Highlight current in list
  document.querySelectorAll(".q-list-item").forEach((item, i) => {
    item.classList.toggle("active", i === index);
  });

  $("answerInput").focus();
}

function renderQuestionsList() {
  const list = $("questionsList");
  list.innerHTML = "";
  STATE.mockQuestions.forEach((q, i) => {
    const item = document.createElement("div");
    item.className = "q-list-item";
    item.dataset.index = i;
    item.innerHTML = `<span class="q-dot"></span><span>${q.length > 60 ? q.slice(0, 60) + "…" : q}</span>`;
    item.addEventListener("click", () => {
      if (i <= STATE.currentQIndex + 1) loadQuestion(i);
    });
    list.appendChild(item);
  });
}

async function submitAnswer() {
  const answer = $("answerInput").value.trim();
  if (!answer) {
    showToast("Please write your answer before submitting.", "warning");
    return;
  }

  const question = STATE.mockQuestions[STATE.currentQIndex];
  showLoading("Evaluating your answer…");

  try {
    const data = await apiPost("/api/evaluate-answer", {
      question,
      answer,
      profile: STATE.profile,
    });
    hideLoading();
    showEvaluation(data.evaluation || "No evaluation returned.");
  } catch (err) {
    hideLoading();
    showToast(`Evaluation error: ${err.message}`, "danger");
  }
}

function showEvaluation(evalText) {
  // Try to extract score
  const scoreMatch = evalText.match(/(\d{1,3})\s*\/\s*100/);
  const score      = scoreMatch ? parseInt(scoreMatch[1]) : null;

  if (score !== null) {
    STATE.sessionScores.push(score);
    $("scoreDisplay").textContent = `${score}/100`;
    $("scoreDisplay").style.background = score >= 80
      ? "linear-gradient(135deg, #16a34a, #059669)"
      : score >= 60
      ? "linear-gradient(135deg, #d97706, #b45309)"
      : "linear-gradient(135deg, #dc2626, #b91c1c)";
    // Mark question as answered
    const qItem = $("questionsList").children[STATE.currentQIndex];
    if (qItem) qItem.classList.add("answered");
  }

  $("evalContent").innerHTML = renderMarkdown(evalText);
  $("evalResult").classList.remove("d-none");
  $("mockSession").querySelector(".answer-area").classList.add("d-none");
  $("evalResult").scrollIntoView({ behavior: "smooth", block: "nearest" });

  // Save to progress
  STATE.progress.totalQuestions++;
  saveProgress();
}

function nextQuestion() {
  $("evalResult").classList.add("d-none");
  $("mockSession").querySelector(".answer-area").classList.remove("d-none");
  loadQuestion(STATE.currentQIndex + 1);
}

function skipQuestion() {
  STATE.sessionScores.push(null);  // null = skipped
  loadQuestion(STATE.currentQIndex + 1);
}

function retryAnswer() {
  $("evalResult").classList.add("d-none");
  $("mockSession").querySelector(".answer-area").classList.remove("d-none");
  $("answerInput").value = "";
  $("answerInput").focus();
}

function showSessionComplete() {
  $("mockSession").classList.add("d-none");
  $("evalResult").classList.add("d-none");
  $("sessionComplete").classList.remove("d-none");

  const validScores = STATE.sessionScores.filter(s => s !== null);
  const avg  = validScores.length ? Math.round(validScores.reduce((a, b) => a + b, 0) / validScores.length) : "--";
  const best = validScores.length ? Math.max(...validScores) : "--";

  $("finalAvgScore").textContent  = avg !== "--" ? `${avg}/100` : "--";
  $("finalQCount").textContent    = STATE.mockQuestions.length;
  $("finalBestScore").textContent = best !== "--" ? `${best}/100` : "--";

  // Save session to progress
  if (validScores.length > 0) {
    STATE.progress.sessions.push({
      date:     new Date().toLocaleDateString(),
      mode:     STATE.sessionMode,
      scores:   validScores,
      avgScore: avg,
    });
    saveProgress();
  }
}

function resetMockSession() {
  STATE.mockQuestions   = [];
  STATE.sessionScores   = [];
  STATE.currentQIndex   = 0;

  $("mockSetup").classList.remove("d-none");
  $("mockSession").classList.add("d-none");
  $("evalResult").classList.add("d-none");
  $("sessionComplete").classList.add("d-none");
  $("questionsList").innerHTML = "<p class='text-muted small'>Start a session to see questions here</p>";
}

// ═════════════════════════════════════════════════════════════════════════════
//  RESUME ANALYZER
// ═════════════════════════════════════════════════════════════════════════════
function initResume() {
  $("analyzeResumeBtn").addEventListener("click", analyzeResume);
}

async function analyzeResume() {
  const text = $("resumeText").value.trim();
  if (!text) {
    showToast("Please paste your resume text first.", "warning");
    return;
  }

  showLoading("Analyzing your resume with AI…");
  try {
    const data = await apiPost("/api/analyze-resume", {
      resume_text: text,
      profile:     STATE.profile,
    });
    hideLoading();
    const result = data.analysis || "No analysis returned.";
    $("resumeResult").innerHTML = `<div class="md-content">${renderMarkdown(result)}</div>`;
    if (data.mode === "demo") {
      $("resumeResult").insertAdjacentHTML("afterbegin",
        `<div class="alert alert-warning mb-3" style="border-radius:8px;font-size:.82rem;padding:.6rem 1rem;">
          ⚠️ Demo mode — Configure IBM API key for full AI analysis
        </div>`);
    }
    $("resumeResultCard").scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (err) {
    hideLoading();
    showToast(`Resume analysis error: ${err.message}`, "danger");
  }
}

// ═════════════════════════════════════════════════════════════════════════════
//  PREP STRATEGY
// ═════════════════════════════════════════════════════════════════════════════
function initPrepStrategy() {
  const range   = $("daysRange");
  const display = $("daysDisplay");
  range.addEventListener("input", () => {
    display.textContent = `${range.value} day${range.value > 1 ? "s" : ""}`;
  });
  $("generateStrategyBtn").addEventListener("click", generateStrategy);
}

async function generateStrategy() {
  const days = parseInt($("daysRange").value);
  showLoading("Building your preparation roadmap…");
  try {
    const data = await apiPost("/api/prep-strategy", {
      profile:               STATE.profile,
      days_until_interview:  days,
    });
    hideLoading();
    const strategy = data.strategy || "No strategy returned.";
    $("strategyResult").innerHTML = `<div class="md-content">${renderMarkdown(strategy)}</div>`;
    if (data.mode === "demo") {
      $("strategyResult").insertAdjacentHTML("afterbegin",
        `<div class="alert alert-warning mb-3" style="border-radius:8px;font-size:.82rem;padding:.6rem 1rem;">
          ⚠️ Demo mode — Configure IBM API key for a personalised AI prep plan
        </div>`);
    }
  } catch (err) {
    hideLoading();
    showToast(`Strategy generation error: ${err.message}`, "danger");
  }
}

// ═════════════════════════════════════════════════════════════════════════════
//  PROGRESS TRACKING
// ═════════════════════════════════════════════════════════════════════════════
let scoreChartInstance = null;
let modeChartInstance  = null;

function initProgress() {
  const savedProgress = localStorage.getItem("itc-progress");
  if (savedProgress) {
    STATE.progress = JSON.parse(savedProgress);
  }
  $("clearProgressBtn").addEventListener("click", clearProgress);
}

function saveProgress() {
  localStorage.setItem("itc-progress", JSON.stringify(STATE.progress));
}

function clearProgress() {
  if (!confirm("Clear all progress data? This cannot be undone.")) return;
  STATE.progress = { sessions: [], totalQuestions: 0 };
  saveProgress();
  renderProgress();
}

function renderProgress() {
  const sessions = STATE.progress.sessions || [];
  const allScores = sessions.flatMap(s => s.scores);

  // Metrics
  $("metTotalSessions").textContent  = sessions.length;
  $("metTotalQuestions").textContent = STATE.progress.totalQuestions || 0;
  $("metAvgScore").textContent       = allScores.length
    ? `${Math.round(allScores.reduce((a,b)=>a+b,0)/allScores.length)}`
    : "--";
  $("metBestScore").textContent = allScores.length ? Math.max(...allScores) : "--";

  renderScoreChart(sessions);
  renderModeChart(sessions);
  renderSessionHistory(sessions);
}

function getChartColors() {
  const dark = document.documentElement.getAttribute("data-theme") === "dark";
  return {
    gridColor:  dark ? "rgba(255,255,255,.08)" : "rgba(0,0,0,.06)",
    textColor:  dark ? "#8892a4" : "#6b7280",
    bgColor:    dark ? "#1a1d27" : "#ffffff",
  };
}

function renderScoreChart(sessions) {
  const ctx    = $("scoreChart");
  if (!ctx) return;
  const colors = getChartColors();

  const labels = sessions.map((s, i) => `Session ${i+1} (${s.mode.replace(/_/g," ")})`);
  const data   = sessions.map(s => s.avgScore);

  if (scoreChartInstance) scoreChartInstance.destroy();

  if (!data.length) {
    ctx.parentElement.innerHTML = `<div class="empty-state"><div class="empty-icon">📈</div><p>Complete sessions to see your score history</p></div>`;
    return;
  }

  scoreChartInstance = new Chart(ctx, {
    type: "line",
    data: {
      labels,
      datasets: [{
        label:           "Average Score",
        data,
        borderColor:     "#4f6ef7",
        backgroundColor: "rgba(79,110,247,.12)",
        tension:         0.4,
        fill:            true,
        pointBackgroundColor: "#4f6ef7",
        pointRadius:     5,
      }],
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      scales: {
        y: {
          min: 0, max: 100,
          grid: { color: colors.gridColor },
          ticks: { color: colors.textColor },
        },
        x: {
          grid: { display: false },
          ticks: { color: colors.textColor, maxRotation: 30 },
        },
      },
      plugins: {
        legend: { labels: { color: colors.textColor } },
        tooltip: { callbacks: { label: ctx => `${ctx.parsed.y}/100` } },
      },
    },
  });
}

function renderModeChart(sessions) {
  const ctx    = $("modeChart");
  if (!ctx) return;
  const colors = getChartColors();

  // Group by mode
  const modeMap = {};
  for (const s of sessions) {
    const m = s.mode.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase());
    if (!modeMap[m]) modeMap[m] = [];
    modeMap[m].push(s.avgScore);
  }

  const labels = Object.keys(modeMap);
  const data   = labels.map(l => Math.round(modeMap[l].reduce((a,b)=>a+b,0)/modeMap[l].length));
  const bgColors = ["#4f6ef7","#7c3aed","#059669","#d97706","#dc2626","#0891b2"].slice(0, labels.length);

  if (modeChartInstance) modeChartInstance.destroy();

  if (!data.length) {
    ctx.parentElement.innerHTML = `<div class="empty-state"><div class="empty-icon">📊</div><p>Complete different interview modes to see comparison</p></div>`;
    return;
  }

  modeChartInstance = new Chart(ctx, {
    type: "doughnut",
    data: {
      labels,
      datasets: [{
        data,
        backgroundColor: bgColors,
        borderColor:     colors.bgColor,
        borderWidth:     3,
      }],
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: {
        legend: { position: "bottom", labels: { color: colors.textColor, font: { size: 11 } } },
        tooltip: { callbacks: { label: ctx => `Avg: ${ctx.parsed}/100` } },
      },
    },
  });
}

function renderSessionHistory(sessions) {
  const container = $("sessionHistory");
  if (!sessions.length) {
    container.innerHTML = `<div class="empty-state"><div class="empty-icon">📊</div><p>Complete mock interview sessions to see your history here</p></div>`;
    return;
  }

  const html = [...sessions].reverse().map((s, i) => {
    const scoreColor = s.avgScore >= 80 ? "#16a34a" : s.avgScore >= 60 ? "#d97706" : "#dc2626";
    return `
      <div class="history-item">
        <div>
          <div class="history-mode">${s.mode.replace(/_/g," ").replace(/\b\w/g,c=>c.toUpperCase())} Interview</div>
          <div class="history-meta">${s.date} &bull; ${s.scores.length} question${s.scores.length>1?"s":""}</div>
        </div>
        <div class="history-score" style="color:${scoreColor}">${s.avgScore}/100</div>
      </div>`;
  }).join("");
  container.innerHTML = html;
}

function updateChartTheme() {
  if (scoreChartInstance || modeChartInstance) {
    renderProgress();
  }
}

// ═════════════════════════════════════════════════════════════════════════════
//  TOAST NOTIFICATIONS
// ═════════════════════════════════════════════════════════════════════════════
function showToast(message, type = "info") {
  const colors = { info:"#4f6ef7", success:"#16a34a", warning:"#d97706", danger:"#dc2626" };
  const toast = document.createElement("div");
  toast.style.cssText = `
    position:fixed; bottom:20px; right:20px; z-index:99999;
    background:${colors[type]||colors.info}; color:#fff;
    padding:.75rem 1.25rem; border-radius:10px;
    font-size:.85rem; font-weight:600;
    box-shadow:0 4px 20px rgba(0,0,0,.25);
    animation: toastIn .25s ease;
    max-width:320px; line-height:1.4;
  `;
  toast.textContent = message;
  document.body.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateX(20px)";
    toast.style.transition = ".25s ease";
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

// ═════════════════════════════════════════════════════════════════════════════
//  UTILITIES
// ═════════════════════════════════════════════════════════════════════════════
function escapeHtml(text) {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

// ═════════════════════════════════════════════════════════════════════════════
//  YEAR FOOTER
// ═════════════════════════════════════════════════════════════════════════════
function setYear() {
  const el = $("currentYear");
  if (el) el.textContent = new Date().getFullYear();
}

// ═════════════════════════════════════════════════════════════════════════════
//  SETTINGS & PROVIDERS
// ═════════════════════════════════════════════════════════════════════════════
function initSettings() {
  const saved = localStorage.getItem("itc-settings");
  let settings = {};
  if (saved) {
    settings = JSON.parse(saved);
  } else {
    settings = {
      llm_provider: "auto",
      huggingface_api_key: "",
      huggingface_model_id: "meta-llama/Llama-3.3-70B-Instruct"
    };
  }
  populateSettingsModal(settings);

  $("saveSettingsBtn").addEventListener("click", () => {
    const newSettings = {
      llm_provider: $("settingsProvider").value,
      huggingface_api_key: $("settingsHfKey").value.trim(),
      huggingface_model_id: $("settingsHfModel").value.trim() || "meta-llama/Llama-3.3-70B-Instruct"
    };
    localStorage.setItem("itc-settings", JSON.stringify(newSettings));
    checkHealth();
  });
}

function populateSettingsModal(s) {
  $("settingsProvider").value = s.llm_provider || "auto";
  $("settingsHfKey").value = s.huggingface_api_key || "";
  $("settingsHfModel").value = s.huggingface_model_id || "meta-llama/Llama-3.3-70B-Instruct";
}

// ═════════════════════════════════════════════════════════════════════════════
//  INIT
// ═════════════════════════════════════════════════════════════════════════════
document.addEventListener("DOMContentLoaded", () => {
  initDarkMode();
  initTabs();
  initProfile();
  initSettings();
  initChat();
  initMockInterview();
  initResume();
  initPrepStrategy();
  initProgress();
  checkHealth();
  setYear();

  // Auto-open profile modal if no profile set
  const saved = localStorage.getItem("itc-profile");
  if (!saved) {
    setTimeout(() => {
      const modal = new bootstrap.Modal($("profileModal"));
      modal.show();
    }, 800);
  }
});
