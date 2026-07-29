/**
 * Zero-npm. Never opens npm.ps1 in Notepad.
 * node run-electron.js  →  dist/electron.exe .
 */
"use strict";
const { spawn } = require("child_process");
const path = require("path");
const fs = require("fs");

const root = __dirname;
const electronExe = path.join(root, "node_modules", "electron", "dist", "electron.exe");
const electronCmd = path.join(root, "node_modules", ".bin", "electron.cmd");

const env = { ...process.env };
delete env.ELECTRON_RUN_AS_NODE;
env.POCKET_URL = env.POCKET_URL || "http://127.0.0.1:8787/";
env.POCKET_ROOT = env.POCKET_ROOT || path.resolve(root, "..");

let bin = electronExe;
if (!fs.existsSync(bin)) {
  try {
    const p = require(path.join(root, "node_modules", "electron"));
    if (typeof p === "string" && fs.existsSync(p)) bin = p;
  } catch (_) {}
}
if (!fs.existsSync(bin) && fs.existsSync(electronCmd)) bin = electronCmd;
if (!fs.existsSync(bin)) {
  console.error("Missing electron binary. In CMD only:");
  console.error('  cd desktop-electron && npm.cmd install');
  process.exit(1);
}

const child = spawn(bin, ["."], {
  cwd: root,
  env,
  stdio: "inherit",
  shell: false,
  windowsHide: false,
});
child.on("error", (e) => {
  console.error(e);
  process.exit(1);
});
child.on("exit", (c) => process.exit(c == null ? 0 : c));
