# Aether Creative Studio - Knowledge Factory

Welcome to your AI-native knowledge operating system! This workspace is orchestrated using **Google Antigravity**.

## Architecture & Concept

The Factory is designed around a **Knowledge-Content-Page** hierarchy, separating permanent expert knowledge from delivery channels:
- **Knowledge Layer**: Permanent assets (YAML/Markdown files under `knowledge/`).
- **Content Layer**: Synthesized artifacts (blog drafts, outlines) validating against strict JSON schemas.
- **Page Layer**: Ephemeral delivery pages (Webflow API payload, HTML, etc.).

For a detailed walkthrough of our standards and decisions, read the documentation:
* [Architecture Design](file:///Users/johnhansen/.gemini/antigravity/scratch/aether-content-factory/docs/architecture.md)
* [Data Schemas](file:///Users/johnhansen/.gemini/antigravity/scratch/aether-content-factory/docs/schemas.md)
* [Agent Design Guidelines](file:///Users/johnhansen/.gemini/antigravity/scratch/aether-content-factory/docs/agent_design.md)

## Repository Structure

- `orchestrator.py`: The entry point for the content production pipeline.
- `factory/`: Core package containing agents, schemas, and utility modules.
- `docs/`: Design system, architecture, and standards docs.
- `requirements.txt`: Python package requirements.
- `.agents/AGENTS.md`: Workspace-scoped rules and style guidelines.

## Getting Started

1. **Set this Directory as your Active Workspace**:
   Ensure your IDE or Antigravity environment is pointed to this folder (`/Users/johnhansen/.gemini/antigravity/scratch/aether-content-factory`).

2. **Install Dependencies**:
   ```bash
   python3 -m pip install -r requirements.txt
   ```

3. **Run the Orchestrator**:
   ```bash
   python3 orchestrator.py
   ```
