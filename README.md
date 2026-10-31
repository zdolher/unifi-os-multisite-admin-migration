# UniFi multi-site local administrator migration toolkit (unofficial POC)

**Status:** community proof of concept · **Release:** 1.0.0-alpha · **Date:** 2026-10-31

Migrate **local-only administrator accounts and per-site Network permissions** from a legacy self-hosted UniFi Network Server to self-hosted UniFi OS Server, in cases where a Network backup brings across the sites and devices but not working UniFi OS local administrator identities.

> **Warning:** The administrator creation API used here is an **undocumented internal API**. It can change or be removed without notice. This is **not an official Ubiquiti tool**, not a supported alternative to the Ubiquiti migration procedure, and not a one-click system conversion. Test in an isolated environment, back up your production VM and applications, and verify each actual permission scope before using it at another customer.

**Field-tested workflow:** UniFi OS Server **5.1.42**, UniFi Network **10.5.67** (2026-10-31). A previous implementation was tested with a local-only read-only test account, a renamed account with two administrator sites, and a successful batch import in **one environment**. This newly generalized public package has been tested offline with synthetic data; it has **not** been independently live-tested on other servers or versions.

## What it does (and does not)

| Included | Not included / manual step |
|---|---|
| Read-only export of legacy `ace.admin`, `ace.site`, `ace.privilege` | Exporting or reusing legacy password hashes |
| Read-only list of sites from the **new** `ace.site` | Modifying MongoDB/PostgreSQL directly |
| Excel user-list template and explicit old-to-new username mapping | Creating system-level **Owner/Super Admin** accounts (manual) |
| Offline privilege preview, site-ID validation, duplicate mapping rejection | Changing already existing administrators' rights |
| Create private `network.management` role; then local-only account | Migrating devices, network settings or guest portals |
| API actions from a logged-in local Chrome session with CSRF header | Guaranteeing future API compatibility |
| Stop-on-error, persisted checkpoints, no automatic re-POST | Automatic recovery from uncertain partial creation |

Ubiquiti's **official** migration guide describes backups, Site Export, and installation; use it for the main controller migration. This toolkit addresses **only the local administrator gap**.

## Quick start (overview)

1. On the **legacy controller**, first back up the entire VM and export a Network backup. Export privilege data using `scripts/export_legacy.js` (read-only).
2. Install/migrate UniFi OS Server using the official process; keep only **one active production controller** at a time. Validate that sites and devices work.
3. On the **new controller**, export `target_sites.jsonl` with `scripts/export_target_sites.js` (read-only). The importer refuses to use legacy site permissions whose IDs do not exist in the target.
4. On a protected Windows admin PC, copy `templates/administrators_TEMPLATE.xlsx` to **`administrators.xlsx`**, replace fictional rows with real records, and complete columns. Set `legacy_username` explicitly for every rename; use `mode=manual` for Owner/Super Admin.
5. Copy `config.example.json` to **`config.json`** and set the correct HTTPS UniFi OS Server URL; assign `manual_admin_usernames` as needed.
6. Put `legacy_privileges.jsonl`, `target_sites.jsonl`, `administrators.xlsx`, `config.json` and `scripts/migrate_admins.py` in a private working directory. Install dependencies:

   ```powershell
   python -m pip install -r requirements.txt
   ```

   **Google Chrome must already be installed.** If you prefer Playwright Chromium, use `python -m playwright install chromium` and set `browser_channel` to `chromium` in `config.json`.

7. Run an **offline preview**, inspect every mapping and site:

   ```powershell
   python scripts/migrate_admins.py --preview
   ```

8. Import **one restricted test account**, log in separately and confirm that it can administer only the intended sites:

   ```powershell
   python scripts/migrate_admins.py --user some-new-username
   ```

9. After the test, run in **small batches** or import the remainder, *after manually checking People for existing usernames*:

   ```powershell
   python scripts/migrate_admins.py --all --limit 3
   python scripts/migrate_admins.py --all
   ```

10. Configure system-level Super Admins via the UI, validate accounts and permission boundaries, then create a **fresh UniFi OS system backup and VM snapshot/backup**.

## Required input columns

Use sheet `Administrators` (the first worksheet), with headers:

`username | first_name | last_name | email | site_count | password | legacy_username | mode`

- `username`: **new** login name; case-insensitive uniqueness.
- `legacy_username`: **old** login name in the legacy export. Required when a user is renamed; do not guess based on site count.
- `site_count`: expected number of positive per-site Network privileges (`admin` or `readonly`), optional but strongly recommended.
- `password`: **new password** (>=12 characters) for imported accounts. Keep only on the admin PC. No reuse of legacy hashes.
- `mode`: `import` for new local-only per-site accounts; `manual` for platform Super Admins / other out-of-band accounts.

**Never publish actual workbooks, `.jsonl` exports, `import_state.json`, secrets, browser profiles, HAR captures, certificates or backups.** The included `.xlsx` is fictional and has no passwords.

## Critical constraints

- Site IDs are required to match the target controller. If a Site Export/other migration has assigned new IDs, **stop**. Do not transfer rights by guessing names.
- A legacy `nobody` privilege is **not** emitted in the new role. The `super` pseudo-site is also excluded.
- The tool sends the same **observed** API fields as the private-role and local-user creation UI in the tested build. Its `POST` requests can create a private role with no user if the second call fails.
- Accounts that already exist in People must **not** be recreated. The state file prevents accidental resends from this tool but **cannot detect all accounts created manually**.
- The `import_state.json` file records a checkpoint **before** every POST and does not store passwords; never delete it to force a retry without manually reconciling the prior attempt.
- Success means the API accepted the request; **confirm effective access in a separate browser session**.
- Valid TLS is required by default. No hard-coded target IP/domain, usernames, customer data or credentials are included in the tool.

## Documentation

- [Slovenska navodila](README_SL.md)
- [Architecture and API boundaries](docs/ARCHITECTURE.md)
- [Troubleshooting and rollback](docs/TROUBLESHOOTING.md)
- [Security and publication checklist](SECURITY.md)

## Official references

- [Self-Hosting UniFi](https://help.ui.com/hc/en-us/articles/34210126298775-Self-Hosting-UniFi)
- [Backups and Migration in UniFi](https://help.ui.com/hc/en-us/articles/360008976393-Backups-and-Migration-in-UniFi)
- [Adding Admins in UniFi](https://help.ui.com/hc/en-us/articles/28692158912279-Adding-Admins-in-UniFi)
- [UniFi Roles Explained](https://help.ui.com/hc/en-us/articles/1500011491541-UniFi-Roles-Explained-Admins-and-Users)
- [Required Ports Reference](https://help.ui.com/hc/en-us/articles/218506997-Required-Ports-Reference)
- [Getting Started with the Official UniFi API](https://help.ui.com/hc/en-us/articles/30076656117655-Getting-Started-with-the-Official-UniFi-API)

**License:** MIT for this original toolkit code/docs only. UniFi and Ubiquiti are third-party trademarks. No vendor code, API tokens or proprietary source bundles are included.
