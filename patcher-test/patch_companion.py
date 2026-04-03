#!/usr/bin/env python3
"""
Patch Claude Code to use a companion from the companions/ directory.

Replaces the salt in Claude Code's CLI and updates ~/.claude.json
with the companion's identity. No external dependencies required.

Usage:
    python3 patch_companion.py <companion-name>
    python3 patch_companion.py vyrenth
    python3 patch_companion.py thistlewing
    python3 patch_companion.py --list
    python3 patch_companion.py --restore

You can also set CLAUDE_BINARY=/path/to/cli.js to skip auto-detection.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

DEFAULT_SALT = "friend-2026-401"
SALT_LENGTH = 15
COMPANIONS_DIR = Path(__file__).resolve().parent.parent / "companions"
CLAUDE_CONFIG_PATHS = [
    Path.home() / ".claude.json",
    Path.home() / ".claude" / ".config.json",
]
PATCHER_STATE = Path(__file__).resolve().parent / ".patcher-state.json"

IS_MAC = platform.system() == "Darwin"
IS_WIN = platform.system() == "Windows"


# ── Binary finder ──


def _which(cmd: str) -> Optional[str]:
    """Find a command on PATH."""
    result = shutil.which(cmd)
    if result and os.path.exists(result):
        return result
    return None


def _resolve(p: str) -> str:
    """Resolve symlinks to get the real path."""
    return str(Path(p).resolve())


def _platform_candidates() -> list[str]:
    """Common Claude Code install locations per platform."""
    home = str(Path.home())

    if IS_WIN:
        appdata = os.environ.get("APPDATA", os.path.join(home, "AppData", "Roaming"))
        localappdata = os.environ.get(
            "LOCALAPPDATA", os.path.join(home, "AppData", "Local")
        )
        return [
            os.path.join(localappdata, "Programs", "claude", "claude.exe"),
            os.path.join(
                appdata, "npm", "node_modules",
                "@anthropic-ai", "claude-code", "cli.js",
            ),
            os.path.join(home, ".volta", "bin", "claude.exe"),
        ]

    if IS_MAC:
        return [
            os.path.join(home, ".local", "bin", "claude"),
            os.path.join(home, ".claude", "local", "claude"),
            "/usr/local/bin/claude",
            "/opt/homebrew/bin/claude",
            os.path.join(home, ".npm-global", "bin", "claude"),
            os.path.join(home, ".volta", "bin", "claude"),
        ]

    # Linux
    return [
        os.path.join(home, ".local", "bin", "claude"),
        "/usr/local/bin/claude",
        "/usr/bin/claude",
        os.path.join(home, ".npm-global", "bin", "claude"),
        os.path.join(home, ".volta", "bin", "claude"),
    ]


def _resolve_to_cli_js(binary_path: str) -> Optional[str]:
    """Given a claude binary path, find the actual cli.js file."""
    resolved = _resolve(binary_path)

    # Already a .js file
    if resolved.endswith(".js"):
        return resolved

    # Check for cli.js relative to the binary's package dir
    # Look for @anthropic-ai/claude-code in the path
    pkg_marker = os.path.join("@anthropic-ai", "claude-code")
    idx = resolved.find(pkg_marker)
    if idx != -1:
        pkg_dir = resolved[: idx + len(pkg_marker)]
        cli_candidate = os.path.join(pkg_dir, "cli.js")
        if os.path.exists(cli_candidate):
            return cli_candidate

    # Try standard node_modules layout relative to binary
    candidates = [
        os.path.join(
            os.path.dirname(os.path.dirname(resolved)),
            "lib", "node_modules", "@anthropic-ai", "claude-code", "cli.js",
        ),
        os.path.join(
            os.path.dirname(resolved),
            "node_modules", "@anthropic-ai", "claude-code", "cli.js",
        ),
    ]

    for candidate in candidates:
        if os.path.exists(candidate):
            return candidate

    # For compiled binaries, return the resolved path itself
    if os.path.exists(resolved) and os.path.getsize(resolved) >= 1_000_000:
        return resolved

    return None


def find_claude_binary() -> str:
    """Find the Claude Code binary/cli.js with multiple strategies."""
    # Strategy 1: CLAUDE_BINARY env var
    env_path = os.environ.get("CLAUDE_BINARY")
    if env_path:
        if os.path.exists(env_path):
            result = _resolve_to_cli_js(env_path)
            if result:
                return result
        print(f"Warning: CLAUDE_BINARY={env_path} not found, trying other methods.")

    # Strategy 2: which claude + resolve symlinks
    on_path = _which("claude")
    if on_path:
        result = _resolve_to_cli_js(on_path)
        if result:
            return result

    # Strategy 3: Check patcher state for previously known path
    state = read_patcher_state()
    if state.get("cliPath") and os.path.exists(state["cliPath"]):
        return state["cliPath"]

    # Strategy 4: Platform-specific candidate paths
    for candidate in _platform_candidates():
        if os.path.exists(candidate):
            result = _resolve_to_cli_js(candidate)
            if result:
                return result

    raise FileNotFoundError(
        "Could not find Claude Code installation.\n"
        "  Tried: `which claude` and common install paths.\n\n"
        "  Set CLAUDE_BINARY=/path/to/cli.js to specify manually."
    )


# ── macOS codesign ──


def _codesign(binary_path: str) -> None:
    """Re-sign a modified binary on macOS."""
    if not IS_MAC:
        return
    # Only codesign compiled binaries, not .js files
    if binary_path.endswith(".js") or binary_path.endswith(".mjs"):
        return
    try:
        subprocess.run(
            ["codesign", "--force", "--sign", "-", binary_path],
            capture_output=True, timeout=30,
        )
    except Exception:
        pass


# ── Salt operations ──


def get_current_salt(cli_path: str) -> str:
    """Detect the current salt by reading the binary."""
    with open(cli_path, "rb") as f:
        content = f.read()

    # Check default salt first
    if DEFAULT_SALT.encode() in content:
        return DEFAULT_SALT

    # Check salts from all known companions
    for name in list_companions():
        buddy_path = COMPANIONS_DIR / name / "buddy.json"
        if buddy_path.exists():
            with open(buddy_path) as f:
                buddy = json.load(f)
            salt = buddy.get("salt", "")
            if salt and salt.encode() in content:
                return salt

    # Check patcher state for previously recorded salt
    state = read_patcher_state()
    if state.get("currentSalt"):
        test_salt = state["currentSalt"]
        if test_salt.encode() in content:
            return test_salt

    raise RuntimeError(
        f"Cannot determine current salt in {cli_path}.\n"
        f"  The default salt '{DEFAULT_SALT}' was not found,\n"
        "  and no known companion salt matched.\n"
        "  If you patched with another tool, restore first,\n"
        "  or set CLAUDE_BINARY to the correct path."
    )


def patch_salt(cli_path: str, old_salt: str, new_salt: str) -> int:
    """Replace salt in the CLI file. Returns number of replacements."""
    if len(new_salt) != SALT_LENGTH:
        raise ValueError(
            f"Salt must be exactly {SALT_LENGTH} characters, got {len(new_salt)}"
        )

    with open(cli_path, "rb") as f:
        content = f.read()

    old_bytes = old_salt.encode("utf-8")
    new_bytes = new_salt.encode("utf-8")
    count = content.count(old_bytes)

    if count == 0:
        raise RuntimeError(
            f"Salt '{old_salt}' not found in {cli_path}.\n"
            "  The CLI may have been updated or patched by another tool."
        )

    new_content = content.replace(old_bytes, new_bytes)

    # Write via temp file for safety
    tmp_path = cli_path + ".patch-tmp"
    try:
        with open(tmp_path, "wb") as f:
            f.write(new_content)
        os.chmod(tmp_path, os.stat(cli_path).st_mode)
        os.replace(tmp_path, cli_path)
    except Exception:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise

    # Verify
    with open(cli_path, "rb") as f:
        verify = f.read()
    if verify.count(new_bytes) < count:
        raise RuntimeError("Verification failed — salt not applied correctly.")

    # Re-sign on macOS if needed
    _codesign(cli_path)

    return count


# ── Config and state ──


def find_claude_config() -> Optional[Path]:
    """Find the Claude Code config file."""
    for path in CLAUDE_CONFIG_PATHS:
        if path.exists():
            return path
    return None


def read_patcher_state() -> dict:
    """Read patcher state file."""
    if PATCHER_STATE.exists():
        with open(PATCHER_STATE) as f:
            return json.load(f)
    return {}


def write_patcher_state(state: dict) -> None:
    """Write patcher state file."""
    with open(PATCHER_STATE, "w") as f:
        json.dump(state, f, indent=2)
        f.write("\n")


def list_companions() -> list:
    """List available companions."""
    if not COMPANIONS_DIR.exists():
        return []
    return sorted(
        d.name
        for d in COMPANIONS_DIR.iterdir()
        if d.is_dir() and (d / "buddy.json").exists()
    )


def load_companion(name: str) -> tuple:
    """Load companion's buddy.json and companion.json."""
    companion_dir = COMPANIONS_DIR / name

    buddy_path = companion_dir / "buddy.json"
    companion_path = companion_dir / "companion.json"

    if not buddy_path.exists():
        print(f"Error: {buddy_path} not found")
        sys.exit(1)
    if not companion_path.exists():
        print(f"Error: {companion_path} not found")
        sys.exit(1)

    with open(buddy_path) as f:
        buddy = json.load(f)
    with open(companion_path) as f:
        companion = json.load(f)

    return buddy, companion


def update_claude_config(config_path: Path, companion: dict) -> None:
    """Update ~/.claude.json with companion identity."""
    with open(config_path) as f:
        config = json.load(f)

    config["companion"] = {
        "name": companion["name"],
        "personality": companion["personality"],
    }
    if "hatchedAt" in companion:
        config["companion"]["hatchedAt"] = companion["hatchedAt"]

    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)
        f.write("\n")


# ── Commands ──


def patch_companion(name: str) -> None:
    """Patch Claude Code to use the specified companion."""
    buddy, companion = load_companion(name)
    new_salt = buddy.get("salt")

    if not new_salt:
        print(f"Error: No salt found in {name}/buddy.json")
        sys.exit(1)

    try:
        cli_path = find_claude_binary()
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)

    config_path = find_claude_config()
    if not config_path:
        print("Error: Claude config not found")
        sys.exit(1)

    try:
        current_salt = get_current_salt(cli_path)
    except RuntimeError as e:
        print(f"Error: {e}")
        sys.exit(1)

    print(f"Companion:    {companion['name']}")
    print(f"Species:      {buddy['bones']['species']} ({buddy['bones']['rarity']})")
    print(f"CLI file:     {cli_path}")
    print(f"Config:       {config_path}")
    print(f"Current salt: {current_salt}")
    print(f"New salt:     {new_salt}")
    print()

    if current_salt == new_salt:
        print("Salt already matches — just updating companion identity.")
    else:
        # Backup
        backup_path = cli_path + f".backup-{int(datetime.now().timestamp())}"
        shutil.copy2(cli_path, backup_path)
        print(f"Backed up CLI to {os.path.basename(backup_path)}")

        try:
            count = patch_salt(cli_path, current_salt, new_salt)
            print(f"Salt patched ({count} replacement(s)).")
        except (RuntimeError, ValueError) as e:
            print(f"Patch failed: {e}")
            print("Restoring backup.")
            shutil.copy2(backup_path, cli_path)
            sys.exit(1)

    # Backup and update config
    config_backup = config_path.with_suffix(
        f".json.backup-{int(datetime.now().timestamp())}"
    )
    shutil.copy2(config_path, config_backup)
    update_claude_config(config_path, companion)
    print("Companion identity updated.")

    write_patcher_state(
        {
            "previousSalt": current_salt,
            "currentSalt": new_salt,
            "companion": name,
            "cliPath": cli_path,
            "patchedAt": datetime.now(timezone.utc).isoformat(),
        }
    )

    print()
    print(f"Done! {companion['name']} is now your companion.")
    print("Restart Claude Code to see the changes.")


def restore_default() -> None:
    """Restore the default salt."""
    try:
        cli_path = find_claude_binary()
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)

    try:
        current_salt = get_current_salt(cli_path)
    except RuntimeError as e:
        print(f"Error: {e}")
        sys.exit(1)

    if current_salt == DEFAULT_SALT:
        print("Already using the default salt. Nothing to restore.")
        return

    print(f"Restoring default salt: {DEFAULT_SALT}")
    print(f"Current salt:           {current_salt}")

    backup_path = cli_path + f".backup-{int(datetime.now().timestamp())}"
    shutil.copy2(cli_path, backup_path)

    try:
        patch_salt(cli_path, current_salt, DEFAULT_SALT)
    except (RuntimeError, ValueError) as e:
        print(f"Restore failed: {e}")
        shutil.copy2(backup_path, cli_path)
        sys.exit(1)

    write_patcher_state(
        {
            "previousSalt": current_salt,
            "currentSalt": DEFAULT_SALT,
            "companion": None,
            "cliPath": cli_path,
            "patchedAt": datetime.now(timezone.utc).isoformat(),
        }
    )

    print("Default salt restored. Restart Claude Code.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Patch Claude Code to use a stored companion"
    )
    parser.add_argument(
        "companion",
        nargs="?",
        help="Companion name from companions/ directory",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available companions",
    )
    parser.add_argument(
        "--restore",
        action="store_true",
        help="Restore the default salt",
    )

    args = parser.parse_args()

    if args.list:
        companions = list_companions()
        if not companions:
            print("No companions found in companions/ directory.")
        else:
            print("Available companions:")
            for name in companions:
                buddy, comp = load_companion(name)
                bones = buddy["bones"]
                print(
                    f"  {name:<16} {comp['name']:<16} "
                    f"{bones['species']:<10} {bones['rarity']:<10} "
                    f"salt={buddy['salt']}"
                )
        return

    if args.restore:
        restore_default()
        return

    if not args.companion:
        parser.print_help()
        return

    name = args.companion.lower()
    available = list_companions()

    if name not in available:
        print(f"Error: Companion '{name}' not found.")
        print(f"Available: {', '.join(available)}")
        sys.exit(1)

    patch_companion(name)


if __name__ == "__main__":
    main()
