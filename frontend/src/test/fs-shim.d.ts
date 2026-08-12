// Minimal ambient declaration so test files can read source files from disk without
// pulling all of @types/node into the app's type environment (which conflicts with
// existing app code). Scope: the single fs call used by token/source-scan tests.
declare module 'node:fs' {
  export function readFileSync(path: URL | string, encoding: 'utf8'): string
}
