import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

test("publishes an observable non-visual release marker", () => {
  const html = readFileSync(new URL("../index.html", import.meta.url), "utf8");
  assert.match(html, /<meta name="ampersand-release" content="edit-core-v0" \/>/);
});
