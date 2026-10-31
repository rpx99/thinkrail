---
id: tooling-openbsd
type: module-design
status: active
title: Local OpenBSD browser-host preparation
parent: architecture
---

## Responsibility

Prepare a user-local OpenBSD amd64 runtime and build the unchanged browser host.
The public commands are `python3 openbsd/prepare.py` and `openbsd/run`.

## Boundary

Owns downloaded build tools, native bun-pty compilation, launch environment and
compatibility corrections for the pinned unofficial Bun executable. Imports no
application internals and changes no application packages or dependency lockfiles.
Generated dependency bindings remain in ignored `node_modules`; downloaded or
compiled libraries are never committed. The normal CLI boots pi in-process.

The preload restores queueMicrotask callbacks and streams BunFile responses to
avoid two demonstrated failures in this Bun build. It applies only on OpenBSD.
Remove it, the loader aliases and the older executable when a current native Bun
passes these probes without them. This remains experimental, not a declaration
of upstream platform support. Live provider sign-in is a separate user step.
