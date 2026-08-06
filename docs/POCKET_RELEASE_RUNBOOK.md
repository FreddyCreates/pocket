# POCKET v3 Release Runbook

## Gate A — source

- Electron syntax and unit tests pass.
- Worker syntax, unit tests, and Wrangler dry-run pass.
- PyInstaller entry compiles.
- Shipping lifecycle scripts contain no automatic process-kill behavior.

## Gate B — Windows artifacts

For x64 and ARM64:

- build `pocket-host.exe`;
- launch packaged host and receive `/health` = 200;
- package NSIS and portable executables;
- calculate SHA-256;
- upload workflow artifacts;
- install on a clean Windows user profile;
- verify Desktop and Start-menu shortcuts;
- verify `--local`, `--cloud`, `--edge`, and `--background`.

## Gate C — cloud

- D1 migrations applied;
- Worker deployed;
- first organization bootstrapped;
- owner login succeeds;
- invite creates a separate member account;
- member cannot administer another organization;
- pair code expires and is single-use;
- device secret cannot access account-only routes;
- queued task is leased once and recovers from an expired lease;
- release download requires entitlement;
- R2 object hash agrees with release metadata.

## Gate D — cutover

- existing tunnel remains untouched during validation;
- new account hostname resolves to Worker;
- clean browser and phone tests pass;
- Electron default cloud URL points to the validated hostname;
- rollback DNS is documented;
- only then retire the tunnel from the primary product hostname.

A source merge is not a live deployment, and a workflow definition is not a built installer.
