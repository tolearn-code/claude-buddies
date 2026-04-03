# Claude Buddies

A collection of **1,845 curated companions** for Claude Code — 18 species across 5 rarities, every visual combo, with hand-crafted fantasy names and unique personalities.

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

### By Species (Legendary)

| Species | Folder | Count | Theme |
|---------|--------|:-----:|-------|
| Axolotl | `companions/by_species/axolotls/` | 96 | Bloom/renewal (Bloomthistle, Regenstar) |
| Blob | `companions/by_species/blobs/` | 96 | Arcane/ethereal (Glymorthin, Aethergel) |
| Cactus | `companions/by_species/cacti/` | 96 | Desert/fortified (Thornhelm, Ironspire) |
| Capybara | `companions/by_species/capybaras/` | 96 | Peaceful/grounded (Stillwater, Calmhearth) |
| Cat | `companions/by_species/cats/` | 96 | Shadow/dark (Nyxshadow, Velvetdusk) |
| Chonk | `companions/by_species/chonks/` | 96 | Grand/imposing (Grandheim, Vastheart) |
| Dragon | `companions/by_species/dragons/` | 96 | Tolkien-inspired (Aldranoth, Orthandir) |
| Duck | `companions/by_species/ducks/` | 96 | Aquatic/elvish (Quellindor, Wavecrest) |
| Ghost | `companions/by_species/ghosts/` | 96 | Void/spectral (Nullvarden, Grimsorrow) |
| Goose | `companions/by_species/geese/` | 96 | Orcish/aggressive (Grakthul, Dreadscar) |
| Mushroom | `companions/by_species/mushrooms/` | 96 | Fungal/mystic (Sporethane, Mycelward) |
| Octopus | `companions/by_species/octopi/` | 96 | Deep sea/ancient (Thalassor, Krethidon) |
| Owl | `companions/by_species/owls/` | 96 | Wise/celestial (Talonmere, Moonvigil) |
| Penguin | `companions/by_species/penguins/` | 96 | Noble/frost (Frosthelm, Glaciermane) |
| Rabbit | `companions/by_species/rabbits/` | 96 | Swift/wind (Swifthare, Veloxfoot) |
| Robot | `companions/by_species/robots/` | 96 | Metal/forge (Ferronax, Voltarian) |
| Snail | `companions/by_species/snails/` | 96 | Nature/gentle (Dewglimmer, Spiralwind) |
| Turtle | `companions/by_species/turtles/` | 96 | Earthen/stoic (Stoneguard, Boulderheart) |

Each species has **48 normal + 48 shiny** variants covering every eye x hat visual combination.

### By Rarity

| Rarity | Folder | Count | Per Species |
|--------|--------|:-----:|:-----------:|
| Uncommon ★★ | `companions/by_rarity/uncommon/` | 36 | 1 normal + 1 shiny |
| Rare ★★★ | `companions/by_rarity/rare/` | 36 | 1 normal + 1 shiny |
| Epic ★★★★ | `companions/by_rarity/epic/` | 36 | 1 normal + 1 shiny |

Best stats selected from 20-50M generated companions per rarity tier. Each has a hand-written name and unique personality.

### Featured Companions

9 companions at the top level of `companions/`:

| Name | Species | Rarity | Notes |
|------|---------|--------|-------|
| Eldûrion | Dragon | Legendary | ◉ halo, WISDOM 100, total 379 |
| Vyrenth | Dragon | Legendary | ✦ wizard, PATIENCE 100 |
| Thistlewing | Owl | Uncommon | Original companion |
| Thunderthistl | Owl | Uncommon | Current companion |
| Anarathil | Dragon | Legendary | ✦ tophat, WISDOM 100 |
| Morgrath | Dragon | Legendary | ◉ crown, CHAOS 100 |
| Ithrandûr | Dragon | Legendary | × wizard, DEBUGGING 100 |
| Faelindor | Dragon | Legendary | ° tinyduck, WISDOM 100 |
| Thráindar | Dragon | Legendary | @ tophat, SNARK 100 |

### Visual Combos

Every companion has a unique combination of:

- **6 eyes:** · ✦ × ◉ @ °
- **8 hats:** none, crown, tophat, propeller, halo, wizard, beanie, tinyduck
- **Shiny:** elvish prefixes (Aur-, Gîl-, Mîr-, Ithil-, Anar-, Lúth-, Cael-, Thal-)

### Per-Companion Files

Each companion folder contains 4 files:

| File | Contents |
|------|----------|
| `buddy.json` | Full profile: name, personality, bones, stats, peak/dump stat |
| `companion.json` | Install config: name, personality, hatchedAt |
| `sprite.txt` | ASCII art animation frames (idle, alt, wink, sleeping) |
| `stats.txt` | Visual stat bars with peak/dump markers |

### Reference Guides

All species reference guides are in [`companions/info/`](companions/info/) with full tables of all companions, their visual combos, stats, and top 5 rankings.

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
- Recursively scans subdirectories
- Creates backups before any modification
- Rejects compiled binaries (requires npm install)
- Backup-based restore via `--restore`

See [`patcher-test/README.md`](patcher-test/README.md) for full docs.

## Hash Algorithms

Claude Code uses different hash algorithms depending on the runtime:

| Runtime | Hash | Patcher flag | How to install |
|---------|------|:------------:|---------------|
| Bun (default) | wyhash | `--wyhash` | Comes with Claude Code desktop app |
| Node.js | FNV-1a | `--fnv1a` | `npm install -g @anthropic-ai/claude-code` |

The same salt produces **different companions** under different hashes. Use `--detect-hash` to see what each algorithm produces for your account, then compare with your current companion to determine which is active.

**Important:** Compiled binaries (desktop app) cannot be patched — byte replacement corrupts their integrity checksums. Install via npm to get a patchable `cli.js`. If you previously used the desktop app (Bun/wyhash), note that npm installs use Node.js (FNV-1a) — you must use the correct hash flag when patching.

## Repo Structure

```
claude-buddies/
├── companions/
│   ├── eldurion/              Featured companions (top level)
│   ├── vyrenth/
│   ├── thistlewing/
│   ├── ...
│   ├── info/                  Species reference guides
│   │   ├── dragons.md
│   │   ├── ducks.md
│   │   └── ...
│   ├── by_species/            Legendary collections (18 species × 96)
│   │   ├── dragons/
│   │   ├── ducks/
│   │   └── ...
│   └── by_rarity/             Uncommon, rare, and epic collections
│       ├── uncommon/          36 companions (2 per species)
│       ├── rare/              36 companions (2 per species)
│       └── epic/              36 companions (2 per species)
├── patcher-test/              Companion patcher (Bun + Python)
├── bun-wyhash-generator/      Bun buddy generator
├── generator/                 Python buddy generator
├── instructions/              LLM extraction guide
├── for_llm.txt                Full project context for LLMs
├── install.sh                 Quick installer
├── species.md                 Species & rarity reference
└── README.md
```
