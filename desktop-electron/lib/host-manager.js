"use strict";

const fs = require("fs");
const http = require("http");
const net = require("net");
const os = require("os");
const path = require("path");
const { spawn } = require("child_process");

function sleep(ms) { return new Promise((resolve) => setTimeout(resolve, ms)); }

function probeHttp({ host, port, timeoutMs = 1800 }) {
  return new Promise((resolve) => {
    const req = http.get({ hostname: host, port, path: "/health", timeout: timeoutMs }, (res) => {
      res.resume();
      resolve({ reachable: true, healthy: res.statusCode === 200, status: res.statusCode || 0 });
    });
    req.on("timeout", () => { req.destroy(); resolve({ reachable: false, healthy: false, error: "timeout" }); });
    req.on("error", (error) => resolve({ reachable: false, healthy: false, error: error.code || error.message }));
  });
}

function portListening(host, port, timeoutMs = 750) {
  return new Promise((resolve) => {
    const socket = net.createConnection({ host, port });
    const finish = (value) => { socket.destroy(); resolve(value); };
    socket.setTimeout(timeoutMs);
    socket.once("connect", () => finish(true));
    socket.once("timeout", () => finish(false));
    socket.once("error", () => finish(false));
  });
}

class HostManager {
  constructor(options = {}) {
    this.host = options.host || "127.0.0.1";
    this.port = Number(options.port || 8787);
    this.baseUrl = `http://${this.host}:${this.port}`;
    this.resourcesPath = options.resourcesPath || process.resourcesPath || "";
    this.appRoot = options.appRoot || path.resolve(__dirname, "..", "..");
    this.userData = options.userData || path.join(os.homedir(), ".pocket");
    this.isPackaged = Boolean(options.isPackaged);
    this.spawnFn = options.spawnFn || spawn;
    this.probeFn = options.probeFn || (() => probeHttp({ host: this.host, port: this.port }));
    this.listenFn = options.listenFn || (() => portListening(this.host, this.port));
    this.starting = null;
    this.lastLaunch = null;
  }

  packagedHostPath() {
    const candidates = [
      path.join(this.resourcesPath, "host", "pocket-host.exe"),
      path.join(this.resourcesPath, "pocket-host.exe"),
      path.join(path.dirname(process.execPath || ""), "resources", "host", "pocket-host.exe"),
    ];
    return candidates.find((candidate) => candidate && fs.existsSync(candidate)) || "";
  }

  pythonPath() {
    const configured = String(process.env.POCKET_PYTHON || "").trim();
    if (configured) return configured;
    const candidates = process.platform === "win32"
      ? [
          path.join(process.env.LOCALAPPDATA || "", "Programs", "Python", "Python312", "python.exe"),
          path.join(process.env.LOCALAPPDATA || "", "Programs", "Python", "Python311-arm64", "python.exe"),
          path.join(process.env.LOCALAPPDATA || "", "Programs", "Python", "Python311", "python.exe"),
          "python.exe",
        ]
      : ["python3", "python"];
    return candidates.find((candidate) => !path.isAbsolute(candidate) || fs.existsSync(candidate)) || candidates.at(-1);
  }

  launchTarget() {
    const packaged = this.packagedHostPath();
    if (packaged) {
      return { command: packaged, args: ["--host", this.host, "--port", String(this.port)], cwd: this.userData, kind: "packaged-sidecar" };
    }
    const src = path.join(this.appRoot, "src");
    if (!fs.existsSync(path.join(src, "pocket"))) throw new Error("POCKET local engine is not installed. Use the cloud account or reinstall POCKET Desktop.");
    return {
      command: this.pythonPath(),
      args: ["-u", "-m", "pocket", "serve", "--host", this.host, "--port", String(this.port)],
      cwd: this.appRoot,
      kind: "source-checkout",
      env: { PYTHONPATH: src },
    };
  }

  async status() { const probe = await this.probeFn(); return { ...probe, baseUrl: this.baseUrl, lastLaunch: this.lastLaunch }; }
  async ensure(timeoutMs = 45000) {
    if (this.starting) return this.starting;
    this.starting = this._ensure(timeoutMs).finally(() => { this.starting = null; });
    return this.starting;
  }
  async _ensure(timeoutMs) {
    const current = await this.probeFn();
    if (current.healthy) return { ok: true, reused: true, baseUrl: this.baseUrl };
    if (await this.listenFn()) throw new Error(`Port ${this.port} is already occupied by a service that is not a healthy POCKET host. POCKET will not kill or replace that process automatically.`);
    fs.mkdirSync(this.userData, { recursive: true });
    const target = this.launchTarget();
    const env = {
      ...process.env, ...target.env, POCKET_PORT: String(this.port), POCKET_DESKTOP_MANAGED: "1",
      POCKET_MESH_HOOK: process.env.POCKET_MESH_HOOK || "0", POCKET_ALWAYS_MESH: process.env.POCKET_ALWAYS_MESH || "0",
      POCKET_HEADLESS_AUTO: process.env.POCKET_HEADLESS_AUTO || "0", POCKET_AURO_TRAIN: process.env.POCKET_AURO_TRAIN || "0",
    };
    const child = this.spawnFn(target.command, target.args, { cwd: target.cwd, env, detached: true, windowsHide: true, stdio: "ignore" });
    child.unref?.();
    this.lastLaunch = { kind: target.kind, pid: child.pid || null, at: new Date().toISOString() };
    const deadline = Date.now() + timeoutMs;
    while (Date.now() < deadline) {
      const probe = await this.probeFn();
      if (probe.healthy) return { ok: true, reused: false, baseUrl: this.baseUrl, launch: this.lastLaunch };
      await sleep(400);
    }
    throw new Error("POCKET local engine did not become healthy. Check ~/.pocket logs or use the cloud account channel.");
  }
}

module.exports = { HostManager, probeHttp, portListening, sleep };
