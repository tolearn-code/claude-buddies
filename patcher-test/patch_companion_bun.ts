#!/usr/bin/env bun
/**
 * Patch Claude Code to use a companion from the companions/ directory.
 * Uses Bun's native wyhash — matches Claude Code's default hash algorithm.
 *
 * Usage:
 *   bun patch_companion_bun.ts <companion-name>
 *   bun patch_companion_bun.ts vyrenth
 *   bun patch_companion_bun.ts --list
 *   bun patch_companion_bun.ts --restore
 *
 * Set CLAUDE_BINARY=/path/to/cli.js to skip auto-detection.
 */

import { existsSync, readFileSync, writeFileSync, copyFileSync, statSync, chmodSync, readdirSync } from "fs";
import { resolve, join, dirname } from "path";
import { homedir, platform } from "os";
import { execSync } from "child_process";

// ── Constants ──

const DEFAULT_SALT = "friend-2026-401";
const SALT_LENGTH = 15;
const SCRIPT_DIR = dirname(resolve(import.meta.path));
const COMPANIONS_DIR = resolve(SCRIPT_DIR, "..", "companions");
const PATCHER_STATE = join(SCRIPT_DIR, ".patcher-state.json");
const IS_MAC = platform() === "darwin";
const IS_WIN = platform() === "win32";

const CLAUDE_CONFIG_PATHS = [
  join(homedir(), ".claude.json"),
  join(homedir(), ".claude", ".config.json"),
];

const RARITIES = ["common", "uncommon", "rare", "epic", "legendary"] as const;
type Rarity = (typeof RARITIES)[number];

const RARITY_WEIGHTS: Record<Rarity, number> = {
  common: 60, uncommon: 25, rare: 10, epic: 4, legendary: 1,
};

const SPECIES = [
  "duck", "goose", "blob", "cat", "dragon", "octopus",
  "owl", "penguin", "turtle", "snail", "ghost", "axolotl",
  "capybara", "cactus", "robot", "rabbit", "mushroom", "chonk",
];

const EYES = ["·", "✦", "×", "◉", "@", "°"];
const HATS = ["none", "crown", "tophat", "propeller", "halo", "wizard", "beanie", "tinyduck"];
const STAT_NAMES = ["DEBUGGING", "PATIENCE", "CHAOS", "WISDOM", "SNARK"];

const RARITY_FLOOR: Record<Rarity, number> = {
  common: 5, uncommon: 15, rare: 25, epic: 35, legendary: 50,
};

// ── Hash ──

function hashWyhash(s: string): number {
  return Number(BigInt(Bun.hash(s)) & 0xffffffffn);
}

function hashFnv1a(s: string): number {
  let h = 2166136261;
  for (let i = 0; i < s.length; i++) {
    h ^= s.charCodeAt(i);
    h = Math.imul(h, 16777619) >>> 0;
  }
  return h;
}

// ── RNG ──

function mulberry32(seed: number): () => number {
  let a = seed >>> 0;
  return function () {
    a |= 0;
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function pick<T>(rng: () => number, arr: readonly T[]): T {
  return arr[Math.floor(rng() * arr.length)];
}

// ── Roll ──

function rollRarity(rng: () => number): Rarity {
  const total = Object.values(RARITY_WEIGHTS).reduce((a, b) => a + b, 0);
  let r = rng() * total;
  for (const rarity of RARITIES) {
    r -= RARITY_WEIGHTS[rarity];
    if (r < 0) return rarity;
  }
  return "common";
}

function rollStats(rng: () => number, rarity: Rarity): Record<string, number> {
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

interface Bones {
  rarity: Rarity;
  species: string;
  eye: string;
  hat: string;
  shiny: boolean;
  stats: Record<string, number>;
}

function roll(userId: string, salt: string, hashFn: (s: string) => number): { bones: Bones; inspirationSeed: number } {
  const rng = mulberry32(hashFn(userId + salt));
  const rarity = rollRarity(rng);
  const bones: Bones = {
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

function bonesMatch(target: Bones, candidate: Bones): boolean {
  return (
    candidate.species === target.species &&
    candidate.rarity === target.rarity &&
    candidate.eye === target.eye &&
    candidate.hat === target.hat &&
    candidate.shiny === target.shiny
  );
}

// ── Hash detection ──

function detectHash(userId: string, salt: string, targetBones: Bones): "wyhash" | "fnv1a" | null {
  const wyResult = roll(userId, salt, hashWyhash);
  if (bonesMatch(targetBones, wyResult.bones)) return "wyhash";

  const fnvResult = roll(userId, salt, hashFnv1a);
  if (bonesMatch(targetBones, fnvResult.bones)) return "fnv1a";

  return null;
}

function detectRuntime(cliPath: string): "bun" | "node" | "unknown" {
  try {
    const content = readFileSync(cliPath, "utf-8").slice(0, 500);
    if (content.startsWith("#!/") && content.includes("bun")) return "bun";
    if (content.startsWith("#!/") && content.includes("node")) return "node";
  } catch {
    // binary file — read as bytes and check shebang
    try {
      const buf = readFileSync(cliPath);
      const head = buf.subarray(0, 200).toString("utf-8");
      if (head.includes("bun")) return "bun";
      if (head.includes("node")) return "node";
    } catch {}
  }
  return "unknown";
}

function chooseHashFn(userId: string, cliPath: string, currentSalt: string): { fn: (s: string) => number; name: string } {
  // Strategy 1: check if the CLI references bun or node in shebang/header
  const runtime = detectRuntime(cliPath);
  if (runtime === "bun") return { fn: hashWyhash, name: "wyhash" };
  if (runtime === "node") return { fn: hashFnv1a, name: "fnv1a" };

  // Strategy 2: roll with default salt using both hashes, see which produces
  // an owl for this user (since the default companion is deterministic)
  const defaultWy = roll(userId, DEFAULT_SALT, hashWyhash);
  const defaultFnv = roll(userId, DEFAULT_SALT, hashFnv1a);

  // If one produces owl and the other doesn't, that's our answer
  // (the original default buddy for most accounts is well-known)
  // But we can't be sure, so prefer wyhash (Bun is the default runtime)
  console.log("  Could not detect runtime from CLI binary.");
  console.log("  Defaulting to wyhash (Bun) — use --fnv1a to override.");
  return { fn: hashWyhash, name: "wyhash" };
}

// ── Salt search ──

function findSalt(userId: string, targetBones: Bones, hashFn: (s: string) => number, maxAttempts = 10_000_000): string {
  console.log("  Searching for a matching salt...");
  for (let i = 0; i < maxAttempts; i++) {
    const salt = `ptch${i.toString(36).padStart(11, "a")}`;
    const result = roll(userId, salt, hashFn);
    if (bonesMatch(targetBones, result.bones)) return salt;
    if (i > 0 && i % 1_000_000 === 0) console.log(`  ...checked ${i.toLocaleString()} salts`);
  }
  throw new Error(`Could not find a matching salt in ${maxAttempts.toLocaleString()} attempts.`);
}

// ── Binary finder ──

function resolveCliJs(binaryPath: string): string | null {
  const resolved = resolve(binaryPath);
  if (resolved.endsWith(".js")) return resolved;

  const pkg = "@anthropic-ai/claude-code";
  const idx = resolved.indexOf(pkg);
  if (idx !== -1) {
    const cli = join(resolved.slice(0, idx + pkg.length), "cli.js");
    if (existsSync(cli)) return cli;
  }

  const candidates = [
    join(dirname(dirname(resolved)), "lib", "node_modules", pkg, "cli.js"),
    join(dirname(resolved), "node_modules", pkg, "cli.js"),
  ];
  for (const c of candidates) {
    if (existsSync(c)) return c;
  }

  // Compiled binaries cannot be safely patched — byte replacement invalidates
  // their internal integrity checksums, causing segfaults on startup.
  if (existsSync(resolved) && statSync(resolved).size >= 1_000_000) {
    throw new Error(
      `Found compiled binary at ${resolved} but cannot patch it.\n` +
      "  Patching compiled binaries corrupts their integrity checksums, causing segfaults.\n" +
      "  Install Claude Code via npm/pnpm so the patcher can modify cli.js directly:\n" +
      "    npm install -g @anthropic-ai/claude-code"
    );
  }
  return null;
}

function findClaudeBinary(): string {
  const envPath = process.env.CLAUDE_BINARY;
  if (envPath && existsSync(envPath)) {
    const result = resolveCliJs(envPath);
    if (result) return result;
  }

  // which claude
  try {
    const whichResult = execSync("which claude", { encoding: "utf-8" }).trim();
    if (whichResult) {
      const result = resolveCliJs(whichResult);
      if (result) return result;
    }
  } catch {}

  // patcher state
  const state = readPatcherState();
  if (state.cliPath && existsSync(state.cliPath)) {
    const result = resolveCliJs(state.cliPath);
    if (result) return result;
  }

  // platform candidates
  const home = homedir();
  const candidates = IS_MAC
    ? [
        join(home, ".local", "bin", "claude"),
        join(home, ".claude", "local", "claude"),
        "/usr/local/bin/claude",
        "/opt/homebrew/bin/claude",
      ]
    : [
        join(home, ".local", "bin", "claude"),
        "/usr/local/bin/claude",
        "/usr/bin/claude",
      ];

  for (const c of candidates) {
    if (existsSync(c)) {
      const result = resolveCliJs(c);
      if (result) return result;
    }
  }

  throw new Error(
    "Could not find Claude Code installation.\n" +
    "  Set CLAUDE_BINARY=/path/to/cli.js to specify manually."
  );
}

// ── Salt patching ──

function getCurrentSalt(cliPath: string, knownSalts: string[]): string {
  const content = readFileSync(cliPath);

  if (content.includes(DEFAULT_SALT)) return DEFAULT_SALT;

  for (const salt of knownSalts) {
    if (salt && content.includes(salt)) return salt;
  }

  const state = readPatcherState();
  if (state.currentSalt && content.includes(state.currentSalt)) return state.currentSalt;

  throw new Error(
    `Cannot determine current salt in ${cliPath}.\n` +
    `  Default '${DEFAULT_SALT}' not found and no known salt matched.`
  );
}

function patchSalt(cliPath: string, oldSalt: string, newSalt: string): number {
  if (newSalt.length !== SALT_LENGTH) {
    throw new Error(`Salt must be exactly ${SALT_LENGTH} characters, got ${newSalt.length}`);
  }

  let content = readFileSync(cliPath);
  const oldBytes = Buffer.from(oldSalt, "utf-8");
  const newBytes = Buffer.from(newSalt, "utf-8");

  let count = 0;
  let idx = content.indexOf(oldBytes);
  while (idx !== -1) {
    count++;
    idx = content.indexOf(oldBytes, idx + oldBytes.length);
  }

  if (count === 0) {
    throw new Error(`Salt '${oldSalt}' not found in ${cliPath}.`);
  }

  // Replace all occurrences
  const contentStr = content.toString("binary");
  const newContentStr = contentStr.replaceAll(oldSalt, newSalt);
  const newContent = Buffer.from(newContentStr, "binary");

  const tmpPath = cliPath + ".patch-tmp";
  try {
    writeFileSync(tmpPath, newContent);
    chmodSync(tmpPath, statSync(cliPath).mode);
    const { renameSync } = require("fs");
    renameSync(tmpPath, cliPath);
  } catch (e) {
    try { const { unlinkSync } = require("fs"); unlinkSync(tmpPath); } catch {}
    throw e;
  }

  // Verify
  const verify = readFileSync(cliPath);
  if (!verify.includes(newBytes)) {
    throw new Error("Verification failed — salt not applied correctly.");
  }

  if (IS_MAC && !cliPath.endsWith(".js") && !cliPath.endsWith(".mjs")) {
    try { execSync(`codesign --force --sign - "${cliPath}"`, { timeout: 30000 }); } catch {}
  }

  return count;
}

// ── Config & state ──

function findClaudeConfig(): string | null {
  for (const p of CLAUDE_CONFIG_PATHS) {
    if (existsSync(p)) return p;
  }
  return null;
}

function getAccountUuid(configPath: string): string {
  const config = JSON.parse(readFileSync(configPath, "utf-8"));
  const uuid = config?.oauthAccount?.accountUuid;
  if (!uuid) throw new Error("No accountUuid found in Claude config.");
  return uuid;
}

function readPatcherState(): any {
  if (existsSync(PATCHER_STATE)) {
    return JSON.parse(readFileSync(PATCHER_STATE, "utf-8"));
  }
  return {};
}

function writePatcherState(state: any): void {
  writeFileSync(PATCHER_STATE, JSON.stringify(state, null, 2) + "\n");
}

function scanCompanionDirs(base: string, depth = 0): Map<string, string> {
  const results = new Map<string, string>();
  if (!existsSync(base) || depth > 3) return results;
  for (const entry of readdirSync(base, { withFileTypes: true })) {
    if (!entry.isDirectory()) continue;
    const full = join(base, entry.name);
    if (existsSync(join(full, "buddy.json"))) {
      results.set(entry.name, full);
    } else {
      for (const [k, v] of scanCompanionDirs(full, depth + 1)) {
        if (!results.has(k)) results.set(k, v);
      }
    }
  }
  return results;
}

function listCompanions(): string[] {
  return [...scanCompanionDirs(COMPANIONS_DIR).keys()].sort();
}

function loadCompanion(name: string): { buddy: any; companion: any } {
  const dirs = scanCompanionDirs(COMPANIONS_DIR);
  const dir = dirs.get(name);
  if (!dir) { console.error(`Error: Companion '${name}' not found`); process.exit(1); }
  const buddyPath = join(dir, "buddy.json");
  const companionPath = join(dir, "companion.json");
  if (!existsSync(buddyPath)) { console.error(`Error: ${buddyPath} not found`); process.exit(1); }
  if (!existsSync(companionPath)) { console.error(`Error: ${companionPath} not found`); process.exit(1); }
  return {
    buddy: JSON.parse(readFileSync(buddyPath, "utf-8")),
    companion: JSON.parse(readFileSync(companionPath, "utf-8")),
  };
}

function updateClaudeConfig(configPath: string, companion: any): void {
  const config = JSON.parse(readFileSync(configPath, "utf-8"));
  config.companion = {
    name: companion.name,
    personality: companion.personality,
  };
  if (companion.hatchedAt) config.companion.hatchedAt = companion.hatchedAt;
  writeFileSync(configPath, JSON.stringify(config, null, 2) + "\n");
}

// ── Commands ──

function patchCompanion(name: string, forceHash?: "wyhash" | "fnv1a"): void {
  const { buddy, companion } = loadCompanion(name);
  const targetBones = buddy.bones as Bones;

  if (!targetBones) { console.error(`Error: No bones in ${name}/buddy.json`); process.exit(1); }

  let cliPath: string;
  try { cliPath = findClaudeBinary(); } catch (e: any) { console.error(`Error: ${e.message}`); process.exit(1); }

  const configPath = findClaudeConfig();
  if (!configPath) { console.error("Error: Claude config not found"); process.exit(1); }

  const userId = getAccountUuid(configPath);

  // Collect known salts from all companions
  const knownSalts = listCompanions()
    .map((n) => { try { return loadCompanion(n).buddy.salt; } catch { return null; } })
    .filter((s): s is string => typeof s === "string" && s.length === 15 && s !== "unknown");

  const currentSalt = getCurrentSalt(cliPath, knownSalts);

  // Detect or choose hash function
  let hashFn: (s: string) => number;
  let hashName: string;

  if (forceHash === "fnv1a") {
    hashFn = hashFnv1a;
    hashName = "fnv1a";
  } else if (forceHash === "wyhash") {
    hashFn = hashWyhash;
    hashName = "wyhash";
  } else {
    // Auto-detect: try the stored salt with both hashes against target bones
    const storedSalt = buddy.salt;
    if (storedSalt) {
      const detected = detectHash(userId, storedSalt, targetBones);
      if (detected) {
        hashFn = detected === "wyhash" ? hashWyhash : hashFnv1a;
        hashName = detected;
        console.log(`  Hash auto-detected: ${detected} (stored salt matches target with this hash)`);
      } else {
        // Neither hash reproduces target with stored salt — try runtime detection
        const chosen = chooseHashFn(userId, cliPath, currentSalt);
        hashFn = chosen.fn;
        hashName = chosen.name;
      }
    } else {
      const chosen = chooseHashFn(userId, cliPath, currentSalt);
      hashFn = chosen.fn;
      hashName = chosen.name;
    }
  }

  console.log(`\nCompanion:    ${companion.name}`);
  console.log(`Target:       ${targetBones.species} (${targetBones.rarity})`);
  console.log(`              eye=${targetBones.eye}  hat=${targetBones.hat}  shiny=${targetBones.shiny ? "yes" : "no"}`);
  console.log(`CLI file:     ${cliPath}`);
  console.log(`Config:       ${configPath}`);
  console.log(`Current salt: ${currentSalt}`);
  console.log(`Hash:         ${hashName}`);
  console.log();

  // Check if stored salt works for this user with the detected hash
  let newSalt: string;
  const storedSalt = buddy.salt;
  if (storedSalt) {
    const result = roll(userId, storedSalt, hashFn);
    if (bonesMatch(targetBones, result.bones)) {
      newSalt = storedSalt;
      console.log(`Stored salt works for this account: ${newSalt}`);
    } else {
      console.log("Stored salt produces different bones for this account.");
      console.log("Finding a new salt...");
      newSalt = findSalt(userId, targetBones, hashFn);
      console.log(`Found matching salt: ${newSalt}`);
    }
  } else {
    console.log("No stored salt — searching for one...");
    newSalt = findSalt(userId, targetBones, hashFn);
    console.log(`Found matching salt: ${newSalt}`);
  }

  console.log(`New salt:     ${newSalt}`);
  console.log();

  let cliBackupPath: string | null = null;
  if (currentSalt === newSalt) {
    console.log("Salt already matches — just updating companion identity.");
  } else {
    cliBackupPath = `${cliPath}.backup-${Math.floor(Date.now() / 1000)}`;
    copyFileSync(cliPath, cliBackupPath);
    console.log(`Backed up CLI to ${cliBackupPath.split("/").pop()}`);

    try {
      const count = patchSalt(cliPath, currentSalt, newSalt);
      console.log(`Salt patched (${count} replacement(s)).`);
    } catch (e: any) {
      console.error(`Patch failed: ${e.message}`);
      console.log("Restoring backup.");
      copyFileSync(cliBackupPath, cliPath);
      process.exit(1);
    }
  }

  const configBackup = configPath.replace(".json", `.json.backup-${Math.floor(Date.now() / 1000)}`);
  copyFileSync(configPath, configBackup);
  updateClaudeConfig(configPath, companion);
  console.log("Companion identity updated.");

  writePatcherState({
    previousSalt: currentSalt,
    currentSalt: newSalt,
    companion: name,
    cliPath,
    cliBackup: cliBackupPath,
    configBackup,
    hashAlgorithm: hashName,
    patchedAt: new Date().toISOString(),
  });

  // Verify
  const verify = roll(userId, newSalt, hashFn);
  console.log();
  console.log(`Done! ${companion.name} is now your companion.`);
  console.log(`  Species: ${verify.bones.species} (${verify.bones.rarity})`);
  console.log(`  Eye: ${verify.bones.eye}  Hat: ${verify.bones.hat}  Shiny: ${verify.bones.shiny ? "yes" : "no"}`);
  console.log(`  Hash: ${hashName}`);
  console.log();
  console.log("Restart Claude Code to see the changes.");
}

function restoreDefault(forceHash?: "wyhash" | "fnv1a"): void {
  const state = readPatcherState();
  const cliBackup: string | null = state.cliBackup ?? null;
  const configBackup: string | null = state.configBackup ?? null;
  let cliPath: string = state.cliPath ?? "";

  // Restore CLI from backup file if available
  if (cliBackup && existsSync(cliBackup)) {
    if (!cliPath) cliPath = cliBackup.split(".backup-")[0];
    console.log(`Restoring CLI from backup: ${cliBackup.split("/").pop()}`);
    copyFileSync(cliBackup, cliPath);
    console.log(`  ${cliPath} restored.`);
  } else {
    // No backup file — fall back to byte replacement
    if (!cliPath) {
      try { cliPath = findClaudeBinary(); } catch (e: any) { console.error(`Error: ${e.message}`); process.exit(1); }
    }

    const knownSalts = listCompanions()
      .map((n) => { try { return loadCompanion(n).buddy.salt; } catch { return null; } })
      .filter(Boolean);

    const currentSalt = getCurrentSalt(cliPath, knownSalts);

    if (currentSalt === DEFAULT_SALT) {
      console.log("Already using the default salt. Nothing to restore.");
      return;
    }

    // Refuse to byte-replace on compiled binaries
    if (!cliPath.endsWith(".js") && !cliPath.endsWith(".mjs")) {
      console.error(
        "Error: No backup file found and CLI is a compiled binary.\n" +
        "  Cannot safely restore via byte replacement.\n" +
        "  Reinstall Claude Code to fix:\n" +
        "    npm install -g @anthropic-ai/claude-code"
      );
      process.exit(1);
    }

    console.log("No backup file found — falling back to salt replacement.");
    console.log(`Restoring default salt: ${DEFAULT_SALT}`);
    console.log(`Current salt:           ${currentSalt}`);

    const preRestoreBackup = `${cliPath}.backup-${Math.floor(Date.now() / 1000)}`;
    copyFileSync(cliPath, preRestoreBackup);

    try {
      patchSalt(cliPath, currentSalt, DEFAULT_SALT);
    } catch (e: any) {
      console.error(`Restore failed: ${e.message}`);
      copyFileSync(preRestoreBackup, cliPath);
      process.exit(1);
    }
  }

  // Restore config from backup if available
  if (configBackup && existsSync(configBackup)) {
    const configPath = configBackup.split(".backup-")[0];
    console.log(`Restoring config from backup: ${configBackup.split("/").pop()}`);
    copyFileSync(configBackup, configPath);
  } else {
    console.log("  No config backup found — companion identity was not reverted.");
  }

  writePatcherState({
    previousSalt: state.currentSalt ?? null,
    currentSalt: DEFAULT_SALT,
    companion: null,
    cliPath,
    cliBackup: null,
    configBackup: null,
    patchedAt: new Date().toISOString(),
  });

  console.log("Restored. Restart Claude Code.");
}

// ── CLI ──

const args = process.argv.slice(2);
const flags = new Set(args.filter((a) => a.startsWith("--")));
const positional = args.filter((a) => !a.startsWith("--"));

const forceHash: "wyhash" | "fnv1a" | undefined =
  flags.has("--fnv1a") ? "fnv1a" : flags.has("--wyhash") ? "wyhash" : undefined;

if (flags.has("--list")) {
  const companions = listCompanions();
  if (!companions.length) {
    console.log("No companions found in companions/ directory.");
  } else {
    console.log("Available companions:");
    for (const name of companions) {
      const { buddy, companion } = loadCompanion(name);
      const b = buddy.bones;
      console.log(
        `  ${name.padEnd(16)} ${companion.name.padEnd(16)} ` +
        `${b.species.padEnd(10)} ${b.rarity.padEnd(10)} ` +
        `eye=${b.eye}  hat=${b.hat}`
      );
    }
  }
} else if (flags.has("--restore")) {
  restoreDefault(forceHash);
} else if (flags.has("--detect-hash")) {
  // Standalone hash detection utility
  const configPath = findClaudeConfig();
  if (!configPath) { console.error("Error: Claude config not found"); process.exit(1); }
  const userId = getAccountUuid(configPath);
  let cliPath: string;
  try { cliPath = findClaudeBinary(); } catch (e: any) { console.error(`Error: ${e.message}`); process.exit(1); }

  console.log("Hash detection report:");
  console.log(`  CLI:     ${cliPath}`);
  console.log(`  Runtime: ${detectRuntime(cliPath)}`);
  console.log();

  const wyResult = roll(userId, DEFAULT_SALT, hashWyhash);
  const fnvResult = roll(userId, DEFAULT_SALT, hashFnv1a);

  console.log(`  With default salt (${DEFAULT_SALT}):`);
  console.log(`    wyhash → ${wyResult.bones.species} (${wyResult.bones.rarity}), eye=${wyResult.bones.eye}`);
  console.log(`    fnv1a  → ${fnvResult.bones.species} (${fnvResult.bones.rarity}), eye=${fnvResult.bones.eye}`);
  console.log();
  console.log("  Compare with what you see in Claude Code to determine which hash is active.");
} else if (positional.length > 0) {
  const name = positional[0].toLowerCase();
  const available = listCompanions();
  if (!available.includes(name)) {
    console.error(`Error: Companion '${name}' not found.`);
    console.error(`Available: ${available.join(", ")}`);
    process.exit(1);
  }
  patchCompanion(name, forceHash);
} else {
  console.log("Usage: bun patch_companion_bun.ts <companion-name> [--wyhash|--fnv1a]");
  console.log("       bun patch_companion_bun.ts --list");
  console.log("       bun patch_companion_bun.ts --restore");
  console.log("       bun patch_companion_bun.ts --detect-hash");
  console.log();
  console.log("Flags:");
  console.log("  --wyhash       Force wyhash (Bun runtime, default for most installs)");
  console.log("  --fnv1a        Force FNV-1a (Node.js runtime)");
  console.log("  --detect-hash  Show what each hash produces for your account");
}
