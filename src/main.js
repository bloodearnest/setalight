import { h, render, Fragment } from 'preact'
import { useState, useEffect, useRef, useCallback } from 'preact/hooks'
import { useEventListener } from './hooks'

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
  if (song.type === 'chordpro' || song.type === 'pdf') {
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

  const keydown = useCallback(ev => {
    switch (ev.which) {
      case KEY.RIGHT:
        if (active < songs.length - 1) { setActive(active + 1) }
        ev.preventDefault()
        break
      case KEY.LEFT:
        if (active > 0) { setActive(active - 1) }
        ev.preventDefault()
        break
      default:
        break
    }
  },
  [active, setActive]
  )

  useEventListener('keydown', keydown)

  // useEffect(() => {
  //  window.addEventListener('keydown', keydown)
  //  return () => window.removeEventListener('keydown', keydown)
  // })

  return (
    <Fragment>
      { songs.map((song, i) => <Song song={song} display={active === i} />) }
    </Fragment>
  )
}

function Song ({ song, display }) {
  return (
    <article className={'song ' + (display ? 'active' : '')}>
      <SongTitle song={song} />
      {map(song.sections, (name, section) => <Section name={name} section={section} />)}
    </article>
  )
}

function SongTitle ({ song }) {
  const keys = ['key', 'time', 'tempo']
  const parts = keys.map((k) => song[k]).filter(Boolean)
  return (
    <header class='title'>{ song['title'] }
      <span class='info'>{ parts.join(' | ') }</span>
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
        <span class='name toggle' onclick={toggleCollapsed}>{name}</span>
        <span class='collapse toggle' onclick={toggleCollapsed}> ⯅</span>
        <span class='expand toggle' onclick={toggleCollapsed}> ⯆</span>
        &nbsp;<span class='show-chords toggle' onclick={toggleChords}>A♭</span>
      </header>
      {lines.map((l) => <Line line={l} />)}
    </section>
  )
}

function Line ({ line }) {
  // split on [chords] or {directives}, removing undefineds
  var parts = line.split(/(\[.+?\])|(\{.+?\})/g).filter(Boolean)
  var nodes = []
  var _class = 'both'
  if (parts.length === 1) {
    // there are no embedded chords in this line, it's either lyrics or chords
    if (line.indexOf('|') === -1) { // lyrics only
      nodes.push(line)
      _class = 'lyrics'
    } else { // chords only
      var chords = line.split(/( *\| *)/g)
      for (const chord of chords) {
        if (chord.indexOf('|') === -1) {
          nodes.push(h('span', { 'class': 'chord' }, chord))
        } else {
          nodes.push(chord)
        }
      }
      _class = 'chords'
    }
  } else {
    for (var i = 0; i < parts.length; i += 1) {
      const part = parts[i]
      const next = i + 1 < parts.length ? parts[i + 1] : 'END'
      const first = part[0]
      const last = part[part.length - 1]
      const beforeSpace = (next[0] === ' ' || next === '')
      if (first === '[' && last === ']') {
        const chord = part.substring(1, part.length - 1)
        const cls = 'chord ' + (beforeSpace ? 'inspace' : 'inword')
        nodes.push(<span className={cls}>{chord}</span>)
      } else if (first === '{' && last === '}') {
        const [directive, text] = part.substring(1, part.length - 1).split(':')
        switch (directive) {
          case 'comment':
            nodes.push(<span className={'comment ' + (beforeSpace ? 'inspace' : 'inword')}>{text}</span>)
            break
        }
      } else {
        nodes.push(part)
      }
    }
  }
  return <p className={'line ' + _class}>{nodes}</p>
}

var app = document.getElementById('setlist')
var songs = SONGDATA.map((song) => load(song))
console.log(songs)
render(<SetList songs={songs} />, app)
