# Experimental OpenBSD browser host

This fork can build and run the browser host on OpenBSD 8.0 amd64. The source
checkout is based on upstream main `8992d802dc2100483b1ede8a2bd828222b4cd14c`
(2026-10-31). The Electrobun desktop application is not ported.

## Prepare and launch

Install Python 3, Git, GitHub CLI, Node.js >= 22.19, Rust/Cargo and a browser.
The experimental Bun executable also needs the official ICU 77.1 data file at
`/usr/local/share/icu/77.1/icudt77l.dat`. It is available in Unicode's
[ICU 77.1 data archive](https://github.com/unicode-org/icu/releases/download/release-77-1/icu4c-77_1-data-bin-l.zip).
Extract `icudt77l.dat` and install that file with `doas install -d` / `doas install`;
do not replace the system's current ICU libraries.

```sh
python3 openbsd/prepare.py
~/.local/bin/thinkrail
```

The preparation downloads a checksum-pinned unofficial Bun executable from
[the OpenCode OpenBSD bundle](https://github.com/bstn-r3x/openbsd-opencode-port/releases/tag/openbsd-bundle-0.0.1-main),
builds bun-pty 0.5.1 natively, installs the locked workspace dependencies, and
builds the current web source through Node and version-matched WASM bindings.
No Linux executable is used. Libraries and generated dependency shims stay
outside tracked source. The application's normal CLI and in-process pi are used.

The installed launcher lives under `~/.local/bin`; its runtime is under
`~/.local/libexec/thinkrail-openbsd`. Build caches live under
`~/.cache/thinkrail-openbsd`. Re-run preparation after updating the source.
Application state keeps the normal `~/.thinkrail` and pi locations; sign in to a
provider through Settings. `thinkrail --no-open --port 24242` runs without opening
a browser. Keep the default loopback binding for local use.

## Compatibility limits

- This uses unofficial Bun 1.3.10, older than upstream's pinned 1.4.4.
- The executable's old libc/libc++abi dependencies are redirected through a
  private loader directory to the installed libraries. This is experimental ABI
  compatibility, not a supported Bun build for current OpenBSD. It changes no
  system libraries or global loader configuration.
- The preload corrects a nonfunctional `queueMicrotask` and avoids the broken
  BunFile HTTP fast path by streaming the same file body and preserving its type.
- These workarounds must be removed after equivalent native Bun fixes; successful
  smoke tests do not establish compatibility with every Bun or pi feature.
- The standard no-agent Playwright suite and real provider interactions are
  separate acceptance gates. See the [validation report](validation.md) for actual results.
- Browser access works independently of Electrobun. The complete mobile shell
  and PWA are still future work in upstream's web spec. A remote deployment needs
  authenticated access; Hetzner installation is outside this local setup.

## Validation

On OpenBSD 8.0 amd64, the current web production build and web TypeScript check
passed. A disposable host/home/pi directory completed HTTP and WebSocket requests,
project/worktree creation, Lisp source reading, PTY input/output and resize, and
SBCL/ASDF execution returning `OPENBSD_LISP_OK=42`. Native Firefox rendered the
compiled UI and connected to the host. No provider credentials or paid agent
requests were used for these checks.
