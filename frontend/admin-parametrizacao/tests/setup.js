import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";
import { cleanup } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";
import {
  afterAll,
  afterEach,
  beforeEach,
  vi,
} from "vitest";
import { consumeCase, ensureCaseStore, normalizeErrors } from "./support/caseLog";

beforeEach((context) => {
  localStorage.clear();
  sessionStorage.clear();
  vi.unstubAllEnvs();
  globalThis.alert = vi.fn();
  context.onTestFinished((finishedContext) => {
    const store = ensureCaseStore();
    const current = consumeCase(finishedContext.task.id);

    store.results.push({
      name: finishedContext.task.name,
      nodeid: finishedContext.task.fullTestName,
      file: finishedContext.task.file?.filepath ?? null,
      state: finishedContext.task.result?.state ?? "unknown",
      duration_ms: finishedContext.task.result?.duration ?? null,
      input: current.input ?? null,
      expected: current.expected ?? null,
      output: current.output ?? null,
      notes: current.notes ?? [],
      errors: normalizeErrors(finishedContext.task.result?.errors),
    });
  });
});

afterEach(() => {
  cleanup();
});

afterAll(() => {
  const store = ensureCaseStore();
  const outputDir = resolve(process.cwd(), "tests/results");
  const outputPath = resolve(outputDir, "last_run.json");
  mkdirSync(outputDir, { recursive: true });
  const existing = existsSync(outputPath)
    ? JSON.parse(readFileSync(outputPath, "utf-8"))
    : {
        app: store.app,
        started_at: store.startedAt,
        generated_at: null,
        tests: [],
      };

  writeFileSync(
    outputPath,
    JSON.stringify(
      {
        app: existing.app ?? store.app,
        started_at: existing.started_at ?? store.startedAt,
        generated_at: new Date().toISOString(),
        tests: [...(existing.tests ?? []), ...store.results],
      },
      null,
      2,
    ),
  );
});
