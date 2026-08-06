"use strict";
const { contextBridge, ipcRenderer } = require("electron");
contextBridge.exposeInMainWorld("pocket", {
  platform: process.platform,
  shell: "electron",
  getConfig: () => ipcRenderer.invoke("pocket:getConfig"),
  getInfo: () => ipcRenderer.invoke("pocket:getInfo"),
  openMode: (payload) => ipcRenderer.invoke("pocket:openMode", payload || {}),
  openEdge: () => ipcRenderer.invoke("pocket:openEdge"),
  hostStatus: () => ipcRenderer.invoke("pocket:hostStatus"),
  cloudDeviceStatus: () => ipcRenderer.invoke("pocket:cloudDeviceStatus"),
  pairDevice: (code) => ipcRenderer.invoke("pocket:pairDevice", code),
  unpairDevice: () => ipcRenderer.invoke("pocket:unpairDevice"),
  setStartAtLogin: (enabled) => ipcRenderer.invoke("pocket:setStartAtLogin", Boolean(enabled)),
  openExternal: (url) => ipcRenderer.invoke("pocket:openExternal", url),
});
