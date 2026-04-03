# Recovery Help

If patching broke your Claude Code installation, follow these steps to restore it.

## Quick Fix: Reinstall

The fastest recovery is always a fresh install:

```bash
npm install -g @anthropic-ai/claude-code
```

This replaces the CLI with a clean copy containing the default salt. Your auth, settings, and conversation history are preserved (they live in `~/.claude/`, not in the CLI).

## Method 1: Patcher Restore (Preferred)

If you patched using this tool, the backup file should still exist:

```bash
# Restore from backup
bun patcher-test/patch_companion_bun.ts --restore

# Or Python version
python3 patcher-test/patch_companion.py --restore
```

This copies the pre-patch backup file back over the CLI. It also restores `~/.claude.json` to the pre-patch companion config.

**If restore says "No backup file found":** The backup was deleted. Use Method 2 or 3 instead.

## Method 2: Manual Backup Restore

Check if backup files exist:

```bash
# Find CLI backups
ls -la $(readlink -f $(which claude))*.backup-* 2>/dev/null

# Find config backups
ls -la ~/.claude.json.backup-* 2>/dev/null
```

If found, copy the most recent backup over the current file:

```bash
# Restore CLI (use the latest .backup-TIMESTAMP file)
cp /path/to/cli.js.backup-TIMESTAMP /path/to/cli.js

# Restore config
cp ~/.claude.json.backup-TIMESTAMP ~/.claude.json
```

## Method 3: Fresh npm Install

```bash
npm install -g @anthropic-ai/claude-code
```

This gives you a clean CLI. Your companion will revert to the default (determined by your account UUID and the default salt `friend-2026-401`).

To set just the name and personality without patching the binary:

```bash
# Edit ~/.claude.json manually or use jq:
cat ~/.claude.json | jq '.companion = {
  "name": "YourCompanionName",
  "personality": "Your personality text here."
}' > /tmp/claude_tmp.json && cp /tmp/claude_tmp.json ~/.claude.json
```

## Method 4: Reset Companion to Default

If the CLI is fine but you just want to reset the companion identity:

```bash
# Remove companion config entirely (reverts to default)
cat ~/.claude.json | jq 'del(.companion)' > /tmp/claude_tmp.json && cp /tmp/claude_tmp.json ~/.claude.json
```

Restart Claude Code — it will show the default companion for your account.

## Method 5: Nuclear Option

If nothing else works, remove everything and start fresh:

```bash
# Uninstall npm version
npm uninstall -g @anthropic-ai/claude-code

# Remove config (WARNING: loses all settings, but not conversations)
rm ~/.claude.json

# Reinstall
npm install -g @anthropic-ai/claude-code
```

Your conversations and auth are stored in `~/.claude/` and will survive this.

## Diagnosing the Problem

### Check which binary is running
```bash
# Which claude binary is on PATH?
which claude
readlink -f $(which claude)

# Is it a compiled binary or cli.js?
file $(readlink -f $(which claude))
# Should say "Node.js script" or similar, NOT "ELF 64-bit"

# What's the running process using?
ls -la /proc/$(pgrep -f "claude" | head -1)/exe 2>/dev/null
```

### Check if the CLI has the default salt
```bash
grep -c "friend-2026-401" $(readlink -f $(which claude))
# Should output: 1
# If 0: the salt was replaced (patched) or the file is corrupted
```

### Check patcher state
```bash
cat patcher-test/.patcher-state.json 2>/dev/null
# Shows: previousSalt, currentSalt, cliPath, backup paths
```

### Check for the "unknown" salt corruption
```bash
# If this returns a large number (400+), the CLI is corrupted
grep -o "ptch[a-z0-9]\{11\}" $(readlink -f $(which claude)) | wc -l
# Should return 0 or 1. If many: the "unknown" bug hit you.
# Fix: npm install -g @anthropic-ai/claude-code
```

### Check companion config
```bash
cat ~/.claude.json | python3 -c "
import json, sys
c = json.load(sys.stdin).get('companion', {})
print('Name:', c.get('name', '(none)'))
print('Personality:', c.get('personality', '(none)')[:80])
"
```

## Preventing Issues

1. **Always use npm install**, not the desktop app binary
2. **Always pass `--fnv1a`** when patching npm-installed Claude Code
3. **Don't delete backup files** until you've verified the patch works
4. **Start a new terminal** after patching — old sessions use the old binary
5. **Verify after patching:** `grep -c "friend-2026-401" $(readlink -f $(which claude))` should return 0 (salt was replaced)

## Getting Help

If you're stuck:
1. Check [known_issues.md](known_issues.md) for documented problems
2. Run `--detect-hash` to see what each hash algorithm produces for your account
3. The safest recovery is always: `npm install -g @anthropic-ai/claude-code`
