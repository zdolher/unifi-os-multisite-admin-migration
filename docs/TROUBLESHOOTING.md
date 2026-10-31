# Troubleshooting and rollback (read before production use)

| Symptom | Meaning and safe action |
|---|---|
| `GET` returns 200, `POST` returns 403 | In the tested build the POST needed `X-CSRF-Token`. Do not repeat requests blindly; check logged-in owner, URL, permissions and that the test build's API behavior still applies. |
| No CSRF token found | Stop without modifying the target. Ensure that the browser logged in locally and loaded the People UI. Avoid sharing token/cookies. |
| `Missing target site ID` | Old and new site IDs differ or sites were not restored. **Stop**; manually investigate mapping, do not grant access based on site names alone. |
| `Site ID matches but internal name differs` | Potential wrong target or changed site record; **stop**, reconcile safely. |
| Existing username already in People | Remove the row from a *working copy* of Excel only after confirming the already-created user's rights. Do not recreate or overwrite the user. |
| POST role succeeded, POST user failed | An unassigned private role may remain. Save the UUID and manually inspect People/roles. Do not run again as-is. |
| Network timeout or browser crash | `import_state.json` stores uncertainty. Inspect People and state; do not delete the state file or try an automatic re-POST. |
| API says `SUCCESS` but account cannot log in | Stop the batch, verify local-only account flag, identity linkage, exact role, and system version. Do not assume permissions are effective. |
| Account sees extra sites | Treat as a serious access-control mismatch. Disable/remove the test account via UI and review all mappings; don't continue. |
| Previous legacy password does not work | Legacy password hash is not migrated by this tool. Generate a fresh new password in the protected workbook. |

## Rollback strategy

- **Before migration:** VM backup/snapshot and application backup, plus list of DNS/NAT/inform ports and existing admins.
- **During staged migration:** one active production controller; record changes to guest portal and HTTPS interface.
- **If the new server is not viable:** stop it, restore the old VM from a known-good backup, verify devices and old local logins, then decide whether to reschedule. Avoid running old and new simultaneously on the same inform endpoint.
- **For local admin import only:** removing created accounts through People may reverse the new identities, but does not replace a complete VM rollback plan. Beware of private roles left orphaned by partial failures; remove them through the UI after careful confirmation.

Do not attempt to "fix" permission propagation by updating MongoDB or PostgreSQL directly. That approach was observed to be insufficient and is not supported.
