# POCKET Cloud Account

`cloudflare/pocket-cloud` is the independent multi-user account and distribution plane.

## Resources

- Cloudflare Worker and Static Assets
- D1 binding: `DB`
- R2 binding: `DOWNLOADS`
- Secrets: `BOOTSTRAP_TOKEN`, `RELEASE_ADMIN_TOKEN`

## Provision once

```powershell
wrangler d1 create pocket-cloud
wrangler r2 bucket create pocket-desktop-releases
wrangler r2 bucket create pocket-desktop-releases-preview
wrangler secret put BOOTSTRAP_TOKEN
wrangler secret put RELEASE_ADMIN_TOKEN
```

Then deploy:

```powershell
$env:POCKET_D1_DATABASE_ID = "..."
.\scripts\Deploy-POCKET-Cloud.ps1
```

## Safe migration from the existing tunnel

Do not delete the named tunnel or change production DNS first.

1. Deploy the Worker to its preview or workers.dev address.
2. Bootstrap the first organization.
3. Test login, invitations, organization isolation, pair codes, device heartbeat, task completion, and downloads.
4. Build and upload hash-addressed desktop artifacts to R2.
5. Test an entitlement-gated download.
6. Add a new hostname such as `app.pocket.medinatechlabs.net`.
7. Move the primary POCKET hostname only after clean-browser and phone validation.
8. Retain rollback DNS and the original tunnel configuration until receipts are captured.

## Release registration

Upload an executable to R2, then register it through the protected endpoint:

```http
POST /api/admin/releases
Authorization: Bearer <RELEASE_ADMIN_TOKEN>
Content-Type: application/json

{
  "id": "pocket-3.0.0-x64",
  "version": "3.0.0",
  "arch": "x64",
  "object_key": "desktop/3.0.0/POCKET-Desktop-3.0.0-x64.exe",
  "sha256": "...",
  "bytes": 123
}
```

Grant access through `/api/admin/entitlements`. A future billing webhook should update the same entitlement table instead of introducing a second authorization model.
