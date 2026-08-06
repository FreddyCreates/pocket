"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const { HostManager } = require("../lib/host-manager");

test("reuses a healthy host without spawning", async () => {
  let spawned = 0;
  const manager = new HostManager({ probeFn: async () => ({ healthy: true }), listenFn: async () => true, spawnFn: () => { spawned += 1; throw new Error("must not spawn"); } });
  const result = await manager.ensure(); assert.equal(result.reused, true); assert.equal(spawned, 0);
});

test("refuses to kill or replace an unknown listener", async () => {
  const manager = new HostManager({ probeFn: async () => ({ healthy: false }), listenFn: async () => true });
  await assert.rejects(() => manager.ensure(), /will not kill or replace/);
});
