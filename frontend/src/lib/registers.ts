// Register foundation (Iron Editorial, Experience Cycle 2, C2.0).
//
// One product identity that changes emotional temperature by register (Calm =
// deciding, Live = training, Human = the coach). Every migrated surface declares its
// register. It is expressed as a `data-register` attribute so surfaces can opt into
// register-scoped styling without a component framework — a documented convention,
// not an abstraction. No surface consumes this yet; C2.1+ adopt it as they migrate.
// Authority: docs/design/visual-identity-v2-iron-editorial.md §5.

export type Register = 'calm' | 'live' | 'human'

export const REGISTERS: readonly Register[] = ['calm', 'live', 'human']

export function registerProps(register: Register): { 'data-register': Register } {
  return { 'data-register': register }
}
