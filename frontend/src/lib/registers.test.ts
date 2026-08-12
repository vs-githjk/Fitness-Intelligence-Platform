import { describe, expect, it } from 'vitest'
import { REGISTERS, registerProps, type Register } from './registers'

describe('registers', () => {
  it('defines the three Iron Editorial registers', () => {
    expect(REGISTERS).toEqual(['calm', 'live', 'human'])
  })

  it('emits a data-register attribute for register-scoped styling', () => {
    const registers: Register[] = ['calm', 'live', 'human']
    for (const register of registers) {
      expect(registerProps(register)).toEqual({ 'data-register': register })
    }
  })
})
