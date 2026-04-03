# Companion Patcher

Patch Claude Code to use any companion stored in the `companions/` directory.
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

## How it finds Claude Code

The patcher uses multiple strategies to locate the Claude Code CLI:

1. `CLAUDE_BINARY` env var (manual override)
2. `which claude` with full symlink resolution
3. Previously known path from patcher state
4. Platform-specific candidate paths (macOS, Linux, Windows)

Supports installations via npm, fnm, nvm, volta, homebrew, and the desktop app.

## What it does

1. Reads the companion's `buddy.json` for the salt and `companion.json` for identity
2. Finds the Claude Code CLI automatically
3. Backs up the CLI file and `~/.claude.json`
4. Replaces the salt in the CLI (byte-level, same length)
5. Re-signs the binary on macOS if needed
6. Updates the `companion` field in `~/.claude.json`
7. Saves state to `.patcher-state.json` for restore capability

## Notes

- The salt determines the visual species. Same salt + same account = same buddy.
- Name and personality apply immediately; species depends on the salt.
- Always restart Claude Code after patching.
- Backups are created before any modification.
- Works with both `.js` CLI files and compiled binaries.
