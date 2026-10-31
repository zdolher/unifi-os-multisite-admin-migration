# Architecture and observed internal API (October 2026)

## Two identity layers

Legacy UniFi Network Server kept user records with `x_shadow` and per-site privileges in MongoDB (`ace.admin`, `ace.privilege`). Restoring a Network backup into a UniFi OS Server can preserve old site and admin records without registering those accounts in the new UniFi OS identity system. The new local login identity is not recreated simply by copying legacy password hashes.

The tested UniFi OS Server build has a **separate identity/role service**, accessed by the People UI. Direct MongoDB updates proved inadequate in the field test: a modified privilege document was subsequently restored to its previous role. Therefore this toolkit **only reads** MongoDB on both sides and sends authorized HTTP requests to the application layer.

## Requests observed in the tested build

The official UI created a private Network role with:

```json
{
  "name": "role_private_1760000000",
  "is_private": true,
  "permissions": [
    {
      "manifest_unique_key": "network.management",
      "formulas": [
        "s-111111111111111111111111-admin",
        "s-222222222222222222222222-readonly"
      ]
    }
  ],
  "permission_resources": []
}
```

`POST /proxy/users/api/v2/custom_role` returned `data.unique_id`. The UI then supplied the same UUID as `role_id` in:

```json
{
  "first_name": "Alice",
  "last_name": "Example",
  "user_email": "alice@example.invalid",
  "force_add_nfc": true,
  "nfc_token": "",
  "group_ids": [],
  "pin_code": "",
  "role_id": "<UUID FROM CREATE ROLE RESPONSE>",
  "username": "alice-new",
  "password": "<SECRET ENTERED LOCALLY; NOT LOGGED>",
  "only_local_account": true
}
```

`POST /proxy/users/api/v2/user` created the account. The script runs both requests via a same-origin authenticated Chrome page and sends `X-CSRF-Token`, obtained from the local session. It does not export cookies or CSRF tokens.

**These paths are not documented as stable admin-creation APIs** in the official UniFi Network API documentation. Their presence does not constitute Ubiquiti support. Never publish real requests containing password, Authorization header, cookies, CSRF tokens, user IDs or site IDs from customers.

## State machine

For each account:

1. Save `role_post_uncertain` **before** trying to create role.
2. If confirmed, save `role_created` and UUID.
3. Save `user_post_uncertain` **before** trying to create account.
4. If confirmed, save `created_pending_manual_verification`.

On failure, STOP. Do not resend the same POST based on a network timeout. Review People and the saved state before deciding whether to reconcile orphan roles or users. State is written atomically and omits passwords.

## Limiting privilege scope

- Only legacy `admin` and `readonly` roles on actual site IDs become formulas.
- The `super` pseudo-site and `nobody` permissions never become positive grants.
- The target site's **ID and internal name** must match the legacy export; otherwise import is blocked.
- Platform Super Admin is different from a per-site Network Admin and is handled manually.
