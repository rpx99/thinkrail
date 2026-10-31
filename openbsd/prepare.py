#!/usr/bin/env python3
import hashlib
import json
import os
from pathlib import Path
import platform
import shlex
import shutil
import subprocess
import tarfile

SOURCE = Path(__file__).resolve().parent.parent
HOME_DIR = Path.home()
CACHE = Path(os.environ.get("XDG_CACHE_HOME", HOME_DIR / ".cache")) / "thinkrail-openbsd"
RUNTIME = Path(os.environ.get("THINKRAIL_OPENBSD_RUNTIME", HOME_DIR / ".local/libexec/thinkrail-openbsd"))
BUNDLE = "opencode-openbsd-amd64-0.0.1-main.tgz"
BUNDLE_SHA256 = "71a2a737db9ad974b8ef758ecf4310576656ca953aeeaf210ba459c1c0645320"
PTY_REVISION = "14ac2cabec8484d0f02234ef300b2b46c4b908fe"
TOOLS = CACHE / "build-tools"


def run(*args, cwd=SOURCE, env=None):
    print("+", shlex.join(map(str, args)), flush=True)
    subprocess.run(list(map(str, args)), cwd=cwd, env=env, check=True)


def link(target, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_symlink():
        if path.resolve() == target.resolve():
            return
        path.unlink()
    elif path.exists():
        raise RuntimeError(f"Refusing to replace {path}")
    path.symlink_to(target, target_is_directory=target.is_dir())


def latest_library(stem):
    files = list(Path("/usr/lib").glob(stem + ".so.*"))
    return max(files, key=lambda p: tuple(map(int, p.name.split(".so.")[1].split("."))))


def main():
    if platform.system() != "OpenBSD" or platform.machine() != "amd64":
        raise RuntimeError("This experimental preparation targets OpenBSD amd64")
    for name in ["gh", "git", "cargo", "rustc", "node", "npm"]:
        if not shutil.which(name):
            raise RuntimeError(f"Missing prerequisite: {name}")
    if not Path("/usr/local/share/icu/77.1/icudt77l.dat").is_file():
        raise RuntimeError("Install the matching ICU 77.1 data first; see openbsd/README.md")
    marker = RUNTIME / "installation.json"
    if RUNTIME.exists() and any(RUNTIME.iterdir()) and not marker.exists():
        raise RuntimeError(f"Refusing to overwrite unmanaged runtime {RUNTIME}")
    launcher = HOME_DIR / ".local/bin/thinkrail"
    launcher_text = "#!/bin/sh\nexec " + shlex.quote(str(SOURCE / "openbsd/run")) + ' "$@"\n'
    if launcher.exists() and launcher.read_text() != launcher_text:
        raise RuntimeError(f"Refusing to replace existing launcher {launcher}")
    CACHE.mkdir(parents=True, exist_ok=True)
    (RUNTIME / "bin").mkdir(parents=True, exist_ok=True)
    marker.write_text(json.dumps({"source": str(SOURCE), "state": "preparing"}))
    archive = CACHE / BUNDLE
    if not archive.exists():
        run("gh", "release", "download", "openbsd-bundle-0.0.1-main", "--repo",
            "bstn-r3x/openbsd-opencode-port", "--pattern", BUNDLE, "--dir", CACHE)
    with archive.open("rb") as f:
        if hashlib.file_digest(f, "sha256").hexdigest() != BUNDLE_SHA256:
            raise RuntimeError("Bun bundle SHA256 mismatch")
    with tarfile.open(archive) as tar:
        member = next(m for m in tar.getmembers() if m.isfile() and m.name.endswith("/libexec/opencode/opencode-bin"))
        with tar.extractfile(member) as src, (RUNTIME / "bun-runtime.next").open("wb") as dst:
            shutil.copyfileobj(src, dst)
    (RUNTIME / "bun-runtime.next").chmod(0o755)
    (RUNTIME / "bun-runtime.next").replace(RUNTIME / "bun-runtime")
    for old, stem in [("libc.so.102.2", "libc"), ("libc++abi.so.9.0", "libc++abi")]:
        link(latest_library(stem), RUNTIME / "compat" / old)
    shutil.copyfile(SOURCE / "openbsd/preload.ts", RUNTIME / "preload.ts")
    wrapper = "\n".join([
        "#!/bin/sh", "set -eu", "runtime=" + shlex.quote(str(RUNTIME)),
        "export BUN_BE_BUN=1",
        'export LD_LIBRARY_PATH="$runtime/compat${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"',
        'export BUN_PTY_LIB="$runtime/librust_pty.so"',
        'case " ${BUN_OPTIONS-} " in',
        '  *" --preload=$runtime/preload.ts "*) ;;',
        '  *) export BUN_OPTIONS="${BUN_OPTIONS:+$BUN_OPTIONS }--preload=$runtime/preload.ts" ;;',
        "esac", 'exec "$runtime/bun-runtime" "$@"', "",
    ])
    (RUNTIME / "bin/bun").write_text(wrapper)
    (RUNTIME / "bin/bun").chmod(0o755)
    pty = CACHE / "bun-pty"
    if not pty.exists():
        run("git", "clone", "https://github.com/sursaone/bun-pty.git", pty)
        run("git", "checkout", "--detach", PTY_REVISION, cwd=pty)
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=pty, text=True).strip()
    dirty = subprocess.check_output(["git", "status", "--porcelain"], cwd=pty, text=True).strip()
    if revision != PTY_REVISION or dirty:
        raise RuntimeError(f"Expected a clean bun-pty checkout at {PTY_REVISION}")
    build_env = dict(os.environ, PATH="/usr/local/bin:/usr/bin:/bin", RUSTFMT="/usr/local/bin/rustfmt")
    run("cargo", "build", "--release", "--locked", "--manifest-path", pty / "rust-pty/Cargo.toml", env=build_env)
    shutil.copyfile(pty / "rust-pty/target/release/librust_pty.so", RUNTIME / "librust_pty.so.next")
    (RUNTIME / "librust_pty.so.next").replace(RUNTIME / "librust_pty.so")
    bun = RUNTIME / "bin/bun"
    bun_env = dict(os.environ, BUN_INSTALL_CACHE_DIR=str(CACHE / "bun-cache"))
    run(bun, "install", "--linker", "hoisted", "--backend", "hardlink", "--ignore-scripts", "--frozen-lockfile", env=bun_env)
    run("npm", "install", "--prefix", TOOLS, "--ignore-scripts", "--no-audit", "--no-fund", "--force", "--save-exact",
        "@rolldown/binding-wasm32-wasi@1.2.15", "rolldown-binding-v1@npm:@rolldown/binding-wasm32-wasi@1.1.5",
        "@tailwindcss/oxide-wasm32-wasi@4.3.3", "lightningcss-wasm@1.33.0", "lightningcss-wasm-v132@npm:lightningcss-wasm@1.32.0",
        "wasm-runtime-v125@npm:@napi-rs/wasm-runtime@1.2.5")
    tools = TOOLS / "node_modules"
    modules = SOURCE / "node_modules"
    for owner, package in [("@rolldown/binding-wasm32-wasi", "wasm-runtime-v125"), ("rolldown-binding-v1", "@napi-rs/wasm-runtime")]:
        destination = tools / owner / "node_modules/@napi-rs/wasm-runtime"
        if destination.exists():
            shutil.rmtree(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(tools / package, destination)
    for destination, package in [("@rolldown/binding-wasm32-wasi", "@rolldown/binding-wasm32-wasi"),
                                 ("vite/node_modules/@rolldown/binding-wasm32-wasi", "rolldown-binding-v1"),
                                 ("@tailwindcss/oxide-wasm32-wasi", "@tailwindcss/oxide-wasm32-wasi")]:
        link(tools / package, modules / destination)
    for package, wasm in [("lightningcss", "lightningcss-wasm"), ("@tailwindcss/node/node_modules/lightningcss", "lightningcss-wasm-v132")]:
        shim = modules / package / "node_modules/lightningcss-openbsd-x64"
        shim.mkdir(parents=True, exist_ok=True)
        (shim / "package.json").write_text(json.dumps({"name": "lightningcss-openbsd-x64", "main": "index.cjs", "private": True}))
        (shim / "index.cjs").write_text("module.exports = require(" + json.dumps(str(tools / wasm / "wasm-node.cjs")) + ");\n")
    run("node", modules / "typescript/bin/tsc", "--noEmit", "-p", "apps/web/tsconfig.json")
    web_env = dict(os.environ, NAPI_RS_FORCE_WASI="true", NAPI_RS_ENFORCE_VERSION_CHECK="1", NAPI_RS_ASYNC_WORK_POOL_SIZE="2", RAYON_NUM_THREADS="2")
    run("node", modules / "vite/bin/vite.js", "build", cwd=SOURCE / "apps/web", env=web_env)
    run(bun, SOURCE / "openbsd/smoke.ts")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=SOURCE, text=True).strip()
    marker.write_text(json.dumps({"source": str(SOURCE), "commit": commit, "bun": "1.3.10", "bunBundleSha256": BUNDLE_SHA256, "bunPtyCommit": PTY_REVISION}, indent=2) + "\n")
    launcher.parent.mkdir(parents=True, exist_ok=True)
    launcher.write_text(launcher_text)
    launcher.chmod(0o755)
    print("Installed:", launcher, flush=True)


if __name__ == "__main__":
    main()
