#!/usr/bin/env python3
"""
Patch Claude Code to use a companion from the companions/ directory.

Reads the desired companion's bones (species, rarity, eye, hat, shiny),
reads the current user's account UUID, then brute-forces a salt that
produces matching bones for this specific user. Works on any machine
regardless of who originally created the companion profile.

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
import math
import os
import platform
import random
import shutil
import string
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


# ── Buddy generation (FNV-1a) ──

RARITIES = ["common", "uncommon", "rare", "epic", "legendary"]
RARITY_WEIGHTS = {"common": 60, "uncommon": 25, "rare": 10, "epic": 4, "legendary": 1}
RARITY_FLOOR = {"common": 5, "uncommon": 15, "rare": 25, "epic": 35, "legendary": 50}

SPECIES = [
    "duck", "goose", "blob", "cat", "dragon", "octopus",
    "owl", "penguin", "turtle", "snail", "ghost", "axolotl",
    "capybara", "cactus", "robot", "rabbit", "mushroom", "chonk",
]

EYES = ["·", "✦", "×", "◉", "@", "°"]
HATS = ["none", "crown", "tophat", "propeller", "halo", "wizard", "beanie", "tinyduck"]
STAT_NAMES = ["DEBUGGING", "PATIENCE", "CHAOS", "WISDOM", "SNARK"]


def fnv1a(s: str) -> int:
    h = 2166136261
    for ch in s:
        h ^= ord(ch)
        h = (h * 16777619) & 0xFFFFFFFF
    return h


def mulberry32(seed: int):
    a = seed & 0xFFFFFFFF

    def _imul(a_val: int, b_val: int) -> int:
        a_val &= 0xFFFFFFFF
        b_val &= 0xFFFFFFFF
        result = (a_val * b_val) & 0xFFFFFFFF
        if result >= 0x80000000:
            result -= 0x100000000
        return result

    def rng() -> float:
        nonlocal a
        a = a & 0xFFFFFFFF
        a_signed = a - 0x100000000 if a >= 0x80000000 else a
        a_signed = (a_signed + 0x6D2B79F5) | 0
        a_signed = a_signed & 0xFFFFFFFF
        if a_signed >= 0x80000000:
            a_signed -= 0x100000000
        a = a_signed & 0xFFFFFFFF

        t = _imul(a_signed ^ ((a & 0xFFFFFFFF) >> 15), 1 | a_signed)
        t = t & 0xFFFFFFFF
        if t >= 0x80000000:
            t -= 0x100000000

        t2 = _imul(t ^ (((t & 0xFFFFFFFF) >> 7)), 61 | t)
        t2 = t2 & 0xFFFFFFFF
        if t2 >= 0x80000000:
            t2 -= 0x100000000

        t = (t + t2) ^ t
        t = t & 0xFFFFFFFF
        if t >= 0x80000000:
            t -= 0x100000000

        return ((t ^ (((t & 0xFFFFFFFF) >> 14))) & 0xFFFFFFFF) / 4294967296

    return rng


def pick(rng, arr):
    return arr[math.floor(rng() * len(arr))]


def roll_rarity(rng):
    total = sum(RARITY_WEIGHTS.values())
    r = rng() * total
    for rarity in RARITIES:
        r -= RARITY_WEIGHTS[rarity]
        if r < 0:
            return rarity
    return "common"


def roll_stats(rng, rarity: str) -> dict:
    floor = RARITY_FLOOR[rarity]
    peak = pick(rng, STAT_NAMES)
    dump = pick(rng, STAT_NAMES)
    while dump == peak:
        dump = pick(rng, STAT_NAMES)
    stats = {}
    for name in STAT_NAMES:
        if name == peak:
            stats[name] = min(100, floor + 50 + math.floor(rng() * 30))
        elif name == dump:
            stats[name] = max(1, floor - 10 + math.floor(rng() * 15))
        else:
            stats[name] = floor + math.floor(rng() * 40)
    return stats


def roll(user_id: str, salt: str) -> dict:
    """Roll a buddy from userId + salt using FNV-1a."""
    h = fnv1a(user_id + salt)
    rng = mulberry32(h)
    rarity = roll_rarity(rng)
    bones = {
        "rarity": rarity,
        "species": pick(rng, SPECIES),
        "eye": pick(rng, EYES),
        "hat": "none" if rarity == "common" else pick(rng, HATS),
        "shiny": rng() < 0.01,
        "stats": roll_stats(rng, rarity),
    }
    inspiration_seed = math.floor(rng() * 1e9)
    return {"bones": bones, "inspirationSeed": inspiration_seed}


def bones_match(target: dict, candidate: dict) -> bool:
    """Check if candidate bones match the target on visual attributes."""
    return (
        candidate["species"] == target["species"]
        and candidate["rarity"] == target["rarity"]
        and candidate["eye"] == target["eye"]
        and candidate["hat"] == target["hat"]
        and candidate["shiny"] == target["shiny"]
    )


def find_salt(user_id: str, target_bones: dict, max_attempts: int = 5_000_000) -> str:
    """Brute-force a salt that produces matching bones for this user."""
    chars = string.ascii_letters + string.digits
    # Try sequential salts first (faster to generate)
    print("  Searching for a matching salt...")
    for i in range(max_attempts):
        salt = f"patch-{i:09d}"
        result = roll(user_id, salt)
        if bones_match(target_bones, result["bones"]):
            return salt
        if i > 0 and i % 500_000 == 0:
            print(f"  ...checked {i:,} salts")

    raise RuntimeError(
        f"Could not find a matching salt in {max_attempts:,} attempts.\n"
        "  The target bones may be extremely rare. Try increasing max_attempts."
    )


# ── Binary finder ──


def _which(cmd: str) -> Optional[str]:
    result = shutil.which(cmd)
    if result and os.path.exists(result):
        return result
    return None


def _resolve(p: str) -> str:
    return str(Path(p).resolve())


def _platform_candidates() -> list:
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
    return [
        os.path.join(home, ".local", "bin", "claude"),
        "/usr/local/bin/claude",
        "/usr/bin/claude",
        os.path.join(home, ".npm-global", "bin", "claude"),
        os.path.join(home, ".volta", "bin", "claude"),
    ]


def _resolve_to_cli_js(binary_path: str) -> Optional[str]:
    resolved = _resolve(binary_path)
    if resolved.endswith(".js"):
        return resolved
    pkg_marker = os.path.join("@anthropic-ai", "claude-code")
    idx = resolved.find(pkg_marker)
    if idx != -1:
        pkg_dir = resolved[: idx + len(pkg_marker)]
        cli_candidate = os.path.join(pkg_dir, "cli.js")
        if os.path.exists(cli_candidate):
            return cli_candidate
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
    if os.path.exists(resolved) and os.path.getsize(resolved) >= 1_000_000:
        return resolved
    return None


def find_claude_binary() -> str:
    env_path = os.environ.get("CLAUDE_BINARY")
    if env_path:
        if os.path.exists(env_path):
            result = _resolve_to_cli_js(env_path)
            if result:
                return result
        print(f"Warning: CLAUDE_BINARY={env_path} not found, trying other methods.")

    on_path = _which("claude")
    if on_path:
        result = _resolve_to_cli_js(on_path)
        if result:
            return result

    state = read_patcher_state()
    if state.get("cliPath") and os.path.exists(state["cliPath"]):
        return state["cliPath"]

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
    if not IS_MAC:
        return
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

    # Check patcher state
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

    with open(cli_path, "rb") as f:
        verify = f.read()
    if verify.count(new_bytes) < count:
        raise RuntimeError("Verification failed — salt not applied correctly.")

    _codesign(cli_path)
    return count


# ── Config and state ──


def find_claude_config() -> Optional[Path]:
    for path in CLAUDE_CONFIG_PATHS:
        if path.exists():
            return path
    return None


def get_account_uuid(config_path: Path) -> str:
    """Read the accountUuid from Claude config."""
    with open(config_path) as f:
        config = json.load(f)
    uuid = (config.get("oauthAccount") or {}).get("accountUuid")
    if not uuid:
        raise RuntimeError(
            "No accountUuid found in Claude config.\n"
            "  Make sure you are logged in to Claude Code."
        )
    return uuid


def read_patcher_state() -> dict:
    if PATCHER_STATE.exists():
        with open(PATCHER_STATE) as f:
            return json.load(f)
    return {}


def write_patcher_state(state: dict) -> None:
    with open(PATCHER_STATE, "w") as f:
        json.dump(state, f, indent=2)
        f.write("\n")


def list_companions() -> list:
    if not COMPANIONS_DIR.exists():
        return []
    return sorted(
        d.name
        for d in COMPANIONS_DIR.iterdir()
        if d.is_dir() and (d / "buddy.json").exists()
    )


def load_companion(name: str) -> tuple:
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
    target_bones = buddy.get("bones")

    if not target_bones:
        print(f"Error: No bones found in {name}/buddy.json")
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

    # Get this user's account UUID
    try:
        user_id = get_account_uuid(config_path)
    except RuntimeError as e:
        print(f"Error: {e}")
        sys.exit(1)

    try:
        current_salt = get_current_salt(cli_path)
    except RuntimeError as e:
        print(f"Error: {e}")
        sys.exit(1)

    print(f"Companion:    {companion['name']}")
    print(f"Target:       {target_bones['species']} ({target_bones['rarity']})")
    print(f"              eye={target_bones['eye']}  hat={target_bones['hat']}  "
          f"shiny={'yes' if target_bones['shiny'] else 'no'}")
    print(f"CLI file:     {cli_path}")
    print(f"Config:       {config_path}")
    print(f"Current salt: {current_salt}")
    print()

    # Check if the stored salt already works for this user
    stored_salt = buddy.get("salt", "")
    if stored_salt:
        result = roll(user_id, stored_salt)
        if bones_match(target_bones, result["bones"]):
            new_salt = stored_salt
            print(f"Stored salt works for this account: {new_salt}")
        else:
            print("Stored salt produces different bones for this account.")
            print("Finding a new salt...")
            try:
                new_salt = find_salt(user_id, target_bones)
            except RuntimeError as e:
                print(f"Error: {e}")
                sys.exit(1)
            print(f"Found matching salt: {new_salt}")
    else:
        print("No stored salt — searching for one...")
        try:
            new_salt = find_salt(user_id, target_bones)
        except RuntimeError as e:
            print(f"Error: {e}")
            sys.exit(1)
        print(f"Found matching salt: {new_salt}")

    print(f"New salt:     {new_salt}")
    print()

    if current_salt == new_salt:
        print("Salt already matches — just updating companion identity.")
    else:
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

    # Verify the roll
    verify = roll(user_id, new_salt)
    print()
    print(f"Done! {companion['name']} is now your companion.")
    print(f"  Species: {verify['bones']['species']} ({verify['bones']['rarity']})")
    print(f"  Eye: {verify['bones']['eye']}  Hat: {verify['bones']['hat']}  "
          f"Shiny: {'yes' if verify['bones']['shiny'] else 'no'}")
    print()
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
                    f"eye={bones['eye']}  hat={bones['hat']}"
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
