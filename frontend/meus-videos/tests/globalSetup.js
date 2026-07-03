import { mkdirSync, rmSync } from "node:fs";
import { resolve } from "node:path";

export default function globalSetup() {
  const outputDir = resolve(process.cwd(), "tests/results");
  mkdirSync(outputDir, { recursive: true });

  for (const filename of [
    "last_run.json",
    "runtime_failures.json",
    "vitest-report.json",
  ]) {
    rmSync(resolve(outputDir, filename), { force: true });
  }
}
