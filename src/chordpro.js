
const isChord = (t) => t[0] === '[' && t[t.length - 1] === ']'
const isComment = (t) => t[0] === '{' && t[t.length - 1] === '}'

const TOKENS = {
  CHORD: 'CHORD',
  COMMENT: 'COMMENT',
  HYPHEN: 'HYPHEN',
  LYRIC: 'LYRIC',
  SPACE: 'SPACE',
}


// tokenise the chordpro line, returning pairs of [current, next] tokens so
// that there is some lookahead context
function tokenise(line) {
  // split line on chords, comments, hyphens, and spaces, keeping the delimiters
  const tokens = line.split(/(\[.+?\])|(\{.+?\})|( - |- | -)|( +)/g).filter(Boolean)
  const pairs = []

  var current = null
  // counts used to determine if this line is chords, lyrics, or both
  var counts = {}
  for (const t of Object.keys(TOKENS)) {
    counts[t] = 0
  }

  for (const token of tokens) {
    var _type = null
    var _value = token
    if (isChord(token)) {
      _type = TOKENS.CHORD
      _value = token.substring(1, token.length - 1) // strip []
    } else if (isComment(token)) {
      _type = TOKENS.COMMENT
      const [directive, text] = token.substring(1, token.length - 1).split(':')
      _value = text
    } else if (/ ?- ?/.test(token)) {
      _type = TOKENS.HYPHEN
    } else if (/\s+/.test(token)) {
      _type = TOKENS.SPACE
    } else {
      _type = TOKENS.LYRIC
    }

    counts[_type] += 1
    const next = {'type': _type, 'value': _value}
    if (current !== null) {
      pairs.push([current, next])
    }
    current = next
  }
  pairs.push([current, null])

  var line_type = 'lyrics'
  if (counts[TOKENS.CHORD] > 0) {
    if (counts[TOKENS.LYRIC] > 0) {
      line_type = 'both'
    } else {
      line_type = 'chords'
    }
  }
  return [line_type, pairs]
}


export {
  TOKENS,
  tokenise,
}
