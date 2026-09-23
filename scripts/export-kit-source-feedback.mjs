#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { buildKitSourceFeedbackBundle } from "../lib/kit-source-feedback.mjs";

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(scriptDir, "..");
const args = process.argv.slice(2);

function valueAfter(flag, fallback = null) {
  const index = args.indexOf(flag);
  return index >= 0 ? args[index + 1] : fallback;
}

const output = path.resolve(repoRoot, valueAfter("--out", "evidence/KIT_SOURCE_FEEDBACK.json"));
const bundle = buildKitSourceFeedbackBundle({
  repoRoot,
  originCommit: valueAfter("--origin-commit"),
  exportedAt: valueAfter("--exported-at"),
  countryRegistryPath: valueAfter("--country-registry", "config/country-source-registry.json"),
  regionalResearchPath: valueAfter("--regional-research", "docs/research/latin-america-2026/research.json"),
});

fs.mkdirSync(path.dirname(output), { recursive: true });
const serialized = `${JSON.stringify(bundle, null, 2)}\n`;
if (args.includes("--check")) {
  if (!fs.existsSync(output) || fs.readFileSync(output, "utf8") !== serialized) {
    throw new Error(`Feedback bundle is not current: ${path.relative(repoRoot, output)}`);
  }
} else {
  fs.writeFileSync(output, serialized);
}

const countries = new Set(bundle.sources.map((source) => source.iso3));
const stages = Object.fromEntries([...new Set(bundle.sources.map((source) => source.evidence_stage))]
  .sort()
  .map((stage) => [stage, bundle.sources.filter((source) => source.evidence_stage === stage).length]));
console.log(JSON.stringify({
  output: path.relative(repoRoot, output).replaceAll("\\", "/"),
  origin_commit: bundle.origin_commit,
  source_count: bundle.sources.length,
  country_count: countries.size,
  stages,
}, null, 2));

