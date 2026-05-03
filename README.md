# Process Security Auditor AV Pro

Defensive-only Windows desktop endpoint security/auditing app.

## New in AV Pro
- Start/Stop live protection
- Manual scan
- Better Tkinter dark UI
- Copy actions
- Export JSON/CSV
- GitHub Releases updater
- Pro license system
- Antivirus-style modules:
  - process risk scoring
  - startup/persistence audit
  - network connection checks
  - hash reputation hooks
  - local allow/block rules
  - safe quarantine workflow requiring explicit confirmation
  - scheduled/live monitor

## Build
Run on Windows:

```powershell
scripts\build_windows_exe.bat
```

Output:

```text
dist\ProcessSecurityAuditorAVPro.exe
```

## GitHub updater setup
Edit:

```text
app/core/config.py
```

Set:

```python
GITHUB_OWNER = "hbkdad"
GITHUB_REPO = "process-security-auditor-pro"
```

Publish GitHub Releases with an asset named:

```text
ProcessSecurityAuditorAVPro.exe
```

The updater checks:

```text
https://api.github.com/repos/<owner>/<repo>/releases/latest
```

## Licensing
This includes an offline license manager for Lite/Pro/Business tiers.

Generate a test license:

```powershell
python tools_generate_license.py --name "Michel" --tier pro --days 365
```

Paste the license into the app under License tab.

## Safety
This tool is defensive-only. It does not exploit, hide, inject, spread, or bypass security tools. Quarantine requires confirmation and moves files only when permissions allow.
