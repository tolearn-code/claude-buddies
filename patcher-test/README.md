# Companion Patcher

Patch Claude Code to use any companion stored in the `companions/` directory.
Works on **any machine and any account** — the patcher reads your account UUID
and finds a salt that produces the exact same companion visuals for you.

No external tools or npm packages required — just Python 3.

## Usage

```bash
# List available companions
python3 patcher-test/patch_companion.py --list

# Apply a companion
python3 patcher-test/patch_companion.py vyrenth
python3 patcher-test/patch_companion.py thistlewing

# Restore default salt
python3 patcher-test/patch_companion.py --restore
```

## How it works

1. Reads the companion's target bones (species, rarity, eye, hat, shiny) from `buddy.json`
2. Reads your `accountUuid` from `~/.claude.json`
3. Tries the stored salt first — if it produces matching bones, uses it directly
4. Otherwise, brute-forces a new salt that produces the exact same visual companion
5. Patches the salt into Claude Code's CLI file
6. Updates `~/.claude.json` with the companion's name and personality

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
- Works with both `.js` CLI files and compiled binaries.
- Re-signs binaries on macOS if needed.
- Uses FNV-1a hash (Node.js runtime). If your install uses Bun, the salt search
  may need adjustment.
