#!/usr/bin/env bun
/**
 * Animated companion viewer with rich terminal UI.
 * Built with Bun + chalk for proper UTF-8 and color handling.
 *
 * Controls:
 *   ←/a  Previous    →/d  Next    ↑  Jump 10 back    ↓  Jump 10 forward
 *   w/s  Species filter    q/e  Rarity filter    x  Exit
 *   --core  Browse only featured companions
 */

import chalk from "chalk";
import { readFileSync, readdirSync, existsSync } from "fs";
import { join, dirname, basename } from "path";

// ── Config ──
const REPO = "/home/sprite/claude-buddies";
const FRAME_DELAY = 800; // ms
const CARD_WIDTH = 68;
const LEFT_PAD = "          "; // 10 chars

const ALL_SPECIES = ["all", "axolotl", "blob", "cactus", "capybara", "cat", "chonk", "dragon", "duck", "ghost", "goose", "mushroom", "octopus", "owl", "penguin", "rabbit", "robot", "snail", "turtle"];
const ALL_RARITIES = ["all", "common", "uncommon", "rare", "epic", "legendary"];
const CORE_LIST = ["anarathil", "eldurion", "faelindor", "ithrandur", "morgrath", "thistlewing", "thunderthistl", "vyrenth"];

const RARITY_STARS: Record<string, string> = {
  common: "★", uncommon: "★★", rare: "★★★", epic: "★★★★", legendary: "★★★★★",
};

// ── Parse args ──
const args = process.argv.slice(2);
const coreOnly = args.includes("--core");
const startAt = args.find((_, i) => args[i - 1] === "--start") ?? "";

// ── Colors ──
const gold = chalk.hex("#FFC107");
const orange = chalk.hex("#D7775B");
const dim = chalk.hex("#888888");
const cyan = chalk.hex("#82AADC");
const green = chalk.hex("#93C882");
const red = chalk.hex("#FF6B80");
const white = chalk.bold.white;
const CLR = "\x1b[K"; // clear to end of line — prevents ghost chars from previous frames

// Rarity color themes: [border, accent, sprite]
const RARITY_THEMES: Record<string, { border: chalk.Chalk; accent: chalk.Chalk; sprite: chalk.Chalk }> = {
  common:    { border: chalk.hex("#9E9E9E"), accent: chalk.hex("#BDBDBD"), sprite: chalk.hex("#B0B0B0") },
  uncommon:  { border: chalk.hex("#4CAF50"), accent: chalk.hex("#81C784"), sprite: chalk.hex("#A5D6A7") },
  rare:      { border: chalk.hex("#2196F3"), accent: chalk.hex("#64B5F6"), sprite: chalk.hex("#90CAF9") },
  epic:      { border: chalk.hex("#9C27B0"), accent: chalk.hex("#CE93D8"), sprite: chalk.hex("#E1BEE7") },
  legendary: { border: chalk.hex("#D7775B"), accent: chalk.hex("#FFC107"), sprite: chalk.hex("#FFC107") },
};

// ── Load companions ──
interface Companion {
  path: string;
  folder: string;
  name: string;
  species: string;
  rarity: string;
  eye: string;
  hat: string;
  shiny: boolean;
  personality: string;
  peakStat: string;
  dumpStat: string;
  stats: Record<string, number>;
  spriteFile: string;
}

function findAllBuddyJsons(): string[] {
  const results: string[] = [];
  function walk(dir: string, depth = 0) {
    if (depth > 5) return;
    try {
      for (const entry of readdirSync(dir, { withFileTypes: true })) {
        const full = join(dir, entry.name);
        if (entry.isFile() && entry.name === "buddy.json") results.push(full);
        else if (entry.isDirectory() && entry.name !== "info" && entry.name !== "node_modules") walk(full, depth + 1);
      }
    } catch {}
  }
  walk(join(REPO, "companions"));
  return results.sort();
}

function loadCompanion(buddyPath: string): Companion {
  const data = JSON.parse(readFileSync(buddyPath, "utf-8"));
  const dir = dirname(buddyPath);
  return {
    path: buddyPath,
    folder: basename(dir),
    name: data.name,
    species: data.bones.species,
    rarity: data.bones.rarity,
    eye: data.bones.eye,
    hat: data.bones.hat,
    shiny: data.bones.shiny,
    personality: data.personality,
    peakStat: data.peakStat ?? "?",
    dumpStat: data.dumpStat ?? "?",
    stats: data.bones.stats,
    spriteFile: join(dir, "sprite.txt"),
  };
}

console.log("Loading companions...");
const allBuddyPaths = findAllBuddyJsons();
let allCompanions: Companion[];

if (coreOnly) {
  allCompanions = CORE_LIST
    .map((c) => join(REPO, "companions", c, "buddy.json"))
    .filter(existsSync)
    .map(loadCompanion);
} else {
  allCompanions = allBuddyPaths.map(loadCompanion);
}
console.log(`Loaded ${allCompanions.length} companions.`);

// ── State ──
let speciesIdx = 0;
let rarityIdx = 0;
let filtered: Companion[] = [];
let index = 0;
let frame = 0;

function rebuildFilter() {
  const sp = ALL_SPECIES[speciesIdx];
  const ra = ALL_RARITIES[rarityIdx];
  filtered = allCompanions.filter((c) => {
    if (sp !== "all" && c.species !== sp) return false;
    if (ra !== "all" && c.rarity !== ra) return false;
    return true;
  });
  index = 0;
}
rebuildFilter();

// Find start position
if (startAt) {
  const idx = filtered.findIndex((c) => c.folder === startAt);
  if (idx >= 0) index = idx;
}

// ── Sprite frames ──
function getFrame(comp: Companion, frameNum: number, sleeping: boolean): string[] {
  if (!existsSync(comp.spriteFile)) return ["  (no sprite)"];
  const text = readFileSync(comp.spriteFile, "utf-8");
  const label = sleeping ? "Sleeping" : `Frame ${frameNum}`;
  const regex = new RegExp(`--- ${label}[^-]*---\\n([\\s\\S]*?)(?=\\n---|\\n*$)`);
  const match = text.match(regex);
  if (!match) return ["  (frame not found)"];
  return match[1].split("\n").filter((l) => l.length > 0).slice(0, 5);
}

// ── Rendering ──
function statBar(val: number): string {
  const filled = Math.floor(val / 5);
  const empty = 20 - filled;
  return white("█".repeat(filled)) + dim("░".repeat(empty));
}

function padRight(str: string, width: number): string {
  // Visual width (not byte length)
  const visLen = [...str].length;
  const pad = Math.max(0, width - visLen);
  return str + " ".repeat(pad);
}

function hline(): string {
  return "─".repeat(CARD_WIDTH);
}

function blankLine(): string {
  return " ".repeat(CARD_WIDTH);
}



function cardLine(content: string, visWidth: number): string {
  const pad = Math.max(0, CARD_WIDTH - 1 - visWidth);
  return `${orange("│")} ${content}${" ".repeat(pad)}${orange("│")}${CLR}`;
}

function renderCard(comp: Companion, frameLines: string[], sleeping: boolean): string {
  const lines: string[] = [];
  const stars = RARITY_STARS[comp.rarity] ?? "?";
  const speciesUpper = comp.species.toUpperCase();
  const rarityUpper = comp.rarity.toUpperCase();
  const shinyTag = comp.shiny ? " ✨" : "";
  const totalFiltered = filtered.length;
  const navPos = `${index + 1}/${totalFiltered}`;

  // Rarity-based colors
  const theme = RARITY_THEMES[comp.rarity] ?? RARITY_THEMES.legendary;
  const b = theme.border;  // border color
  const a = theme.accent;  // accent (headers, stats, stars)
  const s = theme.sprite;  // sprite color

  // Top border
  lines.push(`${LEFT_PAD}${b("╭" + hline() + "╮")}`);

  // Header: rarity + species
  const headerLeft = `${stars}  ${rarityUpper}`;
  const headerGap = CARD_WIDTH - 2 - headerLeft.length - speciesUpper.length;
  lines.push(`${LEFT_PAD}${b("│")} ${a(headerLeft)}${" ".repeat(Math.max(0, headerGap))}${cyan(speciesUpper)} ${b("│")}${CLR}`);

  // Blank
  lines.push(`${LEFT_PAD}${b("│")}${blankLine()}${b("│")}${CLR}`);

  // Sprite
  for (let i = 0; i < 5; i++) {
    const spriteLine = frameLines[i] ?? "";
    const visLen = [...spriteLine].length;
    const pad = Math.max(0, CARD_WIDTH - 1 - visLen);
    lines.push(`${LEFT_PAD}${b("│")} ${s(spriteLine)}${" ".repeat(pad)}${b("│")}${CLR}`);
  }

  // Blank
  lines.push(`${LEFT_PAD}${b("│")}${blankLine()}${b("│")}${CLR}`);

  // Name (✨ is 2 terminal columns but 1 JS char — subtract extra for wide chars)
  const nameDisplay = `${comp.name}${shinyTag}`;
  const wideChars = [...nameDisplay].filter(c => c === "✨").length;
  const namePad = Math.max(0, CARD_WIDTH - 1 - [...nameDisplay].length - wideChars);
  lines.push(`${LEFT_PAD}${b("│")} ${white(nameDisplay)}${" ".repeat(namePad)}${b("│")}${CLR}`);

  // Blank
  lines.push(`${LEFT_PAD}${b("│")}${blankLine()}${b("│")}${CLR}`);

  // Personality (3 lines max, word-wrapped)
  const maxPW = CARD_WIDTH - 4;
  const words = comp.personality.split(" ");
  const pLines: string[] = [];
  let current = "";
  for (const word of words) {
    if (current.length + word.length + 1 > maxPW) {
      pLines.push(current);
      current = word;
    } else {
      current = current ? current + " " + word : word;
    }
  }
  if (current) pLines.push(current);
  for (const pl of pLines.slice(0, 3)) {
    const pPad = Math.max(0, CARD_WIDTH - 1 - pl.length);
    lines.push(`${LEFT_PAD}${b("│")} ${dim(pl)}${" ".repeat(pPad)}${b("│")}${CLR}`);
  }

  // Blank
  lines.push(`${LEFT_PAD}${b("│")}${blankLine()}${b("│")}${CLR}`);

  // Stats
  const statNames = ["DEBUGGING", "PATIENCE", "CHAOS", "WISDOM", "SNARK"] as const;
  for (const stat of statNames) {
    const val = comp.stats[stat] ?? 0;
    const bar = statBar(val);
    let suffix = "";
    if (stat === comp.peakStat) suffix = " (peak)";
    else if (stat === comp.dumpStat) suffix = " (dump)";
    // Visual width: 2(pad) + 10(name) + 1(sp) + 20(bar) + 1(sp) + 3(val) + suffix + 2(pad) = 39 + suffix
    const visWidth = 2 + 10 + 1 + 20 + 1 + 3 + suffix.length + 2;
    const rightPad = Math.max(0, CARD_WIDTH - visWidth);
    const statLine = `  ${a(stat.padEnd(10))} ${bar} ${dim(String(val).padStart(3))}${dim(suffix)}${" ".repeat(rightPad)}  `;
    lines.push(`${LEFT_PAD}${b("│")}${statLine}${b("│")}${CLR}`);
  }

  // Blank
  lines.push(`${LEFT_PAD}${b("│")}${blankLine()}${b("│")}${CLR}`);

  // Status
  if (sleeping) {
    const statusPad = Math.max(0, CARD_WIDTH - 17);
    lines.push(`${LEFT_PAD}${b("│")}  ${dim("💤 sleeping...")}${" ".repeat(statusPad)}${b("│")}${CLR}`);
  } else {
    const statusPad = Math.max(0, CARD_WIDTH - 11);
    lines.push(`${LEFT_PAD}${b("│")}  ${green("● online")}${" ".repeat(statusPad)}${b("│")}${CLR}`);
  }

  // Bottom border
  lines.push(`${LEFT_PAD}${b("╰" + hline() + "╯")}`);
  lines.push("");

  // Navigation footer (clear to end of line to prevent ghost text from previous frames)
  
  lines.push(`${LEFT_PAD}  ${dim("a/← prev")}  ${white(`[ ${navPos} ]`)}  ${dim("d/→ next")}  ${dim("↑↓ jump")}  ${dim("x exit")}${CLR}`);
  if (!coreOnly) {
    lines.push(`${LEFT_PAD}  ${dim("Species:")} ${cyan(ALL_SPECIES[speciesIdx])} ${dim("(w/s)")}  ${dim("Rarity:")} ${cyan(ALL_RARITIES[rarityIdx])} ${dim("(q/e)")}  ${dim(comp.folder)}${CLR}`);
  } else {
    lines.push(`${LEFT_PAD}  ${dim("--core mode")}  ${dim(comp.folder)}${CLR}`);
  }

  return lines.join("\n");
}

function renderEmpty(): string {
  const lines: string[] = [];
  lines.push(`${LEFT_PAD}${orange("╭" + hline() + "╮")}`);
  lines.push(`${LEFT_PAD}${orange("│")}${blankLine()}${orange("│")}${CLR}`);
  const msg = "No companions match filters";
  const pad = Math.floor((CARD_WIDTH - msg.length) / 2);
  lines.push(`${LEFT_PAD}${orange("│")}${" ".repeat(pad)}${red(msg)}${" ".repeat(CARD_WIDTH - pad - msg.length)}${orange("│")}${CLR}`);
  lines.push(`${LEFT_PAD}${orange("│")}${blankLine()}${orange("│")}${CLR}`);
  lines.push(`${LEFT_PAD}${orange("╰" + hline() + "╯")}`);
  lines.push("");
  lines.push(`${LEFT_PAD}  ${dim("Species:")} ${white(ALL_SPECIES[speciesIdx])} ${dim("(w/s)")}  ${dim("Rarity:")} ${white(ALL_RARITIES[rarityIdx])} ${dim("(q/e)")}  ${dim("x exit")}\x1b[K`);
  return lines.join("\n");
}

// ── Terminal control ──
function hideCursor() { process.stdout.write("\x1b[?25l"); }
function showCursor() { process.stdout.write("\x1b[?25h"); }
function moveTo(row: number, col: number) { process.stdout.write(`\x1b[${row};${col}H`); }
function clearScreen() { process.stdout.write("\x1b[2J"); moveTo(1, 1); }

// ── Input handling ──
function setupRawInput() {
  if (process.stdin.isTTY) {
    process.stdin.setRawMode(true);
  }
  process.stdin.resume();
  process.stdin.setEncoding("utf-8");
}

let pendingKey = "";

process.stdin.on("data", (key: string) => {
  pendingKey = key;
});

function consumeKey(): string {
  const k = pendingKey;
  pendingKey = "";
  return k;
}

// ── Animation loop ──
function getFrameData(): { lines: string[]; sleeping: boolean } {
  const comp = filtered[index];
  if (!comp) return { lines: [], sleeping: false };

  switch (frame) {
    case 0: case 1: case 3: case 4:
      return { lines: getFrame(comp, frame % 2, false), sleeping: false };
    case 2:
      return { lines: getFrame(comp, 2, false), sleeping: false };
    case 5:
      return { lines: getFrame(comp, 0, true), sleeping: true };
    default:
      return { lines: getFrame(comp, 0, false), sleeping: false };
  }
}

function handleInput(key: string): boolean {
  const total = filtered.length;

  switch (key) {
    case "\x1b[D": case "a": case "A": // Left
      if (total > 0) index = (index - 1 + total) % total;
      frame = 0;
      return true;
    case "\x1b[C": case "d": case "D": // Right
      if (total > 0) index = (index + 1) % total;
      frame = 0;
      return true;
    case "\x1b[A": // Up — jump 10
      if (total > 0) index = (index - 10 + total) % total;
      frame = 0;
      return true;
    case "\x1b[B": // Down — jump 10
      if (total > 0) index = (index + 10) % total;
      frame = 0;
      return true;
    case "e": case "E": // Rarity up
      if (!coreOnly) {
        rarityIdx = (rarityIdx + 1) % ALL_RARITIES.length;
        rebuildFilter();
      }
      return true;
    case "q": // Rarity down
      if (!coreOnly) {
        rarityIdx = (rarityIdx - 1 + ALL_RARITIES.length) % ALL_RARITIES.length;
        rebuildFilter();
      }
      return true;
    case "s": case "S": // Species next
      if (!coreOnly) {
        speciesIdx = (speciesIdx + 1) % ALL_SPECIES.length;
        rebuildFilter();
      }
      return true;
    case "w": case "W": // Species prev
      if (!coreOnly) {
        speciesIdx = (speciesIdx - 1 + ALL_SPECIES.length) % ALL_SPECIES.length;
        rebuildFilter();
      }
      return true;
    case "x": case "X": case "\x03": // Exit (x or Ctrl+C)
      return false;
    default:
      return true;
  }
}

async function main() {
  setupRawInput();
  hideCursor();
  clearScreen();

  const cleanup = () => {
    showCursor();
    clearScreen();
    const comp = filtered[index];
    console.log(`Goodbye from ${comp?.name ?? "companion"}!`);
    process.exit(0);
  };

  process.on("SIGINT", cleanup);
  process.on("SIGTERM", cleanup);

  while (true) {
    moveTo(1, 1);

    if (filtered.length === 0) {
      process.stdout.write(renderEmpty());
    } else {
      const { lines, sleeping } = getFrameData();
      const comp = filtered[index];
      process.stdout.write(renderCard(comp, lines, sleeping));
    }

    // Wait for frame delay, checking for input
    await new Promise<void>((resolve) => setTimeout(resolve, FRAME_DELAY));

    const key = consumeKey();
    if (key) {
      const cont = handleInput(key);
      if (!cont) {
        cleanup();
        return;
      }
    }

    frame = (frame + 1) % 6;
  }
}

main().catch(console.error);
