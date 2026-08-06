/**
 * User-facing client bridge only — no secrets, no fs, no shell.
 */
const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("pocket", {
  platform: process.platform,
  shell: "electron",
  version: "2.1.0",
});

contextBridge.exposeInMainWorld("pocketClient", {
  getConfig: () => ipcRenderer.invoke("pocket:getConfig"),
  getDefaults: () => ipcRenderer.invoke("pocket:defaults"),
  completeOnboarding: (payload) =>
    ipcRenderer.invoke("pocket:completeOnboarding", payload || {}),
});
