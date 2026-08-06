"use strict";
const fs = require("fs");
const path = require("path");
const test = require("node:test");
const assert = require("node:assert/strict");
const source = fs.readFileSync(path.join(__dirname, "..", "main.js"), "utf8");
const manager = fs.readFileSync(path.join(__dirname, "..", "lib", "host-manager.js"), "utf8");
const pkg = JSON.parse(fs.readFileSync(path.join(__dirname, "..", "package.json"), "utf8"));

test("desktop package includes its local host", () => {
  assert.equal(pkg.version, "3.0.0"); assert.equal(pkg.build.extraResources[0].to, "host/pocket-host.exe");
  assert.match(source, /--edge/); assert.match(source, /--cloud/); assert.match(source, /--background/);
});
test("lifecycle refuses automatic process killing", () => {
  assert.doesNotMatch(source + manager, /taskkill|Stop-Process|process\.kill/); assert.match(manager, /will not kill or replace/);
});
test("paired cloud work uses a restricted API key", () => {
  assert.match(source, /ensureCloudDeviceApiKey/); assert.match(source, /localJson\("\/v1\/ai\/chat"[\s\S]*?apiKey/);
});
