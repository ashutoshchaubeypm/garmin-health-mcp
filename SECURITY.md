# Security and private data

Never commit real API keys, token caches, Garmin responses, exports, PDFs, screenshots, personal paths, tunnel/workspace IDs or chat URLs. Use synthetic fixtures only. `.gitignore` is defense in depth, not a secret scanner. Review `git diff --cached` and run a secret scanner before publishing.

Credentials are saved outside the repository in the OS user's data directory. This is a single-user local stdio server, not a hosted multi-user service. Do not expose it through an unauthenticated public HTTP wrapper. For a business integration, use Garmin's business program and design authentication, isolation, consent and retention separately.

Report vulnerabilities privately using GitHub private vulnerability reporting if enabled. If it is unavailable, open an issue asking for a private contact without including exploit details, keys, health data or logs. Never submit secrets in a public issue. Revoke any accidentally exposed key immediately; deleting a file from the current branch does not remove Git history.

Tool errors intentionally omit upstream response text and credentials. Raw Garmin responses intentionally reach the requested AI client; review that client's privacy settings. Treat provider text as untrusted data. Model instructions are guidance, not a guaranteed clinical or security control.
