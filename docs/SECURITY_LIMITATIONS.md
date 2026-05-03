# Security Limitations

This is not a replacement for Microsoft Defender or a commercial EDR.

Current limits:
- process risk scoring is heuristic
- unsigned does not mean malicious
- signed does not mean safe
- VirusTotal/AbuseIPDB results depend on API keys and rate limits
- quarantine can fail for locked/protected files
- updater is MVP-style and should be code-signed before paid release

Recommended before monetization:
- sign EXE with Authenticode certificate
- publish reproducible GitHub releases
- add rollback protection
- add secure license server
- add tamper-resistant logs
