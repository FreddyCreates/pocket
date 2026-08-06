"use strict";
const fs = require("fs");
const os = require("os");
const path = require("path");
const test = require("node:test");
const assert = require("node:assert/strict");
const { CloudDevice, normalizeCloudUrl } = require("../lib/cloud-device");

test("cloud account URL must use HTTPS", () => {
  assert.equal(normalizeCloudUrl("https://app.example.com/path"), "https://app.example.com");
  assert.throws(() => normalizeCloudUrl("http://app.example.com"), /HTTPS/);
});

test("pairing stores encrypted device credential", async () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "pocket-device-"));
  const safeStorage = { isEncryptionAvailable: () => true, encryptString: (value) => Buffer.from(`sealed:${value}`), decryptString: (buffer) => buffer.toString().replace(/^sealed:/, "") };
  const fetchFn = async () => new Response(JSON.stringify({ device_secret: "secret", device: { id: "dev_1" } }), { status: 200, headers: { "content-type": "application/json" } });
  const device = new CloudDevice({ baseUrl: "https://app.example.com", storagePath: path.join(dir, "device.json"), safeStorage, fetchFn });
  await device.pair("PAIR-CODE");
  const stored = JSON.parse(fs.readFileSync(path.join(dir, "device.json"), "utf8"));
  assert.equal(stored.credential.scheme, "electron-safe-storage"); assert.equal(device.credential(), "secret");
});
