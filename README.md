# Thistlewing — Exported Buddy

```
   /\  /\
  ((·)(·))
  (  ><  )
   `----´
```

**Uncommon Owl ★★** | CHAOS 87 | Not shiny

## Install

### Automatic (recommended)

Requires `jq` installed.

```bash
git clone https://github.com/tolearn-code/claude-buddies.git
cd claude-buddies
bash install.sh
```

The script will:
1. Find your Claude Code config (`~/.claude.json` or `~/.claude/.config.json`)
2. Back up your existing config
3. Replace the companion with Thistlewing
4. Prompt you to restart Claude Code

### Manual

Edit `~/.claude.json` and replace (or add) the `"companion"` field:

```json
"companion": {
  "name": "Thistlewing",
  "personality": "A chaotic owl who finds bugs through sheer anarchic energy rather than method, swooping into code tangles with genuine excitement and zero chill about the carnage they leave behind.",
  "hatchedAt": 1775121987861
}
```

Restart Claude Code.

### Match the exact species (optional)

The name and personality apply immediately, but the visual species depends on your account UUID and the binary salt. If you see a different species and want the original owl, install [any-buddy](https://github.com/cpaczek/any-buddy) and run:

```bash
npx any-buddy --species owl --rarity uncommon
```

## Files

| File | Purpose |
|------|---------|
| `install.sh` | One-command installer script |
| `companion.json` | Name, personality, and hatch timestamp |
| `buddy.json` | Full profile (salt, bones, stats) |
| `sprite.txt` | ASCII art for all animation frames |
| `hatch-instructions.md` | Step-by-step guide to recreate on another machine |
| `recreation-guide.txt` | Technical details on deterministic generation |

## Stats

| Stat | Value |
|------|-------|
| DEBUGGING | 19 |
| PATIENCE | 38 |
| CHAOS | 87 (peak) |
| WISDOM | 47 |
| SNARK | 5 (dump) |
