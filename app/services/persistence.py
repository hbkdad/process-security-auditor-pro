import subprocess, json

def list_windows_startup_items():
    # Defensive audit only. Uses registry QUERY commands; no modification.
    commands = [
        ["reg","query",r"HKCU\Software\Microsoft\Windows\CurrentVersion\Run"],
        ["reg","query",r"HKLM\Software\Microsoft\Windows\CurrentVersion\Run"],
    ]
    items=[]
    for cmd in commands:
        try:
            out = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL, creationflags=0x08000000)
            for line in out.splitlines():
                line=line.strip()
                if line and not line.startswith("HKEY"):
                    items.append(line)
        except Exception:
            pass
    return items
