import { h, render } from 'preact'
import { useState } from 'preact/hooks'

const SONGDATA = JSON.parse(document.getElementById('songdata').innerHTML)

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
    return null
  }
}

// the main application component
function SetList (songs) {
  const [active, setActive] = useState(0)
  var f = (i, song) => h(Song, {
    index: parseInt(i),
    song: song,
    display: active === parseInt(i),
    set: () => setActive(parseInt(i) + 1)
  })
  return h('div', null, map(songs, f))
}

function Song ({ index, song, display, set }) {
  var attrs = {
    'class': 'song ' + (display ? 'active' : ''),
    //onclick: set
  }
  return h(
    'article',
    attrs,
    map(song.sections, (name, section) => h(Section, { name: name, section: section }))
  )
}

function Toggle(cls, text, click) {
    return h('span', {'class': cls + " toggle", onclick: click}, text)
}

function Section ({ name, section }) {
  const [collapsed, setCollapsed] = useState(false)
  const [chords, setChords] = useState(true)
  const lines = section.split(/\n/).map((l) => h(Line, { line: l }))
  const toggle_collapsed = () => setCollapsed(!collapsed)
  const toggle_chords = () => setChords(!chords)
  const _class = (collapsed ? 'collapsed ' : ' ') + (chords ? ' ': 'hide-chords')
  return h('section', {'class': _class},
    h('header', null,
      Toggle('name', name, toggle_collapsed),
      Toggle('collapse', " ⯅", toggle_collapsed),
      Toggle('expand',   " ⯆", toggle_collapsed),
      " ",
      Toggle('show-chords', "A♭", toggle_chords),
    ),
    ...lines,
  )
}

function Line ({ line }) {
  var parts = line.split(/(\[.+?\])/g)
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
          nodes.push(h('span', {'class': 'chord' }, chord))
        } else {
          nodes.push(chord)
        }
      }
      _class = 'chords'
    }
  } else {
    for (var i = 0; i < parts.length; i += 1) {
      const part = parts[i];
      const next = i + 1 < parts.length ? parts[i+1] : 'XXX'
      if (part[0] === '[' && part[part.length - 1] === ']') {
        const chord = part.substring(1, part.length - 1)
        if (next[0] === ' ') { // is chord this before a space?
          nodes.push(h('span', {'class': 'chord inspace'}, chord))
        } else {
          nodes.push(h('span', {'class': 'chord inword' }, chord))
        }
      } else {
        nodes.push(part)
      }
    }
  }
  return h('p', {'class': 'line ' + _class}, ...nodes)
}

var app = document.getElementById('songs')
var songs = SONGDATA.map((song) => load(song))
console.log(songs)
render(h(SetList, songs), app)
