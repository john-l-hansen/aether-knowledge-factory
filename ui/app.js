document.addEventListener("DOMContentLoaded", () => {
  initTabs();
  fetchKnowledge();
  fetchDrafts();
  initGenerator();
});

// Tab Switcher
function initTabs() {
  const navItems = document.querySelectorAll(".nav-item");
  const tabContents = document.querySelectorAll(".tab-content");

  navItems.forEach(item => {
    item.addEventListener("click", () => {
      const tabId = item.getAttribute("data-tab");
      
      // Update nav class
      navItems.forEach(nav => nav.classList.remove("active"));
      item.classList.add("active");

      // Update panel class
      tabContents.forEach(tab => tab.classList.remove("active"));
      document.getElementById(`tab-${tabId}`).classList.add("active");
    });
  });
}

// Fetch Active Knowledge
async function fetchKnowledge() {
  const grid = document.getElementById("knowledge-grid");
  grid.innerHTML = "<div class='loading'>Loading active repository...</div>";

  try {
    const res = await fetch("/api/knowledge");
    const data = await res.json();
    window.knowledgeData = data;
    renderKnowledge(data);
  } catch (err) {
    grid.innerHTML = `<div class='error'>Failed to load repository: ${err}</div>`;
  }
}

// Render Active Knowledge Grid
function renderKnowledge(units, filterType = "all") {
  const grid = document.getElementById("knowledge-grid");
  grid.innerHTML = "";

  const filtered = filterType === "all" ? units : units.filter(u => u.type === filterType);

  if (filtered.length === 0) {
    grid.innerHTML = "<div class='empty'>No active knowledge units found.</div>";
    return;
  }

  filtered.forEach(unit => {
    const card = document.createElement("div");
    card.className = "card";
    card.innerHTML = `
      <div class="card-header">
        <span class="card-badge ${unit.type}">${unit.type}</span>
        <span class="confidence-val">Confidence: ${Math.round(unit.confidence * 100)}%</span>
      </div>
      <h3>${escapeHtml(unit.title)}</h3>
      <div class="card-body">${escapeHtml(unit.content || "")}</div>
      <div class="card-footer">
        <span class="card-id">${escapeHtml(unit.id)}</span>
      </div>
    `;
    grid.appendChild(card);
  });

  // Filter Buttons binding
  const filterBtns = document.querySelectorAll(".filter-btn");
  filterBtns.forEach(btn => {
    btn.onclick = () => {
      filterBtns.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      renderKnowledge(window.knowledgeData, btn.getAttribute("data-type"));
    };
  });
}

// Fetch Pending Drafts
async function fetchDrafts() {
  const grid = document.getElementById("drafts-grid");
  const countBadge = document.getElementById("drafts-count");
  grid.innerHTML = "<div class='loading'>Loading pending drafts...</div>";

  try {
    const res = await fetch("/api/drafts");
    const data = await res.json();
    countBadge.textContent = data.length;
    renderDrafts(data);
  } catch (err) {
    grid.innerHTML = `<div class='error'>Failed to load drafts: ${err}</div>`;
  }
}

// Render Drafts
function renderDrafts(drafts) {
  const grid = document.getElementById("drafts-grid");
  grid.innerHTML = "";

  if (drafts.length === 0) {
    grid.innerHTML = "<div class='empty'>No pending drafts. Your repository is fully synchronized!</div>";
    return;
  }

  drafts.forEach(draft => {
    const card = document.createElement("div");
    card.className = "card";
    card.innerHTML = `
      <div class="card-header">
        <span class="card-badge ${draft.type}">${draft.type}</span>
        <span class="confidence-val">Confidence: ${Math.round(draft.confidence * 100)}%</span>
      </div>
      <h3>${escapeHtml(draft.title)}</h3>
      <div class="card-body">${escapeHtml(draft.content || "")}</div>
      <div class="card-footer">
        <span class="card-id">${escapeHtml(draft.id)}</span>
        <button class="btn btn-sm" onclick="approveDraft('${draft.id}')">Approve</button>
      </div>
    `;
    grid.appendChild(card);
  });
}

// Approve Draft Action
async function approveDraft(id) {
  try {
    const res = await fetch(`/api/approve?id=${id}`, { method: "POST" });
    const result = await res.json();
    if (result.success) {
      fetchKnowledge();
      fetchDrafts();
    } else {
      alert(`Approval error: ${result.error}`);
    }
  } catch (err) {
    alert(`Failed to execute approval: ${err}`);
  }
}

// Ingestion/Generation Launcher
function initGenerator() {
  const runBtn = document.getElementById("btn-run-brief");
  const topicInput = document.getElementById("generator-topic");
  const outputBox = document.getElementById("generation-output");
  const outputText = document.getElementById("output-text");

  runBtn.onclick = async () => {
    const topic = topicInput.value.strip ? topicInput.value.strip() : topicInput.value;
    if (!topic) {
      alert("Please specify a topic.");
      return;
    }

    runBtn.disabled = true;
    runBtn.textContent = "Processing Stage 1 Briefing...";
    outputBox.style.display = "block";
    outputText.textContent = "🚀 Starting briefing agent...\n";

    try {
      const res = await fetch(`/api/generate?topic=${encodeURIComponent(topic)}`, { method: "POST" });
      const data = await res.json();
      if (data.success) {
        outputText.textContent += `\nOutput Logs:\n${data.logs}\n\n`;
        outputText.textContent += `🎉 Success! Content Brief generated and saved under drafts.`;
      } else {
        outputText.textContent += `\n❌ Pipeline Error: ${data.error}`;
      }
    } catch (err) {
      outputText.textContent += `\n❌ Failed to contact API server: ${err}`;
    } finally {
      runBtn.disabled = false;
      runBtn.textContent = "Generate Content Brief (Stage 1)";
    }
  };
}

// Helpers
function escapeHtml(str) {
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
