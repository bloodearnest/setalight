import { h, render, Fragment } from 'preact'
import { useState, useCallback } from 'preact/hooks'
import { useEventListener, useSwipe } from './hooks'
import { tokenise, TOKENS } from './chordpro'

const SONGDATA = JSON.parse(document.getElementById('songdata').innerHTML)
const KEY = {
  LEFT: 37,
  RIGHT: 39
}

// I cannot believe that js has no built-in way to do this!
function map (obj, f) {
  return Object.keys(obj).map((key) => f(key, obj[key]))
}

// oh the humanity
function copy (obj) {
  return JSON.parse(JSON.stringify(obj))
}

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
  const [active, setActive] = useState(0)

  const switchSong = useCallback(
    (direction) => {
      var handled = true
      switch (direction) {
        case 'right':
        case KEY.RIGHT:
          setActive(Math.min(active + 1, songs.length)) // +1 because of index page
          break
        case 'left':
        case KEY.LEFT:
          setActive(Math.max(0, active - 1))
          break
        default:
          handled = false
      }
      return handled
    },
    [active, setActive]
  )

  useEventListener('keydown', ev => {
    if (switchSong(ev.which)) {
      ev.preventDefault()
    }
  })
  useSwipe(switchSong, window)

  return (
    <Fragment>
      <Index songs={songs} active={active}/>
      { songs.map((song, i) => <Song song={song} index={i} active={active} />) }
    </Fragment>
  )
}

function Index({ songs, active }) {
  const x = active * -(window.innerWidth)
  return (
    <div class="container" style={{ transform: 'translateX(' + x + 'px)' }}>
      <article class="index">
        <header>Date goes Here</header>
        <header>Leader goes here</header>
        <ul>
          {songs.map((s, i) => <li>{s.title} | {s.key}</li>)}
        </ul>
      </article>
    </div>
  )
}

function Song ({ song, index, active }) {
  const x = active * -(window.innerWidth)
  return (
    <div class="container" style={{ transform: 'translateX(' + x + 'px)' }}>
      <article class="song">
        <SongTitle song={song} />
        {map(song.sections, (name, section) => <Section name={name} section={section} />)}
      </article>
    </div>
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
