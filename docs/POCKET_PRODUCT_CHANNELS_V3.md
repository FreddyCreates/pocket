# POCKET Product Channels v3

POCKET ships as three coordinated but independently available product channels.

## POCKET Desktop

A normal Windows application distributed as x64 and ARM64 installers and portable executables.

- Electron user interface.
- Bundled PyInstaller `pocket-host.exe` local engine.
- Local engine binds to `127.0.0.1:8787`.
- Closing the window defaults to tray behavior.
- Optional start-at-login keeps the local engine and paired-device relay available.
- A healthy existing engine is reused. POCKET never kills an unknown listener or blindly restarts a healthy process.

The packaged application does not require a repository checkout or separately installed Python interpreter.

## POCKET Cloud Account

A Cloudflare Worker with static assets, D1 account state, and R2 release custody.

- Accounts and password-derived credentials.
- Organizations and role-based memberships.
- Invite-based multi-user onboarding.
- Device pairing and heartbeat.
- Cloud task queue for paired local computers.
- Entitlement-gated desktop downloads.
- Persistent account state independent of the operator's Windows machine.

This replaces the assumption that a Cloudflare Tunnel to `127.0.0.1:8787` is the hosted product. Existing tunnel work may remain during migration, but the account Worker is validated independently before DNS cutover.

## POCKET Edge App

A launcher mode for people who prefer the existing Edge experience.

- Starts or reuses the packaged loopback engine.
- Opens Microsoft Edge with `--app=http://127.0.0.1:8787/desk`.
- Uses the same local state and capabilities as Electron.
- Does not require a developer or assistant to start the server manually.

## Account-to-desktop flow

1. A user creates or joins an organization in POCKET Cloud.
2. The account produces a ten-minute pair code.
3. The user pastes the code into POCKET Desktop.
4. Desktop stores the device credential using Electron `safeStorage` when available.
5. Desktop creates a restricted local `sk_pocket_*` API key.
6. Cloud queues a chat or agent task.
7. The paired desktop claims it and executes against the local POCKET API.
8. The result returns to the cloud account.

The cloud never receives the founder's local owner session or unrestricted desktop-control credential.

## Current truth boundaries

- Worker source and a deployment workflow do not prove a live deployment.
- Desktop packaging source does not prove a downloadable binary until the Windows workflow produces and hashes it.
- Payment-provider webhooks are not included in this release. Entitlements are operator-managed through the protected release-administrator API and can later be driven by billing webhooks.
- The existing local multi-user system remains available inside the local engine. Cloud multi-user state lives in D1 and does not share local JSON files.
