# Intelligent Code Review Assistant (Free, CI-Only)

This repo template posts **automated code reviews on Pull Requests** using:
- ✅ **Semgrep** (multi-language static analysis)
- ✅ **Bandit** (Python security)
- ✅ **Ollama** + a **free local code model** (`qwen2.5-coder:7b-instruct`) via LangChain

Runs **entirely in GitHub Actions** — no servers, webhooks, or paid APIs needed.

---

## Quick Start

1. **Create a new GitHub repo** (or fork this).
2. Copy this template into your repo and push to `main`.
3. Create a new branch, make any code change, and **open a PR**.
4. The “Code Review Assistant” workflow runs, then posts a review comment on your PR.

That’s it.

---

## Notes

- You can switch models by editing the workflow `LLM_MODEL`. (Examples: `codellama:7b-instruct`, `starcoder2:7b`.)
- Large PRs get **diff truncation** to fit prompt size.
- To add linters for other languages (ESLint, Ruff, Gosec, etc.), extend `requirements.txt` and `scripts/ci_review.py`.
- This is CI-only by design. If you want a webhook server later, ask ChatGPT for the **FastAPI + Docker** variant.

---
