import { describe, it, expect } from 'vitest'
import {
  MAX_REGISTRATION_TOTAL_BYTES,
  validateMaterialFileForUpload,
  validateTotalUploadBudget,
} from '../utils/materialFile'

describe('materialFile client validation', () => {
  it('rejects a 22MB file before any API call would run', () => {
    const huge = new File([new Uint8Array(22 * 1024 * 1024)], 'big.pdf', { type: 'application/pdf' })
    expect(huge.size).toBe(22 * 1024 * 1024)
    const result = validateMaterialFileForUpload(huge, ['pdf'])
    expect(result.ok).toBe(false)
    expect(result.error).toMatch(/20MB/i)
  })

  it('accepts a small allowed file', () => {
    const f = new File([new Uint8Array(1024)], 'note.pdf', { type: 'application/pdf' })
    expect(validateMaterialFileForUpload(f, ['pdf'])).toEqual({ ok: true })
  })

  it('rejects disallowed extension', () => {
    const f = new File([new Uint8Array(10)], 'x.exe', { type: 'application/octet-stream' })
    const r = validateMaterialFileForUpload(f, ['pdf'])
    expect(r.ok).toBe(false)
  })

  it('enforces 200MB total budget', () => {
    const f = new File([new Uint8Array(1024)], 'a.pdf', { type: 'application/pdf' })
    const r = validateTotalUploadBudget(MAX_REGISTRATION_TOTAL_BYTES, f)
    expect(r.ok).toBe(false)
  })
})
