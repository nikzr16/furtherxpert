// e-Panduan appends markers to program names. "#" marks programs that need an
// interview or test (every "#" program has the interview flag, and no other
// program does), so it repeats the "Interview required" badge. "Baru" marks a
// new program. Strip both from the name students see; the raw name is kept for
// search. See docs/decisions/0009-program-name-markers.md.
//
// e-Panduan names are ALL CAPS. They contain no acronyms, so they are shown in
// title case, with Malay joining words ("dan", "di", ...) kept lowercase.
const LOWERCASE_WORDS = new Set(['dan', 'di', 'untuk', 'dengan', 'dalam', 'serta', 'atau', 'bagi', 'ke'])

function titleCase(text) {
  return text
    .toLowerCase()
    .split(' ')
    .map((word, index) =>
      index > 0 && LOWERCASE_WORDS.has(word)
        ? word
        : word.replace(/(^|[(\-/])([a-z])/g, (_, before, letter) => before + letter.toUpperCase())
    )
    .join(' ')
}

export function displayProgram(rawName) {
  const isNew = /\bBaru\b/.test(rawName)
  const name = rawName
    .replace(/\s*#\s*$/, '')
    .replace(/\s*\bBaru\b/, '')
    .replace(/\s{2,}/g, ' ')
    .trim()
  return { name: titleCase(name), isNew }
}
