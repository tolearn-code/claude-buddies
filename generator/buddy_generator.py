#!/usr/bin/env python3
"""
Self-contained buddy generator for Claude Code companions.
Reproduces the exact same deterministic roll as any-buddy using FNV-1a hash.

Usage:
    python buddy_generator.py <accountUuid> [salt]

If salt is omitted, defaults to 'friend-2026-401' (Claude Code original).

Output: JSON with full buddy profile + ASCII sprite frames.

Note: This uses FNV-1a hashing (same as any-buddy on Node.js).
      If the Claude Code install uses Bun runtime, the hash algorithm
      is wyhash and results will differ. See --wyhash flag below.
"""

import json
import sys
import os
import subprocess
import shutil

# ── Constants ──

ORIGINAL_SALT = "friend-2026-401"

RARITIES = ["common", "uncommon", "rare", "epic", "legendary"]

RARITY_WEIGHTS = {
    "common": 60,
    "uncommon": 25,
    "rare": 10,
    "epic": 4,
    "legendary": 1,
}

RARITY_FLOOR = {
    "common": 5,
    "uncommon": 15,
    "rare": 25,
    "epic": 35,
    "legendary": 50,
}

RARITY_STARS = {
    "common": "★",
    "uncommon": "★★",
    "rare": "★★★",
    "epic": "★★★★",
    "legendary": "★★★★★",
}

SPECIES = [
    "duck", "goose", "blob", "cat", "dragon", "octopus",
    "owl", "penguin", "turtle", "snail", "ghost", "axolotl",
    "capybara", "cactus", "robot", "rabbit", "mushroom", "chonk",
]

EYES = ["·", "✦", "×", "◉", "@", "°"]

HATS = ["none", "crown", "tophat", "propeller", "halo", "wizard", "beanie", "tinyduck"]

STAT_NAMES = ["DEBUGGING", "PATIENCE", "CHAOS", "WISDOM", "SNARK"]

DEFAULT_PERSONALITIES = {
    "duck": "A cheerful quacker who celebrates your wins with enthusiastic honks and judges your variable names with quiet side-eye.",
    "goose": "An agent of chaos who thrives on your merge conflicts and honks menacingly whenever you write a TODO comment.",
    "blob": "A formless, chill companion who absorbs your stress and responds to everything with gentle, unhurried wisdom.",
    "cat": "An aloof code reviewer who pretends not to care about your bugs but quietly bats at syntax errors when you're not looking.",
    "dragon": "A fierce guardian of clean code who breathes fire at spaghetti logic and hoards well-written functions.",
    "octopus": "A multitasking genius who juggles eight concerns at once and offers tentacle-loads of unsolicited architectural advice.",
    "owl": "A nocturnal sage who comes alive during late-night debugging sessions and asks annoyingly insightful questions.",
    "penguin": "A tuxedo-wearing professional who waddles through your codebase with dignified concern and dry wit.",
    "turtle": "A patient mentor who reminds you that slow, steady refactoring beats heroic rewrites every time.",
    "snail": "A zen minimalist who moves at their own pace and leaves a trail of thoughtful, unhurried observations.",
    "ghost": "A spectral presence who haunts your dead code and whispers about the bugs you thought you fixed.",
    "axolotl": "A regenerative optimist who believes every broken build can be healed and every test can be unflaked.",
    "capybara": "The most relaxed companion possible — nothing fazes them, not even production outages at 3am.",
    "cactus": "A prickly but lovable desert dweller who thrives on neglect and offers sharp, pointed feedback.",
    "robot": "A logical companion who speaks in precise technical observations and occasionally glitches endearingly.",
    "rabbit": "A fast-moving, hyperactive buddy who speed-reads your diffs and bounces between topics at alarming pace.",
    "mushroom": "A wry fungal sage who speaks in meandering tangents about your bugs while secretly enjoying the chaos.",
    "chonk": "An absolute unit of a companion who sits on your terminal with maximum gravitational presence and minimal urgency.",
}

# ── Sprite Data ──

BODIES = {
    "duck": [
        ["            ", "    __      ", "  <({E} )___  ", "   (  ._>   ", "    `--´    "],
        ["            ", "    __      ", "  <({E} )___  ", "   (  ._>   ", "    `--´~   "],
        ["            ", "    __      ", "  <({E} )___  ", "   (  .__>  ", "    `--´    "],
    ],
    "goose": [
        ["            ", "     ({E}>    ", "     ||     ", "   _(__)_   ", "    ^^^^    "],
        ["            ", "    ({E}>     ", "     ||     ", "   _(__)_   ", "    ^^^^    "],
        ["            ", "     ({E}>>   ", "     ||     ", "   _(__)_   ", "    ^^^^    "],
    ],
    "blob": [
        ["            ", "   .----.   ", "  ( {E}  {E} )  ", "  (      )  ", "   `----´   "],
        ["            ", "  .------.  ", " (  {E}  {E}  ) ", " (        ) ", "  `------´  "],
        ["            ", "    .--.    ", "   ({E}  {E})   ", "   (    )   ", "    `--´    "],
    ],
    "cat": [
        ["            ", "   /\\_/\\    ", "  ( {E}   {E})  ", "  (  ω  )   ", '  (")_(")   '],
        ["            ", "   /\\_/\\    ", "  ( {E}   {E})  ", "  (  ω  )   ", '  (")_(")~  '],
        ["            ", "   /\\-/\\    ", "  ( {E}   {E})  ", "  (  ω  )   ", '  (")_(")   '],
    ],
    "dragon": [
        ["            ", "  /^\\  /^\\  ", " <  {E}  {E}  > ", " (   ~~   ) ", "  `-vvvv-´  "],
        ["            ", "  /^\\  /^\\  ", " <  {E}  {E}  > ", " (        ) ", "  `-vvvv-´  "],
        ["   ~    ~   ", "  /^\\  /^\\  ", " <  {E}  {E}  > ", " (   ~~   ) ", "  `-vvvv-´  "],
    ],
    "octopus": [
        ["            ", "   .----.   ", "  ( {E}  {E} )  ", "  (______)  ", "  /\\/\\/\\/\\  "],
        ["            ", "   .----.   ", "  ( {E}  {E} )  ", "  (______)  ", "  \\/\\/\\/\\/  "],
        ["     o      ", "   .----.   ", "  ( {E}  {E} )  ", "  (______)  ", "  /\\/\\/\\/\\  "],
    ],
    "owl": [
        ["            ", "   /\\  /\\   ", "  (({E})({E}))  ", "  (  ><  )  ", "   `----´   "],
        ["            ", "   /\\  /\\   ", "  (({E})({E}))  ", "  (  ><  )  ", "   .----.   "],
        ["            ", "   /\\  /\\   ", "  (({E})(-))  ", "  (  ><  )  ", "   `----´   "],
    ],
    "penguin": [
        ["            ", "  .---.     ", "  ({E}>{E})     ", " /(   )\\    ", "  `---´     "],
        ["            ", "  .---.     ", "  ({E}>{E})     ", " |(   )|    ", "  `---´     "],
        ["  .---.     ", "  ({E}>{E})     ", " /(   )\\    ", "  `---´     ", "   ~ ~      "],
    ],
    "turtle": [
        ["            ", "   _,--._   ", "  ( {E}  {E} )  ", " /[______]\\ ", "  ``    ``  "],
        ["            ", "   _,--._   ", "  ( {E}  {E} )  ", " /[______]\\ ", "   ``  ``   "],
        ["            ", "   _,--._   ", "  ( {E}  {E} )  ", " /[======]\\ ", "  ``    ``  "],
    ],
    "snail": [
        ["            ", " {E}    .--.  ", "  \\  ( @ )  ", "   \\_`--´   ", "  ~~~~~~~   "],
        ["            ", "  {E}   .--.  ", "  |  ( @ )  ", "   \\_`--´   ", "  ~~~~~~~   "],
        ["            ", " {E}    .--.  ", "  \\  ( @  ) ", "   \\_`--´   ", "   ~~~~~~   "],
    ],
    "ghost": [
        ["            ", "   .----.   ", "  / {E}  {E} \\  ", "  |      |  ", "  ~`~``~`~  "],
        ["            ", "   .----.   ", "  / {E}  {E} \\  ", "  |      |  ", "  `~`~~`~`  "],
        ["    ~  ~    ", "   .----.   ", "  / {E}  {E} \\  ", "  |      |  ", "  ~~`~~`~~  "],
    ],
    "axolotl": [
        ["            ", "}~(______)~{", "}~({E} .. {E})~{", "  ( .--. )  ", "  (_/  \\_)  "],
        ["            ", "~}(______){~", "~}({E} .. {E}){~", "  ( .--. )  ", "  (_/  \\_)  "],
        ["            ", "}~(______)~{", "}~({E} .. {E})~{", "  (  --  )  ", "  ~_/  \\_~  "],
    ],
    "capybara": [
        ["            ", "  n______n  ", " ( {E}    {E} ) ", " (   oo   ) ", "  `------´  "],
        ["            ", "  n______n  ", " ( {E}    {E} ) ", " (   Oo   ) ", "  `------´  "],
        ["    ~  ~    ", "  u______n  ", " ( {E}    {E} ) ", " (   oo   ) ", "  `------´  "],
    ],
    "cactus": [
        ["            ", " n  ____  n ", " | |{E}  {E}| | ", " |_|    |_| ", "   |    |   "],
        ["            ", "    ____    ", " n |{E}  {E}| n ", " |_|    |_| ", "   |    |   "],
        [" n        n ", " |  ____  | ", " | |{E}  {E}| | ", " |_|    |_| ", "   |    |   "],
    ],
    "robot": [
        ["            ", "   .[||].   ", "  [ {E}  {E} ]  ", "  [ ==== ]  ", "  `------´  "],
        ["            ", "   .[||].   ", "  [ {E}  {E} ]  ", "  [ -==- ]  ", "  `------´  "],
        ["     *      ", "   .[||].   ", "  [ {E}  {E} ]  ", "  [ ==== ]  ", "  `------´  "],
    ],
    "rabbit": [
        ["            ", "   (\\__/)   ", "  ( {E}  {E} )  ", " =(  ..  )= ", '  (")__(")  '],
        ["            ", "   (|__/)   ", "  ( {E}  {E} )  ", " =(  ..  )= ", '  (")__(")  '],
        ["            ", "   (\\__/)   ", "  ( {E}  {E} )  ", " =( .  . )= ", '  (")__(")  '],
    ],
    "mushroom": [
        ["            ", " .-o-OO-o-. ", "(__________)", "   |{E}  {E}|   ", "   |____|   "],
        ["            ", " .-O-oo-O-. ", "(__________)", "   |{E}  {E}|   ", "   |____|   "],
        ["   . o  .   ", " .-o-OO-o-. ", "(__________)", "   |{E}  {E}|   ", "   |____|   "],
    ],
    "chonk": [
        ["            ", "  /\\    /\\  ", " ( {E}    {E} ) ", " (   ..   ) ", "  `------´  "],
        ["            ", "  /\\    /|  ", " ( {E}    {E} ) ", " (   ..   ) ", "  `------´  "],
        ["            ", "  /\\    /\\  ", " ( {E}    {E} ) ", " (   ..   ) ", "  `------´~ "],
    ],
}

HAT_LINES = {
    "none": "",
    "crown": "   \\^^^/    ",
    "tophat": "   [___]    ",
    "propeller": "    -+-     ",
    "halo": "   (   )    ",
    "wizard": "    /^\\     ",
    "beanie": "   (___)    ",
    "tinyduck": "    ,>      ",
}

# ── Hash Functions ──

def fnv1a(s: str) -> int:
    """FNV-1a hash (same as any-buddy Node.js fallback)."""
    h = 2166136261
    for ch in s:
        h ^= ord(ch)
        h = (h * 16777619) & 0xFFFFFFFF
    return h


def wyhash_via_bun(s: str) -> int:
    """Use Bun.hash (wyhash) by shelling out to bun."""
    bun = shutil.which("bun")
    if not bun:
        raise RuntimeError("Bun not found. Install bun or use --fnv1a flag.")
    result = subprocess.run(
        [bun, "-e",
         'const s=await Bun.stdin.text();process.stdout.write(String(Number(BigInt(Bun.hash(s))&0xffffffffn)))'],
        input=s, capture_output=True, text=True, timeout=5
    )
    return int(result.stdout.strip())


# ── RNG ──

def mulberry32(seed: int):
    """Mulberry32 PRNG — identical to any-buddy's JS implementation."""
    a = seed & 0xFFFFFFFF

    def _ctypes_imul(a_val, b_val):
        """Replicate Math.imul: 32-bit integer multiply."""
        a_val &= 0xFFFFFFFF
        b_val &= 0xFFFFFFFF
        result = (a_val * b_val) & 0xFFFFFFFF
        if result >= 0x80000000:
            result -= 0x100000000
        return result

    def rng():
        nonlocal a
        # a |= 0  (convert to signed 32-bit)
        a = a & 0xFFFFFFFF
        if a >= 0x80000000:
            a_signed = a - 0x100000000
        else:
            a_signed = a

        a_signed = (a_signed + 0x6D2B79F5) | 0
        # Handle JS |0 semantics (signed 32-bit truncation)
        a_signed = a_signed & 0xFFFFFFFF
        if a_signed >= 0x80000000:
            a_signed -= 0x100000000

        a = a_signed & 0xFFFFFFFF

        t = _ctypes_imul(a_signed ^ ((a & 0xFFFFFFFF) >> 15), 1 | a_signed)
        # Convert t to signed
        t = t & 0xFFFFFFFF
        if t >= 0x80000000:
            t -= 0x100000000

        t2 = _ctypes_imul(t ^ (((t & 0xFFFFFFFF) >> 7)), 61 | t)
        t2 = t2 & 0xFFFFFFFF
        if t2 >= 0x80000000:
            t2 -= 0x100000000

        t = (t + t2) ^ t
        t = t & 0xFFFFFFFF
        if t >= 0x80000000:
            t -= 0x100000000

        result = ((t ^ (((t & 0xFFFFFFFF) >> 14))) & 0xFFFFFFFF) / 4294967296
        return result

    return rng


def pick(rng, arr):
    """Pick a random element from array using rng."""
    import math
    return arr[math.floor(rng() * len(arr))]


# ── Roll ──

def roll_rarity(rng):
    total = sum(RARITY_WEIGHTS.values())
    r = rng() * total
    for rarity in RARITIES:
        r -= RARITY_WEIGHTS[rarity]
        if r < 0:
            return rarity
    return "common"


def roll_stats(rng, rarity):
    import math
    floor = RARITY_FLOOR[rarity]
    peak = pick(rng, STAT_NAMES)
    dump = pick(rng, STAT_NAMES)
    while dump == peak:
        dump = pick(rng, STAT_NAMES)

    stats = {}
    for name in STAT_NAMES:
        if name == peak:
            stats[name] = min(100, floor + 50 + math.floor(rng() * 30))
        elif name == dump:
            stats[name] = max(1, floor - 10 + math.floor(rng() * 15))
        else:
            stats[name] = floor + math.floor(rng() * 40)
    return stats


def roll(user_id: str, salt: str, use_fnv1a: bool = True) -> dict:
    """Roll a buddy from userId + salt. Returns full RollResult."""
    import math
    key = user_id + salt
    if use_fnv1a:
        h = fnv1a(key)
    else:
        h = wyhash_via_bun(key)

    rng = mulberry32(h)
    rarity = roll_rarity(rng)

    bones = {
        "rarity": rarity,
        "species": pick(rng, SPECIES),
        "eye": pick(rng, EYES),
        "hat": "none" if rarity == "common" else pick(rng, HATS),
        "shiny": rng() < 0.01,
        "stats": roll_stats(rng, rarity),
    }

    inspiration_seed = math.floor(rng() * 1e9)
    return {"bones": bones, "inspirationSeed": inspiration_seed}


# ── Sprite Rendering ──

def render_sprite(bones: dict, frame: int = 0, sleeping: bool = False) -> list:
    species = bones["species"]
    frames = BODIES[species]
    eye = "-" if sleeping else bones["eye"]
    body = [line.replace("{E}", eye) for line in frames[frame % len(frames)]]
    lines = list(body)

    if bones["hat"] != "none" and not lines[0].strip():
        lines[0] = HAT_LINES[bones["hat"]]

    if not lines[0].strip() and all(not f[0].strip() for f in frames):
        lines.pop(0)

    return lines


def render_all_frames(bones: dict) -> str:
    output = []
    species = bones["species"]
    labels = ["idle", "idle alt", "wink"]

    for i in range(len(BODIES[species])):
        output.append(f"--- Frame {i} ({labels[i] if i < len(labels) else 'alt'}) ---")
        for line in render_sprite(bones, i, False):
            output.append(line)
        output.append("")

    output.append("--- Sleeping ---")
    for line in render_sprite(bones, 0, True):
        output.append(line)

    return "\n".join(output)


# ── Output ──

def generate_buddy_files(user_id: str, salt: str, use_fnv1a: bool, output_dir: str = None):
    """Generate all buddy files (buddy.json, companion.json, sprite.txt)."""
    result = roll(user_id, salt, use_fnv1a)
    bones = result["bones"]
    species = bones["species"]

    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    buddy_data = {
        "name": species.capitalize(),
        "defaultPersonality": DEFAULT_PERSONALITIES[species],
        "salt": salt,
        "bones": bones,
        "inspirationSeed": result["inspirationSeed"],
    }

    companion_data = {
        "name": species.capitalize(),
        "personality": DEFAULT_PERSONALITIES[species],
    }

    sprite_text = (
        f"{species.capitalize()} — {bones['rarity'].capitalize()} {species.capitalize()} "
        f"({RARITY_STARS[bones['rarity']]})\n"
        f"Eyes: {bones['eye']} | Hat: {bones['hat']} | Shiny: {'yes' if bones['shiny'] else 'no'}\n\n"
        f"{render_all_frames(bones)}"
    )

    if output_dir:
        with open(os.path.join(output_dir, "buddy.json"), "w") as f:
            json.dump(buddy_data, f, indent=2, ensure_ascii=False)
        with open(os.path.join(output_dir, "companion.json"), "w") as f:
            json.dump(companion_data, f, indent=2, ensure_ascii=False)
        with open(os.path.join(output_dir, "sprite.txt"), "w") as f:
            f.write(sprite_text + "\n")
        print(f"Files saved to {output_dir}/")
    else:
        print(json.dumps(buddy_data, indent=2, ensure_ascii=False))

    return buddy_data, companion_data, sprite_text


def print_buddy(user_id: str, salt: str, use_fnv1a: bool):
    """Print buddy info to stdout."""
    result = roll(user_id, salt, use_fnv1a)
    bones = result["bones"]
    species = bones["species"]

    hash_type = "FNV-1a" if use_fnv1a else "wyhash (Bun)"

    print(f"\n  {species.capitalize()} — {bones['rarity'].capitalize()} {RARITY_STARS[bones['rarity']]}")
    print(f"  Eye: {bones['eye']}  Hat: {bones['hat']}  Shiny: {'yes' if bones['shiny'] else 'no'}")
    print(f"  Hash: {hash_type}")
    print()

    for line in render_sprite(bones, 0, False):
        print(f"  {line}")
    print()

    print("  Stats:")
    for stat, val in bones["stats"].items():
        bar = "█" * (val // 5) + "░" * (20 - val // 5)
        print(f"    {stat:<10} {bar} {val}")

    print(f"\n  Personality: {DEFAULT_PERSONALITIES[species]}")
    print()


# ── CLI ──

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate Claude Code buddy profiles from userId + salt"
    )
    parser.add_argument("user_id", help="accountUuid from ~/.claude.json")
    parser.add_argument("salt", nargs="?", default=ORIGINAL_SALT,
                        help=f"Salt string (default: {ORIGINAL_SALT})")
    parser.add_argument("--fnv1a", action="store_true", default=True,
                        help="Use FNV-1a hash (default, Node.js compatible)")
    parser.add_argument("--wyhash", action="store_true",
                        help="Use wyhash via Bun (requires bun installed)")
    parser.add_argument("-o", "--output", metavar="DIR",
                        help="Output directory for buddy files")
    parser.add_argument("--json", action="store_true",
                        help="Output raw JSON only")

    args = parser.parse_args()
    use_fnv1a = not args.wyhash

    if args.output:
        generate_buddy_files(args.user_id, args.salt, use_fnv1a, args.output)
    elif args.json:
        result = roll(args.user_id, args.salt, use_fnv1a)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print_buddy(args.user_id, args.salt, use_fnv1a)


if __name__ == "__main__":
    main()
