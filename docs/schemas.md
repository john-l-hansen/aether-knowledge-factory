# Schema Specifications: Aether Knowledge Factory

To ensure consistency and allow programmatic validation of inputs and outputs across various specialized agents, all knowledge units and content assemblies must adhere to defined schemas.

## 1. Knowledge Unit Schema

Knowledge units are stored as markdown files with a YAML frontmatter block. This structured metadata describes the source, type, confidence, and relationships of the asset.

### Example Markdown Structure (`knowledge/concepts/ai-creative-design.md`)
```markdown
---
id: concept-ai-creative-design
title: The Role of Generative AI in Creative Design
type: concept
tags: [ai, design, creative-workflows]
confidence: 0.95
last_updated: 2026-07-12
sources:
  - name: "Aether Creative Studio Internal Playbook"
    url: "https://aether.creative/internal/playbook"
relations:
  - id: concept-human-centric-design
    type: expands
---

Generative AI acts as a creative partner rather than a replacement. It accelerates the ideation phase by generating hundreds of initial concepts, allowing human designers to focus on curation, refinement, and strategic execution.
```

---

## 2. Content Brief Schema

When assembling content, the Orchestrator requests a **Content Brief** from the Researcher Agent. The Content Brief must be a structured JSON object containing:
- `topic`: The core theme.
- `target_audience`: Who the content is for.
- `key_takeaways`: Core messages compiled from the Knowledge Layer.
- `outline`: Section headers and the corresponding knowledge units to reference.

### JSON Schema (`factory/schemas/content_brief.json`)
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "ContentBrief",
  "type": "OBJECT",
  "properties": {
    "topic": { "type": "STRING" },
    "target_audience": { "type": "STRING" },
    "key_takeaways": {
      "type": "ARRAY",
      "items": { "type": "STRING" }
    },
    "outline": {
      "type": "ARRAY",
      "items": {
        "type": "OBJECT",
        "properties": {
          "section_title": { "type": "STRING" },
          "points": {
            "type": "ARRAY",
            "items": { "type": "STRING" }
          },
          "referenced_knowledge_ids": {
            "type": "ARRAY",
            "items": { "type": "STRING" }
          }
        },
        "required": ["section_title", "points"]
      }
    }
  },
  "required": ["topic", "target_audience", "key_takeaways", "outline"]
}
```
