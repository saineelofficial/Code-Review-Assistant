import json
import os
import pathlib
import sys
import traceback
import httpx

# --- Import local services (make sure app/__init__.py and app/services/__init__.py exist) ---
from ..services import analyzers
from ..services.diff_utils import prune_patch
from ..services.llm import review_with_llm

MAX_DIFF_BUDGET = 7000
PER_FILE_BUDGET = 2000

def log(msg: str):
    print(msg, flush=True)

def get_pr_info():
    event_path = os.environ["GITHUB_EVENT_PATH"]
    data = json.loads(open(event_path, "r", encoding="utf-8").read())
    pr = data["pull_request"]
    repo = data["repository"]
    return {
        "owner": repo["owner"]["login"],
        "repo": repo["name"],
        "number": pr["number"],
    }

def get_changed_files(owner, repo, number, token):
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}/files"
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github+json"}
    with httpx.Client(timeout=60.0) as client:
        r = client.get(url, headers=headers)
    if r.status_code >= 400:
        log(f"❌ get_changed_files error {r.status_code}: {r.text}")
        r.raise_for_status()
    return r.json()

def post_review(owner, repo, number, body, token):
    """Try PR Reviews API first."""
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}/reviews"
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github+json"}
    payload = {"body": body, "event": "COMMENT"}
    with httpx.Client(timeout=60.0) as client:
        r = client.post(url, headers=headers, json=payload)
    return r

def post_issue_comment(owner, repo, number, body, token):
    """Fallback: regular PR comment (issues API)."""
    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{number}/comments"
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github+json"}
    payload = {"body": body}
    with httpx.Client(timeout=60.0) as client:
        r = client.post(url, headers=headers, json=payload)
    return r

def summarize_semgrep(res):
    items = res.get("results", [])[:25]
    if not items:
        return "No Semgrep findings."
    out = []
    for r in items:
        path = r.get("path")
        line = (r.get("start") or {}).get("line")
        cid = r.get("check_id")
        msg = (r.get("extra") or {}).get("message")
        out.append(f"- {cid} @ {path}:{line} — {msg}")
    return "\n".join(out)

def summarize_bandit(res):
    items = res.get("results", [])[:25]
    if not items:
        return "No Bandit findings."
    out = []
    for i in items:
        path = i.get("filename")
        line = i.get("line_number")
        tid = i.get("test_id")
        msg = i.get("issue_text")
        out.append(f"- {tid} @ {path}:{line} — {msg}")
    return "\n".join(out)

def try_llm(prompt: str) -> tuple[bool, str]:
    try:
        answer = review_with_llm(prompt)
        return True, answer
    except Exception as e:
        return False, f"LLM unavailable or not ready. Proceeding with static analysis only.\n\n> {e}"

def main():
    try:
        info = get_pr_info()
        token = os.environ["GITHUB_TOKEN"]
        log(f"ℹ️  Reviewing PR {info['owner']}/{info['repo']}#{info['number']}")

        # 1) Static analysis on the checked-out repo
        log("▶ Running Semgrep...")
        semgrep_res = analyzers.run_semgrep(".")
        log("✅ Semgrep done")

        log("▶ Running Bandit...")
        bandit_res  = analyzers.run_bandit(".")
        log("✅ Bandit done")

        # 2) Collect diffs for changed files
        log("▶ Fetching PR changed files...")
        changed = get_changed_files(info["owner"], info["repo"], info["number"], token)
        if not changed:
            log("⚠️ No changed files found by API; continuing with static analysis only.")

        diffs = []
        total = 0
        for f in changed or []:
            p = f.get("patch")
            if not p:
                continue
            pp = prune_patch(p, PER_FILE_BUDGET)
            entry = f"### {f['filename']}\n```diff\n{pp}\n```\n"
            if total + len(entry) > MAX_DIFF_BUDGET:
                break
            diffs.append(entry)
            total += len(entry)

        # 3) Build prompt (fallback to default if file missing)
        prompt_file = pathlib.Path("app/prompts/reviewer_prompt.txt")
        if prompt_file.exists():
            prompt_base = prompt_file.read_text(encoding="utf-8")
        else:
            prompt_base = (
                "You are a senior code reviewer. Analyze the DIFF and static findings.\n"
                "Output: Summary bullets; Findings with Severity/Evidence/Why/Fix; Optional patch diff."
            )

        semgrep_txt = summarize_semgrep(semgrep_res)
        bandit_txt  = summarize_bandit(bandit_res)

        prompt = f"""{prompt_base}

# DIFFS
{''.join(diffs)}

# STATIC ANALYSIS
## Semgrep
{semgrep_txt}

## Bandit
{bandit_txt}
"""

        # 4) LLM review (with fallback)
        log("▶ Generating LLM review (with fallback)...")
        ok, llm_answer = try_llm(prompt)
        if ok:
            body = f"""## Automated Review (LLM + Static Analysis)

{llm_answer}

---
<sub>Generated by Code Review Assistant (Semgrep/Bandit + Ollama)</sub>
"""
        else:
            body = f"""## Automated Review (Static Analysis Only)

{llm_answer}

### Semgrep
{semgrep_txt}

### Bandit
{bandit_txt}

---
<sub>Generated by Code Review Assistant (Semgrep/Bandit)</sub>
"""

        # 5) Post to PR
        log("▶ Posting PR review (Reviews API)...")
        r = post_review(info["owner"], info["repo"], info["number"], body, token)
        if r.status_code >= 400:
            log(f"⚠️ Reviews API failed {r.status_code}: {r.text}")
            log("▶ Falling back to Issue Comments API...")
            ir = post_issue_comment(info["owner"], info["repo"], info["number"], body, token)
            if ir.status_code >= 400:
                log(f"❌ Issue comment API failed {ir.status_code}: {ir.text}")
                ir.raise_for_status()
            else:
                log("✅ Posted issue comment on PR")
        else:
            log("✅ Posted PR review comment")

    except Exception:
        log("❌ Unhandled exception in ci_review.py")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
