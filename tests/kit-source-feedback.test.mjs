import assert from "node:assert/strict";
import path from "node:path";
import test from "node:test";
import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import {
  assertPublicSourceUrl,
  buildKitSourceFeedbackBundle,
  deduplicateFeedbackSources,
  mapRegistryEvidenceStage,
  validateKitSourceFeedbackBundle,
} from "../lib/kit-source-feedback.mjs";

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const originCommit = execFileSync("git", ["rev-parse", "HEAD"], { cwd: repoRoot, encoding: "utf8" }).trim();
const exportedAt = "2026-09-23T00:00:00.000Z";

function sampleSource(overrides = {}) {
  return {
    iso3: "UGA",
    source_id: "UGA_UBOS",
    role: "census_catalog",
    title: "Census catalogue",
    publisher: "Uganda Bureau of Statistics",
    url: "https://statistics.ubos.org/nphc/",
    authority_type: "official_national",
    evidence_stage: "official_location_verified",
    checked_at: "2026-09-23",
    geographic_levels: ["national", "district"],
    reference_periods: ["Census 2024"],
    formats: ["HTML"],
    license_or_terms: null,
    reuse_note: "Reconfirm product coverage before reuse.",
    origin_evidence_path: "config/country-source-registry.json",
    artifact_sha256: null,
    ...overrides,
  };
}

test("build is deterministic and backfills only committed evidence", () => {
  const first = buildKitSourceFeedbackBundle({ repoRoot, originCommit, exportedAt });
  const second = buildKitSourceFeedbackBundle({ repoRoot, originCommit, exportedAt });
  assert.deepEqual(first, second);
  assert.equal(first.sources.length, 106);
  assert.equal(new Set(first.sources.map((source) => source.iso3)).size, 22);
  assert.ok(first.sources.every((source) => !source.origin_evidence_path.includes("raw/")));
  assert.ok(first.sources.every((source) => new URL(source.url).hostname !== "ulii.org"));
  validateKitSourceFeedbackBundle(first, { repoRoot });
});

test("country, role and URL duplicates collapse deterministically", () => {
  const weak = sampleSource();
  const strong = sampleSource({
    source_id: "UGA_UBOS_SECOND",
    evidence_stage: "content_inspected",
    geographic_levels: ["subcounty", "national"],
    formats: ["XLSX"],
  });
  const result = deduplicateFeedbackSources([strong, weak]);
  assert.equal(result.length, 1);
  assert.equal(result[0].evidence_stage, "content_inspected");
  assert.deepEqual(result[0].formats, ["HTML", "XLSX"]);
  assert.deepEqual(result[0].geographic_levels, ["district", "national", "subcounty"]);
});

test("registry stages map without promoting negative or unknown states", () => {
  assert.equal(mapRegistryEvidenceStage("location_and_catalog_content_verified"), "content_inspected");
  assert.equal(mapRegistryEvidenceStage("data_acquired"), "source_acquired");
  assert.equal(mapRegistryEvidenceStage("geography_matched"), "geography_matched");
  assert.equal(mapRegistryEvidenceStage("negative_availability_verified"), null);
  assert.equal(mapRegistryEvidenceStage("candidate"), null);
});

test("schema-required fields and unknown fields are rejected", () => {
  const missing = sampleSource();
  delete missing.publisher;
  assert.throws(() => validateKitSourceFeedbackBundle({
    schema_version: "1.0", produced_by: "AreaData", exported_at: exportedAt, origin_commit: originCommit, sources: [missing],
  }, { repoRoot }), /Missing source field.*publisher/);
  assert.throws(() => validateKitSourceFeedbackBundle({
    schema_version: "1.0", produced_by: "AreaData", exported_at: exportedAt, origin_commit: originCommit,
    sources: [sampleSource({ observations: [1] })],
  }, { repoRoot }), /Unknown source field.*observations/);
});

test("public safety rejects credentials, secret query and local addresses", () => {
  assert.throws(() => assertPublicSourceUrl("https://user:pass@example.org/data"), /credentials/);
  assert.throws(() => assertPublicSourceUrl("https://example.org/data?api_key=secret"), /secret query/);
  assert.throws(() => assertPublicSourceUrl("http://127.0.0.1/data"), /local or loopback/);
  assert.throws(() => assertPublicSourceUrl("http://192.168.1.10/data"), /private address/);
  assert.equal(assertPublicSourceUrl("https://example.org/data?id=1"), "https://example.org/data?id=1");
});

test("absolute, parent, raw and uncommitted evidence paths are rejected", () => {
  const bundle = (origin_evidence_path) => ({
    schema_version: "1.0", produced_by: "AreaData", exported_at: exportedAt, origin_commit: originCommit,
    sources: [sampleSource({ origin_evidence_path })],
  });
  assert.throws(() => validateKitSourceFeedbackBundle(bundle("C:/secret/evidence.json"), { repoRoot }), /repository-relative/);
  assert.throws(() => validateKitSourceFeedbackBundle(bundle("../evidence.json"), { repoRoot }), /repository-relative/);
  assert.throws(() => validateKitSourceFeedbackBundle(bundle("raw/source.json"), { repoRoot }), /Raw artifact/);
  const schemaCommit = execFileSync("git", ["log", "-1", "--format=%H", "--", "schemas/areadata-source-feedback.schema.json"], { cwd: repoRoot, encoding: "utf8" }).trim();
  const beforeSchema = execFileSync("git", ["rev-parse", `${schemaCommit}^`], { cwd: repoRoot, encoding: "utf8" }).trim();
  const preSchemaBundle = bundle("schemas/areadata-source-feedback.schema.json");
  preSchemaBundle.origin_commit = beforeSchema;
  assert.throws(() => validateKitSourceFeedbackBundle(preSchemaBundle, { repoRoot }), /not present at origin_commit/);
});
