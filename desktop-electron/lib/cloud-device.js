"use strict";

const fs = require("fs");
const os = require("os");
const path = require("path");

function normalizeCloudUrl(raw) {
  const url = new URL(String(raw || ""));
  if (url.protocol !== "https:") throw new Error("POCKET cloud account URLs must use HTTPS.");
  url.username = ""; url.password = ""; url.hash = "";
  return url.origin;
}

class CloudDevice {
  constructor(options = {}) {
    this.baseUrl = normalizeCloudUrl(options.baseUrl);
    this.storagePath = options.storagePath || path.join(os.homedir(), ".pocket", "cloud-device.json");
    this.safeStorage = options.safeStorage || null;
    this.fetchFn = options.fetchFn || globalThis.fetch;
    this.version = String(options.version || "");
    this.platform = String(options.platform || process.platform);
    this.pollIntervalMs = Math.max(3000, Number(options.pollIntervalMs || 5000));
    this.heartbeatIntervalMs = Math.max(15000, Number(options.heartbeatIntervalMs || 30000));
    this.timer = null; this.executor = null; this.lastHeartbeat = 0; this.lastTask = null; this.lastError = null;
  }
  read() { try { return JSON.parse(fs.readFileSync(this.storagePath, "utf8")); } catch (_) { return null; } }
  write(value) {
    fs.mkdirSync(path.dirname(this.storagePath), { recursive: true });
    const tmp = `${this.storagePath}.tmp`;
    fs.writeFileSync(tmp, JSON.stringify(value, null, 2), { encoding: "utf8", mode: 0o600 });
    fs.renameSync(tmp, this.storagePath); try { fs.chmodSync(this.storagePath, 0o600); } catch (_) {}
  }
  protect(secret) {
    if (this.safeStorage?.isEncryptionAvailable?.()) return { scheme: "electron-safe-storage", value: this.safeStorage.encryptString(secret).toString("base64") };
    if (process.env.POCKET_ALLOW_INSECURE_DEVICE_SECRET === "1") return { scheme: "plaintext-development-only", value: secret };
    throw new Error("Operating-system credential encryption is unavailable. The device secret was not stored.");
  }
  unprotect(record) {
    if (!record) return "";
    if (record.scheme === "electron-safe-storage" && this.safeStorage?.isEncryptionAvailable?.()) return this.safeStorage.decryptString(Buffer.from(record.value, "base64"));
    if (record.scheme === "plaintext-development-only" && process.env.POCKET_ALLOW_INSECURE_DEVICE_SECRET === "1") return record.value;
    return "";
  }
  credential() { return this.unprotect(this.read()?.credential); }
  localApiKey() { return this.unprotect(this.read()?.localApiKey); }
  setLocalApiKey(raw) {
    if (!String(raw || "").startsWith("sk_pocket_")) throw new Error("The local POCKET API key was not issued correctly.");
    const record = this.read(); if (!record) throw new Error("Pair the device before storing its local API key.");
    record.localApiKey = this.protect(String(raw)); record.localApiKeyConfiguredAt = new Date().toISOString(); this.write(record);
  }
  async request(pathname, options = {}) {
    if (typeof this.fetchFn !== "function") throw new Error("Fetch is unavailable in the desktop runtime.");
    const controller = new AbortController(); const timer = setTimeout(() => controller.abort(), Number(options.timeoutMs || 30000));
    try {
      const response = await this.fetchFn(this.baseUrl + pathname, {
        method: options.method || "GET",
        headers: { ...(options.body ? { "content-type": "application/json" } : {}), ...(options.credential ? { authorization: `Bearer ${options.credential}` } : {}), ...(options.headers || {}) },
        body: options.body ? JSON.stringify(options.body) : undefined, signal: controller.signal,
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(data.error?.message || data.error || `POCKET cloud HTTP ${response.status}`);
      return data;
    } finally { clearTimeout(timer); }
  }
  async pair(pairCode, options = {}) {
    const data = await this.request("/api/devices/pair", { method: "POST", body: { pair_code: String(pairCode || "").trim(), name: String(options.name || os.hostname() || "POCKET Desktop").slice(0, 80), platform: this.platform, version: this.version } });
    if (!data.device_secret) throw new Error("Cloud pairing did not return a device credential.");
    this.write({ schema: "pocket.desktop.cloud-device.v1", baseUrl: this.baseUrl, device: data.device, credential: this.protect(data.device_secret), pairedAt: new Date().toISOString() });
    return { ok: true, device: data.device, baseUrl: this.baseUrl };
  }
  unpair() { this.stop(); try { fs.unlinkSync(this.storagePath); } catch (_) {} return { ok: true }; }
  status() {
    const record = this.read();
    return { paired: Boolean(record && this.credential()), baseUrl: this.baseUrl, device: record?.device || null, running: Boolean(this.timer), lastHeartbeat: this.lastHeartbeat || null, lastTask: this.lastTask, lastError: this.lastError, credentialStorage: record?.credential?.scheme || null, localApiKeyConfigured: Boolean(this.localApiKey()) };
  }
  start(executor) {
    this.executor = executor; if (!this.credential() || this.timer) return this.status();
    const tick = () => this.tick().catch((error) => { this.lastError = String(error.message || error); });
    this.timer = setInterval(tick, this.pollIntervalMs); this.timer.unref?.(); void tick(); return this.status();
  }
  stop() { if (this.timer) clearInterval(this.timer); this.timer = null; }
  async tick() {
    const credential = this.credential(); if (!credential || !this.executor) return;
    const stamp = Date.now();
    if (stamp - this.lastHeartbeat >= this.heartbeatIntervalMs) {
      await this.request("/api/devices/heartbeat", { method: "POST", credential, body: { version: this.version } }); this.lastHeartbeat = stamp;
    }
    const next = await this.request("/api/device/tasks/next", { credential, timeoutMs: 20000 }); if (!next.task) return;
    this.lastTask = { id: next.task.id, kind: next.task.kind, status: "running", at: new Date().toISOString() };
    try {
      const result = await this.executor(next.task);
      await this.request(`/api/device/tasks/${encodeURIComponent(next.task.id)}/complete`, { method: "POST", credential, body: { ok: true, result }, timeoutMs: 120000 });
      this.lastTask = { ...this.lastTask, status: "completed" }; this.lastError = null;
    } catch (error) {
      await this.request(`/api/device/tasks/${encodeURIComponent(next.task.id)}/complete`, { method: "POST", credential, body: { ok: false, error: String(error.message || error).slice(0, 1000) } }).catch(() => {});
      this.lastTask = { ...this.lastTask, status: "failed" }; this.lastError = String(error.message || error);
    }
  }
}

module.exports = { CloudDevice, normalizeCloudUrl };
