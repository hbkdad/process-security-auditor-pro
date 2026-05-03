import psutil, hashlib, os, re, time, json
from pathlib import Path
from app.core.paths import resource_path

SENSITIVE_PATTERNS = [
    re.compile(r"(?i)(password|passwd|pwd|token|apikey|api_key|secret)=\S+"),
]

KNOWN_SYSTEM_DIRS = [
    str(Path(os.environ.get("SystemRoot", r"C:\Windows")).resolve()).lower(),
    str(Path(os.environ.get("ProgramFiles", r"C:\Program Files")).resolve()).lower(),
    str(Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")).resolve()).lower(),
]

RISKY_DIR_PARTS = ["\\temp\\", "\\appdata\\local\\temp\\", "\\downloads\\", "\\users\\public\\"]

def redact_cmdline(cmd):
    if not cmd: return ""
    s = " ".join(cmd) if isinstance(cmd, list) else str(cmd)
    for pat in SENSITIVE_PATTERNS:
        s = pat.sub(lambda m: m.group(0).split("=")[0] + "=<REDACTED>", s)
    return s[:600]

def sha256_file(path):
    try:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for b in iter(lambda: f.read(1024*1024), b""):
                h.update(b)
        return h.hexdigest()
    except Exception:
        return ""

def load_json_rule(name):
    p = resource_path(f"app/rules/{name}")
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return {}

def scan_processes():
    allow = load_json_rule("allowlist.json")
    block = load_json_rule("blocklist.json")
    rows = []
    for p in psutil.process_iter(["pid","name","exe","ppid","username","cmdline","cpu_percent","memory_info"]):
        try:
            info = p.info
            exe = info.get("exe") or ""
            lower = exe.lower()
            file_hash = sha256_file(exe) if exe and os.path.exists(exe) else ""
            parent = ""
            try:
                parent = psutil.Process(info.get("ppid")).name()
            except Exception:
                pass
            conns = []
            try:
                for c in p.net_connections(kind="inet"):
                    if c.raddr:
                        conns.append(f"{c.raddr.ip}:{c.raddr.port}")
            except Exception:
                pass
            row = {
                "pid": info.get("pid"),
                "name": info.get("name") or "",
                "path": exe,
                "parent_pid": info.get("ppid"),
                "parent_name": parent,
                "user": info.get("username") or "",
                "cmdline": redact_cmdline(info.get("cmdline")),
                "cpu": info.get("cpu_percent") or 0,
                "memory_mb": round((getattr(info.get("memory_info"), "rss", 0) or 0)/1024/1024, 1),
                "hash": file_hash,
                "network": conns[:10],
                "startup": False,
                "signed_status": "Unknown",
                "source": "live",
            }
            row.update(score_process(row, allow, block))
            rows.append(row)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
        except Exception as e:
            continue
    return rows

def score_process(row, allow, block):
    score = 0
    reasons = []
    h = row.get("hash","")
    path = (row.get("path") or "").lower()
    name = (row.get("name") or "").lower()
    if h and h in block.get("hashes", []):
        return {"risk_score": 100, "verdict": "Malicious", "reasons": ["Hash appears in local blocklist"]}
    if h and h in allow.get("hashes", []):
        return {"risk_score": 5, "verdict": "Safe", "reasons": ["Hash appears in local allowlist"]}
    if any(part in path for part in RISKY_DIR_PARTS):
        score += 30; reasons.append("Executable is running from temp/download/public user location")
    if not row.get("path"):
        score += 12; reasons.append("Executable path unavailable")
    if row.get("network"):
        score += 10; reasons.append("Process has active network connections")
    cmd = row.get("cmdline","").lower()
    suspicious_flags = [" -enc", "frombase64string", "downloadstring", "invoke-webrequest", "bypass", "hidden", "iex "]
    if any(x in cmd for x in suspicious_flags):
        score += 35; reasons.append("Command line contains suspicious scripting/download/execution flags")
    if name in ["powershell.exe","cmd.exe","wscript.exe","cscript.exe","mshta.exe","rundll32.exe","regsvr32.exe"] and row.get("network"):
        score += 25; reasons.append("LOLBins/scripting host with network activity")
    if any(path.startswith(d) for d in KNOWN_SYSTEM_DIRS):
        score -= 15; reasons.append("Runs from standard Windows/Program Files path")
    score = max(0, min(100, score))
    verdict = "Safe" if score < 20 else "Unknown" if score < 40 else "Suspicious" if score < 80 else "Malicious"
    if not reasons:
        reasons.append("No strong risk signals found")
    return {"risk_score": score, "verdict": verdict, "reasons": reasons}
