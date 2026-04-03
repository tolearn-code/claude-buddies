# How to Extract a Full Buddy Profile

Instructions for any LLM (Claude Code, etc.) to extract all companion data from a Claude Code installation.

## What you need to produce

Three files per buddy in `companions/<buddy-name>/`:

### 1. `companion.json` — Identity
```json
{
  "name": "BuddyName",
  "personality": "personality text",
  "hatchedAt": 1234567890000
}
```

### 2. `buddy.json` — Full Profile
```json
{
  "name": "BuddyName",
  "personality": "personality text",
  "defaultPersonality": "species default personality text",
  "hatchedAt": 1234567890000,
  "salt": "the-15-char-salt",
  "bones": {
    "rarity": "uncommon",
    "species": "owl",
    "eye": "·",
    "hat": "none",
    "shiny": false,
    "stats": {
      "DEBUGGING": 0,
      "PATIENCE": 0,
      "CHAOS": 0,
      "WISDOM": 0,
      "SNARK": 0
    }
  },
  "inspirationSeed": 0
}
```

### 3. `sprite.txt` — ASCII Art
All animation frames (idle, wink, sleeping) rendered from the bones.

## Step-by-step extraction

### Step 1: Get companion identity from Claude config

Read `~/.claude.json` (or `~/.claude/.config.json`). Extract:
```
companion.name
companion.personality
companion.hatchedAt
oauthAccount.accountUuid  (this is the userId for generation)
```

### Step 2: Determine the current salt

Check if any-buddy has been used:
```bash
cat ~/.claude-code-any-buddy.json
```

- If the file exists, read `profiles[activeProfile].salt`
- If it doesn't exist, the salt is the original: `friend-2026-401`

### Step 3: Roll the buddy using generation code

You need the [any-buddy](https://github.com/cpaczek/any-buddy) repo cloned locally.

```bash
# Clone if needed
git clone https://github.com/cpaczek/any-buddy.git
cd any-buddy
```

Run the roll with bun (preferred) or node:

```bash
bun -e "
import { roll } from './src/generation/roll.ts';
const userId = '<accountUuid from step 1>';
const salt = '<salt from step 2>';
const result = roll(userId, salt);
console.log(JSON.stringify(result, null, 2));
"
```

This outputs the full `bones` and `inspirationSeed`.

### Step 4: Get the default personality

```bash
bun -e "
import { DEFAULT_PERSONALITIES } from './src/personalities.ts';
console.log(DEFAULT_PERSONALITIES['<species from step 3>']);
"
```

### Step 5: Render the sprite

```bash
bun -e "
import { renderSprite } from './src/sprites/render.ts';
const bones = <paste bones object from step 3>;
for (let i = 0; i < 3; i++) {
  console.log('--- Frame ' + i + ' ---');
  renderSprite(bones, i, false).forEach(l => console.log(l));
  console.log();
}
console.log('--- Sleeping ---');
renderSprite(bones, 0, true).forEach(l => console.log(l));
"
```

### Step 6: Save files

Create `companions/<buddy-name>/` with the three files described above.

**Important:** Do NOT include `accountUuid` or any personally identifiable info in the saved files.

## Notes

- The userId (`accountUuid`) is needed for generation but should not be saved to the repo
- If bun is not available, use node with `npm run build` first, then import from `./dist/`
- The hash algorithm differs between bun (wyhash) and node (FNV-1a) — use whichever runtime the Claude Code installation uses
- Salt is always exactly 15 characters
