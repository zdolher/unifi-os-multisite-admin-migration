# Security and privacy

This toolkit is designed for **authorized administrators migrating their own customer infrastructure**. It can provision accounts with administrative rights; use only where you have written permission.

## Secrets and personal data

- The **populated Excel workbook** contains plaintext passwords. Store it in a restricted local folder, do not synchronize it to a cloud drive, do not email it, and do not upload it to public repositories or chat tools.
- `legacy_privileges.jsonl` contains usernames, email addresses and customer site identifiers/names. `target_sites.jsonl` contains site information. Both are confidential.
- `import_state.json` does **not** contain passwords, but can contain role UUIDs and usernames; keep private.
- Never upload Chrome profiles, HAR, `Copy as cURL`, raw HTTP Authorization headers, session cookies, CSRF tokens, private keys or TLS certificates.
- Rotate passwords that were ever shared outside the customer-controlled environment.
- Configure TLS verification (`allow_insecure_tls: false`). Only bypass it for temporary, isolated tests after reviewing the risks; don't make that a public deployment default.
- Clean backup/export files from transient locations after use and consider password-manager delivery rather than keeping a plaintext workbook indefinitely.

## Access control and safety

- **Least privilege:** always test that a restricted new account sees *only* expected sites.
- **Stop on uncertainty:** no automatic retries of failed POST calls. A network timeout might occur **after** the server created the role/user.
- **Do not run as the account being replaced.** Use an independent verified local Owner session for provisioning.
- **Manual Super Admins:** do not emulate global Super Admin with hundreds of per-site formulas. Their console-wide permissions must be explicitly assigned through the UI.
- **No DB writes:** exporters are read-only; importer uses the same app-side flow as the tested People interface.
- **Target verification:** import is blocked when positive legacy site IDs are missing from the target or internal site names differ.

## Public release scrub list

Before releasing screenshots, demos or a repository, search every file and revision history for: actual customer domains/IPs, usernames, emails, phone numbers, site names, MongoDB IDs, password fields with values, HTTP sessions, certificates and backups. Publish only the synthetic sample workbook included here. Check hidden Excel sheets, cells, comments, custom properties and archive history too.

This is a community proof of concept: the internal API may change. The tool does not replace penetration testing, access reviews or the vendor's support procedures.
