#!/usr/bin/env python3
"""
Animated companion viewer — pure Python, no external libraries.

Controls:
  ← / → or a/d   Browse companions (prev / next)
  ↑ / ↓           Jump 10 companions
  e / q            Cycle rarity filter
  w / s            Cycle species filter
  x                Exit

Usage:
  python3 viewer.py                     # browse all
  python3 viewer.py --core              # core companions only
  python3 viewer.py --start eldurion    # start at companion
  python3 viewer.py --delay 0.5         # faster animation
"""

import json
import os
import sys
import time
import select
import termios
import tty
from pathlib import Path

# ── Config ──
REPO = Path("/home/sprite/claude-buddies")
CARD_WIDTH = 68
LEFT_PAD = "          "  # 10 chars
FRAME_DELAY = 0.8
CLR = "\033[K"

# ── ANSI color helpers (no libraries needed) ──
def rgb(r, g, b):
    """Return a function that wraps text in RGB color."""
    def colorize(text):
        return f"\033[38;2;{r};{g};{b}m{text}\033[0m"
    return colorize

def bold_white(text):
    return f"\033[1;37m{text}\033[0m"

def dim_text(text):
    return f"\033[38;2;136;136;136m{text}\033[0m"

# ── Rarity color themes ──
RARITY_THEMES = {
    "common":    {"border": rgb(158, 158, 158), "accent": rgb(189, 189, 189), "sprite": rgb(176, 176, 176)},
    "uncommon":  {"border": rgb(76, 175, 80),   "accent": rgb(129, 199, 132), "sprite": rgb(165, 214, 167)},
    "rare":      {"border": rgb(33, 150, 243),  "accent": rgb(100, 181, 246), "sprite": rgb(144, 202, 249)},
    "epic":      {"border": rgb(156, 39, 176),  "accent": rgb(206, 147, 216), "sprite": rgb(225, 190, 231)},
    "legendary": {"border": rgb(215, 119, 87),  "accent": rgb(255, 193, 7),   "sprite": rgb(255, 193, 7)},
}

RARITY_STARS = {
    "common": "★", "uncommon": "★★", "rare": "★★★", "epic": "★★★★", "legendary": "★★★★★"
}

ALL_SPECIES = ["all", "axolotl", "blob", "cactus", "capybara", "cat", "chonk", "dragon",
               "duck", "ghost", "goose", "mushroom", "octopus", "owl", "penguin", "rabbit",
               "robot", "snail", "turtle"]
ALL_RARITIES = ["all", "common", "uncommon", "rare", "epic", "legendary"]

# ── Terminal helpers ──
def hide_cursor():
    sys.stdout.write("\033[?25l")
    sys.stdout.flush()

def show_cursor():
    sys.stdout.write("\033[?25h")
    sys.stdout.flush()

def move_to(row, col):
    sys.stdout.write(f"\033[{row};{col}H")

def clear_screen():
    sys.stdout.write("\033[2J")
    move_to(1, 1)
    sys.stdout.flush()

def visual_width(s):
    """Count terminal columns — wide chars (emoji) count as 2."""
    w = 0
    for ch in s:
        if ch in ("✨", "💤", "●"):
            w += 2
        else:
            w += 1
    return w

# ── Load companions ──
def load_companions(core_only=False):
    CORE = {"anarathil", "eldurion", "faelindor", "ithrandur", "morgrath",
            "thistlewing", "thunderthistl", "vyrenth"}
    companions = []
    comp_dir = REPO / "companions"
    for buddy_path in sorted(comp_dir.rglob("buddy.json")):
        folder = buddy_path.parent.name
        if folder == "info":
            continue
        try:
            data = json.loads(buddy_path.read_text())
            bones = data["bones"]
            companions.append({
                "folder": folder,
                "name": data["name"],
                "personality": data.get("personality", ""),
                "species": bones["species"],
                "rarity": bones["rarity"],
                "eye": bones["eye"],
                "hat": bones["hat"],
                "shiny": bones.get("shiny", False),
                "stats": bones["stats"],
                "peakStat": data.get("peakStat", ""),
                "dumpStat": data.get("dumpStat", ""),
                "sprite_file": buddy_path.parent / "sprite.txt",
            })
        except (json.JSONDecodeError, KeyError):
            continue

    if core_only:
        companions = [c for c in companions if c["folder"] in CORE]
    return companions

def get_frame(sprite_file, frame_num, sleeping=False):
    """Extract a frame from sprite.txt."""
    if not sprite_file.exists():
        return [""] * 5
    text = sprite_file.read_text()
    if sleeping:
        label = "Sleeping"
    else:
        label = f"Frame {frame_num}"

    lines = []
    capturing = False
    for line in text.split("\n"):
        if f"--- {label}" in line:
            capturing = True
            continue
        if capturing:
            if line.startswith("---") or (line.strip() == "" and len(lines) >= 4):
                break
            lines.append(line)
    return (lines + [""] * 5)[:5]

# ── Stat bar ──
def stat_bar(val):
    filled = val // 5
    empty = 20 - filled
    return "█" * filled + "░" * empty

# ── Render card ──
def render_card(comp, frame_lines, sleeping, index, total, species_idx, rarity_idx, core_only):
    theme = RARITY_THEMES.get(comp["rarity"], RARITY_THEMES["legendary"])
    b = theme["border"]
    a = theme["accent"]
    s = theme["sprite"]
    cyan = rgb(130, 170, 220)
    green = rgb(147, 200, 130)

    hline = "─" * CARD_WIDTH
    blank = " " * CARD_WIDTH
    nav = f"{index + 1}/{total}"
    stars = RARITY_STARS.get(comp["rarity"], "?")
    species_upper = comp["species"].upper()
    rarity_upper = comp["rarity"].upper()
    shiny_tag = " ✨" if comp["shiny"] else ""

    lines = []

    # Top border
    lines.append(f"{LEFT_PAD}{b('╭' + hline + '╮')}")

    # Header
    header_left = f"{stars}  {rarity_upper}"
    gap = CARD_WIDTH - 2 - len(header_left) - len(species_upper)
    lines.append(f"{LEFT_PAD}{b('│')} {a(header_left)}{' ' * max(0, gap)}{cyan(species_upper)} {b('│')}{CLR}")

    # Blank
    lines.append(f"{LEFT_PAD}{b('│')}{blank}{b('│')}{CLR}")

    # Sprite (5 lines)
    for i in range(5):
        sprite_line = frame_lines[i] if i < len(frame_lines) else ""
        vw = visual_width(sprite_line)
        pad = max(0, CARD_WIDTH - 1 - vw)
        lines.append(f"{LEFT_PAD}{b('│')} {s(sprite_line)}{' ' * pad}{b('│')}{CLR}")

    # Blank
    lines.append(f"{LEFT_PAD}{b('│')}{blank}{b('│')}{CLR}")

    # Name
    name_display = f"{comp['name']}{shiny_tag}"
    vw = visual_width(name_display)
    pad = max(0, CARD_WIDTH - 1 - vw)
    lines.append(f"{LEFT_PAD}{b('│')} {bold_white(name_display)}{' ' * pad}{b('│')}{CLR}")

    # Blank
    lines.append(f"{LEFT_PAD}{b('│')}{blank}{b('│')}{CLR}")

    # Personality (3 lines word-wrapped)
    max_pw = CARD_WIDTH - 4
    words = comp["personality"].split()
    p_lines = []
    current = ""
    for word in words:
        if len(current) + len(word) + 1 > max_pw:
            p_lines.append(current)
            current = word
        else:
            current = f"{current} {word}" if current else word
    if current:
        p_lines.append(current)
    for pl in p_lines[:3]:
        pad = max(0, CARD_WIDTH - 1 - len(pl))
        lines.append(f"{LEFT_PAD}{b('│')} {dim_text(pl)}{' ' * pad}{b('│')}{CLR}")

    # Blank
    lines.append(f"{LEFT_PAD}{b('│')}{blank}{b('│')}{CLR}")

    # Stats
    for stat_name in ["DEBUGGING", "PATIENCE", "CHAOS", "WISDOM", "SNARK"]:
        val = comp["stats"].get(stat_name, 0)
        bar = stat_bar(val)
        suffix = ""
        if stat_name == comp["peakStat"]:
            suffix = " (peak)"
        elif stat_name == comp["dumpStat"]:
            suffix = " (dump)"
        vis_w = 2 + 10 + 1 + 20 + 1 + 3 + len(suffix) + 2
        right_pad = max(0, CARD_WIDTH - vis_w)
        stat_line = f"  {a(stat_name.ljust(10))} {bold_white(bar)} {dim_text(str(val).rjust(3))}{dim_text(suffix)}{' ' * right_pad}  "
        lines.append(f"{LEFT_PAD}{b('│')}{stat_line}{b('│')}{CLR}")

    # Blank
    lines.append(f"{LEFT_PAD}{b('│')}{blank}{b('│')}{CLR}")

    # Status
    if sleeping:
        pad = max(0, CARD_WIDTH - 17)
        lines.append(f"{LEFT_PAD}{b('│')}  {dim_text('💤 sleeping...')}{' ' * pad}{b('│')}{CLR}")
    else:
        pad = max(0, CARD_WIDTH - 11)
        lines.append(f"{LEFT_PAD}{b('│')}  {green('● online')}{' ' * pad}{b('│')}{CLR}")

    # Bottom border
    lines.append(f"{LEFT_PAD}{b('╰' + hline + '╯')}")
    lines.append("")

    # Footer
    lines.append(f"{LEFT_PAD}  {dim_text('a/← prev')}  {bold_white(f'[ {nav} ]')}  {dim_text('d/→ next')}  {dim_text('↑↓ jump')}  {dim_text('x exit')}{CLR}")
    if not core_only:
        sp = ALL_SPECIES[species_idx]
        ra = ALL_RARITIES[rarity_idx]
        lines.append(f"{LEFT_PAD}  {dim_text('Species:')} {cyan(sp)} {dim_text('(w/s)')}  {dim_text('Rarity:')} {cyan(ra)} {dim_text('(q/e)')}  {dim_text(comp['folder'])}{CLR}")

    return "\r\n".join(lines)

# ── Input ──
def get_key(timeout):
    """Non-blocking key read with timeout."""
    if select.select([sys.stdin], [], [], timeout)[0]:
        ch = sys.stdin.read(1)
        if ch == "\033":
            if select.select([sys.stdin], [], [], 0.05)[0]:
                ch += sys.stdin.read(2)
        return ch
    return None

# ── Main ──
def main():
    args = sys.argv[1:]
    core_only = "--core" in args
    delay = FRAME_DELAY
    start_at = ""

    for i, arg in enumerate(args):
        if arg == "--delay" and i + 1 < len(args):
            delay = float(args[i + 1])
        elif arg == "--start" and i + 1 < len(args):
            start_at = args[i + 1]

    print("Loading companions...")
    companions = load_companions(core_only)
    print(f"Loaded {len(companions)} companions.")

    if not companions:
        print("No companions found!")
        return

    # Filters
    species_idx = 0
    rarity_idx = 0

    def build_filtered():
        sp = ALL_SPECIES[species_idx]
        ra = ALL_RARITIES[rarity_idx]
        return [c for c in companions
                if (sp == "all" or c["species"] == sp)
                and (ra == "all" or c["rarity"] == ra)]

    filtered = build_filtered()
    index = 0

    # Find start companion
    if start_at:
        for i, c in enumerate(filtered):
            if c["folder"] == start_at:
                index = i
                break

    # Terminal setup
    old_settings = termios.tcgetattr(sys.stdin)
    try:
        tty.setraw(sys.stdin.fileno())
        hide_cursor()
        clear_screen()

        frame = 0
        need_reload = True

        while True:
            if need_reload:
                filtered = build_filtered()
                if index >= len(filtered):
                    index = 0
                if index < 0:
                    index = len(filtered) - 1
                need_reload = False
                frame = 0

            if not filtered:
                move_to(1, 1)
                orange = rgb(215, 119, 87)
                hline = "─" * CARD_WIDTH
                blank = " " * CARD_WIDTH
                sys.stdout.write(f"{LEFT_PAD}{orange('╭' + hline + '╮')}\r\n")
                sys.stdout.write(f"{LEFT_PAD}{orange('│')}{blank}{orange('│')}\r\n")
                msg = "No companions match filters"
                p = (CARD_WIDTH - len(msg)) // 2
                sys.stdout.write(f"{LEFT_PAD}{orange('│')}{' ' * p}{rgb(255,107,128)(msg)}{' ' * (CARD_WIDTH - p - len(msg))}{orange('│')}\r\n")
                sys.stdout.write(f"{LEFT_PAD}{orange('│')}{blank}{orange('│')}\r\n")
                sys.stdout.write(f"{LEFT_PAD}{orange('╰' + hline + '╯')}\r\n")
                sys.stdout.flush()
            else:
                comp = filtered[index]

                # Get frame
                if frame in (0, 1, 3, 4):
                    fl = get_frame(comp["sprite_file"], frame % 2, False)
                    sleeping = False
                elif frame == 2:
                    fl = get_frame(comp["sprite_file"], 2, False)
                    sleeping = False
                else:  # frame == 5
                    fl = get_frame(comp["sprite_file"], 0, True)
                    sleeping = True

                move_to(1, 1)
                output = render_card(comp, fl, sleeping, index, len(filtered),
                                     species_idx, rarity_idx, core_only)
                sys.stdout.write(output)
                sys.stdout.flush()

            # Input
            key = get_key(delay)
            if key:
                if key in ("x", "X"):
                    break
                elif key in ("\033[D", "a", "A"):  # Left
                    index = (index - 1) % max(1, len(filtered))
                    need_reload = True
                elif key in ("\033[C", "d", "D"):  # Right
                    index = (index + 1) % max(1, len(filtered))
                    need_reload = True
                elif key == "\033[A":  # Up
                    index = (index - 10) % max(1, len(filtered))
                    need_reload = True
                elif key == "\033[B":  # Down
                    index = (index + 10) % max(1, len(filtered))
                    need_reload = True
                elif key in ("e", "E") and not core_only:
                    rarity_idx = (rarity_idx + 1) % len(ALL_RARITIES)
                    index = 0
                    need_reload = True
                elif key == "q" and not core_only:
                    rarity_idx = (rarity_idx - 1) % len(ALL_RARITIES)
                    index = 0
                    need_reload = True
                elif key in ("s", "S") and not core_only:
                    species_idx = (species_idx + 1) % len(ALL_SPECIES)
                    index = 0
                    need_reload = True
                elif key in ("w", "W") and not core_only:
                    species_idx = (species_idx - 1) % len(ALL_SPECIES)
                    index = 0
                    need_reload = True

            frame = (frame + 1) % 6

    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
        show_cursor()
        clear_screen()
        comp_name = filtered[index]["name"] if filtered else "companion"
        print(f"Goodbye from {comp_name}!")

if __name__ == "__main__":
    main()
