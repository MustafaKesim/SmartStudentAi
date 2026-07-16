// Escapes text that came from user-controlled data (like an uploaded
// file's name, or a typed question) before inserting it into HTML, so it
// can't be used to inject a script (XSS). Never skip this for such text.
function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

// Reads the friendly error message our backend sends (e.g. "You've hit
// Gemini's rate limit...") out of a failed response, with a generic
// fallback if something else entirely went wrong.
async function getErrorMessage(res) {
  try {
    const data = await res.json();
    return data.detail || "Something went wrong. Please try again.";
  } catch {
    return "Something went wrong. Please try again.";
  }
}

function switchPanel(panelId) {
  document.querySelectorAll(".panel").forEach((p) => p.classList.remove("active"));
  document.getElementById(panelId).classList.add("active");
}

document.querySelectorAll(".tab").forEach((tab) => {
  tab.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach((t) => t.classList.remove("active"));
    document.querySelectorAll(".history-item").forEach((h) => h.classList.remove("active"));
    tab.classList.add("active");
    switchPanel("panel-" + tab.dataset.tab);
  });
});

/* ---------------- Upload ---------------- */

const pdfFileInput = document.getElementById("pdfFile");

document.getElementById("dropzone").addEventListener("click", () => pdfFileInput.click());

pdfFileInput.addEventListener("change", () => {
  const file = pdfFileInput.files[0];
  document.getElementById("dropzoneTitle").innerText = file ? file.name : "Click to choose a PDF";
  document.getElementById("dropzoneHint").innerText = file ? "Click Upload to add it to this chat" : "or drag one here";
});

document.getElementById("uploadButton").addEventListener("click", async () => {
  const file = pdfFileInput.files[0];
  const statusEl = document.getElementById("uploadStatusText");

  if (!file) {
    statusEl.innerText = "Please choose a file first.";
    return;
  }

  statusEl.innerText = "Uploading...";

  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch("/upload", { method: "POST", body: formData });

  if (!res.ok) {
    statusEl.innerText = await getErrorMessage(res);
    return;
  }

  const data = await res.json();

  statusEl.innerText = "";
  document.getElementById("fileCard").style.display = "flex";
  document.getElementById("fileCardName").innerText = file.name;
  document.getElementById("fileCardMeta").innerText =
    data.characters_extracted + " characters extracted";

  // A new (or additional) document changes the page layout for the
  // Summarize flow, so restart it.
  resetSummarizeState();
});

/* ---------------- Summarize (paginated) ---------------- */

let summarizeState = { partIndex: -1, totalParts: null, cache: {} };

function resetSummarizeState() {
  summarizeState = { partIndex: -1, totalParts: null, cache: {} };
  document.getElementById("summarizePartLabel").innerText = "Not started yet";
  document.getElementById("summarizeContent").innerHTML =
    "<p>Click &ldquo;Next&rdquo; to start reading through your slides, section by section.</p>";
  document.getElementById("summarizeBackBtn").disabled = true;
  document.getElementById("summarizeNextBtn").innerText = "Next →";
  document.getElementById("summarizeNextBtn").disabled = false;
}

function showSummarizePart(index, data) {
  summarizeState.partIndex = index;
  document.getElementById("summarizePartLabel").innerText =
    "Part " + (index + 1) + " of " + summarizeState.totalParts +
    " (pages " + data.start_page + "-" + data.end_page + ")";
  document.getElementById("summarizeContent").innerHTML = marked.parse(data.summary);
  document.getElementById("summarizeBackBtn").disabled = index <= 0;

  const isLast = index >= summarizeState.totalParts - 1;
  document.getElementById("summarizeNextBtn").innerText = isLast ? "Done" : "Next →";
  document.getElementById("summarizeNextBtn").disabled = isLast;

  refreshHistorySidebar();
}

async function loadSummarizePart(index) {
  if (summarizeState.cache[index]) {
    showSummarizePart(index, summarizeState.cache[index]);
    return;
  }

  document.getElementById("summarizePartLabel").innerText = "Generating...";
  document.getElementById("summarizeNextBtn").disabled = true;
  document.getElementById("summarizeBackBtn").disabled = true;

  const res = await fetch("/summarize-part", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ part_index: index }),
  });

  if (!res.ok) {
    document.getElementById("summarizeContent").innerHTML =
      "<p>" + escapeHtml(await getErrorMessage(res)) + "</p>";
    document.getElementById("summarizePartLabel").innerText = "Not started yet";
    document.getElementById("summarizeNextBtn").disabled = false;
    document.getElementById("summarizeBackBtn").disabled = index <= 0;
    return;
  }

  const data = await res.json();
  summarizeState.totalParts = data.total_parts;
  summarizeState.cache[index] = data;
  showSummarizePart(index, data);
}

document.getElementById("summarizeNextBtn").addEventListener("click", () => {
  loadSummarizePart(summarizeState.partIndex + 1);
});

document.getElementById("summarizeBackBtn").addEventListener("click", () => {
  if (summarizeState.partIndex > 0) {
    loadSummarizePart(summarizeState.partIndex - 1);
  }
});

/* ---------------- Ask ---------------- */

document.getElementById("askButton").addEventListener("click", async () => {
  const input = document.getElementById("questionInput");
  const question = input.value.trim();
  if (!question) return;

  const res = await fetch("/ask", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question: question }),
  });

  const entry = document.createElement("div");
  entry.className = "result-entry";

  if (!res.ok) {
    entry.innerHTML =
      '<p class="qa-question">' + escapeHtml(question) + "</p>" +
      '<div class="result-card"><div class="result-body">' + escapeHtml(await getErrorMessage(res)) + "</div></div>";
    document.getElementById("askResults").prepend(entry);
    return;
  }

  const data = await res.json();
  entry.innerHTML =
    '<p class="qa-question">' + escapeHtml(question) + "</p>" +
    '<div class="result-card"><div class="result-body">' + marked.parse(data.answer) + "</div></div>";
  document.getElementById("askResults").prepend(entry);

  input.value = "";
  refreshHistorySidebar();
});

/* ---------------- Quiz ---------------- */

let quizCounter = 0;

// Builds the HTML for one quiz (without attaching click handlers yet --
// the container needs to actually exist in the page first).
function buildQuizHtml(quizData) {
  quizCounter++;
  const containerId = "quiz-" + quizCounter;
  let html = '<div id="' + containerId + '">';
  quizData.questions.forEach((q, qIndex) => {
    html += '<div class="quiz-question" data-question-index="' + qIndex + '">';
    html += '<p class="quiz-question-text">' + (qIndex + 1) + ". " + escapeHtml(q.question) + "</p>";
    html += '<div class="quiz-options">';
    ["a", "b", "c", "d"].forEach((letter) => {
      const optionText = q["option_" + letter];
      html += '<button type="button" class="quiz-option" data-letter="' + letter.toUpperCase() + '">';
      html += '<span class="quiz-option-letter">' + letter.toUpperCase() + "</span><span>" + escapeHtml(optionText) + "</span>";
      html += "</button>";
    });
    html += "</div></div>";
  });
  html += "</div>";
  return { html: html, containerId: containerId };
}

// Wires up click-to-answer behavior for one quiz's buttons, once its
// HTML is actually in the page.
function attachQuizHandlers(containerId, quizData) {
  const container = document.getElementById(containerId);
  container.querySelectorAll(".quiz-question").forEach((questionEl) => {
    const qIndex = questionEl.getAttribute("data-question-index");
    const correctLetter = quizData.questions[qIndex].correct_answer;

    questionEl.querySelectorAll(".quiz-option").forEach((optionButton) => {
      optionButton.addEventListener("click", () => {
        const chosenLetter = optionButton.getAttribute("data-letter");

        questionEl.querySelectorAll(".quiz-option").forEach((btn) => {
          btn.disabled = true;
          if (btn.getAttribute("data-letter") === correctLetter) {
            btn.classList.add("correct");
          }
        });

        if (chosenLetter !== correctLetter) {
          optionButton.classList.add("incorrect");
        }
      });
    });
  });
}

document.getElementById("quizButton").addEventListener("click", async () => {
  const res = await fetch("/quiz", { method: "POST" });

  if (!res.ok) {
    document.getElementById("quizResult").innerHTML =
      "<p>" + escapeHtml(await getErrorMessage(res)) + "</p>";
    return;
  }

  const data = await res.json();
  const built = buildQuizHtml(data.quiz);
  document.getElementById("quizResult").innerHTML = built.html;
  attachQuizHandlers(built.containerId, data.quiz);
  refreshHistorySidebar();
});

/* ---------------- New chat ---------------- */

document.getElementById("newChatButton").addEventListener("click", async () => {
  await fetch("/new-chat", { method: "POST" });

  document.getElementById("uploadStatusText").innerText = "";
  document.getElementById("fileCard").style.display = "none";
  document.getElementById("dropzoneTitle").innerText = "Click to choose a PDF";
  document.getElementById("dropzoneHint").innerText = "or drag one here";
  pdfFileInput.value = "";

  resetSummarizeState();
  document.getElementById("askResults").innerHTML = "";
  document.getElementById("quizResult").innerHTML = "";

  document.querySelectorAll(".tab").forEach((t) => t.classList.remove("active"));
  document.querySelector('.tab[data-tab="upload"]').classList.add("active");
  switchPanel("panel-upload");
});

/* ---------------- History (sidebar) ---------------- */

const typeLabels = { summary: "Summary", answer: "Question", quiz: "Quiz" };
let historyData = null;

async function refreshHistorySidebar() {
  const res = await fetch("/history");
  historyData = await res.json();
  renderHistorySidebar();
}

function renderHistorySidebar() {
  const list = document.getElementById("historyList");

  if (!historyData || historyData.conversations.length === 0) {
    list.innerHTML = '<li class="history-empty">No history yet</li>';
    return;
  }

  list.innerHTML = "";
  historyData.conversations.forEach((conversation, index) => {
    const li = document.createElement("li");
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "history-item";
    btn.innerHTML = '<div class="history-item-title">' + escapeHtml(conversation.title) + "</div>";
    btn.addEventListener("click", () => openHistoryDetail(index));
    li.appendChild(btn);
    list.appendChild(li);
  });
}

async function openHistoryDetail(index) {
  const conversation = historyData.conversations[index];

  // Make this the active conversation so the Upload/Summarize/Ask/Quiz
  // tabs start operating on it -- exactly like the current chat. Already
  // generated summary parts are cached in the database, so resuming
  // Summarize on this conversation won't spend Gemini quota again.
  await fetch("/activate-conversation", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ conversation_id: conversation.id }),
  });
  resetSummarizeState();
  document.getElementById("askResults").innerHTML = "";
  document.getElementById("quizResult").innerHTML = "";

  document.querySelectorAll(".tab").forEach((t) => t.classList.remove("active"));
  document.querySelectorAll(".history-item").forEach((h) => h.classList.remove("active"));
  document.querySelectorAll(".history-item")[index].classList.add("active");

  let html = '<div class="panel-intro"><p class="panel-eyebrow">History &middot; now active</p><h1 class="panel-title">' +
    escapeHtml(conversation.title) + "</h1><p class=\"panel-desc\">This conversation is active again -- use the Summarize, Ask, or Quiz tabs to continue it.</p></div>";

  const quizzesToWireUp = [];

  conversation.results.forEach((result) => {
    const label = result.question
      ? typeLabels[result.type] + ": " + escapeHtml(result.question)
      : typeLabels[result.type];
    const time = new Date(result.created_at).toLocaleString();

    html += '<div class="result-entry">';
    html += '<p class="result-label">' + label + "</p>";
    html += '<p class="result-meta">' + escapeHtml(result.file_name) + " &middot; " + time + "</p>";

    if (result.type === "quiz") {
      const quizData = JSON.parse(result.output);
      const built = buildQuizHtml(quizData);
      html += built.html;
      quizzesToWireUp.push({ containerId: built.containerId, quizData: quizData });
    } else {
      html += '<div class="result-card"><div class="result-body">' + marked.parse(result.output) + "</div></div>";
    }

    html += "</div>";
  });

  document.getElementById("panel-history").innerHTML = html;
  switchPanel("panel-history");

  quizzesToWireUp.forEach((entry) => attachQuizHandlers(entry.containerId, entry.quizData));
}

refreshHistorySidebar();
