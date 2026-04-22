/** Client-side limits aligned with API (single file ≤ 20MB). */

export const MAX_MATERIAL_FILE_BYTES = 20 * 1024 * 1024
export const MAX_REGISTRATION_TOTAL_BYTES = 200 * 1024 * 1024

/**
 * @param {File | null | undefined} file
 * @param {string[]} allowedTypes lower-case extensions without dot, e.g. ['pdf','jpg']
 * @returns {{ ok: true } | { ok: false, error: string }}
 */
export function validateMaterialFileForUpload(file, allowedTypes) {
  if (!file) {
    return { ok: false, error: 'No file selected.' }
  }
  if (file.size > MAX_MATERIAL_FILE_BYTES) {
    return { ok: false, error: 'File exceeds the 20MB limit and was not sent to the server.' }
  }
  const name = typeof file.name === 'string' ? file.name : ''
  const ext = name.includes('.') ? name.split('.').pop().toLowerCase() : ''
  if (!ext || !allowedTypes.map((t) => t.toLowerCase()).includes(ext)) {
    return {
      ok: false,
      error: `File type ".${ext || '?'}" is not allowed for this item (${allowedTypes.join(', ')}).`,
    }
  }
  return { ok: true }
}

/**
 * @param {number} totalBytesAlreadyUploaded
 * @param {File} file
 */
export function validateTotalUploadBudget(totalBytesAlreadyUploaded, file) {
  if (totalBytesAlreadyUploaded + file.size > MAX_REGISTRATION_TOTAL_BYTES) {
    return {
      ok: false,
      error: 'Adding this file would exceed the 200MB total upload limit for this registration.',
    }
  }
  return { ok: true }
}
