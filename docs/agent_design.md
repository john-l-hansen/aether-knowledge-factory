# Agent Design Guidelines

The Aether Knowledge Factory uses specialized, single-responsibility agents. This document details the standards for defining, configuration, and prompt engineering of these agents.

## 1. Single Responsibility Principle (SRP)

An agent should do one thing extremely well. Do not combine research, writing, and review into a single agent. Instead:
- **Research Agent**: Query databases, search the web, compile information.
- **Synthesizer Agent**: Structure raw data into schemas.
- **Copywriter Agent**: Transform structured inputs into engaging written copy.
- **Reviewer Agent**: Checks copy against voice guidelines and brand rules.

---

## 2. Formatting Enforcements

To keep pipeline automation reliable, write system prompts that instruct the agent to output clean JSON or YAML blocks without markdown wrappers, unless the orchestrator's validation layer is built to strip them.

For example, a prompt targeting a JSON-structured output should look like:
```
You must output a raw JSON object matching the requested schema.
Do not wrap your output in ```json ... ``` code blocks.
Do not include any pre-text or post-text.
```

---

## 3. Configuration Management

Agents should be configured inside Python modules using configurations that read parameters from a centralized config or environment.
* Keep system prompts in separate prompt template files or clean variables inside agent modules.
* Use explicit capabilities configurations (e.g. enable search or file system access only for the Researcher agent).
* Avoid inline anonymous configs in the main `orchestrator.py` script. Keep them declared within `factory/agents/`.
