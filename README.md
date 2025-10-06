# Intelligent Code Review Assistant (CI-Only)

Automated code reviews on every Pull Request — **no paid APIs, no servers**.  
Runs entirely in **GitHub Actions** using a local LLM (via Ollama) + static analyzers (Semgrep, Bandit). Posts a consolidated review back to the PR. Privacy-friendly: code never leaves the GitHub runner.

---

## ✨ What You Get

- Combined **LLM + Static Analysis** review with clear severity, evidence, and actionable fixes
- Single consolidated PR review comment (falls back to a regular PR comment if needed)
- Works on **fork PRs** (safe checkout)
- **Model cache** to avoid re-downloading weights on each run
- **Static-only fallback** when the model isn’t ready yet (your PR still gets useful feedback)
- Token-aware diff truncation to keep prompts fast and reliable

---

## 🧠 How It Works (High Level)

1. **Trigger**: Workflow runs on `pull_request` and `pull_request_target`.
2. **Safe checkout**: Checks out the PR head (read-only) so it works with forks safely.
3. **Setup**: Installs pinned Python libs, starts the Ollama container, restores model cache.
4. **Analysis**:
   - Collects changed-file diffs from the GitHub API
   - Scans the repository with Semgrep and Bandit
5. **LLM Review**: Builds a compact prompt (diffs + summarized findings) and queries a small local code model.
   - If the model isn’t available yet, it automatically posts a **static-only** review.
6. **Post Back**: Tries the Pull Request Reviews API first; falls back to Issues API for a standard PR comment.

---

## 📁 Repository Layout (Key Files)

```plaintext
.
├─ app/
│ ├─ **init**.py
│ ├─ prompts/
│ │ ├─ **init**.py
│ │ └─ reviewer_prompt.txt
│ └─ services/
│ ├─ **init**.py
│ ├─ analyzers.py
│ ├─ diff_utils.py
│ └─ llm.py
├─ scripts/
│ └─ ci_review.py
├─ .github/
│ └─ workflows/
│ └─ review.yml
├─ requirements.txt # for local dev (Actions installs pinned deps directly)
└─ README.md

```

> Keep the three `__init__.py` files. They make `app/` a proper Python package.

---

## 🚀 Quick Start

1. **Add the files** listed above to your repository (preserving paths).
2. **Enable Actions** in your repo settings if disabled.
3. **Commit to `main`** (or default branch).
4. **Open a Pull Request** (any small change).
5. **Watch the workflow** run on the PR; a comment with the automated review appears on the PR Conversation tab.

That’s all you need for a working baseline.

---

## ⚙️ Configuration (No Code Needed)

- **Model selection**

  - Default model: `starcoder2:3b` (small & fast to download).
  - To change it, edit the `LLM_MODEL` environment variable in `.github/workflows/review.yml`.
  - Larger models are supported; the cache mitigates download time after the first run.

- **Model cache**

  - The workflow mounts a persistent cache directory so **subsequent runs** don’t re-download weights.
  - On the **very first** run, expect a short download; later runs use the cache.

- **Permissions**

  - The workflow already requests `contents: read`, `pull-requests: write`, and `issues: write`.
  - This enables posting reviews on both same-repo and fork PRs.

- **Package imports**

  - Ensure `app/__init__.py`, `app/services/__init__.py`, and `app/prompts/__init__.py` exist.
  - The workflow sets `PYTHONPATH` to the repo root so imports work reliably.

- **Secrets**
  - Uses the built-in `GITHUB_TOKEN` provided by GitHub Actions for posting comments.
  - No external tokens are required for the default setup.

---

## 🔐 Security Notes (Fork-Safe)

- Uses `pull_request_target` for permission to comment on fork PRs, **with safe checkout** of the PR head.
- **Pinned dependencies** are installed directly in the workflow (not from PR-controlled files).
- Analyzers **scan** files; they do not execute repository code.
- The LLM runs **locally** in the runner (Ollama container); code and findings remain in your CI environment.

---

## 🧪 What to Expect on a PR

- A consolidated review comment that includes:
  - A short summary of key issues
  - Findings with severity, evidence (file:line), why it matters, and concrete recommendations
  - Optional patch suggestions in unified diff form (when the model proposes them)
  - If the model isn’t ready yet, the comment still includes **Semgrep/Bandit findings** (static-only)

---

## 🛠️ Troubleshooting

- **No comment appeared**

  - Open the PR’s **Checks** → the workflow logs.
  - Confirm you see steps completing for checkout, Python setup, analyzer runs, and “posted PR review” (or “posted issue comment”).
  - Verify workflow **permissions** match the values listed above.

- **Import error: “No module named app”**

  - Ensure the three package marker files are present: `app/__init__.py`, `app/services/__init__.py`, `app/prompts/__init__.py`.
  - Confirm the workflow sets `PYTHONPATH` to the repo root (it does by default).

- **Ollama API not responding / very slow run**

  - First runs can download a model; later runs use the cache.
  - Keep the default small model for speed (`starcoder2:3b`).
  - Even if the model isn’t ready in time, the workflow **does not block**; it posts a static-only review.

- **Semgrep or Bandit fail**
  - Review the workflow logs for analyzer error messages.
  - Add `.semgrepignore` in your repo root if needed to exclude large or generated directories.

---

## 🧩 Extend It (Optional)

- **Language linters**: Add ESLint (JS/TS), Ruff/Flake8 (Python), gosec/golangci-lint (Go), Brakeman (Ruby), etc.
- **Inline comments**: Map findings to exact file/line and use the PR comments API for per-line feedback.
- **Quality gates**: Fail the job on High-severity issues unless a maintainer label (e.g., “security-approved”) is present.
- **Prompt tuning**: Adjust `app/prompts/reviewer_prompt.txt` to match your team’s voice and policies.
- **GitLab support**: Reuse the same analyzer + LLM pipeline, swap GitHub API calls for GitLab MR APIs.

---

## 📈 Measuring Value

- Track PR metrics before/after enablement:
  - Time from PR open → first review
  - Time from PR open → merge
  - High-severity issues per PR
  - False-positive reduction after prompt/rule tuning
- Optional: add a weekly summary job that aggregates findings and trends.

---

## 🧰 Maintenance

- Update model tag and dependencies periodically in `.github/workflows/review.yml`.
- If you ever need to refresh model weights, bump the cache key in the workflow (e.g., add `-v2` to the key name).
- Keep Semgrep rules current; add a `.semgrepignore` for noisy paths.

---

## 📜 License

MIT (or your preferred license). Add a `LICENSE` file at repo root if needed.

---

## 🙋 Support

If a PR doesn’t receive a comment, share the last ~50 lines from the workflow logs (especially around the analyzer steps and final posting) in an issue. The logs include clear messages so we can pinpoint the fix quickly.
