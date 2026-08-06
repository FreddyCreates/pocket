"use strict";
const fs = require("fs");
const path = require("path");
const test = require("node:test");
const assert = require("node:assert/strict");

test("PyInstaller entry calls the existing two-argument serve contract", () => {
  const source = fs.readFileSync(path.join(__dirname, "..", "host", "entry.py"), "utf8");
  assert.match(source, /serve\(host=args\.host, port=args\.port\)/); assert.doesNotMatch(source, /state_dir=/);
});
test("host build collects dynamic pocket modules", () => {
  const source = fs.readFileSync(path.join(__dirname, "..", "scripts", "Build-Host.ps1"), "utf8"); assert.match(source, /--collect-all pocket/);
});
