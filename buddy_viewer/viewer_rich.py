#!/usr/bin/env python3
"""
Animated companion viewer using Rich for styling.
Rich handles colors/formatting, we handle terminal output manually.

Controls: a/d or ←/→ browse, ↑/↓ jump 10, w/s species, q/e rarity, x exit

Usage:
  python3 viewer_rich.py
  python3 viewer_rich.py --core
  python3 viewer_rich.py --start eldurion
  python3 viewer_rich.py --delay 0.5
"""

import json, sys, time, select, termios, tty, io
from pathlib import Path
from rich.console import Console
from rich.text import Text
from rich.table import Table
from rich import box

REPO = Path(__file__).resolve().parent.parent
CARD_WIDTH = 68
LEFT_PAD = "          "
FRAME_DELAY = 0.8
CLR = "\033[K"

# Rich console that renders to string (not stdout)
string_console = Console(file=io.StringIO(), width=120, force_terminal=True)

RARITY_STYLES = {
    "common":    {"border": "grey50",    "accent": "grey70",    "sprite": "grey62"},
    "uncommon":  {"border": "green",     "accent": "bright_green", "sprite": "pale_green3"},
    "rare":      {"border": "dodger_blue2", "accent": "sky_blue1", "sprite": "light_sky_blue1"},
    "epic":      {"border": "medium_purple", "accent": "plum2", "sprite": "thistle1"},
    "legendary": {"border": "#D7775B",   "accent": "#FFC107",   "sprite": "#FFC107"},
}
RARITY_STARS = {"common": "★", "uncommon": "★★", "rare": "★★★", "epic": "★★★★", "legendary": "★★★★★"}
ALL_SPECIES = ["all","axolotl","blob","cactus","capybara","cat","chonk","dragon","duck","ghost","goose","mushroom","octopus","owl","penguin","rabbit","robot","snail","turtle"]
ALL_RARITIES = ["all","common","uncommon","rare","epic","legendary"]

def rich_str(text_obj):
    """Render a Rich Text object to an ANSI string."""
    string_console.file = io.StringIO()
    string_console.print(text_obj, end="")
    return string_console.file.getvalue()

def styled(text, style):
    t = Text(text)
    t.stylize(style)
    return rich_str(t)

def load_companions(core_only=False):
    CORE = {"anarathil","eldurion","faelindor","ithrandur","morgrath","thistlewing","thunderthistl","vyrenth"}
    companions = []
    for bp in sorted((REPO/"companions").rglob("buddy.json")):
        folder = bp.parent.name
        if folder == "info": continue
        try:
            d = json.loads(bp.read_text())
            b = d["bones"]
            companions.append({"folder":folder,"name":d["name"],"personality":d.get("personality",""),
                "species":b["species"],"rarity":b["rarity"],"eye":b["eye"],"hat":b["hat"],
                "shiny":b.get("shiny",False),"stats":b["stats"],"peakStat":d.get("peakStat",""),
                "dumpStat":d.get("dumpStat",""),"sprite_file":bp.parent/"sprite.txt"})
        except: continue
    if core_only: companions = [c for c in companions if c["folder"] in CORE]
    return companions

def get_frame(sf, fn, sleeping=False):
    if not sf.exists(): return [""]*5
    txt = sf.read_text()
    label = "Sleeping" if sleeping else f"Frame {fn}"
    lines, cap = [], False
    for l in txt.split("\n"):
        if f"--- {label}" in l: cap=True; continue
        if cap:
            if l.startswith("---") or (l.strip()=="" and len(lines)>=4): break
            lines.append(l)
    return (lines+[""]*5)[:5]

def visual_width(s):
    return sum(2 if c in "✨💤●" else 1 for c in s)

def render_card(comp, frame_lines, sleeping, idx, total, sp_idx, ra_idx, core_only):
    st = RARITY_STYLES.get(comp["rarity"], RARITY_STYLES["legendary"])
    bs, ac, sp = st["border"], st["accent"], st["sprite"]
    stars = RARITY_STARS.get(comp["rarity"], "?")
    hline = "─"*CARD_WIDTH
    blank = " "*CARD_WIDTH
    shiny_tag = " ✨" if comp["shiny"] else ""

    def border(ch): return styled(ch, f"bold {bs}")
    def accent(t): return styled(t, f"bold {ac}")
    def sprite_c(t): return styled(t, sp)
    def white(t): return styled(t, "bold white")
    def dim(t): return styled(t, "dim")
    def cyn(t): return styled(t, "cyan")
    def grn(t): return styled(t, "bold green")

    lines = []

    # Top border
    lines.append(f"{LEFT_PAD}{border('╭'+hline+'╮')}")

    # Header
    hl = f"{stars}  {comp['rarity'].upper()}"
    su = comp["species"].upper()
    gap = CARD_WIDTH - 2 - len(hl) - len(su)
    lines.append(f"{LEFT_PAD}{border('│')} {accent(hl)}{' '*max(0,gap)}{cyn(su)} {border('│')}{CLR}")

    # Blank
    lines.append(f"{LEFT_PAD}{border('│')}{blank}{border('│')}{CLR}")

    # Sprite
    for i in range(5):
        sl = frame_lines[i] if i < len(frame_lines) else ""
        vw = visual_width(sl)
        pad = max(0, CARD_WIDTH-1-vw)
        lines.append(f"{LEFT_PAD}{border('│')} {sprite_c(sl)}{' '*pad}{border('│')}{CLR}")

    # Blank
    lines.append(f"{LEFT_PAD}{border('│')}{blank}{border('│')}{CLR}")

    # Name
    nd = f"{comp['name']}{shiny_tag}"
    vw = visual_width(nd)
    pad = max(0, CARD_WIDTH-1-vw)
    lines.append(f"{LEFT_PAD}{border('│')} {white(nd)}{' '*pad}{border('│')}{CLR}")

    # Blank
    lines.append(f"{LEFT_PAD}{border('│')}{blank}{border('│')}{CLR}")

    # Personality
    mpw = CARD_WIDTH - 4
    words = comp["personality"].split()
    plines, cur = [], ""
    for w in words:
        if len(cur)+len(w)+1 > mpw: plines.append(cur); cur=w
        else: cur = f"{cur} {w}" if cur else w
    if cur: plines.append(cur)
    for pl in plines[:3]:
        pad = max(0, CARD_WIDTH-1-len(pl))
        lines.append(f"{LEFT_PAD}{border('│')} {dim(pl)}{' '*pad}{border('│')}{CLR}")

    # Blank
    lines.append(f"{LEFT_PAD}{border('│')}{blank}{border('│')}{CLR}")

    # Stats
    for sn in ["DEBUGGING","PATIENCE","CHAOS","WISDOM","SNARK"]:
        val = comp["stats"].get(sn,0)
        filled = val//5; empty = 20-filled
        bar = white("█"*filled) + dim("░"*empty)
        suffix = ""
        if sn == comp["peakStat"]: suffix = " (peak)"
        elif sn == comp["dumpStat"]: suffix = " (dump)"
        vw = 2+10+1+20+1+3+len(suffix)+2
        rpad = max(0, CARD_WIDTH-vw)
        stat_line = f"  {accent(sn.ljust(10))} {bar} {dim(str(val).rjust(3))}{dim(suffix)}{' '*rpad}  "
        lines.append(f"{LEFT_PAD}{border('│')}{stat_line}{border('│')}{CLR}")

    # Blank
    lines.append(f"{LEFT_PAD}{border('│')}{blank}{border('│')}{CLR}")

    # Status
    if sleeping:
        pad = max(0, CARD_WIDTH-17)
        lines.append(f"{LEFT_PAD}{border('│')}  {dim('💤 sleeping...')}{' '*pad}{border('│')}{CLR}")
    else:
        pad = max(0, CARD_WIDTH-11)
        lines.append(f"{LEFT_PAD}{border('│')}  {grn('● online')}{' '*pad}{border('│')}{CLR}")

    # Bottom border
    lines.append(f"{LEFT_PAD}{border('╰'+hline+'╯')}")
    lines.append("")

    # Footer
    nav = f"{idx+1}/{total}"
    lines.append(f"{LEFT_PAD}  {dim('a/← prev')}  {white(f'[ {nav} ]')}  {dim('d/→ next')}  {dim('↑↓ jump')}  {dim('x exit')}{CLR}")
    if not core_only:
        lines.append(f"{LEFT_PAD}  {dim('Species:')} {cyn(ALL_SPECIES[sp_idx])} {dim('(w/s)')}  {dim('Rarity:')} {cyn(ALL_RARITIES[ra_idx])} {dim('(q/e)')}  {dim(comp['folder'])}{CLR}")

    return "\r\n".join(lines)

def get_key(timeout):
    if select.select([sys.stdin],[],[],timeout)[0]:
        ch = sys.stdin.read(1)
        if ch == "\033":
            if select.select([sys.stdin],[],[],0.05)[0]:
                ch += sys.stdin.read(2)
        return ch
    return None

def main():
    args = sys.argv[1:]
    core_only = "--core" in args
    delay = FRAME_DELAY
    start_at = ""
    for i,a in enumerate(args):
        if a=="--delay" and i+1<len(args): delay=float(args[i+1])
        elif a=="--start" and i+1<len(args): start_at=args[i+1]

    sys.stderr.write("Loading companions...\n")
    companions = load_companions(core_only)
    sys.stderr.write(f"Loaded {len(companions)} companions.\n")

    if not companions:
        sys.stderr.write("No companions found!\n")
        return

    sp_idx, ra_idx = 0, 0
    def build_filtered():
        s,r = ALL_SPECIES[sp_idx], ALL_RARITIES[ra_idx]
        return [c for c in companions if (s=="all" or c["species"]==s) and (r=="all" or c["rarity"]==r)]

    filtered = build_filtered()
    index = 0
    if start_at:
        for i,c in enumerate(filtered):
            if c["folder"]==start_at: index=i; break

    old = termios.tcgetattr(sys.stdin)
    try:
        tty.setraw(sys.stdin.fileno())
        sys.stdout.write("\033[?25l\033[2J\033[H"); sys.stdout.flush()

        frame, need_reload = 0, True
        while True:
            if need_reload:
                filtered = build_filtered()
                if index >= len(filtered): index = 0
                if index < 0: index = len(filtered)-1
                need_reload, frame = False, 0

            sys.stdout.write("\033[H")

            if not filtered:
                sys.stdout.write(f"{LEFT_PAD}No companions match filters\r\n")
            else:
                comp = filtered[index]
                if frame in (0,1,3,4): fl=get_frame(comp["sprite_file"],frame%2,False); sl=False
                elif frame==2: fl=get_frame(comp["sprite_file"],2,False); sl=False
                else: fl=get_frame(comp["sprite_file"],0,True); sl=True

                output = render_card(comp, fl, sl, index, len(filtered), sp_idx, ra_idx, core_only)
                sys.stdout.write(output)
                # Clear leftover lines
                sys.stdout.write(f"\r\n{CLR}\r\n{CLR}\r\n{CLR}")

            sys.stdout.flush()

            key = get_key(delay)
            if key:
                if key in ("x","X"): break
                elif key in ("\033[D","a","A"): index=(index-1)%max(1,len(filtered)); need_reload=True
                elif key in ("\033[C","d","D"): index=(index+1)%max(1,len(filtered)); need_reload=True
                elif key=="\033[A": index=(index-10)%max(1,len(filtered)); need_reload=True
                elif key=="\033[B": index=(index+10)%max(1,len(filtered)); need_reload=True
                elif key in ("e","E") and not core_only: ra_idx=(ra_idx+1)%len(ALL_RARITIES); index=0; need_reload=True
                elif key=="q" and not core_only: ra_idx=(ra_idx-1)%len(ALL_RARITIES); index=0; need_reload=True
                elif key in ("s","S") and not core_only: sp_idx=(sp_idx+1)%len(ALL_SPECIES); index=0; need_reload=True
                elif key in ("w","W") and not core_only: sp_idx=(sp_idx-1)%len(ALL_SPECIES); index=0; need_reload=True
            frame = (frame+1)%6
    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old)
        sys.stdout.write("\033[?25h\033[2J\033[H"); sys.stdout.flush()
        name = filtered[index]["name"] if filtered and index<len(filtered) else "companion"
        print(f"Goodbye from {name}!")

if __name__ == "__main__":
    main()
