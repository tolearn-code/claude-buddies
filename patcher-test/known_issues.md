# Known Issues

## Patcher Issues

### 1. Hash auto-detection is unreliable
**Status:** Open — use `--fnv1a` or `--wyhash` explicitly.

The patcher tries to auto-detect the hash algorithm by checking the CLI shebang and testing stored salts. This often fails:
- Compiled binaries have no useful shebang
- The stored salt test can match the wrong hash by coincidence
- Default fallback to wyhash is wrong for npm installs

**Workaround:** Always pass `--fnv1a` (for npm installs) or `--wyhash` (for Bun/desktop app).

### 2. Compiled binaries cannot be patched
**Status:** By design — not fixable.

The desktop app installs a compiled binary (e.g., `/home/user/.local/share/claude/versions/X.Y.Z`). Byte-replacing the salt corrupts internal integrity checksums, causing segfaults.

**Workaround:** Install via npm: `npm install -g @anthropic-ai/claude-code`. The npm version provides a patchable `cli.js` file.

### 3. Old binary persists in memory after switching
**Status:** OS behavior — not fixable.

If you switch from the compiled binary to npm-installed Claude Code, any **already-running** Claude session still uses the old binary (loaded in memory). The new binary only takes effect in new terminal sessions.

**Workaround:** Close all Claude Code sessions and start a new one after switching.

### 4. Desktop app may auto-update and overwrite npm install
**Status:** Open.

If the Claude Code desktop app is also installed, it may auto-update and change which `claude` binary is on PATH. This can silently switch back to the compiled binary.

**Workaround:** After patching, verify with `readlink -f $(which claude)` that it points to the npm `cli.js`, not a compiled binary.

### 5. Salt search can be slow for rare combos
**Status:** Mitigated — 40M limit covers all known combos.

Some species/rarity/eye/hat/shiny combinations require millions of salt attempts to find. Legendary shiny companions with specific accessories are the hardest.

The current 40M attempt limit has zero failures across 831+ tested companions. If you encounter a failure, you can increase `maxAttempts` in the patcher source.

### 6. Restore may fail if backup file was deleted
**Status:** Open.

The `--restore` command uses the backup file path stored in `.patcher-state.json`. If the backup was manually deleted or a reinstall wiped it, restore falls back to byte replacement (only safe for `.js` files) or fails entirely.

**Workaround:** Reinstall Claude Code: `npm install -g @anthropic-ai/claude-code`

### 7. Folder names don't match companion names
**Status:** Cosmetic — not a bug.

Companion folder names in `by_species/` don't match the `name` field in `buddy.json`. This is because companions were renamed after folder creation. The patcher uses folder names for lookup and JSON `name` for identity. Both work correctly.

## Testing Issues

### 8. Visual test has ~25% timing-based failure rate
**Status:** Expected — not a patching issue.

The tmux-based visual test (`/buddy` card capture) fails ~25% of the time because:
- Claude startup takes longer than the 25s wait under load
- `/buddy` card takes longer than 15s to render
- `claude -p` analysis returns empty under concurrent load

These are test infrastructure failures, not patching failures. When analysis succeeds, it's always correct.

### 9. Parallel testing limited to ~10 workers
**Status:** Expected — hardware limitation.

Running more than 10 parallel Claude instances on a single machine causes excessive load, increasing timing failures from 25% to 36%+. The optimal worker count depends on available RAM and CPU.
