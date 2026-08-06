# POCKET user release model

POCKET ships as three coordinated product channels. They share an account and product identity, but they do not share one fragile process lifecycle.

## 1. POCKET Cloud account

The Cloudflare application is the always-on account, organization, entitlement, release, and device-coordination plane.

It must remain available when every customer computer is powered off. It must not proxy its health through `localhost`, an operator terminal, a Cloudflare Tunnel process, or the Electron application.

The cloud account owns:

- account registration and sign-in;
- organization membership and roles;
- team invites;
- product entitlements;
- R2 release downloads;
- device pairing;
- queued device tasks and durable task state;
- release metadata and update notices.

Local execution is represented as an optional paired device. An offline device makes a local task unavailable; it does not make the cloud account unavailable.

## 2. POCKET Desktop

POCKET Desktop is an install-once Electron application. The Windows installer contains a packaged `pocket-host.exe`, so a customer does not need Python, a source checkout, a terminal, or an operator to start the local product.

Opening the normal **POCKET** shortcut:

1. checks `127.0.0.1:8787/health`;
2. reuses a healthy POCKET host;
3. refuses to kill or replace an unknown process using the port;
4. starts the packaged sidecar only when POCKET is not already healthy;
5. opens the selected local or cloud surface;
6. keeps the tray available for reopening the product.

The installer also creates explicit shortcuts:

- **POCKET Local** — packaged local engine and Electron window;
- **POCKET Edge** — packaged local engine and Microsoft Edge app window;
- **POCKET Cloud** — always-on Cloudflare account.

## 3. POCKET Edge app

POCKET Edge is not a separately maintained server. It is an alternate shell for the same installed local engine.

The shortcut invokes:

```text
POCKET.exe --edge
```

POCKET verifies or starts the packaged local host, then launches Microsoft Edge with:

```text
--app=http://127.0.0.1:8787/desk
```

The user can therefore open the Edge experience from the Desktop or Start menu without running a script or asking an operator to start a server.

## 4. Account-to-device journey

The intended customer flow is:

```text
Public website
  -> account / checkout
  -> POCKET Cloud organization
  -> entitlement granted
  -> installer download from R2
  -> POCKET Desktop installed
  -> optional one-time pair code
  -> approved cloud work delegated to that device
```

Pairing stores the device credential through Electron `safeStorage` when the operating-system credential vault is available. The cloud never receives the founder's local owner session. The desktop creates and stores a restricted `sk_pocket_*` local key for delegated work.

## 5. Update model

POCKET is released like a normal software product:

1. source change enters a pull request;
2. the product gate validates desktop, cloud, tenancy, and lifecycle contracts;
3. Windows x64 and ARM64 workflows build the packaged host, installer, and portable application;
4. SHA-256 manifests are produced;
5. a version tag creates the GitHub release;
6. release files are copied to R2 and registered in the Cloud account;
7. entitled users download the new version from their account.

No user-facing release should depend on a developer keeping a terminal open.

## 6. Non-destructive lifecycle rule

Ordinary POCKET startup may never use `taskkill`, `Stop-Process`, or an equivalent broad process-kill operation. A healthy host is reused. A foreign listener causes a clear error. Explicit uninstall or operator recovery procedures remain separate from normal startup.

## Current evidence boundary

The repository contains the product source, packaging path, Cloudflare account plane, tests, and release workflows. A public launch still requires successful installer artifacts plus operator-owned Cloudflare resources and deployment receipts. Payment-provider webhook integration remains a separate release gate; entitlement administration is already represented in the cloud data model.
