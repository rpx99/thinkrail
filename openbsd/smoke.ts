import assert from "node:assert/strict";
import { mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { spawn } from "bun-pty";

const calls: number[] = [];
queueMicrotask(function () {
	calls.push(arguments.length);
});
await new Promise((resolve) => setTimeout(resolve, 10));
assert.deepEqual(calls, [0]);

const directory = mkdtempSync(join(tmpdir(), "thinkrail-openbsd-runtime-"));
const file = join(directory, "probe.txt");
writeFileSync(file, "openbsd-file-response");
const server = Bun.serve({
	hostname: "127.0.0.1",
	port: 0,
	fetch: () => new Response(Bun.file(file)),
});
try {
	const response = await fetch(server.url, { signal: AbortSignal.timeout(3000) });
	assert.ok(response instanceof Response);
	assert.ok(Response.json({ ok: true }) instanceof Response);
	assert.match(response.headers.get("Content-Type") ?? "", /text\/plain/);
	assert.equal(await response.text(), "openbsd-file-response");
} finally {
	server.stop(true);
	rmSync(directory, { recursive: true });
}

await new Promise<void>((resolve, reject) => {
	const terminal = spawn("/bin/sh", ["-c", "printf OPENBSD_PTY_OK"], {
		env: { PATH: "/usr/local/bin:/usr/bin:/bin" },
	});
	let output = "";
	const timer = setTimeout(() => {
		reject(new Error("PTY output timed out"));
		terminal.kill();
	}, 3000);
	terminal.onData((data) => { output += data; });
	terminal.onExit((event) => {
		clearTimeout(timer);
		try {
			assert.equal(event.exitCode, 0);
			assert.equal(output, "OPENBSD_PTY_OK");
			resolve();
		} catch (error) {
			reject(error);
		}
	});
});
console.log("PASS: microtasks, file HTTP response, Response identity and native PTY");
