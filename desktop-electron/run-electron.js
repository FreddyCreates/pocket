"use strict";
const { spawn } = require("child_process");
const fs = require("fs");
const path = require("path");
const root = __dirname;
const env = { ...process.env }; delete env.ELECTRON_RUN_AS_NODE; env.POCKET_ROOT ||= path.resolve(root, "..");
let bin = path.join(root, "node_modules", "electron", "dist", process.platform === "win32" ? "electron.exe" : "electron");
if (!fs.existsSync(bin)) { try { bin = require("electron"); } catch (_) {} }
if (!bin || !fs.existsSync(bin)) { console.error("Missing Electron. Run npm install in desktop-electron."); process.exit(1); }
const child = spawn(bin, [".", ...process.argv.slice(2)], { cwd: root, env, stdio: "inherit", shell: false });
child.on("error", (error) => { console.error(error); process.exit(1); });
child.on("exit", (code) => process.exit(code ?? 0));
