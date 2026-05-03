# v0.3.0 Upgrade Steps

## 1. Copy patch files into your project

Copy these files into your current project folder:

```text
app/services/updater.py
scripts/test_updater.py
docs/V0.3_RELEASE_NOTES.md
VERSION
```

Overwrite the existing updater.py.

## 2. Set version to 0.3.0

The included VERSION file contains:

```text
0.3.0
```

## 3. Build v0.3.0

```powershell
cd C:\Users\miche\OneDrive\Desktop\ProcessSecurityAuditor_PRO
.\scripts\build_windows_exe.bat
```

Confirm:

```powershell
dir dist
```

You should see your EXE.

## 4. Commit and push

```powershell
git add .
git commit -m "v0.3.0 updater reliability release"
git push origin main
```

## 5. Create GitHub release

Go to:

```text
https://github.com/hbkdad/process-security-auditor-pro/releases
```

Create release:

```text
Tag: v0.3.0
Title: Process Security Auditor Pro v0.3.0
```

Attach:

```text
dist\ProcessSecurityAuditorAVPro.exe
```

## 6. Test updater

To test from an older build, set local VERSION to `0.2.0`, rebuild that older copy, then run:

```powershell
python scripts\test_updater.py
```

Expected:

```text
update_available: true
latest_version: v0.3.0
asset_name: ProcessSecurityAuditorAVPro.exe
```
