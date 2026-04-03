# Claude Buddies

A collection of **1,737 curated companions** for Claude Code — 18 species, every visual combo, with hand-crafted fantasy names and personalities.

```
   /\  /\        /^\  /^\       .----.       /\_/\
  ((·)(·))      <  ✦  ✦  >    ( ◉  ◉ )     ( ×   ×)
  (  ><  )      (   ~~   )    (______)      (  ω  )
   `----´        `-vvvv-´     /\/\/\/\      (")_(")
   Owl            Dragon      Octopus        Cat
```

## Quick Start

### Install a companion (name + personality only)

```bash
git clone https://github.com/tolearn-code/claude-buddies.git
cd claude-buddies
bash install.sh
```

### Patch a companion (full visual species change)

Requires Claude Code installed via npm (`npm install -g @anthropic-ai/claude-code`).

```bash
# List all available companions
bun patcher-test/patch_companion_bun.ts --list

# Apply any companion by name
bun patcher-test/patch_companion_bun.ts eldurion
bun patcher-test/patch_companion_bun.ts grakthul

# Detect which hash algorithm your install uses
bun patcher-test/patch_companion_bun.ts --detect-hash

# Restore default
bun patcher-test/patch_companion_bun.ts --restore
```

Python patcher also available:
```bash
python3 patcher-test/patch_companion.py eldurion --wyhash
```

## Collection

| Species | Folder | Count | Theme |
|---------|--------|:-----:|-------|
| Axolotl | `companions/axolotls/` | 96 | Bloom/renewal names (Bloomthistle, Regenstar) |
| Blob | `companions/blobs/` | 96 | Arcane/ethereal names (Glymorthin, Aethergel) |
| Cactus | `companions/cacti/` | 96 | Desert/fortified names (Thornhelm, Ironspire) |
| Capybara | `companions/capybaras/` | 96 | Peaceful/grounded names (Stillwater, Calmhearth) |
| Cat | `companions/cats/` | 96 | Shadow/dark names (Nyxshadow, Velvetdusk) |
| Chonk | `companions/chonks/` | 96 | Grand/imposing names (Grandheim, Vastheart) |
| Dragon | `companions/dragons/` | 96 | Tolkien-inspired names (Aldranoth, Orthandir) |
| Duck | `companions/ducks/` | 96 | Aquatic/elvish names (Quellindor, Wavecrest) |
| Ghost | `companions/ghosts/` | 96 | Void/spectral names (Nullvarden, Grimsorrow) |
| Goose | `companions/geese/` | 96 | Orcish/aggressive names (Grakthul, Dreadscar) |
| Mushroom | `companions/mushrooms/` | 96 | Fungal/mystic names (Sporethane, Mycelward) |
| Octopus | `companions/octopi/` | 96 | Deep sea/ancient names (Thalassor, Krethidon) |
| Owl | `companions/owls/` | 96 | Wise/celestial names (Talonmere, Moonvigil) |
| Penguin | `companions/penguins/` | 96 | Noble/frost names (Frosthelm, Glaciermane) |
| Rabbit | `companions/rabbits/` | 96 | Swift/wind names (Swifthare, Veloxfoot) |
| Robot | `companions/robots/` | 96 | Metal/forge names (Ferronax, Voltarian) |
| Snail | `companions/snails/` | 96 | Nature/gentle names (Dewglimmer, Spiralwind) |
| Turtle | `companions/turtles/` | 96 | Earthen/stoic names (Stoneguard, Boulderheart) |

Plus 9 featured companions at the top level: Eldurion, Vyrenth, Thistlewing, Thunderthistl, and 5 hand-picked dragons.

Each species has **48 normal + 48 shiny** variants covering every eye x hat visual combination. Shiny variants use elvish prefixes (Aur-, Gil-, Mir-, Ithil-, Anar-, Luth-, Cael-, Thal-).

### Visual Combos

Every companion has a unique combination of:

- **6 eyes:** · ✦ × ◉ @ °
- **8 hats:** none, crown, tophat, propeller, halo, wizard, beanie, tinyduck

### Per-Companion Files

Each companion folder contains 4 files:

| File | Contents |
|------|----------|
| `buddy.json` | Full profile: name, personality, bones, stats, peak/dump stat |
| `companion.json` | Install config: name, personality, hatchedAt |
| `sprite.txt` | ASCII art animation frames (idle, alt, wink, sleeping) |
| `stats.txt` | Visual stat bars with peak/dump markers |

### Reference Guides

Each species folder has an `info/<species>.md` with a full table of all companions, their visual combos, stats, and top 5 rankings.

## Generators

Two self-contained generators to roll any buddy from `userId + salt`:

### Bun/wyhash (recommended)

Produces the same results as Claude Code's default. Requires [Bun](https://bun.sh).

```bash
bun bun-wyhash-generator/buddy_generator.ts <accountUuid> [salt]
bun bun-wyhash-generator/buddy_generator.ts <accountUuid> --output companions/mybuddy
bun bun-wyhash-generator/buddy_generator.ts <accountUuid> --json
```

### Python/FNV-1a

Requires only Python 3. Uses FNV-1a hash (Node.js fallback). Can use wyhash via `--wyhash` flag.

```bash
python3 generator/buddy_generator.py <accountUuid> [salt]
python3 generator/buddy_generator.py <accountUuid> --wyhash
python3 generator/buddy_generator.py <accountUuid> -o companions/mybuddy
```

## Patcher

The patcher modifies Claude Code's CLI to display any companion's exact species, rarity, eyes, and hat. Two implementations:

- **Bun** (`patcher-test/patch_companion_bun.ts`) — native wyhash, faster salt search
- **Python** (`patcher-test/patch_companion.py`) — shells out to bun for wyhash

Features:
- Auto-detects hash algorithm (wyhash vs FNV-1a)
- Scans subdirectories (`companions/dragons/aldranoth/`)
- Creates backups before any modification
- Rejects compiled binaries (requires npm install)
- Backup-based restore via `--restore`

See [`patcher-test/README.md`](patcher-test/README.md) for full docs.

## Hash Algorithms

Claude Code uses different hash algorithms depending on the runtime:

| Runtime | Hash | How to install |
|---------|------|---------------|
| Bun (default) | wyhash | Comes with Claude Code desktop app |
| Node.js | FNV-1a | `npm install -g @anthropic-ai/claude-code` |

The same salt produces **different companions** under different hashes. The patcher auto-detects which one to use.

## Repo Structure

```
claude-buddies/
├── companions/
│   ├── eldurion/              Featured companions (top level)
│   ├── vyrenth/
│   ├── thistlewing/
│   ├── thunderthistl/
│   ├── dragons/               96 legendary dragons
│   │   ├── aldranoth/
│   │   ├── ...
│   │   └── info/dragons.md
│   ├── ducks/                 96 legendary ducks
│   ├── geese/                 96 legendary geese
│   ├── ...                    (17 species total)
│   └── turtles/
├── patcher-test/              Companion patcher (Bun + Python)
├── bun-wyhash-generator/      Bun buddy generator
├── generator/                 Python buddy generator
├── instructions/              LLM extraction guide
├── install.sh                 Quick installer
├── species.md                 Species & rarity reference
└── README.md
```

## Stats

- **1,737** unique companions
- **18** species
- **6,978** files
- **16,433** lines
- All names hand-curated, zero duplicates
- Generated from 100M+ companion analysis
