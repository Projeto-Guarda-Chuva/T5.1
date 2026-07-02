import { getCurrentTest } from "@vitest/runner";

const STORE_KEY = "__codex_meus_videos_case_store__";

function cloneSerializable(value) {
  if (value instanceof Error) {
    return {
      name: value.name,
      message: value.message,
      stack: value.stack,
    };
  }

  if (typeof value === "function") {
    return `[Function ${value.name || "anonymous"}]`;
  }

  if (value === undefined) {
    return null;
  }

  try {
    return JSON.parse(
      JSON.stringify(value, (_key, nestedValue) => {
        if (nestedValue instanceof Error) {
          return {
            name: nestedValue.name,
            message: nestedValue.message,
            stack: nestedValue.stack,
          };
        }

        if (typeof nestedValue === "function") {
          return `[Function ${nestedValue.name || "anonymous"}]`;
        }

        return nestedValue;
      }),
    );
  } catch {
    return String(value);
  }
}

export function ensureCaseStore() {
  if (!globalThis[STORE_KEY]) {
    globalThis[STORE_KEY] = {
      app: "meus-videos",
      startedAt: new Date().toISOString(),
      metaByTaskId: new Map(),
      results: [],
    };
  }

  return globalThis[STORE_KEY];
}

export function registerCase(partial = {}) {
  const task = getCurrentTest();

  if (!task) {
    throw new Error("registerCase precisa ser chamado dentro de um teste Vitest.");
  }

  const store = ensureCaseStore();
  const current = store.metaByTaskId.get(task.id) ?? { notes: [] };

  if (partial.notes) {
    current.notes = [...current.notes, ...partial.notes];
  }

  Object.entries(partial).forEach(([key, value]) => {
    if (key !== "notes") {
      current[key] = cloneSerializable(value);
    }
  });

  store.metaByTaskId.set(task.id, current);
  return current;
}

export function consumeCase(taskId) {
  const store = ensureCaseStore();
  const current = store.metaByTaskId.get(taskId) ?? { notes: [] };
  store.metaByTaskId.delete(taskId);
  return current;
}

export function normalizeErrors(errors = []) {
  return errors.map((error) => ({
    name: error?.name ?? "Error",
    message: error?.message ?? String(error),
    stack: error?.stack ?? null,
  }));
}
