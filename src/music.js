const NOTES_SHARP = 'A A# B C C# D D# E F F# G G#'.split(' ')
const NOTES_FLAT = 'A Bb B C Db D Eb E F Gb G Ab'.split(' ')
const NOTES_ALL = 'A A# Bb B C C# Db D D# Eb E F F# Gb G G# Ab'.split(' ')
const SHARP_KEYS = 'C Am G Em D Bm A F#m E C#m B G#m F# D#m C# A#m'.split(' ')
const FLAT_KEYS = 'F Dm Bb Gm Eb Cm Ab Fm Db Bbm Gb Ebm Cb Abm'.split(' ')


function calculateTranspose (src, dst) {
  if (src === dst) {
    return { amount: 0, notes: [] }
  }
  const src_notes = FLAT_KEYS.includes(src) ? NOTES_FLAT : NOTES_SHARP
  const dst_notes = FLAT_KEYS.includes(dst) ? NOTES_FLAT : NOTES_SHARP
  const src_index = src_notes.indexOf(src)
  const dst_index = dst_notes.indexOf(dst)
  const amount = dst_index - src_index
  let transpose = {}
  for (let i = 0; i < src_notes.length; i += 1) {
    transpose[src_notes[i]] = dst_notes[(12 + amount + i) % dst_notes.length]
  }
  return transpose
}

function transposeChord (chord, transpose) {
  const match = chord.match(/^([A-G][b#]?)([^/]*)[/]?([A-G][b#]?)?/)
  const note = match[1]
  const rest = match[2]
  const bass = match[3]
  return transpose[note] + rest + (bass ? '/' + transpose[bass] : '')
}

export {
  transposeChord,
  calculateTranspose,
  NOTES_ALL
}
