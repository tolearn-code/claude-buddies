# Companion Patcher

Patch Claude Code to use any companion stored in the `companions/` directory.
Works on **any machine and any account** — the patcher reads your account UUID
and finds a salt that produces the exact same companion visuals for you.

Two patcher implementations:
- **Python** (`patch_companion.py`) — works with both FNV-1a and wyhash (shells out to bun for wyhash)
- **Bun/TypeScript** (`patch_companion_bun.ts`) — native wyhash support, faster salt brute-forcing

## Usage

### Python patcher

```bash
# List available companions
python3 patcher-test/patch_companion.py --list

# Apply a companion (auto-detects hash algorithm)
python3 patcher-test/patch_companion.py vyrenth
python3 patcher-test/patch_companion.py thistlewing

# Force a specific hash algorithm
python3 patcher-test/patch_companion.py vyrenth --wyhash
python3 patcher-test/patch_companion.py vyrenth --fnv1a

# Detect which hash your installation uses
python3 patcher-test/patch_companion.py --detect-hash

# Restore default salt
python3 patcher-test/patch_companion.py --restore
```

### Bun patcher

```bash
# List available companions
bun patcher-test/patch_companion_bun.ts --list

# Apply a companion (auto-detects hash algorithm)
bun patcher-test/patch_companion_bun.ts vyrenth

# Force a specific hash algorithm
bun patcher-test/patch_companion_bun.ts vyrenth --wyhash
bun patcher-test/patch_companion_bun.ts vyrenth --fnv1a

# Detect which hash your installation uses
bun patcher-test/patch_companion_bun.ts --detect-hash

# Restore default salt
bun patcher-test/patch_companion_bun.ts --restore
```

## Hash algorithm detection

Claude Code uses different hash algorithms depending on the runtime:
- **Bun** (default) → wyhash
- **Node.js** → FNV-1a

The same salt produces **different companions** under different hashes. The patcher auto-detects the correct hash using three strategies:

1. **Stored salt verification** — rolls the companion's stored salt with both hashes and checks which one reproduces the target bones
2. **CLI shebang inspection** — checks if the binary references `bun` or `node`
3. **Default fallback** — assumes wyhash (Bun) since it's the standard Claude Code runtime

Use `--detect-hash` to see what each algorithm produces for your account and compare with your current companion.

## How it works

1. Reads the companion's target bones (species, rarity, eye, hat, shiny) from `buddy.json`
2. Reads your `accountUuid` from `~/.claude.json`
3. Auto-detects the hash algorithm (or uses the forced flag)
4. Tries the stored salt first — if it produces matching bones, uses it directly
5. Otherwise, brute-forces a new salt that produces the exact same visual companion
6. Patches the salt into Claude Code's CLI file
7. Updates `~/.claude.json` with the companion's name and personality

Since buddy generation is deterministic (hash + RNG), any salt that produces matching
bones will give you the same species, rarity, eye style, hat, and shiny status.

## How it finds Claude Code

Multiple strategies, in order:

1. `CLAUDE_BINARY` env var (manual override)
2. `which claude` with full symlink resolution
3. Previously known path from patcher state
4. Platform-specific candidate paths (macOS, Linux, Windows)

Supports installations via npm, fnm, nvm, volta, homebrew, and the desktop app.

## Notes

- Always restart Claude Code after patching.
- Backups are created before any modification.
- **Only `.js` CLI files can be patched.** Compiled binaries are rejected — byte replacement corrupts their internal integrity checksums, causing segfaults.
- `--restore` uses the backup file from patcher state when available, which is safe for any file type. Falls back to byte replacement only for `.js` files.
- Re-signs binaries on macOS if needed.
- The Bun patcher is faster for wyhash salt brute-forcing since it hashes natively.
- The Python patcher shells out to bun for wyhash — requires bun on PATH.
- Use `--fnv1a` if your Claude Code install uses Node.js instead of Bun.
