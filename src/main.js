import { h, render, Fragment } from 'preact'
import { useState, useCallback } from 'preact/hooks'
import { useEventListener, useSwipe } from './hooks'
import { tokenise, TOKENS } from './chordpro'
import { map, copy, toggleFullScreen, toggleWakeLock } from './platform'

const SONGDATA = JSON.parse(document.getElementById('songdata').innerHTML)

// make local copy of the orginal song, possibly converting along the way
function load (orig) {
  var song = copy(orig)
  if (song.type === 'onsong' || song.type === 'pdf') {
    return song
  } else {
    console.error('Could not load song type ' + song.type)
    console.log(song)
    return song
  }
}

// the main application component
function SetList ({ songs }) {
  return (
    <Fragment>
      <Index songs={songs}/>
      { songs.map((song) => <Song song={song} />) }
    </Fragment>
  )
}

function toggleSetlist(ev) {
  toggleFullScreen()
  toggleWakeLock()
}

function Index({ songs }) {
  return (
      <article class="index page">
        <header>Date goes Here
          <span class="fullscreen" onclick={toggleSetlist} ontouchstart={toggleSetlist}>⛶ </span>
        </header>
        <header>Leader goes here</header>
        <ul>
          {songs.map((s) => <li>{s.title} | {s.key}</li>)}
        </ul>
      </article>
  )
}

function Song ({ song }) {
  return (
      <article class="song page">
        <SongTitle song={song} />
        {map(song.sections, (name, section) => <Section name={name} section={section} />)}
      </article>
  )
}

function SongTitle ({ song }) {
  var nodes = []
  var key = song.key ? song.key : ''
  if (song.capo) {
    key += ' Capo ' + song.capo
  }
  nodes.push(key)
  if (song.time) nodes.push(song.time)
  if (song.tempo) nodes.push(song.tempo)

  return (
    <header class='title'>{ song['title'] }
      <span class='info'>{ nodes.join(' | ') }</span>
    </header>
  )
}

function Section ({ name, section }) {
  const [collapsed, setCollapsed] = useState(false)
  const [chords, setChords] = useState(true)
  const lines = section.split(/\n/)
  const toggleCollapsed = () => setCollapsed(!collapsed)
  const toggleChords = () => setChords(!chords)
  const _class = (collapsed ? 'collapsed ' : ' ') + (chords ? ' ' : 'hide-chords')
  return (
    <section className={_class}>
      <header>
        <span class='name toggle' onclick={toggleCollapsed} ontouchend={toggleCollapsed}>{name}</span>
        <span class='collapse toggle' onclick={toggleCollapsed} ontouchend={toggleCollapsed}> ⯅</span>
        <span class='expand toggle' onclick={toggleCollapsed} ontouchend={toggleCollapsed}> ⯆</span>
        &nbsp;<span class='show-chords toggle' onclick={toggleChords} ontouchend={toggleChords}>A♭</span>
      </header>
      {lines.map((l) => <Line line={l} />)}
    </section>
  )
}


const TOKEN_CLASS = {}
TOKEN_CLASS[TOKENS.CHORD] = 'chord'
TOKEN_CLASS[TOKENS.COMMENT] = 'comment'
TOKEN_CLASS[TOKENS.SPACE] = 'space'
TOKEN_CLASS[TOKENS.HYPHEN] = 'hyphen'

const RAISED_TOKENS = [TOKENS.CHORD, TOKENS.COMMENT]

function Line ({ line }) {
  // split on [chords] or {directives}, removing undefineds
  var nodes = []
  const [line_type, tokens] = tokenise(line)

  for (var i = 0; i < tokens.length; i += 1) {
    const [current, next] = tokens[i]
    var className = TOKEN_CLASS[current.type]

    switch (current.type) {
      case TOKENS.CHORD:
      case TOKENS.COMMENT:
        var wrapperClass = "chordlyric "
        var lyric = ' '
        // is the next token not a chord/comment?
        if (next && !RAISED_TOKENS.includes(next.type)) {
          if (next.type === TOKENS.SPACE || next.value[0] === '-') {
            wrapperClass += 'spaced-chord'
          }
          // pull the next lyric into this node
          lyric = next.value
          i += 1
        }
        if (line_type === 'both') {
          nodes.push(
            <span className={wrapperClass}>
              <span className={className}>{current.value}</span>
              <span class="lyric">{lyric}</span>
            </span>
          )
        } else {
          nodes.push(
            <span className={className}>{current.value}</span>
          )
        }
        break

      case TOKENS.HYPHEN:
      case TOKENS.SPACE:
        nodes.push(<span className={className}>{current.value}</span>)
        break

      case TOKENS.LYRIC:
        nodes.push(current.value)
        break

      default:
        console.error("Unknown token type: ", current)
        break;
    }
  }
  return <p className={'line ' + line_type}>{nodes}</p>
}

var app = document.getElementById('setlist')
var songs = SONGDATA.map((song) => load(song))
console.log(songs)
render(<SetList songs={songs} />, app)
