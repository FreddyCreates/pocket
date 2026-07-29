/**
 * POCKET — preload bridge (minimal, context-isolated, sandboxed)
 *
 * Exposes a tiny read-only API. No Node fs/child_process/shell access.
 */
const { contextBridge } = require("electron");

contextBridge.exposeInMainWorld("pocket", {
  platform: process.platform,
  /** App shell identity (renderer may show version badge). */
  shell: "electron",
  version: "2.0.1",
});
