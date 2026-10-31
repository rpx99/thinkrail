# Local validation, 2026-10-31

Source: upstream main `8992d802dc2100483b1ede8a2bd828222b4cd14c`.
System: OpenBSD 8.0 amd64, Node 24.22.1, Rust 1.99.1, Firefox 158.0.1.

Passed:

- Preparation from the pinned bundle and a fresh bun-pty checkout, including
  native release compilation, frozen dependency installation, web TypeScript
  checking and a production web build through Node/WASM.
- Runtime probes for microtask execution, file-backed HTTP responses, preserved
  Response instance checks and native PTY output/exit.
- A fresh HOME/config/data/pi directory using the installed launcher: HTTP
  health, WebSocket protocol 102, project registration, git-worktree creation,
  Lisp file reading, terminal input/output/resize and SBCL/ASDF returning
  `OPENBSD_LISP_OK=42`.
- Native Firefox through its Marionette interface: compiled UI connects, the
  project expands, the worktree opens and its terminal renders a shell prompt.
  A 1440px desktop and a 500px narrow window were inspected. This was not a
  physical-phone test or a complete mobile acceptance test.
- Shell/Python syntax, standalone preload TypeScript checking and whitespace.
- Dependency catalog, module boundaries and the 23 enrolled upstream spec surfaces.
- Repeated preparation replaces runtime/library files atomically; the already
  running disposable host remained healthy during the update.

The complete no-agent suite was invoked with its built web output and fail-fast
enabled. It stopped before test collection with Playwright's
`Error: Unsupported platform: openbsd`. No assertions were weakened or tests
reported as passing because of that failure. The ordinary upstream browser/CI
matrix remains unverified locally.

No real provider sign-in, paid agent request, external deployment or Electrobun
desktop launch was performed. Tests used disposable project/home/pi state and
did not open or modify the user's existing projects or agent sessions.

Local command logs and screenshots are retained under
`~/.cache/thinkrail-openbsd-probe-20261031/`, including `prepare-install.log`,
`installed-rpc-smoke.log`, `browser-workspace.log`, `e2e-no-agent.log` and the
desktop/narrow-window PNG files. They are not committed.
