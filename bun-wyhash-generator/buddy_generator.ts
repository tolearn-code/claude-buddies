#!/usr/bin/env bun
/**
 * Self-contained buddy generator using Bun's native wyhash.
 * This produces the SAME results as Claude Code's default buddy generation.
 *
 * Usage:
 *   bun buddy_generator.ts <accountUuid> [salt]
 *   bun buddy_generator.ts <accountUuid> [salt] --output <dir>
 *   bun buddy_generator.ts <accountUuid> [salt] --json
 */

// ── Constants ──

const ORIGINAL_SALT = "friend-2026-401";

const RARITIES = ["common", "uncommon", "rare", "epic", "legendary"] as const;
type Rarity = (typeof RARITIES)[number];

const RARITY_WEIGHTS: Record<Rarity, number> = {
  common: 60, uncommon: 25, rare: 10, epic: 4, legendary: 1,
};

const RARITY_FLOOR: Record<Rarity, number> = {
  common: 5, uncommon: 15, rare: 25, epic: 35, legendary: 50,
};

const RARITY_STARS: Record<Rarity, string> = {
  common: "★", uncommon: "★★", rare: "★★★", epic: "★★★★", legendary: "★★★★★",
};

const SPECIES = [
  "duck", "goose", "blob", "cat", "dragon", "octopus",
  "owl", "penguin", "turtle", "snail", "ghost", "axolotl",
  "capybara", "cactus", "robot", "rabbit", "mushroom", "chonk",
] as const;

const EYES = ["·", "✦", "×", "◉", "@", "°"] as const;

const HATS = ["none", "crown", "tophat", "propeller", "halo", "wizard", "beanie", "tinyduck"] as const;

const STAT_NAMES = ["DEBUGGING", "PATIENCE", "CHAOS", "WISDOM", "SNARK"] as const;

const DEFAULT_PERSONALITIES: Record<string, string> = {
  duck: "A cheerful quacker who celebrates your wins with enthusiastic honks and judges your variable names with quiet side-eye.",
  goose: "An agent of chaos who thrives on your merge conflicts and honks menacingly whenever you write a TODO comment.",
  blob: "A formless, chill companion who absorbs your stress and responds to everything with gentle, unhurried wisdom.",
  cat: "An aloof code reviewer who pretends not to care about your bugs but quietly bats at syntax errors when you're not looking.",
  dragon: "A fierce guardian of clean code who breathes fire at spaghetti logic and hoards well-written functions.",
  octopus: "A multitasking genius who juggles eight concerns at once and offers tentacle-loads of unsolicited architectural advice.",
  owl: "A nocturnal sage who comes alive during late-night debugging sessions and asks annoyingly insightful questions.",
  penguin: "A tuxedo-wearing professional who waddles through your codebase with dignified concern and dry wit.",
  turtle: "A patient mentor who reminds you that slow, steady refactoring beats heroic rewrites every time.",
  snail: "A zen minimalist who moves at their own pace and leaves a trail of thoughtful, unhurried observations.",
  ghost: "A spectral presence who haunts your dead code and whispers about the bugs you thought you fixed.",
  axolotl: "A regenerative optimist who believes every broken build can be healed and every test can be unflaked.",
  capybara: "The most relaxed companion possible — nothing fazes them, not even production outages at 3am.",
  cactus: "A prickly but lovable desert dweller who thrives on neglect and offers sharp, pointed feedback.",
  robot: "A logical companion who speaks in precise technical observations and occasionally glitches endearingly.",
  rabbit: "A fast-moving, hyperactive buddy who speed-reads your diffs and bounces between topics at alarming pace.",
  mushroom: "A wry fungal sage who speaks in meandering tangents about your bugs while secretly enjoying the chaos.",
  chonk: "An absolute unit of a companion who sits on your terminal with maximum gravitational presence and minimal urgency.",
};

// ── Sprite Data ──

const BODIES: Record<string, string[][]> = {
  duck: [
    ["            ", "    __      ", "  <({E} )___  ", "   (  ._>   ", "    `--´    "],
    ["            ", "    __      ", "  <({E} )___  ", "   (  ._>   ", "    `--´~   "],
    ["            ", "    __      ", "  <({E} )___  ", "   (  .__>  ", "    `--´    "],
  ],
  goose: [
    ["            ", "     ({E}>    ", "     ||     ", "   _(__)_   ", "    ^^^^    "],
    ["            ", "    ({E}>     ", "     ||     ", "   _(__)_   ", "    ^^^^    "],
    ["            ", "     ({E}>>   ", "     ||     ", "   _(__)_   ", "    ^^^^    "],
  ],
  blob: [
    ["            ", "   .----.   ", "  ( {E}  {E} )  ", "  (      )  ", "   `----´   "],
    ["            ", "  .------.  ", " (  {E}  {E}  ) ", " (        ) ", "  `------´  "],
    ["            ", "    .--.    ", "   ({E}  {E})   ", "   (    )   ", "    `--´    "],
  ],
  cat: [
    ["            ", "   /\\_/\\    ", "  ( {E}   {E})  ", "  (  ω  )   ", '  (")_(")   '],
    ["            ", "   /\\_/\\    ", "  ( {E}   {E})  ", "  (  ω  )   ", '  (")_(")~  '],
    ["            ", "   /\\-/\\    ", "  ( {E}   {E})  ", "  (  ω  )   ", '  (")_(")   '],
  ],
  dragon: [
    ["            ", "  /^\\  /^\\  ", " <  {E}  {E}  > ", " (   ~~   ) ", "  `-vvvv-´  "],
    ["            ", "  /^\\  /^\\  ", " <  {E}  {E}  > ", " (        ) ", "  `-vvvv-´  "],
    ["   ~    ~   ", "  /^\\  /^\\  ", " <  {E}  {E}  > ", " (   ~~   ) ", "  `-vvvv-´  "],
  ],
  octopus: [
    ["            ", "   .----.   ", "  ( {E}  {E} )  ", "  (______)  ", "  /\\/\\/\\/\\  "],
    ["            ", "   .----.   ", "  ( {E}  {E} )  ", "  (______)  ", "  \\/\\/\\/\\/  "],
    ["     o      ", "   .----.   ", "  ( {E}  {E} )  ", "  (______)  ", "  /\\/\\/\\/\\  "],
  ],
  owl: [
    ["            ", "   /\\  /\\   ", "  (({E})({E}))  ", "  (  ><  )  ", "   `----´   "],
    ["            ", "   /\\  /\\   ", "  (({E})({E}))  ", "  (  ><  )  ", "   .----.   "],
    ["            ", "   /\\  /\\   ", "  (({E})(-))  ", "  (  ><  )  ", "   `----´   "],
  ],
  penguin: [
    ["            ", "  .---.     ", "  ({E}>{E})     ", " /(   )\\    ", "  `---´     "],
    ["            ", "  .---.     ", "  ({E}>{E})     ", " |(   )|    ", "  `---´     "],
    ["  .---.     ", "  ({E}>{E})     ", " /(   )\\    ", "  `---´     ", "   ~ ~      "],
  ],
  turtle: [
    ["            ", "   _,--._   ", "  ( {E}  {E} )  ", " /[______]\\ ", "  ``    ``  "],
    ["            ", "   _,--._   ", "  ( {E}  {E} )  ", " /[______]\\ ", "   ``  ``   "],
    ["            ", "   _,--._   ", "  ( {E}  {E} )  ", " /[======]\\ ", "  ``    ``  "],
  ],
  snail: [
    ["            ", " {E}    .--.  ", "  \\  ( @ )  ", "   \\_`--´   ", "  ~~~~~~~   "],
    ["            ", "  {E}   .--.  ", "  |  ( @ )  ", "   \\_`--´   ", "  ~~~~~~~   "],
    ["            ", " {E}    .--.  ", "  \\  ( @  ) ", "   \\_`--´   ", "   ~~~~~~   "],
  ],
  ghost: [
    ["            ", "   .----.   ", "  / {E}  {E} \\  ", "  |      |  ", "  ~`~``~`~  "],
    ["            ", "   .----.   ", "  / {E}  {E} \\  ", "  |      |  ", "  `~`~~`~`  "],
    ["    ~  ~    ", "   .----.   ", "  / {E}  {E} \\  ", "  |      |  ", "  ~~`~~`~~  "],
  ],
  axolotl: [
    ["            ", "}~(______)~{", "}~({E} .. {E})~{", "  ( .--. )  ", "  (_/  \\_)  "],
    ["            ", "~}(______){~", "~}({E} .. {E}){~", "  ( .--. )  ", "  (_/  \\_)  "],
    ["            ", "}~(______)~{", "}~({E} .. {E})~{", "  (  --  )  ", "  ~_/  \\_~  "],
  ],
  capybara: [
    ["            ", "  n______n  ", " ( {E}    {E} ) ", " (   oo   ) ", "  `------´  "],
    ["            ", "  n______n  ", " ( {E}    {E} ) ", " (   Oo   ) ", "  `------´  "],
    ["    ~  ~    ", "  u______n  ", " ( {E}    {E} ) ", " (   oo   ) ", "  `------´  "],
  ],
  cactus: [
    ["            ", " n  ____  n ", " | |{E}  {E}| | ", " |_|    |_| ", "   |    |   "],
    ["            ", "    ____    ", " n |{E}  {E}| n ", " |_|    |_| ", "   |    |   "],
    [" n        n ", " |  ____  | ", " | |{E}  {E}| | ", " |_|    |_| ", "   |    |   "],
  ],
  robot: [
    ["            ", "   .[||].   ", "  [ {E}  {E} ]  ", "  [ ==== ]  ", "  `------´  "],
    ["            ", "   .[||].   ", "  [ {E}  {E} ]  ", "  [ -==- ]  ", "  `------´  "],
    ["     *      ", "   .[||].   ", "  [ {E}  {E} ]  ", "  [ ==== ]  ", "  `------´  "],
  ],
  rabbit: [
    ["            ", "   (\\__/)   ", "  ( {E}  {E} )  ", " =(  ..  )= ", '  (")__(")  '],
    ["            ", "   (|__/)   ", "  ( {E}  {E} )  ", " =(  ..  )= ", '  (")__(")  '],
    ["            ", "   (\\__/)   ", "  ( {E}  {E} )  ", " =( .  . )= ", '  (")__(")  '],
  ],
  mushroom: [
    ["            ", " .-o-OO-o-. ", "(__________)", "   |{E}  {E}|   ", "   |____|   "],
    ["            ", " .-O-oo-O-. ", "(__________)", "   |{E}  {E}|   ", "   |____|   "],
    ["   . o  .   ", " .-o-OO-o-. ", "(__________)", "   |{E}  {E}|   ", "   |____|   "],
  ],
  chonk: [
    ["            ", "  /\\    /\\  ", " ( {E}    {E} ) ", " (   ..   ) ", "  `------´  "],
    ["            ", "  /\\    /|  ", " ( {E}    {E} ) ", " (   ..   ) ", "  `------´  "],
    ["            ", "  /\\    /\\  ", " ( {E}    {E} ) ", " (   ..   ) ", "  `------´~ "],
  ],
};

const HAT_LINES: Record<string, string> = {
  none: "",
  crown: "   \\^^^/    ",
  tophat: "   [___]    ",
  propeller: "    -+-     ",
  halo: "   (   )    ",
  wizard: "    /^\\     ",
  beanie: "   (___)    ",
  tinyduck: "    ,>      ",
};

// ── Hash ──

function hashString(s: string): number {
  return Number(BigInt(Bun.hash(s)) & 0xffffffffn);
}

// ── RNG ──

type RngFunction = () => number;

function mulberry32(seed: number): RngFunction {
  let a = seed >>> 0;
  return function () {
    a |= 0;
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function pick<T>(rng: RngFunction, arr: readonly T[]): T {
  return arr[Math.floor(rng() * arr.length)];
}

// ── Roll ──

function rollRarity(rng: RngFunction): Rarity {
  const total = Object.values(RARITY_WEIGHTS).reduce((a, b) => a + b, 0);
  let r = rng() * total;
  for (const rarity of RARITIES) {
    r -= RARITY_WEIGHTS[rarity];
    if (r < 0) return rarity;
  }
  return "common";
}

function rollStats(rng: RngFunction, rarity: Rarity): Record<string, number> {
  const floor = RARITY_FLOOR[rarity];
  const peak = pick(rng, STAT_NAMES);
  let dump = pick(rng, STAT_NAMES);
  while (dump === peak) dump = pick(rng, STAT_NAMES);

  const stats: Record<string, number> = {};
  for (const name of STAT_NAMES) {
    if (name === peak) {
      stats[name] = Math.min(100, floor + 50 + Math.floor(rng() * 30));
    } else if (name === dump) {
      stats[name] = Math.max(1, floor - 10 + Math.floor(rng() * 15));
    } else {
      stats[name] = floor + Math.floor(rng() * 40);
    }
  }
  return stats;
}

function roll(userId: string, salt: string) {
  const key = userId + salt;
  const rng = mulberry32(hashString(key));
  const rarity = rollRarity(rng);

  const bones = {
    rarity,
    species: pick(rng, SPECIES),
    eye: pick(rng, EYES),
    hat: rarity === "common" ? "none" : pick(rng, HATS),
    shiny: rng() < 0.01,
    stats: rollStats(rng, rarity),
  };

  const inspirationSeed = Math.floor(rng() * 1e9);
  return { bones, inspirationSeed };
}

// ── Sprite Rendering ──

function renderSprite(bones: { species: string; eye: string; hat: string }, frame = 0, sleeping = false): string[] {
  const frames = BODIES[bones.species];
  const eye = sleeping ? "-" : bones.eye;
  const body = frames[frame % frames.length].map((line) => line.replaceAll("{E}", eye));
  const lines = [...body];

  if (bones.hat !== "none" && !lines[0].trim()) {
    lines[0] = HAT_LINES[bones.hat];
  }
  if (!lines[0].trim() && frames.every((f) => !f[0].trim())) lines.shift();
  return lines;
}

function renderAllFrames(bones: { species: string; eye: string; hat: string }): string {
  const labels = ["idle", "idle alt", "wink"];
  const output: string[] = [];

  for (let i = 0; i < BODIES[bones.species].length; i++) {
    output.push(`--- Frame ${i} (${labels[i] ?? "alt"}) ---`);
    for (const line of renderSprite(bones, i, false)) output.push(line);
    output.push("");
  }

  output.push("--- Sleeping ---");
  for (const line of renderSprite(bones, 0, true)) output.push(line);

  return output.join("\n");
}

// ── Output ──

function generateBuddyFiles(userId: string, salt: string, outputDir: string) {
  const { bones, inspirationSeed } = roll(userId, salt);
  const species = bones.species;

  const fs = require("fs");
  const path = require("path");
  fs.mkdirSync(outputDir, { recursive: true });

  const buddyData = {
    name: species.charAt(0).toUpperCase() + species.slice(1),
    defaultPersonality: DEFAULT_PERSONALITIES[species],
    salt,
    bones,
    inspirationSeed,
  };

  const companionData = {
    name: species.charAt(0).toUpperCase() + species.slice(1),
    personality: DEFAULT_PERSONALITIES[species],
  };

  const spriteText =
    `${buddyData.name} — ${bones.rarity.charAt(0).toUpperCase() + bones.rarity.slice(1)} ` +
    `${buddyData.name} (${RARITY_STARS[bones.rarity]})\n` +
    `Eyes: ${bones.eye} | Hat: ${bones.hat} | Shiny: ${bones.shiny ? "yes" : "no"}\n\n` +
    renderAllFrames(bones) + "\n";

  fs.writeFileSync(path.join(outputDir, "buddy.json"), JSON.stringify(buddyData, null, 2) + "\n");
  fs.writeFileSync(path.join(outputDir, "companion.json"), JSON.stringify(companionData, null, 2) + "\n");
  fs.writeFileSync(path.join(outputDir, "sprite.txt"), spriteText);

  console.log(`Files saved to ${outputDir}/`);
}

function printBuddy(userId: string, salt: string) {
  const { bones, inspirationSeed } = roll(userId, salt);
  const species = bones.species;
  const name = species.charAt(0).toUpperCase() + species.slice(1);

  console.log(`\n  ${name} — ${bones.rarity.charAt(0).toUpperCase() + bones.rarity.slice(1)} ${RARITY_STARS[bones.rarity]}`);
  console.log(`  Eye: ${bones.eye}  Hat: ${bones.hat}  Shiny: ${bones.shiny ? "yes" : "no"}`);
  console.log(`  Hash: wyhash (Bun native)\n`);

  for (const line of renderSprite(bones, 0, false)) console.log(`  ${line}`);
  console.log("\n  Stats:");

  for (const [stat, val] of Object.entries(bones.stats)) {
    const filled = Math.floor((val as number) / 5);
    const bar = "█".repeat(filled) + "░".repeat(20 - filled);
    console.log(`    ${stat.padEnd(10)} ${bar} ${val}`);
  }

  console.log(`\n  Personality: ${DEFAULT_PERSONALITIES[species]}\n`);
}

// ── CLI ──

const args = process.argv.slice(2);
const flags = new Set(args.filter((a) => a.startsWith("--")));
const positional = args.filter((a) => !a.startsWith("--") && !args[args.indexOf(a) - 1]?.startsWith("--output"));

const outputIdx = args.indexOf("--output");
const outputDir = outputIdx !== -1 ? args[outputIdx + 1] : null;

const userId = positional[0];
const salt = positional[1] ?? ORIGINAL_SALT;

if (!userId) {
  console.log("Usage: bun buddy_generator.ts <accountUuid> [salt] [--output <dir>] [--json]");
  console.log(`\nDefault salt: ${ORIGINAL_SALT}`);
  console.log("This generator uses Bun's native wyhash — the same hash Claude Code uses by default.");
  process.exit(1);
}

if (outputDir) {
  generateBuddyFiles(userId, salt, outputDir);
} else if (flags.has("--json")) {
  const result = roll(userId, salt);
  console.log(JSON.stringify(result, null, 2));
} else {
  printBuddy(userId, salt);
}
