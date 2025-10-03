import json
import subprocess

def run_semgrep(path: str = ".") -> dict:
    # semgrep returns 1 when findings exist; treat 0/1 as OK
    res = subprocess.run(
        ["semgrep", "--config", "auto", "--json", "--error", path],
        capture_output=True, text=True
    )
    if res.returncode not in (0, 1):
        raise RuntimeError(f"Semgrep failed: {res.stderr}")
    return json.loads(res.stdout or "{}")

def run_bandit(path: str = ".") -> dict:
    res = subprocess.run(
        ["bandit", "-r", path, "-f", "json", "-q"],
        capture_output=True, text=True
    )
    if res.returncode not in (0, 1):
        raise RuntimeError(f"Bandit failed: {res.stderr}")
    try:
        return json.loads(res.stdout or "{}")
    except json.JSONDecodeError:
        return {"results": []}
