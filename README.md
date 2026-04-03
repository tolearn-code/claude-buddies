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

## Generators

Two self-contained generators are included to roll any buddy from a `userId + salt`. No need to clone the full any-buddy repo.

### Which hash does Claude Code use?

Claude Code uses **wyhash** (via Bun) by default. If Bun is not available, it falls back to **FNV-1a**. The hash algorithm determines what buddy you get — same userId + salt with different hashes produces a completely different pet.

### Bun/wyhash generator (recommended)

Requires [Bun](https://bun.sh) installed. Produces the **same results as Claude Code's default**.

```bash
bun bun-wyhash-generator/buddy_generator.ts <accountUuid> [salt]
bun bun-wyhash-generator/buddy_generator.ts <accountUuid> --output companions/mybuddy
bun bun-wyhash-generator/buddy_generator.ts <accountUuid> --json
```

### Python/FNV-1a generator

Requires only Python 3. Uses FNV-1a hash (matches Claude Code on systems without Bun). Can also use wyhash if Bun is installed via `--wyhash` flag.

```bash
python3 generator/buddy_generator.py <accountUuid> [salt]
python3 generator/buddy_generator.py <accountUuid> --wyhash          # use Bun's wyhash
python3 generator/buddy_generator.py <accountUuid> -o companions/mybuddy
python3 generator/buddy_generator.py <accountUuid> --json
```

## Files

| File / Folder | Purpose |
|------|---------|
| `install.sh` | One-command installer script |
| `companion.json` | Name, personality, and hatch timestamp |
| `buddy.json` | Full profile (salt, bones, stats) |
| `sprite.txt` | ASCII art for all animation frames |
| `hatch-instructions.md` | Step-by-step guide to recreate on another machine |
| `recreation-guide.txt` | Technical details on deterministic generation |
| `bun-wyhash-generator/` | Bun/TypeScript generator (wyhash, Claude Code default) |
| `generator/` | Python generator (FNV-1a default, wyhash optional) |
| `instructions/` | LLM-friendly extraction guide |

## Stats

| Stat | Value |
|------|-------|
| DEBUGGING | 19 |
| PATIENCE | 38 |
| CHAOS | 87 (peak) |
| WISDOM | 47 |
| SNARK | 5 (dump) |
