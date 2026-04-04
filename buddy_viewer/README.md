# Buddy Viewer

Browse all 1,845 companions with animated ASCII sprites, rarity-colored cards, stats, and filters.

## Quick Start

```bash
# Python (no dependencies)
python3 buddy_viewer/viewer.py

# Python with Rich (prettier output)
pip install rich
python3 buddy_viewer/viewer_rich.py

# Bun/TypeScript
npm install chalk
bun buddy_viewer/viewer.ts
```

## Requirements

| Viewer | Runtime | Dependencies | Install |
|--------|---------|:------------:|---------|
| `viewer.py` | Python 3.6+ | None | Just run it |
| `viewer_rich.py` | Python 3.7+ | `rich` | `pip install rich` |
| `viewer.ts` | Bun | `chalk` | `npm install chalk` |

## Controls

| Key | Action |
|-----|--------|
| `a` / `←` | Previous companion |
| `d` / `→` | Next companion |
| `↑` | Jump 10 back |
| `↓` | Jump 10 forward |
| `w` / `s` | Cycle species filter |
| `q` / `e` | Cycle rarity filter |
| `x` | Exit |

## Options

```bash
python3 viewer.py                     # browse all 1,845 companions
python3 viewer.py --core              # browse 9 featured companions only
python3 viewer.py --start eldurion    # start at a specific companion
python3 viewer.py --delay 0.5         # faster animation (default 0.8s)
```

Same options work for all three viewers.

## Features

- **Animated sprites** — idle, wink, and sleeping frames cycle automatically
- **Rarity color themes** — grey (common), green (uncommon), blue (rare), purple (epic), gold (legendary)
- **Species filter** — press `s`/`w` to cycle through all 18 species
- **Rarity filter** — press `e`/`q` to cycle through common → legendary
- **Shiny indicator** — ✨ shown next to shiny companion names
- **Full stat display** — DEBUGGING, PATIENCE, CHAOS, WISDOM, SNARK with visual bars
- **Peak/dump markers** — stats show (peak) and (dump) labels

## Which Viewer to Use?

- **`viewer.py`** — works everywhere Python exists, no install needed
- **`viewer_rich.py`** — same features but uses Rich library for better color handling
- **`viewer.ts`** — fastest load time (~2s vs ~3s), best for frequent browsing
