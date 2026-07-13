document.addEventListener("DOMContentLoaded", () => {
  initTabs();
  fetchKnowledge();
  fetchDrafts();
  initIngest();
  initGenerator();
  fetchPublications();
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

      // Refetch when switching
      if (tabId === "knowledge") fetchKnowledge();
      if (tabId === "drafts") fetchDrafts();
      if (tabId === "publications") fetchPublications();
      if (tabId === "generator") checkCurrentBrief();
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

// Raw Ingest
function initIngest() {
  const ingestBtn = document.getElementById("btn-run-ingest");
  const ingestInput = document.getElementById("ingest-text");
  const ingestOutput = document.getElementById("ingest-output");
  const ingestOutputText = document.getElementById("ingest-output-text");

  ingestBtn.onclick = async () => {
    const text = ingestInput.value.trim();
    if (!text) {
      alert("Please paste some notes or raw text.");
      return;
    }

    ingestBtn.disabled = true;
    ingestBtn.textContent = "Ingesting...";
    ingestOutput.style.display = "block";
    ingestOutputText.textContent = "🧠 Processing raw input...\n";

    try {
      const res = await fetch("/api/ingest", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text })
      });
      const data = await res.json();
      if (data.success) {
        ingestOutputText.textContent += `\nLogs:\n${data.logs}\n\n🎉 Completed! New draft units are now ready in 'Pending Review' tab.`;
        ingestInput.value = "";
        fetchDrafts();
      } else {
        ingestOutputText.textContent += `\n❌ Error: ${data.error}`;
      }
    } catch (err) {
      ingestOutputText.textContent += `\n❌ Failed connection: ${err}`;
    } finally {
      ingestBtn.disabled = false;
      ingestBtn.textContent = "Extract Knowledge Units";
    }
  };
}

// Generator
function initGenerator() {
  const runBtn = document.getElementById("btn-run-brief");
  const topicInput = document.getElementById("generator-topic");
  const outputBox = document.getElementById("generation-output");
  const outputText = document.getElementById("output-text");
  const approveBriefBtn = document.getElementById("btn-approve-brief");
  const runWriteBtn = document.getElementById("btn-run-write");

  runBtn.onclick = async () => {
    const topic = topicInput.value.trim();
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
        outputText.textContent += `\nLogs:\n${data.logs}\n\n`;
        outputText.textContent += `🎉 Success! Content Brief generated and saved.`;
        checkCurrentBrief();
      } else {
        outputText.textContent += `\n❌ Pipeline Error: ${data.error}`;
      }
    } catch (err) {
      outputText.textContent += `\n❌ Failed to contact API server: ${err}`;
    } finally {
      runBtn.disabled = false;
      runBtn.textContent = "Compile Content Brief (Stage 1)";
    }
  };

  approveBriefBtn.onclick = async () => {
    approveBriefBtn.disabled = true;
    try {
      const res = await fetch("/api/brief/approve", { method: "POST" });
      const data = await res.json();
      if (data.success) {
        alert("Brief approved successfully!");
        runWriteBtn.disabled = false;
        checkCurrentBrief();
      } else {
        alert(`Failed: ${data.error}`);
      }
    } catch (err) {
      alert(`Error: ${err}`);
    } finally {
      approveBriefBtn.disabled = false;
    }
  };

  runWriteBtn.onclick = async () => {
    runWriteBtn.disabled = true;
    runWriteBtn.textContent = "Assembling Draft...";
    outputBox.style.display = "block";
    outputText.textContent = "✍️ Querying Copywriter and Publisher agents...\n";

    try {
      const res = await fetch("/api/write", { method: "POST" });
      const data = await res.json();
      if (data.success) {
        outputText.textContent += `\nLogs:\n${data.logs}\n\n🎉 Success! Article assembled and saved under 'Webflow Publishing'.`;
        fetchPublications();
      } else {
        outputText.textContent += `\n❌ Error: ${data.error}`;
      }
    } catch (err) {
      outputText.textContent += `\n❌ Connection failed: ${err}`;
    } finally {
      runWriteBtn.disabled = false;
      runWriteBtn.textContent = "Assemble Article (Stage 2)";
    }
  };
}

// Check Current Brief
async function checkCurrentBrief() {
  const container = document.getElementById("generator-stage-2");
  const display = document.getElementById("brief-json-display");
  const runWriteBtn = document.getElementById("btn-run-write");

  try {
    const res = await fetch("/api/brief");
    const data = await res.json();
    if (data.topic) {
      container.style.display = "block";
      display.textContent = JSON.stringify(data, null, 2);
      
      // If brief is approved, enable writing stage
      if (data.status === "approved") {
        runWriteBtn.disabled = false;
      } else {
        runWriteBtn.disabled = true;
      }
    } else {
      container.style.display = "none";
    }
  } catch (err) {
    console.error("Failed to check brief:", err);
  }
}

// Fetch Publications
async function fetchPublications() {
  const grid = document.getElementById("publications-grid");
  grid.innerHTML = "<div class='loading'>Loading publications...</div>";

  try {
    const res = await fetch("/api/publications");
    const data = await res.json();
    renderPublications(data);
  } catch (err) {
    grid.innerHTML = `<div class='error'>Failed to load publications: ${err}</div>`;
  }
}

// Render Publications
function renderPublications(pubs) {
  const grid = document.getElementById("publications-grid");
  grid.innerHTML = "";

  if (pubs.length === 0) {
    grid.innerHTML = "<div class='empty'>No publications assembled yet. Approve a brief and write to generate ones.</div>";
    return;
  }

  pubs.forEach(pub => {
    const card = document.createElement("div");
    card.className = "card";
    card.innerHTML = `
      <div class="card-header">
        <span class="card-badge insight">Draft</span>
      </div>
      <h3>${escapeHtml(pub.name)}</h3>
      <div class="card-body">File Path: <code>${escapeHtml(pub.file)}</code></div>
      <div class="card-footer">
        <button class="btn btn-sm" onclick="publishPublication('${pub.file}')">Publish to Webflow</button>
      </div>
    `;
    grid.appendChild(card);
  });
}

// Publish to Webflow Action
async function publishPublication(filePath) {
  const outputBox = document.getElementById("publish-output");
  const outputText = document.getElementById("publish-output-text");

  outputBox.style.display = "block";
  outputText.textContent = `🚀 Publishing ${filePath} to live Webflow CMS...\n`;

  try {
    const res = await fetch(`/api/publish?file=${encodeURIComponent(filePath)}`, { method: "POST" });
    const data = await res.json();
    if (data.success) {
      outputText.textContent += `\nLogs:\n${data.logs}\n\n🎉 Done! Content successfully published to live Webflow collection.`;
    } else {
      outputText.textContent += `\n❌ Error: ${data.error}`;
    }
  } catch (err) {
    outputText.textContent += `\n❌ Connection failed: ${err}`;
  }
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
