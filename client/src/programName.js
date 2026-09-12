// e-Panduan appends markers to program names. "#" marks programs that need an
// interview or test (every "#" program has the interview flag, and no other
// program does), so it repeats the "Interview required" badge. "Baru" marks a
// new program. Strip both from the name students see; the raw name is kept for
// search. See docs/decisions/0009-program-name-markers.md.
export function displayProgram(rawName) {
  const isNew = /\bBaru\b/.test(rawName)
  const name = rawName
    .replace(/\s*#\s*$/, '')
    .replace(/\s*\bBaru\b/, '')
    .replace(/\s{2,}/g, ' ')
    .trim()
  return { name, isNew }
}
