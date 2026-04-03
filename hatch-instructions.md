# Hatch Thistlewing

## Step 1: Set the companion in Claude Code config

Edit `~/.claude.json` (or `~/.claude/.config.json` if that's where your config lives) and add or replace the `"companion"` field:

```json
"companion": {
  "name": "Thistlewing",
  "personality": "A chaotic owl who finds bugs through sheer anarchic energy rather than method, swooping into code tangles with genuine excitement and zero chill about the carnage they leave behind."
}
```

## Step 2: Verify your buddy

Restart Claude Code. Thistlewing should appear as your companion.

If the species/appearance is different from the original (uncommon owl), it's because the buddy visuals are determined by your `accountUuid` + the salt baked into the Claude Code binary. The name and personality above will apply regardless of what species was rolled.

## Step 3 (optional): Match the exact original species/stats

The original Thistlewing was rolled with:
- Salt: `friend-2026-401` (Claude Code default)
- Hash: wyhash (requires Bun runtime)

If your hash algorithm differs, you'll get a different species. To force an owl, install [any-buddy](https://github.com/cpaczek/any-buddy) and run:

```bash
npx any-buddy --species owl --rarity uncommon
```

## Original Stats

| Stat | Value |
|------|-------|
| DEBUGGING | 19 |
| PATIENCE | 38 |
| CHAOS | 87 (peak) |
| WISDOM | 47 |
| SNARK | 5 (dump) |

Rarity: Uncommon (★★)
Eye: · | Hat: none | Shiny: no
